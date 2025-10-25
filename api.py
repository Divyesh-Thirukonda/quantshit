"""
Quantshit Arbitrage Engine API

Clean API-only interface for cross-venue prediction market arbitrage.
No frontend - designed to be called by external applications.
"""

import uvicorn
from fastapi import FastAPI, BackgroundTasks
from fastapi.responses import JSONResponse
from datetime import datetime
from typing import Dict, List, Optional
import asyncio
from pydantic import BaseModel

from src.engine.bot import ArbitrageBot

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
            "POST /scan": "Scan for arbitrage opportunities (JSON body: size, strategy, venues, min_edge)",
            "POST /execute": "Execute arbitrage trade (requires platform, event_id, outcome, action, amount)",
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


@app.post("/webhook/market-created")
async def market_created_webhook(payload: WebhookPayload, background_tasks: BackgroundTasks):
    """Webhook endpoint for new market creation events"""
    try:
        # Convert webhook payload to MarketEvent
        market_event = MarketEvent(
            platform=payload.platform,
            event_id=payload.event_id,
            title=payload.title,
            yes_price=payload.yes_price,
            no_price=payload.no_price,
            volume=payload.volume,
            liquidity=payload.liquidity,
            created_at=datetime.now(),
            tags=event_arbitrage._extract_tags(payload.title)
        )
        
        # Process in background to return quickly
        background_tasks.add_task(process_new_market_event, market_event)
        
        return {"success": True, "message": "Market event received and processing"}
    except Exception as e:
        return JSONResponse(
            status_code=500, content={"success": False, "error": str(e)}
        )


@app.post("/auto-trade/start")
async def start_auto_trading(config: AutoTradeConfig, background_tasks: BackgroundTasks):
    """Start automated event-driven trading"""
    try:
        if config.enabled:
            # Update configuration
            event_arbitrage.min_edge_bps = config.min_edge_bps
            event_arbitrage.max_trade_size = config.max_trade_size
            
            # Start monitoring in background
            background_tasks.add_task(start_event_monitoring)
            
            return {
                "success": True, 
                "message": "Auto-trading started",
                "config": {
                    "min_edge_bps": config.min_edge_bps,
                    "max_trade_size": config.max_trade_size,
                    "platforms": list(bot.api_keys.keys())
                }
            }
        else:
            return {"success": True, "message": "Auto-trading disabled"}
    except Exception as e:
        return JSONResponse(
            status_code=500, content={"success": False, "error": str(e)}
        )


@app.post("/auto-trade/stop")
async def stop_auto_trading():
    """Stop automated trading"""
    try:
        await event_arbitrage._stop_all_listeners()
        return {"success": True, "message": "Auto-trading stopped"}
    except Exception as e:
        return JSONResponse(
            status_code=500, content={"success": False, "error": str(e)}
        )


@app.get("/auto-trade/status")
async def get_auto_trade_status():
    """Get current auto-trading status"""
    try:
        return {
            "success": True,
            "status": {
                "active_listeners": len(event_arbitrage.active_listeners),
                "platforms": list(event_arbitrage.active_listeners.keys()),
                "executed_pairs": len(event_arbitrage.executed_pairs),
                "min_edge_bps": event_arbitrage.min_edge_bps,
                "max_trade_size": event_arbitrage.max_trade_size
            }
        }
    except Exception as e:
        return JSONResponse(
            status_code=500, content={"success": False, "error": str(e)}
        )


@app.post("/simulate/new-market")
async def simulate_new_market(title: str, yes_price: float, platform: str = "polymarket"):
    """Simulate a new market for testing event-driven arbitrage"""
    try:
        # Create a simulated market event
        market_event = MarketEvent(
            platform=platform,
            event_id=f"sim_{int(datetime.now().timestamp())}",
            title=title,
            yes_price=yes_price,
            no_price=1.0 - yes_price,
            volume=10000,
            liquidity=5000,
            created_at=datetime.now()
        )
        
        # Process immediately
        await event_arbitrage._handle_new_market_event(market_event)
        
        return {
            "success": True,
            "message": "Simulated market processed",
            "market": {
                "id": market_event.event_id,
                "title": market_event.title,
                "platform": market_event.platform,
                "yes_price": market_event.yes_price
            }
        }
    except Exception as e:
        return JSONResponse(
            status_code=500, content={"success": False, "error": str(e)}
        )


async def process_new_market_event(market_event: MarketEvent):
    """Background task to process new market events"""
    try:
        await event_arbitrage._handle_new_market_event(market_event)
    except Exception as e:
        print(f"Error processing market event: {e}")


async def start_event_monitoring():
    """Background task to start event-driven monitoring"""
    try:
        await event_arbitrage.start_real_time_monitoring()
    except Exception as e:
        print(f"Error in event monitoring: {e}")


if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)

