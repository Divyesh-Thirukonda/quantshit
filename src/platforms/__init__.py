# Platforms package - API connectors for different prediction markets
from .base import BaseMarketAPI
from .registry import get_market_api, PLATFORM_APIS, get_all_platforms, is_platform_supported
from .polymarket import PolymarketAPI
from .kalshi import KalshiAPI
from .manifold import ManifoldAPI

__all__ = ['get_market_api', 'BaseMarketAPI', 'PolymarketAPI', 'KalshiAPI', 'ManifoldAPI', 'PLATFORM_APIS', 'get_all_platforms', 'is_platform_supported']