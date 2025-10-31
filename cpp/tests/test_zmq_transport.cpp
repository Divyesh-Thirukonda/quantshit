/**
 * ZeroMQ Transport Unit Tests
 */

#include <chrono>
#include <gtest/gtest.h>
#include <thread>

#include "../network/zmq_transport.hpp"

using namespace quantshit;

class ZmqTransportTest : public ::testing::Test {
protected:
  void SetUp() override { ctx_ = std::make_unique<ZmqContext>(); }

  void TearDown() override { ctx_.reset(); }

  std::unique_ptr<ZmqContext> ctx_;
};

TEST_F(ZmqTransportTest, ContextCreation) {
  EXPECT_NE(ctx_->handle(), nullptr);
}

TEST_F(ZmqTransportTest, PubSubBasic) {
  Publisher pub(*ctx_);
  Subscriber sub(*ctx_);

  pub.bind("inproc://test_pubsub");
  sub.connect("inproc://test_pubsub");
  sub.subscribe("");

  // Allow connection to establish
  std::this_thread::sleep_for(std::chrono::milliseconds(10));

  EXPECT_TRUE(pub.publish("topic", "hello"));

  std::string topic, data;
  sub.set_recv_timeout(100);
  bool received = sub.recv_with_topic(topic, data);

  if (received) {
    EXPECT_EQ(topic, "topic");
    EXPECT_EQ(data, "hello");
  }
}

TEST_F(ZmqTransportTest, ReqRepBasic) {
  Replier rep(*ctx_);
  Requester req(*ctx_);

  rep.bind("inproc://test_reqrep");
  req.connect("inproc://test_reqrep");

  // Allow connection
  std::this_thread::sleep_for(std::chrono::milliseconds(10));

  // Start replier in background
  std::thread replier_thread([&rep]() {
    rep.set_recv_timeout(500);
    ZmqMessage msg;
    if (rep.recv(msg)) {
      rep.send("pong");
    }
  });

  req.set_recv_timeout(500);
  req.set_send_timeout(500);
  std::string response = req.request("ping");

  replier_thread.join();

  EXPECT_EQ(response, "pong");
}

TEST_F(ZmqTransportTest, MessageConstruction) {
  ZmqMessage msg1;
  EXPECT_EQ(msg1.size(), 0);

  ZmqMessage msg2(100);
  EXPECT_EQ(msg2.size(), 100);

  std::string str = "test message";
  ZmqMessage msg3(str);
  EXPECT_EQ(msg3.size(), str.size());
  EXPECT_EQ(msg3.to_string(), str);
}

TEST_F(ZmqTransportTest, MessageMove) {
  std::string original = "test data";
  ZmqMessage msg1(original);

  ZmqMessage msg2 = std::move(msg1);
  EXPECT_EQ(msg2.to_string(), original);
}

TEST_F(ZmqTransportTest, PollerBasic) {
  Subscriber sub(*ctx_);
  sub.connect("inproc://test_poller");
  sub.subscribe("");
  sub.set_recv_timeout(10);

  Poller poller;
  poller.add(sub);

  EXPECT_EQ(poller.size(), 1);

  int result = poller.poll(10); // 10ms timeout
  EXPECT_GE(result, 0);
}

TEST_F(ZmqTransportTest, SocketOptions) {
  Publisher pub(*ctx_);

  pub.set_linger(0);
  pub.set_send_timeout(100);
  pub.set_high_water_mark(1000);

  // No assertion - just verify no exceptions
  SUCCEED();
}

int main(int argc, char **argv) {
  ::testing::InitGoogleTest(&argc, argv);
  return RUN_ALL_TESTS();
}
