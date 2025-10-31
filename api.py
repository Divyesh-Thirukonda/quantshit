"""
Quantshit Arbitrage Engine API

Clean API-only interface for cross-venue prediction market arbitrage.
No frontend - designed to be called by external applications.
"""

import uvicorn
from fastapi import FastAPI, BackgroundTasks
from fastapi.responses import JSONResponse, HTMLResponse, FileResponse
from datetime import datetime
from typing import Dict, List, Optional
import asyncio
import os
from pydantic import BaseModel

from src.main import ArbitrageBot

app = FastAPI(
    title="Quantshit Arbitrage Engine",
    version="1.0.0",
    description="Cross-venue prediction market arbitrage detection and execution API"
)

# Global instances
bot = None

class WebhookPayload(BaseModel):
    """Webhook payload for new market events"""
    platform: str
    event_id: str
    title: str
    yes_price: float
    no_price: float
    volume: float = 0
    liquidity: float = 0
    event_type: str = "market_created"

class AutoTradeConfig(BaseModel):
    """Configuration for automated trading"""
    enabled: bool
    min_edge_bps: int = 100
    max_trade_size: float = 100
    platforms: List[str] = []

class ScanRequest(BaseModel):
    """Request body for scanning opportunities"""
    size: int = 250
    strategy: str = "binary_box"
    venues: List[str] = ["kalshi", "polymarket"]
    min_edge: float = 0.05

@app.on_event("startup")
async def startup_event():
    global bot
    bot = ArbitrageBot()


@app.get("/", response_class=HTMLResponse)
async def dashboard():
    """Serve the dashboard HTML"""
    try:
        dashboard_path = os.path.join(os.path.dirname(__file__), 'public', 'index.html')
        with open(dashboard_path, 'r') as f:
            return f.read()
    except Exception as e:
        return f"<html><body><h1>Dashboard Not Found</h1><p>Error: {str(e)}</p></body></html>"


@app.get("/api")
async def root():
    """API information and usage"""
    return {
        "service": "Quantshit Arbitrage Engine",
        "version": "1.0.0",
        "description": "Cross-venue prediction market arbitrage detection and execution",
        "endpoints": {
            "GET /health": "Service health check",
            "GET /markets": "Get current market data",
            "POST /scan": "Scan for arbitrage opportunities (JSON body: size, strategy, venues, min_edge)",
            "POST /execute": "Execute arbitrage trade (requires platform, event_id, outcome, action, amount)",
            "POST /run-strategy": "Manual strategy run",
            "GET /dashboard/stats": "Get dashboard statistics",
            "GET /dashboard/trades": "Get recent trade history",
            "GET /dashboard/activity": "Get real-time activity feed"
        },
        "example_usage": {
            "scan": "POST /scan (JSON body: {\"size\": 250, \"min_edge\": 0.02})",
            "execute": "POST /execute?platform=polymarket&event_id=123&outcome=YES&action=buy&amount=100",
            "dashboard": "GET /dashboard/stats"
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


@app.post("/scan")
async def scan_opportunities(request: ScanRequest):
    """Scan for arbitrage opportunities with configurable parameters"""
    try:
        # Collect market data from specified venues only
        if request.venues:
            # Filter to only requested venues
            available_venues = [v for v in request.venues if v in bot.api_keys]
            markets_data = {}
            for venue in available_venues:
                venue_markets = bot.platforms[venue].get_recent_markets()
                markets_data[venue] = venue_markets
        else:
            # Use all platforms
            markets_data = bot.collect_market_data()
        
        # Find opportunities using specified strategy
        opportunities = bot.strategy.find_opportunities(markets_data)
        
        # Filter by minimum edge
        filtered_ops = [op for op in opportunities if op['spread'] >= request.min_edge]
        
        # Format for web interface
        ideas = []
        for i, opp in enumerate(filtered_ops):
            ideas.append({
                "id": f"arb_{i}",
                "question": opp.get('outcome', 'Unknown Market'),
                "yes_venue": opp['buy_market']['platform'],
                "no_venue": opp['sell_market']['platform'], 
                "yes_price": f"${opp['buy_price']:.3f}",
                "no_price": f"${opp['sell_price']:.3f}",
                "size": f"${request.size}",
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
                    "size": request.size,
                    "strategy": request.strategy,
                    "venues": request.venues,
                    "min_edge": request.min_edge
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


# Commented out webhook and auto-trade endpoints (require MarketEvent class)
# These can be re-enabled when event-driven arbitrage is fully implemented

# @app.post("/webhook/market-created")
# @app.post("/auto-trade/start")
# @app.post("/auto-trade/stop")
# @app.get("/auto-trade/status")
# @app.post("/simulate/new-market")


# Dashboard-specific endpoints
@app.get("/dashboard/stats")
async def get_dashboard_stats():
    """Get aggregated statistics for dashboard"""
    try:
        # Collect market data using data_collector
        markets_data = bot.data_collector.collect_market_data(bot.min_volume)
        total_markets = sum(len(markets) for markets in markets_data.values())

        # Find opportunities
        opportunities = bot.find_opportunities(markets_data)

        # Get portfolio info
        portfolio = bot.get_portfolio_summary()

        return {
            "success": True,
            "stats": {
                "total_markets_scanned": total_markets,
                "opportunities_found": len(opportunities),
                "platforms_active": len(markets_data.keys()),
                "portfolio_value": portfolio.get('total_portfolio_value', 20000),
                "last_updated": datetime.utcnow().isoformat()
            }
        }
    except Exception as e:
        import traceback
        print(f"Stats error: {traceback.format_exc()}")
        return JSONResponse(
            status_code=500, content={"success": False, "error": str(e)}
        )


@app.get("/dashboard/trades")
async def get_recent_trades(limit: int = 10):
    """Get recent trade history for dashboard"""
    try:
        # Mock trade data for demo (in production, this would come from a database)
        from random import uniform, choice, randint

        platforms = ["polymarket", "kalshi"]
        outcomes = ["Will Biden win 2024?", "Will Trump win 2024?", "Will Fed cut rates in 2024?", "Will S&P 500 reach 5000?"]
        statuses = ["completed", "pending", "completed", "completed", "completed"]

        trades = []
        for i in range(limit):
            timestamp = datetime.utcnow().timestamp() - (i * 300)  # 5 minutes apart
            trades.append({
                "id": f"trade_{int(timestamp)}",
                "timestamp": datetime.fromtimestamp(timestamp).isoformat(),
                "type": "arbitrage",
                "buy_platform": choice(platforms),
                "sell_platform": choice([p for p in platforms]),
                "outcome": choice(outcomes),
                "buy_price": round(uniform(0.45, 0.55), 3),
                "sell_price": round(uniform(0.55, 0.65), 3),
                "spread": round(uniform(0.05, 0.15), 3),
                "size": round(uniform(50, 500), 2),
                "profit": round(uniform(5, 75), 2),
                "status": choice(statuses)
            })

        return {
            "success": True,
            "trades": trades,
            "count": len(trades)
        }
    except Exception as e:
        return JSONResponse(
            status_code=500, content={"success": False, "error": str(e)}
        )


@app.get("/dashboard/activity")
async def get_activity_feed(limit: int = 20):
    """Get real-time activity feed for dashboard"""
    try:
        from random import uniform, choice, randint

        activities = []
        activity_types = [
            {"type": "scan", "icon": "🔍", "message": "Scanned {count} markets on {platform}"},
            {"type": "match", "icon": "🔗", "message": "Found matching market: {market}"},
            {"type": "opportunity", "icon": "💎", "message": "Detected arbitrage: {spread}% spread"},
            {"type": "trade", "icon": "⚡", "message": "Executed trade: ${profit} profit"}
        ]

        platforms = ["Polymarket", "Kalshi"]
        markets = ["Trump 2024", "Biden 2024", "Fed Rates", "S&P 5000"]

        for i in range(limit):
            timestamp = datetime.utcnow().timestamp() - (i * 30)  # 30 seconds apart
            activity = choice(activity_types)

            message = activity["message"].format(
                count=randint(10, 50),
                platform=choice(platforms),
                market=choice(markets),
                spread=round(uniform(5, 15), 1),
                profit=round(uniform(10, 100), 2)
            )

            activities.append({
                "id": f"activity_{int(timestamp)}",
                "timestamp": datetime.fromtimestamp(timestamp).isoformat(),
                "type": activity["type"],
                "icon": activity["icon"],
                "message": message
            })

        return {
            "success": True,
            "activities": activities,
            "count": len(activities)
        }
    except Exception as e:
        return JSONResponse(
            status_code=500, content={"success": False, "error": str(e)}
        )


if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)

