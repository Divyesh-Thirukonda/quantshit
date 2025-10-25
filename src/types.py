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


class FillType(Enum):
    """Types of order fills"""
    FULL = "full"
    PARTIAL = "partial"
    NONE = "none"


class PlanStatus(Enum):
    """Status of a trading plan"""
    PENDING = "pending"
    EXECUTING = "executing"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


class LegType(Enum):
    """Types of trade legs"""
    BUY_LEG = "buy_leg"
    SELL_LEG = "sell_leg"
    HEDGE_LEG = "hedge_leg"


class ExecutionMode(Enum):
    """Order execution modes"""
    MARKET = "market"
    LIMIT = "limit"
    IOC = "ioc"  # Immediate or Cancel
    FOK = "fok"  # Fill or Kill


class OrderSide(Enum):
    """Order side (alias for OrderType for compatibility)"""
    BUY = "buy"
    SELL = "sell"


class TradePriority(Enum):
    """Trade execution priority levels"""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    URGENT = "urgent"


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
class OrderBookLevel:
    """Single level in order book"""
    price: float
    volume: float
    num_orders: int = 1
    
    def __post_init__(self):
        if self.price < 0:
            raise ValueError("Price must be non-negative")
        if self.volume < 0:
            raise ValueError("Volume must be non-negative")


@dataclass
class OrderBook:
    """Complete order book for a market outcome"""
    market_id: str
    platform: Platform
    outcome: Outcome
    bids: List[OrderBookLevel] = field(default_factory=list)  # Buy orders
    asks: List[OrderBookLevel] = field(default_factory=list)  # Sell orders
    timestamp: datetime = field(default_factory=datetime.now)
    
    @property
    def best_bid(self) -> Optional[OrderBookLevel]:
        """Highest bid price"""
        return max(self.bids, key=lambda x: x.price) if self.bids else None
    
    @property
    def best_ask(self) -> Optional[OrderBookLevel]:
        """Lowest ask price"""
        return min(self.asks, key=lambda x: x.price) if self.asks else None
    
    @property
    def spread(self) -> float:
        """Bid-ask spread"""
        if self.best_bid and self.best_ask:
            return self.best_ask.price - self.best_bid.price
        return 0.0
    
    @property
    def mid_price(self) -> Optional[float]:
        """Mid market price"""
        if self.best_bid and self.best_ask:
            return (self.best_bid.price + self.best_ask.price) / 2
        return None
    
    def total_bid_volume(self, max_levels: int = 5) -> float:
        """Total volume available at bid levels"""
        return sum(level.volume for level in self.bids[:max_levels])
    
    def total_ask_volume(self, max_levels: int = 5) -> float:
        """Total volume available at ask levels"""
        return sum(level.volume for level in self.asks[:max_levels])


@dataclass
class Fill:
    """Individual order fill/execution"""
    fill_id: str
    order_id: str
    quantity: int
    price: float
    timestamp: datetime
    fees: float = 0.0
    commission: float = 0.0
    
    @property
    def total_value(self) -> float:
        """Total value of fill"""
        return self.quantity * self.price
    
    @property
    def total_cost(self) -> float:
        """Total cost including fees"""
        return self.total_value + self.fees + self.commission


@dataclass
class OrderAck:
    """Order acknowledgment from platform"""
    order_id: str
    platform_order_id: Optional[str]
    status: OrderStatus
    message: Optional[str] = None
    timestamp: datetime = field(default_factory=datetime.now)
    estimated_fill_time: Optional[datetime] = None
    
    @property
    def is_accepted(self) -> bool:
        """Check if order was accepted"""
        return self.status not in [OrderStatus.FAILED, OrderStatus.CANCELLED]


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
    """Enhanced order representation with fills and lifecycle management"""
    order_id: str
    market_id: str
    platform: Platform
    outcome: Outcome
    order_type: OrderType
    quantity: int
    price: float
    execution_mode: ExecutionMode = ExecutionMode.LIMIT
    status: OrderStatus = OrderStatus.PENDING
    filled_quantity: int = 0
    average_fill_price: float = 0.0
    timestamp: datetime = field(default_factory=datetime.now)
    fills: List[Fill] = field(default_factory=list)
    fees: float = 0.0
    acknowledgment: Optional[OrderAck] = None
    parent_plan_id: Optional[str] = None
    leg_id: Optional[str] = None
    
    @property
    def is_filled(self) -> bool:
        """Check if order is completely filled"""
        return self.status == OrderStatus.FILLED
    
    @property
    def is_partial(self) -> bool:
        """Check if order is partially filled"""
        return self.status == OrderStatus.PARTIAL
    
    @property
    def remaining_quantity(self) -> int:
        """Get remaining unfilled quantity"""
        return self.quantity - self.filled_quantity
    
    @property
    def total_cost(self) -> float:
        """Calculate total cost including fees"""
        return (self.filled_quantity * self.average_fill_price) + self.fees
    
    @property
    def fill_percentage(self) -> float:
        """Percentage of order filled"""
        return (self.filled_quantity / self.quantity * 100) if self.quantity > 0 else 0.0
    
    def add_fill(self, fill: Fill):
        """Add a fill to this order"""
        self.fills.append(fill)
        self.filled_quantity += fill.quantity
        self.fees += fill.fees
        
        # Recalculate average fill price
        total_filled_value = sum(f.quantity * f.price for f in self.fills)
        self.average_fill_price = total_filled_value / self.filled_quantity if self.filled_quantity > 0 else 0.0
        
        # Update status
        if self.filled_quantity >= self.quantity:
            self.status = OrderStatus.FILLED
        elif self.filled_quantity > 0:
            self.status = OrderStatus.PARTIAL


@dataclass
class TradeLeg:
    """Individual leg of a multi-leg trade strategy"""
    leg_id: str
    leg_type: LegType
    market: Market
    outcome: Outcome
    order_type: OrderType
    target_quantity: int
    target_price: float
    execution_mode: ExecutionMode = ExecutionMode.LIMIT
    priority: int = 1  # Lower numbers = higher priority
    dependency_legs: List[str] = field(default_factory=list)  # Must execute after these
    order: Optional[Order] = None
    
    @property
    def is_executed(self) -> bool:
        """Check if leg has been executed"""
        return self.order is not None and self.order.is_filled
    
    @property
    def is_pending(self) -> bool:
        """Check if leg is pending execution"""
        return self.order is None or self.order.status == OrderStatus.PENDING
    
    def can_execute(self, executed_legs: List[str]) -> bool:
        """Check if all dependencies are met"""
        return all(dep_id in executed_legs for dep_id in self.dependency_legs)


@dataclass
class Position:
    """Standardized position representation with potential gain tracking"""
    market_id: str
    platform: Platform
    outcome: Outcome
    quantity: int
    average_price: float
    current_price: float
    total_cost: float
    timestamp: datetime = field(default_factory=datetime.now)
    target_exit_price: Optional[float] = None  # Expected exit price for remaining gain calculation
    max_potential_price: Optional[float] = None  # Maximum possible price (usually 1.0 for prediction markets)
    position_id: Optional[str] = None
    origin_plan_id: Optional[str] = None  # Link back to the plan that created this position
    
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
    
    @property
    def potential_remaining_gain(self) -> float:
        """Potential remaining gain in absolute dollars"""
        if self.target_exit_price is None:
            # Use max potential price (1.0 for prediction markets) as conservative estimate
            target_price = self.max_potential_price or 1.0
        else:
            target_price = self.target_exit_price
        
        potential_value = self.quantity * target_price
        return potential_value - self.market_value
    
    @property
    def potential_remaining_gain_pct(self) -> float:
        """Potential remaining gain as percentage of current market value"""
        if self.market_value <= 0:
            return 0.0
        return (self.potential_remaining_gain / self.market_value) * 100
    
    @property
    def total_potential_gain_pct(self) -> float:
        """Total potential gain from entry to target as percentage of cost"""
        if self.total_cost <= 0:
            return 0.0
        
        target_price = self.target_exit_price or self.max_potential_price or 1.0
        total_potential_value = self.quantity * target_price
        total_potential_gain = total_potential_value - self.total_cost
        return (total_potential_gain / self.total_cost) * 100
    
    @property
    def is_profitable(self) -> bool:
        """Check if position is currently profitable"""
        return self.unrealized_pnl > 0


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
    """Complete trading plan with multiple legs and execution strategy"""
    plan_id: str
    name: str
    legs: List[TradeLeg]
    strategy_type: str = "arbitrage"  # arbitrage, hedge, speculative, etc.
    status: PlanStatus = PlanStatus.PENDING
    total_capital_required: float = 0.0
    expected_total_return: float = 0.0
    max_risk_per_trade: float = 0.0
    portfolio_utilization: float = 0.0
    correlation_groups: Dict[str, List[str]] = field(default_factory=dict)
    risk_metrics: Dict[str, float] = field(default_factory=dict)
    timestamp: datetime = field(default_factory=datetime.now)
    start_time: Optional[datetime] = None
    completion_time: Optional[datetime] = None
    timeout_minutes: int = 30
    
    @property
    def num_legs(self) -> int:
        """Number of legs in plan"""
        return len(self.legs)
    
    @property
    def expected_return_pct(self) -> float:
        """Expected return as percentage of capital"""
        return (self.expected_total_return / self.total_capital_required * 100) if self.total_capital_required > 0 else 0.0
    
    @property
    def executed_legs(self) -> List[TradeLeg]:
        """Get all executed legs"""
        return [leg for leg in self.legs if leg.is_executed]
    
    @property
    def pending_legs(self) -> List[TradeLeg]:
        """Get all pending legs"""
        return [leg for leg in self.legs if leg.is_pending]
    
    @property
    def execution_progress(self) -> float:
        """Percentage of legs executed"""
        return (len(self.executed_legs) / len(self.legs) * 100) if self.legs else 0.0
    
    def get_next_executable_legs(self) -> List[TradeLeg]:
        """Get legs that can be executed next based on dependencies"""
        executed_leg_ids = [leg.leg_id for leg in self.executed_legs]
        return [leg for leg in self.pending_legs if leg.can_execute(executed_leg_ids)]
    
    def add_leg(self, leg: TradeLeg):
        """Add a leg to the plan"""
        self.legs.append(leg)
        self.total_capital_required += leg.target_quantity * leg.target_price
    
    def is_complete(self) -> bool:
        """Check if all legs are executed"""
        return all(leg.is_executed for leg in self.legs)
    
    def to_opportunities(self) -> List[ArbitrageOpportunity]:
        """Convert plan legs to legacy ArbitrageOpportunity objects for compatibility"""
        opportunities = []
        
        # Group legs into arbitrage pairs
        buy_legs = [leg for leg in self.legs if leg.leg_type == LegType.BUY_LEG]
        sell_legs = [leg for leg in self.legs if leg.leg_type == LegType.SELL_LEG]
        
        for i, buy_leg in enumerate(buy_legs):
            if i < len(sell_legs):
                sell_leg = sell_legs[i]
                opportunity = ArbitrageOpportunity(
                    id=f"{self.plan_id}_leg_{buy_leg.leg_id}_{sell_leg.leg_id}",
                    buy_market=buy_leg.market,
                    sell_market=sell_leg.market,
                    outcome=buy_leg.outcome,
                    buy_price=buy_leg.target_price,
                    sell_price=sell_leg.target_price,
                    spread=sell_leg.target_price - buy_leg.target_price,
                    expected_profit_per_share=sell_leg.target_price - buy_leg.target_price,
                    max_quantity=min(buy_leg.target_quantity, sell_leg.target_quantity),
                    recommended_quantity=min(buy_leg.target_quantity, sell_leg.target_quantity)
                )
                opportunities.append(opportunity)
        
        return opportunities


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
class ExecutionResult:
    """Comprehensive result of executing a trade plan"""
    plan_id: str
    status: PlanStatus
    executed_legs: List[TradeLeg]
    failed_legs: List[TradeLeg]
    total_profit: float = 0.0
    total_fees: float = 0.0
    execution_time_ms: float = 0.0
    error_messages: List[str] = field(default_factory=list)
    warnings: List[str] = field(default_factory=list)
    timestamp: datetime = field(default_factory=datetime.now)
    start_time: Optional[datetime] = None
    end_time: Optional[datetime] = None
    
    @property
    def net_profit(self) -> float:
        """Net profit after fees"""
        return self.total_profit - self.total_fees
    
    @property
    def success_rate(self) -> float:
        """Percentage of legs executed successfully"""
        total_legs = len(self.executed_legs) + len(self.failed_legs)
        return (len(self.executed_legs) / total_legs * 100) if total_legs > 0 else 0.0
    
    @property
    def is_successful(self) -> bool:
        """Check if execution was completely successful"""
        return self.status == PlanStatus.COMPLETED and not self.failed_legs
    
    @property
    def is_partial_success(self) -> bool:
        """Check if execution had some success"""
        return len(self.executed_legs) > 0 and len(self.failed_legs) > 0


@dataclass
class TradeExecution:
    """Legacy trade execution result for backwards compatibility"""
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
    
    @classmethod
    def from_execution_result(cls, execution_result: ExecutionResult, opportunity_id: str) -> 'TradeExecution':
        """Create TradeExecution from ExecutionResult for compatibility"""
        executed_legs = execution_result.executed_legs
        
        # Find buy and sell orders
        buy_order = None
        sell_order = None
        
        for leg in executed_legs:
            if leg.order:
                if leg.leg_type == LegType.BUY_LEG:
                    buy_order = leg.order
                elif leg.leg_type == LegType.SELL_LEG:
                    sell_order = leg.order
        
        # Create dummy orders if not found
        if not buy_order:
            buy_order = Order(
                order_id="dummy_buy",
                market_id="unknown",
                platform=Platform.POLYMARKET,
                outcome=Outcome.YES,
                order_type=OrderType.BUY,
                quantity=0,
                price=0.0
            )
        
        if not sell_order:
            sell_order = Order(
                order_id="dummy_sell",
                market_id="unknown",
                platform=Platform.KALSHI,
                outcome=Outcome.YES,
                order_type=OrderType.SELL,
                quantity=0,
                price=0.0
            )
        
        return cls(
            opportunity_id=opportunity_id,
            buy_order=buy_order,
            sell_order=sell_order,
            success=execution_result.is_successful,
            profit_realized=execution_result.total_profit,
            fees_paid=execution_result.total_fees,
            execution_time_ms=execution_result.execution_time_ms,
            error_message="; ".join(execution_result.error_messages) if execution_result.error_messages else None,
            timestamp=execution_result.timestamp
        )


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
class PositionManagerConfig:
    """Configuration for position management system"""
    max_open_positions: int = 10
    min_swap_threshold_pct: float = 5.0  # New opportunity must be 5% better to trigger swap
    position_size_pct: float = 0.05  # 5% of portfolio per position
    min_remaining_gain_pct: float = 2.0  # Minimum 2% remaining gain to keep position
    force_close_threshold_pct: float = -10.0  # Force close if loss exceeds 10%
    max_hold_time_hours: int = 24  # Maximum time to hold a position
    rebalance_frequency_minutes: int = 30  # How often to check for rebalancing


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
    position_manager: PositionManagerConfig = field(default_factory=PositionManagerConfig)
    
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
TradePlans = List[TradePlan]
TradeLegs = List[TradeLeg]
Fills = List[Fill]
OrderBooks = List[OrderBook]

# Union types for flexibility
PlatformIdentifier = Union[Platform, str]
OutcomeIdentifier = Union[Outcome, str]
OrderTypeIdentifier = Union[OrderType, str]
ExecutionModeIdentifier = Union[ExecutionMode, str]
LegTypeIdentifier = Union[LegType, str]

# Complex union types for execution interfaces
ExecutableItem = Union[ArbitrageOpportunity, TradePlan, TradeLeg]
ExecutionResultType = Union[ExecutionResult, TradeExecution]


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


def ensure_execution_mode(execution_mode: ExecutionModeIdentifier) -> ExecutionMode:
    """Ensure execution_mode is ExecutionMode enum"""
    if isinstance(execution_mode, str):
        return ExecutionMode(execution_mode.lower())
    return execution_mode


def ensure_leg_type(leg_type: LegTypeIdentifier) -> LegType:
    """Ensure leg_type is LegType enum"""
    if isinstance(leg_type, str):
        return LegType(leg_type.lower())
    return leg_type


# Factory functions for creating common objects
def create_arbitrage_plan(
    plan_id: str,
    buy_market: Market,
    sell_market: Market,
    outcome: Outcome,
    buy_quantity: int,
    sell_quantity: int,
    buy_price: float,
    sell_price: float,
    name: Optional[str] = None
) -> TradePlan:
    """Create a TradePlan for arbitrage opportunity"""
    
    if name is None:
        name = f"Arbitrage {outcome.value} {buy_market.platform.value}->{sell_market.platform.value}"
    
    buy_leg = TradeLeg(
        leg_id=f"{plan_id}_buy",
        leg_type=LegType.BUY_LEG,
        market=buy_market,
        outcome=outcome,
        order_type=OrderType.BUY,
        target_quantity=buy_quantity,
        target_price=buy_price,
        priority=1
    )
    
    sell_leg = TradeLeg(
        leg_id=f"{plan_id}_sell",
        leg_type=LegType.SELL_LEG,
        market=sell_market,
        outcome=outcome,
        order_type=OrderType.SELL,
        target_quantity=sell_quantity,
        target_price=sell_price,
        priority=2,
        dependency_legs=[buy_leg.leg_id]  # Sell after buy
    )
    
    plan = TradePlan(
        plan_id=plan_id,
        name=name,
        legs=[buy_leg, sell_leg],
        strategy_type="arbitrage",
        total_capital_required=buy_quantity * buy_price,
        expected_total_return=(sell_price - buy_price) * min(buy_quantity, sell_quantity)
    )
    
    return plan


def create_order_from_leg(leg: TradeLeg, order_id: str) -> Order:
    """Create an Order from a TradeLeg"""
    return Order(
        order_id=order_id,
        market_id=leg.market.id,
        platform=leg.market.platform,
        outcome=leg.outcome,
        order_type=leg.order_type,
        quantity=leg.target_quantity,
        price=leg.target_price,
        execution_mode=leg.execution_mode,
        parent_plan_id=order_id.split('_')[0] if '_' in order_id else None,
        leg_id=leg.leg_id
    )