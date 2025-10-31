"""
Polymarket API client.
Fetches market data and places orders on Polymarket prediction market.
"""

import requests
from typing import List, Dict, Any
from datetime import datetime

from ..base import BaseExchangeClient
from ...models import Market, Order
from ...types import Exchange, OrderSide, OrderStatus
from ...utils import get_logger
from .parser import parse_market, parse_order

logger = get_logger(__name__)


class PolymarketClient(BaseExchangeClient):
    """Client for Polymarket prediction market API"""

    # Polymarket uses CLOB API
    BASE_URL = "https://clob.polymarket.com"
    GAMMA_URL = "https://gamma-api.polymarket.com"

    def __init__(self, api_key: str):
        """
        Initialize Polymarket client.

        Args:
            api_key: Polymarket API key (can be empty for public data)
        """
        super().__init__(api_key, Exchange.POLYMARKET)
        self.session = requests.Session()
        if api_key:
            self.session.headers.update(self._get_auth_headers())

    def get_markets(self, min_volume: float = 0) -> List[Market]:
        """
        Fetch available markets from Polymarket.

        Args:
            min_volume: Minimum volume filter (in dollars)

        Returns:
            List of Market objects
        """
        try:
            logger.info(f"Fetching markets from Polymarket (min_volume: ${min_volume})")

            # Use Gamma API for market data (public endpoint)
            url = f"{self.GAMMA_URL}/markets"
            params = {
                'limit': 100,
                'active': 'true'
            }

            response = requests.get(url, params=params, timeout=10)
            response.raise_for_status()
            data = response.json()

            markets = []

            # Polymarket returns an array of markets
            market_list = data if isinstance(data, list) else data.get('markets', [])

            for market_data in market_list:
                try:
                    market = parse_market(market_data)
                    if market and market.volume >= min_volume:
                        markets.append(market)
                except Exception as e:
                    logger.warning(f"Failed to parse Polymarket market: {e}")
                    continue

            logger.info(f"Fetched {len(markets)} markets from Polymarket")
            return markets

        except requests.exceptions.RequestException as e:
            logger.error(f"Polymarket API request failed: {e}")
            return []
        except Exception as e:
            logger.error(f"Unexpected error fetching Polymarket markets: {e}")
            return []

    def place_order(
        self,
        market_id: str,
        side: OrderSide,
        quantity: int,
        price: float
    ) -> Order:
        """
        Place an order on Polymarket.

        Args:
            market_id: Polymarket condition ID (token ID)
            side: BUY or SELL
            quantity: Number of contracts
            price: Limit price (0.0 to 1.0)

        Returns:
            Order object
        """
        try:
            logger.info(f"Placing Polymarket order: {side.value} {quantity} contracts @ ${price}")

            # Polymarket uses CLOB (Central Limit Order Book)
            url = f"{self.BASE_URL}/order"

            payload = {
                'market': market_id,
                'price': str(price),
                'size': str(quantity),
                'side': 'BUY' if side == OrderSide.BUY else 'SELL'
            }

            response = self.session.post(url, json=payload, timeout=10)
            response.raise_for_status()
            data = response.json()

            # Parse response into Order object
            return parse_order(data, market_id, side, quantity, price)

        except requests.exceptions.RequestException as e:
            logger.error(f"Polymarket order placement failed: {e}")
            # Return failed order
            return Order(
                order_id=f"polymarket_failed_{datetime.now().timestamp()}",
                exchange=Exchange.POLYMARKET,
                market_id=market_id,
                side=side,
                quantity=quantity,
                price=price,
                status=OrderStatus.REJECTED,
                filled_quantity=0,
                timestamp=datetime.now()
            )

    def get_order_status(self, order_id: str) -> Dict[str, Any]:
        """
        Get the status of an order.

        Args:
            order_id: Polymarket order ID

        Returns:
            Dict with order status information
        """
        try:
            url = f"{self.BASE_URL}/order/{order_id}"
            response = self.session.get(url, timeout=10)
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            logger.error(f"Failed to get Polymarket order status: {e}")
            return {'error': str(e)}

    def _get_auth_headers(self) -> Dict[str, str]:
        """Get Polymarket authentication headers"""
        if not self.api_key:
            return {}

        # Polymarket uses API key in header
        return {
            'Authorization': self.api_key,
            'Content-Type': 'application/json'
        }
