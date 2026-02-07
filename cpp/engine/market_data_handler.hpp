#pragma once

/**
 * Market Data Handler
 *
 * Receives, normalizes, and distributes real-time market data updates.
 * Maintains order books and provides price feeds to strategy components.
 */

#include <atomic>
#include <functional>
#include <map>
#include <mutex>
#include <shared_mutex>
#include <thread>
#include <unordered_map>
#include <vector>

#include "../core/cpu_utils.hpp"
#include "../core/lock_free_queue.hpp"
#include "../core/timing.hpp"
#include "../network/packet_normalizer.hpp"

namespace quantshit {

/**
 * Single side of order book
 */
class BookSide {
public:
  void update(double price, double size) {
    if (size <= 0) {
      levels_.erase(price);
    } else {
      levels_[price] = size;
    }
  }

  double best_price() const {
    if (levels_.empty())
      return 0.0;
    return levels_.begin()->first;
  }

  double size_at(double price) const {
    auto it = levels_.find(price);
    return it != levels_.end() ? it->second : 0.0;
  }

  double total_size(int depth = -1) const {
    double sum = 0.0;
    int count = 0;
    for (const auto &[_, size] : levels_) {
      sum += size;
      if (depth > 0 && ++count >= depth)
        break;
    }
    return sum;
  }

  std::vector<BookLevel> top(size_t n) const {
    std::vector<BookLevel> result;
    result.reserve(n);
    for (const auto &[price, size] : levels_) {
      if (result.size() >= n)
        break;
      result.push_back({price, size, 0});
    }
    return result;
  }

  void clear() { levels_.clear(); }
  bool empty() const { return levels_.empty(); }
  size_t depth() const { return levels_.size(); }

private:
  // For bids: descending order, for asks: ascending order
  // Using map for automatic sorting
  std::map<double, double, std::greater<double>> levels_;
};

/**
 * Full order book for a market
 */
class OrderBook {
public:
  explicit OrderBook(const std::string &market_id) : market_id_(market_id) {}

  const std::string &market_id() const { return market_id_; }

  void update_bid(double price, double size) {
    bids_.update(price, size);
    last_update_ns_ = now_ns();
  }

  void update_ask(double price, double size) {
    asks_.update(price, size);
    last_update_ns_ = now_ns();
  }

  void apply(const OrderBookSnapshot &snapshot) {
    bids_.clear();
    asks_.clear();

    for (const auto &level : snapshot.bids) {
      bids_.update(level.price, level.size);
    }
    for (const auto &level : snapshot.asks) {
      asks_.update(level.price, level.size);
    }

    sequence_ = snapshot.sequence;
    last_update_ns_ = snapshot.timestamp_ns;
  }

  double best_bid() const { return bids_.best_price(); }
  double best_ask() const { return asks_.best_price(); }
  double mid_price() const { return (best_bid() + best_ask()) / 2.0; }
  double spread() const { return best_ask() - best_bid(); }
  double spread_bps() const {
    double mid = mid_price();
    return mid > 0 ? (spread() / mid) * 10000 : 0;
  }

  const BookSide &bids() const { return bids_; }
  const BookSide &asks() const { return asks_; }

  uint32_t sequence() const { return sequence_; }
  int64_t last_update_ns() const { return last_update_ns_; }
  int64_t age_ns() const { return now_ns() - last_update_ns_; }

private:
  std::string market_id_;
  BookSide bids_;
  BookSide asks_;
  uint32_t sequence_ = 0;
  int64_t last_update_ns_ = 0;
};

/**
 * Quote (top of book) for quick access
 */
struct Quote {
  std::string market_id;
  Protocol source;

  double bid_price;
  double bid_size;
  double ask_price;
  double ask_size;

  int64_t timestamp_ns;

  double mid_price() const { return (bid_price + ask_price) / 2.0; }
  double spread() const { return ask_price - bid_price; }
};

/**
 * Market data handler with real-time feed processing
 */
class MarketDataHandler {
public:
  using QuoteCallback = std::function<void(const Quote &)>;
  using TradeCallback = std::function<void(const TradeEvent &)>;
  using BookCallback =
      std::function<void(const std::string &, const OrderBook &)>;

  struct Config {
    int handler_thread_core;
    size_t update_queue_size;
    bool maintain_full_books;
    // Explicit constructor to satisfy AppleClang nested struct requirements
    Config()
        : handler_thread_core(-1), update_queue_size(65536),
          maintain_full_books(true) {}
  };

  explicit MarketDataHandler(const Config &config = Config())
      : config_(config), running_(false) {}

  ~MarketDataHandler() { stop(); }

  void start() {
    if (running_.exchange(true))
      return;

    handler_thread_ = std::thread([this]() {
      if (config_.handler_thread_core >= 0) {
        pin_to_core(config_.handler_thread_core);
      }
      process_loop();
    });
  }

  void stop() {
    if (!running_.exchange(false))
      return;

    if (handler_thread_.joinable()) {
      handler_thread_.join();
    }
  }

  /**
   * Feed a normalized message into the handler
   */
  void on_message(const NormalizedMessage &msg) { update_queue_.try_push(msg); }

  /**
   * Get current quote for a market
   */
  std::optional<Quote> get_quote(const std::string &market_id) const {
    std::shared_lock<std::shared_mutex> lock(quotes_mutex_);
    auto it = quotes_.find(market_id);
    return it != quotes_.end() ? std::make_optional(it->second) : std::nullopt;
  }

  /**
   * Get order book for a market
   */
  const OrderBook *get_book(const std::string &market_id) const {
    std::shared_lock<std::shared_mutex> lock(books_mutex_);
    auto it = books_.find(market_id);
    return it != books_.end() ? &it->second : nullptr;
  }

  /**
   * Get all available market IDs
   */
  std::vector<std::string> get_markets() const {
    std::shared_lock<std::shared_mutex> lock(quotes_mutex_);
    std::vector<std::string> result;
    result.reserve(quotes_.size());
    for (const auto &[id, _] : quotes_) {
      result.push_back(id);
    }
    return result;
  }

  // Callbacks
  void set_quote_callback(QuoteCallback cb) { quote_callback_ = std::move(cb); }
  void set_trade_callback(TradeCallback cb) { trade_callback_ = std::move(cb); }
  void set_book_callback(BookCallback cb) { book_callback_ = std::move(cb); }

  // Statistics
  struct Stats {
    uint64_t quotes_received;
    uint64_t trades_received;
    uint64_t books_received;
    uint64_t queue_drops;
    int64_t avg_processing_latency_ns;
  };

  Stats get_stats() const { return stats_; }

private:
  void process_loop() {
    while (running_) {
      auto msg_opt = update_queue_.try_pop();
      if (!msg_opt) {
        std::this_thread::yield();
        continue;
      }

      int64_t start = now_ns();

      std::visit(
          [this](auto &&msg) {
            using T = std::decay_t<decltype(msg)>;
            if constexpr (std::is_same_v<T, MarketDataUpdate>) {
              handle_quote(msg);
            } else if constexpr (std::is_same_v<T, OrderBookSnapshot>) {
              handle_book(msg);
            } else if constexpr (std::is_same_v<T, TradeEvent>) {
              handle_trade(msg);
            }
          },
          *msg_opt);

      // Update latency stats (simple moving average)
      int64_t latency = now_ns() - start;
      stats_.avg_processing_latency_ns =
          (stats_.avg_processing_latency_ns * 7 + latency) / 8;
    }
  }

  void handle_quote(const MarketDataUpdate &update) {
    Quote quote;
    quote.market_id = update.market_id;
    quote.source = update.source;
    quote.bid_price = update.bid_price;
    quote.bid_size = update.bid_size;
    quote.ask_price = update.ask_price;
    quote.ask_size = update.ask_size;
    quote.timestamp_ns = update.timestamp_ns;

    {
      std::unique_lock<std::shared_mutex> lock(quotes_mutex_);
      quotes_[update.market_id] = quote;
    }

    stats_.quotes_received++;

    if (quote_callback_) {
      quote_callback_(quote);
    }
  }

  void handle_book(const OrderBookSnapshot &snapshot) {
    if (config_.maintain_full_books) {
      std::unique_lock<std::shared_mutex> lock(books_mutex_);
      auto it = books_.find(snapshot.market_id);
      if (it == books_.end()) {
        it = books_.emplace(snapshot.market_id, OrderBook(snapshot.market_id))
                 .first;
      }
      it->second.apply(snapshot);

      stats_.books_received++;

      if (book_callback_) {
        book_callback_(snapshot.market_id, it->second);
      }
    }
  }

  void handle_trade(const TradeEvent &trade) {
    stats_.trades_received++;

    if (trade_callback_) {
      trade_callback_(trade);
    }
  }

  Config config_;
  std::atomic<bool> running_;
  std::thread handler_thread_;

  LockFreeQueue<NormalizedMessage, 65536> update_queue_;

  mutable std::shared_mutex quotes_mutex_;
  std::unordered_map<std::string, Quote> quotes_;

  mutable std::shared_mutex books_mutex_;
  std::unordered_map<std::string, OrderBook> books_;

  QuoteCallback quote_callback_;
  TradeCallback trade_callback_;
  BookCallback book_callback_;

  Stats stats_{};
};

} // namespace quantshit
