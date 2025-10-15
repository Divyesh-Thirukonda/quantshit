import requests
import time
from typing import List, Dict, Optional


class BaseMarketAPI:
    """Base class for all prediction market APIs"""
    
    def __init__(self, api_key: str = None):
        self.api_key = api_key
    
    def get_recent_markets(self, min_volume: float = 1000) -> List[Dict]:
        """Get recent markets with minimum volume threshold"""
        raise NotImplementedError
    
    def place_buy_order(self, market_id: str, outcome: str, amount: float, price: float) -> Dict:
        """Place a buy order"""
        raise NotImplementedError
    
    def place_sell_order(self, market_id: str, outcome: str, amount: float, price: float) -> Dict:
        """Place a sell order"""
        raise NotImplementedError


class PolymarketAPI(BaseMarketAPI):
    """Polymarket API client"""
    
    def __init__(self, api_key: str = None):
        super().__init__(api_key)
        self.base_url = "https://gamma-api.polymarket.com"
    
    def get_recent_markets(self, min_volume: float = 1000) -> List[Dict]:
        """Get recent markets from Polymarket"""
        try:
            # Get markets sorted by volume
            url = f"{self.base_url}/markets"
            params = {
                "limit": 50,
                "order": "volume24hr",
                "direction": "desc"
            }
            
            response = requests.get(url, params=params, timeout=10)
            response.raise_for_status()
            
            markets = response.json()
            filtered_markets = []
            
            for market in markets:
                volume = float(market.get('volume24hr', 0))
                if volume >= min_volume:
                    filtered_markets.append({
                        'id': market['conditionId'],
                        'title': market['question'],
                        'platform': 'polymarket',
                        'volume': volume,
                        'yes_price': float(market.get('outcomePrices', ['0.5', '0.5'])[0]),
                        'no_price': float(market.get('outcomePrices', ['0.5', '0.5'])[1]),
                        'raw_data': market
                    })
            
            return filtered_markets
            
        except Exception as e:
            print(f"Error fetching Polymarket data: {e}")
            return []
    
    def place_buy_order(self, market_id: str, outcome: str, amount: float, price: float) -> Dict:
        """Place buy order on Polymarket"""
        # For demo purposes - would implement actual trading logic
        return {
            'success': True, 
            'order_id': f'poly_buy_{int(time.time())}',
            'message': f'Demo: Buy {amount} shares of {outcome} at {price}'
        }
    
    def place_sell_order(self, market_id: str, outcome: str, amount: float, price: float) -> Dict:
        """Place sell order on Polymarket"""
        # For demo purposes - would implement actual trading logic
        return {
            'success': True,
            'order_id': f'poly_sell_{int(time.time())}',
            'message': f'Demo: Sell {amount} shares of {outcome} at {price}'
        }


class ManifoldAPI(BaseMarketAPI):
    """Manifold Markets API client"""
    
    def __init__(self, api_key: str = None):
        super().__init__(api_key)
        self.base_url = "https://api.manifold.markets/v0"
    
    def get_recent_markets(self, min_volume: float = 1000) -> List[Dict]:
        """Get recent markets from Manifold"""
        try:
            url = f"{self.base_url}/markets"
            params = {
                "limit": 50,
                "sort": "24-hour-vol"
            }
            
            response = requests.get(url, params=params, timeout=10)
            response.raise_for_status()
            
            markets = response.json()
            filtered_markets = []
            
            for market in markets:
                volume = market.get('volume24Hours', 0)
                if volume >= min_volume and market.get('outcomeType') == 'BINARY':
                    prob = market.get('probability', 0.5)
                    filtered_markets.append({
                        'id': market['id'],
                        'title': market['question'],
                        'platform': 'manifold',
                        'volume': volume,
                        'yes_price': prob,
                        'no_price': 1 - prob,
                        'raw_data': market
                    })
            
            return filtered_markets
            
        except Exception as e:
            print(f"Error fetching Manifold data: {e}")
            return []
    
    def place_buy_order(self, market_id: str, outcome: str, amount: float, price: float) -> Dict:
        """Place buy order on Manifold"""
        # For demo purposes - would implement actual trading logic
        return {
            'success': True,
            'order_id': f'manifold_buy_{int(time.time())}',
            'message': f'Demo: Buy {amount} shares of {outcome} at {price}'
        }
    
    def place_sell_order(self, market_id: str, outcome: str, amount: float, price: float) -> Dict:
        """Place sell order on Manifold"""
        # For demo purposes - would implement actual trading logic
        return {
            'success': True,
            'order_id': f'manifold_sell_{int(time.time())}',
            'message': f'Demo: Sell {amount} shares of {outcome} at {price}'
        }


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