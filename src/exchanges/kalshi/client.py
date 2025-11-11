"""
Kalshi API client.
Fetches market data and places orders on Kalshi prediction market.
"""

from datetime import datetime
from typing import Any, Dict, List

import requests

from ...models import Market, Order
from ...fin_types import Exchange, MarketStatus, OrderSide, OrderStatus
from ...utils import get_logger
from ..base import BaseExchangeClient
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

    def get_markets(
        self, 
        min_volume: float = 0,
        min_liquidity: float = 0,
        max_volume: float = None,
        max_liquidity: float = None
    ) -> List[Market]:
        """
        Fetch available markets from Kalshi using cursor pagination.

        Args:
            min_volume: Minimum volume filter (in dollars)
            min_liquidity: Minimum liquidity filter (in dollars)
            max_volume: Maximum volume filter (in dollars)
            max_liquidity: Maximum liquidity filter (in dollars)

        Returns:
            List of Market objects
            
        Note:
            Kalshi API doesn't support volume/liquidity filters at the API level,
            so filtering is done client-side after fetching all markets.
        """
        try:
            logger.info(
                f"Fetching markets from Kalshi "
                f"(volume: ${min_volume:,.0f}-{max_volume if max_volume else '∞'}, "
                f"liquidity: ${min_liquidity:,.0f}-{max_liquidity if max_liquidity else '∞'})"
            )

            markets = []
            cursor = None
            page = 1
            total_fetched = 0

            # Fetch markets directly from /markets endpoint
            url = f"{self.BASE_URL}/markets"

            # Paginate through all available markets
            while True:
                params = {"status": "open", "limit": 1000}  # Max per page

                # Add cursor for pagination if available
                if cursor:
                    params["cursor"] = cursor

                logger.debug(
                    f"Fetching Kalshi page {page} (cursor: {cursor or 'initial'})"
                )

                response = self.session.get(url, params=params, timeout=10)
                response.raise_for_status()
                data = response.json()

                market_list = data.get("markets", [])
                total_fetched += len(market_list)

                logger.debug(
                    f"Page {page}: Received {len(market_list)} markets from Kalshi API"
                )

                # Parse markets from this page
                for market_data in market_list:
                    try:
                        market = parse_market(market_data)
                        if market:
                            # Apply client-side filters
                            if market.volume < min_volume:
                                continue
                            if max_volume and market.volume > max_volume:
                                continue
                            if market.liquidity < min_liquidity:
                                continue
                            if max_liquidity and market.liquidity > max_liquidity:
                                continue
                            markets.append(market)
                    except Exception as e:
                        logger.warning(f"Failed to parse Kalshi market: {e}")
                        continue

                # Check for next page cursor
                cursor = data.get("cursor")

                # Break if no more pages or no markets returned
                if not cursor or len(market_list) == 0:
                    break

                page += 1

            logger.info(
                f"Fetched {len(markets)} markets from Kalshi across {page} pages (total raw: {total_fetched}, after filters)"
            )
            return markets

        except requests.exceptions.RequestException as e:
            logger.error(f"Kalshi API request failed: {e}")
            return []
        except Exception as e:
            logger.error(
                f"Unexpected error fetching Kalshi markets: {e}", exc_info=True
            )
            return []

    def place_order(
        self, market_id: str, side: OrderSide, quantity: int, price: float
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
            logger.info(
                f"Placing Kalshi order: {side.value} {quantity} contracts @ ${price}"
            )

            url = f"{self.BASE_URL}/orders"

            # Convert our price (0.0-1.0) to Kalshi cents (1-99)
            price_cents = int(price * 100)

            payload = {
                "ticker": market_id,
                "action": "buy" if side == OrderSide.BUY else "sell",
                "count": quantity,
                "type": "limit",
                "yes_price" if side == OrderSide.BUY else "no_price": price_cents,
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
                timestamp=datetime.now(),
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
            return {"error": str(e)}

    def _get_auth_headers(self) -> Dict[str, str]:
        """Get Kalshi authentication headers"""
        if not self.api_key:
            return {}

        return {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
        }
