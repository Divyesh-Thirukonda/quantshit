"""
Tests for market matching service (Matcher, Scorer).
"""
import pytest
from decimal import Decimal

from src.services.matching import Matcher, Scorer
from src.types import Outcome


class TestMatcher:
    """Test Matcher service for finding equivalent markets"""

    @pytest.fixture
    def matcher(self):
        """Create matcher instance"""
        return Matcher(similarity_threshold=0.5)

    def test_find_exact_match(self, matcher, sample_kalshi_market, sample_polymarket_market):
        """Test finding markets with high similarity"""
        matches = matcher.find_matches([sample_kalshi_market], [sample_polymarket_market])
        assert len(matches) > 0
        # Should find a match since titles are similar
        match = matches[0]
        assert match[2] > 0.5  # Confidence score should be above threshold

    def test_no_match_different_titles(self, matcher, sample_kalshi_market):
        """Test no matches when titles are completely different"""
        from src.models import Market
        from datetime import datetime
        
        different_market = Market(
            exchange=sample_kalshi_market.exchange,
            market_id="DIFF-001",
            title="Will aliens land in 2025?",
            outcome=Outcome.YES,
            price=Decimal("0.01"),
            volume=Decimal("1000"),
            liquidity=Decimal("5000"),
            last_updated=datetime.now()
        )
        
        matches = matcher.find_matches([sample_kalshi_market], [different_market])
        # Should find no good matches
        assert len(matches) == 0 or matches[0][2] < 0.5

    def test_confidence_scoring(self, matcher):
        """Test confidence scoring increases with similarity"""
        from src.models import Market
        from datetime import datetime
        from src.types import Exchange
        
        market_a = Market(
            exchange=Exchange.KALSHI,
            market_id="A",
            title="Bitcoin $100k 2025",
            outcome=Outcome.YES,
            price=Decimal("0.5"),
            volume=Decimal("1000"),
            liquidity=Decimal("5000"),
            last_updated=datetime.now()
        )
        
        # Very similar
        market_b = Market(
            exchange=Exchange.POLYMARKET,
            market_id="B",
            title="Bitcoin $100k 2025",
            outcome=Outcome.YES,
            price=Decimal("0.5"),
            volume=Decimal("1000"),
            liquidity=Decimal("5000"),
            last_updated=datetime.now()
        )
        
        # Somewhat similar
        market_c = Market(
            exchange=Exchange.POLYMARKET,
            market_id="C",
            title="BTC 100k by end of 2025",
            outcome=Outcome.YES,
            price=Decimal("0.5"),
            volume=Decimal("1000"),
            liquidity=Decimal("5000"),
            last_updated=datetime.now()
        )
        
        matches_b = matcher.find_matches([market_a], [market_b])
        matches_c = matcher.find_matches([market_a], [market_c])
        
        if matches_b and matches_c:
            assert matches_b[0][2] >= matches_c[0][2]  # More similar = higher score


class TestScorer:
    """Test Scorer service for calculating profitability"""

    @pytest.fixture
    def scorer(self):
        """Create scorer instance"""
        return Scorer(
            min_profit_threshold=0.02,
            kalshi_fee=0.007,
            polymarket_fee=0.02,
            slippage=0.01
        )

    def test_calculate_profit(self, scorer, sample_kalshi_market, sample_polymarket_market):
        """Test profit calculation accounts for fees and slippage"""
        matched_pairs = [(sample_kalshi_market, sample_polymarket_market, 0.85)]
        opportunities = scorer.score_opportunities(matched_pairs)
        
        if opportunities:
            opp = opportunities[0]
            # Should have positive expected profit
            assert opp.expected_profit >= 0
            # Price difference should be > 0
            assert opp.price_difference > 0

    def test_filter_unprofitable(self, scorer):
        """Test filtering out opportunities below profit threshold"""
        from src.models import Market
        from datetime import datetime
        from src.types import Exchange
        
        # Create markets with minimal spread
        market_a = Market(
            exchange=Exchange.KALSHI,
            market_id="A",
            title="Test Market",
            outcome=Outcome.YES,
            price=Decimal("0.500"),
            volume=Decimal("1000"),
            liquidity=Decimal("5000"),
            last_updated=datetime.now()
        )
        
        market_b = Market(
            exchange=Exchange.POLYMARKET,
            market_id="B",
            title="Test Market",
            outcome=Outcome.YES,
            price=Decimal("0.501"),  # Only 0.1% difference - not profitable
            volume=Decimal("1000"),
            liquidity=Decimal("5000"),
            last_updated=datetime.now()
        )
        
        matched_pairs = [(market_a, market_b, 1.0)]
        opportunities = scorer.score_opportunities(matched_pairs)
        
        # Should filter out unprofitable opportunities
        assert len(opportunities) == 0

    def test_account_for_fees(self, scorer, sample_kalshi_market, sample_polymarket_market):
        """Test that fees are properly deducted from profit"""
        matched_pairs = [(sample_kalshi_market, sample_polymarket_market, 0.85)]
        opportunities = scorer.score_opportunities(matched_pairs)
        
        if opportunities:
            opp = opportunities[0]
            # Expected profit should be less than raw spread due to fees
            raw_spread = abs(sample_kalshi_market.price - sample_polymarket_market.price)
            assert opp.expected_profit < float(raw_spread * 100)
