# 🎯 Quantshit - Prediction Market Arbitrage Bot

> **A high-performance arbitrage trading system for prediction markets (Kalshi & Polymarket) with automated scanning, matching, execution, and portfolio management.**

[![Python 3.8+](https://img.shields.io/badge/python-3.8+-blue.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)

---

## 📑 Table of Contents

1. [Quick Start](#-quick-start)
2. [System Overview](#-system-overview)
3. [Architecture & Flow](#-architecture--flow)
4. [Directory Structure](#-directory-structure)
5. [Development Guide](#-development-guide)
6. [Developer Lanes](#-developer-lanes)
7. [Commands & Scripts](#-commands--scripts)
8. [Testing](#-testing)
9. [API Documentation](#-api-documentation)
10. [Configuration](#-configuration)
11. [Deployment](#-deployment)
12. [Contributing](#-contributing)

---

## 🚀 Quick Start

### Prerequisites
- Python 3.8+
- pip
- Git

### One-Time Setup

```bash
# 1. Clone the repository
git clone <repo-url>
cd quantshit

# 2. Create and activate virtual environment
python -m venv venv
.\venv\Scripts\activate  # Windows
# source venv/bin/activate  # macOS/Linux

# 3. Install dependencies
pip install -r requirements.txt

# 4. Set up environment variables
cp .env.example .env
# Edit .env with your API keys and configuration

# 5. Initialize database
python -c "from src.database import init_database; init_database()"

# 6. Run tests to verify setup
python run_tests.py fast
```

### Running the Bot

```bash
# Paper trading mode (default - no real money)
python -m src.main

# Scanner mode (fetch markets and find opportunities)
python -m src.scanner

# Start API server locally
vercel dev
```

---

## 🏗️ System Overview

### What Does This Bot Do?

The Quantshit arbitrage bot automatically:

1. **Scans** prediction markets from Kalshi and Polymarket
2. **Matches** similar markets across exchanges using NLP
3. **Detects** arbitrage opportunities with guaranteed profits
4. **Validates** opportunities against capital, fees, and risk limits
5. **Executes** trades across both exchanges simultaneously
6. **Monitors** positions and manages portfolio risk
7. **Reports** performance metrics and alerts

### Core Concept: Arbitrage

When the same event is priced differently on two exchanges, you can:
- Buy YES on Exchange A at $0.60
- Sell YES (buy NO) on Exchange B at $0.45
- **Guaranteed profit**: $1.00 - $0.60 - $0.45 = -$0.05 (after fees, if positive = profit!)

---

## 🔄 Architecture & Flow

### High-Level Data Flow

```
┌─────────────────────────────────────────────────────────────────────┐
│                         ARBITRAGE BOT PIPELINE                       │
└─────────────────────────────────────────────────────────────────────┘

1. DATA ACQUISITION (exchanges/)
   ┌─────────────┐         ┌──────────────────┐
   │   Kalshi    │────────▶│  KalshiClient    │
   │     API     │         │    - Fetch       │
   └─────────────┘         │    - Parse       │
                           │    - Normalize   │
   ┌─────────────┐         └──────────────────┘
   │ Polymarket  │────────▶│PolymarketClient  │
   │     API     │         │    - Fetch       │
   └─────────────┘         │    - Parse       │
                           │    - Normalize   │
                           └──────────────────┘
                                    │
                                    ▼
2. DATA STORAGE (database/)
                           ┌──────────────────┐
                           │   Repository     │
                           │  - Markets       │
                           │  - Opportunities │
                           │  - Positions     │
                           │  - Orders        │
                           └──────────────────┘
                                    │
                                    ▼
3. MARKET MATCHING (services/matching/)
                           ┌──────────────────┐
                           │     Matcher      │
                           │  - Title NLP     │
                           │  - Fuzzy Match   │
                           │  - Similarity    │
                           └──────────────────┘
                                    │
                                    ▼
4. OPPORTUNITY SCORING (services/matching/)
                           ┌──────────────────┐
                           │     Scorer       │
                           │  - Calculate P&L │
                           │  - Apply Fees    │
                           │  - Slippage      │
                           │  - Confidence    │
                           └──────────────────┘
                                    │
                                    ▼
5. STRATEGY FILTERING (strategies/)
                           ┌──────────────────┐
                           │   Strategy       │
                           │  - Filter        │
                           │  - Rank          │
                           │  - Select Best   │
                           └──────────────────┘
                                    │
                                    ▼
6. VALIDATION (services/execution/)
                           ┌──────────────────┐
                           │    Validator     │
                           │  - Capital Check │
                           │  - Risk Limits   │
                           │  - Market Health │
                           └──────────────────┘
                                    │
                                    ▼
7. EXECUTION (services/execution/)
                           ┌──────────────────┐
                           │    Executor      │
                           │  - Create Orders │
                           │  - Submit Trades │
                           │  - Track Status  │
                           └──────────────────┘
                                    │
                                    ▼
8. MONITORING (services/monitoring/)
                           ┌──────────────────┐
                           │   Tracker +      │
                           │   Alerter        │
                           │  - P&L Tracking  │
                           │  - Risk Monitor  │
                           │  - Alerts        │
                           └──────────────────┘
```

### Code Execution Flow

**Function-by-Function Trace** (Start → End):

```python
# Entry Point
main.py::main()
  └─▶ ArbitrageBot.__init__()
      ├─▶ init_database()  # database/__init__.py
      ├─▶ KalshiClient()   # exchanges/kalshi/client.py
      ├─▶ PolymarketClient()  # exchanges/polymarket/client.py
      ├─▶ Matcher()  # services/matching/matcher.py
      ├─▶ Scorer()   # services/matching/scorer.py
      └─▶ Executor() # services/execution/executor.py

# Main Trading Loop
ArbitrageBot.run()
  └─▶ ArbitrageBot._trading_cycle()
      │
      ├─▶ 1. FETCH MARKETS
      │   ├─▶ kalshi_client.get_markets()
      │   │   └─▶ parser.parse_markets()  # exchanges/kalshi/parser.py
      │   └─▶ polymarket_client.get_markets()
      │       └─▶ parser.parse_markets()  # exchanges/polymarket/parser.py
      │
      ├─▶ 2. STORE IN DATABASE
      │   └─▶ repository.save_markets_batch()  # database/repository.py
      │
      ├─▶ 3. FIND MATCHES
      │   └─▶ matcher.find_matches()  # services/matching/matcher.py
      │       ├─▶ _normalize_title()
      │       ├─▶ _calculate_similarity()
      │       └─▶ _fuzzy_match()
      │
      ├─▶ 4. SCORE OPPORTUNITIES
      │   └─▶ scorer.score_match()  # services/matching/scorer.py
      │       ├─▶ _calculate_profit()
      │       ├─▶ _apply_fees()
      │       └─▶ _calculate_confidence()
      │
      ├─▶ 5. APPLY STRATEGY
      │   └─▶ strategy.select_best_opportunity()  # strategies/simple_arb.py
      │       ├─▶ filter_opportunities()
      │       └─▶ rank_opportunities()
      │
      ├─▶ 6. VALIDATE
      │   └─▶ validator.validate_opportunity()  # services/execution/validator.py
      │       ├─▶ _check_capital()
      │       ├─▶ _check_liquidity()
      │       └─▶ _check_risk_limits()
      │
      ├─▶ 7. EXECUTE
      │   └─▶ executor.execute_opportunity()  # services/execution/executor.py
      │       ├─▶ _create_orders()
      │       ├─▶ _submit_order()  # calls exchange clients
      │       └─▶ repository.save_order()
      │
      └─▶ 8. MONITOR
          └─▶ tracker.update_positions()  # services/monitoring/tracker.py
              ├─▶ _calculate_pnl()
              └─▶ alerter.send_alert()  # services/monitoring/alerter.py
```

### File-by-File Trace

| Step | Files Involved | What Happens |
|------|---------------|--------------|
| **Startup** | `main.py` → `config/settings.py` → `database/__init__.py` | Load config, initialize DB |
| **Fetch** | `exchanges/kalshi/client.py` + `exchanges/polymarket/client.py` | HTTP requests to APIs |
| **Parse** | `exchanges/kalshi/parser.py` + `exchanges/polymarket/parser.py` | Raw JSON → `Market` objects |
| **Store** | `database/repository.py` → `database/schema.py` | Save to DB |
| **Match** | `services/matching/matcher.py` | Compare titles using NLP |
| **Score** | `services/matching/scorer.py` → `utils/math.py` | Calculate profit & confidence |
| **Filter** | `strategies/simple_arb.py` → `strategies/base.py` | Apply strategy rules |
| **Validate** | `services/execution/validator.py` | Check limits |
| **Execute** | `services/execution/executor.py` → exchange clients | Submit orders |
| **Monitor** | `services/monitoring/tracker.py` + `alerter.py` | Track P&L, send alerts |

---

## 📂 Directory Structure

```
quantshit/
│
├── 📄 requirements.txt        # Python dependencies
├── 📄 run_tests.py           # Test runner script
├── 📄 vercel.json            # Deployment config for Vercel
├── 📄 supabase_schema.sql    # Database schema
│
├── 📁 api/                   # 🌐 API & FRONTEND
│   ├── index.py              # Main API handler (routes requests)
│   ├── api_handlers.py       # Endpoint handlers (scan, execute, etc.)
│   └── supabase_client.py    # Supabase database client
│
├── 📁 src/                   # 🧠 CORE APPLICATION
│   ├── main.py               # **ENTRY POINT** - orchestrates everything
│   ├── scanner.py            # Market scanning module (can run standalone)
│   ├── types.py              # Type definitions (enums, protocols)
│   │
│   ├── 📁 config/            # ⚙️ CONFIGURATION
│   │   ├── __init__.py       # Config module exports
│   │   ├── settings.py       # Environment variables & API keys
│   │   └── constants.py      # Business constants (fees, thresholds)
│   │
│   ├── 📁 database/          # 💾 DATA PERSISTENCE
│   │   ├── __init__.py       # Database initialization
│   │   ├── schema.py         # SQLAlchemy models
│   │   ├── repository.py     # Data access layer (Supabase)
│   │   └── sqlite_repository.py  # SQLite implementation
│   │
│   ├── 📁 exchanges/         # 🔌 DATA ACQUISITION
│   │   ├── __init__.py       # Exchange module exports
│   │   ├── base.py           # Abstract exchange interface
│   │   ├── 📁 kalshi/
│   │   │   ├── client.py     # Kalshi API client
│   │   │   └── parser.py     # Parse Kalshi responses
│   │   └── 📁 polymarket/
│   │       ├── client.py     # Polymarket API client
│   │       └── parser.py     # Parse Polymarket responses
│   │
│   ├── 📁 models/            # 📊 DOMAIN MODELS
│   │   ├── __init__.py       # Model exports
│   │   ├── market.py         # Market data structure
│   │   ├── opportunity.py    # Arbitrage opportunity
│   │   ├── order.py          # Trade order
│   │   └── position.py       # Open position
│   │
│   ├── 📁 services/          # 🎯 BUSINESS LOGIC
│   │   ├── 📁 matching/      # Market matching & scoring
│   │   │   ├── matcher.py    # Find similar markets (NLP)
│   │   │   └── scorer.py     # Calculate opportunity profitability
│   │   ├── 📁 execution/     # Trade execution
│   │   │   ├── validator.py  # Pre-trade validation
│   │   │   └── executor.py   # Order submission & tracking
│   │   └── 📁 monitoring/    # Performance tracking
│   │       ├── tracker.py    # P&L and position tracking
│   │       └── alerter.py    # Notifications & alerts
│   │
│   ├── 📁 strategies/        # 🧮 TRADING STRATEGIES
│   │   ├── __init__.py       # Strategy exports
│   │   ├── base.py           # Abstract strategy interface
│   │   ├── config.py         # Strategy configuration
│   │   └── simple_arb.py     # Simple arbitrage strategy
│   │
│   └── 📁 utils/             # 🛠️ UTILITIES
│       ├── __init__.py       # Utility exports
│       ├── logger.py         # Logging setup
│       ├── math.py           # Math utilities (profit calc, etc.)
│       └── decorators.py     # Retry, rate limiting, etc.
│
├── 📁 tests/                 # 🧪 TEST SUITE
│   ├── conftest.py           # Pytest fixtures & config
│   ├── test_models.py        # Model tests
│   ├── test_database.py      # Database tests
│   ├── test_matching.py      # Matching logic tests
│   ├── test_execution.py     # Execution tests
│   ├── test_strategies.py    # Strategy tests
│   ├── test_monitoring.py    # Monitoring tests
│   └── test_integration.py   # End-to-end tests
│
├── 📁 docs/                  # 📚 DOCUMENTATION
│   ├── MODULE_EXPLANATIONS.md      # Detailed module docs
│   ├── DATABASE_SYSTEM.md          # Database architecture
│   ├── TESTING.md                  # Testing guide
│   ├── STRATEGY_CONFIG_REFACTOR.md # Strategy design
│   └── ...                         # Other docs
│
├── 📁 examples/              # 📖 EXAMPLES
│   └── custom_strategy_config.py  # How to create custom strategies
│
└── 📁 scripts/               # 🔧 UTILITY SCRIPTS
    └── db_query.py           # Database query tool
```

### File Purpose Quick Reference

| File | Purpose | When to Edit |
|------|---------|--------------|
| `main.py` | Bot orchestration & main loop | Changing overall bot flow |
| `scanner.py` | Market scanning (standalone) | Updating scan logic |
| `config/settings.py` | Environment config | Adding new env vars |
| `config/constants.py` | Business rules (fees, limits) | Changing trading parameters |
| `database/repository.py` | Database operations | Adding new queries |
| `exchanges/*/client.py` | Exchange API calls | API changes or new endpoints |
| `exchanges/*/parser.py` | Parse API responses | API response format changes |
| `models/*.py` | Data structures | Adding new fields |
| `services/matching/matcher.py` | Market matching logic | Improving matching algorithm |
| `services/matching/scorer.py` | Profit calculations | Changing profit formula |
| `services/execution/validator.py` | Pre-trade checks | Adding validation rules |
| `services/execution/executor.py` | Order submission | Changing execution logic |
| `strategies/simple_arb.py` | Trading strategy | Changing strategy behavior |
| `api/api_handlers.py` | API endpoints | Adding new endpoints |

---

## 🎓 Development Guide

### Setting Up Development Environment

```bash
# 1. Fork and clone
git clone https://github.com/your-username/quantshit.git
cd quantshit

# 2. Create virtual environment
python -m venv venv
.\venv\Scripts\activate

# 3. Install dependencies (including dev dependencies)
pip install -r requirements.txt
pip install pytest pytest-cov pytest-asyncio black flake8 mypy

# 4. Set up pre-commit hooks (optional but recommended)
pip install pre-commit
pre-commit install

# 5. Create .env file
cp .env.example .env
# Add your test API keys

# 6. Run tests to verify
python run_tests.py all
```

### Development Workflow

```bash
# 1. Create a feature branch
git checkout -b feature/your-feature-name

# 2. Make changes and test frequently
python run_tests.py fast  # Quick tests

# 3. Run full test suite before committing
python run_tests.py all

# 4. Format code
black src/ tests/
flake8 src/ tests/

# 5. Commit and push
git add .
git commit -m "feat: your feature description"
git push origin feature/your-feature-name

# 6. Open pull request
```

### Code Style Guidelines

- **PEP 8** compliance (use `black` for formatting)
- **Type hints** for all function signatures
- **Docstrings** for all public functions/classes
- **Descriptive variable names** (no single letters except loop counters)
- **Keep functions small** (< 50 lines)
- **DRY principle** - don't repeat yourself

### Adding New Features

#### Example: Adding a New Exchange

1. Create `src/exchanges/newexchange/` directory
2. Implement `client.py` extending `BaseExchange`
3. Implement `parser.py` with parsing logic
4. Add tests in `tests/test_exchanges.py`
5. Update `exchanges/__init__.py` to export new client
6. Update `main.py` to initialize new client

#### Example: Adding a New Strategy

1. Create `src/strategies/my_strategy.py`
2. Extend `BaseStrategy` class
3. Implement required methods:
   - `filter_opportunities()`
   - `rank_opportunities()`
   - `should_close_position()`
4. Add configuration in `strategies/config.py`
5. Add tests in `tests/test_strategies.py`
6. Use in `main.py` by instantiating your strategy

---

## 👥 Developer Lanes

### 🎨 Role-Based Development Guide

```
┌─────────────────────────────────────────────────────────────────────┐
│                      DEVELOPER ROLE MAP                              │
└─────────────────────────────────────────────────────────────────────┘

🟦 DATA ACQUISITION ENGINEER
├─ Files: exchanges/*, models/market.py
├─ Focus: API integration, data parsing, rate limiting
├─ Skills: HTTP requests, JSON parsing, API documentation
└─ Tasks: Add exchanges, fix parsers, handle API changes

🟩 STRATEGY DEVELOPER
├─ Files: strategies/*, services/matching/scorer.py
├─ Focus: Trading logic, opportunity filtering, ranking
├─ Skills: Finance, statistics, algorithmic trading
└─ Tasks: Create strategies, tune parameters, backtest

🟨 EXECUTION ENGINEER
├─ Files: services/execution/*, models/order.py
├─ Focus: Order management, validation, risk controls
├─ Skills: Trading systems, order types, error handling
└─ Tasks: Improve execution, add order types, risk limits

🟪 DATABASE & BACKEND ENGINEER
├─ Files: database/*, api/*, models/*
├─ Focus: Data persistence, API endpoints, queries
├─ Skills: SQL, ORMs, REST APIs, database design
└─ Tasks: Schema changes, optimize queries, API endpoints

🟥 MONITORING & DEVOPS
├─ Files: services/monitoring/*, config/*, utils/logger.py
├─ Focus: Observability, alerts, deployment, scaling
├─ Skills: Logging, metrics, CI/CD, cloud platforms
└─ Tasks: Add metrics, alerts, deploy, monitor

🟧 QA & TESTING ENGINEER
├─ Files: tests/*, run_tests.py
├─ Focus: Test coverage, test quality, CI
├─ Skills: Pytest, mocking, integration testing
└─ Tasks: Write tests, improve coverage, find bugs

🟫 FRONTEND DEVELOPER
├─ Files: api/*, vercel.json
├─ Focus: API design, frontend integration, dashboards
├─ Skills: REST APIs, JavaScript, React, data viz
└─ Tasks: Build UI, create dashboards, API design
```

### Lane-Specific Guides

#### 🟦 DATA ACQUISITION

**Your Mission**: Get clean, reliable market data from exchanges.

**Key Files**:
- `exchanges/base.py` - Interface all clients must implement
- `exchanges/kalshi/client.py` - Kalshi API integration
- `exchanges/polymarket/client.py` - Polymarket API integration
- `exchanges/*/parser.py` - Convert API responses to `Market` objects

**Common Tasks**:
1. **Add New Exchange**:
   - Extend `BaseExchange`
   - Implement `get_markets()`, `place_order()`, `get_positions()`
   - Create parser to normalize data
   - Add tests

2. **Fix API Breaking Changes**:
   - Check parser tests first
   - Update field mappings
   - Validate with real API calls

3. **Improve Data Quality**:
   - Add validation in parsers
   - Handle missing/invalid fields
   - Log data quality issues

**Testing**: `python run_tests.py exchanges`

---

#### 🟩 STRATEGY DEVELOPER

**Your Mission**: Define what opportunities to trade and how to rank them.

**Key Files**:
- `strategies/base.py` - Strategy interface
- `strategies/simple_arb.py` - Reference implementation
- `strategies/config.py` - Strategy configuration
- `services/matching/scorer.py` - Profit calculations

**Common Tasks**:
1. **Create New Strategy**:
   - Extend `BaseStrategy`
   - Define filtering logic (what to skip)
   - Define ranking logic (what's best)
   - Configure parameters in `config.py`

2. **Tune Existing Strategy**:
   - Adjust thresholds in config
   - Update `filter_opportunities()`
   - Change ranking criteria

3. **Improve Scoring**:
   - Modify `scorer.py` profit formulas
   - Add new confidence signals
   - Incorporate historical data

**Testing**: `python run_tests.py strategies`

**Example**: See `examples/custom_strategy_config.py`

---

#### 🟨 EXECUTION ENGINEER

**Your Mission**: Safely and reliably execute trades across exchanges.

**Key Files**:
- `services/execution/validator.py` - Pre-trade validation
- `services/execution/executor.py` - Order submission
- `models/order.py` - Order data structure

**Common Tasks**:
1. **Add Validation Rules**:
   - Add checks in `validator.py`
   - Consider capital, liquidity, fees
   - Add risk limit checks

2. **Improve Execution**:
   - Handle partial fills
   - Add order types (market, limit)
   - Implement retry logic

3. **Error Handling**:
   - Graceful degradation
   - Rollback on failure
   - Alert on critical errors

**Testing**: `python run_tests.py execution`

---

#### 🟪 DATABASE & BACKEND

**Your Mission**: Persist data and expose APIs for frontend/automation.

**Key Files**:
- `database/schema.py` - SQLAlchemy models
- `database/repository.py` - Data access layer
- `api/index.py` - API router
- `api/api_handlers.py` - Endpoint logic

**Common Tasks**:
1. **Schema Changes**:
   - Add fields to `schema.py`
   - Create migration script
   - Update repository methods

2. **Add API Endpoint**:
   - Add handler in `api_handlers.py`
   - Add route in `index.py`
   - Document in API docs

3. **Optimize Queries**:
   - Add indexes
   - Use batch operations
   - Cache frequent queries

**Testing**: `python run_tests.py database`

---

#### 🟥 MONITORING & DEVOPS

**Your Mission**: Ensure bot runs reliably and alert on issues.

**Key Files**:
- `services/monitoring/tracker.py` - P&L tracking
- `services/monitoring/alerter.py` - Alerts/notifications
- `utils/logger.py` - Logging setup
- `vercel.json` - Deployment config

**Common Tasks**:
1. **Add Metrics**:
   - Track in `tracker.py`
   - Log to file/service
   - Create dashboards

2. **Set Up Alerts**:
   - Define alert conditions in `alerter.py`
   - Configure Telegram/email
   - Test alert delivery

3. **Deploy & Scale**:
   - Configure Vercel settings
   - Set up environment variables
   - Monitor resource usage

**Testing**: `python run_tests.py monitoring`

---

#### 🟧 QA & TESTING

**Your Mission**: Ensure code quality and catch bugs before production.

**Key Files**:
- `tests/conftest.py` - Shared fixtures
- `tests/test_*.py` - Test modules
- `run_tests.py` - Test runner

**Common Tasks**:
1. **Write Tests**:
   - Unit tests for new features
   - Integration tests for workflows
   - Mock external dependencies

2. **Improve Coverage**:
   - Run `python run_tests.py all`
   - Check `htmlcov/index.html`
   - Add tests for uncovered lines

3. **Set Up CI**:
   - GitHub Actions workflow
   - Run tests on PR
   - Block merge if tests fail

**Testing**: `python run_tests.py all --cov`

---

#### 🟫 FRONTEND DEVELOPER

**Your Mission**: Build interfaces for traders and admins.

**Key Files**:
- `api/index.py` - API routes
- `api/api_handlers.py` - API logic
- `vercel.json` - Deployment config

**Available Endpoints**:
- `GET /api/markets` - List markets
- `GET /api/opportunities` - List opportunities
- `GET /api/positions` - Current positions
- `GET /api/orders` - Order history
- `GET /api/stats` - Performance stats
- `POST /api/scan-markets` - Trigger scan
- `POST /api/execute-trades` - Execute opportunities

**Common Tasks**:
1. **Build Dashboard**:
   - Fetch data from API
   - Display opportunities
   - Show P&L charts

2. **Add Controls**:
   - Trigger scans
   - Approve trades
   - Adjust parameters

3. **Improve API**:
   - Add pagination
   - Add filtering
   - Optimize responses

**Testing**: `vercel dev` (local testing)

---

## 🔧 Commands & Scripts

### Running the Bot

```bash
# Main bot (paper trading)
python -m src.main

# Scanner only (fetch markets, find opportunities)
python -m src.scanner

# API server (local)
vercel dev

# Production deploy
vercel --prod
```

### Database Operations

```bash
# Initialize database
python -c "from src.database import init_database; init_database()"

# Query database (interactive)
python scripts/db_query.py

# Reset database (WARNING: deletes all data)
python -c "from src.database import init_database; init_database(reset=True)"
```

### Development

```bash
# Format code
black src/ tests/

# Lint code
flake8 src/ tests/

# Type checking
mypy src/

# Run interactive Python with imports
python -i -c "from src import *"
```

---

## 🧪 Testing

### Running Tests

```bash
# All tests with coverage (recommended)
python run_tests.py all

# Fast (no coverage)
python run_tests.py fast

# Specific test file
python run_tests.py tests/test_matching.py

# Specific test function
python run_tests.py tests/test_matching.py::test_find_matches

# By marker
python run_tests.py unit        # Unit tests only
python run_tests.py integration # Integration tests only
python run_tests.py slow        # Long-running tests
```

### Test Coverage

After running `python run_tests.py all`, open `htmlcov/index.html` in browser to see detailed coverage report.

**Coverage Targets**:
- Overall: > 80%
- Critical paths (execution, validation): > 95%
- Utilities: > 90%

### Writing Tests

```python
# tests/test_myfeature.py
import pytest
from src.mymodule import MyClass

@pytest.fixture
def my_instance():
    """Fixture for reusable test data"""
    return MyClass(param="value")

def test_my_function(my_instance):
    """Test description"""
    result = my_instance.do_something()
    assert result == expected_value
```

**See**: `docs/TESTING.md` for comprehensive testing guide.

---

## 📡 API Documentation

### Endpoints

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/api/markets` | GET | List all markets |
| `/api/opportunities` | GET | List arbitrage opportunities |
| `/api/positions` | GET | Current open positions |
| `/api/orders` | GET | Order history |
| `/api/stats` | GET | Performance statistics |
| `/api/scan-markets` | POST | Trigger market scan |
| `/api/detect-opportunities` | POST | Find opportunities |
| `/api/execute-trades` | POST | Execute approved opportunities |
| `/api/manage-portfolio` | POST | Rebalance portfolio |

### Example Request

```bash
# Get opportunities
curl http://localhost:3000/api/opportunities

# Trigger scan
curl -X POST http://localhost:3000/api/scan-markets \
  -H "Content-Type: application/json" \
  -d '{"min_volume": 1000}'
```

### Response Format

```json
{
  "success": true,
  "data": {
    "opportunities": [...],
    "count": 5
  },
  "timestamp": "2025-11-06T12:00:00Z"
}
```

---

## ⚙️ Configuration

### Environment Variables

Create a `.env` file in the root directory:

```bash
# API Keys
KALSHI_API_KEY=your_kalshi_key
POLYMARKET_API_KEY=your_polymarket_key

# Database
DATABASE_URL=postgresql://user:pass@host:5432/dbname
# Or for SQLite (default):
# DATABASE_URL=sqlite:///quantshit.db

# Trading
PAPER_TRADING=true              # false for live trading
ENABLE_ALERTS=false             # true to enable alerts

# Alerts (if enabled)
TELEGRAM_BOT_TOKEN=your_token
TELEGRAM_CHAT_ID=your_chat_id

# Logging
LOG_LEVEL=INFO                  # DEBUG, INFO, WARNING, ERROR
LOG_FILE=quantshit.log

# Performance
MAX_CONCURRENT_REQUESTS=5
REQUEST_TIMEOUT_SECONDS=30
```

### Business Constants

Edit `src/config/constants.py`:

```python
# Fees
FEE_KALSHI = 0.007              # 0.7%
FEE_POLYMARKET = 0.02           # 2%

# Thresholds
MIN_PROFIT_THRESHOLD = 0.02     # 2% minimum profit
TITLE_SIMILARITY_THRESHOLD = 0.5
SLIPPAGE_FACTOR = 0.01          # 1%

# Capital Management
INITIAL_CAPITAL_PER_EXCHANGE = 10000
MAX_POSITION_SIZE = 1000
MIN_POSITION_SIZE = 10
```

---

## 🚀 Deployment

### Vercel (Recommended)

```bash
# Install Vercel CLI
npm install -g vercel

# Login
vercel login

# Deploy
vercel --prod
```

### Environment Variables (Vercel)

Set in Vercel dashboard or via CLI:
```bash
vercel env add KALSHI_API_KEY
vercel env add POLYMARKET_API_KEY
vercel env add DATABASE_URL
```

### Scheduled Tasks

Configured in `vercel.json`:
- Market scan runs daily at 12:00 UTC
- Customize cron schedule as needed

### Manual Deployment

```bash
# Any server with Python 3.8+
git clone <repo>
cd quantshit
pip install -r requirements.txt
python -m src.main
```

---

## 🤝 Contributing

We welcome contributions! Here's how:

1. **Fork** the repository
2. **Create** a feature branch (`git checkout -b feature/amazing-feature`)
3. **Write** tests for your changes
4. **Ensure** all tests pass (`python run_tests.py all`)
5. **Format** code (`black src/ tests/`)
6. **Commit** with clear message (`git commit -m 'feat: add amazing feature'`)
7. **Push** to your fork (`git push origin feature/amazing-feature`)
8. **Open** a Pull Request

### Commit Message Convention

```
feat: add new exchange support
fix: correct profit calculation
docs: update API documentation
test: add integration tests
refactor: simplify matching logic
perf: optimize database queries
```

### Code Review Process

- All PRs require review
- Tests must pass
- Coverage should not decrease
- Code must be formatted

---

## 📚 Additional Resources

- **Architecture**: `docs/MODULE_EXPLANATIONS.md`
- **Database**: `docs/DATABASE_SYSTEM.md`
- **Testing**: `docs/TESTING.md`
- **Strategy Design**: `docs/STRATEGY_CONFIG_REFACTOR.md`

---

## 📞 Support

- **Issues**: GitHub Issues
- **Discussions**: GitHub Discussions
- **Email**: [your-email]

---

## 📄 License

MIT License - see LICENSE file for details

---

## 🎯 Roadmap

- [ ] Add more exchanges (PredictIt, Manifold)
- [ ] Advanced strategies (mean reversion, correlation)
- [ ] Real-time websocket feeds
- [ ] Machine learning for market matching
- [ ] Mobile app
- [ ] Backtesting framework
- [ ] Paper trading competition

---

**Built with ❤️ by the Quantshit team**

*Happy arbitraging! 🚀*
