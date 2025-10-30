#pragma once

/**
 * Market Protocol Interface
 *
 * Abstract interface for connecting to decentralized market protocols.
 * Provides connection management, message sending, and connection pooling.
 */

#include <atomic>
#include <chrono>
#include <condition_variable>
#include <functional>
#include <memory>
#include <mutex>
#include <queue>
#include <string>
#include <thread>
#include <vector>

#include "packet_normalizer.hpp"

namespace quantshit {

/**
 * Connection state
 */
enum class ConnectionState {
  DISCONNECTED,
  CONNECTING,
  CONNECTED,
  RECONNECTING,
  ERROR
};

/**
 * Connection configuration
 */
struct ConnectionConfig {
  std::string endpoint;
  int port = 0;
  std::string api_key;
  std::string api_secret;

  int connect_timeout_ms = 5000;
  int read_timeout_ms = 1000;
  int write_timeout_ms = 1000;
  int heartbeat_interval_ms = 30000;

  bool auto_reconnect = true;
  int max_reconnect_attempts = 5;
  int reconnect_delay_ms = 1000;
};

/**
 * Message callback types
 */
using DataCallback = std::function<void(const RawPacket &)>;
using StateCallback = std::function<void(ConnectionState)>;
using ErrorCallback = std::function<void(int, const std::string &)>;

/**
 * Abstract market connection interface
 */
class MarketConnection {
public:
  virtual ~MarketConnection() = default;

  virtual Protocol protocol() const = 0;
  virtual ConnectionState state() const = 0;

  virtual bool connect() = 0;
  virtual void disconnect() = 0;

  virtual bool send(const void *data, size_t size) = 0;
  virtual bool send(const std::string &message) {
    return send(message.data(), message.size());
  }

  virtual void subscribe(const std::string &channel,
                         const std::string &symbol = "") = 0;
  virtual void unsubscribe(const std::string &channel,
                           const std::string &symbol = "") = 0;

  virtual void set_data_callback(DataCallback cb) = 0;
  virtual void set_state_callback(StateCallback cb) = 0;
  virtual void set_error_callback(ErrorCallback cb) = 0;
};

/**
 * WebSocket-based market connection
 */
class WebSocketConnection : public MarketConnection {
public:
  explicit WebSocketConnection(const ConnectionConfig &config, Protocol proto)
      : config_(config), proto_(proto), state_(ConnectionState::DISCONNECTED) {}

  ~WebSocketConnection() override { disconnect(); }

  Protocol protocol() const override { return proto_; }
  ConnectionState state() const override { return state_.load(); }

  bool connect() override {
    state_ = ConnectionState::CONNECTING;

    // In real implementation, use libwebsockets, Beast, or uWebSockets
    // For now, this is a stub

    state_ = ConnectionState::CONNECTED;

    if (state_callback_) {
      state_callback_(ConnectionState::CONNECTED);
    }

    return true;
  }

  void disconnect() override {
    if (state_ == ConnectionState::DISCONNECTED)
      return;

    state_ = ConnectionState::DISCONNECTED;

    if (state_callback_) {
      state_callback_(ConnectionState::DISCONNECTED);
    }
  }

  bool send(const void *data, size_t size) override {
    if (state_ != ConnectionState::CONNECTED) {
      return false;
    }

    // Queue message for sending
    std::lock_guard<std::mutex> lock(send_mutex_);
    outgoing_.emplace(static_cast<const uint8_t *>(data),
                      static_cast<const uint8_t *>(data) + size);
    return true;
  }

  void subscribe(const std::string &channel,
                 [[maybe_unused]] const std::string &symbol) override {
    subscriptions_.push_back(channel);
  }

  void unsubscribe(const std::string &channel,
                   [[maybe_unused]] const std::string &symbol) override {
    subscriptions_.erase(
        std::remove(subscriptions_.begin(), subscriptions_.end(), channel),
        subscriptions_.end());
  }

  void set_data_callback(DataCallback cb) override {
    data_callback_ = std::move(cb);
  }
  void set_state_callback(StateCallback cb) override {
    state_callback_ = std::move(cb);
  }
  void set_error_callback(ErrorCallback cb) override {
    error_callback_ = std::move(cb);
  }

protected:
  ConnectionConfig config_;
  Protocol proto_;
  std::atomic<ConnectionState> state_;

  DataCallback data_callback_;
  StateCallback state_callback_;
  ErrorCallback error_callback_;

  std::vector<std::string> subscriptions_;

  std::mutex send_mutex_;
  std::queue<std::vector<uint8_t>> outgoing_;
};

/**
 * Connection pool for managing multiple connections
 */
class ConnectionPool {
public:
  explicit ConnectionPool(size_t max_connections = 10)
      : max_connections_(max_connections) {}

  void add(std::unique_ptr<MarketConnection> conn) {
    std::lock_guard<std::mutex> lock(mutex_);
    if (connections_.size() < max_connections_) {
      connections_.push_back(std::move(conn));
    }
  }

  MarketConnection *get(Protocol proto) {
    std::lock_guard<std::mutex> lock(mutex_);
    for (auto &conn : connections_) {
      if (conn->protocol() == proto &&
          conn->state() == ConnectionState::CONNECTED) {
        return conn.get();
      }
    }
    return nullptr;
  }

  void connect_all() {
    std::lock_guard<std::mutex> lock(mutex_);
    for (auto &conn : connections_) {
      if (conn->state() == ConnectionState::DISCONNECTED) {
        conn->connect();
      }
    }
  }

  void disconnect_all() {
    std::lock_guard<std::mutex> lock(mutex_);
    for (auto &conn : connections_) {
      conn->disconnect();
    }
  }

  size_t size() const {
    std::lock_guard<std::mutex> lock(mutex_);
    return connections_.size();
  }

  size_t connected_count() const {
    std::lock_guard<std::mutex> lock(mutex_);
    size_t count = 0;
    for (const auto &conn : connections_) {
      if (conn->state() == ConnectionState::CONNECTED) {
        ++count;
      }
    }
    return count;
  }

private:
  size_t max_connections_;
  mutable std::mutex mutex_;
  std::vector<std::unique_ptr<MarketConnection>> connections_;
};

/**
 * Kalshi-specific connection
 */
class KalshiConnection : public WebSocketConnection {
public:
  explicit KalshiConnection(const ConnectionConfig &config)
      : WebSocketConnection(config, Protocol::KALSHI_WS) {}

  bool authenticate() {
    // Kalshi authentication handshake
    return true;
  }
};

/**
 * Polymarket-specific connection
 */
class PolymarketConnection : public WebSocketConnection {
public:
  explicit PolymarketConnection(const ConnectionConfig &config)
      : WebSocketConnection(config, Protocol::POLYMARKET_WS) {}
};

} // namespace quantshit
