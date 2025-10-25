"""
Type definitions for the Quantshit arbitrage engine
Provides standardized data structures across all platforms and components
"""

from dataclasses import dataclass, field
from typing import Dict, List, Optional, Union, Literal
from enum import Enum
from datetime import datetime


# Enums for constrained values
class Platform(Enum):
    """Supported trading platforms"""
    POLYMARKET = "polymarket"
    KALSHI = "kalshi"


class Outcome(Enum):
    """Prediction market outcomes"""
    YES = "YES"
    NO = "NO"


class OrderType(Enum):
    """Order types"""
    BUY = "buy"
    SELL = "sell"


class OrderStatus(Enum):
    """Order execution status"""
    PENDING = "pending"
    FILLED = "filled"
    PARTIAL = "partial"
    CANCELLED = "cancelled"
    FAILED = "failed"


class RiskLevel(Enum):
    """Risk assessment levels"""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


# Core Market Data Types
@dataclass
class Quote:
    """Price quote for a specific outcome"""
    price: float
    volume: float
    liquidity: float
    timestamp: datetime = field(default_factory=datetime.now)
    
    def __post_init__(self):
        """Validate quote data"""
        if not (0 <= self.price <= 1):
            raise ValueError(f"Price must be between 0 and 1, got {self.price}")
        if self.volume < 0:
            raise ValueError(f"Volume must be non-negative, got {self.volume}")
        if self.liquidity < 0:
            raise ValueError(f"Liquidity must be non-negative, got {self.liquidity}")


@dataclass
class Market:
    """Standardized market representation"""
    id: str
    platform: Platform
    title: str
    yes_quote: Quote
    no_quote: Quote
    total_volume: float
    total_liquidity: float
    end_date: Optional[datetime] = None
    category: Optional[str] = None
    tags: List[str] = field(default_factory=list)
    
    @property
    def yes_price(self) -> float:
        """Convenience property for YES price"""
        return self.yes_quote.price
    
    @property
    def no_price(self) -> float:
        """Convenience property for NO price"""
        return self.no_quote.price
    
    @property
    def spread(self) -> float:
        """Calculate bid-ask spread"""
        return abs((self.yes_price + self.no_price) - 1.0)
    
    def to_dict(self) -> Dict:
        """Convert to legacy dict format for compatibility"""
        return {
            'id': self.id,
            'platform': self.platform.value,
            'title': self.title,
            'yes_price': self.yes_price,
            'no_price': self.no_price,
            'volume': self.total_volume,
            'liquidity': self.total_liquidity
        }


# Order and Trade Types
@dataclass
class Order:
    """Standardized order representation"""
    market_id: str
    platform: Platform
    outcome: Outcome
    order_type: OrderType
    quantity: int
    price: float
    order_id: Optional[str] = None
    status: OrderStatus = OrderStatus.PENDING
    filled_quantity: int = 0
    average_fill_price: float = 0.0
    timestamp: datetime = field(default_factory=datetime.now)
    fees: float = 0.0
    
    @property
    def is_filled(self) -> bool:
        """Check if order is completely filled"""
        return self.status == OrderStatus.FILLED
    
    @property
    def remaining_quantity(self) -> int:
        """Get remaining unfilled quantity"""
        return self.quantity - self.filled_quantity
    
    @property
    def total_cost(self) -> float:
        """Calculate total cost including fees"""
        return (self.filled_quantity * self.average_fill_price) + self.fees


@dataclass
class Position:
    """Standardized position representation"""
    market_id: str
    platform: Platform
    outcome: Outcome
    quantity: int
    average_price: float
    current_price: float
    total_cost: float
    timestamp: datetime = field(default_factory=datetime.now)
    
    @property
    def market_value(self) -> float:
        """Current market value of position"""
        return self.quantity * self.current_price
    
    @property
    def unrealized_pnl(self) -> float:
        """Unrealized profit/loss"""
        return self.market_value - self.total_cost
    
    @property
    def unrealized_pnl_pct(self) -> float:
        """Unrealized P&L as percentage"""
        return (self.unrealized_pnl / self.total_cost) * 100 if self.total_cost > 0 else 0.0


# Opportunity and Strategy Types
@dataclass
class ArbitrageOpportunity:
    """Standardized arbitrage opportunity"""
    id: str
    buy_market: Market
    sell_market: Market
    outcome: Outcome
    buy_price: float
    sell_price: float
    spread: float
    expected_profit_per_share: float
    confidence_score: float = 0.0
    risk_level: RiskLevel = RiskLevel.MEDIUM
    max_quantity: int = 100
    timestamp: datetime = field(default_factory=datetime.now)
    
    # Planning and sizing fields
    recommended_quantity: Optional[int] = None
    position_value: Optional[float] = None
    kelly_fraction: Optional[float] = None
    risk_adjustment: Optional[float] = None
    win_probability: Optional[float] = None
    
    @property
    def expected_profit(self) -> float:
        """Expected profit for recommended quantity"""
        quantity = self.recommended_quantity or self.max_quantity
        return self.expected_profit_per_share * quantity
    
    @property
    def is_profitable(self) -> bool:
        """Check if opportunity is profitable"""
        return self.expected_profit_per_share > 0
    
    def to_legacy_dict(self) -> Dict:
        """Convert to legacy dict format for compatibility"""
        return {
            'type': 'arbitrage',
            'outcome': self.outcome.value,
            'buy_market': self.buy_market.to_dict(),
            'sell_market': self.sell_market.to_dict(),
            'buy_price': self.buy_price,
            'sell_price': self.sell_price,
            'spread': self.spread,
            'expected_profit': self.expected_profit_per_share,
            'position_size': self.recommended_quantity or self.max_quantity,
            'trade_amount': self.recommended_quantity or self.max_quantity,
        }


@dataclass
class TradePlan:
    """Complete trading plan with multiple opportunities"""
    opportunities: List[ArbitrageOpportunity]
    total_capital_required: float
    expected_total_return: float
    max_risk_per_trade: float
    portfolio_utilization: float
    correlation_groups: Dict[str, List[str]] = field(default_factory=dict)
    risk_metrics: Dict[str, float] = field(default_factory=dict)
    timestamp: datetime = field(default_factory=datetime.now)
    
    @property
    def num_trades(self) -> int:
        """Number of trades in plan"""
        return len(self.opportunities)
    
    @property
    def expected_return_pct(self) -> float:
        """Expected return as percentage of capital"""
        return (self.expected_total_return / self.total_capital_required * 100) if self.total_capital_required > 0 else 0.0


# Portfolio and Risk Types
@dataclass
class PortfolioSnapshot:
    """Complete portfolio state at a point in time"""
    platforms: Dict[Platform, 'PlatformPortfolio']
    total_value: float
    total_cash: float
    total_positions_value: float
    unrealized_pnl: float
    timestamp: datetime = field(default_factory=datetime.now)
    
    @property
    def cash_percentage(self) -> float:
        """Cash as percentage of total portfolio"""
        return (self.total_cash / self.total_value * 100) if self.total_value > 0 else 0.0


@dataclass
class PlatformPortfolio:
    """Portfolio state for a single platform"""
    platform: Platform
    cash_balance: float
    positions: List[Position]
    total_value: float
    unrealized_pnl: float
    
    @property
    def positions_value(self) -> float:
        """Total value of all positions"""
        return sum(pos.market_value for pos in self.positions)
    
    @property
    def num_positions(self) -> int:
        """Number of active positions"""
        return len(self.positions)


@dataclass
class RiskMetrics:
    """Risk assessment metrics"""
    correlation_risk: float
    concentration_risk: float
    liquidity_risk: float
    platform_risk: float
    overall_risk_score: float
    risk_level: RiskLevel
    warnings: List[str] = field(default_factory=list)
    recommendations: List[str] = field(default_factory=list)


# Execution and Results Types
@dataclass
class TradeExecution:
    """Result of executing a trade"""
    opportunity_id: str
    buy_order: Order
    sell_order: Order
    success: bool
    profit_realized: float = 0.0
    fees_paid: float = 0.0
    execution_time_ms: float = 0.0
    error_message: Optional[str] = None
    timestamp: datetime = field(default_factory=datetime.now)
    
    @property
    def net_profit(self) -> float:
        """Net profit after fees"""
        return self.profit_realized - self.fees_paid
    
    @property
    def both_orders_filled(self) -> bool:
        """Check if both sides of arbitrage were executed"""
        return self.buy_order.is_filled and self.sell_order.is_filled


@dataclass
class ExecutionSummary:
    """Summary of multiple trade executions"""
    executions: List[TradeExecution]
    total_trades_attempted: int
    successful_trades: int
    total_profit: float
    total_fees: float
    average_execution_time: float
    timestamp: datetime = field(default_factory=datetime.now)
    
    @property
    def success_rate(self) -> float:
        """Percentage of successful trades"""
        return (self.successful_trades / self.total_trades_attempted * 100) if self.total_trades_attempted > 0 else 0.0
    
    @property
    def net_profit(self) -> float:
        """Total profit minus fees"""
        return self.total_profit - self.total_fees


# Configuration Types
@dataclass
class TradingConfig:
    """Trading system configuration"""
    min_spread: float = 0.05
    max_position_pct: float = 0.15
    max_platform_pct: float = 0.65
    min_cash_reserve: float = 0.25
    correlation_threshold: float = 0.7
    min_volume: float = 1000.0
    max_trades_per_session: int = 10
    paper_trading: bool = True
    
    def validate(self) -> List[str]:
        """Validate configuration parameters"""
        errors = []
        
        if not (0 < self.min_spread < 1):
            errors.append("min_spread must be between 0 and 1")
        if not (0 < self.max_position_pct <= 1):
            errors.append("max_position_pct must be between 0 and 1")
        if not (0 < self.max_platform_pct <= 1):
            errors.append("max_platform_pct must be between 0 and 1")
        if not (0 <= self.min_cash_reserve < 1):
            errors.append("min_cash_reserve must be between 0 and 1")
        if self.min_volume < 0:
            errors.append("min_volume must be non-negative")
        if self.max_trades_per_session < 1:
            errors.append("max_trades_per_session must be positive")
            
        return errors


# Type aliases for common collections
Markets = List[Market]
Orders = List[Order]
Positions = List[Position]
Opportunities = List[ArbitrageOpportunity]
Executions = List[TradeExecution]

# Union types for flexibility
PlatformIdentifier = Union[Platform, str]
OutcomeIdentifier = Union[Outcome, str]
OrderTypeIdentifier = Union[OrderType, str]


# Utility functions for type conversion
def ensure_platform(platform: PlatformIdentifier) -> Platform:
    """Ensure platform is Platform enum"""
    if isinstance(platform, str):
        return Platform(platform.lower())
    return platform


def ensure_outcome(outcome: OutcomeIdentifier) -> Outcome:
    """Ensure outcome is Outcome enum"""
    if isinstance(outcome, str):
        return Outcome(outcome.upper())
    return outcome


def ensure_order_type(order_type: OrderTypeIdentifier) -> OrderType:
    """Ensure order_type is OrderType enum"""
    if isinstance(order_type, str):
        return OrderType(order_type.lower())
    return order_type