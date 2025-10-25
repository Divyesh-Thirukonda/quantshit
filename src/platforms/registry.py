"""
Platform registry for prediction market APIs
"""

import os
from .base import BaseMarketAPI
from .kalshi import KalshiAPI
from .polymarket import PolymarketAPI


# Registry mapping platform names to API classes
PLATFORM_APIS = {
    'polymarket': PolymarketAPI,
    'kalshi': KalshiAPI
}


def get_market_api(platform: str, api_key: str = None) -> BaseMarketAPI:
    """Factory function to get market API instance (paper trading mode only)"""
    if platform not in PLATFORM_APIS:
        raise ValueError(f"Unsupported platform: {platform}")
    
    # Get API key from environment if not provided
    if api_key is None:
        if platform == 'polymarket':
            api_key = os.getenv('POLYMARKET_API_KEY')
        elif platform == 'kalshi':
            api_key = os.getenv('KALSHI_API_KEY')
    
    # Always return mock APIs for paper trading
    print(f"   📄 Creating paper trading API for {platform}")
    return PLATFORM_APIS[platform](api_key)


def get_all_platforms() -> list:
    """Get list of all supported platform names"""
    return list(PLATFORM_APIS.keys())


def is_platform_supported(platform: str) -> bool:
    """Check if a platform is supported"""
    return platform in PLATFORM_APIS