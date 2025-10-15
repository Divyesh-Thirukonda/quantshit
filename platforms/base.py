from typing import List, Dict


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
