# Platforms package - API connectors for different prediction markets
from .base import get_market_api, BaseMarketAPI
from .polymarket import PolymarketAPI
from .kalshi import KalshiAPI
from .manifold import ManifoldAPI

__all__ = ['get_market_api', 'BaseMarketAPI', 'PolymarketAPI', 'KalshiAPI', 'ManifoldAPI']