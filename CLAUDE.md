# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

Quantshit is a cross-venue arbitrage engine for prediction markets that detects and executes profitable trades across Polymarket and Kalshi. The system uses a **clean architecture** in the `src/` directory following clean architecture principles.

**Current Status**: The codebase is now fully functional:
- Clean architecture implemented in `src/` (models, services, strategies pattern) with exchange clients
- Exchange clients for Kalshi and Polymarket implemented and integrated
- Successfully fetches real market data from both exchanges with cursor-based pagination
- **NEW**: SQLite database system for persistent storage
- **NEW**: Market scanner that fetches, matches, and stores opportunities
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

### Database Scanner
```bash
# Run market scan (fetch, match, store opportunities)
python -m src.scanner

# Query database
python scripts/db_query.py stats
python scripts/db_query.py markets
python scripts/db_query.py opportunities
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

### 1. Tests Need Updating
All tests in `tests/` reference old architecture that was removed. Tests need rewrite for new structure.

### 2. Order Placement Not Tested
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
```

Optional:
```bash
PAPER_TRADING=true              # Paper trading mode (default)
ENABLE_ALERTS=false             # Enable Telegram alerts
LOG_LEVEL=INFO                  # Logging level
LOG_FILE=logs/arbitrage.log     # Log file path
```

**Trading Parameters**: As of the latest refactor, trading parameters like `MIN_VOLUME`, `MIN_SPREAD`, profit thresholds, position sizes, etc. are no longer configured via environment variables. Instead, they are owned by individual strategies and configured in `src/strategies/config.py`. This allows:
- Different strategies to have different parameters
- Easier testing and experimentation with strategy configs
- Clear separation: infrastructure config (`.env`) vs. trading logic (strategy config)

## Next Steps for Improvement

1. **Fix Kalshi API integration** - Debug why no markets are returned, verify endpoint and auth
2. **Update tests** - Rewrite test suite for new architecture
3. **Test order placement** - Try placing real orders (with small amounts) to verify integration works
4. **Add position management** - Create positions from executed orders, implement exit logic
5. **Implement real trading** - Remove paper trading mode, add proper error handling for real trades
6. **Add monitoring** - Circuit breakers, better logging, alerting for errors
7. **Performance optimization** - Add caching, rate limiting, concurrent requests

---

## 🔥 DETAILED TODO LIST

### Phase 1: Critical Fixes (Blocking Issues)

#### 1.1 Fix Kalshi API Integration ✅ FIXED (October 31, 2025)
**Status**: ✅ Working - Returns 200+ markets with pagination support
- [x] Debug actual API response from Kalshi
- [x] Verify correct API endpoint (using `/markets` instead of `/events`)
- [x] Update parser to match actual response structure
- [x] Fix price calculations (use mid-price of bid/ask)
- [x] Fix volume calculations (convert contracts to dollars)
- [x] Test end-to-end integration
- [x] Implement cursor-based pagination to fetch all markets (not just first page)

See `docs/KALSHI_FIX.md` for complete details.

#### 1.2 Implement Position Creation (src/main.py:182-184)
**Status**: TODO comment, not implemented
- [ ] Create `_create_position_from_execution()` method in ArbitrageBot
- [ ] Build Position object from ExecutionResult (buy + sell orders)
- [ ] Link both legs to same arbitrage position
- [ ] Save position to repository
- [ ] Add position to tracker
- [ ] Test position creation flow

#### 1.3 Implement Position Closing (src/main.py:242-245)
**Status**: TODO comment, execution not implemented
- [ ] Implement `_close_position()` method in ArbitrageBot
- [ ] Place closing orders on both exchanges
- [ ] Handle partial closes gracefully
- [ ] Calculate realized P&L
- [ ] Update tracker with realized gains/losses
- [ ] Remove closed positions from repository

---

### Phase 2: Real Trading (High Priority)

#### 2.1 Real Order Placement (src/services/execution/executor.py:136-138)
**Status**: Raises NotImplementedError for live trading
- [ ] Implement real API calls in `_place_buy_order()`
- [ ] Implement real API calls in `_place_sell_order()`
- [ ] Call exchange client `place_order()` methods
- [ ] Parse order response and update Order object
- [ ] Handle order confirmations
- [ ] Implement order status polling
- [ ] Handle partial fills
- [ ] Handle rejections and timeouts
- [ ] Implement cancellation logic if one leg fails

#### 2.2 Real-time Price Updates (src/main.py:239)
**Status**: TODO comment
- [ ] Create `_fetch_current_prices()` method
- [ ] Periodically fetch market prices for open positions
- [ ] Update `position.current_price` for all open positions
- [ ] Calculate unrealized P&L in real-time
- [ ] Trigger exit signals based on updated prices
- [ ] Add price staleness checks

#### 2.3 Order Status Management
**Status**: Not implemented
- [ ] Poll order status after placement
- [ ] Update order objects with fill information
- [ ] Handle partial fills (decide whether to cancel or wait)
- [ ] Implement order timeouts
- [ ] Add order cancellation logic
- [ ] Track fill prices vs. expected prices (slippage)

---

### Phase 3: API Server Fixes (Medium Priority)

#### 3.1 Fix API Endpoints (api.py)
**Status**: Calls non-existent methods on ArbitrageBot
- [ ] Fix `bot.run_strategy_cycle()` → should be `bot.run_cycle()` (Line 104)
- [ ] Fix `bot.collect_market_data()` → implement or use `_fetch_markets()` (Line 116)
- [ ] Fix `bot.api_keys` → use `settings.KALSHI_API_KEY` etc. (Line 131)
- [ ] Fix `bot.platforms` → use `bot.kalshi_client` / `bot.polymarket_client` (Line 134)
- [ ] Fix `bot.strategy.find_opportunities()` → refactor to use existing flow (Line 141)
- [ ] Fix `bot.search_events()` → implement or remove (Line 188)
- [ ] Fix `bot.execute_trade()` → implement or use existing execution flow (Line 207)
- [ ] Add `bot.get_portfolio_summary()` method (Line 238)
- [ ] Add `bot.find_opportunities()` method (Line 235)
- [ ] Add `bot.data_collector` or refactor (Line 231)

#### 3.2 Dashboard Integration
**Status**: Backend incomplete
- [ ] Connect dashboard to real bot data
- [ ] Remove mock trade data (Lines 263-295)
- [ ] Fetch real trade history from repository
- [ ] Fetch real activity feed from logs
- [ ] Add WebSocket for real-time updates (optional)

---

### Phase 4: Alerting & Monitoring (Medium Priority)

#### 4.1 Telegram Notifications (src/services/monitoring/alerter.py:147-153)
**Status**: Stubbed out
- [ ] Implement actual Telegram Bot API call using `requests`
- [ ] Add proper error handling
- [ ] Implement retry logic for failed sends
- [ ] Test with real bot token and chat ID
- [ ] Add message rate limiting (avoid spam)
- [ ] Format messages with markdown for better readability

#### 4.2 Enhanced Monitoring
**Status**: Basic monitoring exists, needs expansion
- [ ] Add performance metrics collection
- [ ] Track latency for each step in cycle
- [ ] Monitor API response times
- [ ] Track success/failure rates
- [ ] Add circuit breakers for repeated failures
- [ ] Implement emergency stop mechanism
- [ ] Add health check endpoint

---

### Phase 5: Testing (High Priority)

#### 5.1 Rewrite Test Suite
**Status**: All tests reference old architecture (will fail)
- [ ] Rewrite `tests/test_executors.py` for new structure
- [ ] Rewrite `tests/test_integration.py` for new structure
- [ ] Rewrite `tests/test_collectors.py` → should be test_exchanges.py
- [ ] Rewrite `tests/test_trackers.py` for new structure
- [ ] Update `tests/conftest.py` with new fixtures

#### 5.2 Add New Tests
**Status**: Need comprehensive test coverage
- [ ] Unit tests for `src/services/matching/matcher.py`
- [ ] Unit tests for `src/services/matching/scorer.py`
- [ ] Unit tests for `src/services/execution/validator.py`
- [ ] Unit tests for `src/services/execution/executor.py`
- [ ] Unit tests for `src/strategies/simple_arb.py`
- [ ] Mock exchange clients for testing
- [ ] Integration test for full arbitrage cycle
- [ ] Test error handling and edge cases

---

### Phase 6: Database & Persistence (Medium Priority)

#### 6.1 SQL Database Implementation
**Status**: In-memory only (loses data on restart)
- [ ] Implement SQLite backend for Repository
- [ ] Create database schema from `src/database/schema.py`
- [ ] Add SQLAlchemy ORM models
- [ ] Implement migrations system
- [ ] Add connection pooling
- [ ] Test PostgreSQL compatibility (production)
- [ ] Add database backup/restore

#### 6.2 Data Retention
**Status**: Not implemented
- [ ] Implement data archiving for old opportunities
- [ ] Add trade history export (CSV, JSON)
- [ ] Implement log rotation
- [ ] Add database cleanup jobs

---

### Phase 7: Advanced Features (Nice to Have)

#### 7.1 Order Book Analysis
**Status**: Not implemented (uses mid-price only)
- [ ] Fetch order book depth from exchanges
- [ ] Analyze liquidity before placing orders
- [ ] Calculate actual executable prices
- [ ] Check if sufficient liquidity exists
- [ ] Adjust position size based on depth

#### 7.2 Risk Management Enhancements
**Status**: Basic validation exists, needs improvement
- [ ] Enforce portfolio-level exposure limits
- [ ] Add per-exchange exposure limits
- [ ] Implement correlation risk checks
- [ ] Add maximum drawdown limits
- [ ] Implement position concentration limits
- [ ] Add margin/capital utilization tracking

#### 7.3 Multi-leg Arbitrage
**Status**: Only 2-leg arbitrage supported
- [ ] Support 3+ leg arbitrage opportunities
- [ ] Handle complex arbitrage chains
- [ ] Optimize execution order for multi-leg
- [ ] Add rollback for failed multi-leg trades

#### 7.4 Rate Limiting & Performance
**Status**: No actual rate limiting enforced
- [ ] Implement token bucket rate limiter
- [ ] Add request queuing
- [ ] Implement concurrent API requests
- [ ] Add caching for market data
- [ ] Optimize matching algorithm performance
- [ ] Add connection pooling for HTTP requests

#### 7.5 Backtesting Framework
**Status**: Not implemented
- [ ] Create historical data collection system
- [ ] Build backtesting engine
- [ ] Implement strategy performance metrics
- [ ] Add visualization for backtest results
- [ ] Test strategies on historical data

#### 7.6 Additional Exchanges
**Status**: Only Kalshi + Polymarket
- [ ] Add PredictIt integration
- [ ] Add Manifold Markets integration
- [ ] Add Metaculus integration (if trading available)
- [ ] Create generic exchange adapter interface

---

## 🎯 Priority Summary

**🔥 BLOCKING (Do First)**:
1. Implement position creation from orders
2. Implement position closing logic

**⚠️ HIGH PRIORITY (Do Next)**:
3. Real order placement implementation
4. Real-time price updates for positions
5. Rewrite test suite

**📊 MEDIUM PRIORITY (Important)**:
6. Fix API server methods
7. Implement Telegram alerts
8. Add SQL database persistence

**✨ NICE TO HAVE (Future)**:
9. Order book analysis
10. Advanced risk management
11. Backtesting framework
12. Additional exchanges
