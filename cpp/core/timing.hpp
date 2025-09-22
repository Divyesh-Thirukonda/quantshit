#pragma once

/**
 * High-Resolution Timing Utilities
 *
 * Provides nanosecond-precision timing for latency measurement,
 * jitter analysis, and performance profiling.
 */

#include <algorithm>
#include <chrono>
#include <cmath>
#include <cstdint>
#include <iomanip>
#include <sstream>
#include <string>
#include <vector>

namespace quantshit {

using Clock = std::chrono::steady_clock;
using TimePoint = Clock::time_point;
using Duration = Clock::duration;
using Nanoseconds = std::chrono::nanoseconds;
using Microseconds = std::chrono::microseconds;
using Milliseconds = std::chrono::milliseconds;

/**
 * Get current high-resolution timestamp
 */
inline TimePoint now() noexcept { return Clock::now(); }

/**
 * Get timestamp as nanoseconds since epoch
 */
inline int64_t now_ns() noexcept {
  return std::chrono::duration_cast<Nanoseconds>(
             Clock::now().time_since_epoch())
      .count();
}

/**
 * Get timestamp as microseconds since epoch
 */
inline int64_t now_us() noexcept {
  return std::chrono::duration_cast<Microseconds>(
             Clock::now().time_since_epoch())
      .count();
}

/**
 * Convert duration to nanoseconds
 */
inline int64_t to_ns(Duration d) noexcept {
  return std::chrono::duration_cast<Nanoseconds>(d).count();
}

/**
 * Convert duration to microseconds
 */
inline int64_t to_us(Duration d) noexcept {
  return std::chrono::duration_cast<Microseconds>(d).count();
}

/**
 * RAII-style scope timer for measuring code block execution time
 */
class ScopeTimer {
public:
  explicit ScopeTimer(int64_t &output_ns) : start_(now()), output_(output_ns) {}

  ~ScopeTimer() { output_ = to_ns(now() - start_); }

  // Non-copyable
  ScopeTimer(const ScopeTimer &) = delete;
  ScopeTimer &operator=(const ScopeTimer &) = delete;

private:
  TimePoint start_;
  int64_t &output_;
};

/**
 * Latency statistics calculator
 * Tracks min, max, mean, percentiles, and jitter
 */
class LatencyStats {
public:
  explicit LatencyStats(size_t reserve_size = 10000) {
    samples_.reserve(reserve_size);
  }

  void record(int64_t latency_ns) {
    samples_.push_back(latency_ns);
    sum_ += latency_ns;

    if (latency_ns < min_)
      min_ = latency_ns;
    if (latency_ns > max_)
      max_ = latency_ns;
  }

  void record(Duration d) { record(to_ns(d)); }

  size_t count() const { return samples_.size(); }
  int64_t min() const { return min_; }
  int64_t max() const { return max_; }

  double mean() const {
    if (samples_.empty())
      return 0.0;
    return static_cast<double>(sum_) / samples_.size();
  }

  double stddev() const {
    if (samples_.size() < 2)
      return 0.0;

    double m = mean();
    double sq_sum = 0.0;
    for (int64_t s : samples_) {
      double d = s - m;
      sq_sum += d * d;
    }
    return std::sqrt(sq_sum / (samples_.size() - 1));
  }

  int64_t percentile(double p) {
    if (samples_.empty())
      return 0;

    // Lazy sort
    if (!sorted_) {
      std::sort(samples_.begin(), samples_.end());
      sorted_ = true;
    }

    size_t idx = static_cast<size_t>(p * (samples_.size() - 1));
    return samples_[idx];
  }

  int64_t p50() { return percentile(0.50); }
  int64_t p90() { return percentile(0.90); }
  int64_t p95() { return percentile(0.95); }
  int64_t p99() { return percentile(0.99); }
  int64_t p999() { return percentile(0.999); }

  /**
   * Calculate jitter (variation in latency)
   * Defined as stddev / mean
   */
  double jitter() const {
    double m = mean();
    if (m == 0.0)
      return 0.0;
    return stddev() / m;
  }

  void reset() {
    samples_.clear();
    sum_ = 0;
    min_ = INT64_MAX;
    max_ = 0;
    sorted_ = false;
  }

  std::string summary() {
    std::ostringstream ss;
    ss << std::fixed << std::setprecision(2);
    ss << "n=" << count() << " min=" << min() << "ns"
       << " max=" << max() << "ns"
       << " mean=" << mean() << "ns"
       << " p50=" << p50() << "ns"
       << " p99=" << p99() << "ns"
       << " jitter=" << (jitter() * 100) << "%";
    return ss.str();
  }

private:
  std::vector<int64_t> samples_;
  int64_t sum_ = 0;
  int64_t min_ = INT64_MAX;
  int64_t max_ = 0;
  bool sorted_ = false;
};

/**
 * Measure execution time of a callable
 */
template <typename Func> int64_t measure_ns(Func &&func) {
  auto start = now();
  std::forward<Func>(func)();
  return to_ns(now() - start);
}

/**
 * Run a function multiple times and collect statistics
 */
template <typename Func>
LatencyStats benchmark(Func &&func, size_t iterations) {
  LatencyStats stats(iterations);

  for (size_t i = 0; i < iterations; ++i) {
    int64_t latency = measure_ns(std::forward<Func>(func));
    stats.record(latency);
  }

  return stats;
}

/**
 * Busy-wait for a specified duration
 * More precise than sleep for short durations
 */
inline void busy_wait_ns(int64_t nanoseconds) {
  auto end = now() + Nanoseconds(nanoseconds);
  while (now() < end) {
    // Spin
  }
}

inline void busy_wait_us(int64_t microseconds) {
  busy_wait_ns(microseconds * 1000);
}

/**
 * RDTSC-based timing (x86 only, not portable but faster)
 */
#if defined(__x86_64__) || defined(_M_X64)
inline uint64_t rdtsc() {
  uint32_t lo, hi;
  __asm__ __volatile__("rdtsc" : "=a"(lo), "=d"(hi));
  return (static_cast<uint64_t>(hi) << 32) | lo;
}

inline uint64_t rdtscp() {
  uint32_t lo, hi, aux;
  __asm__ __volatile__("rdtscp" : "=a"(lo), "=d"(hi), "=c"(aux));
  return (static_cast<uint64_t>(hi) << 32) | lo;
}
#endif

} // namespace quantshit
