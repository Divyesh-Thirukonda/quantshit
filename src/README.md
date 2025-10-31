# Quantshit Arbitrage Engine - Clean Architecture

This is a refactored version of the arbitrage bot following clean architecture principles as defined in `docs/MODULE_EXPLANATIONS.md` and `docs/VISUAL_FLOW.md`.

## Architecture Overview

```
src-2/
├── types.py                    # Universal types & enums (Exchange, OrderSide, etc.)
├── models/                     # Domain models (Market, Order, Position, Opportunity)
├── config/                     # Configuration (settings, constants)
├── utils/                      # Shared utilities (logger, math, decorators)
├── services/                   # Business logic
│   ├── matching/              # Market matching & scoring
│   ├── execution/             # Trade validation & execution
│   └── monitoring/            # Position tracking & alerts
├── strategies/                # Trading strategies (base, simple_arb)
├── database/                  # Data persistence layer
└── main.py                    # Application entry point & orchestrator
```

## Design Principles

1. **Single Responsibility**: Each module has one job
2. **Dependency Inversion**: Services depend on abstractions (Repository), not implementations
3. **Open/Closed**: Add new strategies/exchanges by extending, not modifying
4. **DRY**: Constants, types, and utilities defined once, used everywhere
5. **Separation of Concerns**: Data (models) separate from logic (services) separate from persistence (database)

## What's Complete

✅ **Core Architecture**
- Universal types system (`types.py`)
- Domain models (Market, Order, Position, Opportunity)
- Configuration management (settings from env, constants)
- Utility functions (logger, math, decorators)

✅ **Services Layer**
- Market matching with fuzzy string matching
- Opportunity scoring with fee/slippage calculation
- Trade validation with safety checks
- Trade executor (paper trading mode)
- Position tracker with P&L monitoring
- Alert system (Telegram placeholder)

✅ **Strategy System**
- Base strategy interface
- Simple arbitrage strategy implementation
- Position sizing and exit logic

✅ **Database Layer**
- Repository pattern for data access
- In-memory implementation (ready for SQL migration)
- Schema definitions for future database

✅ **Main Orchestrator**
- Complete trading cycle flow
- Error handling and logging
- Continuous and single-run modes

## What Needs to Be Done

❌ **Exchange Integration**
The biggest missing piece is adapting the exchange clients from `src/platforms/`. We need to:

1. Create `src-2/exchanges/` directory
2. Adapt `src/platforms/kalshi.py` and `src/platforms/polymarket.py`
3. Create parsers to convert exchange-specific data to our `Market` model
4. Wire them into `main.py`

**Structure should be:**
```
src-2/exchanges/
├── __init__.py
├── kalshi/
│   ├── __init__.py
│   ├── client.py      # API calls (adapted from src/platforms/kalshi.py)
│   └── parser.py      # Convert to models/market.py format
└── polymarket/
    ├── __init__.py
    ├── client.py      # API calls (adapted from src/platforms/polymarket.py)
    └── parser.py      # Convert to models/market.py format
```

❌ **Real Trading Implementation**
- executor.py has placeholder for real API calls
- Need to implement actual order placement
- Need to handle order confirmations and fills

❌ **Position Management**
- Creating positions from executed orders
- Closing positions
- Updating positions with current prices

❌ **Testing**
- Unit tests for each service
- Integration tests for full cycle
- Mock exchange clients for testing

## How to Run (Once Exchange Integration is Complete)

```bash
# Install dependencies
pip install -r requirements.txt

# Configure environment
cp .env.example .env
# Edit .env with API keys

# Run single cycle
python -m src-2.main

# Run continuously (modify main.py to call bot.run_continuous())
python -m src-2.main
```

## Key Differences from Old Architecture

### Old (`src/`)
- Mixed concerns (platform API + strategy + execution + tracking)
- Types scattered across modules
- Tight coupling between components
- Hard to test in isolation
- Hard to add new platforms/strategies

### New (`src-2/`)
- Clear separation of concerns
- Single source of truth for types
- Loose coupling via interfaces (BaseStrategy, Repository)
- Each component testable independently
- Easy to extend (new strategy = extend BaseStrategy, new exchange = implement client + parser)

## Migration Path

1. ✅ Build clean architecture in `src-2/` (DONE)
2. ⏭️ Adapt exchange clients from `src/platforms/`
3. ⏭️ Test with paper trading
4. ⏭️ Add unit tests
5. ⏭️ Test with live markets (small positions)
6. ⏭️ Replace `src/` with `src-2/`

## References

- See `docs/MODULE_EXPLANATIONS.md` for detailed module documentation
- See `docs/VISUAL_FLOW.md` for data flow diagrams
- See `CLAUDE.md` for original architecture notes
