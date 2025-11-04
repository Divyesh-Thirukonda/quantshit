#pragma once

/**
 * Execution Engine
 *
 * Core component for low-latency order execution with dedicated worker threads,
 * CPU pinning, and lock-free message passing.
 */

#include <atomic>
#include <functional>
#include <memory>
#include <string>
#include <thread>
#include <unordered_map>

#include "../core/cpu_utils.hpp"
#include "../core/lock_free_queue.hpp"
#include "../core/timing.hpp"
#include "../network/market_protocol.hpp"
#include "../network/packet_normalizer.hpp"

namespace quantshit {

/**
 * Order status
 */
enum class OrderStatus : uint8_t {
  PENDING = 0,
  SUBMITTED,
  ACKNOWLEDGED,
  PARTIALLY_FILLED,
  FILLED,
  CANCELLED,
  REJECTED,
  ERROR
};

/**
 * Order type
 */
enum class OrderType : uint8_t {
  MARKET = 0,
  LIMIT,
  IOC, // Immediate or Cancel
  FOK, // Fill or Kill
  GTC  // Good Till Cancel
};

/**
 * Internal order representation
 */
struct Order {
  uint64_t internal_id;
  std::string external_id;
  std::string market_id;
  Protocol venue;

  Side side;
  OrderType type;
  OrderStatus status;

  double price;
  double quantity;
  double filled_quantity;
  double average_fill_price;

  int64_t created_at_ns;
  int64_t submitted_at_ns;
  int64_t last_update_ns;

  std::string error_message;
};

/**
 * Execution report from venue
 */
struct ExecutionReport {
  uint64_t order_id;
  std::string external_id;
  OrderStatus status;

  double filled_quantity;
  double fill_price;
  double remaining_quantity;

  int64_t timestamp_ns;
  std::string message;
};

/**
 * Order submission request
 */
struct OrderRequest {
  std::string market_id;
  Protocol venue;
  Side side;
  OrderType type;
  double price;
  double quantity;

  // Callback for async notification
  std::function<void(const ExecutionReport &)> callback;
};

/**
 * Risk check result
 */
struct RiskCheckResult {
  bool passed;
  std::string reason;
};

/**
 * Risk limits configuration
 */
struct RiskLimits {
  double max_order_size = 10000.0;
  double max_position_per_market = 50000.0;
  double max_total_position = 200000.0;
  int max_orders_per_second = 10;
  double max_loss_per_day = 1000.0;
};

/**
 * Position tracker
 */
class PositionTracker {
public:
  void update(const std::string &market_id, double delta) {
    std::lock_guard<std::mutex> lock(mutex_);
    positions_[market_id] += delta;
  }

  double get(const std::string &market_id) const {
    std::lock_guard<std::mutex> lock(mutex_);
    auto it = positions_.find(market_id);
    return it != positions_.end() ? it->second : 0.0;
  }

  double total() const {
    std::lock_guard<std::mutex> lock(mutex_);
    double sum = 0.0;
    for (const auto &[_, pos] : positions_) {
      sum += std::abs(pos);
    }
    return sum;
  }

  void reset() {
    std::lock_guard<std::mutex> lock(mutex_);
    positions_.clear();
  }

private:
  mutable std::mutex mutex_;
  std::unordered_map<std::string, double> positions_;
};

/**
 * Risk manager for pre-trade checks
 */
class RiskManager {
public:
  explicit RiskManager(const RiskLimits &limits) : limits_(limits) {}

  RiskCheckResult check(const OrderRequest &req,
                        const PositionTracker &positions) {
    // Check order size
    if (req.quantity > limits_.max_order_size) {
      return {false, "Order size exceeds limit"};
    }

    // Check position limit for market
    double current_pos = positions.get(req.market_id);
    double new_pos =
        current_pos + (req.side == Side::BUY ? req.quantity : -req.quantity);
    if (std::abs(new_pos) > limits_.max_position_per_market) {
      return {false, "Would exceed position limit for market"};
    }

    // Check total position
    double total = positions.total() + req.quantity;
    if (total > limits_.max_total_position) {
      return {false, "Would exceed total position limit"};
    }

    // Rate limit check
    auto now = now_ns();
    orders_this_second_.erase(
        std::remove_if(orders_this_second_.begin(), orders_this_second_.end(),
                       [now](int64_t t) { return now - t > 1'000'000'000; }),
        orders_this_second_.end());

    if (static_cast<int>(orders_this_second_.size()) >=
        limits_.max_orders_per_second) {
      return {false, "Rate limit exceeded"};
    }
    orders_this_second_.push_back(now);

    return {true, ""};
  }

  void set_limits(const RiskLimits &limits) { limits_ = limits; }

private:
  RiskLimits limits_;
  std::vector<int64_t> orders_this_second_;
};

/**
 * Main execution engine
 */
class ExecutionEngine {
public:
  using OrderCallback = std::function<void(const Order &)>;
  using ExecutionCallback = std::function<void(const ExecutionReport &)>;

  struct Config {
    int order_thread_core = -1; // CPU core for order thread (-1 = no pinning)
    int market_data_thread_core = -1;
    size_t order_queue_size = 16384;
    RiskLimits risk_limits;
  };

  explicit ExecutionEngine(const Config &config = Config())
      : config_(config), risk_manager_(config.risk_limits), running_(false),
        next_order_id_(1) {}

  ~ExecutionEngine() { stop(); }

  /**
   * Start the execution engine threads
   */
  void start() {
    if (running_.exchange(true)) {
      return; // Already running
    }

    // Start order processing thread
    order_thread_ = std::thread([this]() {
      if (config_.order_thread_core >= 0) {
        pin_to_core(config_.order_thread_core);
      }
      order_loop();
    });

    // Start execution report processing thread
    exec_thread_ = std::thread([this]() { exec_loop(); });
  }

  /**
   * Stop the execution engine
   */
  void stop() {
    if (!running_.exchange(false)) {
      return; // Not running
    }

    if (order_thread_.joinable()) {
      order_thread_.join();
    }
    if (exec_thread_.joinable()) {
      exec_thread_.join();
    }
  }

  /**
   * Submit an order for execution
   */
  bool submit_order(const OrderRequest &request) {
    // Pre-trade risk check
    auto risk_result = risk_manager_.check(request, positions_);
    if (!risk_result.passed) {
      if (request.callback) {
        ExecutionReport report;
        report.status = OrderStatus::REJECTED;
        report.message = risk_result.reason;
        request.callback(report);
      }
      return false;
    }

    // Create internal order
    Order order;
    order.internal_id = next_order_id_.fetch_add(1);
    order.market_id = request.market_id;
    order.venue = request.venue;
    order.side = request.side;
    order.type = request.type;
    order.price = request.price;
    order.quantity = request.quantity;
    order.filled_quantity = 0.0;
    order.status = OrderStatus::PENDING;
    order.created_at_ns = now_ns();

    // Store callback
    if (request.callback) {
      std::lock_guard<std::mutex> lock(callbacks_mutex_);
      callbacks_[order.internal_id] = request.callback;
    }

    // Queue for processing
    return order_queue_.try_push(order);
  }

  /**
   * Cancel an existing order
   */
  bool cancel_order(uint64_t order_id) {
    // In real implementation, send cancel to venue
    std::lock_guard<std::mutex> lock(orders_mutex_);
    auto it = active_orders_.find(order_id);
    if (it != active_orders_.end()) {
      it->second.status = OrderStatus::CANCELLED;
      return true;
    }
    return false;
  }

  /**
   * Get order by ID
   */
  std::optional<Order> get_order(uint64_t order_id) const {
    std::lock_guard<std::mutex> lock(orders_mutex_);
    auto it = active_orders_.find(order_id);
    if (it != active_orders_.end()) {
      return it->second;
    }
    return std::nullopt;
  }

  /**
   * Register a connection for a venue
   */
  void register_connection(Protocol venue, MarketConnection *conn) {
    std::lock_guard<std::mutex> lock(connections_mutex_);
    connections_[venue] = conn;
  }

  /**
   * Get engine statistics
   */
  struct Stats {
    uint64_t orders_submitted;
    uint64_t orders_filled;
    uint64_t orders_rejected;
    double total_volume;
    int64_t avg_latency_ns;
  };

  Stats get_stats() const { return stats_; }

  /**
   * Set callback for order updates
   */
  void set_order_callback(OrderCallback cb) { order_callback_ = std::move(cb); }
  void set_execution_callback(ExecutionCallback cb) {
    execution_callback_ = std::move(cb);
  }

private:
  void order_loop() {
    while (running_) {
      auto order_opt = order_queue_.try_pop();
      if (!order_opt) {
        // No orders, yield briefly
        std::this_thread::yield();
        continue;
      }

      Order &order = *order_opt;
      order.status = OrderStatus::SUBMITTED;
      order.submitted_at_ns = now_ns();

      // Store in active orders
      {
        std::lock_guard<std::mutex> lock(orders_mutex_);
        active_orders_[order.internal_id] = order;
      }

      // Send to venue
      send_to_venue(order);

      stats_.orders_submitted++;

      if (order_callback_) {
        order_callback_(order);
      }
    }
  }

  void exec_loop() {
    while (running_) {
      auto report_opt = exec_queue_.try_pop();
      if (!report_opt) {
        std::this_thread::yield();
        continue;
      }

      ExecutionReport &report = *report_opt;

      // Update order state
      {
        std::lock_guard<std::mutex> lock(orders_mutex_);
        auto it = active_orders_.find(report.order_id);
        if (it != active_orders_.end()) {
          it->second.status = report.status;
          it->second.filled_quantity = report.filled_quantity;
          it->second.last_update_ns = report.timestamp_ns;

          if (report.status == OrderStatus::FILLED) {
            stats_.orders_filled++;
            stats_.total_volume += report.filled_quantity;

            // Update position
            double delta = it->second.side == Side::BUY
                               ? report.filled_quantity
                               : -report.filled_quantity;
            positions_.update(it->second.market_id, delta);
          }
        }
      }

      // Invoke callback
      {
        std::lock_guard<std::mutex> lock(callbacks_mutex_);
        auto it = callbacks_.find(report.order_id);
        if (it != callbacks_.end()) {
          it->second(report);
          if (report.status == OrderStatus::FILLED ||
              report.status == OrderStatus::CANCELLED ||
              report.status == OrderStatus::REJECTED) {
            callbacks_.erase(it);
          }
        }
      }

      if (execution_callback_) {
        execution_callback_(report);
      }
    }
  }

  void send_to_venue(const Order &order) {
    MarketConnection *conn = nullptr;
    {
      std::lock_guard<std::mutex> lock(connections_mutex_);
      auto it = connections_.find(order.venue);
      if (it != connections_.end()) {
        conn = it->second;
      }
    }

    if (conn && conn->state() == ConnectionState::CONNECTED) {
      // Serialize and send order
      // In real implementation, use proper serialization
      std::string msg = serialize_order(order);
      conn->send(msg);
    }
  }

  std::string serialize_order(const Order &order) {
    // Simple JSON-like serialization (use proper serializer in production)
    return "{\"id\":" + std::to_string(order.internal_id) + ",\"market\":\"" +
           order.market_id + "\"" +
           ",\"side\":" + std::to_string(static_cast<int>(order.side)) +
           ",\"price\":" + std::to_string(order.price) +
           ",\"qty\":" + std::to_string(order.quantity) + "}";
  }

  Config config_;
  RiskManager risk_manager_;
  PositionTracker positions_;

  std::atomic<bool> running_;
  std::atomic<uint64_t> next_order_id_;

  std::thread order_thread_;
  std::thread exec_thread_;

  LockFreeQueue<Order, 16384> order_queue_;
  LockFreeQueue<ExecutionReport, 16384> exec_queue_;

  mutable std::mutex orders_mutex_;
  std::unordered_map<uint64_t, Order> active_orders_;

  std::mutex callbacks_mutex_;
  std::unordered_map<uint64_t, ExecutionCallback> callbacks_;

  std::mutex connections_mutex_;
  std::unordered_map<Protocol, MarketConnection *> connections_;

  OrderCallback order_callback_;
  ExecutionCallback execution_callback_;

  Stats stats_{};
};

} // namespace quantshit
