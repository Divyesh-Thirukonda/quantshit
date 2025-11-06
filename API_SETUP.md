# API Setup Guide

## Overview

This API provides endpoints for the arbitrage trading bot pipeline and frontend dashboard.

## Architecture

### Trading Pipeline (Automated)
1. **`/api/scan-markets`** (POST) - Cron job runs hourly
   - Fetches markets from Kalshi and Polymarket
   - Uses Matcher to find similar markets
   - Stores markets and matches in Supabase
   
2. **`/api/detect-opportunities`** (POST) - Called after scan
   - Analyzes matched markets for arbitrage opportunities
   - Uses SimpleArbitrageStrategy to filter profitable trades
   - Stores opportunities in database
   
3. **`/api/manage-portfolio`** (POST) - Portfolio management
   - Reviews open positions
   - Calculates current P&L
   - Decides when to close positions
   
4. **`/api/execute-trades`** (POST) - Trade execution
   - Executes new opportunities
   - Places orders on both exchanges
   - Creates position and order records

### Frontend Endpoints (Read-only)
- **`GET /api/markets`** - Get active markets (optional `?exchange=kalshi|polymarket`)
- **`GET /api/opportunities`** - Get active arbitrage opportunities
- **`GET /api/positions`** - Get open positions
- **`GET /api/orders`** - Get orders (optional `?position_id=uuid`)
- **`GET /api/stats`** - Get trading statistics
- **`GET /api/scans`** - Get recent scan logs (optional `?limit=10`)
- **`GET /health`** - Health check

## Setup

### 1. Set up Supabase

1. Create a new Supabase project at https://supabase.com
2. Run the SQL from `supabase_schema.sql` in your Supabase SQL Editor
3. Get your Supabase URL and anon key from Project Settings > API

### 2. Configure Environment Variables

In your Vercel project settings, add:

```bash
SUPABASE_URL=https://your-project.supabase.co
SUPABASE_KEY=your-anon-key
```

You'll also need exchange API keys:
```bash
KALSHI_API_KEY=your-kalshi-key
KALSHI_API_SECRET=your-kalshi-secret
POLYMARKET_API_KEY=your-polymarket-key
```

### 3. Deploy to Vercel

```bash
vercel --prod
```

The cron job is automatically configured in `vercel.json` to run hourly.

## Cron Job

The cron job runs every hour (on the hour) and triggers `/api/scan-markets`:

```json
{
  "crons": [
    {
      "path": "/api/scan-markets",
      "schedule": "0 * * * *"
    }
  ]
}
```

Cron schedule format: `minute hour day month dayOfWeek`
- `0 * * * *` = Every hour at minute 0
- `*/30 * * * *` = Every 30 minutes
- `0 */2 * * *` = Every 2 hours

## Pipeline Flow

```
┌─────────────────────────────────────────────────────────────┐
│  CRON JOB (Hourly)                                          │
└────────────┬────────────────────────────────────────────────┘
             │
             ▼
    ┌────────────────────┐
    │  /scan-markets     │  Fetch markets, find matches
    └────────┬───────────┘
             │
             ▼
    ┌────────────────────┐
    │ /detect-opps       │  Analyze for arbitrage
    └────────┬───────────┘
             │
             ▼
    ┌────────────────────┐
    │ /manage-portfolio  │  Check open positions
    └────────┬───────────┘
             │
             ▼
    ┌────────────────────┐
    │ /execute-trades    │  Execute new opportunities
    └────────────────────┘
```

## Database Schema

### Tables
- **markets** - Market data from exchanges
- **market_matches** - Paired markets found by Matcher
- **opportunities** - Detected arbitrage opportunities
- **positions** - Open and closed trading positions
- **orders** - Individual orders on exchanges
- **scan_logs** - Logs of scanning operations

### Views
- **active_opportunities** - Opportunities with market details
- **open_positions** - Positions with order counts
- **trading_stats** - Aggregate trading statistics

## Frontend Integration

Your frontend can call these GET endpoints:

```javascript
// Get active opportunities
const response = await fetch('https://your-app.vercel.app/api/opportunities');
const data = await response.json();
console.log(data.opportunities);

// Get trading stats
const stats = await fetch('https://your-app.vercel.app/api/stats');
const statsData = await stats.json();
console.log(statsData.stats);
```

## Development

To test locally:

```bash
# Install dependencies
pip install -r requirements.txt

# Set environment variables
export SUPABASE_URL=your-url
export SUPABASE_KEY=your-key

# Test a specific endpoint
curl -X POST http://localhost:3000/api/scan-markets
```

## Notes

- **Paper Trading**: Currently set to paper trading mode (no real trades)
- **Rate Limits**: Be aware of exchange API rate limits
- **Error Handling**: All endpoints return JSON with `success` field
- **CORS**: Enabled for frontend access
- **Authentication**: Add authentication layer before production use

## Troubleshooting

1. **Cron not running**: Check Vercel logs, ensure you're on a Pro plan (crons require Pro)
2. **Database errors**: Verify SUPABASE_URL and SUPABASE_KEY are set
3. **Import errors**: Make sure all dependencies are in requirements.txt
4. **250MB limit**: Keep dependencies minimal, exclude large files in .vercelignore
