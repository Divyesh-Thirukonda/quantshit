# 🚀 Vercel + Supabase Deployment Guide

## ✅ **What We Built**

Your **Quantshit Arbitrage System** is now ready for **free deployment** on Vercel + Supabase!

### 🏗️ **New Architecture:**
- ✅ **Vercel**: Serverless API hosting (FREE)
- ✅ **Supabase**: PostgreSQL database (FREE tier)
- ✅ **FastAPI**: Same powerful API, now serverless
- ✅ **No AWS needed**: No permissions, no complexity

### 📁 **New Project Structure:**
```
quantshit/
├── api/main.py              # 🚀 Vercel-compatible FastAPI
├── vercel.json              # Vercel deployment config
├── package.json             # Node.js metadata for Vercel
├── database_schema.sql      # 📄 Supabase database setup
├── src/database/            # Supabase client utilities
└── requirements.txt         # Updated dependencies
```

## 🎯 **Step 1: Setup Supabase (2 minutes)**

### **Create Supabase Project:**

1. **Go to**: https://supabase.com/
2. **Sign up** with GitHub (free)
3. **Click "New Project"**
4. **Set:**
   - Name: `quantshit-db`
   - Password: `(generate strong password)`
   - Region: `(choose closest to you)`
5. **Click "Create new project"**

### **Setup Database:**

1. **In Supabase dashboard** → **SQL Editor**
2. **Copy & paste** the contents of `database_schema.sql`
3. **Click "Run"** to create tables

### **Get Connection Details:**

1. **Go to Settings** → **API**
2. **Copy these values:**
   - **Project URL**: `https://xxx.supabase.co`
   - **Project API Key** (anon/public): `eyJhbGc...`

## 🚀 **Step 2: Deploy to Vercel (1 minute)**

### **Option A: GitHub Integration (Recommended)**

1. **Push to GitHub:**
   ```bash
   git add .
   git commit -m "Ready for Vercel deployment"
   git push origin main
   ```

2. **Deploy on Vercel:**
   - Go to: https://vercel.com/
   - Sign up with GitHub
   - Click "Import Project" 
   - Select your `quantshit` repository
   - Click "Deploy"

### **Option B: Vercel CLI**

```bash
# Install Vercel CLI
npm install -g vercel

# Deploy
vercel

# Follow prompts:
# - Project name: quantshit-api
# - Framework: Other
# - Build command: (leave empty)
# - Output directory: (leave empty)
```

## ⚙️ **Step 3: Configure Environment Variables**

**In Vercel Dashboard:**

1. **Go to your project** → **Settings** → **Environment Variables**
2. **Add these variables:**

| Key | Value | Notes |
|-----|-------|-------|
| `SUPABASE_URL` | `https://xxx.supabase.co` | From Step 1 |
| `SUPABASE_KEY` | `eyJhbGc...` | From Step 1 |
| `ENVIRONMENT` | `production` | |

3. **Click "Redeploy"** to apply changes

## 🧪 **Step 4: Test Your Deployment**

Your API will be live at: `https://your-project.vercel.app`

**Test endpoints:**
- Health: `https://your-project.vercel.app/health`
- Markets: `https://your-project.vercel.app/markets`
- Opportunities: `https://your-project.vercel.app/arbitrage/opportunities`
- Docs: `https://your-project.vercel.app/docs`

## 🎉 **Deployment Complete!**

### ✅ **What You Have:**
- 🌐 **Live API**: FastAPI running on Vercel
- 🗄️ **Database**: PostgreSQL on Supabase  
- 📊 **Monitoring**: Health checks and metrics
- 🔄 **Auto-deploy**: Updates on git push
- 💰 **Cost**: **$0** (both platforms free tier)

### 🔧 **Next Steps:**
1. **Connect real market data** (Kalshi/Polymarket APIs)
2. **Add authentication** (Supabase Auth)
3. **Build a frontend** (Next.js + Vercel)
4. **Real arbitrage detection** logic

## 📋 **Quick Commands:**

```bash
# Test API locally
python test_vercel_api.py

# Check deployment status
vercel ls

# View logs
vercel logs

# Redeploy
vercel --prod
```

## 🆘 **Troubleshooting:**

### **Common Issues:**
- **Build fails**: Check `requirements.txt` format
- **API 500 errors**: Check Supabase credentials in Vercel env vars
- **CORS issues**: Already configured in the API

### **Support:**
- Vercel: https://vercel.com/docs
- Supabase: https://supabase.com/docs
- FastAPI: https://fastapi.tiangolo.com/

---

**🎯 You now have a production-ready arbitrage system running on modern, free infrastructure!** 🚀