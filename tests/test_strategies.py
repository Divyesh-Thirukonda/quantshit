"""
Comprehensive unit tests for trading strategies.
Tests strategy logic, filtering, ranking, and position sizing.
"""
import pytest
from datetime import datetime, timedelta
from unittest.mock import Mock

from src.types import Exchange, MarketStatus, Outcome
from src.models import Market, Opportunity, Position, Order
from src.strategies.simple_arb import SimpleArbitrageStrategy
from src.config import constants


@pytest.mark.unit
class TestSimpleArbitrageStrategy:
    """Test Simple Arbitrage Strategy"""

    def test_strategy_initialization(self):
        """Test strategy initializes with correct parameters"""
        strategy = SimpleArbitrageStrategy(min_profit_pct=0.03, min_confidence=0.7)
        assert strategy.name == "Simple Arbitrage"
        assert strategy.min_profit_pct == 0.03
        assert strategy.min_confidence == 0.7

    def test_strategy_initialization_defaults(self):
        """Test strategy uses default parameters from constants"""
        strategy = SimpleArbitrageStrategy()
        assert strategy.min_profit_pct == constants.MIN_PROFIT_THRESHOLD
        assert strategy.min_confidence == constants.MIN_CONFIDENCE_SCORE

    def test_filter_opportunities_passes_profitable(self, sample_opportunity):
        """Test that profitable opportunities pass filtering"""
        strategy = SimpleArbitrageStrategy()
        opportunities = [sample_opportunity]

        filtered = strategy.filter_opportunities(opportunities)

        assert len(filtered) == 1
        assert filtered[0] == sample_opportunity

    def test_filter_opportunities_rejects_low_profit(self, sample_kalshi_market, sample_polymarket_market):
        """Test that low profit opportunities are filtered out"""
        low_profit_opp = Opportunity(
            market_kalshi=sample_kalshi_market,
            market_polymarket=sample_polymarket_market,
            outcome=Outcome.YES,
            spread=0.01,
            expected_profit=10.0,
            expected_profit_pct=0.005,  # 0.5%, below threshold
            confidence_score=0.8,
            recommended_size=100,
            max_size=500
        )

        strategy = SimpleArbitrageStrategy()
        filtered = strategy.filter_opportunities([low_profit_opp])

        assert len(filtered) == 0

    def test_filter_opportunities_rejects_low_confidence(self, low_confidence_opportunity):
        """Test that low confidence opportunities are filtered out"""
        strategy = SimpleArbitrageStrategy()
        filtered = strategy.filter_opportunities([low_confidence_opportunity])

        assert len(filtered) == 0

    def test_filter_opportunities_rejects_expired(self, expired_opportunity):
        """Test that expired opportunities are filtered out"""
        strategy = SimpleArbitrageStrategy()
        filtered = strategy.filter_opportunities([expired_opportunity])

        assert len(filtered) == 0

    def test_filter_opportunities_rejects_closed_markets(self, sample_opportunity, closed_market):
        """Test that opportunities with closed markets are filtered out"""
        sample_opportunity.market_kalshi = closed_market

        strategy = SimpleArbitrageStrategy()
        filtered = strategy.filter_opportunities([sample_opportunity])

        assert len(filtered) == 0

    def test_filter_opportunities_multiple(self):
        """Test filtering multiple opportunities"""
        kalshi_market = Market(
            id="k1", exchange=Exchange.KALSHI, title="Test",
            yes_price=0.40, no_price=0.60,
            volume=10000.0, liquidity=5000.0, status=MarketStatus.OPEN
        )
        poly_market = Market(
            id="p1", exchange=Exchange.POLYMARKET, title="Test",
            yes_price=0.50, no_price=0.50,
            volume=10000.0, liquidity=5000.0, status=MarketStatus.OPEN
        )

        good_opp = Opportunity(
            market_kalshi=kalshi_market,
            market_polymarket=poly_market,
            outcome=Outcome.YES,
            spread=0.10,
            expected_profit=200.0,
            expected_profit_pct=0.05,
            confidence_score=0.9,
            recommended_size=100,
            max_size=500
        )

        bad_opp = Opportunity(
            market_kalshi=kalshi_market,
            market_polymarket=poly_market,
            outcome=Outcome.YES,
            spread=0.02,
            expected_profit=20.0,
            expected_profit_pct=0.01,  # Below threshold
            confidence_score=0.9,
            recommended_size=100,
            max_size=500
        )

        strategy = SimpleArbitrageStrategy()
        filtered = strategy.filter_opportunities([good_opp, bad_opp])

        assert len(filtered) == 1
        assert filtered[0] == good_opp

    def test_rank_opportunities_by_profit_pct(self):
        """Test that opportunities are ranked by profit percentage"""
        kalshi_market = Market(
            id="k1", exchange=Exchange.KALSHI, title="Test",
            yes_price=0.40, no_price=0.60,
            volume=10000.0, liquidity=5000.0, status=MarketStatus.OPEN
        )
        poly_market = Market(
            id="p1", exchange=Exchange.POLYMARKET, title="Test",
            yes_price=0.50, no_price=0.50,
            volume=10000.0, liquidity=5000.0, status=MarketStatus.OPEN
        )

        opp1 = Opportunity(
            market_kalshi=kalshi_market,
            market_polymarket=poly_market,
            outcome=Outcome.YES,
            spread=0.05,
            expected_profit=100.0,
            expected_profit_pct=0.03,  # 3%
            confidence_score=0.9,
            recommended_size=100,
            max_size=500
        )

        opp2 = Opportunity(
            market_kalshi=kalshi_market,
            market_polymarket=poly_market,
            outcome=Outcome.YES,
            spread=0.10,
            expected_profit=200.0,
            expected_profit_pct=0.05,  # 5% - higher
            confidence_score=0.9,
            recommended_size=100,
            max_size=500
        )

        strategy = SimpleArbitrageStrategy()
        ranked = strategy.rank_opportunities([opp1, opp2])

        # opp2 should be first (higher profit %)
        assert ranked[0] == opp2
        assert ranked[1] == opp1

    def test_rank_opportunities_empty_list(self):
        """Test ranking empty list returns empty list"""
        strategy = SimpleArbitrageStrategy()
        ranked = strategy.rank_opportunities([])
        assert ranked == []

    def test_calculate_position_size_uses_recommended(self, sample_opportunity):
        """Test position size calculation uses recommended size"""
        strategy = SimpleArbitrageStrategy()
        size = strategy.calculate_position_size(
            opportunity=sample_opportunity,
            available_capital=10000.0
        )

        # Should use recommended size from opportunity
        assert size == sample_opportunity.recommended_size

    def test_calculate_position_size_respects_capital_limit(self, sample_opportunity):
        """Test position size is reduced when capital is insufficient"""
        strategy = SimpleArbitrageStrategy()
        size = strategy.calculate_position_size(
            opportunity=sample_opportunity,
            available_capital=20.0  # Very low capital
        )

        # Size should be reduced to fit capital
        capital_required = size * (sample_opportunity.buy_price or 0.5)
        assert capital_required <= 20.0

    def test_calculate_position_size_respects_min_limit(self, sample_opportunity):
        """Test position size respects minimum limit"""
        strategy = SimpleArbitrageStrategy()
        size = strategy.calculate_position_size(
            opportunity=sample_opportunity,
            available_capital=1.0  # Tiny capital
        )

        # Should be at least MIN_POSITION_SIZE
        assert size >= constants.MIN_POSITION_SIZE

    def test_calculate_position_size_respects_max_limit(self):
        """Test position size respects maximum limit"""
        kalshi_market = Market(
            id="k1", exchange=Exchange.KALSHI, title="Test",
            yes_price=0.01, no_price=0.99,  # Very cheap
            volume=1000000.0, liquidity=500000.0, status=MarketStatus.OPEN
        )
        poly_market = Market(
            id="p1", exchange=Exchange.POLYMARKET, title="Test",
            yes_price=0.05, no_price=0.95,
            volume=1000000.0, liquidity=500000.0, status=MarketStatus.OPEN
        )

        huge_opp = Opportunity(
            market_kalshi=kalshi_market,
            market_polymarket=poly_market,
            outcome=Outcome.YES,
            spread=0.04,
            expected_profit=10000.0,
            expected_profit_pct=0.05,
            confidence_score=0.9,
            recommended_size=100000,  # Very large
            max_size=500000
        )

        strategy = SimpleArbitrageStrategy()
        size = strategy.calculate_position_size(
            opportunity=huge_opp,
            available_capital=1000000.0
        )

        # Should not exceed MAX_POSITION_SIZE
        assert size <= constants.MAX_POSITION_SIZE

    def test_should_close_position_take_profit(self):
        """Test that position is closed at take profit target"""
        # Create mock position with high profit
        position = Mock()
        position.position_id = "test_pos"
        position.unrealized_pnl_pct = 10.5  # Above 10% target

        strategy = SimpleArbitrageStrategy()
        should_close = strategy.should_close_position(position)

        assert should_close is True

    def test_should_close_position_stop_loss(self):
        """Test that position is closed at stop loss"""
        # Create mock position with loss
        position = Mock()
        position.position_id = "test_pos"
        position.unrealized_pnl_pct = -6.0  # Below -5% stop loss

        strategy = SimpleArbitrageStrategy()
        should_close = strategy.should_close_position(position)

        assert should_close is True

    def test_should_close_position_partial_profit(self):
        """Test that position is closed at partial profit target"""
        # Create mock position with moderate profit
        position = Mock()
        position.position_id = "test_pos"
        position.unrealized_pnl_pct = 5.5  # Above 5% (50% of take profit)

        strategy = SimpleArbitrageStrategy()
        should_close = strategy.should_close_position(position)

        assert should_close is True

    def test_should_close_position_no_trigger(self):
        """Test that position is not closed when no conditions met"""
        # Create mock position with small profit
        position = Mock()
        position.position_id = "test_pos"
        position.unrealized_pnl_pct = 2.0  # Small profit, no trigger

        strategy = SimpleArbitrageStrategy()
        should_close = strategy.should_close_position(position)

        assert should_close is False

    def test_select_best_opportunity_from_list(self):
        """Test selecting best opportunity from ranked list"""
        kalshi_market = Market(
            id="k1", exchange=Exchange.KALSHI, title="Test",
            yes_price=0.40, no_price=0.60,
            volume=10000.0, liquidity=5000.0, status=MarketStatus.OPEN
        )
        poly_market = Market(
            id="p1", exchange=Exchange.POLYMARKET, title="Test",
            yes_price=0.50, no_price=0.50,
            volume=10000.0, liquidity=5000.0, status=MarketStatus.OPEN
        )

        opp1 = Opportunity(
            market_kalshi=kalshi_market,
            market_polymarket=poly_market,
            outcome=Outcome.YES,
            spread=0.05,
            expected_profit=100.0,
            expected_profit_pct=0.03,
            confidence_score=0.9,
            recommended_size=100,
            max_size=500
        )

        opp2 = Opportunity(
            market_kalshi=kalshi_market,
            market_polymarket=poly_market,
            outcome=Outcome.YES,
            spread=0.10,
            expected_profit=200.0,
            expected_profit_pct=0.05,  # Higher
            confidence_score=0.9,
            recommended_size=100,
            max_size=500
        )

        strategy = SimpleArbitrageStrategy()
        best = strategy.select_best_opportunity([opp1, opp2])

        # Should select opp2 (higher profit)
        assert best == opp2

    def test_select_best_opportunity_empty_list(self):
        """Test selecting from empty list returns None"""
        strategy = SimpleArbitrageStrategy()
        best = strategy.select_best_opportunity([])

        assert best is None
