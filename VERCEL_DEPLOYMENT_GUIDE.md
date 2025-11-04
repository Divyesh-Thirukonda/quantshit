# 🚀 Vercel Deployment Guide for Quantshit Trading API

## Step-by-Step Vercel Setup

### 1. **Go to Vercel Dashboard**
   - Visit: [vercel.com](https://vercel.com)
   - Sign in with your GitHub account
   - Click **"New Project"**

### 2. **Import Your Repository**
   - Click **"Import Git Repository"**
   - Select your GitHub account
   - Find and select: **`Divyesh-Thirukonda/quantshit`**
   - Click **"Import"**

### 3. **Configure Project Settings**
   - **Project Name**: `quantshit-trading-api` (or whatever you prefer)
   - **Framework Preset**: Vercel will auto-detect "Other"
   - **Root Directory**: Leave as `.` (root)
   - **Build and Output Settings**: Leave as default

### 4. **Deploy**
   - Click **"Deploy"**
   - Wait 2-3 minutes for the build to complete
   - You'll get a URL like: `https://quantshit-trading-api.vercel.app`

### 5. **Test Your Deployment**
   - Visit your deployed URL
   - You should see the API info page
   - Test key endpoints:
     - `GET /` - API info
     - `GET /health` - Health check
     - `GET /docs` - Interactive API documentation
     - `POST /pipeline/scan-markets` - Pipeline test

## 🔧 Environment Variables (Optional - Add Later)

In Vercel Dashboard → Project → Settings → Environment Variables:

```
POLYMARKET_API_KEY=your_polymarket_api_key_here
KALSHI_API_KEY=your_kalshi_api_key_here
SUPABASE_URL=your_supabase_url_here
SUPABASE_KEY=your_supabase_key_here
```

**Note**: The API works without these variables (shows mock data) - add them when you're ready for live data.

## 📱 What You'll Have After Deployment

### ✅ **Live API Endpoints**
```
https://your-app.vercel.app/
├── /                           # API info
├── /health                     # Health check
├── /docs                       # Interactive API docs
├── /pipeline/
│   ├── scan-markets           # Step 1: Market scanning
│   ├── detect-opportunities   # Step 2: Find arbitrage
│   ├── portfolio-management   # Step 3: Position sizing
│   └── execute-trades         # Step 4: Trade execution
└── /dashboard/
    ├── overview               # Portfolio summary
    ├── opportunities          # Live opportunities
    ├── positions              # Current positions
    └── performance            # Performance metrics
```

### ✅ **Pipeline Flow** (Works immediately with mock data)
```bash
# Test the complete pipeline
curl -X POST https://your-app.vercel.app/pipeline/scan-markets
curl -X POST https://your-app.vercel.app/pipeline/detect-opportunities  
curl -X POST https://your-app.vercel.app/pipeline/portfolio-management
curl -X POST "https://your-app.vercel.app/pipeline/execute-trades?paper_trading=true"
```

### ✅ **Dashboard Data** (For frontend development)
```bash
# Get dashboard data
curl https://your-app.vercel.app/dashboard/overview
curl https://your-app.vercel.app/dashboard/opportunities
curl https://your-app.vercel.app/dashboard/positions
curl https://your-app.vercel.app/dashboard/performance
```

## 🔄 Automatic Deployments

Vercel will automatically redeploy when you push to the main branch:

```bash
# Make changes, then:
git add .
git commit -m "Your update message"
git push origin main
# Vercel automatically rebuilds and deploys!
```

## ⏰ Setting Up Cron Jobs

### Option 1: Vercel Cron (Recommended)
Add to your `vercel.json`:
```json
{
  "crons": [
    {
      "path": "/pipeline/scan-markets",
      "schedule": "0 * * * *"
    },
    {
      "path": "/pipeline/detect-opportunities", 
      "schedule": "*/30 * * * *"
    }
  ]
}
```

### Option 2: External Cron Service
Use services like:
- **UptimeRobot** (free monitoring + cron)
- **Zapier** (automation)
- **GitHub Actions** (free for public repos)

### Option 3: Server Cron Jobs
```bash
# Every hour: scan markets
0 * * * * curl -X POST https://your-app.vercel.app/pipeline/scan-markets

# Every 30 minutes: detect opportunities
*/30 * * * * curl -X POST https://your-app.vercel.app/pipeline/detect-opportunities
```

## 🛠️ Troubleshooting

### Build Fails?
1. Check the build logs in Vercel dashboard
2. Make sure `requirements.txt` has all dependencies
3. Verify `vercel.json` configuration

### API Not Working?
1. Check `/health` endpoint first
2. Look at function logs in Vercel dashboard
3. Test locally: `python -m uvicorn api.app:app --reload`

### Want to Test Locally?
```bash
# Install Vercel CLI
npm i -g vercel

# Test locally with Vercel environment
vercel dev
```

## 🎯 Next Steps After Deployment

1. **✅ Share the URL** with your team
2. **✅ Test all endpoints** work correctly  
3. **✅ Set up monitoring** (UptimeRobot for uptime)
4. **✅ Add cron jobs** for automated trading
5. **✅ Build frontend** using the dashboard endpoints
6. **✅ Add real API keys** when ready for live data

## 📋 Quick Test Commands

After deployment, test these:

```bash
# Replace YOUR_URL with your actual Vercel URL
export API_URL="https://your-app.vercel.app"

# Test API health
curl $API_URL/health

# Test pipeline (should return mock data)
curl -X POST $API_URL/pipeline/scan-markets

# Test dashboard data
curl $API_URL/dashboard/overview

# View interactive docs
open $API_URL/docs
```

---

**🎉 Your trading API will be live and working with the complete pipeline!**

The system is designed to work immediately without any configuration - perfect for testing, team collaboration, and frontend development!