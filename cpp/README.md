# Quantshit C++ Execution Engine

High-performance C++ execution layer for real-time predictive market arbitrage.

## Features

- **Lock-Free Queues**: SPSC and MPSC queues with cache-line padding
- **CPU Pinning**: Thread affinity and real-time scheduling for minimal jitter
- **ZeroMQ Transport**: High-frequency pub/sub and req/rep messaging
- **Packet Normalization**: Protocol-specific parsers for Kalshi/Polymarket
- **Execution Engine**: Order management with risk checks
- **Python Bindings**: pybind11 integration with existing ArbitrageBot

## Requirements

- C++17 compatible compiler (GCC 8+, Clang 7+)
- CMake 3.16+
- ZeroMQ 4.x
- pybind11 (optional, for Python bindings)
- Google Test (optional, for tests)

## Building

```bash
# Install dependencies (macOS)
brew install zeromq pybind11 googletest

# Install dependencies (Ubuntu)
sudo apt install libzmq3-dev pybind11-dev libgtest-dev

# Build
mkdir build && cd build
cmake ..
make -j$(nproc)
```

## Usage

### C++ Direct Usage

```cpp
#include "engine/execution_engine.hpp"
#include "engine/market_data_handler.hpp"

using namespace quantshit;

// Configure engine with CPU pinning
ExecutionEngine::Config config;
config.order_thread_core = 2;  // Pin to core 2
config.risk_limits.max_order_size = 10000;

ExecutionEngine engine(config);
engine.start();

// Submit order
OrderRequest request;
request.market_id = "KALSHI_TRUMP_2024";
request.venue = Protocol::KALSHI_WS;
request.side = Side::BUY;
request.price = 0.55;
request.quantity = 100;

engine.submit_order(request);
```

### Python Integration

```python
from quantshit_engine import engine, core

# Initialize engine
config = engine.ExecutionEngineConfig()
config.order_thread_core = 2

exec_engine = engine.ExecutionEngine(config)
exec_engine.start()

# Submit order from Python
request = engine.OrderRequest()
request.market_id = "KALSHI_TRUMP_2024"
request.venue = engine.Protocol.KALSHI_WS
request.side = engine.Side.BUY
request.price = 0.55
request.quantity = 100

exec_engine.submit_order(request)
```

## Benchmarks

Run benchmarks to verify performance:

```bash
./build/queue_benchmark
./build/latency_benchmark
```

Typical results on modern hardware:
- SPSC Queue: 20M+ ops/sec, <50ns p99 latency
- MPSC Queue: 10M+ ops/sec with 4 producers
- End-to-end: <1μs from market data to order

## Architecture

```
cpp/
├── core/               # Core utilities
│   ├── lock_free_queue.hpp
│   ├── cpu_utils.hpp
│   └── timing.hpp
├── network/            # Network layer
│   ├── zmq_transport.hpp
│   ├── packet_normalizer.hpp
│   └── market_protocol.hpp
├── engine/             # Execution engine
│   ├── execution_engine.hpp
│   ├── market_data_handler.hpp
│   ├── order_router.hpp
│   └── arbitrage_detector.hpp
├── bindings/           # Python bindings
│   └── python_module.cpp
├── tests/              # Unit tests
└── benchmarks/         # Performance tests
```
