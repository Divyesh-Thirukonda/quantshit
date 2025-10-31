"""
Order model - represents a buy/sell order placed on an exchange.
Created by executor, tracked by monitor, stored in DB.
"""

from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional

from ..types import Exchange, OrderSide, OrderStatus, Price, Quantity, Outcome


@dataclass
class Order:
    """
    Standardized order representation.
    One definition used across all components.
    """

    # Identification
    id: str  # Our internal order ID
    platform_order_id: Optional[str] = None  # Exchange's order ID (after placement)

    # Order details
    exchange: Exchange  # Which exchange
    market_id: str  # Which market
    outcome: Outcome  # YES or NO
    side: OrderSide  # BUY or SELL

    # Quantities and pricing
    quantity: Quantity  # Total number of contracts
    price: Price  # Limit price per contract
    filled_quantity: Quantity = 0  # How many contracts filled
    average_fill_price: Price = 0.0  # Average price of fills

    # Status and timing
    status: OrderStatus = OrderStatus.PENDING
    timestamp: datetime = field(default_factory=datetime.now)
    filled_at: Optional[datetime] = None

    # Fees and costs
    fees: float = 0.0  # Total fees paid

    def __post_init__(self):
        """Validate order data"""
        if self.quantity <= 0:
            raise ValueError(f"Quantity must be positive, got {self.quantity}")
        if not (0 <= self.price <= 1):
            raise ValueError(f"Price must be between 0 and 1, got {self.price}")
        if self.filled_quantity < 0:
            raise ValueError(f"Filled quantity cannot be negative, got {self.filled_quantity}")
        if self.filled_quantity > self.quantity:
            raise ValueError(f"Filled quantity ({self.filled_quantity}) exceeds total quantity ({self.quantity})")

    @property
    def is_filled(self) -> bool:
        """Check if order is completely filled"""
        return self.status == OrderStatus.FILLED

    @property
    def is_partial(self) -> bool:
        """Check if order is partially filled"""
        return self.status == OrderStatus.PARTIAL

    @property
    def remaining_quantity(self) -> Quantity:
        """Get remaining unfilled quantity"""
        return self.quantity - self.filled_quantity

    @property
    def total_cost(self) -> float:
        """Calculate total cost including fees"""
        return (self.filled_quantity * self.average_fill_price) + self.fees

    @property
    def fill_percentage(self) -> float:
        """Percentage of order filled (0-100)"""
        return (self.filled_quantity / self.quantity * 100) if self.quantity > 0 else 0.0
