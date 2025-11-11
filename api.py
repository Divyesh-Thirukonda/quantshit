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
from concurrent.futures import ThreadPoolExecutor

from src.main import ArbitrageBot

app = FastAPI(
    title="Quantshit Arbitrage Engine",
    version="1.0.0",
    description="Cross-venue prediction market arbitrage detection and execution API"
)

# Global instances
bot = None
executor = ThreadPoolExecutor(max_workers=4)  # Thread pool for blocking operations

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
    return {"status": "healthy", "timestamp": datetime.utcnow().isoformat()}


@app.post("/run-strategy")
async def run_strategy():
    """Manually trigger a strategy run"""
    try:
        loop = asyncio.get_event_loop()
        await loop.run_in_executor(executor, bot.run_cycle)
        return {"success": True, "message": "Strategy cycle completed"}
    except Exception as e:
        return JSONResponse(
            status_code=500, content={"success": False, "error": str(e)}
        )


@app.get("/markets")
async def get_markets():
    """Get current market data"""
    try:
        # Fetch markets from both exchanges (non-blocking)
        loop = asyncio.get_event_loop()
        kalshi_markets, polymarket_markets = await loop.run_in_executor(executor, bot.fetch_markets)

        markets_data = {
            "kalshi": [
                {
                    "id": m.market_id,
                    "title": m.title,
                    "yes_price": m.yes_price,
                    "no_price": m.no_price,
                    "volume": m.volume
                } for m in kalshi_markets[:10]  # Limit to 10 for API
            ],
            "polymarket": [
                {
                    "id": m.market_id,
                    "title": m.title,
                    "yes_price": m.yes_price,
                    "no_price": m.no_price,
                    "volume": m.volume
                } for m in polymarket_markets[:10]  # Limit to 10 for API
            ]
        }

        return {"success": True, "data": markets_data}
    except Exception as e:
        return JSONResponse(
            status_code=500, content={"success": False, "error": str(e)}
        )


@app.post("/scan")
async def scan_opportunities(request: ScanRequest):
    """Scan for arbitrage opportunities with configurable parameters"""
    try:
        # Fetch markets from exchanges (non-blocking)
        loop = asyncio.get_event_loop()
        kalshi_markets, polymarket_markets = await loop.run_in_executor(executor, bot.fetch_markets)

        # Filter by requested venues if specified
        if request.venues:
            if "kalshi" not in request.venues:
                kalshi_markets = []
            if "polymarket" not in request.venues:
                polymarket_markets = []

        # Find matching markets (non-blocking)
        matched_pairs = await loop.run_in_executor(
            executor, bot.matcher.find_matches, kalshi_markets, polymarket_markets
        )

        # Score opportunities (non-blocking)
        opportunities = await loop.run_in_executor(
            executor, bot.scorer.score_opportunities, matched_pairs
        )

        # Filter by minimum edge
        filtered_ops = [op for op in opportunities if op.expected_profit_pct >= request.min_edge]

        # Format for web interface
        ideas = []
        for i, opp in enumerate(filtered_ops):
            ideas.append({
                "id": f"arb_{i}",
                "question": opp.outcome.value,
                "market_title": opp.market_kalshi.title[:60],
                "kalshi_price": f"${opp.kalshi_price:.3f}",
                "polymarket_price": f"${opp.polymarket_price:.3f}",
                "size": f"${request.size}",
                "edge_bps": f"{int(opp.expected_profit_pct * 10000)}",
                "spread": f"{opp.expected_profit_pct:.2%}",
                "profit": f"${opp.expected_profit:.2f}"
            })

        return {
            "success": True,
            "opportunities": ideas,
            "meta": {
                "scanned_markets": len(kalshi_markets) + len(polymarket_markets),
                "matched_pairs": len(matched_pairs),
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
        import traceback
        return JSONResponse(
            status_code=500, content={"error": str(e), "traceback": traceback.format_exc()}
        )


@app.get("/search")
async def search_events(keyword: str, platforms: str = None, limit: int = 10):
    """Search for events across platforms"""
    try:
        # Fetch all markets (non-blocking)
        loop = asyncio.get_event_loop()
        kalshi_markets, polymarket_markets = await loop.run_in_executor(executor, bot.fetch_markets)

        # Filter by keyword (case-insensitive)
        keyword_lower = keyword.lower()
        results = []

        # Search in Kalshi markets
        if not platforms or "kalshi" in platforms:
            for market in kalshi_markets:
                if keyword_lower in market.title.lower():
                    results.append({
                        "platform": "kalshi",
                        "id": market.market_id,
                        "title": market.title,
                        "yes_price": market.yes_price,
                        "no_price": market.no_price,
                        "volume": market.volume
                    })

        # Search in Polymarket markets
        if not platforms or "polymarket" in platforms:
            for market in polymarket_markets:
                if keyword_lower in market.title.lower():
                    results.append({
                        "platform": "polymarket",
                        "id": market.market_id,
                        "title": market.title,
                        "yes_price": market.yes_price,
                        "no_price": market.no_price,
                        "volume": market.volume
                    })

        # Limit results
        results = results[:limit]

        return {"success": True, "results": results, "count": len(results)}
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
        # Note: This endpoint is for manual trades, not arbitrage
        # Direct execution would require extending the bot with a manual trade method
        # For now, return a not implemented message
        return {
            "success": False,
            "error": "Manual trade execution not yet implemented",
            "message": "Use /run-strategy to execute arbitrage opportunities"
        }
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
        # Fetch markets from both exchanges (non-blocking)
        loop = asyncio.get_event_loop()
        kalshi_markets, polymarket_markets = await loop.run_in_executor(executor, bot.fetch_markets)
        total_markets = len(kalshi_markets) + len(polymarket_markets)

        # Find matching markets and score opportunities (non-blocking)
        matched_pairs = await loop.run_in_executor(
            executor, bot.matcher.find_matches, kalshi_markets, polymarket_markets
        )
        opportunities = await loop.run_in_executor(
            executor, bot.scorer.score_opportunities, matched_pairs
        )

        # Get repository stats
        stats = bot.repository.get_stats()

        # Get tracker summary
        tracker_summary = bot.tracker.get_summary()

        return {
            "success": True,
            "stats": {
                "total_markets_scanned": total_markets,
                "opportunities_found": len(opportunities),
                "platforms_active": 2,  # Kalshi + Polymarket
                "total_trades": stats.get('total_trades', 0),
                "total_cycles": bot.cycle_count,
                "unrealized_pnl": tracker_summary.get('total_unrealized_pnl', 0),
                "realized_pnl": tracker_summary.get('total_realized_pnl', 0),
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
        # Get orders from repository
        orders = bot.repository.get_orders()

        # Format orders for dashboard
        trades = []
        for order in orders[:limit]:
            trades.append({
                "id": order.order_id,
                "timestamp": order.timestamp.isoformat() if hasattr(order.timestamp, 'isoformat') else str(order.timestamp),
                "type": "arbitrage",
                "platform": order.exchange.value,
                "market_id": order.market_id,
                "side": order.side.value,
                "quantity": order.quantity,
                "price": order.price,
                "status": order.status.value
            })

        # If no real trades, return empty list instead of mock data
        return {
            "success": True,
            "trades": trades,
            "count": len(trades)
        }
    except Exception as e:
        import traceback
        print(f"Trades error: {traceback.format_exc()}")
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
            "count": len(activities),
            "is_mock_data": True,
            "message": "Demo data - real activity feed not yet implemented"
        }
    except Exception as e:
        return JSONResponse(
            status_code=500, content={"success": False, "error": str(e)}
        )


if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)

