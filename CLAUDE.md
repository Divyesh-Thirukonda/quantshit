# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

Quantshit is a cross-venue arbitrage engine for prediction markets that detects and executes profitable trades across Polymarket and Kalshi. The system uses a **clean architecture** in the `src/` directory following clean architecture principles.

**Current Status**: The codebase is now fully functional:
- Clean architecture implemented in `src/` (models, services, strategies pattern) with exchange clients
- Exchange clients for Kalshi and Polymarket implemented and integrated
- Successfully fetches real market data from both exchanges
- Paper trading mode is active (no real orders placed)

## Development Commands

### Setup
```bash
pip install -r requirements.txt
cp .env.example .env  # Add your API keys
```

### Running
```bash
# Run single strategy cycle (fetches markets, finds opportunities, executes if found)
python main.py

# Run as API server (dashboard + REST endpoints)
python api.py  # Available at http://localhost:8000
```

### Testing
```bash
# Tests exist but reference OLD code structure that was removed
# Most tests will fail until they're updated for new architecture
python -m pytest tests/ -v

# Individual test modules:
python -m pytest tests/test_strategies.py -v
python -m pytest tests/test_executors.py -v      # Tests for old structure
python -m pytest tests/test_integration.py -v    # Tests for old structure
```

## Current Architecture (NEW - In `src/`)

The new architecture follows clean architecture principles with clear separation of concerns:

```
src/
├── types.py                    # Universal type definitions (Exchange, OrderSide, OrderStatus, etc.)
├── models/                     # Domain models (data structures only)
│   ├── market.py              # Market data structure
│   ├── order.py               # Order data structure
│   ├── position.py            # Position data structure
│   └── opportunity.py         # Arbitrage opportunity structure
├── config/                     # Configuration management
│   ├── settings.py            # Environment variables, runtime config
│   └── constants.py           # Business logic constants (fees, thresholds)
├── utils/                      # Shared utilities
│   ├── logger.py              # Logging configuration
│   ├── math.py                # Profit calculations, probability conversions
│   └── decorators.py          # Reusable decorators (retry, rate limit)
├── exchanges/                  # Exchange client implementations
│   ├── base.py                # Abstract base class for exchange clients
│   ├── kalshi/                # Kalshi integration
│   │   ├── client.py          # Kalshi API calls
│   │   └── parser.py          # Convert Kalshi data → Market model
│   └── polymarket/            # Polymarket integration
│       ├── client.py          # Polymarket API calls
│       └── parser.py          # Convert Polymarket data → Market model
├── services/                   # Business logic layer
│   ├── matching/              # Market matching algorithms
│   │   ├── matcher.py         # Find equivalent markets across exchanges
│   │   └── scorer.py          # Calculate profitability of opportunities
│   ├── execution/             # Trade execution
│   │   ├── validator.py       # Pre-trade validation (balance, risk checks)
│   │   └── executor.py        # Execute trades (currently paper trading only)
│   └── monitoring/            # Position and performance tracking
│       ├── tracker.py         # Track positions and P&L
│       └── alerter.py         # Send notifications (Telegram placeholder)
├── strategies/                 # Trading strategy implementations
│   ├── base.py                # Abstract base class for strategies
│   └── simple_arb.py          # Simple arbitrage strategy
├── database/                   # Data persistence layer
│   ├── repository.py          # Data access layer (currently in-memory)
│   └── schema.py              # Database schema definitions (for future SQL)
└── main.py                     # Main orchestrator with ArbitrageBot class

Root level:
├── main.py                     # Entry point wrapper
├── api.py                      # FastAPI server
├── api/                        # Vercel serverless deployment
└── tests/                      # Test suite (needs updating for new structure)
```

## Key Design Patterns

**Clean Architecture**:
- **Models** (inner layer): Pure data structures, no dependencies
- **Services** (middle layer): Business logic, depends on models
- **Main** (outer layer): Orchestration, wires everything together

**Repository Pattern**: All data access through `Repository` class - easy to swap in-memory storage for SQL database later.

**Strategy Pattern**: Multiple trading strategies can be implemented by extending `BaseStrategy` class.

**Single Responsibility**: Each module has one job:
- `Matcher`: Find equivalent markets
- `Scorer`: Calculate profitability
- `Validator`: Check if trade is safe
- `Executor`: Place orders
- `Tracker`: Monitor positions
- `Alerter`: Send notifications

## Known Issues & Limitations

### 1. Kalshi API Returns No Markets
The Kalshi client currently returns 0 markets. This could be due to:
- Incorrect API endpoint (currently using `https://api.elections.kalshi.com/trade-api/v2`)
- Different response structure than expected
- Possible authentication requirement for market data
- Recommend testing with valid Kalshi API key and verifying endpoint/response format

### 2. Tests Need Updating
All tests in `tests/` reference old architecture that was removed. Tests need rewrite for new structure.

### 3. Order Placement Not Tested
The `place_order()` methods in exchange clients are implemented but haven't been tested with real API calls (paper trading mode only).

## How Data Flows (Once Exchange Clients Exist)

```
ArbitrageBot.run_cycle() in src/main.py:
  │
  ├─> 1. Fetch Markets
  │   ├─> exchanges/kalshi/client.py.get_markets()
  │   │   └─> exchanges/kalshi/parser.py → List[models.Market]
  │   └─> exchanges/polymarket/client.py.get_markets()
  │       └─> exchanges/polymarket/parser.py → List[models.Market]
  │
  ├─> 2. Match Markets
  │   └─> services/matching/matcher.py.find_matches()
  │       └─> List[(Market, Market, confidence_score)]
  │
  ├─> 3. Score Opportunities
  │   └─> services/matching/scorer.py.score_opportunities()
  │       └─> List[models.Opportunity] (sorted by profit)
  │
  ├─> 4. Select Best
  │   └─> strategies/simple_arb.py.select_best_opportunity()
  │       └─> models.Opportunity
  │
  ├─> 5. Validate
  │   └─> services/execution/validator.py.validate()
  │       └─> ValidationResult(valid=True/False, reason)
  │
  ├─> 6. Execute (if valid)
  │   └─> services/execution/executor.py.execute()
  │       ├─> exchanges/kalshi/client.py.place_order()
  │       ├─> exchanges/polymarket/client.py.place_order()
  │       └─> database/repository.py.save_order()
  │
  └─> 7. Monitor
      └─> services/monitoring/tracker.py.update_positions()
          └─> database/repository.py.save_position()
```

## Type System (`src/types.py`)

All modules use strongly-typed enums from `src/types.py`:

```python
Exchange: KALSHI, POLYMARKET
OrderSide: BUY, SELL
OrderStatus: PENDING, FILLED, PARTIAL, CANCELLED, REJECTED
MarketStatus: OPEN, CLOSED, SETTLED
Outcome: YES, NO

# Type aliases for clarity
Price = float          # 0.0 to 1.0
Quantity = int         # Number of contracts
Probability = float    # 0.0 to 1.0
```

## Configuration (`src/config/`)

**settings.py**: Runtime configuration from environment variables
```python
KALSHI_API_KEY        # From .env
POLYMARKET_API_KEY    # From .env
PAPER_TRADING         # Default: True
ENABLE_ALERTS         # Default: False
LOG_LEVEL             # Default: "INFO"
DATABASE_URL          # Default: "sqlite:///arbitrage.db"
```

**constants.py**: Business logic constants
```python
MIN_PROFIT_THRESHOLD = 0.02        # 2% minimum profit
MAX_POSITION_SIZE = 1000           # Max contracts per position
FEE_KALSHI = 0.007                 # 0.7% fee
FEE_POLYMARKET = 0.02              # 2% fee
SLIPPAGE_FACTOR = 0.01             # 1% slippage
TITLE_SIMILARITY_THRESHOLD = 0.5   # 50% word overlap for matching
```

## Adding New Features

### Add New Exchange
1. Create `src/exchanges/newexchange/client.py` implementing base interface
2. Create `src/exchanges/newexchange/parser.py` to convert to `models.Market`
3. Add `Exchange.NEWEXCHANGE` to `src/types.py`
4. Wire into `src/main.py` initialization

### Add New Strategy
1. Create class extending `strategies/base.py:BaseStrategy`
2. Implement `select_best_opportunity(opportunities) -> Opportunity`
3. Instantiate in `src/main.py` instead of `SimpleArbitrageStrategy`

### Add Real Trading (Currently Paper Only)
1. Set `PAPER_TRADING=False` in `.env`
2. Implement real API calls in `services/execution/executor.py` (currently returns mock data)
3. Add error handling for order failures, partial fills, etc.

## Important Implementation Notes

**Market Matching Algorithm** (`services/matching/matcher.py`):
- Uses word-based Jaccard similarity
- Normalizes titles (lowercase, remove punctuation)
- Filters common stop words
- Threshold: 0.5 (50% word overlap)

**Opportunity Scoring** (`services/matching/scorer.py`):
- Calculates spread: `|price_A - price_B|`
- Subtracts fees: Kalshi 0.7%, Polymarket 2%
- Accounts for slippage: 1% default
- Returns profit as both absolute ($) and percentage (%)

**Validation Checks** (`services/execution/validator.py`):
- Sufficient account balance
- Markets still open
- Prices haven't moved beyond tolerance
- Within risk limits (max position size)
- Not already in this position

**Paper Trading Mode**: By default, `executor.py` returns mock success responses without placing real orders. Set `PAPER_TRADING=False` and implement real API calls for live trading.

## API Server (`api.py`)

FastAPI application with endpoints:
- `GET /` - Dashboard HTML
- `GET /api` - API documentation
- `POST /scan` - Scan for opportunities
- `POST /execute` - Execute a trade
- `POST /run-strategy` - Run strategy cycle
- `GET /dashboard/stats` - Portfolio statistics
- `GET /dashboard/trades` - Trade history

Run with: `python api.py` (currently broken - see "Fix Import Path" above)

Configured for Vercel serverless deployment via `vercel.json` (deploys `api/` directory).

## Documentation References

- `docs/MODULE_EXPLANATIONS.md` - Detailed theoretical design of clean architecture
- `docs/VISUAL_FLOW.md` - Data flow diagrams and dependency rules
- `src/README.md` - Status of refactor, what's complete vs incomplete

## Environment Variables

Required in `.env`:
```bash
KALSHI_API_KEY=your_key_here
POLYMARKET_API_KEY=your_key_here
MIN_VOLUME=1000                 # Minimum market volume to consider
MIN_SPREAD=0.05                 # Minimum profitable spread (5%)
```

Optional:
```bash
PAPER_TRADING=true              # Paper trading mode (default)
ENABLE_ALERTS=false             # Enable Telegram alerts
LOG_LEVEL=INFO                  # Logging level
LOG_FILE=logs/arbitrage.log     # Log file path
```

## Next Steps for Improvement

1. **Fix Kalshi API integration** - Debug why no markets are returned, verify endpoint and auth
2. **Update tests** - Rewrite test suite for new architecture
3. **Test order placement** - Try placing real orders (with small amounts) to verify integration works
4. **Add position management** - Create positions from executed orders, implement exit logic
5. **Implement real trading** - Remove paper trading mode, add proper error handling for real trades
6. **Add monitoring** - Circuit breakers, better logging, alerting for errors
7. **Performance optimization** - Add caching, rate limiting, concurrent requests
