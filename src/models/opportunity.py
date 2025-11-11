"""
Opportunity model - represents an arbitrage opportunity between exchanges.
Created by matcher, scored by scorer, validated by validator, executed by executor.
"""

from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional

from ..fin_types import Outcome, Price, Quantity, Spread, ProfitPct
from .market import Market


@dataclass
class Opportunity:
    """
    Arbitrage opportunity found between two exchanges.
    Matcher creates these, scorer ranks them, executor acts on them.
    """

    # The matched markets
    market_kalshi: Market  # Market on Kalshi
    market_polymarket: Market  # Equivalent market on Polymarket

    # Opportunity details
    outcome: Outcome  # Which outcome (YES or NO) presents arbitrage
    spread: Spread  # Price difference between exchanges
    expected_profit: float  # Expected profit in dollars after fees
    expected_profit_pct: ProfitPct  # Expected profit as percentage

    # Quality metrics
    confidence_score: float  # How confident markets are equivalent (0-1)

    # Position sizing
    recommended_size: Quantity  # Recommended number of contracts
    max_size: Quantity  # Maximum possible size based on liquidity

    # Timing
    timestamp: datetime = field(default_factory=datetime.now)
    expiry: Optional[datetime] = None  # When opportunity/market expires

    # Execution details (which exchange to buy/sell on)
    buy_exchange: Optional[str] = None  # Where to buy (cheaper price)
    sell_exchange: Optional[str] = None  # Where to sell (higher price)
    buy_price: Optional[Price] = None  # Price to buy at
    sell_price: Optional[Price] = None  # Price to sell at

    def __post_init__(self):
        """
        Validate opportunity data.
        Business logic for setting buy/sell exchanges moved to OpportunityBuilder.
        Single Responsibility: Model only validates its own data.
        """
        if self.confidence_score < 0 or self.confidence_score > 1:
            raise ValueError(f"Confidence score must be 0-1, got {self.confidence_score}")
        if self.spread < 0:
            raise ValueError(f"Spread cannot be negative, got {self.spread}")
        if self.recommended_size <= 0:
            raise ValueError(f"Recommended size must be positive, got {self.recommended_size}")

    @property
    def is_profitable(self) -> bool:
        """Check if opportunity is profitable after fees"""
        return self.expected_profit > 0

    @property
    def profit_per_contract(self) -> float:
        """Profit per contract after fees"""
        return self.expected_profit / self.recommended_size if self.recommended_size > 0 else 0.0

    @property
    def is_expired(self) -> bool:
        """Check if opportunity has expired"""
        if self.expiry is None:
            return False
        return datetime.now() >= self.expiry
