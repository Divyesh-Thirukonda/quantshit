from fastapi import FastAPI, Query
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
import uvicorn
from typing import Optional
from main import ArbitrageBot
from position_tracker import PositionTracker

app = FastAPI(
    title="Prediction Market Trading Bot API", 
    version="2.0.0",
    description="REST API for prediction market arbitrage and expiry trading bot"
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Global bot instance
bot = None
position_tracker = None

@app.on_event("startup")
async def startup_event():
    global bot, position_tracker
    bot = ArbitrageBot()
    position_tracker = PositionTracker()

@app.get("/")
async def root():
    return {
        "message": "Prediction Market Trading Bot API", 
        "version": "2.0.0",
        "docs": "/docs"
    }

@app.get("/health")
async def health_check():
    from datetime import datetime
    return {
        "status": "healthy", 
        "timestamp": datetime.now().isoformat(),
        "strategies": list(bot.strategies.keys()) if bot else [],
        "platforms": list(bot.api_keys.keys()) if bot else []
    }

# STRATEGY ENDPOINTS
@app.post("/strategy/run")
async def run_strategy():
    """Manually trigger a strategy run"""
    try:
        bot.run_strategy_cycle()
        return {"success": True, "message": "Strategy cycle completed"}
    except Exception as e:
        return JSONResponse(
            status_code=500,
            content={"success": False, "error": str(e)}
        )

@app.get("/strategy/opportunities")
async def get_current_opportunities():
    """Get current trading opportunities without executing trades"""
    try:
        markets_data = bot.collect_market_data()
        
        all_opportunities = []
        for strategy_name, strategy in bot.strategies.items():
            opportunities = strategy.find_opportunities(markets_data)
            for opp in opportunities:
                opp['strategy'] = strategy_name
            all_opportunities.extend(opportunities)
        
        # Sort by expected profit
        all_opportunities.sort(key=lambda x: x.get('expected_profit', 0), reverse=True)
        
        return {
            "success": True, 
            "opportunities": all_opportunities,
            "total_count": len(all_opportunities)
        }
    except Exception as e:
        return JSONResponse(
            status_code=500,
            content={"success": False, "error": str(e)}
        )

# MARKET DATA ENDPOINTS
@app.get("/markets")
async def get_markets():
    """Get current market data"""
    try:
        markets_data = bot.collect_market_data()
        
        # Count markets by platform
        market_counts = {platform: len(markets) for platform, markets in markets_data.items()}
        total_markets = sum(market_counts.values())
        
        return {
            "success": True, 
            "data": markets_data,
            "summary": {
                "total_markets": total_markets,
                "by_platform": market_counts
            }
        }
    except Exception as e:
        return JSONResponse(
            status_code=500,
            content={"success": False, "error": str(e)}
        )

# POSITION TRACKING ENDPOINTS
@app.get("/positions")
async def get_open_positions():
    """Get all open trading positions"""
    try:
        positions = position_tracker.get_open_positions()
        return {
            "success": True,
            "positions": positions,
            "count": len(positions)
        }
    except Exception as e:
        return JSONResponse(
            status_code=500,
            content={"success": False, "error": str(e)}
        )

@app.get("/positions/summary")
async def get_portfolio_summary():
    """Get portfolio summary with P&L statistics"""
    try:
        summary = position_tracker.get_portfolio_summary()
        return {
            "success": True,
            "summary": summary
        }
    except Exception as e:
        return JSONResponse(
            status_code=500,
            content={"success": False, "error": str(e)}
        )

@app.get("/trades")
async def get_trade_history(
    limit: Optional[int] = Query(None, description="Maximum number of trades to return"),
    strategy: Optional[str] = Query(None, description="Filter by strategy name"),
    platform: Optional[str] = Query(None, description="Filter by platform")
):
    """Get trade history with optional filters"""
    try:
        trades = position_tracker.get_trade_history(limit)
        
        # Apply filters
        if strategy:
            trades = [t for t in trades if t.get('strategy') == strategy]
        if platform:
            trades = [t for t in trades if t.get('platform') == platform]
        
        return {
            "success": True,
            "trades": trades,
            "count": len(trades),
            "filters": {
                "limit": limit,
                "strategy": strategy,
                "platform": platform
            }
        }
    except Exception as e:
        return JSONResponse(
            status_code=500,
            content={"success": False, "error": str(e)}
        )

@app.post("/positions/update-prices")
async def update_position_prices():
    """Update current market prices for all open positions"""
    try:
        # Get current market data
        markets_data = bot.collect_market_data()
        
        # Convert to price dict format
        market_prices = {}
        for platform_markets in markets_data.values():
            for market in platform_markets:
                market_prices[market['id']] = {
                    'yes_price': market.get('yes_price', 0.5),
                    'no_price': market.get('no_price', 0.5)
                }
        
        # Update position tracker
        position_tracker.update_market_prices(market_prices)
        
        return {
            "success": True,
            "message": f"Updated prices for {len(market_prices)} markets"
        }
    except Exception as e:
        return JSONResponse(
            status_code=500,
            content={"success": False, "error": str(e)}
        )

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)