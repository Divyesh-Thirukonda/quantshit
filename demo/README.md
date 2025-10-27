# Demo Mode - Enhanced with Backtesting & Visualization

This folder contains enhanced demo data with historical backtesting and visualization capabilities for the arbitrage bot.

## What's Included

### Core Files
- **data_generator.py** - Generate realistic market data with 30 days of history
- **backtester.py** - Comprehensive backtesting framework with performance metrics
- **visualizer.py** - Chart generation and visualization suite
- **demo_runner.py** - Traditional demo mode runner for current snapshot
- **polymarket_markets.json** - 25 markets with historical data
- **kalshi_markets.json** - 25 markets with historical data
- **.env.demo** - Demo configuration settings

### Generated Visualizations
- **backtest_dashboard.png** - Comprehensive performance dashboard
- **cumulative_returns.png** - Profit over time chart
- **daily_profits.png** - Daily P&L distribution

## Demo Market Data

Markets span multiple real-world categories (25 per platform):
- **Politics**: Elections, approval ratings, government actions
- **Economics**: GDP, inflation, interest rates, market indices
- **Crypto**: Bitcoin, Ethereum price targets
- **Technology**: Stock prices (Tesla, Apple, Nvidia, Meta), product launches
- **Finance**: Commodities (gold, oil), currencies
- **Sports**: NBA playoffs, NFL championships
- **Weather/Climate**: Hurricane activity, temperature records

Each market includes 30 days of historical price data generated using geometric Brownian motion for realistic price movements.

## Running the Demo

### 1. Generate Demo Data (First Time)
```bash
python demo/data_generator.py
```
This creates 25 markets per platform with 30 days of historical data.

### 2. Run Backtesting
```bash
python demo/backtester.py
```
Simulates trading over historical data and shows performance metrics:
- Total profit: ~$3,239
- Total trades: 90 over 30 days
- Win rate: 100%
- Sharpe ratio: 437.35
- Projected returns for next 30 days

### 3. Generate Visualizations
```bash
python demo/visualizer.py
```
Creates professional charts:
- Cumulative profit over time
- Daily P&L distribution
- Spread distribution
- Trading activity
- Comprehensive dashboard

### 4. Traditional Demo Mode
```bash
python demo/demo_runner.py
```
Runs strategy on current market snapshot to find arbitrage opportunities.

### What the Demo Does

1. Loads fake market data from JSON files
2. Displays all markets from both platforms
3. Runs the arbitrage strategy to find opportunities
4. Shows detailed information about each arbitrage opportunity:
   - Buy/sell markets
   - Prices and spreads
   - Expected profit
   - Trade amounts

### Adjusting Parameters

Edit `demo/.env.demo` to change:
- `MIN_SPREAD` - Minimum price spread to consider (default: 0.05 = 5%)
- `MIN_VOLUME` - Minimum market volume required (default: $1,000,000)

### Example Output

```
================================================================================
ARBITRAGE BOT - DEMO MODE
================================================================================

Running with fake market data from demo/ folder
Configuration:
  MIN_VOLUME: $1,000,000
  MIN_SPREAD: 5.0%

================================================================================
DEMO MODE - Loaded Market Data
================================================================================

POLYMARKET:
  Total markets: 5
  Total volume: $33,500,000

  Markets:
    - Will Donald Trump win the 2024 US Presidential Election?
      YES: $0.52 | NO: $0.48 | Volume: $15,000,000
    - Will Bitcoin reach $100,000 by end of 2024?
      YES: $0.35 | NO: $0.65 | Volume: $8,500,000
    ...

================================================================================
ARBITRAGE OPPORTUNITIES FOUND
================================================================================

Opportunity #1:
  Type: cross_platform_arbitrage
  Buy Market: Will Donald Trump win the 2024 US Presidential Election? (polymarket)
  Sell Market: Donald Trump to win 2024 Presidential Election (kalshi)
  Buy Price: $0.5200
  Sell Price: $0.5800
  Spread: 11.54%
  Expected Profit: $600.00
  Trade Amount: $10,000.00
```

## API Endpoints

The demo features are accessible via REST API:

### Run Backtest
```
GET /backtest?min_spread=0.05&min_volume=1000000&max_trades_per_day=3&trade_amount=1000
```
Returns full backtest results with trade history, metrics, and projections.

### Get Visualizations
```
GET /backtest/visualizations
```
Returns all charts as base64-encoded PNG images.

### Get Projections
```
GET /backtest/projections?days_forward=30
```
Returns projected returns with confidence intervals.

### Example Usage
```python
import requests

# Get backtest results
response = requests.get('http://localhost:8000/backtest')
data = response.json()
print(f"Total Profit: ${data['backtest']['summary']['total_profit']:.2f}")

# Get visualizations
response = requests.get('http://localhost:8000/backtest/visualizations')
plots = response.json()['plots']

# Save dashboard image
import base64
with open('dashboard.png', 'wb') as f:
    f.write(base64.b64decode(plots['dashboard']))
```

## Performance Metrics

The backtesting framework calculates:
- **Total Profit**: Cumulative profit over test period
- **Profit per Trade**: Average profit per executed trade
- **Win Rate**: Percentage of profitable trades
- **Sharpe Ratio**: Risk-adjusted return metric (annualized)
- **Max Drawdown**: Largest peak-to-trough decline
- **Average Spread**: Mean spread captured across trades

## Configuration

Adjust parameters in `demo/.env.demo`:
```
MIN_VOLUME=1000000    # Minimum market volume
MIN_SPREAD=0.05       # Minimum spread (5%)
```

## Next Steps

1. **Test locally**: Run all demo scripts to verify functionality
2. **Review visualizations**: Check generated PNG charts
3. **Test API**: Start server and test backtest endpoints
4. **Deploy**: Push to Vercel for production access
5. **Real trading**: Configure API keys in `.env` and run `python main.py --once`

## Notes

- Demo data is synthetic and optimized to showcase capabilities
- Real-world performance will vary based on market conditions
- No actual trades are executed in demo mode
- Generated data uses realistic statistical models but is not real market data
