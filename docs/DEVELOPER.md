# Developer Guide

## Getting Started

This guide will help you get started with developing new strategies and extending the arbitrage system.

## Architecture Overview

The system is built with a modular architecture:

```
src/
├── core/          # Core system components (config, logging, database)
├── data/          # Data acquisition and market data providers
├── platforms/     # Platform-specific implementations (Kalshi, etc.)
├── strategies/    # Trading strategies
├── execution/     # Order execution and management
├── risk/          # Risk management
├── backtesting/   # Backtesting framework
├── modules/       # Utility modules (stats, NLP)
└── frontend/      # Web dashboard
```

## Adding New Strategies

### 1. Create Strategy Class

Create a new file in `src/strategies/` that inherits from `BaseStrategy`:

```python
from src.strategies.base import BaseStrategy, TradingSignal, ArbitrageOpportunity
from typing import List, Dict, Any, Optional

class MyCustomStrategy(BaseStrategy):
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        super().__init__("my_custom_strategy", config)
        # Initialize strategy-specific parameters
        
    async def analyze_markets(
        self,
        markets: Dict[str, List[MarketData]],
        order_books: Optional[Dict[str, OrderBook]] = None
    ) -> List[TradingSignal]:
        """Implement your market analysis logic here."""
        signals = []
        
        # Your analysis code here
        # Generate signals based on market conditions
        
        return signals
    
    async def find_opportunities(
        self,
        markets: Dict[str, List[MarketData]],
        order_books: Optional[Dict[str, OrderBook]] = None
    ) -> List[ArbitrageOpportunity]:
        """Implement your opportunity detection logic here."""
        opportunities = []
        
        # Your opportunity detection code here
        
        return opportunities
```

### 2. Register Strategy

Add your strategy to the main system in `main.py`:

```python
from src.strategies.my_custom import MyCustomStrategy

# In ArbitrageSystem._setup_strategies():
custom_strategy = MyCustomStrategy(custom_config)
self.strategy_manager.add_strategy(custom_strategy)
```

### 3. Configuration

Add strategy configuration to `config/strategies.conf`:

```ini
[my_custom_strategy]
parameter1 = value1
parameter2 = value2
```

## Adding New Platforms

### 1. Data Provider

Create a data provider that inherits from `BaseDataProvider`:

```python
from src.data.providers import BaseDataProvider, MarketData, OrderBook

class MyPlatformDataProvider(BaseDataProvider):
    def __init__(self):
        super().__init__("my_platform")
        
    async def connect(self) -> bool:
        # Implement connection logic
        pass
        
    async def get_markets(self, category: Optional[str] = None) -> List[MarketData]:
        # Implement market data fetching
        pass
        
    # Implement other required methods...
```

### 2. Trading Client

Create a trading client that inherits from `BaseTradingClient`:

```python
from src.execution.engine import BaseTradingClient, Order, ExecutionResult

class MyPlatformTradingClient(BaseTradingClient):
    def __init__(self):
        super().__init__("my_platform")
        
    async def place_order(self, order: Order) -> ExecutionResult:
        # Implement order placement logic
        pass
        
    # Implement other required methods...
```

### 3. Integration

Register your platform in the main system:

```python
# Add data provider
my_platform_provider = MyPlatformDataProvider()
self.data_aggregator.add_provider(my_platform_provider)

# Add trading client
my_platform_client = MyPlatformTradingClient()
self.order_manager.add_trading_client(my_platform_client)
```

## Backtesting Custom Strategies

### 1. Prepare Historical Data

Create a DataFrame with the required columns:

```python
import pandas as pd

historical_data = {
    'platform_name': pd.DataFrame({
        'timestamp': timestamps,
        'market_id': market_ids,
        'title': titles,
        'yes_price': yes_prices,
        'no_price': no_prices,
        'volume': volumes
    })
}
```

### 2. Run Backtest

```python
from src.backtesting.engine import BacktestEngine
from datetime import datetime

engine = BacktestEngine(initial_capital=100000.0)

results = await engine.run_backtest(
    strategy=my_strategy,
    historical_data=historical_data,
    start_date=datetime(2024, 1, 1),
    end_date=datetime(2024, 12, 31)
)

print(f"Total Return: {results.total_return:.2%}")
print(f"Sharpe Ratio: {results.sharpe_ratio:.2f}")
```

## Adding Analysis Modules

### 1. Statistical Analysis

Extend the `StatisticalAnalyzer` class in `src/modules/statistics.py`:

```python
def my_custom_analysis(self, data: pd.DataFrame) -> Dict[str, Any]:
    """Add your custom statistical analysis."""
    # Your analysis code here
    return results
```

### 2. NLP Analysis

Extend the `TextProcessor` class in `src/modules/nlp.py`:

```python
def my_custom_nlp(self, text: str) -> Dict[str, Any]:
    """Add your custom NLP analysis."""
    # Your NLP code here
    return results
```

## Risk Management

### Custom Risk Checks

Add custom risk checks to the `RiskManager`:

```python
def check_custom_risk(self, signal: TradingSignal) -> tuple[bool, Optional[str]]:
    """Add your custom risk checks."""
    # Your risk logic here
    if risk_condition:
        return False, "Custom risk check failed"
    return True, None
```

## Testing

### Unit Tests

Create tests for your strategies:

```python
import pytest
from src.strategies.my_custom import MyCustomStrategy

@pytest.mark.asyncio
async def test_my_strategy():
    strategy = MyCustomStrategy()
    
    # Test with sample data
    sample_markets = create_sample_markets()
    signals = await strategy.analyze_markets(sample_markets)
    
    assert len(signals) >= 0
    # Add more assertions
```

### Integration Tests

Test your strategy with the full system:

```python
@pytest.mark.asyncio
async def test_strategy_integration():
    # Test strategy with actual system components
    pass
```

## Performance Optimization

### 1. Async Operations

Use async/await for I/O operations:

```python
async def fetch_data(self):
    async with aiohttp.ClientSession() as session:
        async with session.get(url) as response:
            return await response.json()
```

### 2. Caching

Implement caching for expensive operations:

```python
from functools import lru_cache

@lru_cache(maxsize=128)
def expensive_calculation(self, param):
    # Expensive operation
    return result
```

### 3. Batch Operations

Process data in batches when possible:

```python
def process_markets_batch(self, markets: List[MarketData]):
    # Process multiple markets at once
    pass
```

## Monitoring and Logging

### Custom Metrics

Add custom metrics to track your strategy:

```python
from src.core.logger import get_logger

logger = get_logger(__name__)

def track_custom_metric(self, value):
    logger.info(f"Custom metric: {value}", extra={
        "strategy": self.name,
        "metric": "custom_value",
        "value": value
    })
```

### Dashboard Integration

Add custom widgets to the dashboard:

```python
# In src/frontend/dashboard.py
def render_custom_widget(self):
    st.subheader("My Custom Widget")
    # Your Streamlit code here
```

## Deployment

### Environment Setup

1. Set up production environment variables
2. Configure logging for production
3. Set up monitoring and alerting

### Database Migration

For schema changes:

```python
from src.core.database import Base, create_database_engine
from alembic import command
from alembic.config import Config

# Run migrations
alembic_cfg = Config("alembic.ini")
command.upgrade(alembic_cfg, "head")
```

## Best Practices

### 1. Error Handling

Always handle exceptions gracefully:

```python
try:
    result = await risky_operation()
except Exception as e:
    logger.error(f"Operation failed: {e}")
    return default_value
```

### 2. Configuration

Use configuration files for parameters:

```python
def __init__(self, config: Dict[str, Any]):
    self.param1 = config.get("param1", default_value)
    self.param2 = config.get("param2", default_value)
```

### 3. Documentation

Document your strategies and modules:

```python
def analyze_markets(self, markets):
    """
    Analyze markets for trading signals.
    
    Args:
        markets: Dictionary of platform -> market list
        
    Returns:
        List of trading signals
        
    Raises:
        ValueError: If markets data is invalid
    """
```

### 4. Testing

Write comprehensive tests:

- Unit tests for individual functions
- Integration tests for system components
- Backtests for strategy validation

## Getting Help

- Check the logs in `logs/arbitrage.log`
- Review the API documentation in `docs/API.md`
- Run tests with `python -m pytest tests/`
- Use the dashboard for real-time monitoring