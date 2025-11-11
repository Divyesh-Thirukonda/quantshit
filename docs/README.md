# Quantshit - Cross-Venue Arbitrage Engine

A prediction market arbitrage trading system built with clean architecture principles. Detects and executes profitable trades across Polymarket and Kalshi using advanced market matching algorithms.

## Quick Start

```bash
git clone https://github.com/Divyesh-Thirukonda/quantshit.git
cd quantshit
pip install -r requirements.txt
cp .env.example .env  # Add your API keys
python main.py
```

## Current Status

**✅ Working:**

- Clean architecture implemented with clear separation of concerns
- Exchange clients for Kalshi and Polymarket (fetches real market data)
- Market matching algorithm with fuzzy string matching
- Opportunity scoring with fee and slippage calculations
- Trade validation and risk checks
- Paper trading mode (no real orders placed)
- Position tracking and P&L monitoring
- FastAPI server with dashboard

**🚧 In Progress / Known Issues:**

- Kalshi API returns 0 markets (endpoint/auth issue - see `src/exchanges/kalshi/client.py:22`)
- Position creation from executed orders not implemented (`src/main.py:182-184`)
- Position closing logic not implemented (`src/main.py:242-245`)
- Real order placement disabled (paper trading only - `src/services/execution/executor.py:136-138`)
- Tests reference old architecture and need updating
- API server has broken endpoints referencing non-existent methods (`api.py`)

See `CLAUDE.md` for detailed TODO list.

## Architecture

Quantshit follows **clean architecture** with strict dependency rules:

```
┌─────────────────────────────────────────────┐
│         Outer Layer (Frameworks)            │
│  main.py, api.py, exchanges/, database/     │
│                                             │
│    ┌─────────────────────────────────┐      │
│    │   Middle Layer (Services)       │      │
│    │  matching/, execution/,         │      │
│    │  monitoring/, strategies/       │      │
│    │                                 │      │
│    │   ┌─────────────────────┐       │      │
│    │   │  Inner Layer (Core) │       │      │
│    │   │  models/, types.py  │       │      │
│    │   └─────────────────────┘       │      │
│    └─────────────────────────────────┘      │
└─────────────────────────────────────────────┘
```

**Dependencies flow inward:** Outer layers depend on inner layers, never the reverse.

## Directory Structure

```
quantshit/
├── src/                        # Clean architecture implementation
│   ├── types.py               # Universal enums (Exchange, OrderSide, OrderStatus)
│   ├── models/                # 📦 Domain models (inner layer)
│   │   ├── market.py         # Market data structure
│   │   ├── order.py          # Order data structure
│   │   ├── position.py       # Position data structure
│   │   └── opportunity.py    # Arbitrage opportunity
│   ├── config/               # ⚙️ Configuration
│   │   ├── settings.py       # Environment variables
│   │   └── constants.py      # Business constants (fees, thresholds)
│   ├── utils/                # 🛠️ Shared utilities
│   │   ├── logger.py         # Logging setup
│   │   ├── math.py           # Profit calculations
│   │   └── decorators.py     # Retry, rate limit
│   ├── services/             # 🎯 Business logic (middle layer)
│   │   ├── matching/
│   │   │   ├── matcher.py    # Find equivalent markets
│   │   │   └── scorer.py     # Calculate profitability
│   │   ├── execution/
│   │   │   ├── validator.py  # Pre-trade validation
│   │   │   └── executor.py   # Execute trades (paper mode)
│   │   └── monitoring/
│   │       ├── tracker.py    # Track positions & P&L
│   │       └── alerter.py    # Notifications (Telegram stub)
│   ├── strategies/           # 📊 Trading strategies
│   │   ├── base.py           # Abstract base class
│   │   └── simple_arb.py     # Simple arbitrage strategy
│   ├── exchanges/            # 🔌 Exchange integrations (outer layer)
│   │   ├── base.py           # Abstract exchange interface
│   │   ├── kalshi/
│   │   │   ├── client.py     # Kalshi API client
│   │   │   └── parser.py     # Convert to Market model
│   │   └── polymarket/
│   │       ├── client.py     # Polymarket API client
│   │       └── parser.py     # Convert to Market model
│   ├── database/             # 💾 Data persistence (outer layer)
│   │   ├── repository.py     # Data access layer (in-memory)
│   │   └── schema.py         # Database schema (for future SQL)
│   └── main.py               # 🤖 Main orchestrator (ArbitrageBot)
├── main.py                   # Entry point wrapper
├── api.py                    # FastAPI server
├── api/                      # Vercel serverless deployment
├── tests/                    # ⚠️ Tests need updating for new architecture
├── docs/                     # Architecture documentation
│   ├── MODULE_EXPLANATIONS.md
│   ├── VISUAL_FLOW.md
│   └── TESTING.md
├── CLAUDE.md                 # Project instructions for Claude Code
└── requirements.txt
```

## How It Works

### Data Flow (Single Strategy Cycle)

```
ArbitrageBot.run_cycle():
  │
  1. Fetch Markets
  ├─> kalshi/client.py.get_markets() → List[Market]
  └─> polymarket/client.py.get_markets() → List[Market]
  │
  2. Match Markets
  └─> matching/matcher.py.find_matches()
      └─> List[(Market, Market, confidence_score)]
  │
  3. Score Opportunities
  └─> matching/scorer.py.score_opportunities()
      └─> List[Opportunity] (sorted by profit)
  │
  4. Select Best
  └─> strategies/simple_arb.py.select_best_opportunity()
      └─> Opportunity
  │
  5. Validate Trade
  └─> execution/validator.py.validate()
      └─> ValidationResult(valid=True/False, reason)
  │
  6. Execute (if valid)
  └─> execution/executor.py.execute()
      ├─> kalshi/client.py.place_order() [Paper mode]
      ├─> polymarket/client.py.place_order() [Paper mode]
      └─> database/repository.py.save_order()
  │
  7. Monitor Positions
  └─> monitoring/tracker.py.update_positions()
      └─> database/repository.py.save_position()
```

### Market Matching Algorithm

Uses **fuzzy string matching** to find equivalent markets:

- Normalizes titles (lowercase, remove punctuation)
- Filters stop words ("the", "a", "will", etc.)
- Calculates Jaccard similarity (word overlap)
- Threshold: 0.5 (50% word overlap required)
- Returns confidence score for each match

### Opportunity Scoring

Calculates profit accounting for fees and slippage:

```python
spread = |price_A - price_B|
profit = spread - fee_A - fee_B - slippage
profit_pct = profit / investment

Fees:
- Kalshi: 0.7%
- Polymarket: 2.0%
- Slippage: 1.0%
```

## Configuration

Environment variables in `.env`:

```bash
# Exchange API Keys
KALSHI_API_KEY=your_key_here
POLYMARKET_API_KEY=your_key_here

# System Configuration
PAPER_TRADING=true           # Paper trading mode (default)
ENABLE_ALERTS=false          # Telegram alerts
LOG_LEVEL=INFO               # Logging verbosity
LOG_FILE=quantshit.log       # Log file path
```

**Note**: Trading parameters (min_volume, min_spread, profit thresholds, etc.) are now configured per-strategy in code at `src/strategies/config.py`, not via environment variables. This allows different strategies to have different parameters.

Business constants in `src/config/constants.py`:

```python
MIN_PROFIT_THRESHOLD = 0.02   # 2% minimum profit
MAX_POSITION_SIZE = 1000      # Max contracts per position
FEE_KALSHI = 0.007           # 0.7% Kalshi fee
FEE_POLYMARKET = 0.02        # 2% Polymarket fee
SLIPPAGE_FACTOR = 0.01       # 1% slippage assumption
```

## Running the System

### CLI Mode (Single Cycle)

```bash
python main.py
```

Runs one complete cycle: fetch markets → find opportunities → execute best trade

### API Server

```bash
python api.py  # Starts on http://localhost:8000
```

**Available Endpoints:**

- `GET /` - Dashboard UI
- `POST /scan` - Scan for opportunities
- `POST /execute` - Execute a trade
- `POST /run-strategy` - Run full strategy cycle
- `GET /dashboard/stats` - Portfolio statistics

**Note:** API server currently has broken endpoints - needs fixing (see `api.py` issues in CLAUDE.md)

## Testing

⚠️ **Tests are currently broken** - they reference the old architecture that was removed.

```bash
# Will fail until tests are updated
python -m pytest tests/ -v

# Individual test files (all need rewriting)
python -m pytest tests/test_strategies.py -v
python -m pytest tests/test_integration.py -v
```

See `docs/TESTING.md` for test suite documentation.

## Development Guide

### Adding a New Exchange

1. Create directory: `src/exchanges/newexchange/`
2. Implement `client.py` extending `exchanges/base.py`
3. Create `parser.py` to convert API data → `models.Market`
4. Add `Exchange.NEWEXCHANGE` to `src/types.py`
5. Wire into `src/main.py` initialization

### Adding a New Strategy

1. Create class extending `strategies/base.py:BaseStrategy`
2. Implement `select_best_opportunity(opportunities) -> Opportunity`
3. Instantiate in `src/main.py` instead of `SimpleArbitrageStrategy`

### Enabling Real Trading

⚠️ **Currently disabled** - only paper trading works

1. Set `PAPER_TRADING=False` in `.env`
2. Implement real API calls in `src/services/execution/executor.py:136-138`
3. Add error handling for order failures, partial fills, rejections
4. Test with small positions first

## Key Design Patterns

**Repository Pattern:** All data access through `Repository` class - easy to swap in-memory for SQL later

**Strategy Pattern:** Multiple strategies by extending `BaseStrategy`

**Single Responsibility:** Each module has one job:

- `Matcher`: Find equivalent markets
- `Scorer`: Calculate profitability
- `Validator`: Check if trade is safe
- `Executor`: Place orders
- `Tracker`: Monitor positions
- `Alerter`: Send notifications

**Dependency Inversion:** Services depend on abstractions (Repository, BaseStrategy) not concrete implementations

## Documentation

- **`CLAUDE.md`** - Complete project overview, detailed TODO list, architecture notes
- **`docs/MODULE_EXPLANATIONS.md`** - Theoretical design of clean architecture
- **`docs/VISUAL_FLOW.md`** - Data flow diagrams and dependency rules
- **`docs/TESTING.md`** - Test suite documentation
- **`src/README.md`** - Refactor status and migration notes

## Contributing

1. Check `CLAUDE.md` for priority TODOs
2. Pick a task from the TODO list
3. Follow clean architecture principles (inner layers don't depend on outer layers)
4. Add tests for new features
5. Update documentation
6. Submit PR

**High Priority Areas:**

- Fix Kalshi API integration (returns 0 markets)
- Implement position creation/closing
- Rewrite test suite for new architecture
- Implement real order placement
- Fix API server endpoints

---

**⚠️ Paper Trading Only:** System currently operates in simulation mode. Real trading requires:

- Valid API keys for both exchanges
- Implementation of real order placement logic
- Thorough testing with small positions
- Risk management review

