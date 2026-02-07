#pragma once

/**
 * CPU Utilities for Low-Latency Trading
 *
 * Provides thread affinity (CPU pinning) and scheduling policy configuration
 * to minimize context switches and scheduling jitter.
 *
 * Key features:
 * - Pin threads to specific CPU cores
 * - Set real-time scheduling priorities (SCHED_FIFO)
 * - NUMA-aware memory allocation hints
 * - Core isolation recommendations
 */

#include <atomic>
#include <cstdint>
#include <pthread.h>
#include <sched.h>
#include <stdexcept>
#include <string>
#include <thread>
#include <unistd.h>
#include <vector>

#ifdef __linux__
#include <numa.h>
#endif

#ifdef __APPLE__
#include <mach/mach.h>
#include <mach/thread_policy.h>
#endif

namespace quantshit {

/**
 * Result of CPU pinning operation
 */
struct PinResult {
  bool success;
  int error_code;
  std::string message;

  explicit operator bool() const { return success; }
};

/**
 * CPU core information
 */
struct CoreInfo {
  int core_id;
  int numa_node;
  bool isolated;    // Is this core isolated from kernel scheduler?
  bool hyperthread; // Is this a hyperthread (SMT)?
};

/**
 * Pin current thread to a specific CPU core
 *
 * @param core_id The CPU core to pin to (0-indexed)
 * @return PinResult with success/failure information
 */
inline PinResult pin_to_core(int core_id) {
#ifdef __linux__
  cpu_set_t cpuset;
  CPU_ZERO(&cpuset);
  CPU_SET(core_id, &cpuset);

  int result =
      pthread_setaffinity_np(pthread_self(), sizeof(cpu_set_t), &cpuset);

  if (result == 0) {
    return {true, 0, "Pinned to core " + std::to_string(core_id)};
  } else {
    return {false, result, "Failed to pin to core: " + std::to_string(result)};
  }
#elif defined(__APPLE__)
  // macOS doesn't support thread affinity directly
  // Use thread_policy_set with THREAD_AFFINITY_POLICY as a hint
  thread_port_t thread = pthread_mach_thread_np(pthread_self());
  thread_affinity_policy_data_t policy = {core_id + 1};
  kern_return_t result =
      thread_policy_set(thread, THREAD_AFFINITY_POLICY,
                        (thread_policy_t)&policy, THREAD_AFFINITY_POLICY_COUNT);

  if (result == KERN_SUCCESS) {
    return {true, 0, "Affinity hint set for core " + std::to_string(core_id)};
  } else {
    return {false, static_cast<int>(result), "Failed to set affinity hint"};
  }
#else
  return {false, -1, "CPU pinning not supported on this platform"};
#endif
}

/**
 * Pin a std::thread to a specific CPU core
 */
inline PinResult pin_thread_to_core(std::thread &thread, int core_id) {
#ifdef __linux__
  cpu_set_t cpuset;
  CPU_ZERO(&cpuset);
  CPU_SET(core_id, &cpuset);

  int result = pthread_setaffinity_np(thread.native_handle(), sizeof(cpu_set_t),
                                      &cpuset);

  if (result == 0) {
    return {true, 0, "Pinned thread to core " + std::to_string(core_id)};
  } else {
    return {false, result, "Failed to pin thread: " + std::to_string(result)};
  }
#else
  return {false, -1, "Thread pinning not supported on this platform"};
#endif
}

/**
 * Set real-time scheduling for current thread
 *
 * @param priority SCHED_FIFO priority (1-99, higher = more priority)
 * @return PinResult with success/failure information
 *
 * Note: Requires CAP_SYS_NICE capability or root privileges
 */
inline PinResult set_realtime_priority(int priority) {
#ifdef __linux__
  if (priority < 1 || priority > 99) {
    return {false, -1, "Priority must be 1-99"};
  }

  struct sched_param param;
  param.sched_priority = priority;

  int result = sched_setscheduler(0, SCHED_FIFO, &param);

  if (result == 0) {
    return {true, 0, "Set SCHED_FIFO priority " + std::to_string(priority)};
  } else {
    return {false, errno, "Failed to set RT priority (need CAP_SYS_NICE?)"};
  }
#else
  return {false, -1, "Real-time scheduling not supported on this platform"};
#endif
}

/**
 * Set thread to low-latency scheduling policy
 * Combines CPU pinning with RT priority
 */
inline PinResult configure_low_latency(int core_id, int rt_priority = 50) {
  auto pin_result = pin_to_core(core_id);
  if (!pin_result) {
    return pin_result;
  }

  auto rt_result = set_realtime_priority(rt_priority);
  if (!rt_result) {
    // Pinning succeeded, but RT failed - still partially successful
    return {true, rt_result.error_code,
            pin_result.message +
                "; RT scheduling failed: " + rt_result.message};
  }

  return {true, 0, pin_result.message + "; " + rt_result.message};
}

/**
 * Get the number of available CPU cores
 */
inline int get_num_cores() {
  return static_cast<int>(std::thread::hardware_concurrency());
}

/**
 * Get the current CPU core this thread is running on
 */
inline int get_current_core() {
#ifdef __linux__
  return sched_getcpu();
#else
  return -1; // Not available on all platforms
#endif
}

/**
 * Get NUMA node for a CPU core
 */
inline int get_numa_node([[maybe_unused]] int core_id) {
#ifdef __linux__
  if (numa_available() < 0) {
    return 0; // NUMA not available, assume single node
  }
  return numa_node_of_cpu(core_id);
#else
  return 0;
#endif
}

/**
 * Get list of CPU cores in a NUMA node
 */
inline std::vector<int> get_cores_in_numa_node([[maybe_unused]] int numa_node) {
  std::vector<int> cores;

#ifdef __linux__
  if (numa_available() >= 0) {
    struct bitmask *cpumask = numa_allocate_cpumask();
    if (numa_node_to_cpus(numa_node, cpumask) >= 0) {
      for (int i = 0; i < numa_num_configured_cpus(); ++i) {
        if (numa_bitmask_isbitset(cpumask, i)) {
          cores.push_back(i);
        }
      }
    }
    numa_free_cpumask(cpumask);
  } else {
    // Fallback: return all cores
    int num_cores = get_num_cores();
    for (int i = 0; i < num_cores; ++i) {
      cores.push_back(i);
    }
  }
#else
  // Fallback: return all cores
  int num_cores = get_num_cores();
  for (int i = 0; i < num_cores; ++i) {
    cores.push_back(i);
  }
#endif

  return cores;
}

/**
 * Prefetch memory hint for cache warming
 */
template <typename T> inline void prefetch_for_read(const T *ptr) {
  __builtin_prefetch(ptr, 0, 3); // Read, high temporal locality
}

template <typename T> inline void prefetch_for_write(T *ptr) {
  __builtin_prefetch(ptr, 1, 3); // Write, high temporal locality
}

/**
 * Memory barrier utilities
 */
inline void memory_fence() {
  std::atomic_thread_fence(std::memory_order_seq_cst);
}

inline void compiler_fence() {
  std::atomic_signal_fence(std::memory_order_seq_cst);
}

} // namespace quantshit
