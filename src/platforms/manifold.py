"""
Manifold Markets API implementation
"""

from typing import List, Dict
from .base import BaseMarketAPI


class ManifoldAPI(BaseMarketAPI):
    """Manifold Markets prediction market API"""
    
    BASE_URL = "https://api.manifold.markets"
    
    def _get_auth_headers(self) -> Dict[str, str]:
        return {
            'Authorization': f'Bearer {self.api_key}',
            'Content-Type': 'application/json'
        }
    
    def get_recent_markets(self, min_volume: float = 1000) -> List[Dict]:
        """Get recent markets from Manifold"""
        try:
            # Mock data for demo purposes
            return [
                {
                    'id': 'manifold_1',
                    'platform': 'manifold',
                    'title': 'Will Donald Trump be elected President in 2024?',
                    'yes_price': 0.63,
                    'no_price': 0.37,
                    'volume': 35000,
                    'liquidity': 18000
                },
                {
                    'id': 'manifold_2',
                    'platform': 'manifold',
                    'title': 'Will the Fed cut interest rates by year-end 2024?',
                    'yes_price': 0.82,
                    'no_price': 0.18,
                    'volume': 22000,
                    'liquidity': 12000
                },
                {
                    'id': 'manifold_3',
                    'platform': 'manifold',
                    'title': 'Will Tesla stock hit $300 before 2025?',
                    'yes_price': 0.35,
                    'no_price': 0.65,
                    'volume': 15000,
                    'liquidity': 8000
                },
                {
                    'id': 'manifold_4',
                    'platform': 'manifold',
                    'title': 'AI breakthrough in autonomous driving by Q1 2025',
                    'yes_price': 0.28,
                    'no_price': 0.72,
                    'volume': 12000,
                    'liquidity': 6000
                },
                {
                    'id': 'manifold_5',
                    'platform': 'manifold',
                    'title': 'Apple to launch VR headset successor in 2025',
                    'yes_price': 0.67,
                    'no_price': 0.33,
                    'volume': 19000,
                    'liquidity': 10000
                }
            ]
        except Exception as e:
            print(f"Manifold API error: {e}")
            return []
    
    def place_buy_order(self, market_id: str, outcome: str, amount: float, price: float) -> Dict:
        """Place buy order on Manifold"""
        try:
            # Mock implementation
            return {
                'success': True,
                'order_id': f"manifold_buy_{market_id}_{outcome}",
                'message': f'Buy order placed: {amount} shares of {outcome} at ${price}'
            }
        except Exception as e:
            return {
                'success': False,
                'message': f'Buy order failed: {str(e)}'
            }
    
    def place_sell_order(self, market_id: str, outcome: str, amount: float, price: float) -> Dict:
        """Place sell order on Manifold"""
        try:
            # Mock implementation
            return {
                'success': True,
                'order_id': f"manifold_sell_{market_id}_{outcome}",
                'message': f'Sell order placed: {amount} shares of {outcome} at ${price}'
            }
        except Exception as e:
            return {
                'success': False,
                'message': f'Sell order failed: {str(e)}'
            }
    
    def find_event(self, keyword: str, limit: int = 10) -> List[Dict]:
        """Search for events on Manifold by keyword"""
        try:
            # In real implementation, this would call Manifold's search API
            # For now, return filtered mock data
            all_markets = self.get_recent_markets(0)  # Get all markets
            
            # Filter by keyword (case insensitive)
            keyword_lower = keyword.lower()
            matching_markets = [
                market for market in all_markets
                if keyword_lower in market['title'].lower()
            ]
            
            return matching_markets[:limit]
        except Exception as e:
            print(f"Manifold search error: {e}")
            return []