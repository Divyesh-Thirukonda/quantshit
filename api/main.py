"""
FastAPI application entry point for the prediction market arbitrage system.
"""

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
import uvicorn
import os
from datetime import datetime

from api.routes import markets, arbitrage, portfolio, health
from api.database import init_database

app = FastAPI(
    title="Prediction Market Arbitrage API",
    description="API for identifying and executing arbitrage opportunities across prediction markets",
    version="0.1.0",
    docs_url="/docs",
    redoc_url="/redoc"
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure this properly for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(health.router, prefix="/api/v1")
app.include_router(markets.router, prefix="/api/v1/markets", tags=["markets"])
app.include_router(arbitrage.router, prefix="/api/v1/arbitrage", tags=["arbitrage"])
app.include_router(portfolio.router, prefix="/api/v1/portfolio", tags=["portfolio"])


@app.on_event("startup")
async def startup_event():
    """Initialize database and other startup tasks."""
    await init_database()


@app.get("/")
async def root():
    """Root endpoint."""
    return {
        "message": "🎯 Prediction Market Arbitrage API",
        "version": "0.1.0",
        "status": "deployed",
        "timestamp": datetime.utcnow().isoformat(),
        "endpoints": {
            "health": "/api/v1/health",
            "markets": "/api/v1/markets",
            "arbitrage": "/api/v1/arbitrage/opportunities",
            "portfolio": "/api/v1/portfolio",
            "docs": "/docs"
        }
    }


@app.exception_handler(Exception)
async def global_exception_handler(request, exc):
    """Global exception handler."""
    return JSONResponse(
        status_code=500,
        content={"message": "Internal server error", "detail": str(exc)}
    )


if __name__ == "__main__":
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=int(os.getenv("PORT", 8000)),
        reload=True
    )