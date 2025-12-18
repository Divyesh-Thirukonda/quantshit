/**
 * End-to-End Latency Benchmark
 *
 * Measures the complete path from market data reception to order submission.
 */

#include <iomanip>
#include <iostream>

#include "../core/cpu_utils.hpp"
#include "../core/lock_free_queue.hpp"
#include "../core/timing.hpp"
#include "../engine/execution_engine.hpp"
#include "../engine/market_data_handler.hpp"

using namespace quantshit;

void benchmark_market_data_to_order() {
  std::cout << "\n=== Market Data to Order Latency ===\n";

  // Configure with CPU pinning if available
  MarketDataHandler::Config md_config;
  md_config.handler_thread_core = -1; // No pinning in benchmark

  ExecutionEngine::Config exec_config;
  exec_config.order_thread_core = -1;

  MarketDataHandler market_data(md_config);
  ExecutionEngine engine(exec_config);

  market_data.start();
  engine.start();

  LatencyStats e2e_stats;
  const int num_samples = 100000;

  for (int i = 0; i < num_samples; ++i) {
    int64_t start = now_ns();

    // Simulate market data update
    MarketDataUpdate update;
    update.market_id = "TEST_MARKET";
    update.source = Protocol::KALSHI_WS;
    update.bid_price = 0.50;
    update.ask_price = 0.52;
    update.bid_size = 1000;
    update.ask_size = 1000;
    update.timestamp_ns = start;

    // Feed to market data handler
    market_data.on_message(update);

    // Wait for quote to be available (simulate processing)
    while (!market_data.get_quote("TEST_MARKET")) {
      std::this_thread::yield();
    }

    // Submit order based on quote
    OrderRequest request;
    request.market_id = "TEST_MARKET";
    request.venue = Protocol::KALSHI_WS;
    request.side = Side::BUY;
    request.type = OrderType::LIMIT;
    request.price = 0.51;
    request.quantity = 10;

    engine.submit_order(request);

    int64_t end = now_ns();
    e2e_stats.record(end - start);
  }

  market_data.stop();
  engine.stop();

  std::cout << "End-to-end latency (MD update -> order submitted):\n";
  std::cout << "  " << e2e_stats.summary() << "\n";
}

void benchmark_cpu_pinning_impact() {
  std::cout << "\n=== CPU Pinning Impact ===\n";

  // Test with and without CPU pinning
  for (bool with_pinning : {false, true}) {
    LockFreeQueue<int64_t, 65536> queue;
    LatencyStats stats;
    const int num_samples = 500000;

    std::thread worker([&]() {
      if (with_pinning) {
        auto result = pin_to_core(0);
        if (!result.success) {
          std::cout << "Warning: Could not pin to core: " << result.message
                    << "\n";
        }
      }

      for (int i = 0; i < num_samples; ++i) {
        int64_t start = now_ns();
        queue.try_push(i);
        queue.try_pop();
        stats.record(now_ns() - start);
      }
    });

    worker.join();

    std::cout << (with_pinning ? "With" : "Without") << " CPU pinning:\n";
    std::cout << "  " << stats.summary() << "\n";
  }
}

void benchmark_timing_resolution() {
  std::cout << "\n=== Timing Resolution ===\n";

  // Measure resolution of timing functions
  LatencyStats resolution_stats;

  for (int i = 0; i < 100000; ++i) {
    int64_t t1 = now_ns();
    int64_t t2 = now_ns();
    if (t2 > t1) {
      resolution_stats.record(t2 - t1);
    }
  }

  std::cout << "now_ns() resolution:\n";
  std::cout << "  " << resolution_stats.summary() << "\n";

#if defined(__x86_64__)
  // Test RDTSC
  LatencyStats rdtsc_stats;
  for (int i = 0; i < 100000; ++i) {
    uint64_t t1 = rdtsc();
    uint64_t t2 = rdtsc();
    if (t2 > t1) {
      rdtsc_stats.record(t2 - t1);
    }
  }
  std::cout << "RDTSC resolution (cycles):\n";
  std::cout << "  " << rdtsc_stats.summary() << "\n";
#endif
}

int main() {
  std::cout << "=====================================\n";
  std::cout << "  End-to-End Latency Benchmark\n";
  std::cout << "=====================================\n";
  std::cout << "CPU cores available: " << get_num_cores() << "\n";

  benchmark_timing_resolution();
  benchmark_cpu_pinning_impact();
  benchmark_market_data_to_order();

  std::cout << "\nBenchmark complete!\n";
  return 0;
}
