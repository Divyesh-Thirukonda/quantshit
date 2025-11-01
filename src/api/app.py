"""FastAPI web service for the prediction market arbitrage system."""

from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
import uvicorn
import sys
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Optional
import asyncio
import time

# Add project root to path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from src.core import Platform, Market, Quote, ArbitrageOpportunity
from src.monitoring import health_monitor
from config.settings import config

# Initialize FastAPI app
app = FastAPI(
    title="Quantshit Arbitrage API",
    description="Prediction Market Arbitrage System",
    version="0.1.0",
    docs_url="/docs",
    redoc_url="/redoc"
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure appropriately for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Middleware to track request metrics
@app.middleware("http")
async def track_requests(request: Request, call_next):
    start_time = time.time()
    
    try:
        response = await call_next(request)
        process_time = (time.time() - start_time) * 1000  # Convert to milliseconds
        
        # Record metrics
        is_error = response.status_code >= 400
        health_monitor.record_request(process_time, is_error)
        
        # Add performance header
        response.headers["X-Process-Time"] = str(round(process_time, 2))
        
        return response
    except Exception as e:
        process_time = (time.time() - start_time) * 1000
        health_monitor.record_request(process_time, True)
        raise e

# Global state (will be replaced with proper database in Phase 2)
active_opportunities: List[Dict] = []
portfolio_state: Dict = {
    "total_value": 10000.0,
    "available_balance": 10000.0,
    "positions": [],
    "daily_pnl": 0.0
}


@app.get("/")
async def root():
    """Root endpoint with API information."""
    return {
        "service": "Quantshit Arbitrage API",
        "version": "0.1.0",
        "status": "operational",
        "timestamp": datetime.utcnow().isoformat(),
        "phase": "Phase 1: Foundation & Types"
    }


@app.get("/health")
async def health_check():
    """Health check endpoint for cloud deployment."""
    health_status = health_monitor.get_detailed_health()
    
    # Return appropriate HTTP status code
    status_code = 200
    if health_status["overall_status"] == "degraded":
        status_code = 200  # Still OK, but monitoring should alert
    elif health_status["overall_status"] == "unhealthy":
        status_code = 503  # Service unavailable
    
    return JSONResponse(
        status_code=status_code,
        content={
            "status": health_status["overall_status"],
            "timestamp": health_status["timestamp"],
            "checks": health_status["checks"],
            "uptime_seconds": health_status["system"]["uptime_seconds"]
        }
    )


@app.get("/health/detailed")
async def health_detailed():
    """Detailed health information for monitoring."""
    return health_monitor.get_detailed_health()


@app.get("/metrics")
async def get_metrics():
    """Prometheus-style metrics endpoint."""
    health_info = health_monitor.get_detailed_health()
    
    metrics = []
    metrics.append(f'quantshit_cpu_percent {health_info["system"]["cpu_percent"]}')
    metrics.append(f'quantshit_memory_percent {health_info["system"]["memory_percent"]}')
    metrics.append(f'quantshit_uptime_seconds {health_info["system"]["uptime_seconds"]}')
    metrics.append(f'quantshit_total_requests {health_info["service"]["total_requests"]}')
    metrics.append(f'quantshit_total_errors {health_info["service"]["total_errors"]}')
    metrics.append(f'quantshit_error_rate {health_info["service"]["error_rate"]}')
    metrics.append(f'quantshit_response_time_ms {health_info["service"]["response_time_ms"]}')
    
    return "\n".join(metrics)


@app.get("/status")
async def get_status():
    """Get system status and configuration."""
    platform_configs = {}
    for platform in Platform:
        config_exists = config.get_platform_config(platform) is not None
        platform_configs[platform.value] = {
            "configured": config_exists,
            "testnet": True  # Always testnet in Phase 1
        }
    
    return {
        "system": {
            "environment": config.environment,
            "debug": config.debug,
            "paper_trading": config.trading.paper_trading
        },
        "platforms": platform_configs,
        "trading": {
            "max_position_size": config.trading.max_position_size,
            "max_total_exposure": config.trading.max_total_exposure,
            "min_profit_threshold": config.trading.min_profit_threshold
        },
        "portfolio": portfolio_state
    }


@app.get("/opportunities")
async def get_opportunities():
    """Get current arbitrage opportunities."""
    return {
        "opportunities": active_opportunities,
        "count": len(active_opportunities),
        "last_updated": datetime.utcnow().isoformat()
    }


@app.get("/portfolio")
async def get_portfolio():
    """Get current portfolio state."""
    return {
        "portfolio": portfolio_state,
        "last_updated": datetime.utcnow().isoformat()
    }


@app.post("/simulate/opportunity")
async def simulate_opportunity(data: Dict):
    """Simulate an arbitrage opportunity (for testing)."""
    try:
        # Create a simulated opportunity
        opportunity = {
            "id": f"SIM_{len(active_opportunities) + 1}",
            "market_a": {
                "platform": "kalshi",
                "title": data.get("title", "Test Market"),
                "yes_price": data.get("price_a", 0.65)
            },
            "market_b": {
                "platform": "polymarket", 
                "title": data.get("title", "Test Market"),
                "yes_price": data.get("price_b", 0.70)
            },
            "expected_profit": abs(data.get("price_b", 0.70) - data.get("price_a", 0.65)) * 100,
            "profit_percentage": abs(data.get("price_b", 0.70) - data.get("price_a", 0.65)) / data.get("price_a", 0.65),
            "confidence_score": 0.85,
            "detected_at": datetime.utcnow().isoformat()
        }
        
        active_opportunities.append(opportunity)
        
        return {
            "success": True,
            "opportunity": opportunity,
            "message": "Simulated opportunity created"
        }
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@app.delete("/opportunities/{opportunity_id}")
async def remove_opportunity(opportunity_id: str):
    """Remove an opportunity (simulate execution)."""
    global active_opportunities
    
    initial_count = len(active_opportunities)
    active_opportunities = [opp for opp in active_opportunities if opp.get("id") != opportunity_id]
    
    if len(active_opportunities) < initial_count:
        return {
            "success": True,
            "message": f"Opportunity {opportunity_id} removed"
        }
    else:
        raise HTTPException(status_code=404, detail="Opportunity not found")


@app.get("/markets/{platform}")
async def get_markets(platform: str):
    """Get markets for a specific platform (placeholder)."""
    if platform.lower() not in ["kalshi", "polymarket"]:
        raise HTTPException(status_code=400, detail="Unsupported platform")
    
    # Placeholder response
    return {
        "platform": platform,
        "markets": [],
        "message": "Market data integration coming in Phase 2",
        "count": 0
    }


@app.get("/config")
async def get_config():
    """Get current configuration (sanitized)."""
    return {
        "environment": config.environment,
        "debug": config.debug,
        "paper_trading": config.trading.paper_trading,
        "trading_limits": {
            "max_position_size": config.trading.max_position_size,
            "max_total_exposure": config.trading.max_total_exposure,
            "min_profit_threshold": config.trading.min_profit_threshold
        },
        "platforms_configured": len(config.platforms)
    }


if __name__ == "__main__":
    # Run the server
    uvicorn.run(
        "app:app",
        host=config.api_host,
        port=config.api_port,
        reload=config.debug,
        log_level="info" if not config.debug else "debug"
    )