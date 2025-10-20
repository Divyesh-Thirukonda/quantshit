"""
Base classes and factory for prediction market APIs
"""

from abc import ABC, abstractmethod
from typing import List, Dict, Optional
import requests


class BaseMarketAPI(ABC):
    """Base class for prediction market APIs"""
    
    def __init__(self, api_key: str = None):
        self.api_key = api_key
        self.session = requests.Session()
        
        if api_key:
            self.session.headers.update(self._get_auth_headers())
    
    @abstractmethod
    def _get_auth_headers(self) -> Dict[str, str]:
        """Get authentication headers for API requests"""
        pass
    
    @abstractmethod
    def get_recent_markets(self, min_volume: float = 1000) -> List[Dict]:
        """Get recent markets with minimum volume"""
        pass
    
    @abstractmethod
    def place_buy_order(self, market_id: str, outcome: str, amount: float, price: float) -> Dict:
        """Place a buy order"""
        pass
    
    @abstractmethod
    def place_sell_order(self, market_id: str, outcome: str, amount: float, price: float) -> Dict:
        """Place a sell order"""
        pass
    
    @abstractmethod
    def find_event(self, keyword: str, limit: int = 10) -> List[Dict]:
        """Search for events/markets by keyword"""
        pass
    
    def execute_event(self, event_id: str, outcome: str, action: str, amount: float, price: float = None) -> Dict:
        """Execute a trade on a specific event
        
        Args:
            event_id: The market/event ID
            outcome: 'YES' or 'NO' 
            action: 'BUY' or 'SELL'
            amount: Number of shares
            price: Price per share (if None, use market price)
        """
        if action.upper() == 'BUY':
            return self.place_buy_order(event_id, outcome, amount, price)
        elif action.upper() == 'SELL':
            return self.place_sell_order(event_id, outcome, amount, price)
        else:
            return {'success': False, 'error': f'Invalid action: {action}'}


# Platform imports
from .polymarket import PolymarketAPI
from .kalshi import KalshiAPI  
from .manifold import ManifoldAPI

# Registry
PLATFORM_APIS = {
    'polymarket': PolymarketAPI,
    'kalshi': KalshiAPI,
    'manifold': ManifoldAPI
}


def get_market_api(platform: str, api_key: str = None) -> BaseMarketAPI:
    """Factory function to get market API instance"""
    if platform not in PLATFORM_APIS:
        raise ValueError(f"Unsupported platform: {platform}")
    
    return PLATFORM_APIS[platform](api_key)