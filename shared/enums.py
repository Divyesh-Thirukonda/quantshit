"""
Core enums for the prediction market arbitrage system.
"""

from enum import Enum


class Platform(str, Enum):
    """Trading platforms we support."""
    KALSHI = "kalshi"
    POLYMARKET = "polymarket"


class Outcome(str, Enum):
    """Possible outcomes for binary prediction markets."""
    YES = "yes"
    NO = "no"


class OrderType(str, Enum):
    """Types of orders we can place."""
    BUY = "buy"
    SELL = "sell"


class OrderStatus(str, Enum):
    """Status of orders."""
    PENDING = "pending"
    FILLED = "filled"
    CANCELLED = "cancelled"
    PARTIALLY_FILLED = "partially_filled"
    FAILED = "failed"


class RiskLevel(str, Enum):
    """Risk levels for trades."""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"


class MarketStatus(str, Enum):
    """Status of prediction markets."""
    ACTIVE = "active"
    CLOSED = "closed"
    RESOLVED = "resolved"
    SUSPENDED = "suspended"


class TradeStatus(str, Enum):
    """Status of arbitrage trades."""
    MONITORING = "monitoring"
    ENTERED = "entered"
    EXITED = "exited"
    EXPIRED = "expired"


class StrategyType(str, Enum):
    """Types of trading strategies."""
    ARBITRAGE = "arbitrage"
    INSIDER_INFO = "insider_info"
    PAIR_TRADING = "pair_trading"
    MEAN_REVERSION = "mean_reversion"
    NEURAL_NETWORK = "neural_network"