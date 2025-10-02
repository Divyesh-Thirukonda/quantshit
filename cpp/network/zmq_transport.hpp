#pragma once

/**
 * ZeroMQ Transport Layer
 *
 * High-performance messaging infrastructure for market data and order routing.
 * Supports multiple patterns:
 * - PUB/SUB for market data distribution
 * - REQ/REP for synchronous order submission
 * - PUSH/PULL for async order queuing
 * - DEALER/ROUTER for async bidirectional communication
 */

#include <atomic>
#include <functional>
#include <memory>
#include <stdexcept>
#include <string>
#include <thread>
#include <unordered_map>
#include <vector>
#include <zmq.h>

namespace quantshit {

/**
 * RAII wrapper for ZMQ context
 */
class ZmqContext {
public:
  explicit ZmqContext(int io_threads = 2) {
    ctx_ = zmq_ctx_new();
    if (!ctx_) {
      throw std::runtime_error("Failed to create ZMQ context");
    }
    zmq_ctx_set(ctx_, ZMQ_IO_THREADS, io_threads);
  }

  ~ZmqContext() {
    if (ctx_) {
      zmq_ctx_destroy(ctx_);
    }
  }

  // Non-copyable
  ZmqContext(const ZmqContext &) = delete;
  ZmqContext &operator=(const ZmqContext &) = delete;

  void *handle() const { return ctx_; }

private:
  void *ctx_ = nullptr;
};

/**
 * Message buffer for zero-copy operations
 */
class ZmqMessage {
public:
  ZmqMessage() { zmq_msg_init(&msg_); }

  explicit ZmqMessage(size_t size) { zmq_msg_init_size(&msg_, size); }

  ZmqMessage(const void *data, size_t size) {
    zmq_msg_init_size(&msg_, size);
    memcpy(zmq_msg_data(&msg_), data, size);
  }

  explicit ZmqMessage(const std::string &str)
      : ZmqMessage(str.data(), str.size()) {}

  ~ZmqMessage() { zmq_msg_close(&msg_); }

  // Move semantics for zero-copy
  ZmqMessage(ZmqMessage &&other) noexcept {
    zmq_msg_init(&msg_);
    zmq_msg_move(&msg_, &other.msg_);
  }

  ZmqMessage &operator=(ZmqMessage &&other) noexcept {
    if (this != &other) {
      zmq_msg_close(&msg_);
      zmq_msg_init(&msg_);
      zmq_msg_move(&msg_, &other.msg_);
    }
    return *this;
  }

  void *data() { return zmq_msg_data(&msg_); }
  const void *data() const { return zmq_msg_data(&msg_); }
  size_t size() const { return zmq_msg_size(&msg_); }

  std::string to_string() const {
    return std::string(static_cast<const char *>(data()), size());
  }

  zmq_msg_t *handle() { return &msg_; }

private:
  zmq_msg_t msg_;
};

/**
 * Base socket wrapper with common operations
 */
class ZmqSocket {
public:
  ZmqSocket(ZmqContext &ctx, int socket_type) {
    socket_ = zmq_socket(ctx.handle(), socket_type);
    if (!socket_) {
      throw std::runtime_error("Failed to create ZMQ socket");
    }
  }

  virtual ~ZmqSocket() {
    if (socket_) {
      zmq_close(socket_);
    }
  }

  // Non-copyable
  ZmqSocket(const ZmqSocket &) = delete;
  ZmqSocket &operator=(const ZmqSocket &) = delete;

  void bind(const std::string &endpoint) {
    if (zmq_bind(socket_, endpoint.c_str()) != 0) {
      throw std::runtime_error("Failed to bind: " +
                               std::string(zmq_strerror(errno)));
    }
    bound_endpoint_ = endpoint;
  }

  void connect(const std::string &endpoint) {
    if (zmq_connect(socket_, endpoint.c_str()) != 0) {
      throw std::runtime_error("Failed to connect: " +
                               std::string(zmq_strerror(errno)));
    }
    connected_endpoints_.push_back(endpoint);
  }

  void disconnect(const std::string &endpoint) {
    zmq_disconnect(socket_, endpoint.c_str());
  }

  // Set socket options
  void set_linger(int ms) {
    zmq_setsockopt(socket_, ZMQ_LINGER, &ms, sizeof(ms));
  }

  void set_recv_timeout(int ms) {
    zmq_setsockopt(socket_, ZMQ_RCVTIMEO, &ms, sizeof(ms));
  }

  void set_send_timeout(int ms) {
    zmq_setsockopt(socket_, ZMQ_SNDTIMEO, &ms, sizeof(ms));
  }

  void set_high_water_mark(int hwm) {
    zmq_setsockopt(socket_, ZMQ_SNDHWM, &hwm, sizeof(hwm));
    zmq_setsockopt(socket_, ZMQ_RCVHWM, &hwm, sizeof(hwm));
  }

  // Send/receive operations
  bool send(const void *data, size_t size, int flags = 0) {
    int rc = zmq_send(socket_, data, size, flags);
    return rc >= 0;
  }

  bool send(const std::string &data, int flags = 0) {
    return send(data.data(), data.size(), flags);
  }

  bool send(ZmqMessage &msg, int flags = 0) {
    int rc = zmq_msg_send(msg.handle(), socket_, flags);
    return rc >= 0;
  }

  int recv(void *buffer, size_t max_size, int flags = 0) {
    return zmq_recv(socket_, buffer, max_size, flags);
  }

  bool recv(ZmqMessage &msg, int flags = 0) {
    int rc = zmq_msg_recv(msg.handle(), socket_, flags);
    return rc >= 0;
  }

  std::string recv_string(int flags = 0) {
    ZmqMessage msg;
    if (recv(msg, flags)) {
      return msg.to_string();
    }
    return "";
  }

  void *handle() const { return socket_; }

protected:
  void *socket_ = nullptr;
  std::string bound_endpoint_;
  std::vector<std::string> connected_endpoints_;
};

/**
 * Publisher socket for market data broadcasting
 */
class Publisher : public ZmqSocket {
public:
  explicit Publisher(ZmqContext &ctx) : ZmqSocket(ctx, ZMQ_PUB) {
    set_linger(0);
  }

  bool publish(const std::string &topic, const void *data, size_t size) {
    // Send topic as first frame
    if (!send(topic, ZMQ_SNDMORE)) {
      return false;
    }
    // Send data as second frame
    return send(data, size);
  }

  bool publish(const std::string &topic, const std::string &data) {
    return publish(topic, data.data(), data.size());
  }
};

/**
 * Subscriber socket for receiving market data
 */
class Subscriber : public ZmqSocket {
public:
  explicit Subscriber(ZmqContext &ctx) : ZmqSocket(ctx, ZMQ_SUB) {}

  void subscribe(const std::string &topic = "") {
    zmq_setsockopt(socket_, ZMQ_SUBSCRIBE, topic.c_str(), topic.size());
  }

  void unsubscribe(const std::string &topic = "") {
    zmq_setsockopt(socket_, ZMQ_UNSUBSCRIBE, topic.c_str(), topic.size());
  }

  // Receive with topic
  bool recv_with_topic(std::string &topic, std::string &data) {
    ZmqMessage topic_msg, data_msg;

    if (!recv(topic_msg))
      return false;
    topic = topic_msg.to_string();

    // Check for more parts
    int more = 0;
    size_t more_size = sizeof(more);
    zmq_getsockopt(socket_, ZMQ_RCVMORE, &more, &more_size);

    if (more) {
      if (!recv(data_msg))
        return false;
      data = data_msg.to_string();
    }

    return true;
  }
};

/**
 * Request socket for synchronous order submission
 */
class Requester : public ZmqSocket {
public:
  explicit Requester(ZmqContext &ctx) : ZmqSocket(ctx, ZMQ_REQ) {
    set_linger(0);
  }

  std::string request(const std::string &data) {
    if (!send(data)) {
      return "";
    }
    return recv_string();
  }
};

/**
 * Reply socket for order handling
 */
class Replier : public ZmqSocket {
public:
  explicit Replier(ZmqContext &ctx) : ZmqSocket(ctx, ZMQ_REP) {}
};

/**
 * Poller for multiplexing multiple sockets
 */
class Poller {
public:
  void add(ZmqSocket &socket, short events = ZMQ_POLLIN) {
    zmq_pollitem_t item;
    item.socket = socket.handle();
    item.fd = 0;
    item.events = events;
    item.revents = 0;
    items_.push_back(item);
    sockets_.push_back(&socket);
  }

  int poll(int timeout_ms = -1) {
    return zmq_poll(items_.data(), static_cast<int>(items_.size()), timeout_ms);
  }

  bool has_input(size_t index) const {
    return items_[index].revents & ZMQ_POLLIN;
  }

  bool has_output(size_t index) const {
    return items_[index].revents & ZMQ_POLLOUT;
  }

  ZmqSocket *socket(size_t index) { return sockets_[index]; }

  size_t size() const { return items_.size(); }

private:
  std::vector<zmq_pollitem_t> items_;
  std::vector<ZmqSocket *> sockets_;
};

/**
 * Async message handler with callback
 */
class AsyncReceiver {
public:
  using MessageCallback =
      std::function<void(const std::string &, const std::string &)>;

  AsyncReceiver(ZmqContext &ctx, const std::string &endpoint,
                MessageCallback callback)
      : subscriber_(ctx), callback_(std::move(callback)), running_(false) {
    subscriber_.connect(endpoint);
    subscriber_.subscribe("");
  }

  void start() {
    running_ = true;
    thread_ = std::thread([this]() {
      while (running_) {
        std::string topic, data;
        subscriber_.set_recv_timeout(100); // 100ms timeout
        if (subscriber_.recv_with_topic(topic, data)) {
          callback_(topic, data);
        }
      }
    });
  }

  void stop() {
    running_ = false;
    if (thread_.joinable()) {
      thread_.join();
    }
  }

  ~AsyncReceiver() { stop(); }

private:
  Subscriber subscriber_;
  MessageCallback callback_;
  std::atomic<bool> running_;
  std::thread thread_;
};

} // namespace quantshit
