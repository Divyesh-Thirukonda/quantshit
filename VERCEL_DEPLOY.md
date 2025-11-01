# 🚀 Vercel Deployment Guide

## Step 1: Push to GitHub (if not done already)

```bash
git add .
git commit -m "Ready for Vercel deployment"
git push origin main
```

## Step 2: Deploy to Vercel

1. Go to [vercel.com](https://vercel.com)
2. Click "New Project"
3. Import your GitHub repository: `Divyesh-Thirukonda/quantshit`
4. Vercel will auto-detect the Python project
5. Click "Deploy"

## Step 3: Environment Variables (Optional for now)

In Vercel dashboard → Settings → Environment Variables, add:

```
SUPABASE_URL=your_supabase_url_here
SUPABASE_KEY=your_supabase_key_here
KALSHI_API_KEY=your_kalshi_key_here
POLYMARKET_API_KEY=your_polymarket_key_here
```

## Step 4: Test Your Deployed API

Your API will be available at: `https://your-app-name.vercel.app`

Test endpoints:
- `GET /` - Main info page
- `GET /api/v1/health` - Health check
- `GET /api/v1/status` - Deployment status
- `GET /api/v1/markets` - Markets (mock data)
- `GET /api/v1/arbitrage/opportunities` - Arbitrage opportunities
- `GET /docs` - Interactive API documentation

## What Works Right Now

✅ **All API endpoints** (with mock data)
✅ **API documentation** at `/docs`
✅ **Health monitoring** at `/api/v1/health`
✅ **CORS enabled** for frontend development
✅ **Production-ready** FastAPI setup

## What You'll Get

A live API that responds with real data structure like:

```json
{
  "message": "🎯 Prediction Market Arbitrage API",
  "status": "deployed",
  "endpoints": {
    "health": "/api/v1/health",
    "markets": "/api/v1/markets",
    "arbitrage": "/api/v1/arbitrage/opportunities",
    "portfolio": "/api/v1/portfolio",
    "docs": "/docs"
  }
}
```

## After Deployment

1. **Share the URL** with your team
2. **Test all endpoints** work correctly
3. **Add environment variables** when ready
4. **Start building** real data integration

The system is designed to work without any environment variables - it will just show "not_connected" status for database/external APIs until you add the keys.