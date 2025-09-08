#include "lock_free_queue.hpp"

// Header-only implementation, this file exists for CMake source list
namespace quantshit {
// Explicit template instantiations for common types to reduce compile times
template class LockFreeQueue<int64_t, 65536>;
template class LockFreeQueue<double, 65536>;
template class MPSCQueue<int64_t, 65536>;
template class MPSCQueue<double, 65536>;
} // namespace quantshit
