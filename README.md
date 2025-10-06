# QuantShit - Quantitative Trading Library

A comprehensive Python library for quantitative trading strategies, including options market-making, volatility capture, and momentum trading.

## Features

### Options Market-Making / Volatility Capture
- **Black-Scholes Pricing Model**: Complete implementation with pricing for European calls and puts
- **Greeks Calculation**: Delta, Gamma, Theta, Vega, and Rho
- **Volatility Analysis**:
  - Historical volatility calculation
  - Implied volatility solver
  - Volatility surface and smile construction
  - Rolling volatility metrics
- **Risk Management**:
  - Portfolio Greeks aggregation
  - Delta and Gamma hedging
  - VaR and CVaR calculations
  - Kelly Criterion position sizing
  - Sharpe ratio calculation
- **Market Data Tools**:
  - Order book management
  - Simulated market data feeds
  - Option chain data structures
  - Mispriced option detection

### Momentum Trading
- **Technical Indicators**:
  - Moving Averages (SMA, EMA)
  - Relative Strength Index (RSI)
  - MACD (Moving Average Convergence Divergence)
  - Bollinger Bands
  - Stochastic Oscillator
  - Average True Range (ATR)
  - Average Directional Index (ADX)
  - On-Balance Volume (OBV)
  - Momentum and Rate of Change (ROC)
- **Trend Detection**:
  - Linear regression trend analysis
  - Moving average crossover signals
  - Higher highs/higher lows detection
  - Support and resistance level identification
  - Breakout detection
  - Pattern recognition (double top, double bottom)
- **Time Series Forecasting**:
  - Simple forecasting methods
  - Moving average forecasts
  - Exponential smoothing
  - Linear and polynomial regression
  - ARIMA-like models
  - Momentum-based forecasting
  - Ensemble forecasting
  - Confidence intervals

## Installation

```bash
pip install -r requirements.txt
```

## Requirements

- Python 3.7+
- NumPy >= 1.21.0
- SciPy >= 1.7.0

## Quick Start

### Options Trading Example

```python
from quantshit.options import BlackScholes, PortfolioRiskManager, historical_volatility

# Calculate option price and Greeks
bs = BlackScholes(S=100, K=105, T=0.25, r=0.05, sigma=0.2, option_type='call')
price = bs.price()
greeks = bs.greeks()

print(f"Option Price: ${price:.2f}")
print(f"Delta: {greeks['delta']:.4f}")
print(f"Gamma: {greeks['gamma']:.4f}")

# Portfolio risk management
portfolio = PortfolioRiskManager()
portfolio.add_position(
    option_contract={'strike': 100, 'expiry': 0.25, 'type': 'call'},
    quantity=10,
    greeks=greeks
)

# Calculate hedge requirements
hedge_shares = portfolio.delta_hedge_quantity()
print(f"Delta Hedge: {hedge_shares:.2f} shares")
```

### Momentum Trading Example

```python
from quantshit.momentum import (
    simple_moving_average, rsi, TrendDetector, MomentumForecaster
)
import numpy as np

# Generate sample price data
prices = np.array([100, 102, 101, 105, 107, 106, 110, 112, 111, 115])

# Calculate technical indicators
sma = simple_moving_average(prices, window=5)
rsi_value = rsi(prices, window=5)

print(f"Current SMA: ${sma[-1]:.2f}")
print(f"Current RSI: {rsi_value[-1]:.2f}")

# Detect trends
detector = TrendDetector(prices)
trend = detector.linear_regression_trend()
print(f"Trend Direction: {trend['direction']}")
print(f"Trend Strength: {trend['strength']:.2f}")

# Forecast future prices
forecaster = MomentumForecaster(prices)
forecast = forecaster.forecast_with_momentum(horizon=3)
print(f"3-period forecast: {forecast['forecast']}")
```

## Examples

Comprehensive examples are available in the `examples/` directory:

- `options_example.py`: Demonstrates options pricing, Greeks calculation, volatility analysis, risk management, and market data handling
- `momentum_example.py`: Shows technical indicators, trend detection, forecasting, and a complete trading strategy

Run the examples:

```bash
cd examples
python options_example.py
python momentum_example.py
```

## Module Structure

```
quantshit/
├── options/
│   ├── black_scholes.py      # Black-Scholes pricing model
│   ├── volatility.py          # Volatility calculations
│   ├── risk_management.py    # Portfolio risk management
│   └── market_data.py         # Order book and market data feeds
├── momentum/
│   ├── indicators.py          # Technical indicators
│   ├── trend_detection.py    # Trend analysis tools
│   └── forecasting.py         # Time series forecasting
└── utils/                     # Utility functions
```

## Use Cases

### Options Market-Making
- Identify mispriced options by comparing market prices to Black-Scholes theoretical values
- Capture bid-ask spreads by providing liquidity
- Manage risk through delta and gamma hedging
- Monitor implied vs historical volatility to identify trading opportunities

### Volatility Trading
- Trade volatility spreads when implied volatility deviates from historical volatility
- Construct volatility surfaces to identify arbitrage opportunities
- Use Greeks to manage directional and volatility risk

### Momentum Trading
- Identify trend direction and strength using multiple indicators
- Generate entry and exit signals based on moving average crossovers
- Detect support/resistance breakouts for momentum entries
- Forecast price movements using ensemble methods

### Risk Management
- Calculate portfolio Greeks for multi-leg option strategies
- Determine optimal hedge ratios for delta and gamma neutrality
- Size positions using Kelly Criterion
- Monitor VaR and CVaR for portfolio risk assessment

## Key Concepts Implemented

### Black-Scholes Model
The Black-Scholes model prices European options using the following formula:

- **Call**: C = S₀N(d₁) - Ke^(-rT)N(d₂)
- **Put**: P = Ke^(-rT)N(-d₂) - S₀N(-d₁)

Where d₁ and d₂ are calculated from the stock price, strike price, time to expiration, risk-free rate, and volatility.

### Greeks
- **Delta (Δ)**: Rate of change of option price with respect to underlying price
- **Gamma (Γ)**: Rate of change of delta with respect to underlying price
- **Theta (Θ)**: Rate of change of option price with respect to time
- **Vega (ν)**: Rate of change of option price with respect to volatility
- **Rho (ρ)**: Rate of change of option price with respect to interest rate

### Volatility
- **Historical Volatility**: Calculated from past price movements using standard deviation of log returns
- **Implied Volatility**: Derived from market option prices by solving the Black-Scholes equation
- **Volatility Smile**: Pattern where implied volatility varies with strike price
- **Volatility Surface**: 3D representation of implied volatility across strikes and expirations

### Technical Indicators
- **Moving Averages**: Smooth price data to identify trends
- **RSI**: Measures momentum on a 0-100 scale to identify overbought/oversold conditions
- **MACD**: Shows relationship between two moving averages to signal trend changes
- **Bollinger Bands**: Volatility bands that expand and contract with price volatility

## Contributing

This is a quantitative trading library designed for educational and research purposes. Contributions are welcome!

## Disclaimer

This library is for educational and research purposes only. It should not be used for actual trading without thorough testing and risk management. Trading financial instruments carries risk, and you should never trade with money you cannot afford to lose.

## License

MIT License - See LICENSE file for details