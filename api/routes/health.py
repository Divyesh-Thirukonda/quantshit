"""
Health check endpoints.
"""

from fastapi import APIRouter
from datetime import datetime
import os

router = APIRouter()


@router.get("/health")
async def health_check():
    """Health check endpoint."""
    return {
        "status": "healthy",
        "timestamp": datetime.utcnow().isoformat(),
        "service": "prediction-market-arbitrage-api"
    }


@router.get("/status")
async def status_check():
    """Detailed status check."""
    return {
        "status": "operational",
        "timestamp": datetime.utcnow().isoformat(),
        "version": "0.1.0",
        "deployment": "vercel",
        "environment": "production" if os.getenv("VERCEL") else "development",
        "components": {
            "api": "healthy",
            "database": "not_connected" if not os.getenv("SUPABASE_URL") else "ready",
            "external_apis": "not_configured"
        }
    }