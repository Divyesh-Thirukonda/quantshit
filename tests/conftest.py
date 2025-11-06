"""
Pytest configuration and shared fixtures for all tests.
"""
import pytest
from datetime import datetime
from decimal import Decimal

from src.types import Exchange, OrderSide, OrderStatus, Outcome
from src.models import Market, Opportunity, Order, Position


@pytest.fixture
def sample_kalshi_market():
    """Sample Kalshi market for testing"""
    return Market(
        exchange=Exchange.KALSHI,
        market_id="KALSHI-001",
        title="Will Bitcoin reach $100k by end of 2025?",
        outcome=Outcome.YES,
        price=Decimal("0.65"),
        volume=Decimal("10000"),
        liquidity=Decimal("50000"),
        last_updated=datetime.now()
    )


@pytest.fixture
def sample_polymarket_market():
    """Sample Polymarket market for testing"""
    return Market(
        exchange=Exchange.POLYMARKET,
        market_id="POLY-001",
        title="Bitcoin to hit $100k by 2025?",
        outcome=Outcome.YES,
        price=Decimal("0.60"),
        volume=Decimal("15000"),
        liquidity=Decimal("60000"),
        last_updated=datetime.now()
    )


@pytest.fixture
def sample_opportunity(sample_kalshi_market, sample_polymarket_market):
    """Sample arbitrage opportunity for testing"""
    return Opportunity(
        opportunity_id="OPP-001",
        market_kalshi=sample_kalshi_market,
        market_polymarket=sample_polymarket_market,
        outcome=Outcome.YES,
        price_difference=Decimal("0.05"),
        expected_profit=Decimal("30.00"),
        expected_profit_pct=Decimal("0.05"),
        confidence_score=0.85,
        discovered_at=datetime.now()
    )


@pytest.fixture
def sample_order():
    """Sample order for testing"""
    return Order(
        order_id="ORDER-001",
        exchange=Exchange.KALSHI,
        market_id="KALSHI-001",
        side=OrderSide.BUY,
        quantity=Decimal("100"),
        price=Decimal("0.65"),
        status=OrderStatus.FILLED,
        created_at=datetime.now(),
        filled_at=datetime.now()
    )


@pytest.fixture
def sample_position():
    """Sample position for testing"""
    return Position(
        position_id="POS-001",
        opportunity_id="OPP-001",
        market_kalshi_id="KALSHI-001",
        market_polymarket_id="POLY-001",
        outcome=Outcome.YES,
        kalshi_order_id="ORDER-001",
        polymarket_order_id="ORDER-002",
        quantity=Decimal("100"),
        entry_price_kalshi=Decimal("0.65"),
        entry_price_polymarket=Decimal("0.60"),
        expected_profit=Decimal("30.00"),
        opened_at=datetime.now()
    )
