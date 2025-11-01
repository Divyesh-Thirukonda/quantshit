"""
Core data models for the prediction market arbitrage system.
"""

from datetime import datetime
from decimal import Decimal
from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field

from .enums import (
    Platform, Outcome, OrderType, OrderStatus, 
    RiskLevel, MarketStatus, TradeStatus, StrategyType
)


class Market(BaseModel):
    """Represents a prediction market."""
    id: str
    platform: Platform
    title: str
    description: Optional[str] = None
    close_date: datetime
    status: MarketStatus
    category: Optional[str] = None
    tags: List[str] = Field(default_factory=list)
    volume_24h: Optional[Decimal] = None
    created_at: datetime
    updated_at: datetime


class Quote(BaseModel):
    """Represents a price quote for a market outcome."""
    market_id: str
    platform: Platform
    outcome: Outcome
    bid_price: Decimal
    ask_price: Decimal
    bid_size: Decimal
    ask_size: Decimal
    last_price: Optional[Decimal] = None
    volume: Optional[Decimal] = None
    timestamp: datetime


class ArbitrageOpportunity(BaseModel):
    """Represents an arbitrage opportunity between platforms."""
    id: str
    market_1_id: str
    market_2_id: str
    platform_1: Platform
    platform_2: Platform
    outcome: Outcome
    buy_platform: Platform
    sell_platform: Platform
    buy_price: Decimal
    sell_price: Decimal
    spread: Decimal
    spread_percentage: Decimal
    max_profit: Decimal
    estimated_profit: Decimal
    confidence_score: Decimal
    risk_level: RiskLevel
    created_at: datetime
    expires_at: datetime


class Position(BaseModel):
    """Represents a trading position."""
    id: str
    market_id: str
    platform: Platform
    outcome: Outcome
    order_type: OrderType
    quantity: Decimal
    entry_price: Decimal
    current_price: Optional[Decimal] = None
    unrealized_pnl: Optional[Decimal] = None
    realized_pnl: Optional[Decimal] = None
    status: TradeStatus
    opened_at: datetime
    closed_at: Optional[datetime] = None


class TradePlan(BaseModel):
    """Represents a planned arbitrage trade."""
    id: str
    opportunity_id: str
    strategy_type: StrategyType
    leg_1: Dict[str, Any]  # Buy leg details
    leg_2: Dict[str, Any]  # Sell leg details
    total_investment: Decimal
    expected_profit: Decimal
    max_loss: Decimal
    risk_level: RiskLevel
    execution_priority: int
    status: TradeStatus
    created_at: datetime
    executed_at: Optional[datetime] = None


class Order(BaseModel):
    """Represents a trading order."""
    id: str
    position_id: str
    platform: Platform
    market_id: str
    outcome: Outcome
    order_type: OrderType
    quantity: Decimal
    price: Decimal
    filled_quantity: Decimal = Decimal('0')
    status: OrderStatus
    platform_order_id: Optional[str] = None
    created_at: datetime
    updated_at: datetime
    filled_at: Optional[datetime] = None


class Portfolio(BaseModel):
    """Represents the overall trading portfolio."""
    total_value: Decimal
    cash_balance: Decimal
    unrealized_pnl: Decimal
    realized_pnl: Decimal
    total_pnl: Decimal
    positions: List[Position]
    daily_pnl: Decimal
    win_rate: Decimal
    sharpe_ratio: Optional[Decimal] = None
    max_drawdown: Decimal
    updated_at: datetime


class Strategy(BaseModel):
    """Represents a trading strategy configuration."""
    id: str
    name: str
    strategy_type: StrategyType
    parameters: Dict[str, Any]
    is_active: bool
    performance_metrics: Dict[str, Any] = Field(default_factory=dict)
    created_at: datetime
    updated_at: datetime