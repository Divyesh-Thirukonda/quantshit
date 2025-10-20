"""
Quantshit Arbitrage Engine API

Clean API-only interface for cross-venue prediction market arbitrage.
No frontend - designed to be called by external applications.
"""

import uvicorn
from fastapi import FastAPI
from fastapi.responses import JSONResponse
from datetime import datetime
from typing import Dict, List, Optional

from src.engine.bot import ArbitrageBot

app = FastAPI(
    title="Quantshit Arbitrage Engine", 
    version="1.0.0",
    description="Cross-venue prediction market arbitrage detection and execution API"
)

# Global bot instance
bot = None


@app.on_event("startup")
async def startup_event():
    global bot
    bot = ArbitrageBot()


@app.get("/")
async def root():
    """API information and usage"""
    return {
        "service": "Quantshit Arbitrage Engine",
        "version": "1.0.0",
        "description": "Cross-venue prediction market arbitrage detection and execution",
        "endpoints": {
            "GET /health": "Service health check",
            "GET /markets": "Get current market data",
            "GET /scan": "Scan for arbitrage opportunities",
            "POST /execute/{opportunity_id}": "Execute arbitrage trade",
            "POST /run-strategy": "Manual strategy run"
        },
        "example_usage": {
            "scan": "GET /scan?size=250&min_edge=0.02",
            "execute": "POST /execute/arb_123"
        }
    }


@app.get("/health")
async def health_check():
    return {"status": "healthy", "timestamp": "2024-01-01T00:00:00Z"}


@app.post("/run-strategy")
async def run_strategy():
    """Manually trigger a strategy run"""
    try:
        bot.run_strategy_cycle()
        return {"success": True, "message": "Strategy cycle completed"}
    except Exception as e:
        return JSONResponse(
            status_code=500, content={"success": False, "error": str(e)}
        )


@app.get("/markets")
async def get_markets():
    """Get current market data"""
    try:
        markets_data = bot.collect_market_data()
        return {"success": True, "data": markets_data}
    except Exception as e:
        return JSONResponse(
            status_code=500, content={"success": False, "error": str(e)}
        )


@app.get("/scan") 
async def scan_opportunities(size: int = 250, min_edge: float = 0.05):
    """Scan for arbitrage opportunities - compatible with Next.js frontend"""
    try:
        # Collect market data from all platforms
        markets_data = bot.collect_market_data()
        
        # Find opportunities using existing strategy  
        opportunities = bot.strategy.find_opportunities(markets_data)
        
        # Filter by minimum edge
        filtered_ops = [op for op in opportunities if op['spread'] >= min_edge]
        
        # Format for web interface
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
                "parameters": {
                    "size": size,
                    "min_edge": min_edge
                }
            }
        }
    except Exception as e:
        return JSONResponse(
            status_code=500, content={"error": str(e)}
        )


@app.get("/search")
async def search_events(keyword: str, platforms: str = None, limit: int = 10):
    """Search for events across platforms"""
    try:
        platform_list = platforms.split(",") if platforms else None
        results = bot.search_events(keyword, platform_list, limit)
        return {"success": True, "results": results}
    except Exception as e:
        return JSONResponse(
            status_code=500, content={"success": False, "error": str(e)}
        )


@app.post("/execute")
async def execute_trade(
    platform: str, 
    event_id: str, 
    outcome: str, 
    action: str, 
    amount: float, 
    price: Optional[float] = None
):
    """Execute a trade on a specific event"""
    try:
        result = bot.execute_trade(platform, event_id, outcome, action, amount, price)
        return {"success": True, "result": result}
    except Exception as e:
        return JSONResponse(
            status_code=500, content={"success": False, "error": str(e)}
        )


if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)

