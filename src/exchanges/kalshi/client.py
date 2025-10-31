"""
Kalshi API client.
Fetches market data and places orders on Kalshi prediction market.
"""

import requests
from typing import List, Dict, Any
from datetime import datetime

from ..base import BaseExchangeClient
from ...models import Market, Order
from ...types import Exchange, OrderSide, OrderStatus, MarketStatus
from ...utils import get_logger
from .parser import parse_market, parse_order

logger = get_logger(__name__)


class KalshiClient(BaseExchangeClient):
    """Client for Kalshi prediction market API"""

    BASE_URL = "https://api.elections.kalshi.com/trade-api/v2"

    def __init__(self, api_key: str):
        """
        Initialize Kalshi client.

        Args:
            api_key: Kalshi API key (can be empty string for public endpoints)
        """
        super().__init__(api_key, Exchange.KALSHI)
        self.session = requests.Session()
        if api_key:
            self.session.headers.update(self._get_auth_headers())

    def get_markets(self, min_volume: float = 0) -> List[Market]:
        """
        Fetch available markets from Kalshi.

        Args:
            min_volume: Minimum volume filter (in dollars)

        Returns:
            List of Market objects
        """
        try:
            logger.info(f"Fetching markets from Kalshi (min_volume: ${min_volume})")

            # Fetch events (markets on Kalshi are called "events")
            url = f"{self.BASE_URL}/events"
            params = {
                'status': 'open',
                'limit': 200  # Fetch up to 200 markets
            }

            response = self.session.get(url, params=params, timeout=10)
            response.raise_for_status()
            data = response.json()

            markets = []
            events = data.get('events', [])

            for event_data in events:
                # Get market details for each event
                try:
                    market = self._fetch_market_details(event_data)
                    if market and market.volume >= min_volume:
                        markets.append(market)
                except Exception as e:
                    logger.warning(f"Failed to parse Kalshi market: {e}")
                    continue

            logger.info(f"Fetched {len(markets)} markets from Kalshi")
            return markets

        except requests.exceptions.RequestException as e:
            logger.error(f"Kalshi API request failed: {e}")
            return []
        except Exception as e:
            logger.error(f"Unexpected error fetching Kalshi markets: {e}")
            return []

    def _fetch_market_details(self, event_data: Dict[str, Any]) -> Market:
        """
        Fetch detailed market information for an event.

        Args:
            event_data: Event data from Kalshi API

        Returns:
            Market object
        """
        # Get the first market for this event (events can have multiple markets)
        markets = event_data.get('markets', [])
        if not markets:
            return None

        # Use the first market
        market_data = markets[0]

        # Parse into our Market model
        return parse_market(event_data, market_data)

    def place_order(
        self,
        market_id: str,
        side: OrderSide,
        quantity: int,
        price: float
    ) -> Order:
        """
        Place an order on Kalshi.

        Args:
            market_id: Kalshi market ticker
            side: BUY or SELL
            quantity: Number of contracts
            price: Limit price (in cents, 1-99)

        Returns:
            Order object
        """
        try:
            logger.info(f"Placing Kalshi order: {side.value} {quantity} contracts @ ${price}")

            url = f"{self.BASE_URL}/orders"

            # Convert our price (0.0-1.0) to Kalshi cents (1-99)
            price_cents = int(price * 100)

            payload = {
                'ticker': market_id,
                'action': 'buy' if side == OrderSide.BUY else 'sell',
                'count': quantity,
                'type': 'limit',
                'yes_price' if side == OrderSide.BUY else 'no_price': price_cents
            }

            response = self.session.post(url, json=payload, timeout=10)
            response.raise_for_status()
            data = response.json()

            # Parse response into Order object
            return parse_order(data, market_id, side, quantity, price)

        except requests.exceptions.RequestException as e:
            logger.error(f"Kalshi order placement failed: {e}")
            # Return failed order
            return Order(
                order_id=f"kalshi_failed_{datetime.now().timestamp()}",
                exchange=Exchange.KALSHI,
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
            order_id: Kalshi order ID

        Returns:
            Dict with order status information
        """
        try:
            url = f"{self.BASE_URL}/orders/{order_id}"
            response = self.session.get(url, timeout=10)
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            logger.error(f"Failed to get Kalshi order status: {e}")
            return {'error': str(e)}

    def _get_auth_headers(self) -> Dict[str, str]:
        """Get Kalshi authentication headers"""
        if not self.api_key:
            return {}

        return {
            'Authorization': f'Bearer {self.api_key}',
            'Content-Type': 'application/json'
        }
