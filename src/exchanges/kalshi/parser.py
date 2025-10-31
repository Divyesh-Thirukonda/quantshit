"""
Parser for Kalshi API responses.
Converts Kalshi-specific data formats into our standard Market and Order models.
"""

from datetime import datetime
from typing import Dict, Any

from ...models import Market, Order
from ...types import Exchange, MarketStatus, OrderStatus, OrderSide


def parse_market(event_data: Dict[str, Any], market_data: Dict[str, Any]) -> Market:
    """
    Parse Kalshi event and market data into our Market model.

    Args:
        event_data: Event data from Kalshi API
        market_data: Market data from Kalshi API

    Returns:
        Market object
    """
    # Extract prices (Kalshi uses cents, we use 0-1 range)
    yes_price = market_data.get('yes_bid', 50) / 100.0
    no_price = market_data.get('no_bid', 50) / 100.0

    # Ensure prices sum to ~1.0
    if yes_price + no_price != 1.0:
        no_price = 1.0 - yes_price

    # Extract volume and liquidity
    volume = market_data.get('volume', 0.0)
    liquidity = market_data.get('open_interest', 0.0)

    # Parse expiry date
    expiry = None
    if 'close_time' in event_data:
        try:
            expiry = datetime.fromisoformat(event_data['close_time'].replace('Z', '+00:00'))
        except:
            pass

    # Determine status
    status = MarketStatus.OPEN
    market_status = market_data.get('status', 'open').lower()
    if market_status == 'closed':
        status = MarketStatus.CLOSED
    elif market_status == 'settled':
        status = MarketStatus.SETTLED

    return Market(
        id=market_data.get('ticker', event_data.get('event_ticker', 'unknown')),
        exchange=Exchange.KALSHI,
        title=event_data.get('title', 'Unknown Market'),
        yes_price=yes_price,
        no_price=no_price,
        volume=volume,
        liquidity=liquidity,
        status=status,
        expiry=expiry,
        category=event_data.get('category', None)
    )


def parse_order(
    response_data: Dict[str, Any],
    market_id: str,
    side: OrderSide,
    quantity: int,
    price: float
) -> Order:
    """
    Parse Kalshi order response into our Order model.

    Args:
        response_data: Response from Kalshi order API
        market_id: Market identifier
        side: Order side
        quantity: Order quantity
        price: Order price

    Returns:
        Order object
    """
    order_data = response_data.get('order', {})

    # Parse status
    status_map = {
        'resting': OrderStatus.PENDING,
        'filled': OrderStatus.FILLED,
        'partially_filled': OrderStatus.PARTIAL,
        'canceled': OrderStatus.CANCELLED,
        'rejected': OrderStatus.REJECTED
    }
    status_str = order_data.get('status', 'pending')
    status = status_map.get(status_str, OrderStatus.PENDING)

    # Get filled quantity
    filled_quantity = order_data.get('filled_count', 0)

    # Parse timestamp
    timestamp = datetime.now()
    if 'created_time' in order_data:
        try:
            timestamp = datetime.fromisoformat(order_data['created_time'].replace('Z', '+00:00'))
        except:
            pass

    return Order(
        order_id=order_data.get('order_id', f'kalshi_{datetime.now().timestamp()}'),
        exchange=Exchange.KALSHI,
        market_id=market_id,
        side=side,
        quantity=quantity,
        price=price,
        status=status,
        filled_quantity=filled_quantity,
        timestamp=timestamp
    )
