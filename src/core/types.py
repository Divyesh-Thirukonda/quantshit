"""Core data types for the prediction market arbitrage system."""

from dataclasses import dataclass, field
from datetime import datetime
from decimal import Decimal
from typing import Dict, List, Optional, Any
from uuid import UUID, uuid4

from .enums import (
    Platform, Outcome, OrderType, OrderStatus, RiskLevel,
    StrategyType, MarketStatus, PositionSide
)


@dataclass
class Market:
    """Represents a prediction market."""
    id: str
    platform: Platform
    title: str
    description: str
    status: MarketStatus
    close_time: datetime
    yes_price: Decimal
    no_price: Decimal
    volume_24h: Decimal
    liquidity: Decimal
    created_at: datetime = field(default_factory=datetime.utcnow)
    updated_at: datetime = field(default_factory=datetime.utcnow)
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class Quote:
    """Represents a price quote for a market."""
    market_id: str
    platform: Platform
    outcome: Outcome
    bid_price: Decimal
    ask_price: Decimal
    bid_size: Decimal
    ask_size: Decimal
    timestamp: datetime = field(default_factory=datetime.utcnow)


@dataclass
class ArbitrageOpportunity:
    """Represents an arbitrage opportunity between markets."""
    market_a: Market
    market_b: Market
    quote_a: Quote
    quote_b: Quote
    expected_profit: Decimal
    profit_percentage: Decimal
    confidence_score: Decimal  # 0-1, how confident we are in the opportunity
    risk_level: RiskLevel
    id: UUID = field(default_factory=uuid4)
    detected_at: datetime = field(default_factory=datetime.utcnow)
    expires_at: Optional[datetime] = None


@dataclass
class Position:
    """Represents a trading position."""
    market_id: str
    platform: Platform
    side: PositionSide
    outcome: Outcome
    quantity: Decimal
    entry_price: Decimal
    current_price: Decimal
    unrealized_pnl: Decimal
    id: UUID = field(default_factory=uuid4)
    realized_pnl: Decimal = field(default=Decimal('0'))
    opened_at: datetime = field(default_factory=datetime.utcnow)
    closed_at: Optional[datetime] = None
    strategy_type: Optional[StrategyType] = None


@dataclass
class Order:
    """Represents a trading order."""
    market_id: str
    platform: Platform
    order_type: OrderType
    outcome: Outcome
    quantity: Decimal
    price: Decimal
    status: OrderStatus
    id: UUID = field(default_factory=uuid4)
    filled_quantity: Decimal = field(default=Decimal('0'))
    average_fill_price: Decimal = field(default=Decimal('0'))
    created_at: datetime = field(default_factory=datetime.utcnow)
    updated_at: datetime = field(default_factory=datetime.utcnow)
    position_id: Optional[UUID] = None


@dataclass
class TradePlan:
    """Represents a complete trading plan for an arbitrage opportunity."""
    opportunity: ArbitrageOpportunity
    orders: List[Order]
    max_investment: Decimal
    expected_return: Decimal
    risk_assessment: Dict[str, Any]
    id: UUID = field(default_factory=uuid4)
    created_at: datetime = field(default_factory=datetime.utcnow)
    executed_at: Optional[datetime] = None
    status: str = "pending"  # pending, executing, completed, failed


@dataclass
class Portfolio:
    """Represents the current portfolio state."""
    total_value: Decimal
    available_balance: Decimal
    positions: List[Position]
    open_orders: List[Order]
    daily_pnl: Decimal
    total_pnl: Decimal
    last_updated: datetime = field(default_factory=datetime.utcnow)


@dataclass
class PlatformConfig:
    """Configuration for a prediction market platform."""
    platform: Platform
    api_key: str
    api_secret: Optional[str] = None
    base_url: str = ""
    rate_limit: int = 100  # requests per minute
    is_testnet: bool = True