# Prediction Market Arbitrage Bot

A simple arbitrage trading bot that finds related events across different prediction markets and executes trades to capture price spreads.

## Quick Start

1. **Install dependencies:**
```bash
pip install -r requirements.txt
```

2. **Set up environment variables:**
Copy `.env.example` to `.env` and add your API keys:
```bash
cp .env.example .env
```

4. **Test the bot:**
```bash
python test_bot.py              # Test all components
python demo.py                  # Demo arbitrage strategy
python demo_expiry.py           # Demo expiry strategy  
python demo_multi_strategy.py   # Demo both strategies together
python demo_positions.py        # Demo position tracking
```

5. **Run the bot:**
```bash
# Run once for testing
python main.py --once

# Run continuously (every hour)
python main.py

# Run as REST API server
python api.py                   # Server at http://localhost:8000
python test_api.py              # Test API endpoints
```

## Deploy to Vercel

1. **Install Vercel CLI:**
```bash
npm i -g vercel
```

3. **Deploy to Vercel:**
```bash
vercel
```

4. **Set environment variables in Vercel dashboard:**
- `POLYMARKET_API_KEY`
- `MANIFOLD_API_KEY` 
- `MIN_VOLUME=1000`
- `MIN_SPREAD=0.05`
- `MAX_DAYS_TO_EXPIRY=7`

5. **Test the deployment:**
- Visit `https://your-deployment.vercel.app/` 
- API Documentation: `https://your-deployment.vercel.app/docs`
- Check health: `GET https://your-deployment.vercel.app/health`
- Get positions: `GET https://your-deployment.vercel.app/positions`

## How it works

1. **Data Collection** (`market_apis.py`): Fetches recent markets from multiple prediction platforms with expiry dates
2. **Multi-Strategy Analysis** (`strategies.py`): 
   - **Arbitrage Strategy**: Finds similar markets across platforms using text similarity and calculates price spreads
   - **Expiry Strategy**: Identifies markets close to expiration with overconfident pricing or high uncertainty
3. **Opportunity Ranking**: Combines and ranks opportunities from all strategies by expected profit
4. **Trade Execution** (`executor.py`): Places trades to capture the highest-value opportunities
5. **Position Tracking** (`position_tracker.py`): Records all trades and tracks P&L for open positions
6. **REST API** (`api.py`): Exposes endpoints for positions, trade history, and live opportunities

## Architecture

- **Modular Design**: Easy to add new platforms and strategies
- **Base Classes**: `BaseMarketAPI` and `BaseStrategy` for extensibility
- **Simple Configuration**: Environment variables for all settings
- **Minimal Dependencies**: Only essential packages for Vercel compatibility

## Adding New Platforms

1. Create a new class inheriting from `BaseMarketAPI`
2. Implement `get_recent_markets()`, `place_buy_order()`, `place_sell_order()`
3. Add to `MARKET_APIS` registry in `market_apis.py`

## Available Strategies

### 1. Arbitrage Strategy
- Finds price differences for the same event across platforms
- Uses text similarity to match related markets
- Configurable minimum spread threshold (5% default)

### 2. Expiry Strategy ⏰ **NEW**
- Targets markets close to expiration (within 7 days default)
- Identifies three patterns:
  - **Overconfident markets**: Very high/low probabilities that may correct
  - **Undervalued markets**: Very low probabilities that may be wrong
  - **Uncertain markets**: Close to 50/50 that may swing dramatically
- Higher urgency for markets expiring sooner
- Configurable time window and volume thresholds

## Adding New Strategies  

1. Create a new class inheriting from `BaseStrategy`
2. Implement `find_opportunities()` method
3. Add to `STRATEGIES` registry in `strategies.py`
4. Update bot initialization in `main.py`

## REST API Endpoints 📡

The bot exposes a comprehensive REST API for monitoring and control:

### Core Endpoints
- `GET /health` - System status and configuration
- `POST /strategy/run` - Manually trigger strategy cycle
- `GET /strategy/opportunities` - Current trading opportunities

### Position Management  
- `GET /positions` - All open positions with P&L
- `GET /positions/summary` - Portfolio statistics
- `POST /positions/update-prices` - Refresh position values

### Trade History
- `GET /trades` - Complete trade history (supports filtering)
- `GET /markets` - Current market data

### Interactive Documentation
- `/docs` - Swagger UI for testing endpoints
- `/redoc` - ReDoc API documentation

See [`API_DOCS.md`](API_DOCS.md) for complete endpoint documentation and examples.

## Files

- `main.py` - Main bot orchestration  
- `api.py` - REST API server with comprehensive endpoints
- `market_apis.py` - Platform API clients with expiry date support
- `strategies.py` - Trading strategies (arbitrage + expiry)
- `executor.py` - Trade execution with position tracking
- `position_tracker.py` - Position and trade history management
- `test_bot.py` - Bot functionality testing
- `test_api.py` - API endpoint testing
- `demo_*.py` - Various strategy demos
- `API_DOCS.md` - Complete API documentation