import requests
import time
from typing import List, Dict

from .base import BaseMarketAPI


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
