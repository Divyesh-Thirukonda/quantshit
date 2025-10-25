# Quantshit - Cross-Venue Arbitrage Engine

A high-performance arbitrage trading system for prediction markets. Automatically detects and executes profitable trades across Polymarket and Kalshi.

## Quick Start

```bash
git clone https://github.com/Divyesh-Thirukonda/quantshit.git
cd quantshit
pip install -r requirements.txt
python main.py  # Start paper trading mode
```

## System Overview

Quantshit is a **3-layer architecture** designed for speed and reliability:

**Data Pipeline** → **Strategy Engine** → **Execution Engine**

1. **Data Pipeline**: Collects real-time market data from multiple platforms
2. **Strategy Engine**: Detects arbitrage opportunities using advanced matching algorithms  
3. **Execution Engine**: Places orders, tracks positions, manages risk

**Current Status**: Live paper trading with $20,123 portfolio value, executing ~2 opportunities per cycle.

## Architecture Tour

### 🔄 Data Pipeline Layer
- **`src/collectors/`** - Multi-platform market data aggregation
- **`src/platforms/`** - Platform-specific API adapters (Polymarket, Kalshi)
- **`src/adapters.py`** - Unified data format conversion

### 🧠 Strategy Engine Layer  
- **`src/strategies/arbitrage.py`** - Opportunity detection algorithms
- **`src/utils/advanced_matching.py`** - Smart market matching logic
- **`src/engine/event_driven.py`** - Real-time strategy execution

### ⚡ Execution Engine Layer
- **`src/executors/`** - Order placement and management
- **`src/engine/position_manager.py`** - Position sizing, stop-loss, take-profit
- **`src/trackers/`** - Portfolio and trade tracking
- **`src/coordinators/`** - High-level execution coordination

## Directory Structure

```
quantshit/
├── src/
│   ├── collectors/          # 📊 Market data collection
│   │   └── market_data_collector.py
│   ├── strategies/          # 🎯 Trading strategies  
│   │   ├── arbitrage.py     # Core arbitrage detection
│   │   └── planning.py      # Strategy planning
│   ├── executors/           # ⚡ Order execution
│   │   └── order_executor.py
│   ├── engine/              # 🔧 Core engine components
│   │   ├── bot.py           # Main trading bot
│   │   ├── position_manager.py  # Position management
│   │   └── event_driven.py  # Event processing
│   ├── coordinators/        # 🎛️ High-level coordination
│   │   ├── trading_orchestrator.py  # Main orchestrator
│   │   └── execution_coordinator.py # Execution management
│   ├── trackers/            # 📈 Portfolio tracking
│   │   └── portfolio_tracker.py
│   ├── platforms/           # 🔌 Platform integrations
│   │   ├── base.py          # Base platform interface
│   │   ├── kalshi.py        # Kalshi API integration
│   │   ├── polymarket.py    # Polymarket API integration
│   │   └── registry.py      # Platform registry
│   ├── utils/               # 🛠️ Utilities
│   │   └── advanced_matching.py
│   ├── types.py             # 📋 Type definitions
│   └── adapters.py          # 🔄 Data adapters
├── api/                     # 🌐 REST API
│   └── index.py
├── tests/                   # ✅ Comprehensive test suite
├── main.py                  # 🚀 CLI entry point
├── api.py                   # 🌐 FastAPI server
└── requirements.txt
```

## Development Guide

### For Data Pipeline Developers
- Work in `src/collectors/` and `src/platforms/`
- Add new exchanges in `src/platforms/`
- Extend data collection in `src/collectors/market_data_collector.py`

### For Strategy Developers  
- Extend `src/strategies/arbitrage.py` for new detection algorithms
- Modify `src/utils/advanced_matching.py` for better market matching
- Add new strategies in `src/strategies/`

### For Execution Developers
- Enhance `src/executors/order_executor.py` for order management
- Improve `src/engine/position_manager.py` for risk controls
- Extend `src/trackers/portfolio_tracker.py` for better tracking

## Running Tests

```bash
# Run all tests
python -m pytest tests/ -v

# Run specific component tests  
python -m pytest tests/test_strategies.py -v
python -m pytest tests/test_executors.py -v
python -m pytest tests/test_integration.py -v
```

**Test Coverage**: 68 tests covering all components - collectors, strategies, executors, trackers, position management, and end-to-end integration.

## Configuration

Set environment variables in `.env`:
```bash
KALSHI_API_KEY=your_key
POLYMARKET_API_KEY=your_key  
MIN_SPREAD=0.05        # Minimum profitable spread
MIN_VOLUME=1000        # Minimum market volume
```

## API Server

```bash
python api.py  # Starts on http://localhost:8000
```

**Endpoints**: `/portfolio`, `/opportunities`, `/run-cycle`

## Contributing

1. Pick a layer (Data/Strategy/Execution)
2. Check existing tests for examples
3. Add tests for new features
4. Ensure `python -m pytest tests/ -v` passes
5. Submit PR

**Current Focus Areas**: 
- 📊 New exchange integrations
- 🧠 Advanced opportunity detection  
- ⚡ Execution optimization
- 🛡️ Enhanced risk management

---
**⚠️ Paper Trading Only**: Currently configured for simulation. Real trading requires API key setup and risk management review.