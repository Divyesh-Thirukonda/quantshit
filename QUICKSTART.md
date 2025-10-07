# Quick Start Guide

## Installation

```bash
git clone <repository-url>
cd quantshit
pip install -r requirements.txt
pip install -e .
```

## Running the Demo

```bash
python examples/backtest_demo.py
```

## Running Tests

```bash
pytest tests/ -v
```

## Basic Usage

### 1. Import the library

```python
from quantshit import Backtester, Market
from quantshit.strategies.examples import MeanReversionStrategy
from datetime import datetime
```

### 2. Create market data

```python
markets = [
    Market(
        id="market_1",
        question="Will candidate A win?",
        current_yes_price=0.45,
        current_no_price=0.55,
        timestamp=datetime.now()
    ),
    # Add more market states...
]
```

### 3. Initialize backtester

```python
backtester = Backtester(
    initial_capital=10000,  # Starting capital
    commission_rate=0.01,   # 1% commission
    slippage=0.005          # 0.5% slippage
)
```

### 4. Set up strategy

```python
strategy = MeanReversionStrategy()
strategy.set_params(
    threshold=0.5,      # Mean price
    deviation=0.15,     # Trigger threshold
    position_size=0.2   # Use 20% of capital per trade
)
```

### 5. Run backtest

```python
performance = backtester.run(markets, strategy)
results = backtester.get_results()
```

### 6. View results

```python
print(f"Total P&L: ${results['total_pnl']:.2f}")
print(f"Returns: {results['returns']*100:.2f}%")
print(f"Sharpe Ratio: {results['sharpe_ratio']:.2f}")
print(f"Max Drawdown: {results['max_drawdown']*100:.2f}%")
```

## Creating Custom Strategies

```python
from quantshit.strategies.base import Strategy
from quantshit.backtesting.models import Order, OrderType

class MyStrategy(Strategy):
    def __init__(self):
        super().__init__(name="MyStrategy")
        
    def generate_signals(self, markets, portfolio, timestamp):
        orders = []
        
        for market_id, market in markets.items():
            if market.resolved:
                continue
                
            # Your trading logic here
            if some_condition:
                orders.append(Order(
                    market_id=market_id,
                    order_type=OrderType.BUY,
                    outcome=True,  # True for YES, False for NO
                    shares=100,
                    price=market.current_yes_price,
                    timestamp=timestamp
                ))
        
        return orders
```

## Key Concepts

### Markets
- Each market has YES and NO prices
- Prices should sum to 1.0
- Markets can be resolved to TRUE (YES wins) or FALSE (NO wins)

### Orders
- **BUY**: Purchase shares at limit price
- **SELL**: Sell shares at limit price
- Orders fill when limit price is favorable vs market price

### Positions
- Track shares and average price
- Calculate unrealized P&L
- Automatically settled when market resolves

### Performance Metrics
- **Total P&L**: Absolute profit/loss
- **Returns**: Percentage gain/loss
- **Sharpe Ratio**: Risk-adjusted returns
- **Max Drawdown**: Largest peak-to-trough decline
- **Win Rate**: Percentage of profitable trades

## Example Strategies

### Mean Reversion
Buy when price deviates significantly from threshold (default 0.5), sell when it reverts.

### Momentum
Follow price trends - buy when price is rising, sell when falling.

## Project Structure

```
quantshit/
├── quantshit/          # Main package
│   ├── backtesting/    # Core backtesting engine
│   ├── strategies/     # Trading strategies
│   └── data/           # Data utilities
├── examples/           # Example usage
├── tests/              # Test suite
└── README.md           # Documentation
```

## Support

For issues, please check the README.md or create an issue in the repository.
