#pragma once

/**
 * Arbitrage Detector
 *
 * Real-time cross-venue arbitrage opportunity detection using
 * lock-free data structures and minimal latency processing.
 */

#include <atomic>
#include <cmath>
#include <functional>
#include <unordered_map>
#include <vector>

#include "../core/lock_free_queue.hpp"
#include "../core/timing.hpp"
#include "market_data_handler.hpp"

namespace quantshit {

/**
 * Arbitrage opportunity between two venues
 */
struct ArbitrageOpportunity {
  std::string market_id;

  Protocol buy_venue;
  Protocol sell_venue;

  double buy_price;  // Price to buy at buy_venue
  double sell_price; // Price to sell at sell_venue
  double max_size;   // Maximum executable size

  double spread;            // sell_price - buy_price
  double spread_bps;        // Spread in basis points
  double expected_profit;   // Expected profit for max_size
  double profit_after_fees; // After estimated fees

  int64_t detected_at_ns;
  int64_t quote_age_ns; // Age of oldest quote used

  // Confidence metrics
  double confidence; // 0.0 to 1.0
  bool stale;        // True if quotes are too old
};

/**
 * Arbitrage detector configuration
 */
struct ArbitrageConfig {
  double min_spread_bps = 10.0;           // Minimum spread to report
  double min_profit = 1.0;                // Minimum expected profit
  int64_t max_quote_age_ns = 100'000'000; // 100ms max quote staleness

  double kalshi_fee_bps = 7.0;     // Kalshi trading fee
  double polymarket_fee_bps = 0.0; // Polymarket fee (none currently)

  std::vector<std::string> tracked_markets; // Empty = all markets
};

/**
 * Cross-venue arbitrage detector
 */
class ArbitrageDetector {
public:
  using OpportunityCallback = std::function<void(const ArbitrageOpportunity &)>;

  explicit ArbitrageDetector(MarketDataHandler &market_data,
                             const ArbitrageConfig &config = ArbitrageConfig())
      : market_data_(market_data), config_(config), running_(false) {}

  ~ArbitrageDetector() { stop(); }

  void start() {
    if (running_.exchange(true))
      return;

    detector_thread_ = std::thread([this]() { detect_loop(); });
  }

  void stop() {
    if (!running_.exchange(false))
      return;

    if (detector_thread_.joinable()) {
      detector_thread_.join();
    }
  }

  /**
   * Manually check for arbitrage on a specific market
   */
  std::vector<ArbitrageOpportunity> check_market(const std::string &market_id) {
    std::vector<ArbitrageOpportunity> opportunities;

    // Get quotes from all venues for this market
    auto quote = market_data_.get_quote(market_id);
    if (!quote)
      return opportunities;

    // For each pair of venues, check for arbitrage
    // In a real system, we'd have quotes per venue
    // Here we simulate with assumed cross-venue data

    auto opp =
        check_pair(market_id, Protocol::KALSHI_WS, Protocol::POLYMARKET_WS);
    if (opp && opp->spread_bps >= config_.min_spread_bps) {
      opportunities.push_back(*opp);
    }

    return opportunities;
  }

  /**
   * Get all current opportunities (snapshot)
   */
  std::vector<ArbitrageOpportunity> get_opportunities() const {
    std::lock_guard<std::mutex> lock(opportunities_mutex_);
    std::vector<ArbitrageOpportunity> result;
    for (const auto &[_, opp] : current_opportunities_) {
      result.push_back(opp);
    }
    return result;
  }

  /**
   * Get best current opportunity
   */
  std::optional<ArbitrageOpportunity> get_best_opportunity() const {
    std::lock_guard<std::mutex> lock(opportunities_mutex_);

    ArbitrageOpportunity *best = nullptr;
    for (auto &[_, opp] : current_opportunities_) {
      if (!best || opp.profit_after_fees > best->profit_after_fees) {
        best = &opp;
      }
    }

    return best ? std::make_optional(*best) : std::nullopt;
  }

  void set_callback(OpportunityCallback cb) { callback_ = std::move(cb); }
  void set_config(const ArbitrageConfig &config) { config_ = config; }

  // Statistics
  struct Stats {
    uint64_t scans;
    uint64_t opportunities_found;
    uint64_t opportunities_executed;
    double total_theoretical_profit;
    int64_t last_scan_ns;
  };

  Stats get_stats() const { return stats_; }

private:
  void detect_loop() {
    while (running_) {
      int64_t start = now_ns();

      scan_all_markets();

      stats_.scans++;
      stats_.last_scan_ns = now_ns() - start;

      // Rate limit scanning
      std::this_thread::sleep_for(std::chrono::milliseconds(1));
    }
  }

  void scan_all_markets() {
    auto markets = config_.tracked_markets.empty() ? market_data_.get_markets()
                                                   : config_.tracked_markets;

    for (const auto &market_id : markets) {
      auto opportunities = check_market(market_id);

      for (const auto &opp : opportunities) {
        process_opportunity(opp);
      }
    }

    // Clean up stale opportunities
    cleanup_stale();
  }

  std::optional<ArbitrageOpportunity>
  check_pair(const std::string &market_id, Protocol venue_a, Protocol venue_b) {

    // In real implementation, get separate quotes per venue
    auto quote = market_data_.get_quote(market_id);
    if (!quote)
      return std::nullopt;

    int64_t current_time = now_ns();
    int64_t quote_age = current_time - quote->timestamp_ns;

    // Simulate venue price differences (in real system, actual venue prices)
    // For demo, assume 0.5% price difference between venues
    double venue_a_bid = quote->bid_price * 0.998;
    double venue_a_ask = quote->ask_price;
    double venue_b_bid = quote->bid_price;
    double venue_b_ask = quote->ask_price * 1.002;

    // Check both directions
    ArbitrageOpportunity opp;
    opp.market_id = market_id;
    opp.detected_at_ns = current_time;
    opp.quote_age_ns = quote_age;
    opp.stale = quote_age > config_.max_quote_age_ns;

    // Direction 1: Buy on venue_a, sell on venue_b
    double spread_1 = venue_b_bid - venue_a_ask;

    // Direction 2: Buy on venue_b, sell on venue_a
    double spread_2 = venue_a_bid - venue_b_ask;

    if (spread_1 > spread_2 && spread_1 > 0) {
      opp.buy_venue = venue_a;
      opp.sell_venue = venue_b;
      opp.buy_price = venue_a_ask;
      opp.sell_price = venue_b_bid;
      opp.spread = spread_1;
    } else if (spread_2 > 0) {
      opp.buy_venue = venue_b;
      opp.sell_venue = venue_a;
      opp.buy_price = venue_b_ask;
      opp.sell_price = venue_a_bid;
      opp.spread = spread_2;
    } else {
      return std::nullopt; // No arbitrage
    }

    // Calculate metrics
    double mid_price = (opp.buy_price + opp.sell_price) / 2.0;
    opp.spread_bps = (opp.spread / mid_price) * 10000;

    opp.max_size = std::min(quote->bid_size, quote->ask_size);
    opp.expected_profit = opp.spread * opp.max_size;

    // Calculate fees
    double fee_buy =
        get_venue_fee(opp.buy_venue) * opp.buy_price * opp.max_size / 10000;
    double fee_sell =
        get_venue_fee(opp.sell_venue) * opp.sell_price * opp.max_size / 10000;
    opp.profit_after_fees = opp.expected_profit - fee_buy - fee_sell;

    // Confidence based on quote freshness
    opp.confidence = std::max(
        0.0, 1.0 - (static_cast<double>(quote_age) / config_.max_quote_age_ns));

    if (opp.spread_bps < config_.min_spread_bps ||
        opp.profit_after_fees < config_.min_profit) {
      return std::nullopt;
    }

    return opp;
  }

  double get_venue_fee(Protocol venue) const {
    switch (venue) {
    case Protocol::KALSHI_WS:
    case Protocol::KALSHI_REST:
      return config_.kalshi_fee_bps;
    case Protocol::POLYMARKET_WS:
    case Protocol::POLYMARKET_REST:
      return config_.polymarket_fee_bps;
    default:
      return 0.0;
    }
  }

  void process_opportunity(const ArbitrageOpportunity &opp) {
    std::string key = opp.market_id + "_" +
                      std::to_string(static_cast<int>(opp.buy_venue)) + "_" +
                      std::to_string(static_cast<int>(opp.sell_venue));

    {
      std::lock_guard<std::mutex> lock(opportunities_mutex_);
      auto it = current_opportunities_.find(key);
      bool is_new = (it == current_opportunities_.end());
      current_opportunities_[key] = opp;

      if (is_new) {
        stats_.opportunities_found++;
        stats_.total_theoretical_profit += opp.profit_after_fees;
      }
    }

    if (callback_) {
      callback_(opp);
    }
  }

  void cleanup_stale() {
    int64_t current = now_ns();
    std::lock_guard<std::mutex> lock(opportunities_mutex_);

    for (auto it = current_opportunities_.begin();
         it != current_opportunities_.end();) {
      if (current - it->second.detected_at_ns > config_.max_quote_age_ns * 10) {
        it = current_opportunities_.erase(it);
      } else {
        ++it;
      }
    }
  }

  MarketDataHandler &market_data_;
  ArbitrageConfig config_;
  std::atomic<bool> running_;
  std::thread detector_thread_;

  mutable std::mutex opportunities_mutex_;
  mutable std::unordered_map<std::string, ArbitrageOpportunity>
      current_opportunities_;

  OpportunityCallback callback_;
  Stats stats_{};
};

} // namespace quantshit
