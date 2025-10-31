"""
Universal type definitions used across the entire application.
Single source of truth for types - every module imports from here.
"""

from enum import Enum
from typing import TypeAlias


# Exchange/Platform Enums
class Exchange(Enum):
    """Supported prediction market exchanges"""
    KALSHI = "kalshi"
    POLYMARKET = "polymarket"


# Order Enums
class OrderSide(Enum):
    """Order side - buy or sell"""
    BUY = "buy"
    SELL = "sell"


class OrderStatus(Enum):
    """Order execution status"""
    PENDING = "pending"
    FILLED = "filled"
    PARTIAL = "partial"
    CANCELLED = "cancelled"
    REJECTED = "rejected"


# Market Enums
class MarketStatus(Enum):
    """Market lifecycle status"""
    OPEN = "open"
    CLOSED = "closed"
    SETTLED = "settled"


class Outcome(Enum):
    """Prediction market outcomes"""
    YES = "YES"
    NO = "NO"


# Type Aliases for clarity
Price: TypeAlias = float  # Price of a contract (0.0 to 1.0 typically)
Quantity: TypeAlias = int  # Number of contracts
Probability: TypeAlias = float  # Probability (0.0 to 1.0)
Volume: TypeAlias = float  # Trading volume
Spread: TypeAlias = float  # Price difference between exchanges
ProfitPct: TypeAlias = float  # Profit percentage
