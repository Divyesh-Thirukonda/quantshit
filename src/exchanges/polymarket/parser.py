"""
Parser for Polymarket API responses.
Converts Polymarket-specific data formats into our standard Market and Order models.
"""

from datetime import datetime
from typing import Dict, Any

from ...models import Market, Order
from ...fin_types import Exchange, MarketStatus, OrderStatus, OrderSide


def parse_market(market_data: Dict[str, Any]) -> Market:
    """
    Parse Polymarket market data into our Market model.

    Args:
        market_data: Market data from Polymarket API

    Returns:
        Market object
    """
    # Polymarket markets have tokens for YES and NO outcomes
    # We need to extract the best bid/ask prices

    # Get YES token (usually the first token, or has outcome "Yes")
    tokens = market_data.get('tokens', [])

    # Try to find YES and NO tokens
    yes_price = 0.5
    no_price = 0.5

    if tokens:
        # Polymarket typically has 2 tokens per market (YES and NO)
        for token in tokens:
            outcome = token.get('outcome', '').lower()
            if 'yes' in outcome or token.get('token_id', '') == market_data.get('yes_token_id', ''):
                # Get best bid price for YES
                yes_price = float(token.get('price', 0.5))
            elif 'no' in outcome or token.get('token_id', '') == market_data.get('no_token_id', ''):
                # Get best bid price for NO
                no_price = float(token.get('price', 0.5))

    # Alternative: use outcomeprices if available
    if 'outcomePrices' in market_data:
        prices = market_data['outcomePrices']
        if isinstance(prices, list) and len(prices) >= 2:
            yes_price = float(prices[0])
            no_price = float(prices[1])

    # Ensure prices are in valid range and sum to ~1.0
    yes_price = max(0.01, min(0.99, yes_price))
    no_price = max(0.01, min(0.99, no_price))

    # If they don't sum to 1.0, adjust
    total = yes_price + no_price
    if abs(total - 1.0) > 0.1:  # If significantly off
        yes_price = yes_price / total
        no_price = no_price / total

    # Extract volume and liquidity (may not be present in CLOB API)
    volume = 0.0
    liquidity = 0.0
    
    # Try different field names for volume
    if 'volume' in market_data:
        volume = float(market_data['volume'])
    elif 'volumeNum' in market_data:
        volume = float(market_data['volumeNum'])
    
    # Try different field names for liquidity  
    if 'liquidity' in market_data:
        liquidity = float(market_data['liquidity'])
    elif 'liquidityNum' in market_data:
        liquidity = float(market_data['liquidityNum'])

    # Parse expiry/end date
    expiry = None
    end_date_str = market_data.get('end_date_iso') or market_data.get('endDate')
    if end_date_str:
        try:
            expiry = datetime.fromisoformat(end_date_str.replace('Z', '+00:00'))
        except:
            pass

    # Determine status
    status = MarketStatus.OPEN
    closed = market_data.get('closed', False)
    active = market_data.get('active', True)

    if closed or not active:
        status = MarketStatus.CLOSED

    # Get market ID (condition_id or market_id)
    market_id = market_data.get('condition_id') or market_data.get('id') or market_data.get('market_id', 'unknown')

    return Market(
        id=str(market_id),
        exchange=Exchange.POLYMARKET,
        title=market_data.get('question', market_data.get('title', 'Unknown Market')),
        yes_price=yes_price,
        no_price=no_price,
        volume=volume,
        liquidity=liquidity,
        status=status,
        expiry=expiry,
        category=market_data.get('category', None)
    )


def parse_order(
    response_data: Dict[str, Any],
    market_id: str,
    side: OrderSide,
    quantity: int,
    price: float
) -> Order:
    """
    Parse Polymarket order response into our Order model.

    Args:
        response_data: Response from Polymarket order API
        market_id: Market identifier
        side: Order side
        quantity: Order quantity
        price: Order price

    Returns:
        Order object
    """
    # Parse status
    status_map = {
        'open': OrderStatus.PENDING,
        'matched': OrderStatus.FILLED,
        'partial': OrderStatus.PARTIAL,
        'cancelled': OrderStatus.CANCELLED,
        'rejected': OrderStatus.REJECTED
    }

    status_str = response_data.get('status', 'open')
    status = status_map.get(status_str, OrderStatus.PENDING)

    # Get filled quantity
    filled_quantity = int(response_data.get('filled_size', 0))

    # Parse timestamp
    timestamp = datetime.now()
    created_at = response_data.get('created_at')
    if created_at:
        try:
            timestamp = datetime.fromisoformat(created_at.replace('Z', '+00:00'))
        except:
            pass

    return Order(
        order_id=response_data.get('order_id', f'polymarket_{datetime.now().timestamp()}'),
        exchange=Exchange.POLYMARKET,
        market_id=market_id,
        side=side,
        quantity=quantity,
        price=price,
        status=status,
        filled_quantity=filled_quantity,
        timestamp=timestamp
    )
