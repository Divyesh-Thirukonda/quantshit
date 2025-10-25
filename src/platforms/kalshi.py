"""
Kalshi API implementation
"""

from typing import Dict, List

from .base import BaseMarketAPI


class KalshiAPI(BaseMarketAPI):
    """Kalshi prediction market API"""
    
    BASE_URL = "https://api.kalshi.com"
    
    def _get_auth_headers(self) -> Dict[str, str]:
        return {
            'Authorization': f'Bearer {self.api_key}',
            'Content-Type': 'application/json'
        }
    
    def get_recent_markets(self, min_volume: float = 1000) -> List[Dict]:
        """Get recent markets from Kalshi"""
        try:
            # Mock data for demo purposes
            return [
                {
                    'id': 'kalshi_1',
                    'platform': 'kalshi',
                    'title': 'Trump to win 2024 Presidential Election',
                    'yes_price': 0.42,
                    'no_price': 0.58,
                    'volume': 75000,
                    'liquidity': 40000
                },
                {
                    'id': 'kalshi_2',
                    'platform': 'kalshi', 
                    'title': 'Federal Reserve to cut rates in December 2024',
                    'yes_price': 0.78,
                    'no_price': 0.22,
                    'volume': 45000,
                    'liquidity': 20000
                },
                {
                    'id': 'kalshi_3',
                    'platform': 'kalshi',
                    'title': 'S&P 500 to close above 5000 by year end',
                    'yes_price': 0.68,
                    'no_price': 0.32,
                    'volume': 35000,
                    'liquidity': 18000
                },
                {
                    'id': 'kalshi_4',
                    'platform': 'kalshi',
                    'title': 'Bitcoin above $50k on election day',
                    'yes_price': 0.55,
                    'no_price': 0.45,
                    'volume': 28000,
                    'liquidity': 14000
                },
                {
                    'id': 'kalshi_5',
                    'platform': 'kalshi',
                    'title': 'Apple earnings to beat estimates Q4 2024',
                    'yes_price': 0.42,
                    'no_price': 0.58,
                    'volume': 32000,
                    'liquidity': 16000
                }
            ]
        except Exception as e:
            print(f"Kalshi API error: {e}")
            return []
    
    def place_buy_order(self, market_id: str, outcome: str, amount: float, price: float) -> Dict:
        """Place buy order on Kalshi"""
        try:
            # Mock implementation
            return {
                'success': True,
                'order_id': f"kalshi_buy_{market_id}_{outcome}",
                'message': f'Buy order placed: {amount} shares of {outcome} at ${price}'
            }
        except Exception as e:
            return {
                'success': False,
                'message': f'Buy order failed: {str(e)}'
            }
    
    def place_sell_order(self, market_id: str, outcome: str, amount: float, price: float) -> Dict:
        """Place sell order on Kalshi"""
        try:
            # Mock implementation
            return {
                'success': True,
                'order_id': f"kalshi_sell_{market_id}_{outcome}",
                'message': f'Sell order placed: {amount} shares of {outcome} at ${price}'
            }
        except Exception as e:
            return {
                'success': False,
                'message': f'Sell order failed: {str(e)}'
            }
    
    def find_event(self, keyword: str, limit: int = 10) -> List[Dict]:
        """Search for events on Kalshi by keyword"""
        try:
            # In real implementation, this would call Kalshi's search API
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
            print(f"Kalshi search error: {e}")
            return []