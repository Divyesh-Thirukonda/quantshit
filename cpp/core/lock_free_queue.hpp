#pragma once

/**
 * Lock-Free Single-Producer Single-Consumer (SPSC) Queue
 * 
 * High-performance queue for inter-thread communication with zero contention.
 * Uses cache-line padding to prevent false sharing between producer and consumer.
 * 
 * Design decisions:
 * - Fixed capacity (power of 2) for fast modulo via bitwise AND
 * - Separate cache lines for head/tail to eliminate false sharing
 * - Memory ordering: relaxed loads, release stores for optimal performance
 * - Wait-free operations: try_push/try_pop never block
 */

#include <atomic>
#include <cstddef>
#include <memory>
#include <optional>
#include <new>

namespace quantshit {

// Cache line size for x86-64
static constexpr size_t CACHE_LINE_SIZE = 64;

template<typename T, size_t Capacity = 65536>
class LockFreeQueue {
    static_assert((Capacity & (Capacity - 1)) == 0, "Capacity must be power of 2");
    static_assert(Capacity > 0, "Capacity must be positive");

public:
    LockFreeQueue() : head_(0), tail_(0) {
        // Pre-allocate buffer aligned to cache line
        buffer_ = std::make_unique<Slot[]>(Capacity);
    }

    ~LockFreeQueue() = default;

    // Non-copyable, non-movable (pointers are shared between threads)
    LockFreeQueue(const LockFreeQueue&) = delete;
    LockFreeQueue& operator=(const LockFreeQueue&) = delete;
    LockFreeQueue(LockFreeQueue&&) = delete;
    LockFreeQueue& operator=(LockFreeQueue&&) = delete;

    /**
     * Try to push an element (producer only)
     * @return true if push succeeded, false if queue is full
     */
    template<typename U>
    bool try_push(U&& value) noexcept {
        const size_t current_tail = tail_.load(std::memory_order_relaxed);
        const size_t next_tail = (current_tail + 1) & MASK;
        
        // Check if queue is full
        if (next_tail == head_.load(std::memory_order_acquire)) {
            return false;
        }
        
        // Store the value
        buffer_[current_tail].data = std::forward<U>(value);
        
        // Publish to consumer
        tail_.store(next_tail, std::memory_order_release);
        return true;
    }

    /**
     * Try to pop an element (consumer only)
     * @return optional containing value if pop succeeded, empty if queue is empty
     */
    std::optional<T> try_pop() noexcept {
        const size_t current_head = head_.load(std::memory_order_relaxed);
        
        // Check if queue is empty
        if (current_head == tail_.load(std::memory_order_acquire)) {
            return std::nullopt;
        }
        
        // Read the value
        T value = std::move(buffer_[current_head].data);
        
        // Advance head
        head_.store((current_head + 1) & MASK, std::memory_order_release);
        return value;
    }

    /**
     * Check if queue is empty (approximate, may race)
     */
    bool empty() const noexcept {
        return head_.load(std::memory_order_relaxed) == 
               tail_.load(std::memory_order_relaxed);
    }

    /**
     * Get approximate size (may race with concurrent operations)
     */
    size_t size() const noexcept {
        const size_t head = head_.load(std::memory_order_relaxed);
        const size_t tail = tail_.load(std::memory_order_relaxed);
        return (tail - head) & MASK;
    }

    /**
     * Get maximum capacity
     */
    static constexpr size_t capacity() noexcept {
        return Capacity - 1;  // One slot reserved for full/empty distinction
    }

private:
    static constexpr size_t MASK = Capacity - 1;

    struct Slot {
        T data;
    };

    // Separate cache lines for producer and consumer indices
    alignas(CACHE_LINE_SIZE) std::atomic<size_t> head_;
    alignas(CACHE_LINE_SIZE) std::atomic<size_t> tail_;
    alignas(CACHE_LINE_SIZE) std::unique_ptr<Slot[]> buffer_;
};

/**
 * Multi-Producer Single-Consumer (MPSC) Queue variant
 * Uses compare-and-swap for thread-safe multi-producer push
 */
template<typename T, size_t Capacity = 65536>
class MPSCQueue {
    static_assert((Capacity & (Capacity - 1)) == 0, "Capacity must be power of 2");

public:
    MPSCQueue() : head_(0), tail_(0) {
        buffer_ = std::make_unique<Slot[]>(Capacity);
        for (size_t i = 0; i < Capacity; ++i) {
            buffer_[i].sequence.store(i, std::memory_order_relaxed);
        }
    }

    template<typename U>
    bool try_push(U&& value) noexcept {
        size_t pos;
        Slot* slot;
        
        while (true) {
            pos = tail_.load(std::memory_order_relaxed);
            slot = &buffer_[pos & MASK];
            size_t seq = slot->sequence.load(std::memory_order_acquire);
            
            intptr_t diff = static_cast<intptr_t>(seq) - static_cast<intptr_t>(pos);
            
            if (diff == 0) {
                if (tail_.compare_exchange_weak(pos, pos + 1, std::memory_order_relaxed)) {
                    break;
                }
            } else if (diff < 0) {
                return false;  // Queue full
            }
            // else retry
        }
        
        slot->data = std::forward<U>(value);
        slot->sequence.store(pos + 1, std::memory_order_release);
        return true;
    }

    std::optional<T> try_pop() noexcept {
        size_t pos = head_.load(std::memory_order_relaxed);
        Slot* slot = &buffer_[pos & MASK];
        size_t seq = slot->sequence.load(std::memory_order_acquire);
        
        intptr_t diff = static_cast<intptr_t>(seq) - static_cast<intptr_t>(pos + 1);
        
        if (diff < 0) {
            return std::nullopt;  // Queue empty
        }
        
        T value = std::move(slot->data);
        slot->sequence.store(pos + Capacity, std::memory_order_release);
        head_.store(pos + 1, std::memory_order_relaxed);
        return value;
    }

private:
    static constexpr size_t MASK = Capacity - 1;

    struct Slot {
        std::atomic<size_t> sequence;
        T data;
    };

    alignas(CACHE_LINE_SIZE) std::atomic<size_t> head_;
    alignas(CACHE_LINE_SIZE) std::atomic<size_t> tail_;
    alignas(CACHE_LINE_SIZE) std::unique_ptr<Slot[]> buffer_;
};

} // namespace quantshit
