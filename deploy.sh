#!/bin/bash

# Deployment script for Quantshit Arbitrage Engine

echo "🚀 Quantshit Deployment Script"
echo ""

# Check if vercel CLI is installed
if ! command -v vercel &> /dev/null; then
    echo "❌ Vercel CLI not found. Please install it first:"
    echo "   npm i -g vercel"
    exit 1
fi

# Ask user which environment to deploy
echo "Select deployment environment:"
echo "1) Paper Trading (Test Environment)"
echo "2) Live Trading (Production Environment)"
echo ""
read -p "Enter choice (1 or 2): " choice

case $choice in
    1)
        echo "🧪 Deploying Paper Trading Environment..."
        
        # Copy paper trading env file
        cp .env.paper .env.deploy
        
        # Deploy with paper trading settings
        vercel --prod \
            --env TRADING_MODE=paper \
            --env ENVIRONMENT=development \
            --env MIN_VOLUME=1000 \
            --env MIN_SPREAD=0.01 \
            --env MAX_POSITION_SIZE=1000 \
            --env MAX_TOTAL_EXPOSURE=5000 \
            --env MAX_DAILY_TRADES=50 \
            --env MAX_LOSS_PER_DAY=1000 \
            --env MIN_PROFIT_THRESHOLD=0.01
        
        echo "✅ Paper trading deployment complete!"
        echo "🔗 Test your deployment:"
        echo "   GET /health - Check if service is running"
        echo "   GET /status - Verify paper trading mode"
        echo "   POST /scan - Find arbitrage opportunities"
        ;;
        
    2)
        echo "💰 Deploying Live Trading Environment..."
        echo ""
        echo "⚠️  WARNING: This will deploy with REAL MONEY trading!"
        echo "⚠️  Make sure you have:"
        echo "   - Real API keys from Kalshi and Polymarket"
        echo "   - Sufficient funds deposited on both platforms"
        echo "   - Tested your strategy in paper trading first"
        echo ""
        read -p "Are you sure you want to continue? (yes/no): " confirm
        
        if [ "$confirm" != "yes" ]; then
            echo "❌ Deployment cancelled"
            exit 1
        fi
        
        # Check if production env file exists
        if [ ! -f ".env.production" ]; then
            echo "❌ .env.production file not found!"
            echo "   Please create it with your real API keys"
            exit 1
        fi
        
        echo "📋 Please make sure to set these environment variables in Vercel dashboard:"
        echo "   KALSHI_API_KEY=your_real_kalshi_key"
        echo "   KALSHI_PRIVATE_KEY=your_real_kalshi_private_key" 
        echo "   POLYMARKET_API_KEY=your_real_polymarket_key"
        echo "   POLYMARKET_PRIVATE_KEY=your_real_polymarket_private_key"
        echo ""
        read -p "Have you set the API keys in Vercel? (yes/no): " keys_set
        
        if [ "$keys_set" != "yes" ]; then
            echo "❌ Please set API keys in Vercel dashboard first"
            exit 1
        fi
        
        # Deploy with live trading settings
        vercel --prod \
            --env TRADING_MODE=live \
            --env ENVIRONMENT=production \
            --env MIN_VOLUME=1000 \
            --env MIN_SPREAD=0.05 \
            --env MAX_POSITION_SIZE=500 \
            --env MAX_TOTAL_EXPOSURE=2000 \
            --env MAX_DAILY_TRADES=10 \
            --env MAX_LOSS_PER_DAY=200 \
            --env MIN_PROFIT_THRESHOLD=0.05
        
        echo "✅ Live trading deployment complete!"
        echo "🔗 Monitor your deployment:"
        echo "   GET /health - Check if service is running" 
        echo "   GET /status - Check real account balances"
        echo "   POST /scan - Find real arbitrage opportunities"
        echo ""
        echo "⚠️  IMPORTANT: Monitor your trades closely!"
        ;;
        
    *)
        echo "❌ Invalid choice. Please run the script again."
        exit 1
        ;;
esac

echo ""
echo "🎉 Deployment script complete!"
echo "📚 See DEPLOYMENT.md for more details"