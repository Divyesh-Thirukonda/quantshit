/**
 * Lock-Free Queue Benchmark
 *
 * Measures throughput and latency of queue operations.
 */

#include <atomic>
#include <iomanip>
#include <iostream>
#include <thread>
#include <vector>

#include "../core/lock_free_queue.hpp"
#include "../core/timing.hpp"

using namespace quantshit;

void benchmark_spsc_throughput() {
  std::cout << "\n=== SPSC Queue Throughput Benchmark ===\n";

  LockFreeQueue<int64_t, 65536> queue;
  const int num_items = 10'000'000;
  std::atomic<bool> consumer_done{false};

  int64_t start = now_ns();

  std::thread producer([&]() {
    for (int i = 0; i < num_items; ++i) {
      while (!queue.try_push(i)) {
        // Spin
      }
    }
  });

  std::thread consumer([&]() {
    int count = 0;
    while (count < num_items) {
      if (queue.try_pop()) {
        ++count;
      }
    }
    consumer_done = true;
  });

  producer.join();
  consumer.join();

  int64_t elapsed_ns = now_ns() - start;
  double elapsed_sec = elapsed_ns / 1e9;
  double throughput = num_items / elapsed_sec;

  std::cout << std::fixed << std::setprecision(2);
  std::cout << "Items: " << num_items << "\n";
  std::cout << "Time: " << elapsed_sec << " seconds\n";
  std::cout << "Throughput: " << throughput / 1e6 << " M items/sec\n";
  std::cout << "Latency per item: " << elapsed_ns / num_items << " ns\n";
}

void benchmark_spsc_latency() {
  std::cout << "\n=== SPSC Queue Latency Benchmark ===\n";

  LockFreeQueue<int64_t, 65536> queue;
  const int num_samples = 1'000'000;
  LatencyStats push_stats, pop_stats, round_trip_stats;

  // Push latency (empty queue)
  for (int i = 0; i < num_samples; ++i) {
    int64_t start = now_ns();
    queue.try_push(i);
    push_stats.record(now_ns() - start);
  }

  // Pop all
  while (queue.try_pop()) {
  }

  // Pop latency (measure with pre-filled queue)
  for (int i = 0; i < num_samples; ++i) {
    queue.try_push(i);
  }

  for (int i = 0; i < num_samples; ++i) {
    int64_t start = now_ns();
    queue.try_pop();
    pop_stats.record(now_ns() - start);
  }

  // Round-trip latency
  for (int i = 0; i < num_samples; ++i) {
    int64_t start = now_ns();
    queue.try_push(i);
    queue.try_pop();
    round_trip_stats.record(now_ns() - start);
  }

  std::cout << "Push latency:\n";
  std::cout << "  " << push_stats.summary() << "\n";

  std::cout << "Pop latency:\n";
  std::cout << "  " << pop_stats.summary() << "\n";

  std::cout << "Round-trip latency:\n";
  std::cout << "  " << round_trip_stats.summary() << "\n";
}

void benchmark_mpsc_throughput() {
  std::cout << "\n=== MPSC Queue Throughput Benchmark ===\n";

  MPSCQueue<int64_t, 65536> queue;
  const int num_producers = 4;
  const int items_per_producer = 2'500'000;
  const int total_items = num_producers * items_per_producer;

  std::atomic<bool> start_flag{false};
  std::atomic<int> producer_count{0};

  int64_t start = now_ns();

  std::vector<std::thread> producers;
  for (int p = 0; p < num_producers; ++p) {
    producers.emplace_back([&, p]() {
      producer_count++;
      while (!start_flag) {
      }

      for (int i = 0; i < items_per_producer; ++i) {
        while (!queue.try_push(p * items_per_producer + i)) {
          // Spin
        }
      }
    });
  }

  std::thread consumer([&]() {
    while (producer_count < num_producers) {
    }
    start_flag = true;

    int count = 0;
    while (count < total_items) {
      if (queue.try_pop()) {
        ++count;
      }
    }
  });

  for (auto &t : producers) {
    t.join();
  }
  consumer.join();

  int64_t elapsed_ns = now_ns() - start;
  double elapsed_sec = elapsed_ns / 1e9;
  double throughput = total_items / elapsed_sec;

  std::cout << std::fixed << std::setprecision(2);
  std::cout << "Producers: " << num_producers << "\n";
  std::cout << "Total items: " << total_items << "\n";
  std::cout << "Time: " << elapsed_sec << " seconds\n";
  std::cout << "Throughput: " << throughput / 1e6 << " M items/sec\n";
}

void benchmark_contention() {
  std::cout << "\n=== Queue Contention Benchmark ===\n";

  // Compare SPSC vs MPSC under various producer counts
  const int items_total = 4'000'000;

  for (int num_producers : {1, 2, 4, 8}) {
    MPSCQueue<int64_t, 65536> queue;
    const int items_per_producer = items_total / num_producers;

    std::atomic<bool> start_flag{false};
    std::atomic<int> ready_count{0};

    int64_t start = now_ns();

    std::vector<std::thread> producers;
    for (int p = 0; p < num_producers; ++p) {
      producers.emplace_back([&]() {
        ready_count++;
        while (!start_flag) {
        }

        for (int i = 0; i < items_per_producer; ++i) {
          while (!queue.try_push(i)) {
          }
        }
      });
    }

    std::thread consumer([&]() {
      while (ready_count < num_producers) {
      }
      start_flag = true;

      int count = 0;
      while (count < items_total) {
        if (queue.try_pop())
          ++count;
      }
    });

    for (auto &t : producers)
      t.join();
    consumer.join();

    int64_t elapsed = now_ns() - start;
    double throughput = static_cast<double>(items_total) / elapsed * 1e9;

    std::cout << num_producers << " producers: " << std::fixed
              << std::setprecision(2) << throughput / 1e6 << " M items/sec\n";
  }
}

int main() {
  std::cout << "======================================\n";
  std::cout << "  Lock-Free Queue Benchmark Suite\n";
  std::cout << "======================================\n";

  benchmark_spsc_throughput();
  benchmark_spsc_latency();
  benchmark_mpsc_throughput();
  benchmark_contention();

  std::cout << "\nBenchmark complete!\n";
  return 0;
}
