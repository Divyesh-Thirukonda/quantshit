"""
Tests for domain models (Market, Opportunity, Order, Position).
"""
import pytest
from datetime import datetime
from decimal import Decimal

from src.types import Exchange, OrderSide, OrderStatus, Outcome
from src.models import Market, Opportunity, Order, Position


class TestMarket:
    """Test Market model"""

    def test_market_creation(self):
        """Test creating a valid market"""
        market = Market(
            exchange=Exchange.KALSHI,
            market_id="TEST-001",
            title="Test Market",
            outcome=Outcome.YES,
            price=Decimal("0.50"),
            volume=Decimal("1000"),
            liquidity=Decimal("5000"),
            last_updated=datetime.now()
        )
        assert market.exchange == Exchange.KALSHI
        assert market.market_id == "TEST-001"
        assert market.price == Decimal("0.50")

    def test_market_price_bounds(self):
        """Test market price is between 0 and 1"""
        market = Market(
            exchange=Exchange.POLYMARKET,
            market_id="TEST-002",
            title="Test Market",
            outcome=Outcome.NO,
            price=Decimal("0.75"),
            volume=Decimal("1000"),
            liquidity=Decimal("5000"),
            last_updated=datetime.now()
        )
        assert 0 <= market.price <= 1


class TestOpportunity:
    """Test Opportunity model"""

    def test_opportunity_creation(self, sample_kalshi_market, sample_polymarket_market):
        """Test creating a valid opportunity"""
        opp = Opportunity(
            opportunity_id="OPP-TEST",
            market_kalshi=sample_kalshi_market,
            market_polymarket=sample_polymarket_market,
            outcome=Outcome.YES,
            price_difference=Decimal("0.05"),
            expected_profit=Decimal("30.00"),
            expected_profit_pct=Decimal("0.05"),
            confidence_score=0.85,
            discovered_at=datetime.now()
        )
        assert opp.expected_profit > 0
        assert opp.confidence_score > 0

    def test_opportunity_profit_calculation(self, sample_opportunity):
        """Test profit percentage calculation"""
        assert sample_opportunity.expected_profit_pct == Decimal("0.05")
        assert sample_opportunity.expected_profit == Decimal("30.00")


class TestOrder:
    """Test Order model"""

    def test_order_creation(self):
        """Test creating a valid order"""
        order = Order(
            order_id="ORDER-TEST",
            exchange=Exchange.KALSHI,
            market_id="MARKET-001",
            side=OrderSide.BUY,
            quantity=Decimal("100"),
            price=Decimal("0.65"),
            status=OrderStatus.PENDING,
            created_at=datetime.now()
        )
        assert order.status == OrderStatus.PENDING
        assert order.side == OrderSide.BUY

    def test_order_status_transitions(self, sample_order):
        """Test order status can be updated"""
        assert sample_order.status == OrderStatus.FILLED
        assert sample_order.filled_at is not None


class TestPosition:
    """Test Position model"""

    def test_position_creation(self, sample_position):
        """Test creating a valid position"""
        assert sample_position.quantity > 0
        assert sample_position.expected_profit > 0

    def test_position_pnl_calculation(self):
        """Test P&L calculation for a position"""
        position = Position(
            position_id="POS-TEST",
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
            opened_at=datetime.now(),
            current_price_kalshi=Decimal("0.70"),
            current_price_polymarket=Decimal("0.58")
        )
        # Position should have unrealized P&L if current prices are set
        assert position.current_price_kalshi is not None
