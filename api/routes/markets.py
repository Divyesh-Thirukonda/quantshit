"""
Market data endpoints.
"""

from fastapi import APIRouter, Query, HTTPException
from typing import List, Optional
from datetime import datetime

from shared.models import Market
from shared.enums import Platform, MarketStatus

router = APIRouter()


@router.get("/", response_model=List[Market])
async def get_markets(
    platform: Optional[Platform] = Query(None, description="Filter by platform"),
    status: Optional[MarketStatus] = Query(None, description="Filter by market status"),
    limit: int = Query(100, description="Maximum number of markets to return", le=1000)
):
    """Get list of markets with optional filters."""
    # TODO: Implement actual database query
    # For now, return mock data
    mock_markets = [
        Market(
            id="mock_market_1",
            platform=Platform.KALSHI,
            title="Will Bitcoin be above $50,000 on December 31, 2024?",
            description="Binary market on Bitcoin price",
            close_date=datetime(2024, 12, 31),
            status=MarketStatus.ACTIVE,
            category="crypto",
            tags=["bitcoin", "cryptocurrency"],
            volume_24h=1000.0,
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow()
        )
    ]
    
    return mock_markets


@router.get("/{market_id}", response_model=Market)
async def get_market(market_id: str):
    """Get a specific market by ID."""
    # TODO: Implement actual database query
    if market_id == "mock_market_1":
        return Market(
            id=market_id,
            platform=Platform.KALSHI,
            title="Will Bitcoin be above $50,000 on December 31, 2024?",
            description="Binary market on Bitcoin price",
            close_date=datetime(2024, 12, 31),
            status=MarketStatus.ACTIVE,
            category="crypto",
            tags=["bitcoin", "cryptocurrency"],
            volume_24h=1000.0,
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow()
        )
    
    raise HTTPException(status_code=404, detail="Market not found")


@router.get("/{market_id}/quotes")
async def get_market_quotes(market_id: str):
    """Get current quotes for a market."""
    # TODO: Implement actual quote fetching from platforms
    return {
        "market_id": market_id,
        "quotes": [
            {
                "outcome": "yes",
                "bid_price": 0.45,
                "ask_price": 0.47,
                "last_price": 0.46,
                "timestamp": datetime.utcnow().isoformat()
            },
            {
                "outcome": "no", 
                "bid_price": 0.53,
                "ask_price": 0.55,
                "last_price": 0.54,
                "timestamp": datetime.utcnow().isoformat()
            }
        ]
    }