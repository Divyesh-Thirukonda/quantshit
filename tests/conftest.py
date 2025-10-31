"""Test configuration and fixtures."""

import sys
from pathlib import Path

# Add the project root to the Python path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

import pytest
from decimal import Decimal
from datetime import datetime, timedelta
from uuid import uuid4

from src.core import (
    Platform, Outcome, OrderType, OrderStatus, RiskLevel,
    Market, Quote, ArbitrageOpportunity, Position, Order, MarketStatus
)


@pytest.fixture
def sample_market_kalshi():
    """Sample Kalshi market for testing."""
    return Market(
        id="KALSHI_MARKET_001",
        platform=Platform.KALSHI,
        title="Will Bitcoin hit $100k by end of 2024?",
        description="Bitcoin price prediction market",
        status=MarketStatus.ACTIVE,
        close_time=datetime.utcnow() + timedelta(days=60),
        yes_price=Decimal('0.65'),
        no_price=Decimal('0.35'),
        volume_24h=Decimal('50000'),
        liquidity=Decimal('100000')
    )


@pytest.fixture
def sample_market_polymarket():
    """Sample Polymarket market for testing."""
    return Market(
        id="POLY_MARKET_001", 
        platform=Platform.POLYMARKET,
        title="Bitcoin $100k by 2024 end",
        description="Will BTC reach $100,000 by December 31, 2024?",
        status=MarketStatus.ACTIVE,
        close_time=datetime.utcnow() + timedelta(days=60),
        yes_price=Decimal('0.70'),
        no_price=Decimal('0.30'),
        volume_24h=Decimal('75000'),
        liquidity=Decimal('150000')
    )


@pytest.fixture
def sample_quote_kalshi():
    """Sample Kalshi quote for testing."""
    return Quote(
        market_id="KALSHI_MARKET_001",
        platform=Platform.KALSHI,
        outcome=Outcome.YES,
        bid_price=Decimal('0.64'),
        ask_price=Decimal('0.66'),
        bid_size=Decimal('1000'),
        ask_size=Decimal('1500')
    )


@pytest.fixture
def sample_quote_polymarket():
    """Sample Polymarket quote for testing."""
    return Quote(
        market_id="POLY_MARKET_001",
        platform=Platform.POLYMARKET,
        outcome=Outcome.YES,
        bid_price=Decimal('0.69'),
        ask_price=Decimal('0.71'),
        bid_size=Decimal('2000'),
        ask_size=Decimal('1800')
    )


@pytest.fixture
def sample_arbitrage_opportunity(sample_market_kalshi, sample_market_polymarket, 
                                 sample_quote_kalshi, sample_quote_polymarket):
    """Sample arbitrage opportunity for testing."""
    return ArbitrageOpportunity(
        market_a=sample_market_kalshi,
        market_b=sample_market_polymarket,
        quote_a=sample_quote_kalshi,
        quote_b=sample_quote_polymarket,
        expected_profit=Decimal('100'),
        profit_percentage=Decimal('0.05'),
        confidence_score=Decimal('0.85'),
        risk_level=RiskLevel.MEDIUM
    )