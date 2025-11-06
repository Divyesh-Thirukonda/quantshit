# Quantshit - Arbitrage Trading Bot# Quantshit - Cross-Venue Arbitrage Engine



Prediction market arbitrage engine for Kalshi and Polymarket. Finds price differences, executes trades, tracks P&L.A prediction market arbitrage trading system built with clean architecture principles. Detects and executes profitable trades across Polymarket and Kalshi using advanced market matching algorithms.



## Quick Start---



```bash## Table of Contents

git clone https://github.com/Divyesh-Thirukonda/quantshit.git

cd quantshit1. [Quick Start](#quick-start)

pip install -r requirements.txt2. [Testing](#testing)

cp .env.example .env  # Add your API keys3. [Prerequisites](#prerequisites)

python run_tests.py   # Verify setup4. [Installation & Setup](#installation--setup)

python src/main.py    # Run bot5. [Running the System](#running-the-system)

```6. [System Overview](#system-overview)

7. [Architecture](#architecture)

## Run Tests8. [Directory Structure](#directory-structure)

9. [How It Works: Code Flow](#how-it-works-code-flow)

```bash10. [Development Guide by Role](#development-guide-by-role)

python run_tests.py              # Run all tests11. [Configuration](#configuration)

python run_tests.py fast         # Quick run12. [Key Design Patterns](#key-design-patterns)

python run_tests.py strategies   # Test specific module13. [Contributing](#contributing)

python run_tests.py help         # See all options14. [Current Status](#current-status)

```

---

## What It Does

## Quick Start

1. **Fetches markets** from Kalshi + Polymarket

2. **Matches equivalent markets** using fuzzy string matching  ```bash

3. **Calculates profit** after fees (Kalshi 0.7%, Polymarket 2%)git clone https://github.com/Divyesh-Thirukonda/quantshit.git

4. **Validates trades** (capital, volume, risk limits)cd quantshit

5. **Executes orders** (paper trading mode by default)pip install -r requirements.txt

6. **Monitors positions** and tracks P&Lcp .env.example .env  # Add your API keys

python run_tests.py  # Run tests to verify setup

**Example**: Buy "Bitcoin $100k" on Polymarket @ $0.60, sell on Kalshi @ $0.68 → $45 profit (8% return)python src/main.py   # Run the bot

```

## Architecture

---

Clean architecture with 3 layers:

## Testing

```

┌─ OUTER (Frameworks) ──────────────────┐### Run All Tests

│  exchanges/, database/, api/          │

│  ┌─ MIDDLE (Services) ─────────┐      │The easiest way to verify your setup and ensure everything is working:

│  │  matching/, execution/,     │      │

│  │  monitoring/, strategies/   │      │```bash

│  │  ┌─ INNER (Core) ────┐      │      │python run_tests.py

│  │  │  models/, types.py │      │      │```

│  │  └────────────────────┘      │      │

│  └──────────────────────────────┘      │This runs the complete test suite with coverage reporting.

└────────────────────────────────────────┘

```### Test Commands



**Rule**: Dependencies flow inward only. Core has zero external dependencies.```bash

# Run all tests with coverage (default)

## Project Structurepython run_tests.py all



```# Run all tests quickly (no coverage)

src/python run_tests.py fast

├── main.py              # Entry point - orchestrates everything

├── types.py             # Enums (Exchange, OrderSide, OrderStatus)# Run specific test categories

├── models/              # Data structures (Market, Order, Position)python run_tests.py models       # Test domain models

├── config/              # Settings and constantspython run_tests.py matching     # Test market matching

├── exchanges/           # Kalshi & Polymarket API clientspython run_tests.py execution    # Test trade execution

│   ├── kalshi/python run_tests.py strategies   # Test trading strategies

│   └── polymarket/python run_tests.py integration  # Test full pipeline

├── services/            # Business logic

│   ├── matching/        # Find equivalent markets, score profit# Show all available commands

│   ├── execution/       # Validate & execute tradespython run_tests.py help

│   └── monitoring/      # Track positions, send alerts```

├── strategies/          # Trading strategies

└── database/            # Data persistence (in-memory)### What's Tested

tests/                   # Comprehensive test suite (80+ tests)

api/                     # Vercel serverless API- ✅ **Domain Models** (`test_models.py`) - Market, Opportunity, Order, Position data structures

```- ✅ **Market Matching** (`test_matching.py`) - Fuzzy matching algorithm, confidence scoring

- ✅ **Opportunity Scoring** (`test_matching.py`) - Profit calculation, fee accounting

## Contributing by Role- ✅ **Trade Validation** (`test_execution.py`) - Pre-trade checks, risk validation

- ✅ **Trade Execution** (`test_execution.py`) - Order creation, paper trading

Pick your lane:- ✅ **Trading Strategies** (`test_strategies.py`) - Opportunity selection, position management

- ✅ **Database** (`test_database.py`) - Data persistence, CRUD operations

**🔵 Data Engineer** → `src/exchanges/` - Fix Kalshi API, add new exchanges  - ✅ **Monitoring** (`test_monitoring.py`) - Position tracking, P&L calculation, alerts

**🟢 Strategy Dev** → `src/strategies/`, `src/services/matching/` - Build algorithms  - ✅ **Integration** (`test_integration.py`) - Full pipeline from market fetch to execution

**🟡 Execution** → `src/services/execution/` - Implement live trading  

**🟠 Portfolio** → `src/services/monitoring/`, `src/models/position.py` - P&L tracking  ---

**🔴 Frontend** → `api/` - Build dashboard, fix endpoints  

**⚫ QA** → `tests/` - Improve test coverage## Prerequisites



## Key Files### Required



| File | What It Does | Edit When |- **Python 3.10+** (3.11 recommended)

|------|-------------|-----------|- **pip** (Python package manager)

| `src/main.py` | Orchestrates bot, runs trading loop | Adding exchanges/strategies |- **Git** (for cloning the repository)

| `src/services/matching/matcher.py` | Finds equivalent markets | Improving matching accuracy |

| `src/services/matching/scorer.py` | Calculates profit | Changing fee structure |### Optional but Recommended

| `src/services/execution/executor.py` | Executes trades | Implementing live trading |

| `src/strategies/simple_arb.py` | Selects best opportunity | Building new strategies |- **Virtual environment** (venv, conda, or virtualenv)

| `src/exchanges/*/client.py` | Exchange API calls | Fixing API issues |- **API Keys**:

  - Kalshi API key ([kalshi.com](https://kalshi.com))

## Configuration  - Polymarket API key ([polymarket.com](https://polymarket.com))

- **Telegram** (for trade alerts)

Edit `.env`:

```bash### System Requirements

KALSHI_API_KEY=your_key

POLYMARKET_API_KEY=your_key- **OS**: Windows, macOS, or Linux

PAPER_TRADING=true        # false for live trading (CAREFUL!)- **RAM**: 2GB minimum

```- **Disk**: 500MB for installation

- **Network**: Stable internet connection for API calls

Edit `src/config/constants.py` for fees, thresholds, limits.

---

## Current Status

## Installation & Setup

✅ **Working**: Market fetching, matching, scoring, validation, paper trading, tests  

⚠️ **Issues**: Kalshi API returns 0 markets, position creation/closing not implemented, live trading disabled  ### 1. Clone the Repository

🚀 **Next**: Fix Kalshi API, implement position lifecycle, enable live trading

```bash

## Development Workflowgit clone https://github.com/Divyesh-Thirukonda/quantshit.git

cd quantshit

1. Pick a task from GitHub Issues```

2. Create branch: `git checkout -b feature/your-feature`

3. Make changes following clean architecture### 2. Create Virtual Environment (Recommended)

4. Run tests: `python run_tests.py`

5. Submit PR```bash

# Using venv

## Design Patternspython -m venv venv



- **Repository Pattern**: All data access through `Repository` class# Activate (Windows)

- **Strategy Pattern**: Extend `BaseStrategy` for new algorithmsvenv\Scripts\activate

- **Single Responsibility**: Each module has one clear job

- **Dependency Inversion**: Services depend on abstractions, not implementations# Activate (macOS/Linux)

source venv/bin/activate

## Running the Bot```



**Single cycle** (runs once):### 3. Install Dependencies

```bash

python src/main.py```bash

```pip install -r requirements.txt

```

**Continuous** (edit `src/main.py`, change `bot.run_once()` to `bot.run_continuous(60)`):

```bash### 4. Configure Environment Variables

python src/main.py  # Runs every 60 seconds

```Create a `.env` file in the project root:



**API Server** (local dev):```bash

```bashcp .env.example .env

vercel dev  # Access at http://localhost:3000```

```

Edit `.env` and add your API keys:

## How It Works (Code Flow)

```bash

```# Exchange API Keys

src/main.py: ArbitrageBot.run_cycle()KALSHI_API_KEY=your_kalshi_key_here

  ↓POLYMARKET_API_KEY=your_polymarket_key_here

1. Fetch markets (exchanges/*/client.py)

  ↓# System Configuration

2. Match markets (services/matching/matcher.py)PAPER_TRADING=true              # Set to false for live trading

  ↓ENABLE_ALERTS=false             # Set to true to enable Telegram alerts

3. Score opportunities (services/matching/scorer.py)LOG_LEVEL=INFO                  # DEBUG, INFO, WARNING, ERROR

  ↓LOG_FILE=quantshit.log

4. Select best (strategies/simple_arb.py)

  ↓# Optional: Telegram Alerts

5. Validate (services/execution/validator.py)TELEGRAM_BOT_TOKEN=your_bot_token

  ↓TELEGRAM_CHAT_ID=your_chat_id

6. Execute (services/execution/executor.py)```

  ↓

7. Monitor positions (services/monitoring/tracker.py)### 5. Verify Installation

```

```bash

Trace the code by following this path through the files. Each step is a single function call.# Run tests to verify everything is set up correctly

python run_tests.py

## Adding Features```



**New Exchange**:All tests should pass (or skip if dependencies are missing).

1. Create `src/exchanges/newexchange/`

2. Implement `client.py` (extend `BaseExchange`)### 6. Initialize Database

3. Implement `parser.py` (API → `Market` model)

4. Add to `src/types.py:Exchange` enumThe bot uses an in-memory database by default. To use SQLite:

5. Wire into `src/main.py`

```bash

**New Strategy**:# Database will be created automatically on first run

1. Extend `src/strategies/base.py:BaseStrategy`python src/main.py

2. Implement `select_best_opportunity()````

3. Use in `src/main.py` instead of `SimpleArbitrageStrategy`

---

**Enable Live Trading** (⚠️ DANGEROUS):

1. Set `PAPER_TRADING=false` in `.env`## Running the System

2. Implement real order placement in `src/services/execution/executor.py:136-138`

3. Test extensively with small positions first!### CLI Mode (Single Cycle)



## Documentation```bash

### CLI Mode (Single Cycle)

- **`docs/MODULE_EXPLANATIONS.md`** - Architecture deep dive

- **`docs/VISUAL_FLOW.md`** - Data flow diagramsRun one complete cycle (fetch markets → find opportunities → execute best trade):

- **`docs/TESTING.md`** - Test suite details

```bash

## Important Warningspython src/main.py

```

⚠️ **Paper Trading Only**: System currently simulates trades. Live trading requires:

- Valid API keys### Continuous Trading Mode

- Real order implementation

- Extensive testingEdit `src/main.py` to enable continuous mode:

- Risk management

```python

⚠️ **Before Going Live**:# In main() function, change:

- Test thoroughly with paper tradingbot.run_once()  # Single cycle

- Start with minimum position sizes# To:

- Set stop losses and position limitsbot.run_continuous(interval_seconds=60)  # Run every 60 seconds

- Understand you can lose money```



## SupportThen run:



- **Issues**: [GitHub Issues](https://github.com/Divyesh-Thirukonda/quantshit/issues)```bash

- **PRs**: [GitHub PRs](https://github.com/Divyesh-Thirukonda/quantshit/pulls)python src/main.py

```

---

Press `Ctrl+C` to stop.

**Built with clean architecture principles** • Paper trading by default • Use at your own risk

### API Server Mode

Start the API server (Vercel serverless function):

```bash
# For local development, you can use Python's http.server or vercel dev
vercel dev
```

Access the API at `http://localhost:3000`

**Available Endpoints:**
- `GET /` - Dashboard UI
- `POST /scan` - Scan for opportunities
- `POST /execute` - Execute a trade
- `POST /run-strategy` - Run full strategy cycle
- `GET /dashboard/stats` - Portfolio statistics

⚠️ **Note:** API server currently has some broken endpoints - see [Current Status](#current-status).

---

## System Overview

### What Does This Bot Do?

The Quantshit arbitrage engine continuously:

1. **Fetches markets** from Kalshi and Polymarket prediction markets
2. **Matches equivalent markets** across exchanges using fuzzy string matching
3. **Calculates profitability** accounting for fees, slippage, and liquidity
4. **Selects the best opportunity** using configurable trading strategies
5. **Validates trades** against risk limits and capital constraints
6. **Executes trades** (currently in paper trading mode)
7. **Monitors positions** and tracks P&L in real-time
8. **Sends alerts** via Telegram when trades execute

### Example Flow

```
User starts bot
    ↓
Bot fetches 150 Kalshi markets + 200 Polymarket markets
    ↓
Matcher finds 45 similar market pairs
    ↓
Scorer identifies 12 profitable opportunities
    ↓
Strategy selects best: "Bitcoin $100k by 2025"
  - Buy on Polymarket @ $0.60
  - Sell on Kalshi @ $0.68
  - Expected profit: $45 (8% return)
    ↓
Validator checks: ✓ Capital available, ✓ Volume sufficient
    ↓
Executor places orders (paper trading)
    ↓
Position tracker monitors for exit opportunity
    ↓
Alert sent to Telegram: "Trade executed: $45 profit"
```

### Core Components

```
┌─────────────────────────────────────────────────────────┐
│                    MAIN ORCHESTRATOR                    │
│                   (src/main.py)                         │
│                                                         │
│  ArbitrageBot coordinates all components               │
└─────────────────────────────────────────────────────────┘
                          │
        ┌─────────────────┼─────────────────┐
        ↓                 ↓                 ↓
   EXCHANGES          SERVICES          STRATEGIES
   ┌─────────┐       ┌─────────┐       ┌──────────┐
   │ Kalshi  │       │Matching │       │ Simple   │
   │ Client  │       │Execution│       │ Arbitrage│
   │─────────│       │Monitor  │       └──────────┘
   │Polymarket       └─────────┘
   └─────────┘             │
        │            ┌─────┴─────┐
        │            ↓           ↓
        │       MODELS      DATABASE
        │      ┌──────┐    ┌─────────┐
        └─────>│Market│───>│Repository
               │Order │    └─────────┘
               │Position
               └──────┘
```

---

## Architecture

Quantshit follows **clean architecture** with strict dependency rules:

```
┌─────────────────────────────────────────────────────────┐
│              OUTER LAYER (Frameworks)                   │
│  main.py, api.py, exchanges/, database/                 │
│  - External dependencies (APIs, DB, file I/O)           │
│  - Can depend on inner layers                           │
│                                                         │
│    ┌──────────────────────────────────────────┐        │
│    │       MIDDLE LAYER (Services)            │        │
│    │  matching/, execution/, monitoring/,     │        │
│    │  strategies/                             │        │
│    │  - Business logic and use cases          │        │
│    │  - Can depend on core layer              │        │
│    │                                          │        │
│    │   ┌──────────────────────────────┐       │        │
│    │   │  INNER LAYER (Core Domain)  │       │        │
│    │   │  models/, types.py          │       │        │
│    │   │  - Pure business entities    │       │        │
│    │   │  - No external dependencies  │       │        │
│    │   └──────────────────────────────┘       │        │
│    └──────────────────────────────────────────┘        │
└─────────────────────────────────────────────────────────┘
```

### Dependency Rules

1. **Inner layers never depend on outer layers**
2. **Dependencies flow inward** (outer → middle → inner)
3. **Core domain is pure** (no external dependencies)
4. **Interfaces define boundaries** (e.g., BaseExchange, Repository)

### Dependency Rules

1. **Inner layers never depend on outer layers**
2. **Dependencies flow inward** (outer → middle → inner)
3. **Core domain is pure** (no external dependencies)
4. **Interfaces define boundaries** (e.g., BaseExchange, Repository)

---

## Directory Structure

### Complete Project Layout

```
quantshit/
│
├── 📄 README.md                    # This file - complete project documentation
├── 📄 requirements.txt             # Python dependencies
├── 📄 .env.example                 # Environment variables template
├── 📄 .env                         # Your local configuration (not in git)
├── 📄 run_tests.py                 # Test runner script
├── 📄 vercel.json                  # Vercel deployment configuration
├── 📄 supabase_schema.sql          # Database schema for Supabase
│
├── 📁 src/                         # Main application code
│   ├── 📄 main.py                  # 🤖 MAIN ORCHESTRATOR - Entry point, wires everything together
│   ├── 📄 scanner.py               # Market scanner (legacy/alternative)
│   ├── 📄 types.py                 # 🎯 Core enums: Exchange, OrderSide, OrderStatus, Outcome
│   │
│   ├── 📁 models/                  # 📦 DOMAIN MODELS (Inner Layer - Core)
│   │   ├── __init__.py
│   │   ├── market.py               # Market data structure (price, volume, liquidity)
│   │   ├── order.py                # Order data structure (buy/sell, status, fills)
│   │   ├── position.py             # Position tracking (entry, P&L, status)
│   │   └── opportunity.py          # Arbitrage opportunity (spread, profit, confidence)
│   │
│   ├── 📁 config/                  # ⚙️ CONFIGURATION
│   │   ├── __init__.py
│   │   ├── settings.py             # Environment variables (API keys, feature flags)
│   │   └── constants.py            # Business constants (fees, thresholds, limits)
│   │
│   ├── 📁 utils/                   # 🛠️ SHARED UTILITIES
│   │   ├── __init__.py
│   │   ├── logger.py               # Logging configuration and setup
│   │   ├── math.py                 # Profit calculations, decimal handling
│   │   └── decorators.py           # Retry logic, rate limiting, error handling
│   │
│   ├── 📁 services/                # 🎯 BUSINESS LOGIC (Middle Layer)
│   │   ├── __init__.py
│   │   │
│   │   ├── 📁 matching/            # Market matching and opportunity scoring
│   │   │   ├── __init__.py
│   │   │   ├── matcher.py          # Find equivalent markets (fuzzy matching)
│   │   │   └── scorer.py           # Calculate profitability (fees, slippage)
│   │   │
│   │   ├── 📁 execution/           # Trade execution and validation
│   │   │   ├── __init__.py
│   │   │   ├── validator.py        # Pre-trade validation (capital, risk, volume)
│   │   │   └── executor.py         # Execute trades (paper/live mode)
│   │   │
│   │   └── 📁 monitoring/          # Position tracking and alerts
│   │       ├── __init__.py
│   │       ├── tracker.py          # Track positions, calculate P&L
│   │       └── alerter.py          # Send notifications (Telegram)
│   │
│   ├── 📁 strategies/              # 📊 TRADING STRATEGIES
│   │   ├── __init__.py
│   │   ├── base.py                 # Abstract base class for all strategies
│   │   ├── config.py               # Strategy configuration classes
│   │   └── simple_arb.py           # Simple arbitrage strategy (highest profit)
│   │
│   ├── 📁 exchanges/               # 🔌 EXCHANGE INTEGRATIONS (Outer Layer)
│   │   ├── __init__.py
│   │   ├── base.py                 # Abstract exchange interface (contract)
│   │   │
│   │   ├── 📁 kalshi/              # Kalshi exchange implementation
│   │   │   ├── __init__.py
│   │   │   ├── client.py           # Kalshi API client (fetch markets, place orders)
│   │   │   └── parser.py           # Parse Kalshi API → Market model
│   │   │
│   │   └── 📁 polymarket/          # Polymarket exchange implementation
│   │       ├── __init__.py
│   │       ├── client.py           # Polymarket API client
│   │       └── parser.py           # Parse Polymarket API → Market model
│   │
│   └── 📁 database/                # 💾 DATA PERSISTENCE (Outer Layer)
│       ├── __init__.py
│       ├── repository.py           # Repository pattern (in-memory implementation)
│       ├── sqlite_repository.py    # SQLite implementation (alternative)
│       └── schema.py               # Database schema definitions
│
├── 📁 api/                         # 🌐 API SERVER (Vercel Serverless)
│   ├── index.py                    # HTTP handler entry point (BaseHTTPRequestHandler)
│   ├── api_handlers.py             # API route handlers
│   └── supabase_client.py          # Supabase database client
│
├── 📁 tests/                       # ✅ TEST SUITE
│   ├── __init__.py
│   ├── conftest.py                 # Pytest fixtures (sample data for tests)
│   ├── test_models.py              # Test domain models
│   ├── test_matching.py            # Test matching and scoring
│   ├── test_execution.py           # Test validation and execution
│   ├── test_strategies.py          # Test trading strategies
│   ├── test_database.py            # Test data persistence
│   ├── test_monitoring.py          # Test tracking and alerts
│   └── test_integration.py         # Test full pipeline end-to-end
│
├── 📁 docs/                        # 📚 DOCUMENTATION
│   ├── MODULE_EXPLANATIONS.md      # Detailed module documentation
│   ├── VISUAL_FLOW.md              # Data flow diagrams
│   ├── TESTING.md                  # Testing documentation
│   ├── DATABASE_SYSTEM.md          # Database architecture
│   ├── KALSHI_FIX.md               # Kalshi integration notes
│   ├── PAGINATION_IMPLEMENTATION.md # API pagination guide
│   ├── STRATEGY_CONFIG_REFACTOR.md # Strategy configuration changes
│   └── TEST_SUITE_SUMMARY.md       # Test coverage summary
│
├── 📁 examples/                    # 📝 EXAMPLE CODE
│   └── custom_strategy_config.py   # Example: Create custom strategy
│
└── 📁 scripts/                     # 🔧 UTILITY SCRIPTS
    └── db_query.py                 # Database query helper
```

### Key Files Explained

| File | Purpose | When to Edit |
|------|---------|--------------|
| `src/main.py` | Main orchestrator - wires all components together | Adding new exchanges, strategies, or changing main loop |
| `src/types.py` | Core enums used across the system | Adding new exchange, order type, or status |
| `src/models/*.py` | Domain models (pure data structures) | Changing data structures or adding fields |
| `src/config/settings.py` | Environment configuration | Adding new environment variables |
| `src/config/constants.py` | Business constants (fees, limits) | Changing fees, thresholds, or business rules |
| `src/services/matching/matcher.py` | Market matching algorithm | Improving matching accuracy |
| `src/services/matching/scorer.py` | Profit calculation | Changing fee structure or profit formula |
| `src/services/execution/validator.py` | Trade validation rules | Adding new risk checks |
| `src/services/execution/executor.py` | Trade execution logic | Implementing live trading |
| `src/strategies/simple_arb.py` | Trading strategy logic | Changing opportunity selection criteria |
| `src/exchanges/*/client.py` | Exchange API integration | Fixing API issues or adding endpoints |
| `src/database/repository.py` | Data persistence layer | Adding new queries or data operations |
| `run_tests.py` | Test runner | Adding new test categories |

---

## How It Works: Code Flow

### Tracing a Complete Cycle

Follow the code execution step-by-step through the bot:

#### 1️⃣ **Initialization** (`src/main.py:36-98`)

```python
bot = ArbitrageBot()  # Line 318
```

**What happens:**
- Validates configuration (`settings.validate()`)
- Initializes database (`init_database()`)
- Creates exchange clients (`KalshiClient`, `PolymarketClient`)
- Creates services (`Matcher`, `Scorer`, `Validator`, `Executor`)
- Creates monitoring (`Tracker`, `Alerter`)
- Creates strategy (`SimpleArbitrageStrategy`)

**Files involved:**
- `src/main.py` → `ArbitrageBot.__init__()`
- `src/config/settings.py` → `Settings.validate()`
- `src/exchanges/kalshi/client.py` → `KalshiClient()`
- `src/exchanges/polymarket/client.py` → `PolymarketClient()`

#### 2️⃣ **Start Cycle** (`src/main.py:100-104`)

```python
bot.run_cycle()  # Line 321 or 324
```

**What happens:**
- Logs cycle start
- Increments cycle counter
- Wraps everything in try/except for error handling

**Files involved:**
- `src/main.py` → `ArbitrageBot.run_cycle()`

#### 3️⃣ **Fetch Markets** (`src/main.py:106-110`)

```python
kalshi_markets, polymarket_markets = self._fetch_markets()
```

**What happens:**
- Calls Kalshi API to fetch active markets
- Calls Polymarket API to fetch active markets
- Parses API responses into `Market` models
- Filters by minimum volume from strategy config

**Files involved:**
- `src/main.py` → `_fetch_markets()`
- `src/exchanges/kalshi/client.py` → `get_markets()`
- `src/exchanges/kalshi/parser.py` → Parse response
- `src/exchanges/polymarket/client.py` → `get_markets()`
- `src/exchanges/polymarket/parser.py` → Parse response
- `src/models/market.py` → `Market` data structure

**API Calls:**
- `GET /markets` on Kalshi
- `GET /markets` on Polymarket

#### 4️⃣ **Match Markets** (`src/main.py:112-116`)

```python
matched_pairs = self.matcher.find_matches(kalshi_markets, polymarket_markets)
```

**What happens:**
- Compares all Kalshi markets against all Polymarket markets
- Normalizes titles (lowercase, remove punctuation)
- Calculates Jaccard similarity (word overlap)
- Filters matches above threshold (default 0.5)
- Returns list of (kalshi_market, polymarket_market, confidence_score)

**Files involved:**
- `src/services/matching/matcher.py` → `find_matches()`

**Algorithm:**
```python
similarity = len(words_A ∩ words_B) / len(words_A ∪ words_B)
if similarity >= threshold:
    matches.append((market_A, market_B, similarity))
```

#### 5️⃣ **Score Opportunities** (`src/main.py:122-129`)

```python
opportunities = self.scorer.score_opportunities(matched_pairs)
```

**What happens:**
- For each matched pair, calculates potential profit
- Accounts for Kalshi fees (0.7%), Polymarket fees (2%), slippage (1%)
- Filters opportunities below minimum profit threshold (2%)
- Creates `Opportunity` objects with profit metrics
- Saves to repository

**Files involved:**
- `src/services/matching/scorer.py` → `score_opportunities()`
- `src/models/opportunity.py` → `Opportunity` data structure
- `src/database/repository.py` → `save_opportunity()`

**Formula:**
```python
spread = |price_kalshi - price_polymarket|
profit = spread - fee_kalshi - fee_polymarket - slippage
profit_pct = profit / capital_invested
```

#### 6️⃣ **Select Best Opportunity** (`src/main.py:135-148`)

```python
best_opportunity = self.strategy.select_best_opportunity(opportunities)
```

**What happens:**
- Strategy filters opportunities by:
  - Minimum volume (configurable)
  - Minimum confidence (configurable)
  - Minimum profit percentage
- Selects opportunity with highest expected profit
- Returns `None` if no opportunities meet criteria

**Files involved:**
- `src/strategies/simple_arb.py` → `select_best_opportunity()`
- `src/strategies/config.py` → `SimpleArbitrageConfig`

#### 7️⃣ **Validate Trade** (`src/main.py:150-156`)

```python
validation = self.validator.validate(best_opportunity)
```

**What happens:**
- Checks if sufficient capital available
- Checks if volume is adequate for position size
- Checks if spread is still valid
- Returns `ValidationResult` with pass/fail and reason

**Files involved:**
- `src/services/execution/validator.py` → `validate()`

**Validation Checks:**
- `capital_required <= available_capital`
- `volume >= min_position_size`
- `confidence_score >= min_confidence`

#### 8️⃣ **Execute Trade** (`src/main.py:163-192`)

```python
execution = self.executor.execute(best_opportunity)
```

**What happens:**
- Creates buy order for lower-priced exchange
- Creates sell order for higher-priced exchange
- In paper mode: simulates order fills
- In live mode: calls exchange APIs (not implemented)
- Saves orders to repository
- Returns `ExecutionResult`

**Files involved:**
- `src/services/execution/executor.py` → `execute()`
- `src/models/order.py` → `Order` data structure
- `src/database/repository.py` → `save_order()`

**Order Creation:**
```python
buy_order = Order(
    exchange=lower_price_exchange,
    side=OrderSide.BUY,
    price=lower_price,
    quantity=position_size
)
sell_order = Order(
    exchange=higher_price_exchange,
    side=OrderSide.SELL,
    price=higher_price,
    quantity=position_size
)
```

#### 9️⃣ **Monitor Positions** (`src/main.py:197-219`)

```python
self._monitor_positions()
```

**What happens:**
- Fetches all open positions from repository
- Updates current prices for each position
- Calculates unrealized P&L
- Checks if any positions should be closed
- Logs summary statistics

**Files involved:**
- `src/main.py` → `_monitor_positions()`
- `src/services/monitoring/tracker.py` → `update_position()`, `get_summary()`
- `src/strategies/simple_arb.py` → `should_close_position()`

#### 🔟 **Send Alerts** (`src/main.py:176-188`)

```python
self.alerter.alert_trade_executed(...)
```

**What happens:**
- If alerts enabled, sends Telegram message
- Includes profit, market title, success/failure
- Sends error alerts on failures

**Files involved:**
- `src/services/monitoring/alerter.py` → `alert_trade_executed()`, `alert_error()`

---

## Development Guide by Role

### 🎨 **Role-Based Development Map**

```
┌────────────────────────────────────────────────────────────┐
│                    DEVELOPER ROLES                         │
└────────────────────────────────────────────────────────────┘

🔵 DATA ACQUISITION ENGINEER
   Focus: Fetching market data from exchanges
   Files: src/exchanges/*/client.py, src/exchanges/*/parser.py
   Tasks: Fix Kalshi API, add new exchanges, improve data quality
   
🟢 STRATEGY DEVELOPER  
   Focus: Trading algorithms and opportunity selection
   Files: src/strategies/*.py, src/services/matching/*
   Tasks: Build new strategies, improve matching, optimize selection
   
🟡 EXECUTION ENGINEER
   Focus: Trade execution and order management  
   Files: src/services/execution/*.py
   Tasks: Implement live trading, handle order failures, manage positions
   
🟠 PORTFOLIO MANAGER
   Focus: Position tracking, P&L, risk management
   Files: src/services/monitoring/*, src/models/position.py
   Tasks: Improve P&L calc, add risk limits, position lifecycle
   
🔴 API/FRONTEND DEVELOPER
   Focus: Web interface and API endpoints
   Files: api/*, vercel.json
   Tasks: Build dashboard, fix endpoints, add visualizations
   
🟣 DEVOPS/DEPLOYMENT
   Focus: Deployment, infrastructure, monitoring
   Files: vercel.json, requirements.txt, scripts/*
   Tasks: Deploy to prod, setup CI/CD, monitoring/alerting
   
⚫ QA/TESTING ENGINEER
   Focus: Test coverage, validation, quality
   Files: tests/*, run_tests.py
   Tasks: Write tests, improve coverage, integration testing
```

### Developer Guides by Role

#### 🔵 Data Acquisition Engineer

**Your Mission:** Fetch high-quality market data from exchanges reliably.

**Files You'll Work With:**
- `src/exchanges/kalshi/client.py` - Kalshi API integration
- `src/exchanges/kalshi/parser.py` - Parse Kalshi responses
- `src/exchanges/polymarket/client.py` - Polymarket API integration
- `src/exchanges/polymarket/parser.py` - Parse Polymarket responses
- `src/exchanges/base.py` - Exchange interface (contract)
- `src/models/market.py` - Market data structure

**Common Tasks:**
1. **Fix Kalshi API Integration** (Currently returns 0 markets)
   - Check authentication in `src/exchanges/kalshi/client.py:22`
   - Verify API endpoint and request format
   - Test with Kalshi API documentation
   
2. **Add New Exchange**
   - Create `src/exchanges/newexchange/` directory
   - Implement `client.py` extending `BaseExchange`
   - Implement `parser.py` to convert API → `Market` model
   - Add exchange to `src/types.py:Exchange` enum
   - Wire into `src/main.py`

3. **Improve Data Quality**
   - Add data validation in parsers
   - Handle missing/malformed data gracefully
   - Add retry logic for failed requests
   - Implement caching to reduce API calls

**Testing Your Changes:**
```bash
# Test exchange clients
python run_tests.py  # Will need to add exchange tests

# Manual testing
python -c "from src.exchanges.kalshi import KalshiClient; \
           client = KalshiClient('your_key'); \
           markets = client.get_markets(); \
           print(f'Fetched {len(markets)} markets')"
```

**What to Consider:**
- API rate limits (use `@rate_limit` decorator from `src/utils/decorators.py`)
- API authentication (keys, tokens, OAuth)
- Error handling (network failures, invalid responses)
- Data normalization (different exchanges have different formats)
- Testing with real API vs mocked data

---

#### 🟢 Strategy Developer

**Your Mission:** Build intelligent algorithms to select profitable opportunities.

**Files You'll Work With:**
- `src/strategies/simple_arb.py` - Current simple strategy
- `src/strategies/base.py` - Base class for all strategies
- `src/strategies/config.py` - Strategy configuration
- `src/services/matching/matcher.py` - Market matching
- `src/services/matching/scorer.py` - Profit calculation
- `src/models/opportunity.py` - Opportunity data structure

**Common Tasks:**
1. **Create New Strategy**
   ```python
   # src/strategies/my_strategy.py
   from .base import BaseStrategy
   from .config import BaseStrategyConfig
   
   class MyStrategyConfig(BaseStrategyConfig):
       custom_param: float = 0.5
   
   class MyStrategy(BaseStrategy):
       def __init__(self, config: MyStrategyConfig):
           super().__init__(config)
       
       def select_best_opportunity(self, opportunities):
           # Your logic here
           pass
       
       def should_close_position(self, position):
           # Your logic here
           pass
   ```

2. **Improve Market Matching**
   - Enhance similarity algorithm in `matcher.py`
   - Add semantic matching (ML-based)
   - Consider market categories, tags, keywords
   - Improve confidence scoring

3. **Optimize Opportunity Selection**
   - Add risk-adjusted returns (Sharpe ratio)
   - Consider historical performance
   - Factor in market liquidity depth
   - Multi-objective optimization (profit vs risk vs probability)

**Testing Your Changes:**
```bash
# Test strategies
python run_tests.py strategies

# Test matching
python run_tests.py matching
```

**What to Consider:**
- Profitability vs probability tradeoff
- Risk management (position sizing, stop losses)
- Market conditions (volatility, liquidity)
- Strategy parameter optimization (backtesting)
- Multiple simultaneous positions

---

#### 🟡 Execution Engineer

**Your Mission:** Execute trades reliably and handle order lifecycle.

**Files You'll Work With:**
- `src/services/execution/executor.py` - Trade execution
- `src/services/execution/validator.py` - Pre-trade validation
- `src/models/order.py` - Order data structure
- `src/exchanges/*/client.py` - Exchange order APIs

**Common Tasks:**
1. **Implement Live Trading** (Currently paper trading only)
   - Implement real order placement in `executor.py:136-138`
   - Call exchange APIs: `client.place_order()`
   - Handle order responses (order ID, status, fills)
   - Implement order status polling
   
2. **Handle Order Failures**
   - Timeout handling
   - Partial fills
   - Order rejections
   - Retry logic with backoff
   
3. **Order Lifecycle Management**
   - Order status updates (pending → filled → closed)
   - Cancel orders
   - Modify orders
   - Handle multiple order types (limit, market, stop)

**Testing Your Changes:**
```bash
# Test execution
python run_tests.py execution

# Test with paper trading first
PAPER_TRADING=true python src/main.py
```

**What to Consider:**
- Exchange-specific order requirements
- Order timing and execution speed
- Slippage management
- Transaction costs and fees
- Error recovery and rollback
- Order matching and fills

---

#### 🟠 Portfolio Manager

**Your Mission:** Track positions, calculate P&L, manage risk.

**Files You'll Work With:**
- `src/services/monitoring/tracker.py` - Position tracking
- `src/services/monitoring/alerter.py` - Alerts and notifications
- `src/models/position.py` - Position data structure
- `src/main.py` - Position lifecycle (create, update, close)

**Common Tasks:**
1. **Implement Position Creation** (Currently not implemented)
   - Create position from executed orders (`main.py:182-184`)
   - Link position to opportunity
   - Set entry prices and quantities
   
2. **Implement Position Closing** (Currently not implemented)
   - Detect when to close positions (`main.py:242-245`)
   - Execute closing trades
   - Calculate realized P&L
   - Update position status
   
3. **Enhance P&L Calculation**
   - Real-time mark-to-market
   - Unrealized vs realized P&L
   - Fee attribution
   - Historical performance tracking

4. **Add Risk Management**
   - Position size limits
   - Portfolio-level risk (VaR, max drawdown)
   - Correlation between positions
   - Stop losses and take profits

**Testing Your Changes:**
```bash
# Test monitoring
python run_tests.py monitoring

# Test full pipeline
python run_tests.py integration
```

**What to Consider:**
- Position lifecycle states
- P&L calculation accuracy
- Risk metrics and limits
- Performance attribution
- Position exit strategies

---

#### 🔴 API/Frontend Developer

**Your Mission:** Build web interface and API for the bot.

**Files You'll Work With:**
- `api/index.py` - HTTP server entry point (BaseHTTPRequestHandler)
- `api/api_handlers.py` - API route handlers
- `api/supabase_client.py` - Database client for API
- `vercel.json` - Deployment configuration

**Common Tasks:**
1. **Fix Broken Endpoints** (See CLAUDE.md TODO)
   - Fix endpoints referencing non-existent methods
   - Update API handlers to use new architecture
   - Add proper error handling
   
2. **Build Dashboard UI**
   - Real-time opportunity display
   - Position tracking dashboard
   - P&L charts and metrics
   - Trade history
   
3. **Add API Endpoints**
   ```python
   @app.get("/api/opportunities")
   async def get_opportunities():
       # Return current opportunities
       pass
   
   @app.get("/api/positions")
   async def get_positions():
       # Return open positions
       pass
   ```

4. **WebSocket Support**
   - Real-time updates for dashboard
   - Live P&L streaming
   - Order status updates

**Testing Your Changes:**
```bash
# Start API server locally
vercel dev

# Test endpoints
curl http://localhost:3000/api/opportunities
```

**What to Consider:**
- API authentication and security
- Rate limiting
- CORS configuration
- Error responses and status codes
- WebSocket connections
- Frontend framework (React, Vue, etc.)

---

#### 🟣 DevOps/Deployment Engineer

**Your Mission:** Deploy bot to production, ensure reliability.

**Files You'll Work With:**
- `vercel.json` - Vercel deployment config
- `requirements.txt` - Python dependencies
- `.env.example` - Environment template
- `scripts/` - Utility scripts

**Common Tasks:**
1. **Setup CI/CD Pipeline**
   - GitHub Actions for automated testing
   - Automated deployment to Vercel
   - Environment management (dev, staging, prod)
   
2. **Production Deployment**
   - Deploy API to Vercel
   - Deploy bot to cloud (AWS, GCP, Azure)
   - Setup scheduled runs (cron jobs)
   - Configure secrets management
   
3. **Monitoring and Alerting**
   - Application monitoring (Datadog, NewRelic)
   - Error tracking (Sentry)
   - Performance metrics
   - Uptime monitoring
   
4. **Infrastructure**
   - Database setup (PostgreSQL, Supabase)
   - Message queue (for async processing)
   - Caching (Redis)
   - Load balancing

**Testing Your Changes:**
```bash
# Test deployment locally
vercel dev

# Deploy to preview
vercel

# Deploy to production
vercel --prod
```

**What to Consider:**
- Secrets and API key management
- Database migrations
- Scaling and performance
- Cost optimization
- Disaster recovery and backups
- Logging and monitoring

---

#### ⚫ QA/Testing Engineer

**Your Mission:** Ensure code quality and comprehensive test coverage.

**Files You'll Work With:**
- `tests/` - All test files
- `run_tests.py` - Test runner
- `tests/conftest.py` - Test fixtures

**Common Tasks:**
1. **Improve Test Coverage**
   - Identify untested code paths
   - Add unit tests for new features
   - Add integration tests for workflows
   - Add end-to-end tests
   
2. **Performance Testing**
   - Load testing API endpoints
   - Benchmark critical algorithms
   - Test with large datasets
   
3. **Test Automation**
   - Setup CI/CD testing
   - Automated regression testing
   - Test result reporting
   
4. **Quality Metrics**
   - Code coverage reports
   - Test execution time
   - Flaky test detection

**Testing Your Changes:**
```bash
# Run all tests with coverage
python run_tests.py all

# Generate coverage report
# View htmlcov/index.html
```

**What to Consider:**
- Test data quality (fixtures)
- Test isolation (no shared state)
- Mock external dependencies (APIs)
- Test execution speed
- Continuous integration

---

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

## Current Status

### ✅ Working

- ✓ Clean architecture implemented with separation of concerns
- ✓ Exchange clients for Kalshi and Polymarket
- ✓ Market matching algorithm (fuzzy string matching)
- ✓ Opportunity scoring with fees and slippage
- ✓ Trade validation and risk checks
- ✓ Paper trading mode (simulated execution)
- ✓ Position tracking and P&L monitoring
- ✓ API server with endpoints (Vercel serverless)
- ✓ **Comprehensive test suite with 80+ tests**
- ✓ **Test runner for easy testing (`python run_tests.py`)**

### 🚧 In Progress / Known Issues

- ⚠️ **Kalshi API returns 0 markets** (endpoint/auth issue)
  - See `src/exchanges/kalshi/client.py:22`
  - Needs investigation and fix
  
- ⚠️ **Position creation not implemented**
  - See `src/main.py:182-184`
  - Need to create Position from ExecutionResult
  
- ⚠️ **Position closing logic not implemented**
  - See `src/main.py:242-245`
  - Need to implement close decision + execution
  
- ⚠️ **Real order placement disabled**
  - See `src/services/execution/executor.py:136-138`
  - Only paper trading works currently
  - **CRITICAL:** Test thoroughly before enabling
  
- ⚠️ **API server has broken endpoints**
  - References non-existent methods from old architecture
  - Needs refactoring to use new components

### 📋 Next Steps

1. Fix Kalshi API integration
2. Implement position lifecycle (create → update → close)
3. Thoroughly test with paper trading
4. Implement live trading with small positions
5. Add more comprehensive error handling
6. Build web dashboard UI
7. Add backtesting framework
8. Expand to more exchanges

---

## 📚 Additional Documentation

- **`CLAUDE.md`** - Complete project overview, detailed TODO list
- **`docs/MODULE_EXPLANATIONS.md`** - Theoretical design of clean architecture
- **`docs/VISUAL_FLOW.md`** - Data flow diagrams and dependency rules
- **`docs/TESTING.md`** - Test suite documentation
- **`docs/DATABASE_SYSTEM.md`** - Database architecture
- **`docs/STRATEGY_CONFIG_REFACTOR.md`** - Strategy configuration changes

---

## ⚠️ **Important Warnings**

### Paper Trading Only

This system currently operates in **simulation mode only**. Real trading requires:

- ✓ Valid API keys for both exchanges
- ✓ Implementation of real order placement logic
- ✓ Thorough testing with small positions
- ✓ Risk management review
- ✓ Capital you can afford to lose

### Before Going Live

1. **Test extensively** with paper trading
2. **Start small** - use minimum position sizes
3. **Monitor closely** - watch for errors and unexpected behavior
4. **Set limits** - implement stop losses and position size limits
5. **Understand risks** - prediction markets can be volatile
6. **Legal compliance** - ensure trading is legal in your jurisdiction

### Risk Disclaimer

Trading prediction markets involves substantial risk of loss. This software is provided "as is" without warranty. The developers are not responsible for any losses incurred. Use at your own risk.

---

## 📞 Support & Contact

- **Issues**: [GitHub Issues](https://github.com/Divyesh-Thirukonda/quantshit/issues)
- **Discussions**: [GitHub Discussions](https://github.com/Divyesh-Thirukonda/quantshit/discussions)
- **Pull Requests**: [GitHub PRs](https://github.com/Divyesh-Thirukonda/quantshit/pulls)

---

## 📄 License

[Add your license here]

---

**Built with ❤️ using Clean Architecture principles**

