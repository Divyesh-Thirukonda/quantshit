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

3. **Test the bot:**
```bash
python test_bot.py
```

4. **Run locally:**
```bash
# Run once
python main.py --once

# Run continuously (every hour)
python main.py

# Run as API server
python api.py
```

## Deploy to Vercel

1. **Install Vercel CLI:**
```bash
npm i -g vercel
```

2. **Deploy:**
```bash
vercel
```

3. **Set environment variables in Vercel dashboard:**
- `POLYMARKET_API_KEY`
- `MANIFOLD_API_KEY` 
- `MIN_VOLUME=1000`
- `MIN_SPREAD=0.05`

4. **Test the deployment:**
- Visit `https://your-deployment.vercel.app/`
- Trigger manual run: `POST https://your-deployment.vercel.app/run-strategy`
- Get market data: `GET https://your-deployment.vercel.app/markets`

## How it works

1. **Data Collection** (`market_apis.py`): Fetches recent markets from multiple prediction platforms
2. **Market Matching** (`strategies.py`): Finds similar markets across platforms using text similarity
3. **Arbitrage Detection**: Calculates price spreads and identifies profitable opportunities  
4. **Trade Execution** (`executor.py`): Places trades to capture the spread

## Architecture

- **Modular Design**: Easy to add new platforms and strategies
- **Base Classes**: `BaseMarketAPI` and `BaseStrategy` for extensibility
- **Simple Configuration**: Environment variables for all settings
- **Minimal Dependencies**: Only essential packages for Vercel compatibility

## Adding New Platforms

1. Create a new class inheriting from `BaseMarketAPI`
2. Implement `get_recent_markets()`, `place_buy_order()`, `place_sell_order()`
3. Add to `MARKET_APIS` registry in `market_apis.py`

## Adding New Strategies  

1. Create a new class inheriting from `BaseStrategy`
2. Implement `find_opportunities()`
3. Add to `STRATEGIES` registry in `strategies.py`

## Files

- `main.py` - Main bot orchestration
- `api.py` - FastAPI web interface for Vercel  
- `market_apis.py` - Platform API clients
- `strategies.py` - Trading strategies
- `executor.py` - Trade execution engine
- `test_bot.py` - Testing script