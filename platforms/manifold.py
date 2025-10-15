import requests
import time
from typing import List, Dict

from .base import BaseMarketAPI


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
