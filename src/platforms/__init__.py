# Platforms package - API connectors for different prediction markets
from .base import BaseMarketAPI
from .kalshi import KalshiAPI
from .polymarket import PolymarketAPI
from .registry import (
    PLATFORM_APIS,
    get_all_platforms,
    get_market_api,
    is_platform_supported,
)

__all__ = [
    'BaseMarketAPI',
    'get_market_api', 
    'KalshiAPI',
    'PLATFORM_APIS',
    'PolymarketAPI',
    'get_all_platforms',
    'is_platform_supported',
]