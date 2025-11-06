"""
Tests for trading strategies.
"""
import pytest
from decimal import Decimal

from src.strategies import SimpleArbitrageStrategy, SimpleArbitrageConfig
from src.models import Position


class TestSimpleArbitrageStrategy:
    """Test SimpleArbitrageStrategy"""

    @pytest.fixture
    def strategy(self):
        """Create strategy instance with test config"""
        config = SimpleArbitrageConfig(
            min_volume=1000.0,
            min_profit_pct=0.02,
            min_confidence=0.5,
            max_position_size=1000,
            min_position_size=10
        )
        return SimpleArbitrageStrategy(config=config)

    def test_select_best_opportunity(self, strategy, sample_opportunity):
        """Test selecting best opportunity from list"""
        opportunities = [sample_opportunity]
        best = strategy.select_best_opportunity(opportunities)
        
        assert best is not None
        assert best.opportunity_id == sample_opportunity.opportunity_id

    def test_select_highest_profit(self, strategy, sample_opportunity):
        """Test selects opportunity with highest profit"""
        from src.models import Opportunity
        from datetime import datetime
        from src.types import Outcome
        
        # Create second opportunity with higher profit
        high_profit_opp = Opportunity(
            opportunity_id="OPP-HIGH",
            market_kalshi=sample_opportunity.market_kalshi,
            market_polymarket=sample_opportunity.market_polymarket,
            outcome=Outcome.YES,
            price_difference=Decimal("0.10"),
            expected_profit=Decimal("50.00"),  # Higher than sample
            expected_profit_pct=Decimal("0.08"),
            confidence_score=0.85,
            discovered_at=datetime.now()
        )
        
        opportunities = [sample_opportunity, high_profit_opp]
        best = strategy.select_best_opportunity(opportunities)
        
        assert best.opportunity_id == "OPP-HIGH"

    def test_filter_low_confidence(self, strategy, sample_opportunity):
        """Test filters out low confidence opportunities"""
        sample_opportunity.confidence_score = 0.3  # Below threshold
        
        opportunities = [sample_opportunity]
        best = strategy.select_best_opportunity(opportunities)
        
        # Should not select low confidence opportunity
        assert best is None

    def test_filter_low_volume(self, strategy, sample_opportunity):
        """Test filters out low volume opportunities"""
        sample_opportunity.market_kalshi.volume = Decimal("100")  # Too low
        sample_opportunity.market_polymarket.volume = Decimal("100")
        
        opportunities = [sample_opportunity]
        best = strategy.select_best_opportunity(opportunities)
        
        # Should not select low volume opportunity
        assert best is None

    def test_should_close_position(self, strategy, sample_position):
        """Test position closing logic"""
        # Update position with current prices
        sample_position.current_price_kalshi = Decimal("0.70")
        sample_position.current_price_polymarket = Decimal("0.68")
        
        should_close = strategy.should_close_position(sample_position)
        
        # Should return a boolean
        assert isinstance(should_close, bool)

    def test_empty_opportunities(self, strategy):
        """Test handling of empty opportunity list"""
        opportunities = []
        best = strategy.select_best_opportunity(opportunities)
        
        assert best is None
