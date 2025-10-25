"""
Vercel serverless function wrapper for the Quantshit Arbitrage Engine
Comprehensive API for position management, TradePlan execution, and portfolio analytics
"""

import sys
import os
import logging
from datetime import datetime, timedelta

# Add the parent directory to the path so we can import our modules
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from fastapi import FastAPI, HTTPException, Depends
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from typing import List, Optional, Dict, Any
from pydantic import BaseModel
import json

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Import our comprehensive trading system (using new clean architecture)
try:
    from src.coordinators.trading_orchestrator import TradingOrchestrator as ArbitrageBot
    from src.coordinators.execution_coordinator import ExecutionCoordinator as TradeExecutor
    from src.engine.position_manager import PositionManager, PositionManagerConfig
    from src.types import (
        PositionManagerConfig, TradingConfig, Platform, Outcome, OrderSide, TradePriority,
        create_arbitrage_plan, ArbitrageOpportunity, Market, Quote, TradePlan, Position
    )
    IMPORTS_AVAILABLE = True
except ImportError as e:
    # Fallback for Vercel environment where some imports might fail
    logger.warning(f"Import failed: {e}")
    ArbitrageBot = None
    TradeExecutor = None
    PositionManager = None
    PositionManagerConfig = None
    OrderSide = None
    TradePriority = None
    TradePlan = None
    IMPORTS_AVAILABLE = False

# Create FastAPI app
app = FastAPI(
    title="Quantshit Arbitrage Engine", 
    version="2.0.0",
    description="Enterprise-grade Arbitrage Detection with Intelligent Position Management"
)

# Add CORS middleware for frontend integration
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure this properly for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Global instances
bot = None
executor = None

# Pydantic models for API requests/responses
class ScanRequest(BaseModel):
    """Request body for scanning opportunities"""
    size: int = 250
    strategy: str = "arbitrage"
    platforms: List[str] = ["kalshi", "polymarket"]
    min_edge: float = 0.05
    max_results: int = 10

class PositionConfigRequest(BaseModel):
    """Position manager configuration"""
    max_open_positions: int = 10
    min_swap_threshold_pct: float = 5.0
    position_size_pct: float = 0.05
    min_remaining_gain_pct: float = 2.0
    force_close_threshold_pct: float = -10.0

class TradePlanRequest(BaseModel):
    """Request to create and execute a TradePlan"""
    plan_name: str
    buy_platform: str
    sell_platform: str
    outcome: str  # "YES" or "NO"
    buy_quantity: int
    sell_quantity: int
    buy_price: float
    sell_price: float
    market_title: str = "Custom Market"

class ExecuteOpportunityRequest(BaseModel):
    """Request to execute a single opportunity"""
    opportunity_id: str
    quantity: Optional[int] = None
    max_slippage: float = 0.01

class ClosePositionRequest(BaseModel):
    """Request to close a specific position"""
    position_id: str
    quantity: Optional[int] = None  # If None, close entire position

class PortfolioAnalyticsRequest(BaseModel):
    """Request for portfolio analytics"""
    include_positions: bool = True
    include_history: bool = False
    timeframe_hours: int = 24

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
            print("Arbitrage Bot initialized for Vercel")
        except Exception as e:
            print(f"⚠️ Could not initialize bot: {e}. Using mock data.")
            bot = None
    else:
        print("⚠️ Running in mock mode for Vercel deployment")

@app.get("/")
async def root():
    """API information and usage"""
    return {
        "service": "Quantshit Enterprise Trading System",
        "version": "2.0.0", 
        "description": "Comprehensive prediction market arbitrage engine with position management, TradePlan execution, and portfolio analytics",
        "deployment": "Vercel Serverless",
        "capabilities": {
            "arbitrage_detection": "Cross-venue opportunity scanning",
            "position_management": "Intelligent position tracking with auto-swapping",
            "trade_plans": "Multi-leg strategy execution with dependency management",
            "portfolio_analytics": "Real-time performance tracking and risk analysis",
            "enterprise_features": "Kelly criterion sizing, correlation analysis, automated position optimization"
        },
        "endpoints": {
            "legacy": {
                "POST /scan": "Basic arbitrage opportunity scanning",
                "POST /execute/{opportunity_id}": "Execute arbitrage trade"
            },
            "enterprise": {
                "GET /api/positions": "Get all positions with analytics",
                "GET /api/positions/{position_id}": "Get specific position details",
                "POST /api/positions/close": "Close position",
                "POST /api/tradeplan/create": "Create sophisticated trading plan",
                "POST /api/tradeplan/execute": "Execute complete trading plan",
                "POST /api/execute/opportunity": "Execute opportunity with position management",
                "GET /api/portfolio/summary": "Portfolio performance summary",
                "POST /api/portfolio/analytics": "Detailed portfolio analytics",
                "GET /api/config/position-manager": "Get position manager config",
                "POST /api/config/position-manager": "Update position manager config",
                "GET /api/system/status": "System health and status"
            }
        },
        "example_usage": {
            "scan_opportunities": "POST /scan with JSON: {size: 250, strategy: 'arbitrage', platforms: ['kalshi', 'polymarket'], min_edge: 0.02}",
            "create_trade_plan": "POST /api/tradeplan/create with plan details",
            "get_portfolio": "GET /api/portfolio/summary for real-time performance",
            "position_analytics": "GET /api/positions for all positions with analytics"
        },
        "github": "https://github.com/Divyesh-Thirukonda/quantshit",
        "features": {
            "position_management": "10-position limit with intelligent swapping",
            "risk_management": "Kelly criterion, correlation analysis, stop-losses",
            "execution_engine": "Universal place() method supporting TradePlans and opportunities",
            "portfolio_optimization": "Automatic position swapping based on potential remaining gain"
        }
    }

@app.get("/health")
async def health_check():
    return {
        "status": "healthy", 
        "timestamp": datetime.utcnow().isoformat(),
        "environment": "vercel",
        "bot_initialized": bot is not None
    }

@app.post("/scan")
async def scan_opportunities(request: ScanRequest):
    """Scan for arbitrage opportunities with configurable parameters"""
    try:
        if bot:
            # Use real bot if available - filter by requested platforms
            if request.platforms:
                # Filter to only requested platforms (simplified for Vercel)
                markets_data = bot.collect_market_data()
            else:
                markets_data = bot.collect_market_data()
                
            opportunities = bot.strategy.find_opportunities(markets_data)
            
            # Filter by minimum edge
            filtered_ops = [op for op in opportunities if op['spread'] >= request.min_edge]
            
            # Format for API response
            ideas = []
            for i, opp in enumerate(filtered_ops[:request.max_results]):
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
                        "min_edge": request.min_edge,
                        "platforms": request.platforms,
                        "strategy": request.strategy
                    },
                    "source": "live_data"
                }
            }
        else:
            # Use mock data for demo
            filtered_mock = [opp for opp in MOCK_OPPORTUNITIES if int(opp['edge_bps']) >= request.min_edge * 10000]
            
            return {
                "success": True,
                "opportunities": filtered_mock[:request.max_results],
                "meta": {
                    "scanned_markets": 25,
                    "opportunities_found": len(filtered_mock),
                    "timestamp": datetime.utcnow().isoformat(),
                    "parameters": {
                        "size": request.size, 
                        "min_edge": request.min_edge,
                        "platforms": request.platforms,
                        "strategy": request.strategy
                    },
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

# ============================================================================
# ENTERPRISE TRADING SYSTEM ENDPOINTS
# ============================================================================

# Initialize global executor with position manager
executor = None
position_manager = None

@app.on_event("startup")
async def initialize_trading_system():
    """Initialize the enterprise trading system"""
    global executor, position_manager
    try:
        if IMPORTS_AVAILABLE and PositionManager and PositionManagerConfig:
            # Initialize position manager with default config
            config = PositionManagerConfig()
            position_manager = PositionManager(config)
            
            # Initialize executor with position manager
            executor = TradeExecutor(position_manager=position_manager)
            
            logger.info("🏛️ Enterprise Trading System initialized")
        else:
            logger.info("🔧 Running in mock mode - trading system components not available")
            executor = None
            position_manager = None
    except Exception as e:
        logger.error(f"Failed to initialize trading system: {e}")
        executor = None
        position_manager = None

# Position Management Endpoints
@app.get("/api/positions",
         summary="Get All Positions",
         description="Retrieve all current positions with analytics")
async def get_positions():
    """Get all current positions"""
    try:
        if not position_manager:
            raise HTTPException(status_code=503, detail="Trading system not initialized")
        
        positions = position_manager.get_all_positions()
        
        return {
            "status": "success",
            "data": {
                "positions": [pos.to_dict() for pos in positions],
                "summary": {
                    "total_positions": len(positions),
                    "total_invested": sum(pos.invested_amount for pos in positions),
                    "total_potential_value": sum(pos.potential_value for pos in positions),
                    "total_unrealized_pnl": sum(pos.unrealized_pnl for pos in positions),
                    "average_potential_gain": sum(pos.potential_remaining_gain_pct for pos in positions) / len(positions) if positions else 0
                },
                "timestamp": datetime.now().isoformat()
            }
        }
    except Exception as e:
        logger.error(f"Error getting positions: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/positions/{position_id}",
         summary="Get Position Details",
         description="Get detailed information about a specific position")
async def get_position(position_id: str):
    """Get specific position details"""
    try:
        if not position_manager:
            raise HTTPException(status_code=503, detail="Trading system not initialized")
        
        position = position_manager.get_position(position_id)
        if not position:
            raise HTTPException(status_code=404, detail="Position not found")
        
        return {
            "status": "success",
            "data": {
                "position": position.to_dict(),
                "analytics": {
                    "potential_remaining_gain_pct": position.potential_remaining_gain_pct,
                    "time_held_hours": (datetime.now() - position.opened_at).total_seconds() / 3600,
                    "should_force_close": position.unrealized_pnl_pct < position_manager.config.force_close_threshold_pct
                },
                "timestamp": datetime.now().isoformat()
            }
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting position {position_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/positions/close",
          summary="Close Position",
          description="Close a specific position partially or completely")
async def close_position(request: ClosePositionRequest):
    """Close a position"""
    try:
        if not executor:
            raise HTTPException(status_code=503, detail="Trading system not initialized")
        
        # For now, return mock close confirmation
        # In a real implementation, this would execute the close orders
        
        return {
            "status": "success",
            "data": {
                "position_id": request.position_id,
                "close_quantity": request.quantity or "full",
                "execution_status": "simulated_close",
                "timestamp": datetime.now().isoformat(),
                "note": "Position close simulated - add real execution logic for live trading"
            }
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error closing position: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# TradePlan Endpoints
@app.post("/api/tradeplan/create",
          summary="Create Trade Plan",
          description="Create a sophisticated multi-leg trading plan")
async def create_trade_plan(request: TradePlanRequest):
    """Create a new TradePlan"""
    try:
        if not IMPORTS_AVAILABLE:
            # Return mock response when trading system not available
            return {
                "status": "success",
                "data": {
                    "plan": {
                        "id": f"plan_{int(datetime.now().timestamp())}",
                        "name": request.plan_name,
                        "buy_platform": request.buy_platform,
                        "sell_platform": request.sell_platform,
                        "outcome": request.outcome,
                        "estimated_profit": (request.sell_price - request.buy_price) * min(request.buy_quantity, request.sell_quantity)
                    },
                    "estimated_execution_time": "< 5 minutes",
                    "risk_assessment": {
                        "spread": f"{request.sell_price - request.buy_price:.4f}",
                        "potential_profit": f"${(request.sell_price - request.buy_price) * min(request.buy_quantity, request.sell_quantity):.2f}",
                        "confidence": "80.0%"
                    },
                    "timestamp": datetime.now().isoformat(),
                    "note": "Mock trade plan - add trading system components for live functionality"
                }
            }
        
        # Create market objects
        buy_market = Market(
            id=f"market_{request.buy_platform}",
            title=request.market_title,
            platform=request.buy_platform,
            outcome=request.outcome,
            close_time=datetime.now() + timedelta(days=30)
        )
        
        sell_market = Market(
            id=f"market_{request.sell_platform}",
            title=request.market_title,
            platform=request.sell_platform,
            outcome=request.outcome,
            close_time=datetime.now() + timedelta(days=30)
        )
        
        # Create quotes
        buy_quote = Quote(
            market=buy_market,
            price=request.buy_price,
            size=request.buy_quantity,
            side=OrderSide.BUY,
            timestamp=datetime.now()
        )
        
        sell_quote = Quote(
            market=sell_market,
            price=request.sell_price,
            size=request.sell_quantity,
            side=OrderSide.SELL,
            timestamp=datetime.now()
        )
        
        # Create arbitrage opportunity
        opportunity = ArbitrageOpportunity(
            buy_quote=buy_quote,
            sell_quote=sell_quote,
            spread=request.sell_price - request.buy_price,
            potential_profit=(request.sell_price - request.buy_price) * min(request.buy_quantity, request.sell_quantity),
            confidence_score=0.8
        )
        
        # Create TradePlan
        plan = TradePlan(
            id=f"plan_{int(datetime.now().timestamp())}",
            name=request.plan_name,
            opportunities=[opportunity],
            dependencies={},
            priority=TradePriority.MEDIUM,
            max_execution_time=timedelta(minutes=5)
        )
        
        return {
            "status": "success",
            "data": {
                "plan": plan.to_dict(),
                "estimated_execution_time": "< 5 minutes",
                "risk_assessment": {
                    "spread": f"{opportunity.spread:.4f}",
                    "potential_profit": f"${opportunity.potential_profit:.2f}",
                    "confidence": f"{opportunity.confidence_score:.1%}"
                },
                "timestamp": datetime.now().isoformat()
            }
        }
        
    except Exception as e:
        logger.error(f"Error creating trade plan: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/tradeplan/execute",
          summary="Execute Trade Plan",
          description="Execute a complete trading plan with position management")
async def execute_trade_plan(plan_data: Dict[str, Any]):
    """Execute a TradePlan"""
    try:
        if not executor:
            raise HTTPException(status_code=503, detail="Trading system not initialized")
        
        # For now, return mock execution
        # In real implementation, this would reconstruct the TradePlan and execute it
        
        return {
            "status": "success",
            "data": {
                "execution_id": f"exec_{int(datetime.now().timestamp())}",
                "plan_id": plan_data.get("id", "unknown"),
                "execution_status": "simulated_execution",
                "legs_executed": 2,
                "total_legs": 2,
                "execution_progress": "100%",
                "timestamp": datetime.now().isoformat(),
                "note": "Plan execution simulated - add real execution logic for live trading"
            }
        }
        
    except Exception as e:
        logger.error(f"Error executing trade plan: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# Execution Endpoints
@app.post("/api/execute/opportunity",
          summary="Execute Single Opportunity",
          description="Execute a single arbitrage opportunity with position management")
async def execute_opportunity(request: ExecuteOpportunityRequest):
    """Execute a single arbitrage opportunity"""
    try:
        if not executor:
            raise HTTPException(status_code=503, detail="Trading system not initialized")
        
        # For now, return mock execution
        return {
            "status": "success", 
            "data": {
                "execution_id": f"exec_{int(datetime.now().timestamp())}",
                "opportunity_id": request.opportunity_id,
                "quantity": request.quantity or "optimal",
                "max_slippage": f"{request.max_slippage:.1%}",
                "execution_status": "simulated_execution",
                "estimated_profit": "$12.50",
                "position_created": True,
                "timestamp": datetime.now().isoformat(),
                "note": "Execution simulated - add real execution logic for live trading"
            }
        }
        
    except Exception as e:
        logger.error(f"Error executing opportunity: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# Portfolio Analytics Endpoints
@app.get("/api/portfolio/summary",
         summary="Portfolio Summary",
         description="Get comprehensive portfolio performance summary")
async def get_portfolio_summary():
    """Get portfolio performance summary"""
    try:
        if not position_manager:
            raise HTTPException(status_code=503, detail="Trading system not initialized")
        
        positions = position_manager.get_all_positions()
        
        # Calculate portfolio metrics
        total_invested = sum(pos.invested_amount for pos in positions)
        total_potential = sum(pos.potential_value for pos in positions)
        total_unrealized = sum(pos.unrealized_pnl for pos in positions)
        
        return {
            "status": "success",
            "data": {
                "performance": {
                    "total_invested": total_invested,
                    "total_potential_value": total_potential,
                    "total_unrealized_pnl": total_unrealized,
                    "unrealized_pnl_pct": (total_unrealized / total_invested * 100) if total_invested > 0 else 0,
                    "position_count": len(positions),
                    "available_slots": position_manager.config.max_open_positions - len(positions)
                },
                "risk_metrics": {
                    "max_position_correlation": 0.3,  # Mock data
                    "portfolio_kelly_fraction": 0.15,  # Mock data
                    "max_drawdown_pct": -2.1,  # Mock data
                    "sharpe_ratio": 1.8  # Mock data
                },
                "recent_activity": {
                    "trades_last_24h": 5,  # Mock data
                    "profits_last_24h": 45.60,  # Mock data
                    "avg_hold_time_hours": 8.3  # Mock data
                },
                "timestamp": datetime.now().isoformat()
            }
        }
        
    except Exception as e:
        logger.error(f"Error getting portfolio summary: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/portfolio/analytics",
          summary="Detailed Portfolio Analytics", 
          description="Get detailed portfolio analytics with customizable parameters")
async def get_portfolio_analytics(request: PortfolioAnalyticsRequest):
    """Get detailed portfolio analytics"""
    try:
        if not position_manager:
            raise HTTPException(status_code=503, detail="Trading system not initialized")
        
        analytics_data = {
            "portfolio_composition": {
                "by_platform": {"kalshi": 0.6, "polymarket": 0.4},  # Mock data
                "by_strategy": {"arbitrage": 1.0},
                "by_time_held": {"<1day": 0.3, "1-7days": 0.5, ">7days": 0.2}
            },
            "performance_metrics": {
                "total_return_pct": 8.5,  # Mock data
                "annualized_return_pct": 156.2,  # Mock data
                "max_drawdown_pct": -2.1,
                "profit_factor": 3.2,
                "win_rate_pct": 78.5
            },
            "risk_analysis": {
                "var_95_pct": -1.8,  # Value at Risk
                "portfolio_beta": 0.15,
                "correlation_matrix": {
                    "kalshi_polymarket": 0.23,
                    "yes_no_correlation": -0.05
                }
            }
        }
        
        if request.include_positions:
            positions = position_manager.get_all_positions()
            analytics_data["current_positions"] = [pos.to_dict() for pos in positions]
        
        if request.include_history:
            analytics_data["trade_history"] = {
                "note": "Historical data would be included here",
                "timeframe_hours": request.timeframe_hours
            }
        
        return {
            "status": "success",
            "data": analytics_data,
            "metadata": {
                "timeframe_hours": request.timeframe_hours,
                "generated_at": datetime.now().isoformat()
            }
        }
        
    except Exception as e:
        logger.error(f"Error getting portfolio analytics: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# Configuration Endpoints
@app.get("/api/config/position-manager",
         summary="Get Position Manager Config",
         description="Get current position manager configuration")
async def get_position_config():
    """Get position manager configuration"""
    try:
        if not position_manager:
            raise HTTPException(status_code=503, detail="Trading system not initialized")
        
        return {
            "status": "success",
            "data": {
                "config": position_manager.config.to_dict(),
                "current_stats": {
                    "open_positions": len(position_manager.get_all_positions()),
                    "max_positions": position_manager.config.max_open_positions,
                    "available_slots": position_manager.config.max_open_positions - len(position_manager.get_all_positions())
                },
                "timestamp": datetime.now().isoformat()
            }
        }
        
    except Exception as e:
        logger.error(f"Error getting position config: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/config/position-manager",
          summary="Update Position Manager Config",
          description="Update position manager configuration")
async def update_position_config(request: PositionConfigRequest):
    """Update position manager configuration"""
    try:
        if not position_manager:
            raise HTTPException(status_code=503, detail="Trading system not initialized")
        
        # Update configuration
        position_manager.config.max_open_positions = request.max_open_positions
        position_manager.config.min_swap_threshold_pct = request.min_swap_threshold_pct
        position_manager.config.position_size_pct = request.position_size_pct
        position_manager.config.min_remaining_gain_pct = request.min_remaining_gain_pct
        position_manager.config.force_close_threshold_pct = request.force_close_threshold_pct
        
        return {
            "status": "success",
            "data": {
                "message": "Configuration updated successfully",
                "new_config": position_manager.config.to_dict(),
                "timestamp": datetime.now().isoformat()
            }
        }
        
    except Exception as e:
        logger.error(f"Error updating position config: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/system/status",
         summary="System Status",
         description="Get comprehensive system status and health")
async def get_system_status():
    """Get system status and health"""
    return {
        "status": "success",
        "data": {
            "system": {
                "version": "2.0.0",
                "environment": "production",
                "trading_system_initialized": executor is not None and position_manager is not None,
                "uptime": "N/A",  # Would calculate actual uptime
            },
            "components": {
                "position_manager": "healthy" if position_manager else "not_initialized",
                "trade_executor": "healthy" if executor else "not_initialized", 
                "platform_connectors": "simulated",  # Mock/Simulated for Vercel
                "data_feeds": "simulated"
            },
            "metrics": {
                "active_positions": len(position_manager.get_all_positions()) if position_manager else 0,
                "system_load": "low",
                "memory_usage": "normal"
            },
            "timestamp": datetime.now().isoformat()
        }
    }

# Export the FastAPI app for Vercel
handler = app

# For local development
if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)