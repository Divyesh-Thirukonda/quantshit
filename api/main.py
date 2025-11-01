# Vercel + FastAPI + Supabase
# Main entry point for Vercel deployment

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
import os
import psutil
import time
from datetime import datetime
import json
from typing import Optional, List, Dict, Any

# Create FastAPI app
app = FastAPI(title="Quantshit API", description="Prediction Market Arbitrage System")

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Supabase integration (simplified for Vercel)
class SimpleSupabaseClient:
    """Simplified Supabase client for demo purposes"""
    
    def __init__(self):
        self.sample_markets = [
            {
                "id": 1,
                "platform": "KALSHI",
                "market_id": "PRES-2024",
                "title": "Presidential Election 2024",
                "yes_price": 0.52,
                "no_price": 0.48,
                "volume": 125000,
                "status": "active"
            },
            {
                "id": 2,
                "platform": "POLYMARKET", 
                "market_id": "pres-election-2024",
                "title": "2024 US Presidential Election",
                "yes_price": 0.51,
                "no_price": 0.49,
                "volume": 89000,
                "status": "active"
            }
        ]
        
        self.sample_opportunities = [
            {
                "id": 1,
                "market_a_platform": "KALSHI",
                "market_a_price": 0.52,
                "market_b_platform": "POLYMARKET",
                "market_b_price": 0.51,
                "profit_percentage": 1.96,
                "confidence_score": 0.85,
                "created_at": "2025-10-31T20:00:00Z"
            }
        ]
    
    def get_markets(self, platform: Optional[str] = None):
        if platform:
            return [m for m in self.sample_markets if m["platform"] == platform]
        return self.sample_markets
    
    def get_opportunities(self, limit: int = 10):
        return self.sample_opportunities[:limit]

# Initialize clients
supabase_client = SimpleSupabaseClient()

# Health monitoring class (simplified for Vercel)
class HealthMonitor:
    def __init__(self):
        self.start_time = time.time()
    
    def get_health_status(self):
        """Get current system health status"""
        current_time = datetime.now()
        uptime = time.time() - self.start_time
        
        try:
            cpu_percent = psutil.cpu_percent(interval=0.1)
            memory = psutil.virtual_memory()
            
            health_data = {
                "status": "healthy",
                "timestamp": current_time.isoformat(),
                "checks": {
                    "api_responsive": True,
                    "cpu_healthy": cpu_percent < 80,
                    "memory_healthy": memory.percent < 85,
                    "database_connected": True,  # Simulated for demo
                    "error_rate_healthy": True
                },
                "uptime_seconds": round(uptime, 2),
                "system_info": {
                    "cpu_percent": cpu_percent,
                    "memory_percent": memory.percent,
                }
            }
            
            # Overall health determination
            all_healthy = all(health_data["checks"].values())
            health_data["status"] = "healthy" if all_healthy else "degraded"
            
            return health_data
            
        except Exception as e:
            return {
                "status": "unhealthy",
                "timestamp": current_time.isoformat(),
                "error": str(e),
                "uptime_seconds": round(uptime, 2)
            }

# Initialize health monitor
health_monitor = HealthMonitor()

@app.get("/")
async def root():
    """Root endpoint"""
    return {
        "message": "Quantshit Prediction Market Arbitrage API",
        "version": "1.0.0",
        "status": "running",
        "docs": "/docs",
        "endpoints": {
            "health": "/health",
            "markets": "/markets",
            "opportunities": "/arbitrage/opportunities",
            "metrics": "/metrics"
        }
    }

@app.get("/health")
async def health_check():
    """Basic health check endpoint"""
    health_data = health_monitor.get_health_status()
    status_code = 200 if health_data["status"] == "healthy" else 503
    return JSONResponse(content=health_data, status_code=status_code)

@app.get("/health/detailed")
async def detailed_health():
    """Detailed health check with system metrics"""
    return health_monitor.get_health_status()

@app.get("/metrics")
async def metrics():
    """System metrics endpoint"""
    try:
        cpu_percent = psutil.cpu_percent(interval=0.1)
        memory = psutil.virtual_memory()
        
        return {
            "timestamp": datetime.now().isoformat(),
            "metrics": {
                "cpu": {
                    "percent": cpu_percent,
                    "count": psutil.cpu_count()
                },
                "memory": {
                    "total": memory.total,
                    "available": memory.available,
                    "percent": memory.percent,
                    "used": memory.used
                },
                "api": {
                    "uptime_seconds": time.time() - health_monitor.start_time,
                    "total_markets": len(supabase_client.sample_markets),
                    "total_opportunities": len(supabase_client.sample_opportunities)
                }
            }
        }
    except Exception as e:
        return JSONResponse(
            content={"error": str(e)},
            status_code=500
        )

@app.get("/markets")
async def get_markets(platform: Optional[str] = None):
    """Get all markets or markets from specific platform"""
    try:
        markets = supabase_client.get_markets(platform)
        return {
            "markets": markets,
            "count": len(markets),
            "timestamp": datetime.now().isoformat()
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/arbitrage/opportunities")
async def get_arbitrage_opportunities(limit: int = 10):
    """Get recent arbitrage opportunities"""
    try:
        opportunities = supabase_client.get_opportunities(limit)
        return {
            "opportunities": opportunities,
            "count": len(opportunities),
            "timestamp": datetime.now().isoformat()
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/status")
async def system_status():
    """System status overview"""
    return {
        "system": "Quantshit Arbitrage System",
        "status": "operational",
        "version": "1.0.0",
        "deployment": "vercel",
        "database": "supabase",
        "uptime": time.time() - health_monitor.start_time,
        "timestamp": datetime.now().isoformat()
    }

# Vercel handler function
def handler(request):
    """Main handler for Vercel"""
    return app