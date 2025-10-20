"""
Vercel serverless function wrapper for the Quantshit Arbitrage Engine
"""

import sys
import os

# Add the parent directory to the path so we can import our modules
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from fastapi import FastAPI
from fastapi.responses import JSONResponse
from datetime import datetime
import json

# Import our main application components
try:
    from src.engine.bot import ArbitrageBot
except ImportError:
    # Fallback for Vercel environment where some imports might fail
    ArbitrageBot = None

# Create FastAPI app
app = FastAPI(
    title="Quantshit Arbitrage Engine", 
    version="1.0.0",
    description="Cross-venue prediction market arbitrage detection API"
)

# Global bot instance
bot = None

# Mock data for when real APIs aren't available (like in serverless environment)
MOCK_OPPORTUNITIES = [
    {
        "id": "arb_0",
        "question": "Trump Wins 2024 Presidential Election",
        "yes_venue": "polymarket",
        "no_venue": "kalshi",
        "yes_price": "$0.520",
        "no_price": "$0.465",
        "size": "$250",
        "edge_bps": "150",
        "cost": "$246.25",
        "profit": "$3.75"
    },
    {
        "id": "arb_1", 
        "question": "Fed Cuts Rates in November 2024",
        "yes_venue": "kalshi",
        "no_venue": "polymarket",
        "yes_price": "$0.680",
        "no_price": "$0.310",
        "size": "$250",
        "edge_bps": "100",
        "cost": "$247.50",
        "profit": "$2.50"
    }
]

@app.on_event("startup")
async def startup_event():
    global bot
    if ArbitrageBot:
        try:
            bot = ArbitrageBot()
            print("🤖 Arbitrage Bot initialized for Vercel")
        except Exception as e:
            print(f"⚠️ Could not initialize bot: {e}. Using mock data.")
            bot = None
    else:
        print("⚠️ Running in mock mode for Vercel deployment")

@app.get("/")
async def root():
    """API information and usage"""
    return {
        "service": "Quantshit Arbitrage Engine",
        "version": "1.0.0", 
        "description": "Cross-venue prediction market arbitrage detection API",
        "deployment": "Vercel Serverless",
        "endpoints": {
            "GET /health": "Service health check",
            "GET /scan": "Scan for arbitrage opportunities",
            "POST /execute/{opportunity_id}": "Execute arbitrage trade"
        },
        "example_usage": {
            "scan": "GET /scan?size=250&min_edge=0.02",
            "execute": "POST /execute/arb_123"
        },
        "github": "https://github.com/Divyesh-Thirukonda/quantshit"
    }

@app.get("/health")
async def health_check():
    return {
        "status": "healthy", 
        "timestamp": datetime.utcnow().isoformat(),
        "environment": "vercel",
        "bot_initialized": bot is not None
    }

@app.get("/scan") 
async def scan_opportunities(size: int = 250, min_edge: float = 0.05):
    """Scan for arbitrage opportunities"""
    try:
        if bot:
            # Use real bot if available
            markets_data = bot.collect_market_data()
            opportunities = bot.strategy.find_opportunities(markets_data)
            
            # Filter by minimum edge
            filtered_ops = [op for op in opportunities if op['spread'] >= min_edge]
            
            # Format for API response
            ideas = []
            for i, opp in enumerate(filtered_ops):
                ideas.append({
                    "id": f"arb_{i}",
                    "question": opp.get('outcome', 'Unknown Market'),
                    "yes_venue": opp['buy_market']['platform'],
                    "no_venue": opp['sell_market']['platform'],
                    "yes_price": f"${opp['buy_market']['price']:.3f}",
                    "no_price": f"${1 - opp['sell_market']['price']:.3f}",
                    "size": f"${size}",
                    "edge_bps": f"{int(opp['spread'] * 10000)}",
                    "cost": f"${opp['trade_amount']:.2f}",
                    "profit": f"${opp['expected_profit']:.2f}"
                })
            
            return {
                "success": True,
                "opportunities": ideas,
                "meta": {
                    "scanned_markets": sum(len(markets) for markets in markets_data.values()),
                    "opportunities_found": len(filtered_ops),
                    "timestamp": datetime.utcnow().isoformat(),
                    "parameters": {"size": size, "min_edge": min_edge},
                    "source": "live_data"
                }
            }
        else:
            # Use mock data for demo
            filtered_mock = [opp for opp in MOCK_OPPORTUNITIES if int(opp['edge_bps']) >= min_edge * 10000]
            
            return {
                "success": True,
                "opportunities": filtered_mock,
                "meta": {
                    "scanned_markets": 25,
                    "opportunities_found": len(filtered_mock),
                    "timestamp": datetime.utcnow().isoformat(),
                    "parameters": {"size": size, "min_edge": min_edge},
                    "source": "mock_data",
                    "note": "Add API keys to environment variables for live data"
                }
            }
            
    except Exception as e:
        return JSONResponse(
            status_code=500, content={"success": False, "error": str(e)}
        )

@app.post("/execute/{idea_id}")
async def execute_trade(idea_id: str):
    """Execute an arbitrage trade"""
    try:
        if bot and hasattr(bot, 'executor'):
            # Use real executor if available
            result = bot.executor.execute_arbitrage({"id": idea_id})
            return {"success": True, "result": result, "source": "live_execution"}
        else:
            # Mock execution for demo
            return {
                "success": True,
                "message": f"Mock execution for opportunity {idea_id}",
                "execution_id": f"exec_{int(datetime.utcnow().timestamp())}",
                "status": "completed",
                "legs": [
                    {"venue": "polymarket", "side": "buy", "status": "filled"},
                    {"venue": "kalshi", "side": "sell", "status": "filled"}
                ],
                "source": "mock_execution",
                "note": "Add API keys to environment variables for live execution"
            }
    except Exception as e:
        return JSONResponse(
            status_code=500, content={"success": False, "error": str(e)}
        )

# Export the FastAPI app for Vercel
handler = app

# For local development
if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)