#include "cpu_utils.hpp"

// Most functionality is in the header, this file provides any
// non-inline implementations and explicit instantiations

namespace quantshit {

// Platform-specific implementations that need .cpp file

#ifdef __APPLE__
#include <mach/mach.h>
#include <mach/thread_policy.h>
#endif

} // namespace quantshit
