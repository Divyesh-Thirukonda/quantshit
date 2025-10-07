"""
Core data models for the backtesting engine
"""

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Optional


class OrderType(Enum):
    """Order types"""
    BUY = "buy"
    SELL = "sell"


class OrderStatus(Enum):
    """Order status"""
    PENDING = "pending"
    FILLED = "filled"
    CANCELLED = "cancelled"
    REJECTED = "rejected"


@dataclass
class Market:
    """
    Represents a prediction market
    
    Attributes:
        id: Unique market identifier
        question: The prediction market question
        current_yes_price: Current price for YES outcome (0-1 or 0-100)
        current_no_price: Current price for NO outcome (0-1 or 0-100)
        resolved: Whether the market has resolved
        resolution: Final outcome (True for YES, False for NO, None if unresolved)
        timestamp: Current timestamp for market data
    """
    id: str
    question: str
    current_yes_price: float
    current_no_price: float
    resolved: bool = False
    resolution: Optional[bool] = None
    timestamp: Optional[datetime] = None
    
    def __post_init__(self):
        if self.timestamp is None:
            self.timestamp = datetime.now()


@dataclass
class Position:
    """
    Represents a position in a prediction market
    
    Attributes:
        market_id: Market identifier
        outcome: Position outcome (True for YES, False for NO)
        shares: Number of shares held
        avg_price: Average purchase price per share
        realized_pnl: Realized profit/loss from closed positions
    """
    market_id: str
    outcome: bool
    shares: float = 0.0
    avg_price: float = 0.0
    realized_pnl: float = 0.0
    
    def unrealized_pnl(self, current_price: float) -> float:
        """Calculate unrealized profit/loss"""
        return self.shares * (current_price - self.avg_price)
    
    def total_pnl(self, current_price: float) -> float:
        """Calculate total profit/loss"""
        return self.realized_pnl + self.unrealized_pnl(current_price)


@dataclass
class Order:
    """
    Represents a trading order
    
    Attributes:
        market_id: Market identifier
        order_type: BUY or SELL
        outcome: Outcome to trade (True for YES, False for NO)
        shares: Number of shares to trade
        price: Limit price for the order
        timestamp: When the order was created
        status: Current order status
        order_id: Unique order identifier
    """
    market_id: str
    order_type: OrderType
    outcome: bool
    shares: float
    price: float
    timestamp: datetime = field(default_factory=datetime.now)
    status: OrderStatus = OrderStatus.PENDING
    order_id: Optional[str] = None
    
    def __post_init__(self):
        if self.order_id is None:
            self.order_id = f"{self.market_id}_{self.timestamp.timestamp()}"


@dataclass
class Trade:
    """
    Represents a completed trade
    
    Attributes:
        order_id: Associated order identifier
        market_id: Market identifier
        order_type: BUY or SELL
        outcome: Outcome traded (True for YES, False for NO)
        shares: Number of shares traded
        price: Execution price
        timestamp: When the trade was executed
        commission: Trading fees/commission
    """
    order_id: str
    market_id: str
    order_type: OrderType
    outcome: bool
    shares: float
    price: float
    timestamp: datetime = field(default_factory=datetime.now)
    commission: float = 0.0
    
    def total_cost(self) -> float:
        """Calculate total cost including commission"""
        base_cost = self.shares * self.price
        if self.order_type == OrderType.BUY:
            return base_cost + self.commission
        else:
            return base_cost - self.commission
