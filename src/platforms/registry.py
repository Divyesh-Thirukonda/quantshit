"""
Platform registry for prediction market APIs
"""

from .base import BaseMarketAPI
from .kalshi import KalshiAPI, KalshiPaperAPI
from .polymarket import PolymarketAPI, PolymarketPaperAPI
from ..config.environment import env


# Registry mapping platform names to API classes
PLATFORM_APIS = {
    'polymarket': PolymarketAPI,
    'kalshi': KalshiAPI
}

# Paper trading API registry
PAPER_TRADING_APIS = {
    'polymarket': PolymarketPaperAPI,
    'kalshi': KalshiPaperAPI
}


def get_market_api(platform: str, api_key: str = None) -> BaseMarketAPI:
    """Factory function to get market API instance based on environment"""
    if platform not in PLATFORM_APIS:
        raise ValueError(f"Unsupported platform: {platform}")
    
    if env.is_paper_trading():
        # Use paper trading APIs
        paper_api_class = PAPER_TRADING_APIS.get(platform)
        if paper_api_class:
            config = env.get_api_config()
            return paper_api_class(config['initial_balance_per_platform'])
        else:
            raise ValueError(f"No paper trading API available for platform: {platform}")
    else:
        # Use real APIs
        return PLATFORM_APIS[platform](api_key)


def get_all_platforms() -> list:
    """Get list of all supported platform names"""
    return list(PLATFORM_APIS.keys())


def is_platform_supported(platform: str) -> bool:
    """Check if a platform is supported"""
    return platform in PLATFORM_APIS