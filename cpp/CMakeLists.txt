cmake_minimum_required(VERSION 3.16)
project(quantshit_engine VERSION 1.0.0 LANGUAGES CXX)

set(CMAKE_CXX_STANDARD 17)
set(CMAKE_CXX_STANDARD_REQUIRED ON)
set(CMAKE_EXPORT_COMPILE_COMMANDS ON)

# Build options
option(BUILD_TESTS "Build unit tests" ON)
option(BUILD_BENCHMARKS "Build benchmarks" ON)
option(BUILD_PYTHON_BINDINGS "Build Python bindings" ON)

# Find dependencies
find_package(Threads REQUIRED)
find_package(PkgConfig REQUIRED)
pkg_check_modules(ZMQ REQUIRED libzmq)

# Core library
add_library(quantengine STATIC
    core/lock_free_queue.cpp
    core/cpu_utils.cpp
    core/timing.cpp
    network/zmq_transport.cpp
    network/packet_normalizer.cpp
    network/market_protocol.cpp
    engine/execution_engine.cpp
    engine/market_data_handler.cpp
    engine/order_router.cpp
    engine/arbitrage_detector.cpp
)

target_include_directories(quantengine PUBLIC
    ${CMAKE_CURRENT_SOURCE_DIR}
    ${ZMQ_INCLUDE_DIRS}
)

target_link_libraries(quantengine PUBLIC
    Threads::Threads
    ${ZMQ_LIBRARIES}
)

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
        
        add_executable(test_zmq_transport tests/test_zmq_transport.cpp)
        target_link_libraries(test_zmq_transport quantengine GTest::gtest_main)
        add_test(NAME ZmqTransportTest COMMAND test_zmq_transport)
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

# Installation
install(TARGETS quantengine
    LIBRARY DESTINATION lib
    ARCHIVE DESTINATION lib
)

install(DIRECTORY core/ network/ engine/
    DESTINATION include/quantshit
    FILES_MATCHING PATTERN "*.hpp"
)
