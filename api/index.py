"""
Vercel serverless function for Quantshit Arbitrage Engine
"""

import sys
import os
from datetime import datetime

# Add the parent directory to the path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

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

# Try to import trading system
try:
    from src.coordinators.trading_orchestrator import TradingOrchestrator
    from src.platforms.registry import get_all_platforms
    SYSTEM_AVAILABLE = True
except ImportError as e:
    SYSTEM_AVAILABLE = False

@app.get("/")
async def root():
    """API root endpoint"""
    return {
        "message": "Quantshit Arbitrage Engine API",
        "version": "2.0.0",
        "status": "healthy",
        "system_available": SYSTEM_AVAILABLE,
        "timestamp": datetime.now().isoformat()
    }

@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "timestamp": datetime.now().isoformat(),
        "system_imports": SYSTEM_AVAILABLE,
        "env_check": {
            "POLYMARKET_API_KEY": "SET" if os.getenv("POLYMARKET_API_KEY") else "MISSING",
            "KALSHI_API_KEY": "SET" if os.getenv("KALSHI_API_KEY") else "MISSING"
        }
    }

@app.get("/scan")
async def scan_opportunities(size: int = 250, min_edge: float = 0.05):
    """Scan for arbitrage opportunities"""
    if not SYSTEM_AVAILABLE:
        return {
            "success": False,
            "error": "Trading system not available",
            "opportunities": []
        }
    
    try:
        orchestrator = TradingOrchestrator()
        opportunities = orchestrator.scan_once(size=size, min_edge=min_edge)
        
        return {
            "success": True,
            "opportunities": opportunities,
            "parameters": {"size": size, "min_edge": min_edge},
            "timestamp": datetime.now().isoformat()
        }
    except Exception as e:
        return {
            "success": False,
            "error": str(e),
            "opportunities": []
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
        platforms = get_all_platforms()
        markets_data = {}
        
        for platform_name, platform in platforms.items():
            try:
                markets = platform.get_markets()
                markets_data[platform_name] = {
                    "status": "connected",
                    "market_count": len(markets),
                    "markets": markets[:5]  # Return first 5 markets as sample
                }
            except Exception as e:
                markets_data[platform_name] = {
                    "status": "error",
                    "error": str(e)
                }
        
        return {
            "success": True,
            "markets": markets_data,
            "timestamp": datetime.now().isoformat()
        }
        
    except Exception as e:
        return {
            "success": False,
            "error": str(e),
            "markets": {}
        }

@app.post("/execute/{opportunity_id}")
async def execute_opportunity(opportunity_id: str):
    """Execute an arbitrage opportunity"""
    try:
        if not SYSTEM_AVAILABLE:
            return {
                "success": False,
                "error": "Trading system not available",
                "execution_id": None
            }
        
        # For now, return a simulation response
        return {
            "success": True,
            "message": f"Opportunity {opportunity_id} executed in paper trading mode",
            "execution_id": f"exec_{opportunity_id}_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
            "mode": "paper_trading",
            "timestamp": datetime.now().isoformat()
        }
        
    except Exception as e:
        return {
            "success": False,
            "error": str(e),
            "execution_id": None,
            "timestamp": datetime.now().isoformat()
        }

# This is the handler that Vercel will call
app = app

# For local development
if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)