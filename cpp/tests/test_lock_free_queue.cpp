/**
 * Lock-Free Queue Unit Tests
 *
 * Tests for SPSC and MPSC queue implementations.
 */

#include <atomic>
#include <gtest/gtest.h>
#include <thread>
#include <vector>

#include "../core/lock_free_queue.hpp"
#include "../core/timing.hpp"

using namespace quantshit;

class LockFreeQueueTest : public ::testing::Test {
protected:
  void SetUp() override {}
  void TearDown() override {}
};

// Basic SPSC Queue Tests

TEST_F(LockFreeQueueTest, SPSCBasicPushPop) {
  LockFreeQueue<int, 1024> queue;

  EXPECT_TRUE(queue.empty());
  EXPECT_EQ(queue.size(), 0);

  EXPECT_TRUE(queue.try_push(42));
  EXPECT_FALSE(queue.empty());
  EXPECT_EQ(queue.size(), 1);

  auto result = queue.try_pop();
  EXPECT_TRUE(result.has_value());
  EXPECT_EQ(*result, 42);
  EXPECT_TRUE(queue.empty());
}

TEST_F(LockFreeQueueTest, SPSCMultiplePushPop) {
  LockFreeQueue<int, 1024> queue;

  for (int i = 0; i < 100; ++i) {
    EXPECT_TRUE(queue.try_push(i));
  }

  EXPECT_EQ(queue.size(), 100);

  for (int i = 0; i < 100; ++i) {
    auto result = queue.try_pop();
    EXPECT_TRUE(result.has_value());
    EXPECT_EQ(*result, i);
  }

  EXPECT_TRUE(queue.empty());
}

TEST_F(LockFreeQueueTest, SPSCFullQueue) {
  LockFreeQueue<int, 16> queue; // Capacity 15 (one slot reserved)

  // Fill the queue
  for (int i = 0; i < 15; ++i) {
    EXPECT_TRUE(queue.try_push(i));
  }

  // Queue should be full
  EXPECT_FALSE(queue.try_push(999));

  // Pop one and push again
  queue.try_pop();
  EXPECT_TRUE(queue.try_push(999));
}

TEST_F(LockFreeQueueTest, SPSCEmptyPop) {
  LockFreeQueue<int, 1024> queue;

  auto result = queue.try_pop();
  EXPECT_FALSE(result.has_value());
}

TEST_F(LockFreeQueueTest, SPSCMoveSemantics) {
  LockFreeQueue<std::string, 1024> queue;

  std::string str = "Hello, World!";
  EXPECT_TRUE(queue.try_push(std::move(str)));

  auto result = queue.try_pop();
  EXPECT_TRUE(result.has_value());
  EXPECT_EQ(*result, "Hello, World!");
}

// SPSC Multi-threaded Tests

TEST_F(LockFreeQueueTest, SPSCProducerConsumer) {
  LockFreeQueue<int, 65536> queue;
  const int num_items = 100000;
  std::atomic<int> consumed_count{0};
  std::atomic<int64_t> checksum{0};

  // Producer thread
  std::thread producer([&]() {
    for (int i = 0; i < num_items; ++i) {
      while (!queue.try_push(i)) {
        std::this_thread::yield();
      }
    }
  });

  // Consumer thread
  std::thread consumer([&]() {
    int count = 0;
    int64_t sum = 0;
    while (count < num_items) {
      auto result = queue.try_pop();
      if (result) {
        sum += *result;
        ++count;
      } else {
        std::this_thread::yield();
      }
    }
    consumed_count = count;
    checksum = sum;
  });

  producer.join();
  consumer.join();

  EXPECT_EQ(consumed_count.load(), num_items);

  // Expected sum: 0 + 1 + 2 + ... + (n-1) = n*(n-1)/2
  int64_t expected_sum = static_cast<int64_t>(num_items) * (num_items - 1) / 2;
  EXPECT_EQ(checksum.load(), expected_sum);
}

// MPSC Queue Tests

TEST_F(LockFreeQueueTest, MPSCBasicPushPop) {
  MPSCQueue<int, 1024> queue;

  EXPECT_TRUE(queue.try_push(42));

  auto result = queue.try_pop();
  EXPECT_TRUE(result.has_value());
  EXPECT_EQ(*result, 42);
}

TEST_F(LockFreeQueueTest, MPSCMultiProducer) {
  MPSCQueue<int, 65536> queue;
  const int num_producers = 4;
  const int items_per_producer = 10000;
  std::atomic<int> consumed_count{0};

  std::vector<std::thread> producers;

  // Start producers
  for (int p = 0; p < num_producers; ++p) {
    producers.emplace_back([&, p]() {
      for (int i = 0; i < items_per_producer; ++i) {
        int value = p * items_per_producer + i;
        while (!queue.try_push(value)) {
          std::this_thread::yield();
        }
      }
    });
  }

  // Consumer thread
  std::thread consumer([&]() {
    int target = num_producers * items_per_producer;
    int count = 0;
    while (count < target) {
      auto result = queue.try_pop();
      if (result) {
        ++count;
      } else {
        std::this_thread::yield();
      }
    }
    consumed_count = count;
  });

  for (auto &t : producers) {
    t.join();
  }
  consumer.join();

  EXPECT_EQ(consumed_count.load(), num_producers * items_per_producer);
}

// Performance Tests

TEST_F(LockFreeQueueTest, SPSCThroughput) {
  LockFreeQueue<int64_t, 65536> queue;
  const int num_items = 1000000;
  LatencyStats push_stats, pop_stats;

  // Measure push latency
  for (int i = 0; i < 10000; ++i) {
    int64_t start = now_ns();
    queue.try_push(i);
    push_stats.record(now_ns() - start);
  }

  // Clear queue
  while (queue.try_pop()) {
  }

  // Fill queue then measure pop latency
  for (int i = 0; i < 10000; ++i) {
    queue.try_push(i);
  }

  for (int i = 0; i < 10000; ++i) {
    int64_t start = now_ns();
    queue.try_pop();
    pop_stats.record(now_ns() - start);
  }

  std::cout << "Push latency: " << push_stats.summary() << std::endl;
  std::cout << "Pop latency: " << pop_stats.summary() << std::endl;

  // Assert reasonable latency (under 1us for p99)
  EXPECT_LT(push_stats.p99(), 1000);
  EXPECT_LT(pop_stats.p99(), 1000);
}

TEST_F(LockFreeQueueTest, QueueCapacity) {
  LockFreeQueue<int, 1024> queue;
  EXPECT_EQ(queue.capacity(), 1023); // One slot reserved

  LockFreeQueue<int, 65536> large_queue;
  EXPECT_EQ(large_queue.capacity(), 65535);
}

int main(int argc, char **argv) {
  ::testing::InitGoogleTest(&argc, argv);
  return RUN_ALL_TESTS();
}
