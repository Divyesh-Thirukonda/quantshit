"""
Position model - represents current holdings in a market.
Tracked by monitor, updated by executor, stored in DB.
"""

from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional

from ..fin_types import Exchange, Outcome, Price, Quantity


@dataclass
class Position:
    """
    Represents an open position in a market.
    Monitor tracks positions, executor updates them. Shared structure.
    """

    # Identification
    position_id: str  # Unique position ID
    market_id: str  # Which market
    exchange: Exchange  # Which exchange

    # Position details
    outcome: Outcome  # YES or NO (what we're long on)
    quantity: Quantity  # Number of contracts held
    avg_entry_price: Price  # Average price we bought at

    # Current state
    current_price: Price  # Current market price
    timestamp: datetime = field(default_factory=datetime.now)

    # Optional metadata
    total_cost: float = 0.0  # Total cost including fees
    target_exit_price: Optional[Price] = None  # When to close position

    def __post_init__(self):
        """Validate position data"""
        if self.quantity <= 0:
            raise ValueError(f"Quantity must be positive, got {self.quantity}")
        if not (0 <= self.avg_entry_price <= 1):
            raise ValueError(f"Entry price must be between 0 and 1, got {self.avg_entry_price}")
        if not (0 <= self.current_price <= 1):
            raise ValueError(f"Current price must be between 0 and 1, got {self.current_price}")

    @property
    def market_value(self) -> float:
        """Current market value of position"""
        return self.quantity * self.current_price

    @property
    def unrealized_pnl(self) -> float:
        """Unrealized profit/loss in dollars"""
        cost = self.total_cost if self.total_cost > 0 else (self.quantity * self.avg_entry_price)
        return self.market_value - cost

    @property
    def unrealized_pnl_pct(self) -> float:
        """Unrealized P&L as percentage"""
        cost = self.total_cost if self.total_cost > 0 else (self.quantity * self.avg_entry_price)
        return (self.unrealized_pnl / cost * 100) if cost > 0 else 0.0

    @property
    def is_profitable(self) -> bool:
        """Check if position is currently profitable"""
        return self.unrealized_pnl > 0

    @property
    def potential_max_profit(self) -> float:
        """Maximum possible profit if price goes to 1.0"""
        max_value = self.quantity * 1.0
        cost = self.total_cost if self.total_cost > 0 else (self.quantity * self.avg_entry_price)
        return max_value - cost
