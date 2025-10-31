"""Core enums for the prediction market arbitrage system."""

from enum import Enum, auto


class Platform(Enum):
    """Supported prediction market platforms."""
    KALSHI = "kalshi"
    POLYMARKET = "polymarket"


class Outcome(Enum):
    """Possible outcomes for binary markets."""
    YES = "yes"
    NO = "no"


class OrderType(Enum):
    """Types of orders that can be placed."""
    MARKET = "market"
    LIMIT = "limit"
    STOP_LOSS = "stop_loss"


class OrderStatus(Enum):
    """Status of placed orders."""
    PENDING = "pending"
    FILLED = "filled"
    PARTIAL = "partial"
    CANCELLED = "cancelled"
    FAILED = "failed"


class RiskLevel(Enum):
    """Risk levels for position sizing."""
    LOW = auto()
    MEDIUM = auto()
    HIGH = auto()


class StrategyType(Enum):
    """Types of trading strategies."""
    ARBITRAGE = "arbitrage"
    MEAN_REVERSION = "mean_reversion"
    CORRELATION = "correlation"
    INSIDER_INFO = "insider_info"


class MarketStatus(Enum):
    """Status of prediction markets."""
    ACTIVE = "active"
    CLOSED = "closed"
    SETTLED = "settled"
    SUSPENDED = "suspended"


class PositionSide(Enum):
    """Side of a position."""
    LONG = "long"
    SHORT = "short"