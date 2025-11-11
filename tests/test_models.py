"""
Comprehensive unit tests for all data models.
Tests validation, properties, edge cases, and error handling.
"""
import pytest
from datetime import datetime, timedelta

from src.fin_types import Exchange, OrderSide, OrderStatus, MarketStatus, Outcome
from src.models import Market, Order, Position, Opportunity


@pytest.mark.unit
class TestMarket:
    """Test Market model"""

    def test_market_creation_valid(self, sample_kalshi_market):
        """Test creating a valid market"""
        assert sample_kalshi_market.id == "kalshi_test_001"
        assert sample_kalshi_market.exchange == Exchange.KALSHI
        assert sample_kalshi_market.yes_price == 0.45
        assert sample_kalshi_market.no_price == 0.55
        assert sample_kalshi_market.volume == 50000.0
        assert sample_kalshi_market.liquidity == 25000.0
        assert sample_kalshi_market.status == MarketStatus.OPEN

    def test_market_price_validation_yes_price_too_high(self):
        """Test that yes_price > 1 raises ValueError"""
        with pytest.raises(ValueError, match="YES price must be between 0 and 1"):
            Market(
                id="test",
                exchange=Exchange.KALSHI,
                title="Test",
                yes_price=1.5,  # Invalid
                no_price=0.5,
                volume=1000.0,
                liquidity=500.0,
                status=MarketStatus.OPEN
            )

    def test_market_price_validation_yes_price_negative(self):
        """Test that negative yes_price raises ValueError"""
        with pytest.raises(ValueError, match="YES price must be between 0 and 1"):
            Market(
                id="test",
                exchange=Exchange.KALSHI,
                title="Test",
                yes_price=-0.1,  # Invalid
                no_price=0.5,
                volume=1000.0,
                liquidity=500.0,
                status=MarketStatus.OPEN
            )

    def test_market_price_validation_no_price_invalid(self):
        """Test that invalid no_price raises ValueError"""
        with pytest.raises(ValueError, match="NO price must be between 0 and 1"):
            Market(
                id="test",
                exchange=Exchange.KALSHI,
                title="Test",
                yes_price=0.5,
                no_price=1.5,  # Invalid
                volume=1000.0,
                liquidity=500.0,
                status=MarketStatus.OPEN
            )

    def test_market_volume_validation_negative(self):
        """Test that negative volume raises ValueError"""
        with pytest.raises(ValueError, match="Volume must be non-negative"):
            Market(
                id="test",
                exchange=Exchange.KALSHI,
                title="Test",
                yes_price=0.5,
                no_price=0.5,
                volume=-1000.0,  # Invalid
                liquidity=500.0,
                status=MarketStatus.OPEN
            )

    def test_market_liquidity_validation_negative(self):
        """Test that negative liquidity raises ValueError"""
        with pytest.raises(ValueError, match="Liquidity must be non-negative"):
            Market(
                id="test",
                exchange=Exchange.KALSHI,
                title="Test",
                yes_price=0.5,
                no_price=0.5,
                volume=1000.0,
                liquidity=-500.0,  # Invalid
                status=MarketStatus.OPEN
            )

    def test_market_spread_property_perfect_market(self):
        """Test spread calculation for perfect market (yes + no = 1)"""
        market = Market(
            id="test",
            exchange=Exchange.KALSHI,
            title="Test",
            yes_price=0.4,
            no_price=0.6,
            volume=1000.0,
            liquidity=500.0,
            status=MarketStatus.OPEN
        )
        assert market.spread == 0.0

    def test_market_spread_property_imperfect_market(self):
        """Test spread calculation for imperfect market (yes + no != 1)"""
        market = Market(
            id="test",
            exchange=Exchange.KALSHI,
            title="Test",
            yes_price=0.48,
            no_price=0.48,
            volume=1000.0,
            liquidity=500.0,
            status=MarketStatus.OPEN
        )
        # Spread = |(0.48 + 0.48) - 1.0| = 0.04
        assert abs(market.spread - 0.04) < 0.001

    def test_market_is_open_property_true(self, sample_kalshi_market):
        """Test is_open property returns True for open market"""
        assert sample_kalshi_market.is_open is True

    def test_market_is_open_property_false(self, closed_market):
        """Test is_open property returns False for closed market"""
        assert closed_market.is_open is False

    def test_market_with_expiry(self):
        """Test market with expiry date"""
        expiry = datetime.now() + timedelta(days=30)
        market = Market(
            id="test",
            exchange=Exchange.KALSHI,
            title="Test",
            yes_price=0.5,
            no_price=0.5,
            volume=1000.0,
            liquidity=500.0,
            status=MarketStatus.OPEN,
            expiry=expiry
        )
        assert market.expiry == expiry

    def test_market_with_category(self):
        """Test market with category"""
        market = Market(
            id="test",
            exchange=Exchange.KALSHI,
            title="Test",
            yes_price=0.5,
            no_price=0.5,
            volume=1000.0,
            liquidity=500.0,
            status=MarketStatus.OPEN,
            category="politics"
        )
        assert market.category == "politics"


@pytest.mark.unit
class TestOrder:
    """Test Order model"""

    def test_order_creation_valid(self, sample_buy_order):
        """Test creating a valid order"""
        assert sample_buy_order.id == "order_buy_001"
        assert sample_buy_order.side == OrderSide.BUY
        assert sample_buy_order.outcome == Outcome.YES
        assert sample_buy_order.quantity == 100
        assert sample_buy_order.price == 0.40
        assert sample_buy_order.status == OrderStatus.PENDING

    def test_order_total_cost_property(self, sample_buy_order):
        """Test order total_cost property calculation"""
        # Initially 0 because not filled yet
        assert sample_buy_order.total_cost == 0.0

        # After filling, should calculate cost
        sample_buy_order.filled_quantity = 100
        sample_buy_order.average_fill_price = 0.40
        sample_buy_order.fees = 0.50
        # Total = (100 * 0.40) + 0.50 = 40.50
        assert sample_buy_order.total_cost == 40.50

    def test_order_is_filled_property_pending(self, sample_buy_order):
        """Test is_filled property for pending order"""
        assert sample_buy_order.is_filled is False

    def test_order_is_filled_property_filled(self, sample_buy_order):
        """Test is_filled property for filled order"""
        sample_buy_order.status = OrderStatus.FILLED
        assert sample_buy_order.is_filled is True

    def test_order_is_filled_property_partial(self, sample_buy_order):
        """Test is_filled property for partially filled order"""
        sample_buy_order.status = OrderStatus.PARTIAL
        assert sample_buy_order.is_filled is False

    def test_order_fill_time_tracking(self):
        """Test order tracks fill time"""
        order = Order(
            order_id="test_order",
            market_id="test_market",
            exchange=Exchange.KALSHI,
            side=OrderSide.BUY,
            quantity=100,
            price=0.50,
            status=OrderStatus.FILLED,
            timestamp=datetime.now(),
            filled_at=datetime.now()
        )
        assert order.filled_at is not None
        assert order.is_filled is True


@pytest.mark.unit
class TestOpportunity:
    """Test Opportunity model"""

    def test_opportunity_creation_valid(self, sample_opportunity):
        """Test creating a valid opportunity"""
        assert sample_opportunity.outcome == Outcome.YES
        assert sample_opportunity.spread == 0.05
        assert sample_opportunity.expected_profit == 125.50
        assert sample_opportunity.expected_profit_pct == 0.0315
        assert sample_opportunity.confidence_score == 0.85
        assert sample_opportunity.recommended_size == 100

    def test_opportunity_confidence_validation_negative(self, sample_kalshi_market, sample_polymarket_market):
        """Test that negative confidence raises ValueError"""
        with pytest.raises(ValueError, match="Confidence score must be 0-1"):
            Opportunity(
                market_kalshi=sample_kalshi_market,
                market_polymarket=sample_polymarket_market,
                outcome=Outcome.YES,
                spread=0.05,
                expected_profit=100.0,
                expected_profit_pct=0.025,
                confidence_score=-0.1,  # Invalid
                recommended_size=100,
                max_size=500
            )

    def test_opportunity_confidence_validation_too_high(self, sample_kalshi_market, sample_polymarket_market):
        """Test that confidence > 1 raises ValueError"""
        with pytest.raises(ValueError, match="Confidence score must be 0-1"):
            Opportunity(
                market_kalshi=sample_kalshi_market,
                market_polymarket=sample_polymarket_market,
                outcome=Outcome.YES,
                spread=0.05,
                expected_profit=100.0,
                expected_profit_pct=0.025,
                confidence_score=1.5,  # Invalid
                recommended_size=100,
                max_size=500
            )

    def test_opportunity_spread_validation_negative(self, sample_kalshi_market, sample_polymarket_market):
        """Test that negative spread raises ValueError"""
        with pytest.raises(ValueError, match="Spread cannot be negative"):
            Opportunity(
                market_kalshi=sample_kalshi_market,
                market_polymarket=sample_polymarket_market,
                outcome=Outcome.YES,
                spread=-0.05,  # Invalid
                expected_profit=100.0,
                expected_profit_pct=0.025,
                confidence_score=0.8,
                recommended_size=100,
                max_size=500
            )

    def test_opportunity_size_validation_zero(self, sample_kalshi_market, sample_polymarket_market):
        """Test that zero recommended_size raises ValueError"""
        with pytest.raises(ValueError, match="Recommended size must be positive"):
            Opportunity(
                market_kalshi=sample_kalshi_market,
                market_polymarket=sample_polymarket_market,
                outcome=Outcome.YES,
                spread=0.05,
                expected_profit=100.0,
                expected_profit_pct=0.025,
                confidence_score=0.8,
                recommended_size=0,  # Invalid
                max_size=500
            )

    def test_opportunity_determines_buy_sell_exchanges_yes_outcome(self):
        """Test that opportunity correctly determines buy/sell exchanges for YES outcome"""
        kalshi_market = Market(
            id="k1", exchange=Exchange.KALSHI, title="Test",
            yes_price=0.40, no_price=0.60,
            volume=1000.0, liquidity=500.0, status=MarketStatus.OPEN
        )
        poly_market = Market(
            id="p1", exchange=Exchange.POLYMARKET, title="Test",
            yes_price=0.45, no_price=0.55,
            volume=1000.0, liquidity=500.0, status=MarketStatus.OPEN
        )

        opp = Opportunity(
            market_kalshi=kalshi_market,
            market_polymarket=poly_market,
            outcome=Outcome.YES,
            spread=0.05,
            expected_profit=100.0,
            expected_profit_pct=0.025,
            confidence_score=0.8,
            recommended_size=100,
            max_size=500
        )

        # Buy on Kalshi (cheaper at 0.40), sell on Polymarket (higher at 0.45)
        assert opp.buy_exchange == "kalshi"
        assert opp.sell_exchange == "polymarket"
        assert opp.buy_price == 0.40
        assert opp.sell_price == 0.45

    def test_opportunity_determines_buy_sell_exchanges_no_outcome(self):
        """Test that opportunity correctly determines buy/sell exchanges for NO outcome"""
        kalshi_market = Market(
            id="k1", exchange=Exchange.KALSHI, title="Test",
            yes_price=0.40, no_price=0.60,
            volume=1000.0, liquidity=500.0, status=MarketStatus.OPEN
        )
        poly_market = Market(
            id="p1", exchange=Exchange.POLYMARKET, title="Test",
            yes_price=0.45, no_price=0.55,
            volume=1000.0, liquidity=500.0, status=MarketStatus.OPEN
        )

        opp = Opportunity(
            market_kalshi=kalshi_market,
            market_polymarket=poly_market,
            outcome=Outcome.NO,
            spread=0.05,
            expected_profit=100.0,
            expected_profit_pct=0.025,
            confidence_score=0.8,
            recommended_size=100,
            max_size=500
        )

        # Buy on Polymarket (cheaper at 0.55), sell on Kalshi (higher at 0.60)
        assert opp.buy_exchange == "polymarket"
        assert opp.sell_exchange == "kalshi"
        assert opp.buy_price == 0.55
        assert opp.sell_price == 0.60

    def test_opportunity_is_profitable_property_true(self, sample_opportunity):
        """Test is_profitable property returns True for profitable opportunity"""
        assert sample_opportunity.is_profitable is True

    def test_opportunity_is_profitable_property_false(self, sample_kalshi_market, sample_polymarket_market):
        """Test is_profitable property returns False for unprofitable opportunity"""
        opp = Opportunity(
            market_kalshi=sample_kalshi_market,
            market_polymarket=sample_polymarket_market,
            outcome=Outcome.YES,
            spread=0.01,
            expected_profit=-10.0,  # Negative profit
            expected_profit_pct=-0.005,
            confidence_score=0.8,
            recommended_size=100,
            max_size=500
        )
        assert opp.is_profitable is False

    def test_opportunity_profit_per_contract_property(self, sample_opportunity):
        """Test profit_per_contract property calculation"""
        # 125.50 / 100 = 1.255
        assert abs(sample_opportunity.profit_per_contract - 1.255) < 0.001

    def test_opportunity_is_expired_property_not_expired(self, sample_opportunity):
        """Test is_expired property for active opportunity"""
        assert sample_opportunity.is_expired is False

    def test_opportunity_is_expired_property_expired(self, expired_opportunity):
        """Test is_expired property for expired opportunity"""
        assert expired_opportunity.is_expired is True

    def test_opportunity_no_expiry(self, sample_kalshi_market, sample_polymarket_market):
        """Test opportunity without expiry date"""
        opp = Opportunity(
            market_kalshi=sample_kalshi_market,
            market_polymarket=sample_polymarket_market,
            outcome=Outcome.YES,
            spread=0.05,
            expected_profit=100.0,
            expected_profit_pct=0.025,
            confidence_score=0.8,
            recommended_size=100,
            max_size=500,
            expiry=None
        )
        assert opp.is_expired is False


@pytest.mark.unit
class TestPosition:
    """Test Position model"""

    def test_position_creation_valid(self, sample_position):
        """Test creating a valid position"""
        assert sample_position.position_id == "pos_001"
        assert sample_position.outcome == Outcome.YES
        assert sample_position.quantity == 100
        assert sample_position.avg_entry_price == 0.40

    def test_position_tracks_timestamp(self, sample_position):
        """Test that position tracks timestamp"""
        assert sample_position.timestamp is not None
        assert isinstance(sample_position.timestamp, datetime)

    def test_position_unrealized_pnl(self, sample_position):
        """Test unrealized P&L calculation"""
        # Current price is 0.45, entry was 0.40, quantity 100
        # P&L = (100 * 0.45) - 40.0 = 5.0
        assert sample_position.unrealized_pnl == 5.0

    def test_position_is_profitable(self, sample_position):
        """Test is_profitable property"""
        assert sample_position.is_profitable is True
