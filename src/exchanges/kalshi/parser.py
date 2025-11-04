"""
Parser for Kalshi API responses.
Converts Kalshi-specific data formats into our standard Market and Order models.
"""

from datetime import datetime
from typing import Dict, Any

from ...models import Market, Order
from ...types import Exchange, MarketStatus, OrderStatus, OrderSide


def parse_market(market_data: Dict[str, Any]) -> Market:
    """
    Parse Kalshi market data into our Market model.

    Args:
        market_data: Market data from Kalshi /markets API

    Returns:
        Market object
    """
    # Extract prices (Kalshi uses cents 0-100, we use 0.0-1.0 range)
    # Use mid-price between bid and ask for better accuracy
    yes_bid = market_data.get('yes_bid', 50)
    yes_ask = market_data.get('yes_ask', 50)
    yes_price = ((yes_bid + yes_ask) / 2.0) / 100.0

    no_bid = market_data.get('no_bid', 50)
    no_ask = market_data.get('no_ask', 50)
    no_price = ((no_bid + no_ask) / 2.0) / 100.0

    # Ensure prices sum to ~1.0 (adjust if needed)
    if abs(yes_price + no_price - 1.0) > 0.01:
        no_price = 1.0 - yes_price

    # Extract volume (convert to dollars: volume * notional_value / 100)
    volume_contracts = market_data.get('volume', 0)
    notional_value = market_data.get('notional_value', 100)  # Usually 100 cents = $1
    volume = (volume_contracts * notional_value) / 100.0

    # Extract liquidity (already in dollars in liquidity_dollars field)
    liquidity = float(market_data.get('liquidity_dollars', '0').replace('$', ''))

    # Parse expiry date
    expiry = None
    if 'close_time' in market_data:
        try:
            expiry = datetime.fromisoformat(market_data['close_time'].replace('Z', '+00:00'))
        except:
            pass

    # Determine status
    status = MarketStatus.OPEN
    market_status = market_data.get('status', 'active').lower()
    if market_status == 'active':
        status = MarketStatus.OPEN
    elif market_status == 'closed':
        status = MarketStatus.CLOSED
    elif market_status == 'settled' or market_status == 'finalized':
        status = MarketStatus.SETTLED

    # Extract category from event ticker if available
    category = market_data.get('category')

    return Market(
        id=market_data.get('ticker', 'unknown'),
        exchange=Exchange.KALSHI,
        title=market_data.get('title', 'Unknown Market'),
        yes_price=yes_price,
        no_price=no_price,
        volume=volume,
        liquidity=liquidity,
        status=status,
        expiry=expiry,
        category=category
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
