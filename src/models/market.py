"""
Market model - normalized representation of a prediction market.
Works for both Kalshi and Polymarket by standardizing their different formats.
"""

from dataclasses import dataclass
from datetime import datetime
from typing import Optional

from ..types import Exchange, MarketStatus, Price, Volume


@dataclass
class Market:
    """
    Normalized market representation across all exchanges.
    Parsers convert exchange-specific formats into this standard structure.
    """

    # Identification
    id: str  # Unique identifier on the exchange
    exchange: Exchange  # Which exchange this market is from
    title: str  # Market question/title

    # Pricing
    yes_price: Price  # Current YES price (0.0 to 1.0)
    no_price: Price  # Current NO price (0.0 to 1.0)

    # Market metrics
    volume: Volume  # Total trading volume
    liquidity: Volume  # Available liquidity

    # Market lifecycle
    status: MarketStatus  # OPEN, CLOSED, or SETTLED
    expiry: Optional[datetime] = None  # When market closes/resolves

    # Optional metadata
    category: Optional[str] = None  # Market category (politics, sports, etc.)

    def __post_init__(self):
        """Validate market data"""
        if not (0 <= self.yes_price <= 1):
            raise ValueError(f"YES price must be between 0 and 1, got {self.yes_price}")
        if not (0 <= self.no_price <= 1):
            raise ValueError(f"NO price must be between 0 and 1, got {self.no_price}")
        if self.volume < 0:
            raise ValueError(f"Volume must be non-negative, got {self.volume}")
        if self.liquidity < 0:
            raise ValueError(f"Liquidity must be non-negative, got {self.liquidity}")

    @property
    def spread(self) -> float:
        """Calculate bid-ask spread (deviation from perfect market)"""
        # In a perfect market, yes_price + no_price = 1.0
        return abs((self.yes_price + self.no_price) - 1.0)

    @property
    def is_open(self) -> bool:
        """Check if market is open for trading"""
        return self.status == MarketStatus.OPEN
