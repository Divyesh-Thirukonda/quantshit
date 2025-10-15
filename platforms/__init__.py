"""
Platforms package for prediction market API clients.

This package provides a modular structure for different prediction market platforms.
Each platform has its own module and all inherit from BaseMarketAPI.
"""

from .base import BaseMarketAPI
from .polymarket import PolymarketAPI
from .manifold import ManifoldAPI


# Registry to easily add new platforms
MARKET_APIS = {
    'polymarket': PolymarketAPI,
    'manifold': ManifoldAPI
}


def get_market_api(platform: str, api_key: str = None) -> BaseMarketAPI:
    """Factory function to get market API instance"""
    if platform not in MARKET_APIS:
        raise ValueError(f"Unsupported platform: {platform}")

    return MARKET_APIS[platform](api_key)


__all__ = [
    'BaseMarketAPI',
    'PolymarketAPI',
    'ManifoldAPI',
    'MARKET_APIS',
    'get_market_api'
]
