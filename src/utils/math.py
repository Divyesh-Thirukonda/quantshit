"""
Mathematical calculations used throughout the application.
Reused in scorer, executor, monitor - one implementation.
"""

from typing import Tuple
from ..types import Price, Quantity, Probability


def calculate_profit(
    buy_price: Price,
    sell_price: Price,
    quantity: Quantity,
    buy_fee_pct: float = 0.0,
    sell_fee_pct: float = 0.0
) -> float:
    """
    Calculate net profit from an arbitrage trade after fees.

    Args:
        buy_price: Price paid to buy contracts
        sell_price: Price received from selling contracts
        quantity: Number of contracts
        buy_fee_pct: Fee percentage on buy side (e.g., 0.007 for 0.7%)
        sell_fee_pct: Fee percentage on sell side

    Returns:
        Net profit in dollars after all fees
    """
    # Cost to buy (including fees)
    buy_cost = quantity * buy_price * (1 + buy_fee_pct)

    # Revenue from selling (after fees)
    sell_revenue = quantity * sell_price * (1 - sell_fee_pct)

    # Net profit
    return sell_revenue - buy_cost


def price_to_probability(price: Price) -> Probability:
    """
    Convert a prediction market price to implied probability.
    In prediction markets, price typically equals probability.

    Args:
        price: Market price (0.0 to 1.0)

    Returns:
        Implied probability (0.0 to 1.0)
    """
    # In binary prediction markets, price IS probability
    # E.g., price of 0.65 means 65% probability
    if not (0 <= price <= 1):
        raise ValueError(f"Price must be between 0 and 1, got {price}")
    return price


def probability_to_price(prob: Probability) -> Price:
    """
    Convert probability back to market price.
    Reverse of price_to_probability.

    Args:
        prob: Probability (0.0 to 1.0)

    Returns:
        Market price (0.0 to 1.0)
    """
    if not (0 <= prob <= 1):
        raise ValueError(f"Probability must be between 0 and 1, got {prob}")
    return prob


def calculate_implied_odds(yes_price: Price, no_price: Price) -> Tuple[float, float]:
    """
    Calculate implied odds from YES and NO prices.
    Useful for detecting arbitrage opportunities within a single market.

    Args:
        yes_price: Price of YES outcome
        no_price: Price of NO outcome

    Returns:
        Tuple of (yes_odds, no_odds) as decimals (e.g., 2.0 = 2:1)
    """
    # Implied odds = 1 / probability
    yes_prob = price_to_probability(yes_price)
    no_prob = price_to_probability(no_price)

    # Avoid division by zero
    yes_odds = 1.0 / yes_prob if yes_prob > 0 else float('inf')
    no_odds = 1.0 / no_prob if no_prob > 0 else float('inf')

    return (yes_odds, no_odds)


def kelly_criterion(
    win_probability: Probability,
    win_amount: float,
    loss_amount: float,
    kelly_fraction: float = 0.25
) -> float:
    """
    Calculate optimal position size using Kelly Criterion.
    Conservative version uses fractional Kelly (e.g., 0.25 = quarter Kelly).

    Args:
        win_probability: Probability of winning (0-1)
        win_amount: Amount won if successful
        loss_amount: Amount lost if unsuccessful (positive number)
        kelly_fraction: Fraction of Kelly to use (0-1, lower is more conservative)

    Returns:
        Recommended position size as fraction of bankroll (0-1)
    """
    if not (0 <= win_probability <= 1):
        raise ValueError(f"Win probability must be 0-1, got {win_probability}")

    loss_probability = 1 - win_probability

    # Kelly formula: (p * b - q) / b
    # where p = win prob, q = loss prob, b = win/loss ratio
    if loss_amount == 0:
        return 0.0

    win_loss_ratio = win_amount / loss_amount

    kelly = (win_probability * win_loss_ratio - loss_probability) / win_loss_ratio

    # Apply fractional Kelly for risk management
    kelly = max(0.0, kelly * kelly_fraction)

    # Cap at 100% of bankroll
    return min(1.0, kelly)


def calculate_spread_percentage(price_a: Price, price_b: Price) -> float:
    """
    Calculate percentage spread between two prices.

    Args:
        price_a: First price
        price_b: Second price

    Returns:
        Absolute percentage difference
    """
    return abs(price_a - price_b) / max(price_a, price_b) if max(price_a, price_b) > 0 else 0.0
