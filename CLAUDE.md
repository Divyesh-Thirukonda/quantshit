# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

Quantshit is a cross-venue arbitrage engine for prediction markets. It detects and executes profitable trades across Polymarket and Kalshi using a 3-layer architecture: **Data Collection → Strategy Detection → Trade Execution**.

The system operates in paper trading mode by default and can run as a CLI tool or FastAPI web service.

## Development Commands

### Setup
```bash
pip install -r requirements.txt
cp .env.example .env  # Configure API keys
```

### Running the Bot
```bash
# Run single strategy cycle (for testing)
python main.py

# Run as API server (dashboard + REST endpoints)
python api.py  # Available at http://localhost:8000
```

### Testing
```bash
# Run all tests
python -m pytest tests/ -v

# Run specific test modules
python -m pytest tests/test_strategies.py -v
python -m pytest tests/test_executors.py -v
python -m pytest tests/test_integration.py -v
python -m pytest tests/test_collectors.py -v
python -m pytest tests/test_position_manager.py -v
python -m pytest tests/test_trading_orchestrator.py -v

# Run single test function
python -m pytest tests/test_strategies.py::test_arbitrage_detection -v
```

### Deployment
```bash
vercel  # Deploy to Vercel serverless

# Required environment variables in Vercel dashboard:
# - POLYMARKET_API_KEY
# - KALSHI_API_KEY
# - MIN_VOLUME (default: 1000)
# - MIN_SPREAD (default: 0.05)
```

## Architecture Deep Dive

### Layer 1: Data Collection (`src/collectors/`, `src/platforms/`)

**MarketDataCollector** (`src/collectors/market_data_collector.py`) aggregates data from multiple platforms using a unified interface.

**Platform Registry** (`src/platforms/registry.py`) provides the factory pattern:
- `get_market_api(platform_name, api_key)` creates platform instances
- All platforms inherit from `BaseMarketAPI` (`src/platforms/base.py`)
- Each platform implements: `get_recent_markets()`, `place_buy_order()`, `place_sell_order()`, `find_event()`
- Currently supports: `PolymarketAPI`, `KalshiAPI`

**Data Flow**: Raw platform data → Adapters (`src/adapters.py`) → Standardized `Market` objects (defined in `src/types.py`)

### Layer 2: Strategy Detection (`src/strategies/`)

**ArbitrageStrategy** (`src/strategies/arbitrage.py:23-208`) is the core strategy:
- Market matching uses word-based Jaccard similarity (threshold: 0.5) at line 130
- Detects arbitrage for both YES and NO outcomes separately
- Filters opportunities by `MIN_SPREAD` configuration
- Returns `ArbitrageOpportunity` objects (typed dataclasses from `src/types.py`)

**Strategy Registry** (`src/strategies/arbitrage.py:211-220`):
- `get_strategy(name, **kwargs)` factory function
- Current strategies: `'arbitrage'` → `ArbitrageStrategy`
- Extend by adding to `STRATEGIES` dict

### Layer 3: Trade Execution (`src/executors/`, `src/coordinators/`, `src/trackers/`)

**OrderExecutor** (`src/executors/order_executor.py`) handles low-level order placement:
- `execute_buy_order()` / `execute_sell_order()` call platform APIs
- `execute_arbitrage_legs()` executes both sides of a trade
- Single responsibility: API calls only, no portfolio tracking

**TradingOrchestrator** (`src/coordinators/trading_orchestrator.py`) is the main coordinator:
- Orchestrates the full cycle: data → strategy → execution → logging
- `run_strategy_cycle()` (line 48) is the main entry point
- Manages component lifecycle and error handling
- Provides portfolio summary and search functionality

**PortfolioTracker** (`src/trackers/portfolio_tracker.py`) maintains virtual balances and positions for paper trading.

### Type System (`src/types.py`)

All components use strongly-typed dataclasses:
- **Market Data**: `Market`, `Quote`, `OrderBook`, `OrderBookLevel`
- **Orders & Execution**: `Order`, `Fill`, `OrderAck`, `ExecutionResult`
- **Trading**: `ArbitrageOpportunity`, `TradeLeg`, `TradePlan`
- **Portfolio**: `Position`, `PortfolioSnapshot`, `PlatformPortfolio`
- **Enums**: `Platform`, `Outcome`, `OrderType`, `OrderStatus`, `RiskLevel`

Factory functions for common operations:
- `create_arbitrage_plan()` (line 839): Creates a `TradePlan` from buy/sell markets
- `create_order_from_leg()` (line 890): Converts `TradeLeg` to `Order`
- `ensure_platform()`, `ensure_outcome()`, etc.: Type conversion utilities

### API Layer (`api.py`)

FastAPI application with key endpoints:
- `GET /` - Dashboard HTML interface
- `GET /api` - API documentation
- `POST /scan` - Scan for opportunities with configurable parameters
- `POST /execute` - Execute a trade
- `POST /run-strategy` - Trigger manual strategy cycle
- `GET /dashboard/stats` - Portfolio and market statistics
- `GET /dashboard/trades` - Recent trade history
- `GET /dashboard/activity` - Real-time activity feed

Configured for Vercel serverless deployment via `vercel.json`.

## Key Design Patterns

**Registry + Factory Pattern**: Both platforms (`src/platforms/registry.py`) and strategies (`src/strategies/arbitrage.py`) use registries with factory functions. To add new components:
1. Create class inheriting from base
2. Add to registry dict
3. Use factory function to instantiate

**Single Responsibility Principle**: Each component has one job:
- `MarketDataCollector`: Fetch data
- `ArbitrageStrategy`: Find opportunities
- `OrderExecutor`: Place orders
- `PortfolioTracker`: Track balances
- `TradingOrchestrator`: Coordinate everything

**Typed Dataclasses**: All data structures use Python dataclasses with type hints (`src/types.py`). This provides:
- Compile-time type checking
- Auto-generated `__init__`, `__repr__`, etc.
- Property methods for computed values
- Validation in `__post_init__`

## Adding New Platforms

1. Create `src/platforms/newplatform.py`:
```python
from .base import BaseMarketAPI

class NewPlatformAPI(BaseMarketAPI):
    def _get_auth_headers(self) -> Dict[str, str]:
        return {'Authorization': f'Bearer {self.api_key}'}

    def get_recent_markets(self, min_volume: float = 1000) -> List[Dict]:
        # Return list of dicts with keys: id, title, platform, yes_price, no_price, volume
        pass

    def place_buy_order(self, market_id: str, outcome: str, amount: float, price: float) -> Dict:
        # Return dict with keys: success, order_id, message
        pass

    def place_sell_order(self, market_id: str, outcome: str, amount: float, price: float) -> Dict:
        # Return dict with keys: success, order_id, message
        pass

    def find_event(self, keyword: str, limit: int = 10) -> List[Dict]:
        # Search and return matching events
        pass
```

2. Register in `src/platforms/registry.py`:
```python
from .newplatform import NewPlatformAPI

PLATFORM_APIS = {
    'polymarket': PolymarketAPI,
    'kalshi': KalshiAPI,
    'newplatform': NewPlatformAPI  # Add here
}
```

3. Add to `Platform` enum in `src/types.py:13-16`:
```python
class Platform(Enum):
    POLYMARKET = "polymarket"
    KALSHI = "kalshi"
    NEWPLATFORM = "newplatform"  # Add here
```

4. Add API key to `.env`:
```bash
NEWPLATFORM_API_KEY=your_key_here
```

## Adding New Strategies

1. Create strategy class in `src/strategies/`:
```python
class MyStrategy(BaseStrategy):
    def __init__(self, **kwargs):
        super().__init__("My Strategy Name")
        # Initialize parameters

    def find_opportunities(self, markets_by_platform: Dict[str, List],
                          portfolio_summary: Dict = None) -> List[ArbitrageOpportunity]:
        # Analyze markets and return list of ArbitrageOpportunity objects
        pass
```

2. Register in `src/strategies/arbitrage.py` (or create separate module):
```python
STRATEGIES = {
    'arbitrage': ArbitrageStrategy,
    'mystrategy': MyStrategy  # Add here
}
```

3. Use via `get_strategy('mystrategy', **params)` in main.py or orchestrator.

## Important Implementation Notes

**Paper Trading Mode**: The system runs in simulation mode by default. Real trading requires:
- Valid API keys in `.env`
- Setting `paper_trading=False` in `TradingOrchestrator` initialization (line 43)
- Platform API implementations for real order placement (currently return demo responses)

**Market Matching Algorithm**: Markets are matched using word-based Jaccard similarity:
- Titles are normalized (lowercase, remove special chars)
- Common stop words are filtered out
- Threshold is 0.5 (50% word overlap required)
- Located at `src/strategies/arbitrage.py:130-153`

**Opportunity Filtering**:
- Minimum spread configured via `MIN_SPREAD` env var (default: 0.05 = 5%)
- Minimum volume configured via `MIN_VOLUME` env var (default: 1000)
- Opportunities sorted by `expected_profit_per_share` descending

**Test Coverage**: 68 tests covering all major components. Tests use pytest with fixtures defined in `tests/conftest.py`. When adding features, add corresponding tests following existing patterns.

**Backward Compatibility**: `main.py` is a thin wrapper that imports from `src.engine.bot`. The main bot logic is in `src/coordinators/trading_orchestrator.py` (aliased as `ArbitrageBot` for compatibility).

**Configuration**: All settings via environment variables loaded from `.env`:
- `POLYMARKET_API_KEY`, `KALSHI_API_KEY` - Platform credentials
- `MIN_VOLUME` - Minimum market volume to consider (default: 1000)
- `MIN_SPREAD` - Minimum profitable spread (default: 0.05)
