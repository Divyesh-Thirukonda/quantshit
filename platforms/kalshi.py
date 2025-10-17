import requests
import time
from typing import List, Dict

from .base import BaseMarketAPI


class KalshiAPI(BaseMarketAPI):
    """Kalshi API client"""

    def __init__(self, api_key: str = None):
        super().__init__(api_key)
        self.base_url = "https://api.elections.kalshi.com/trade-api/v2"

    def get_recent_markets(self, min_volume: float = 1000) -> List[Dict]:
        """Get recent markets from Kalshi"""
        try:
            url = f"{self.base_url}/markets"
            params = {
                "limit": 1000,  # Get max markets to filter by volume
                "status": "open"  # Only get currently tradeable markets
            }

            response = requests.get(url, params=params, timeout=10)
            response.raise_for_status()

            data = response.json()
            markets = data.get('markets', [])
            filtered_markets = []

            for market in markets:
                # Get 24h volume, fallback to total volume
                volume = float(market.get('volume_24h', 0))
                if volume == 0:
                    volume = float(market.get('volume', 0))

                if volume >= min_volume:
                    # Calculate mid prices from bid/ask spreads
                    yes_bid = float(market.get('yes_bid', 0))
                    yes_ask = float(market.get('yes_ask', 0))
                    no_bid = float(market.get('no_bid', 0))
                    no_ask = float(market.get('no_ask', 0))

                    # Use mid price, or last price as fallback
                    yes_price = (yes_bid + yes_ask) / 2 if (yes_bid + yes_ask) > 0 else float(market.get('last_price', 0.5))
                    no_price = (no_bid + no_ask) / 2 if (no_bid + no_ask) > 0 else (1 - yes_price)

                    filtered_markets.append({
                        'id': market['ticker'],
                        'title': market.get('title', market.get('subtitle', '')),
                        'platform': 'kalshi',
                        'volume': volume,
                        'yes_price': yes_price,
                        'no_price': no_price,
                        'raw_data': market
                    })

            # Sort by volume (client-side since API doesn't support sorting)
            filtered_markets.sort(key=lambda x: x['volume'], reverse=True)

            # Limit to top 50 for consistency with other platforms
            return filtered_markets[:50]

        except Exception as e:
            print(f"Error fetching Kalshi data: {e}")
            return []

    def place_buy_order(self, market_id: str, outcome: str, amount: float, price: float) -> Dict:
        """Place buy order on Kalshi"""
        # For demo purposes - would implement actual trading logic
        # Real implementation would use POST /portfolio/orders endpoint
        return {
            'success': True,
            'order_id': f'kalshi_buy_{int(time.time())}',
            'message': f'Demo: Buy {amount} shares of {outcome} at {price}'
        }

    def place_sell_order(self, market_id: str, outcome: str, amount: float, price: float) -> Dict:
        """Place sell order on Kalshi"""
        # For demo purposes - would implement actual trading logic
        # Real implementation would use POST /portfolio/orders endpoint
        return {
            'success': True,
            'order_id': f'kalshi_sell_{int(time.time())}',
            'message': f'Demo: Sell {amount} shares of {outcome} at {price}'
        }
