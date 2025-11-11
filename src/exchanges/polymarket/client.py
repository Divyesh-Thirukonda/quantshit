"""
Polymarket API client.
Fetches market data and places orders on Polymarket prediction market.
"""

import requests
from typing import List, Dict, Any
from datetime import datetime

from ..base import BaseExchangeClient
from ...models import Market, Order
from ...fin_types import Exchange, OrderSide, OrderStatus
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

    def get_markets(
        self, 
        min_volume: float = 0,
        min_liquidity: float = 0,
        max_volume: float = None,
        max_liquidity: float = None
    ) -> List[Market]:
        """
        Fetch available markets from Polymarket CLOB API using cursor pagination.

        Args:
            min_volume: Minimum volume filter (in dollars)
            min_liquidity: Minimum liquidity filter (in dollars)
            max_volume: Maximum volume filter (in dollars)
            max_liquidity: Maximum liquidity filter (in dollars)

        Returns:
            List of Market objects
            
        Note:
            Volume/liquidity filters are sent to the API but may not be supported
            on the public endpoint. The API will return all markets regardless of
            these filters. The CLOB API also doesn't return volume/liquidity data
            in the response, so Market objects will have volume=0 and liquidity=0.
        """
        try:
            logger.info(
                f"Fetching markets from Polymarket "
                f"(volume: ${min_volume:,.0f}-{max_volume if max_volume else '∞'}, "
                f"liquidity: ${min_liquidity:,.0f}-{max_liquidity if max_liquidity else '∞'})"
            )

            markets = []
            next_cursor = ""  # Empty string means start from beginning
            page = 1
            total_fetched = 0

            # Use CLOB API for market data
            url = f"{self.BASE_URL}/markets"

            # Paginate through all available markets using cursor
            while True:
                params = {'limit': 1000}  # CLOB API supports up to 1000 per page
                
                # Add API-level filters to reduce data transfer
                if min_volume > 0:
                    params['volume_num_min'] = min_volume
                if max_volume:
                    params['volume_num_max'] = max_volume
                if min_liquidity > 0:
                    params['liquidity_num_min'] = min_liquidity
                if max_liquidity:
                    params['liquidity_num_max'] = max_liquidity
                
                if next_cursor:
                    params['next_cursor'] = next_cursor

                logger.debug(f"Fetching Polymarket page {page} (cursor: {next_cursor or 'initial'})")

                response = requests.get(url, params=params, timeout=10)
                response.raise_for_status()
                data = response.json()

                # CLOB API returns dict with 'data', 'next_cursor', 'count', 'limit'
                market_list = data.get('data', [])
                total_fetched += len(market_list)
                next_cursor = data.get('next_cursor', '')

                logger.debug(f"Page {page}: Received {len(market_list)} markets (next_cursor: {next_cursor})")

                # Parse markets from this page (API has already filtered by volume/liquidity)
                for market_data in market_list:
                    try:
                        market = parse_market(market_data)
                        if market:
                            markets.append(market)
                    except Exception as e:
                        logger.warning(f"Failed to parse Polymarket market: {e}")
                        continue

                # Break if we've reached the end ('LTE=' means end of pagination)
                if not next_cursor or next_cursor == 'LTE=' or len(market_list) == 0:
                    break

                page += 1

            logger.info(f"Fetched {len(markets)} markets from Polymarket across {page} pages (total raw: {total_fetched})")
            return markets

        except requests.exceptions.RequestException as e:
            logger.error(f"Polymarket API request failed: {e}")
            return []
        except Exception as e:
            logger.error(f"Unexpected error fetching Polymarket markets: {e}", exc_info=True)
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
