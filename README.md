# quantshit

A trading bot for prediction markets with a comprehensive backtesting engine.

## Features

- **Event-driven backtesting engine** - Simulate trading strategies on historical prediction market data
- **Portfolio management** - Track positions, cash, P&L, and performance metrics
- **Flexible strategy framework** - Easy-to-implement custom trading strategies
- **Built-in example strategies** - Mean reversion and momentum strategies included
- **Performance analytics** - Sharpe ratio, maximum drawdown, win rate, and more

## Installation

```bash
pip install -r requirements.txt
pip install -e .
```

## Quick Start

```python
from quantshit import Backtester, Market
from quantshit.strategies.examples import MeanReversionStrategy
from datetime import datetime

# Create some sample market data
markets = [
    Market(
        id="market_1",
        question="Will candidate A win?",
        current_yes_price=0.6,
        current_no_price=0.4,
        timestamp=datetime.now()
    ),
    # ... more market data
]

# Initialize backtester
backtester = Backtester(
    initial_capital=10000,
    commission_rate=0.01
)

# Create and configure strategy
strategy = MeanReversionStrategy()
strategy.set_params(
    threshold=0.5,
    deviation=0.15,
    position_size=0.2
)

# Run backtest
performance = backtester.run(markets, strategy)
results = backtester.get_results()

print(f"Total P&L: ${results['total_pnl']:.2f}")
print(f"Returns: {results['returns']*100:.2f}%")
print(f"Sharpe Ratio: {results['sharpe_ratio']:.2f}")
```

## Architecture

### Core Components

- **Backtester** (`backtesting/engine.py`) - Main backtesting engine with event-driven architecture
- **Portfolio** (`backtesting/portfolio.py`) - Portfolio management, position tracking, and P&L calculation
- **Models** (`backtesting/models.py`) - Data models for markets, positions, orders, and trades
- **Strategy** (`strategies/base.py`) - Base class for implementing custom trading strategies

### Data Models

- **Market** - Represents a prediction market with YES/NO prices and resolution state
- **Position** - Tracks shares held in a specific market outcome
- **Order** - Represents a buy/sell order with limit price
- **Trade** - Completed trade with execution details

## Creating Custom Strategies

Extend the `Strategy` base class and implement the `generate_signals` method:

```python
from quantshit.strategies.base import Strategy
from quantshit.backtesting.models import Order, OrderType

class MyStrategy(Strategy):
    def __init__(self):
        super().__init__(name="MyStrategy")
        self.set_params(
            some_param=0.5
        )
    
    def generate_signals(self, markets, portfolio, timestamp):
        orders = []
        
        for market_id, market in markets.items():
            # Your trading logic here
            if market.current_yes_price < self.params['some_param']:
                orders.append(Order(
                    market_id=market_id,
                    order_type=OrderType.BUY,
                    outcome=True,
                    shares=100,
                    price=market.current_yes_price,
                    timestamp=timestamp
                ))
        
        return orders
```

## Running Examples

```bash
cd examples
python backtest_demo.py
```

This will run backtests using both the Mean Reversion and Momentum strategies on simulated market data.

## Project Structure

```
quantshit/
├── quantshit/
│   ├── backtesting/
│   │   ├── engine.py      # Main backtesting engine
│   │   ├── portfolio.py   # Portfolio management
│   │   └── models.py      # Data models
│   ├── strategies/
│   │   ├── base.py        # Base strategy class
│   │   └── examples.py    # Example strategies
│   └── data/              # Data utilities (future)
├── examples/
│   └── backtest_demo.py   # Example usage
├── requirements.txt
├── setup.py
└── README.md
```

## Performance Metrics

The backtesting engine calculates:

- **Total P&L** - Profit and loss in absolute terms
- **Returns** - Percentage returns on initial capital
- **Sharpe Ratio** - Risk-adjusted returns
- **Maximum Drawdown** - Largest peak-to-trough decline
- **Win Rate** - Percentage of profitable trades
- **Number of Trades** - Total trades executed

## License

MIT