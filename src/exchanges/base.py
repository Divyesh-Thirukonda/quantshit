"""
Base exchange client interface.
All exchange clients must implement this interface.
"""

from abc import ABC, abstractmethod
from typing import List, Dict, Any
from ..models import Market, Order
from ..fin_types import Exchange, OrderSide


class BaseExchangeClient(ABC):
    """
    Abstract base class for exchange clients.
    All exchange implementations must inherit from this and implement all methods.
    """

    def __init__(self, api_key: str, exchange: Exchange):
        """
        Initialize the exchange client.

        Args:
            api_key: API key for authentication
            exchange: Exchange enum value
        """
        self.api_key = api_key
        self.exchange = exchange

    @abstractmethod
    def get_markets(
        self, 
        min_volume: float = 0,
        min_liquidity: float = 0,
        max_volume: float = None,
        max_liquidity: float = None
    ) -> List[Market]:
        """
        Fetch available markets from the exchange.

        Args:
            min_volume: Minimum volume filter (in dollars)
            min_liquidity: Minimum liquidity filter (in dollars)
            max_volume: Maximum volume filter (in dollars)
            max_liquidity: Maximum liquidity filter (in dollars)

        Returns:
            List of Market objects
        """
        pass

    @abstractmethod
    def place_order(
        self,
        market_id: str,
        side: OrderSide,
        quantity: int,
        price: float
    ) -> Order:
        """
        Place an order on the exchange.

        Args:
            market_id: Market identifier
            side: BUY or SELL
            quantity: Number of contracts
            price: Limit price

        Returns:
            Order object with execution details
        """
        pass

    @abstractmethod
    def get_order_status(self, order_id: str) -> Dict[str, Any]:
        """
        Get the status of an order.

        Args:
            order_id: Order identifier

        Returns:
            Dict with order status information
        """
        pass

    def _get_auth_headers(self) -> Dict[str, str]:
        """
        Get authentication headers for API requests.
        Override this in subclasses if needed.

        Returns:
            Dict of headers
        """
        return {
            'Authorization': f'Bearer {self.api_key}',
            'Content-Type': 'application/json'
        }
