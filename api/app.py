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

# ==================== TRADING PIPELINE ENDPOINTS ====================
# These endpoints form the complete trading pipeline that can be called
# sequentially by cron jobs or manually for testing

@app.post("/pipeline/scan-markets")
async def pipeline_scan_markets():
    """
    Step 1: Scan and match markets between platforms
    This endpoint fetches all markets, finds matches, and stores them in database
    """
    if not SYSTEM_AVAILABLE:
        return {
            "success": False,
            "error": "Trading system not available",
            "timestamp": datetime.now().isoformat()
        }

    try:
        # Initialize bot
        bot = ArbitrageBot()
        
        # Fetch markets from both platforms
        logger.info("Fetching markets from Kalshi and Polymarket...")
        kalshi_markets, polymarket_markets = bot._fetch_markets()
        
        # Find matches between platforms
        logger.info("Finding market matches...")
        matched_pairs = bot.matcher.find_matches(kalshi_markets, polymarket_markets)
        
        # TODO: Store markets and matches in database
        # For now, return summary
        
        result = {
            "success": True,
            "summary": {
                "kalshi_markets": len(kalshi_markets),
                "polymarket_markets": len(polymarket_markets),
                "total_matches": len(matched_pairs),
                "high_confidence_matches": len([m for m in matched_pairs if m.similarity_score > 0.8])
            },
            "matches": [
                {
                    "kalshi_title": match.market_kalshi.title[:60],
                    "polymarket_title": match.market_polymarket.title[:60],
                    "similarity_score": match.similarity_score,
                    "confidence": "high" if match.similarity_score > 0.8 else "medium" if match.similarity_score > 0.6 else "low"
                }
                for match in matched_pairs[:10]  # Show top 10 matches
            ],
            "next_step": "Call /pipeline/detect-opportunities to find arbitrage opportunities",
            "timestamp": datetime.now().isoformat()
        }
        
        logger.info(f"Market scan complete: {len(matched_pairs)} matches found")
        return result
        
    except Exception as e:
        logger.error(f"Market scan failed: {e}")
        return {
            "success": False,
            "error": str(e),
            "timestamp": datetime.now().isoformat()
        }

@app.post("/pipeline/detect-opportunities")
async def pipeline_detect_opportunities(min_spread: float = 0.02, max_opportunities: int = 50):
    """
    Step 2: Detect arbitrage opportunities from matched markets
    This finds profitable spreads and stores opportunities in database
    """
    if not SYSTEM_AVAILABLE:
        return {
            "success": False,
            "error": "Trading system not available",
            "timestamp": datetime.now().isoformat()
        }

    try:
        # Initialize bot
        bot = ArbitrageBot()
        
        # Fetch markets and find matches (in production, this would read from DB)
        logger.info("Fetching markets and finding opportunities...")
        kalshi_markets, polymarket_markets = bot._fetch_markets()
        matched_pairs = bot.matcher.find_matches(kalshi_markets, polymarket_markets)
        
        # Score opportunities
        opportunities = bot.scorer.score_opportunities(matched_pairs)
        
        # Filter by minimum spread
        filtered_opportunities = [
            opp for opp in opportunities 
            if opp.expected_profit_pct >= min_spread
        ]
        
        # Sort by profitability
        filtered_opportunities.sort(key=lambda x: x.expected_profit_pct, reverse=True)
        
        # Limit results
        top_opportunities = filtered_opportunities[:max_opportunities]
        
        # TODO: Store opportunities in database
        
        # Format for response
        formatted_opportunities = []
        for i, opp in enumerate(top_opportunities):
            formatted_opportunities.append({
                "id": f"opp_{i}",
                "market_pair": {
                    "kalshi": opp.market_kalshi.title[:60],
                    "polymarket": opp.market_polymarket.title[:60]
                },
                "outcome": opp.outcome.value,
                "prices": {
                    "kalshi": opp.kalshi_price,
                    "polymarket": opp.polymarket_price
                },
                "spread": {
                    "absolute": opp.kalshi_price - opp.polymarket_price if opp.kalshi_price > opp.polymarket_price else opp.polymarket_price - opp.kalshi_price,
                    "percentage": opp.expected_profit_pct
                },
                "expected_profit": opp.expected_profit,
                "risk_level": "low" if opp.expected_profit_pct > 0.05 else "medium" if opp.expected_profit_pct > 0.03 else "high"
            })
        
        result = {
            "success": True,
            "summary": {
                "total_opportunities": len(opportunities),
                "filtered_opportunities": len(filtered_opportunities),
                "top_opportunities": len(top_opportunities),
                "best_spread": max([opp.expected_profit_pct for opp in top_opportunities]) if top_opportunities else 0,
                "average_spread": sum([opp.expected_profit_pct for opp in top_opportunities]) / len(top_opportunities) if top_opportunities else 0
            },
            "opportunities": formatted_opportunities,
            "parameters": {
                "min_spread": min_spread,
                "max_opportunities": max_opportunities
            },
            "next_step": "Call /pipeline/portfolio-management to optimize positions",
            "timestamp": datetime.now().isoformat()
        }
        
        logger.info(f"Opportunity detection complete: {len(top_opportunities)} opportunities found")
        return result
        
    except Exception as e:
        logger.error(f"Opportunity detection failed: {e}")
        return {
            "success": False,
            "error": str(e),
            "timestamp": datetime.now().isoformat()
        }

@app.post("/pipeline/portfolio-management")
async def pipeline_portfolio_management(max_position_size: float = 1000, max_total_exposure: float = 10000):
    """
    Step 3: Portfolio management - optimize positions and risk
    This determines position sizes and manages overall portfolio risk
    """
    try:
        # TODO: In production, this would read current positions from database
        # For now, simulate portfolio management logic
        
        # Mock current portfolio state
        current_portfolio = {
            "total_value": 10000,
            "cash_balance": 8500,
            "positions_value": 1500,
            "unrealized_pnl": 150,
            "realized_pnl": 75,
            "active_positions": 3,
            "daily_pnl": 25
        }
        
        # Mock position recommendations
        position_recommendations = [
            {
                "opportunity_id": "opp_0",
                "action": "open_position",
                "recommended_size": min(max_position_size, 500),
                "reasoning": "High confidence opportunity with good liquidity",
                "risk_score": 0.2
            },
            {
                "opportunity_id": "opp_1", 
                "action": "open_position",
                "recommended_size": min(max_position_size, 750),
                "reasoning": "Medium risk, high reward opportunity",
                "risk_score": 0.4
            }
        ]
        
        # Calculate portfolio metrics
        total_recommended_exposure = sum([rec["recommended_size"] for rec in position_recommendations])
        remaining_capacity = max_total_exposure - current_portfolio["positions_value"]
        
        result = {
            "success": True,
            "portfolio_status": current_portfolio,
            "recommendations": position_recommendations,
            "risk_analysis": {
                "current_exposure": current_portfolio["positions_value"],
                "recommended_additional_exposure": total_recommended_exposure,
                "remaining_capacity": remaining_capacity,
                "utilization_percentage": (current_portfolio["positions_value"] / max_total_exposure) * 100,
                "risk_level": "low" if remaining_capacity > 5000 else "medium" if remaining_capacity > 2000 else "high"
            },
            "parameters": {
                "max_position_size": max_position_size,
                "max_total_exposure": max_total_exposure
            },
            "next_step": "Call /pipeline/execute-trades to execute recommended positions",
            "timestamp": datetime.now().isoformat()
        }
        
        logger.info(f"Portfolio management complete: {len(position_recommendations)} recommendations")
        return result
        
    except Exception as e:
        logger.error(f"Portfolio management failed: {e}")
        return {
            "success": False,
            "error": str(e),
            "timestamp": datetime.now().isoformat()
        }

@app.post("/pipeline/execute-trades")
async def pipeline_execute_trades(paper_trading: bool = True):
    """
    Step 4: Execute trades based on portfolio recommendations
    This executes the actual trades (paper trading by default)
    """
    try:
        # TODO: In production, this would read recommendations from database
        # and execute actual trades on platforms
        
        if paper_trading:
            # Simulate trade execution
            executed_trades = [
                {
                    "trade_id": "trade_001",
                    "opportunity_id": "opp_0",
                    "platform": "kalshi",
                    "action": "buy",
                    "outcome": "yes",
                    "quantity": 500,
                    "price": 0.45,
                    "status": "filled",
                    "timestamp": datetime.now().isoformat()
                },
                {
                    "trade_id": "trade_002", 
                    "opportunity_id": "opp_0",
                    "platform": "polymarket",
                    "action": "sell",
                    "outcome": "yes",
                    "quantity": 500,
                    "price": 0.52,
                    "status": "filled",
                    "timestamp": datetime.now().isoformat()
                }
            ]
            
            execution_summary = {
                "total_trades": len(executed_trades),
                "successful_trades": len([t for t in executed_trades if t["status"] == "filled"]),
                "failed_trades": 0,
                "total_volume": sum([t["quantity"] * t["price"] for t in executed_trades]),
                "expected_profit": 35.0  # Mock calculation
            }
        else:
            # Would execute real trades here
            executed_trades = []
            execution_summary = {
                "message": "Real trading not implemented yet - use paper_trading=true"
            }
        
        result = {
            "success": True,
            "trading_mode": "paper" if paper_trading else "live",
            "execution_summary": execution_summary,
            "executed_trades": executed_trades,
            "next_step": "Monitor positions and repeat pipeline as needed",
            "timestamp": datetime.now().isoformat()
        }
        
        logger.info(f"Trade execution complete: {len(executed_trades)} trades executed")
        return result
        
    except Exception as e:
        logger.error(f"Trade execution failed: {e}")
        return {
            "success": False,
            "error": str(e),
            "timestamp": datetime.now().isoformat()
        }

# ==================== FRONTEND DASHBOARD ENDPOINTS ====================
# These endpoints provide data for the frontend dashboard

@app.get("/dashboard/overview")
async def dashboard_overview():
    """Get overview data for dashboard"""
    try:
        # TODO: Get real data from database
        # Mock data for now
        overview = {
            "portfolio": {
                "total_value": 10150.00,
                "daily_pnl": 150.00,
                "daily_pnl_percentage": 1.5,
                "unrealized_pnl": 75.00,
                "realized_pnl": 225.00,
                "cash_balance": 8500.00,
                "positions_value": 1650.00
            },
            "trading_stats": {
                "active_opportunities": 23,
                "active_positions": 5,
                "total_trades_today": 8,
                "win_rate": 0.75,
                "best_spread_today": 0.089,
                "average_spread": 0.034
            },
            "system_status": {
                "last_scan": "2025-11-03T10:30:00Z",
                "markets_monitored": 247,
                "system_health": "healthy",
                "api_connections": {
                    "kalshi": "connected",
                    "polymarket": "connected"
                }
            }
        }
        
        return {
            "success": True,
            "data": overview,
            "timestamp": datetime.now().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Dashboard overview failed: {e}")
        return {
            "success": False,
            "error": str(e),
            "timestamp": datetime.now().isoformat()
        }

@app.get("/dashboard/opportunities")
async def dashboard_opportunities(limit: int = 20):
    """Get current arbitrage opportunities for dashboard"""
    try:
        # TODO: Get real data from database
        # Mock data for now
        opportunities = [
            {
                "id": "opp_1",
                "market_title": "Bitcoin above $50,000 on Dec 31, 2024",
                "outcome": "yes",
                "platforms": "Kalshi → Polymarket",
                "buy_price": 0.45,
                "sell_price": 0.52,
                "spread_percentage": 15.6,
                "expected_profit": 35.00,
                "confidence": "high",
                "risk_level": "medium",
                "volume": 1250,
                "last_updated": "2025-11-03T10:25:00Z"
            },
            {
                "id": "opp_2",
                "market_title": "Trump wins 2024 election",
                "outcome": "yes", 
                "platforms": "Polymarket → Kalshi",
                "buy_price": 0.58,
                "sell_price": 0.63,
                "spread_percentage": 8.6,
                "expected_profit": 25.00,
                "confidence": "high",
                "risk_level": "low",
                "volume": 2100,
                "last_updated": "2025-11-03T10:23:00Z"
            }
        ]
        
        return {
            "success": True,
            "opportunities": opportunities[:limit],
            "total_count": len(opportunities),
            "timestamp": datetime.now().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Dashboard opportunities failed: {e}")
        return {
            "success": False,
            "error": str(e),
            "timestamp": datetime.now().isoformat()
        }

@app.get("/dashboard/positions")
async def dashboard_positions():
    """Get current positions for dashboard"""
    try:
        # TODO: Get real data from database
        # Mock data for now
        positions = [
            {
                "id": "pos_1",
                "market_title": "Bitcoin above $50,000 - YES",
                "platform": "kalshi",
                "side": "buy",
                "quantity": 100,
                "entry_price": 0.45,
                "current_price": 0.47,
                "unrealized_pnl": 2.00,
                "unrealized_pnl_percentage": 4.4,
                "opened_at": "2025-11-03T09:15:00Z",
                "status": "open"
            },
            {
                "id": "pos_2",
                "market_title": "Election Winner - Trump",
                "platform": "polymarket",
                "side": "sell",
                "quantity": 75,
                "entry_price": 0.62,
                "current_price": 0.58,
                "unrealized_pnl": 3.00,
                "unrealized_pnl_percentage": 6.5,
                "opened_at": "2025-11-03T08:45:00Z",
                "status": "open"
            }
        ]
        
        return {
            "success": True,
            "positions": positions,
            "summary": {
                "total_positions": len(positions),
                "total_unrealized_pnl": sum([p["unrealized_pnl"] for p in positions]),
                "open_positions": len([p for p in positions if p["status"] == "open"])
            },
            "timestamp": datetime.now().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Dashboard positions failed: {e}")
        return {
            "success": False,
            "error": str(e),
            "timestamp": datetime.now().isoformat()
        }

@app.get("/dashboard/performance")
async def dashboard_performance(days: int = 30):
    """Get performance metrics for dashboard"""
    try:
        # TODO: Get real data from database
        # Mock performance data
        performance = {
            "summary": {
                "total_return": 0.152,  # 15.2%
                "sharpe_ratio": 1.45,
                "max_drawdown": -0.05,  # -5%
                "win_rate": 0.75,  # 75%
                "total_trades": 47,
                "profitable_trades": 35,
                "avg_trade_duration_hours": 2.5,
                "avg_profit_per_trade": 3.23
            },
            "daily_pnl": [
                {"date": "2025-10-31", "pnl": 25.00},
                {"date": "2025-11-01", "pnl": -10.50},
                {"date": "2025-11-02", "pnl": 45.75},
                {"date": "2025-11-03", "pnl": 15.25}
            ],
            "best_trades": [
                {"date": "2025-11-02", "profit": 45.75, "market": "Bitcoin futures"},
                {"date": "2025-10-30", "profit": 32.50, "market": "Election betting"}
            ],
            "worst_trades": [
                {"date": "2025-11-01", "profit": -10.50, "market": "Sports betting"}
            ]
        }
        
        return {
            "success": True,
            "performance": performance,
            "period_days": days,
            "timestamp": datetime.now().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Dashboard performance failed: {e}")
        return {
            "success": False,
            "error": str(e),
            "timestamp": datetime.now().isoformat()
        }

# For local development
if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)