# PowerShell Deployment script for Quantshit Arbitrage Engine

Write-Host "🚀 Quantshit Deployment Script" -ForegroundColor Green
Write-Host ""

# Check if vercel CLI is installed
try {
    vercel --version | Out-Null
} catch {
    Write-Host "❌ Vercel CLI not found. Please install it first:" -ForegroundColor Red
    Write-Host "   npm i -g vercel" -ForegroundColor Yellow
    exit 1
}

# Ask user which environment to deploy
Write-Host "Select deployment environment:"
Write-Host "1) Paper Trading (Test Environment)"
Write-Host "2) Live Trading (Production Environment)"
Write-Host ""
$choice = Read-Host "Enter choice (1 or 2)"

switch ($choice) {
    "1" {
        Write-Host "🧪 Deploying Paper Trading Environment..." -ForegroundColor Blue
        
        # Deploy with paper trading settings
        vercel deploy --prod `
            --env TRADING_MODE=paper `
            --env ENVIRONMENT=development `
            --env MIN_VOLUME=1000 `
            --env MIN_SPREAD=0.01 `
            --env MAX_POSITION_SIZE=1000 `
            --env MAX_TOTAL_EXPOSURE=5000 `
            --env MAX_DAILY_TRADES=50 `
            --env MAX_LOSS_PER_DAY=1000 `
            --env MIN_PROFIT_THRESHOLD=0.01
        
        Write-Host "✅ Paper trading deployment complete!" -ForegroundColor Green
        Write-Host "🔗 Test your deployment:"
        Write-Host "   GET /health - Check if service is running"
        Write-Host "   GET /status - Verify paper trading mode"
        Write-Host "   POST /scan - Find arbitrage opportunities"
    }
    
    "2" {
        Write-Host "💰 Deploying Live Trading Environment..." -ForegroundColor Yellow
        Write-Host ""
        Write-Host "⚠️  WARNING: This will deploy with REAL MONEY trading!" -ForegroundColor Red
        Write-Host "⚠️  Make sure you have:" -ForegroundColor Red
        Write-Host "   - Real API keys from Kalshi and Polymarket"
        Write-Host "   - Sufficient funds deposited on both platforms"
        Write-Host "   - Tested your strategy in paper trading first"
        Write-Host ""
        $confirm = Read-Host "Are you sure you want to continue? (yes/no)"
        
        if ($confirm -ne "yes") {
            Write-Host "❌ Deployment cancelled" -ForegroundColor Red
            exit 1
        }
        
        # Check if production env file exists
        if (!(Test-Path ".env.production")) {
            Write-Host "❌ .env.production file not found!" -ForegroundColor Red
            Write-Host "   Please create it with your real API keys"
            exit 1
        }
        
        Write-Host "📋 Please make sure to set these environment variables in Vercel dashboard:"
        Write-Host "   KALSHI_API_KEY=your_real_kalshi_key"
        Write-Host "   KALSHI_PRIVATE_KEY=your_real_kalshi_private_key" 
        Write-Host "   POLYMARKET_API_KEY=your_real_polymarket_key"
        Write-Host "   POLYMARKET_PRIVATE_KEY=your_real_polymarket_private_key"
        Write-Host ""
        $keys_set = Read-Host "Have you set the API keys in Vercel? (yes/no)"
        
        if ($keys_set -ne "yes") {
            Write-Host "❌ Please set API keys in Vercel dashboard first" -ForegroundColor Red
            exit 1
        }
        
        # Deploy with live trading settings
        vercel deploy --prod `
            --env TRADING_MODE=live `
            --env ENVIRONMENT=production `
            --env MIN_VOLUME=1000 `
            --env MIN_SPREAD=0.05 `
            --env MAX_POSITION_SIZE=500 `
            --env MAX_TOTAL_EXPOSURE=2000 `
            --env MAX_DAILY_TRADES=10 `
            --env MAX_LOSS_PER_DAY=200 `
            --env MIN_PROFIT_THRESHOLD=0.05
        
        Write-Host "✅ Live trading deployment complete!" -ForegroundColor Green
        Write-Host "🔗 Monitor your deployment:"
        Write-Host "   GET /health - Check if service is running" 
        Write-Host "   GET /status - Check real account balances"
        Write-Host "   POST /scan - Find real arbitrage opportunities"
        Write-Host ""
        Write-Host "⚠️  IMPORTANT: Monitor your trades closely!" -ForegroundColor Red
    }
    
    default {
        Write-Host "❌ Invalid choice. Please run the script again." -ForegroundColor Red
        exit 1
    }
}

Write-Host ""
Write-Host "🎉 Deployment script complete!" -ForegroundColor Green
Write-Host "📚 See DEPLOYMENT.md for more details"