cmake_minimum_required(VERSION 3.16)
project(quantshit_engine VERSION 1.0.0 LANGUAGES CXX)

set(CMAKE_CXX_STANDARD 17)
set(CMAKE_CXX_STANDARD_REQUIRED ON)
set(CMAKE_EXPORT_COMPILE_COMMANDS ON)

# Build options
option(BUILD_TESTS "Build unit tests" OFF)
option(BUILD_BENCHMARKS "Build benchmarks" ON)
option(BUILD_PYTHON_BINDINGS "Build Python bindings" OFF)
option(USE_ZMQ "Use ZeroMQ for networking (requires libzmq)" OFF)

# Find dependencies
find_package(Threads REQUIRED)

# ZMQ is optional - only needed for real network communication
if(USE_ZMQ)
    find_package(PkgConfig QUIET)
    if(PkgConfig_FOUND)
        pkg_check_modules(ZMQ libzmq)
    endif()
    if(NOT ZMQ_FOUND)
        message(WARNING "ZeroMQ not found. Building without ZMQ support.")
        set(USE_ZMQ OFF)
    endif()
endif()

# Core library (header-only components work without ZMQ)
set(CORE_SOURCES
    core/lock_free_queue.cpp
    core/cpu_utils.cpp
    core/timing.cpp
    engine/execution_engine.cpp
    engine/market_data_handler.cpp
    engine/order_router.cpp
    engine/arbitrage_detector.cpp
)

# Add ZMQ-dependent sources only if ZMQ is available
if(USE_ZMQ)
    list(APPEND CORE_SOURCES
        network/zmq_transport.cpp
        network/packet_normalizer.cpp
        network/market_protocol.cpp
    )
endif()

add_library(quantengine STATIC ${CORE_SOURCES})

target_include_directories(quantengine PUBLIC
    ${CMAKE_CURRENT_SOURCE_DIR}
)

target_link_libraries(quantengine PUBLIC
    Threads::Threads
)

# Add ZMQ if available
if(USE_ZMQ)
    target_include_directories(quantengine PUBLIC ${ZMQ_INCLUDE_DIRS})
    target_link_libraries(quantengine PUBLIC ${ZMQ_LIBRARIES})
    target_compile_definitions(quantengine PUBLIC HAS_ZMQ=1)
else()
    target_compile_definitions(quantengine PUBLIC HAS_ZMQ=0)
endif()

target_compile_options(quantengine PRIVATE
    -Wall -Wextra -Wpedantic
    -O3 -march=native
    -fno-omit-frame-pointer
)

# Python bindings
if(BUILD_PYTHON_BINDINGS)
    find_package(pybind11 QUIET)
    if(pybind11_FOUND)
        pybind11_add_module(quantshit_bindings bindings/python_module.cpp)
        target_link_libraries(quantshit_bindings PRIVATE quantengine)
    else()
        message(WARNING "pybind11 not found, skipping Python bindings")
    endif()
endif()

# Tests
if(BUILD_TESTS)
    enable_testing()
    find_package(GTest QUIET)
    if(GTest_FOUND)
        add_executable(test_lock_free_queue tests/test_lock_free_queue.cpp)
        target_link_libraries(test_lock_free_queue quantengine GTest::gtest_main)
        add_test(NAME LockFreeQueueTest COMMAND test_lock_free_queue)
        
        if(USE_ZMQ)
            add_executable(test_zmq_transport tests/test_zmq_transport.cpp)
            target_link_libraries(test_zmq_transport quantengine GTest::gtest_main)
            add_test(NAME ZmqTransportTest COMMAND test_zmq_transport)
        endif()
    else()
        message(WARNING "GTest not found, skipping tests")
    endif()
endif()

# Benchmarks
if(BUILD_BENCHMARKS)
    add_executable(queue_benchmark benchmarks/queue_benchmark.cpp)
    target_link_libraries(queue_benchmark quantengine)
    
    add_executable(latency_benchmark benchmarks/latency_benchmark.cpp)
    target_link_libraries(latency_benchmark quantengine)
endif()

# Demo executable with mock data (no ZMQ required)
add_executable(quantshit_demo demo/main.cpp)
target_link_libraries(quantshit_demo quantengine)

# Installation
install(TARGETS quantengine
    LIBRARY DESTINATION lib
    ARCHIVE DESTINATION lib
)

install(DIRECTORY core/ network/ engine/
    DESTINATION include/quantshit
    FILES_MATCHING PATTERN "*.hpp"
)
