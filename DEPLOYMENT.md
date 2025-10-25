# Vercel Deployment Guide

This project supports both **paper trading** (test) and **live trading** (production) environments.

## 🧪 Paper Trading Deployment (Test Environment)

### Step 1: Deploy Paper Trading Version
```bash
# Deploy paper trading version
vercel --prod --env TRADING_MODE=paper --env ENVIRONMENT=development
```

### Step 2: Set Environment Variables in Vercel
Go to your Vercel dashboard → Project Settings → Environment Variables:

```
TRADING_MODE=paper
ENVIRONMENT=development
MIN_VOLUME=1000
MIN_SPREAD=0.01
MAX_POSITION_SIZE=1000
MAX_TOTAL_EXPOSURE=5000
MAX_DAILY_TRADES=50
MAX_LOSS_PER_DAY=1000
MIN_PROFIT_THRESHOLD=0.01
```

### Step 3: Test Paper Trading
- Visit your deployed URL
- Call `GET /status` to verify paper trading mode
- Use `POST /scan` to find opportunities (using simulated data)
- Use `POST /execute/{id}` to test trades (with paper money)

## 💰 Production Deployment (Live Trading)

### Step 1: Get Real API Keys
1. **Kalshi**: Sign up at https://kalshi.com, get API key and private key
2. **Polymarket**: Get API credentials from Polymarket

### Step 2: Deploy Production Version
```bash
# Deploy to production environment
vercel --prod --env TRADING_MODE=live --env ENVIRONMENT=production
```

### Step 3: Set Environment Variables in Vercel
Go to your Vercel dashboard → Project Settings → Environment Variables:

```
TRADING_MODE=live
ENVIRONMENT=production
MIN_VOLUME=1000
MIN_SPREAD=0.05
MAX_POSITION_SIZE=500
MAX_TOTAL_EXPOSURE=2000
MAX_DAILY_TRADES=10
MAX_LOSS_PER_DAY=200
MIN_PROFIT_THRESHOLD=0.05

# CRITICAL: Real API credentials
KALSHI_API_KEY=your_real_kalshi_api_key
KALSHI_PRIVATE_KEY=your_real_kalshi_private_key
POLYMARKET_API_KEY=your_real_polymarket_api_key
POLYMARKET_PRIVATE_KEY=your_real_polymarket_private_key
```

## 🚀 Multiple Environment Strategy

### Option 1: Two Separate Projects
- `quantshit-paper` - Paper trading environment
- `quantshit-live` - Live trading environment

### Option 2: Single Project with Branch Deployment
- `main` branch → Paper trading (default)
- `production` branch → Live trading

### Option 3: Environment-based Deployment
Use Vercel's environment features to deploy the same code with different configs:

```bash
# Deploy paper trading
vercel --prod --env TRADING_MODE=paper

# Deploy live trading (to different domain)
vercel --prod --env TRADING_MODE=live --env VERCEL_PROJECT_NAME=quantshit-live
```

## 📊 Monitoring Both Environments

### Paper Trading URLs:
- Health: `https://your-app.vercel.app/health`
- Status: `https://your-app.vercel.app/status`
- Scan: `POST https://your-app.vercel.app/scan`

### Live Trading URLs:
- Health: `https://your-live-app.vercel.app/health`
- Status: `https://your-live-app.vercel.app/status`
- Capital: `https://your-live-app.vercel.app/status` (shows real balances)

## ⚠️ Safety Recommendations

1. **Always test in paper trading first**
2. **Start with small position sizes in production**
3. **Monitor API rate limits**
4. **Set up alerts for failed trades**
5. **Keep API keys secure** (never commit to git)

## 🔧 Local Development

### Paper Trading:
```bash
cp .env.paper .env
python main.py
```

### Live Trading Testing:
```bash
cp .env.production .env
# Add your real API keys to .env
python main.py
```

## 📈 Capital Management

### Paper Trading:
- Starts with $10,000 per platform
- Unlimited "funding"
- Perfect for strategy testing

### Live Trading:
- Uses real account balances
- Must deposit funds on each platform
- Real P&L tracking

## 🔍 Debugging

Check which mode you're running:
```bash
curl https://your-app.vercel.app/status
```

Response shows:
```json
{
  "trading_mode": "paper",
  "environment": "development",
  "bot_status": "active",
  "capital": {
    "balances": {
      "kalshi": 10000,
      "polymarket": 10000
    }
  }
}
```