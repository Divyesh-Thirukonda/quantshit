# Developer Quick Start Guide

Welcome to the Quantshit trading system! This guide will get you up and running quickly, whether you're building data sources, strategies, or execution logic.

## 🚀 Quick Setup (5 minutes)

```bash
# 1. Clone and enter the project
git clone <repository>
cd quantshit

# 2. Install dependencies
pip install -r requirements.txt

# 3. Copy environment file
cp .env.example .env
# Edit .env with your API keys (optional for development)

# 4. Test the system
python scripts/quick_start.py
```

## 🎯 What You Can Build

### 1. **Data Sources** (Easiest)
- Add new market data providers
- Create custom data feeds
- Build real-time price streams

### 2. **Trading Strategies** (Medium)
- Simple buy/sell logic
- Arbitrage detection
- Complex multi-market analysis

### 3. **Execution Logic** (Advanced)
- Order management
- Risk controls
- Portfolio optimization

## 📊 Your First Data Source (5 minutes)

```python
# Create: src/data/my_source.py
from src.data.framework import data_source, EasyDataProvider, MarketData

# Option 1: Simple function (easiest)
@data_source("my_prices", platforms=["demo"], refresh_interval=30)
async def get_demo_prices(symbols: List[str]) -> List[MarketData]:
    markets = []
    for symbol in symbols:
        markets.append(MarketData(
            platform="demo",
            market_id=symbol,
            title=f"Demo Market {symbol}",
            yes_price=0.5,  # Your price logic here
            no_price=0.5,
            volume=1000.0
        ))
    return markets

# Option 2: Full provider class (more features)
class MyProvider(EasyDataProvider):
    def __init__(self):
        super().__init__("my_provider", {"api_key": "your_key"})
    
    async def connect(self) -> bool:
        # Your connection logic
        self.is_connected = True
        return True
    
    async def get_markets(self, symbols=None) -> List[MarketData]:
        # Your market data logic
        return []

# Test your data source
from src.data.framework import QuickDataFetcher
fetcher = QuickDataFetcher()
markets = await fetcher.get_markets("demo", ["TEST1", "TEST2"])
```

## 🧠 Your First Strategy (10 minutes)

```python
# Create: src/strategies/my_strategy.py
from src.strategies.framework import strategy, EasyStrategy, StrategyDifficulty
from src.strategies.base import TradingSignal, SignalType

# Option 1: Simple function (easiest)
@strategy(
    name="Buy Low Sell High",
    description="Buy when price < 0.3, sell when price > 0.7",
    difficulty=StrategyDifficulty.BEGINNER,
    tags=["reversal", "simple"]
)
def buy_low_sell_high(market: MarketData) -> Optional[TradingSignal]:
    if market.yes_price < 0.3:
        return TradingSignal(
            strategy_name="buy_low_sell_high",
            market_id=market.market_id,
            platform=market.platform,
            signal_type=SignalType.BUY,
            outcome="yes",
            confidence=0.8,
            suggested_size=100.0
        )
    elif market.yes_price > 0.7:
        return TradingSignal(
            strategy_name="buy_low_sell_high",
            market_id=market.market_id,
            platform=market.platform,
            signal_type=SignalType.SELL,
            outcome="yes",
            confidence=0.8,
            suggested_size=100.0
        )
    return None

# Option 2: Class-based (more control)
class VolumeStrategy(EasyStrategy):
    def __init__(self):
        super().__init__(
            name="Volume Breakout",
            description="Trade on volume spikes",
            difficulty=StrategyDifficulty.BEGINNER
        )
        self.volume_threshold = 500
    
    def should_buy(self, market: MarketData) -> bool:
        return market.volume > self.volume_threshold and market.yes_price < 0.5
    
    def should_sell(self, market: MarketData) -> bool:
        return market.volume > self.volume_threshold and market.yes_price > 0.8

# Test your strategy
from src.strategies.framework import StrategyTester
tester = StrategyTester()
test_markets = tester.generate_test_markets(count=10)
results = await tester.test_strategy(buy_low_sell_high, test_markets)
print(f"Generated {len(results.signals)} signals")
```

## 💰 Your First Execution (5 minutes)

```python
# Simple trading
from src.execution.framework import QuickTrader

trader = QuickTrader(initial_cash=1000.0)

# Buy a market
result = await trader.buy("MARKET_001", quantity=100, max_price=0.6)
print(f"Buy result: {result.success} - {result.message}")

# Sell a market  
result = await trader.sell("MARKET_001", quantity=50, min_price=0.7)
print(f"Sell result: {result.success} - {result.message}")

# Check your portfolio
print(f"Cash: ${trader.cash:.2f}")
print(f"Positions: {trader.positions}")
print(f"Stats: {trader.get_stats()}")
```

## 🧪 Testing Your Code

```python
# Test data sources
python -c "
from src.data.framework import auto_discover_data_sources
auto_discover_data_sources('src.data.my_source')
"

# Test strategies  
python scripts/test_strategy.py --strategy my_strategy

# Run backtests
python scripts/quick_backtest.py --strategy my_strategy

# Paper trading
python scripts/paper_trade.py --strategy my_strategy --capital 1000
```

## 📁 Project Structure for Developers

```
src/
├── data/
│   ├── framework.py      # 🆕 Easy data source creation
│   ├── providers.py      # Base classes
│   └── my_source.py      # 👈 Your data sources here
├── strategies/
│   ├── framework.py      # 🆕 Easy strategy creation  
│   ├── base.py          # Base classes
│   └── my_strategy.py    # 👈 Your strategies here
├── execution/
│   ├── framework.py      # 🆕 Easy execution
│   ├── engine.py        # Advanced execution
│   └── my_executor.py    # 👈 Your execution logic here
└── platforms/
    └── kalshi.py        # Platform integrations
```

## 🎓 Difficulty Levels

### **Beginner** (Start here!)
- Simple buy/sell strategies
- Basic data sources
- Paper trading

**Example Projects:**
- Price reversal strategy
- Volume spike detector
- Demo data provider

### **Intermediate** 
- Multi-market strategies
- Real-time data feeds
- Risk management

**Example Projects:**
- Correlation arbitrage
- Sentiment analysis strategy
- Order book data source

### **Advanced**
- Complex arbitrage
- Machine learning strategies
- Live execution systems

**Example Projects:**
- Cross-platform arbitrage
- ML prediction models
- Production trading systems

## 🔍 Common Patterns

### Data Source Pattern
```python
@data_source("my_source", refresh_interval=60)
async def my_data_source(params) -> List[MarketData]:
    # 1. Fetch from API/database
    # 2. Transform to MarketData
    # 3. Return list
    pass
```

### Strategy Pattern
```python
@strategy(name="My Strategy", difficulty=BEGINNER)
def my_strategy(market: MarketData) -> Optional[TradingSignal]:
    # 1. Analyze market data
    # 2. Apply your logic
    # 3. Return signal or None
    pass
```

### Execution Pattern
```python
trader = QuickTrader(initial_cash=1000)
# 1. trader.buy() / trader.sell()
# 2. Check trader.positions
# 3. Get trader.get_stats()
```

## 🚨 Development Rules

### **DO:**
- ✅ Start with the framework classes (`EasyStrategy`, `QuickTrader`, etc.)
- ✅ Use decorators for simple functions (`@strategy`, `@data_source`)
- ✅ Test with paper trading first
- ✅ Add logging for debugging
- ✅ Handle errors gracefully

### **DON'T:**
- ❌ Start with complex base classes
- ❌ Skip testing with sample data
- ❌ Jump straight to live trading
- ❌ Ignore risk management
- ❌ Hardcode API keys

## 📚 API Reference

### Quick Classes
```python
# Data
QuickDataFetcher()              # Fetch any market data
EasyDataProvider()              # Create custom providers

# Strategies  
EasyStrategy()                  # Simple strategy base class
StrategyTester()               # Test strategies

# Execution
QuickTrader()                  # Simple buy/sell interface
SimpleExecutor()               # Paper trading
BatchExecutor()                # Multiple trades at once
```

### Decorators
```python
@data_source(name, platforms, refresh_interval)
@strategy(name, description, difficulty, tags)
@execution_rule(max_position_size, max_daily_trades)
@risk_check(max_loss_per_trade, max_portfolio_risk)
```

## 🆘 Getting Help

### Debug Your Code
```python
# Enable debug logging
import logging
logging.basicConfig(level=logging.DEBUG)

# Test with sample data
from src.strategies.framework import StrategyTester
tester = StrategyTester()
test_markets = tester.generate_test_markets(10)
# Test your strategy with test_markets
```

### Common Issues

**"Strategy not generating signals"**
- Check your logic with print statements
- Test with extreme market data (price=0.1, price=0.9)
- Verify return types match TradingSignal

**"Data source not working"**
- Test connection first
- Check API keys in .env
- Use caching for development

**"Execution failing"**
- Start with paper trading mode
- Check position sizes vs available cash
- Verify market IDs exist

## 🚀 Next Steps

1. **Build Your First Strategy** (30 minutes)
   - Copy an example strategy
   - Modify the logic
   - Test with sample data

2. **Add a Data Source** (45 minutes)
   - Find a free API (Alpha Vantage, Yahoo Finance, etc.)
   - Create a simple provider
   - Test data fetching

3. **Run End-to-End** (60 minutes)
   - Connect your data source
   - Run your strategy
   - Execute with paper trading

4. **Deploy & Monitor** (Advanced)
   - Set up production environment
   - Add monitoring and alerts
   - Implement live trading

## 🎯 Ready-to-Use Examples

Check out these working examples in the codebase:
- `src/strategies/framework.py` - Example strategies
- `src/data/framework.py` - Example data sources  
- `src/execution/framework.py` - Example execution
- `scripts/examples/` - Full working examples

Happy coding! 🚀