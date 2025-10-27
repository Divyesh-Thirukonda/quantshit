# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

This is a prediction market arbitrage bot that identifies and executes arbitrage opportunities across multiple prediction market platforms (Polymarket, Manifold, Kalshi). The bot can run as a standalone CLI application or as a FastAPI web service deployed on Vercel.

## Development Commands

### Setup
```bash
pip install -r requirements.txt
cp .env.example .env  # Then add API keys
```

### Testing
```bash
# Run full bot test (data collection, strategy, execution)
python test_bot.py

# Run bot once (single cycle, no scheduling)
python main.py --once
```

### Running Locally
```bash
# Run bot with hourly scheduling
python main.py

# Run as API server
python api.py
```

### Deployment
```bash
# Deploy to Vercel
vercel

# Required environment variables in Vercel dashboard:
# - POLYMARKET_API_KEY
# - MANIFOLD_API_KEY
# - KALSHI_API_KEY
# - MIN_VOLUME (default: 1000)
# - MIN_SPREAD (default: 0.05)
```

## Architecture

### Core Components

**ArbitrageBot** (`main.py:12-120`)
- Main orchestrator that coordinates all operations
- Loads configuration from environment variables
- Runs the three-phase cycle: data collection → strategy execution → trade execution
- Can run in single-shot mode (`--once`) or continuous scheduling (hourly)

**Market API Layer** (`platforms/`)
- All platform APIs inherit from `BaseMarketAPI` (`platforms/base.py:4-21`)
- Each platform implements: `get_recent_markets()`, `place_buy_order()`, `place_sell_order()`
- Platform registry in `platforms/__init__.py:15-19` using `MARKET_APIS` dict
- Factory function `get_market_api()` creates platform instances

**Strategy Layer** (`strategies.py`)
- All strategies inherit from `BaseStrategy` (`strategies.py:5-13`)
- `ArbitrageStrategy` (strategies.py:16-144) finds price discrepancies across platforms
- Market matching uses Jaccard similarity on cleaned titles (`_are_markets_similar()` at line 62)
- Strategy registry in `STRATEGIES` dict (`strategies.py:148-150`)

**Execution Layer** (`executor.py`)
- `TradeExecutor` (`executor.py:6-132`) handles order placement across platforms
- Executes both sides of arbitrage: buy on cheaper market, sell on expensive market
- Includes rate limiting (1-2 second delays between orders)
- Limits to 3 trades per cycle by default (`max_trades` parameter)

**API Interface** (`api.py`)
- FastAPI application for external access (e.g., dashboard integration)
- Endpoints:
  - `GET /` - Health check
  - `POST /run-strategy` - Manual trigger for strategy cycle
  - `GET /markets` - Get current market data from all platforms
- Configured for Vercel serverless deployment via `vercel.json`

### Data Flow

1. **Collection**: `ArbitrageBot.collect_market_data()` queries all configured platforms
2. **Matching**: Strategy compares markets across platforms using text similarity
3. **Detection**: Calculate spreads between matched markets (YES and NO prices)
4. **Filtering**: Only opportunities with spread ≥ MIN_SPREAD are considered
5. **Execution**: Top opportunities (sorted by profit) are executed up to max_trades limit

### Key Design Patterns

**Registry Pattern**: Both `MARKET_APIS` and `STRATEGIES` use registries for extensibility. To add a new platform or strategy, create the class and add it to the respective registry dict.

**Factory Pattern**: `get_market_api()` and `get_strategy()` create instances from registries based on string identifiers.

**Template Method**: Base classes define the interface; subclasses implement platform/strategy-specific logic.

## Adding New Platforms

1. Create file `platforms/newplatform.py` with class inheriting from `BaseMarketAPI`
2. Implement required methods:
   - `get_recent_markets()`: Return list of dicts with keys: `id`, `title`, `platform`, `volume`, `yes_price`, `no_price`
   - `place_buy_order()` and `place_sell_order()`: Return dict with `success` and `order_id`
3. Add import to `platforms/__init__.py`
4. Register in `MARKET_APIS` dict: `'newplatform': NewPlatformAPI`
5. Add API key environment variable: `NEWPLATFORM_API_KEY`

## Adding New Strategies

1. Create class in `strategies.py` inheriting from `BaseStrategy`
2. Implement `find_opportunities(markets_by_platform)` method
   - Input: Dict mapping platform names to lists of market dicts
   - Output: List of opportunity dicts with keys: `type`, `outcome`, `buy_market`, `sell_market`, `buy_price`, `sell_price`, `spread`, `expected_profit`, `trade_amount`
3. Register in `STRATEGIES` dict: `'strategy_name': StrategyClass`
4. Use via `get_strategy('strategy_name')` in main.py

## Important Notes

- **Demo Mode**: Trade execution methods (`place_buy_order`, `place_sell_order`) currently return demo responses. Real trading logic needs to be implemented for production use.
- **API Keys**: Bot runs in demo mode if no API keys are configured (main.py:30-34).
- **Market Matching**: Similarity threshold is 0.6 Jaccard coefficient on cleaned titles (strategies.py:62). Adjust if getting too many/few matches.
- **Environment Variables**: All configuration via `.env` file: API keys, `MIN_VOLUME`, `MIN_SPREAD`.
- **Vercel Deployment**: Configured as serverless function via `vercel.json`. API runs on-demand, not continuously scheduled.
