# WARP.md

This file provides guidance to WARP (warp.dev) when working with code in this repository.

## Project Overview

This is a Python-based arbitrage trading system for prediction markets (currently focused on Kalshi). It provides a modular framework for developing trading strategies, data acquisition, backtesting, and risk management.

## Development Commands

### Essential Commands

```bash
# Install dependencies
pip install -r requirements.txt

# Quick setup (creates directories, copies .env, runs tests)
python scripts/setup.py

# Run the trading system
python main.py run

# Launch web dashboard (runs on port 8501 by default)
python main.py dashboard

# Check system status
python main.py status

# Run quick start demo (see all frameworks in action)
python scripts/quick_start.py

# Test strategies
python scripts/test_strategy.py --list                    # List all strategies
python scripts/test_strategy.py --strategy "Strategy Name" # Test specific strategy
python scripts/test_strategy.py --create-example          # Create example strategy
python scripts/test_strategy.py --compare "Strat1" "Strat2" # Compare strategies

# Run backtesting
python scripts/quick_backtest.py

# Run tests
pytest tests/                     # Run all tests
pytest tests/test_strategies.py   # Test strategies
pytest tests/ --cov=src           # Run with coverage
pytest -v                         # Verbose output
```

### Development Workflows

```bash
# Paper trading mode (testing with fake money)
python scripts/paper_trade.py --strategy my_strategy --capital 1000

# Test a single strategy quickly
python -c "from src.strategies.framework import StrategyTester; import asyncio; tester = StrategyTester(); asyncio.run(tester.test_strategy(my_strategy, tester.generate_test_markets(10)))"

# Auto-discover and register strategies/data sources
python -c "from src.data.framework import auto_discover_data_sources; auto_discover_data_sources('src.data.my_source')"
```

## Architecture & Code Organization

### Core Architecture

The system follows a modular architecture with clear separation of concerns:

1. **Data Layer** (`src/data/`) - Market data acquisition and aggregation
2. **Strategy Layer** (`src/strategies/`) - Trading logic and signal generation  
3. **Execution Layer** (`src/execution/`) - Order management and trade execution
4. **Risk Layer** (`src/risk/`) - Risk management and position monitoring
5. **Platform Layer** (`src/platforms/`) - Exchange-specific integrations

### Key Components

#### Main Entry Point (`main.py`)
- `ArbitrageSystem` class orchestrates all components
- Trading loop runs every 5 seconds
- Manages data providers, strategies, order execution, and risk

#### Developer-Friendly Frameworks

The codebase provides simplified frameworks for rapid development:

1. **Data Framework** (`src/data/framework.py`)
   - `@data_source` decorator for simple data sources
   - `EasyDataProvider` base class
   - `QuickDataFetcher` for testing

2. **Strategy Framework** (`src/strategies/framework.py`)
   - `@strategy` decorator for simple strategies
   - `EasyStrategy` base class
   - `StrategyTester` for backtesting
   - Difficulty levels: BEGINNER, INTERMEDIATE, ADVANCED

3. **Execution Framework** (`src/execution/framework.py`)
   - `QuickTrader` for simple buy/sell operations
   - `SimpleExecutor` for paper trading
   - `BatchExecutor` for multiple trades

### Data Flow

```
Data Providers → DataAggregator → StrategyManager → TradingSignals
                                         ↓
                                   RiskManager
                                         ↓
                                   OrderManager → Trading Clients
                                         ↓
                                   Execution Results
```

### Key Abstractions

- **MarketData**: Standard format for market information
- **TradingSignal**: Strategy output with buy/sell recommendations
- **ArbitrageOpportunity**: Cross-market arbitrage opportunities
- **Order/ExecutionResult**: Order management structures

## Configuration

### Environment Variables (.env)
```bash
# Core database/caching
DATABASE_URL=postgresql://user:password@localhost:5432/arbitrage_db
REDIS_URL=redis://localhost:6379/0

# Kalshi API credentials
KALSHI_API_URL=https://trading-api.kalshi.com/trade-api/v2
KALSHI_EMAIL=your_email@example.com
KALSHI_PASSWORD=your_password
KALSHI_API_KEY=your_api_key

# Risk parameters
MAX_POSITION_SIZE=1000
MAX_DAILY_LOSS=5000
MAX_CORRELATION_EXPOSURE=10000
MIN_ARBITRAGE_PROFIT=0.02

# Execution settings
ORDER_TIMEOUT=30
MAX_SLIPPAGE=0.005
RETRY_ATTEMPTS=3

# Strategy parameters
CROSS_PLATFORM_MIN_SPREAD=0.03
CORRELATION_MIN_THRESHOLD=0.7
CORRELATION_MAX_THRESHOLD=0.95
```

### Trading Modes
- `TRADING_MODE=paper` - Paper trading (simulated)
- `TRADING_MODE=live` - Live trading (real money)

## Adding New Components

### Creating a New Strategy

1. **Simple Function Strategy**:
```python
# src/strategies/my_strategy.py
from src.strategies.framework import strategy, StrategyDifficulty

@strategy(name="My Strategy", difficulty=StrategyDifficulty.BEGINNER)
def my_strategy(market):
    if market.yes_price < 0.3:
        return TradingSignal(...)
    return None
```

2. **Class-based Strategy**:
```python
from src.strategies.framework import EasyStrategy

class MyStrategy(EasyStrategy):
    def should_buy(self, market):
        return market.yes_price < 0.3
```

### Creating a Data Source

```python
# src/data/my_source.py
from src.data.framework import data_source

@data_source("my_source", platforms=["demo"], refresh_interval=30)
async def get_my_data(symbols):
    # Fetch and return MarketData objects
    return markets
```

### Adding a Platform Integration

1. Create data provider in `src/platforms/`
2. Implement `BaseDataProvider` interface
3. Add trading client implementing `BaseTradingClient`
4. Register in `main.py`

## Testing Strategy

### Unit Testing
- Test individual strategies with `StrategyTester`
- Mock market data with `generate_test_markets()`
- Validate signal generation logic

### Integration Testing
- Test complete data → strategy → execution flow
- Verify risk management integration
- Check database persistence

### Backtesting
- Use `BacktestEngine` for historical testing
- Analyze performance metrics (Sharpe ratio, returns, drawdown)
- Compare multiple strategies

## Database Schema

The system uses SQLAlchemy ORM with these main tables:
- Orders - Trade execution history
- Positions - Current holdings
- Markets - Market data cache
- Signals - Strategy signal history
- Risk metrics - Risk tracking

## Monitoring & Debugging

### Logging
- Structured logging via `src/core/logger.py`
- Log levels: DEBUG, INFO, WARNING, ERROR
- Default log file: `logs/arbitrage.log`

### Web Dashboard (port 8501)
- Real-time market monitoring
- Strategy performance tracking
- Risk metrics visualization
- Order management interface

### Debug Mode
```bash
python main.py run --log-level DEBUG
```

## Performance Optimization

- Async/await for all I/O operations
- Redis caching for market data
- Batch processing for multiple markets
- Connection pooling for database

## Risk Management

Built-in risk controls:
- Position size limits
- Daily loss limits
- Correlation exposure limits
- Emergency stop functionality
- Slippage protection

## Common Development Patterns

### Strategy Development Workflow
1. Create strategy using `@strategy` decorator or `EasyStrategy` class
2. Test with `StrategyTester` using sample data
3. Run backtests with historical data
4. Paper trade to validate
5. Deploy to production with risk limits

### Data Source Integration
1. Implement data fetcher with `@data_source`
2. Test with `QuickDataFetcher`
3. Add caching if needed
4. Register in data aggregator

### Quick Iteration
- Use `scripts/quick_start.py` to see examples
- Modify example strategies in `scripts/test_strategy.py --create-example`
- Test immediately with paper trading mode