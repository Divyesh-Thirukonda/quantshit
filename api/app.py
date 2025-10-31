"""
Simplified Vercel deployment entry point for Quantshit Arbitrage Engine
"""

import sys
import os
import logging
from datetime import datetime

# Add the parent directory to the path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from fastapi import FastAPI, HTTPException
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from typing import Dict, Any, Optional
import json

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Create FastAPI app
app = FastAPI(
    title="Quantshit Arbitrage Engine", 
    version="2.0.0",
    description="Cross-venue arbitrage trading system for prediction markets"
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Import our trading system with error handling
try:
    from src.main import ArbitrageBot
    SYSTEM_AVAILABLE = True
    logger.info("Trading system successfully imported")
except ImportError as e:
    logger.warning(f"Trading system import failed: {e}")
    SYSTEM_AVAILABLE = False

# Global bot instance (will be created per request in serverless)
bot = None

@app.get("/")
async def root():
    """API root endpoint with status information"""
    return {
        "message": "Quantshit Arbitrage Engine API",
        "version": "2.0.0",
        "status": "healthy",
        "system_available": SYSTEM_AVAILABLE,
        "timestamp": datetime.now().isoformat(),
        "endpoints": {
            "health": "/health",
            "scan": "/scan",
            "markets": "/markets",
            "system_status": "/status",
            "backtest": "/backtest",
            "backtest_viz": "/backtest/visualizations",
            "projections": "/backtest/projections"
        }
    }

@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "timestamp": datetime.now().isoformat(),
        "system_imports": SYSTEM_AVAILABLE
    }

@app.get("/status")
async def system_status():
    """Get system status and configuration"""
    try:
        # Get environment variables
        env_vars = {
            "POLYMARKET_API_KEY": "SET" if os.getenv("POLYMARKET_API_KEY") else "MISSING",
            "KALSHI_API_KEY": "SET" if os.getenv("KALSHI_API_KEY") else "MISSING",
        }

        # Trading parameters are now in strategy config, not env vars
        note = "Trading parameters (min_volume, min_spread) are now configured per-strategy in code"
        
        return {
            "status": "operational",
            "system_available": SYSTEM_AVAILABLE,
            "environment": env_vars,
            "note": note,
            "timestamp": datetime.now().isoformat()
        }
    except Exception as e:
        logger.error(f"Status check failed: {e}")
        raise HTTPException(status_code=500, detail=f"Status check failed: {str(e)}")

@app.get("/scan")
async def scan_opportunities(size: Optional[int] = 250, min_edge: Optional[float] = 0.05):
    """Scan for arbitrage opportunities"""
    if not SYSTEM_AVAILABLE:
        return {
            "success": False,
            "error": "Trading system not available",
            "opportunities": [],
            "timestamp": datetime.now().isoformat()
        }

    try:
        # Initialize bot for this request (serverless)
        bot = ArbitrageBot()

        # Fetch markets
        kalshi_markets, polymarket_markets = bot._fetch_markets()

        # Find matches and score opportunities
        matched_pairs = bot.matcher.find_matches(kalshi_markets, polymarket_markets)
        opportunities = bot.scorer.score_opportunities(matched_pairs)

        # Filter by min_edge
        filtered_ops = [op for op in opportunities if op.expected_profit_pct >= min_edge]

        # Format for API response
        formatted_ops = []
        for i, opp in enumerate(filtered_ops[:20]):  # Limit to 20
            formatted_ops.append({
                "id": f"arb_{i}",
                "outcome": opp.outcome.value,
                "market_title": opp.market_kalshi.title[:60],
                "kalshi_price": opp.kalshi_price,
                "polymarket_price": opp.polymarket_price,
                "spread": opp.expected_profit_pct,
                "expected_profit": opp.expected_profit
            })

        return {
            "success": True,
            "opportunities": formatted_ops,
            "parameters": {
                "size": size,
                "min_edge": min_edge
            },
            "meta": {
                "markets_scanned": len(kalshi_markets) + len(polymarket_markets),
                "matched_pairs": len(matched_pairs),
                "opportunities_found": len(filtered_ops)
            },
            "timestamp": datetime.now().isoformat()
        }

    except Exception as e:
        logger.error(f"Scan failed: {e}")
        import traceback
        logger.error(traceback.format_exc())
        return {
            "success": False,
            "error": str(e),
            "opportunities": [],
            "timestamp": datetime.now().isoformat()
        }

@app.get("/markets")
async def get_markets():
    """Get current market data from all platforms"""
    if not SYSTEM_AVAILABLE:
        return {
            "success": False,
            "error": "Trading system not available",
            "markets": {}
        }

    try:
        # Initialize bot for this request
        bot = ArbitrageBot()

        # Fetch markets
        kalshi_markets, polymarket_markets = bot._fetch_markets()

        markets_data = {
            "kalshi": {
                "status": "connected",
                "market_count": len(kalshi_markets),
                "markets": [
                    {
                        "id": m.market_id,
                        "title": m.title,
                        "yes_price": m.yes_price,
                        "no_price": m.no_price,
                        "volume": m.volume
                    } for m in kalshi_markets[:5]
                ]
            },
            "polymarket": {
                "status": "connected",
                "market_count": len(polymarket_markets),
                "markets": [
                    {
                        "id": m.market_id,
                        "title": m.title,
                        "yes_price": m.yes_price,
                        "no_price": m.no_price,
                        "volume": m.volume
                    } for m in polymarket_markets[:5]
                ]
            }
        }

        return {
            "success": True,
            "markets": markets_data,
            "timestamp": datetime.now().isoformat()
        }

    except Exception as e:
        logger.error(f"Markets fetch failed: {e}")
        import traceback
        logger.error(traceback.format_exc())
        return {
            "success": False,
            "error": str(e),
            "markets": {}
        }

# Health check for Vercel
@app.get("/api/health")
async def api_health():
    """Vercel-specific health check"""
    return await health_check()

@app.get("/backtest")
async def run_backtest(
    min_spread: Optional[float] = 0.05,
    min_volume: Optional[float] = 1000000,
    max_trades_per_day: Optional[int] = 3,
    trade_amount: Optional[float] = 1000
):
    """Run backtest on historical demo data"""
    try:
        # Import backtesting modules
        import sys
        from pathlib import Path

        # Add demo directory to path
        demo_path = Path(__file__).parent.parent / "demo"
        sys.path.insert(0, str(demo_path))

        from backtester import Backtester

        # Run backtest
        backtester = Backtester(
            min_spread=min_spread,
            min_volume=min_volume,
            max_trades_per_day=max_trades_per_day,
            trade_amount=trade_amount
        )

        result = backtester.run_backtest()

        # Get projections
        projection = backtester.project_returns(result, days_forward=30)

        return {
            "success": True,
            "backtest": result.to_dict(),
            "projections": projection,
            "parameters": {
                "min_spread": min_spread,
                "min_volume": min_volume,
                "max_trades_per_day": max_trades_per_day,
                "trade_amount": trade_amount
            },
            "timestamp": datetime.now().isoformat()
        }

    except Exception as e:
        logger.error(f"Backtest failed: {e}")
        import traceback
        logger.error(traceback.format_exc())
        return {
            "success": False,
            "error": str(e),
            "timestamp": datetime.now().isoformat()
        }

@app.get("/backtest/visualizations")
async def get_backtest_visualizations(
    min_spread: Optional[float] = 0.05,
    min_volume: Optional[float] = 1000000,
    max_trades_per_day: Optional[int] = 3,
    trade_amount: Optional[float] = 1000
):
    """Get backtest visualizations as base64-encoded images"""
    try:
        # Import backtesting and visualization modules
        import sys
        from pathlib import Path

        # Add demo directory to path
        demo_path = Path(__file__).parent.parent / "demo"
        sys.path.insert(0, str(demo_path))

        from backtester import Backtester
        from visualizer import BacktestVisualizer

        # Run backtest
        backtester = Backtester(
            min_spread=min_spread,
            min_volume=min_volume,
            max_trades_per_day=max_trades_per_day,
            trade_amount=trade_amount
        )

        result = backtester.run_backtest()

        # Generate visualizations
        visualizer = BacktestVisualizer(result)
        plots = visualizer.generate_all_plots()

        return {
            "success": True,
            "plots": plots,
            "summary": result.to_dict()["summary"],
            "timestamp": datetime.now().isoformat()
        }

    except Exception as e:
        logger.error(f"Visualization generation failed: {e}")
        import traceback
        logger.error(traceback.format_exc())
        return {
            "success": False,
            "error": str(e),
            "timestamp": datetime.now().isoformat()
        }

@app.get("/backtest/projections")
async def get_projections(
    days_forward: Optional[int] = 30,
    min_spread: Optional[float] = 0.05,
    min_volume: Optional[float] = 1000000,
    max_trades_per_day: Optional[int] = 3,
    trade_amount: Optional[float] = 1000
):
    """Get projected returns based on historical backtest"""
    try:
        # Import backtesting modules
        import sys
        from pathlib import Path

        # Add demo directory to path
        demo_path = Path(__file__).parent.parent / "demo"
        sys.path.insert(0, str(demo_path))

        from backtester import Backtester

        # Run backtest
        backtester = Backtester(
            min_spread=min_spread,
            min_volume=min_volume,
            max_trades_per_day=max_trades_per_day,
            trade_amount=trade_amount
        )

        result = backtester.run_backtest()

        # Get projections
        projection = backtester.project_returns(result, days_forward=days_forward)

        return {
            "success": True,
            "projections": projection,
            "historical_performance": result.to_dict()["summary"],
            "parameters": {
                "days_forward": days_forward,
                "min_spread": min_spread,
                "min_volume": min_volume,
                "max_trades_per_day": max_trades_per_day,
                "trade_amount": trade_amount
            },
            "timestamp": datetime.now().isoformat()
        }

    except Exception as e:
        logger.error(f"Projections failed: {e}")
        import traceback
        logger.error(traceback.format_exc())
        return {
            "success": False,
            "error": str(e),
            "timestamp": datetime.now().isoformat()
        }

# Vercel entry point
app = app

# For local development
if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)