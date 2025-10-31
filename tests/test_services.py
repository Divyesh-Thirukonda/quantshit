"""
Comprehensive unit tests for the services layer.
Tests matching, scoring, validation, and execution logic.
"""
import pytest
from datetime import datetime, timedelta
from unittest.mock import Mock, patch

from src.types import Exchange, OrderSide, OrderStatus, MarketStatus, Outcome
from src.models import Market, Order, Opportunity
from src.services.matching.matcher import Matcher
from src.services.matching.scorer import Scorer
from src.services.execution.validator import Validator, ValidationResult
from src.config import constants


@pytest.mark.unit
class TestMatcher:
    """Test Matcher service for finding equivalent markets across exchanges"""

    def test_matcher_initialization(self):
        """Test matcher initializes with correct threshold"""
        matcher = Matcher(similarity_threshold=0.7)
        assert matcher.similarity_threshold == 0.7

    def test_matcher_initialization_default_threshold(self):
        """Test matcher uses default threshold from constants"""
        matcher = Matcher()
        assert matcher.similarity_threshold == constants.TITLE_SIMILARITY_THRESHOLD

    def test_find_matches_identical_titles(self, sample_kalshi_markets, sample_polymarket_markets):
        """Test matcher finds markets with identical titles"""
        matcher = Matcher(similarity_threshold=0.5)
        matches = matcher.find_matches(sample_kalshi_markets, sample_polymarket_markets)

        # Should find at least the Trump markets which are very similar
        assert len(matches) > 0

        # Verify match structure
        for kalshi_market, poly_market, confidence in matches:
            assert isinstance(kalshi_market, Market)
            assert isinstance(poly_market, Market)
            assert 0.0 <= confidence <= 1.0

    def test_find_matches_no_matches(self):
        """Test matcher returns empty list when no markets match"""
        kalshi_markets = [
            Market(
                id="k1", exchange=Exchange.KALSHI,
                title="Bitcoin will hit $100k",
                yes_price=0.5, no_price=0.5,
                volume=1000.0, liquidity=500.0,
                status=MarketStatus.OPEN
            )
        ]
        poly_markets = [
            Market(
                id="p1", exchange=Exchange.POLYMARKET,
                title="Ethereum will hit $10k",
                yes_price=0.5, no_price=0.5,
                volume=1000.0, liquidity=500.0,
                status=MarketStatus.OPEN
            )
        ]

        matcher = Matcher(similarity_threshold=0.8)
        matches = matcher.find_matches(kalshi_markets, poly_markets)
        assert len(matches) == 0

    def test_normalize_title_lowercase(self):
        """Test title normalization converts to lowercase"""
        matcher = Matcher()
        normalized = matcher._normalize_title("TRUMP WINS 2024")
        assert normalized == "trump wins 2024"

    def test_normalize_title_removes_special_chars(self):
        """Test title normalization removes special characters"""
        matcher = Matcher()
        normalized = matcher._normalize_title("Trump wins 2024? Yes!")
        assert normalized == "trump wins 2024 yes"

    def test_normalize_title_normalizes_whitespace(self):
        """Test title normalization fixes whitespace"""
        matcher = Matcher()
        normalized = matcher._normalize_title("Trump  wins    2024")
        assert normalized == "trump wins 2024"

    def test_calculate_similarity_identical_titles(self):
        """Test similarity calculation for identical titles"""
        matcher = Matcher()
        market1 = Market(
            id="1", exchange=Exchange.KALSHI, title="Trump wins 2024",
            yes_price=0.5, no_price=0.5, volume=1000.0, liquidity=500.0,
            status=MarketStatus.OPEN
        )
        market2 = Market(
            id="2", exchange=Exchange.POLYMARKET, title="Trump wins 2024",
            yes_price=0.5, no_price=0.5, volume=1000.0, liquidity=500.0,
            status=MarketStatus.OPEN
        )
        similarity = matcher._calculate_similarity(market1, market2)
        assert similarity == 1.0

    def test_calculate_similarity_completely_different(self):
        """Test similarity calculation for completely different titles"""
        matcher = Matcher()
        market1 = Market(
            id="1", exchange=Exchange.KALSHI, title="Bitcoin price prediction",
            yes_price=0.5, no_price=0.5, volume=1000.0, liquidity=500.0,
            status=MarketStatus.OPEN
        )
        market2 = Market(
            id="2", exchange=Exchange.POLYMARKET, title="Chiefs win Super Bowl",
            yes_price=0.5, no_price=0.5, volume=1000.0, liquidity=500.0,
            status=MarketStatus.OPEN
        )
        similarity = matcher._calculate_similarity(market1, market2)
        assert similarity == 0.0

    def test_calculate_similarity_partial_match(self):
        """Test similarity calculation for partial match"""
        matcher = Matcher()
        market1 = Market(
            id="1", exchange=Exchange.KALSHI, title="Trump wins 2024 election",
            yes_price=0.5, no_price=0.5, volume=1000.0, liquidity=500.0,
            status=MarketStatus.OPEN
        )
        market2 = Market(
            id="2", exchange=Exchange.POLYMARKET, title="Trump 2024 presidential victory",
            yes_price=0.5, no_price=0.5, volume=1000.0, liquidity=500.0,
            status=MarketStatus.OPEN
        )
        similarity = matcher._calculate_similarity(market1, market2)
        # Should have some overlap on "trump" and "2024"
        assert 0.0 < similarity < 1.0

    def test_check_key_terms_match_adds_bonus(self):
        """Test that matching key terms adds bonus to similarity"""
        matcher = Matcher()
        words1 = {"trump", "wins", "election"}
        words2 = {"trump", "victory", "election"}
        bonus = matcher._check_key_terms_match(words1, words2)
        # Should get bonus for "trump"
        assert bonus > 0.0
        assert bonus <= 0.2

    def test_find_matches_respects_threshold(self):
        """Test that matcher only returns matches above threshold"""
        kalshi_markets = [
            Market(
                id="k1", exchange=Exchange.KALSHI,
                title="Trump wins 2024 election",
                yes_price=0.5, no_price=0.5,
                volume=1000.0, liquidity=500.0,
                status=MarketStatus.OPEN
            )
        ]
        poly_markets = [
            Market(
                id="p1", exchange=Exchange.POLYMARKET,
                title="Trump 2024 victory",  # Partial match
                yes_price=0.5, no_price=0.5,
                volume=1000.0, liquidity=500.0,
                status=MarketStatus.OPEN
            )
        ]

        # With high threshold, should not match
        matcher = Matcher(similarity_threshold=0.9)
        matches = matcher.find_matches(kalshi_markets, poly_markets)
        assert len(matches) == 0

        # With low threshold, should match
        matcher = Matcher(similarity_threshold=0.3)
        matches = matcher.find_matches(kalshi_markets, poly_markets)
        assert len(matches) > 0


@pytest.mark.unit
class TestScorer:
    """Test Scorer service for calculating opportunity profitability"""

    def test_scorer_initialization(self):
        """Test scorer initializes with correct parameters"""
        scorer = Scorer(
            min_profit_threshold=0.03,
            kalshi_fee=0.01,
            polymarket_fee=0.02,
            slippage=0.01
        )
        assert scorer.min_profit_threshold == 0.03
        assert scorer.kalshi_fee == 0.01
        assert scorer.polymarket_fee == 0.02
        assert scorer.slippage == 0.01

    def test_scorer_initialization_defaults(self):
        """Test scorer uses defaults from constants"""
        scorer = Scorer()
        assert scorer.min_profit_threshold == constants.MIN_PROFIT_THRESHOLD
        assert scorer.kalshi_fee == constants.FEE_KALSHI
        assert scorer.polymarket_fee == constants.FEE_POLYMARKET

    def test_score_opportunities_finds_profitable(self, sample_kalshi_markets, sample_polymarket_markets):
        """Test scorer finds profitable opportunities"""
        scorer = Scorer()
        matcher = Matcher(similarity_threshold=0.5)

        # First match the markets
        matched_pairs = matcher.find_matches(sample_kalshi_markets, sample_polymarket_markets)

        # Then score them
        opportunities = scorer.score_opportunities(matched_pairs)

        # Should find at least one profitable opportunity from Trump markets
        # Kalshi: 0.52, Polymarket: 0.48 - there's a spread
        assert isinstance(opportunities, list)
        for opp in opportunities:
            assert isinstance(opp, Opportunity)
            assert opp.is_profitable

    def test_score_opportunities_sorted_by_profit(self):
        """Test that opportunities are sorted by expected profit"""
        kalshi_markets = [
            Market(
                id="k1", exchange=Exchange.KALSHI, title="Market 1",
                yes_price=0.40, no_price=0.60,
                volume=100000.0, liquidity=50000.0, status=MarketStatus.OPEN
            ),
            Market(
                id="k2", exchange=Exchange.KALSHI, title="Market 2",
                yes_price=0.30, no_price=0.70,
                volume=100000.0, liquidity=50000.0, status=MarketStatus.OPEN
            )
        ]
        poly_markets = [
            Market(
                id="p1", exchange=Exchange.POLYMARKET, title="Market 1",
                yes_price=0.50, no_price=0.50,  # 10% spread on YES
                volume=100000.0, liquidity=50000.0, status=MarketStatus.OPEN
            ),
            Market(
                id="p2", exchange=Exchange.POLYMARKET, title="Market 2",
                yes_price=0.35, no_price=0.65,  # 5% spread on YES
                volume=100000.0, liquidity=50000.0, status=MarketStatus.OPEN
            )
        ]

        scorer = Scorer()
        matched_pairs = [
            (kalshi_markets[0], poly_markets[0], 1.0),
            (kalshi_markets[1], poly_markets[1], 1.0)
        ]

        opportunities = scorer.score_opportunities(matched_pairs)

        # Should be sorted by profit (highest first)
        if len(opportunities) >= 2:
            assert opportunities[0].expected_profit >= opportunities[1].expected_profit

    def test_calculate_opportunity_yes_outcome(self):
        """Test calculating opportunity for YES outcome"""
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

        scorer = Scorer()
        opp = scorer._calculate_opportunity(kalshi_market, poly_market, Outcome.YES, 1.0)

        assert opp.outcome == Outcome.YES
        assert opp.spread == 0.10  # |0.40 - 0.50|
        assert opp.recommended_size > 0
        assert opp.confidence_score == 1.0

    def test_calculate_opportunity_no_outcome(self):
        """Test calculating opportunity for NO outcome"""
        kalshi_market = Market(
            id="k1", exchange=Exchange.KALSHI, title="Test",
            yes_price=0.40, no_price=0.60,
            volume=10000.0, liquidity=5000.0, status=MarketStatus.OPEN
        )
        poly_market = Market(
            id="p1", exchange=Exchange.POLYMARKET, title="Test",
            yes_price=0.45, no_price=0.55,
            volume=10000.0, liquidity=5000.0, status=MarketStatus.OPEN
        )

        scorer = Scorer()
        opp = scorer._calculate_opportunity(kalshi_market, poly_market, Outcome.NO, 1.0)

        assert opp.outcome == Outcome.NO
        assert opp.spread == 0.05  # |0.60 - 0.55|

    def test_calculate_opportunity_includes_fees(self):
        """Test that opportunity calculation includes fees"""
        kalshi_market = Market(
            id="k1", exchange=Exchange.KALSHI, title="Test",
            yes_price=0.40, no_price=0.60,
            volume=100000.0, liquidity=50000.0, status=MarketStatus.OPEN
        )
        poly_market = Market(
            id="p1", exchange=Exchange.POLYMARKET, title="Test",
            yes_price=0.50, no_price=0.50,
            volume=100000.0, liquidity=50000.0, status=MarketStatus.OPEN
        )

        scorer = Scorer(kalshi_fee=0.01, polymarket_fee=0.02, slippage=0.005)
        opp = scorer._calculate_opportunity(kalshi_market, poly_market, Outcome.YES, 1.0)

        # Profit should be less than naive spread due to fees
        naive_profit = (0.50 - 0.40) * opp.recommended_size
        assert opp.expected_profit < naive_profit

    def test_calculate_opportunity_respects_liquidity_limits(self):
        """Test that opportunity respects available liquidity"""
        kalshi_market = Market(
            id="k1", exchange=Exchange.KALSHI, title="Test",
            yes_price=0.40, no_price=0.60,
            volume=10000.0, liquidity=50.0,  # Low liquidity
            status=MarketStatus.OPEN
        )
        poly_market = Market(
            id="p1", exchange=Exchange.POLYMARKET, title="Test",
            yes_price=0.50, no_price=0.50,
            volume=10000.0, liquidity=100.0,
            status=MarketStatus.OPEN
        )

        scorer = Scorer()
        opp = scorer._calculate_opportunity(kalshi_market, poly_market, Outcome.YES, 1.0)

        # Max size should be limited by lower liquidity (50)
        assert opp.max_size <= 50

    def test_calculate_opportunity_respects_max_position_size(self):
        """Test that opportunity respects MAX_POSITION_SIZE constant"""
        kalshi_market = Market(
            id="k1", exchange=Exchange.KALSHI, title="Test",
            yes_price=0.40, no_price=0.60,
            volume=1000000.0, liquidity=500000.0,  # Huge liquidity
            status=MarketStatus.OPEN
        )
        poly_market = Market(
            id="p1", exchange=Exchange.POLYMARKET, title="Test",
            yes_price=0.50, no_price=0.50,
            volume=1000000.0, liquidity=500000.0,
            status=MarketStatus.OPEN
        )

        scorer = Scorer()
        opp = scorer._calculate_opportunity(kalshi_market, poly_market, Outcome.YES, 1.0)

        # Recommended size should not exceed MAX_POSITION_SIZE
        assert opp.recommended_size <= constants.MAX_POSITION_SIZE


@pytest.mark.unit
class TestValidator:
    """Test Validator service for pre-trade safety checks"""

    def test_validator_initialization(self):
        """Test validator initializes with correct capital"""
        validator = Validator(available_capital=5000.0)
        assert validator.available_capital == 5000.0

    def test_validator_initialization_default(self):
        """Test validator uses default capital from constants"""
        validator = Validator()
        expected_capital = constants.INITIAL_CAPITAL_PER_EXCHANGE * 2
        assert validator.available_capital == expected_capital

    def test_validate_profitable_opportunity_passes(self, sample_opportunity):
        """Test that profitable opportunity passes validation"""
        validator = Validator(available_capital=10000.0)
        result = validator.validate(sample_opportunity)

        assert isinstance(result, ValidationResult)
        assert result.valid is True
        assert result.reason is not None

    def test_validate_unprofitable_opportunity_fails(self, sample_kalshi_market, sample_polymarket_market):
        """Test that unprofitable opportunity fails validation"""
        unprofitable_opp = Opportunity(
            market_kalshi=sample_kalshi_market,
            market_polymarket=sample_polymarket_market,
            outcome=Outcome.YES,
            spread=0.01,
            expected_profit=-10.0,  # Negative profit
            expected_profit_pct=-0.01,
            confidence_score=0.8,
            recommended_size=100,
            max_size=500
        )

        validator = Validator(available_capital=10000.0)
        result = validator.validate(unprofitable_opp)

        assert result.valid is False
        assert "not profitable" in result.reason.lower()

    def test_validate_low_profit_threshold_fails(self, sample_kalshi_market, sample_polymarket_market):
        """Test that opportunity below profit threshold fails"""
        low_profit_opp = Opportunity(
            market_kalshi=sample_kalshi_market,
            market_polymarket=sample_polymarket_market,
            outcome=Outcome.YES,
            spread=0.01,
            expected_profit=10.0,
            expected_profit_pct=0.005,  # 0.5%, below 2% threshold
            confidence_score=0.8,
            recommended_size=100,
            max_size=500
        )

        validator = Validator(available_capital=10000.0)
        result = validator.validate(low_profit_opp)

        assert result.valid is False
        assert "threshold" in result.reason.lower()

    def test_validate_closed_market_fails(self, sample_opportunity, closed_market):
        """Test that opportunity with closed market fails"""
        sample_opportunity.market_kalshi = closed_market

        validator = Validator(available_capital=10000.0)
        result = validator.validate(sample_opportunity)

        assert result.valid is False
        assert "closed" in result.reason.lower()

    def test_validate_expired_opportunity_fails(self, expired_opportunity):
        """Test that expired opportunity fails validation"""
        validator = Validator(available_capital=10000.0)
        result = validator.validate(expired_opportunity)

        assert result.valid is False
        assert "expired" in result.reason.lower()

    def test_validate_low_confidence_fails(self, low_confidence_opportunity):
        """Test that low confidence opportunity fails"""
        validator = Validator(available_capital=10000.0)
        result = validator.validate(low_confidence_opportunity)

        assert result.valid is False
        assert "confidence" in result.reason.lower()

    def test_validate_insufficient_capital_fails(self, sample_opportunity):
        """Test that opportunity requiring more capital than available fails"""
        validator = Validator(available_capital=10.0)  # Very low capital
        result = validator.validate(sample_opportunity)

        assert result.valid is False
        assert "capital" in result.reason.lower()

    def test_validate_position_size_too_large_fails(self, sample_kalshi_market, sample_polymarket_market):
        """Test that position size exceeding max fails"""
        huge_position_opp = Opportunity(
            market_kalshi=sample_kalshi_market,
            market_polymarket=sample_polymarket_market,
            outcome=Outcome.YES,
            spread=0.05,
            expected_profit=1000.0,
            expected_profit_pct=0.05,
            confidence_score=0.8,
            recommended_size=constants.MAX_POSITION_SIZE + 1,  # Too large
            max_size=5000
        )

        validator = Validator(available_capital=100000.0)
        result = validator.validate(huge_position_opp)

        assert result.valid is False
        assert "exceeds maximum" in result.reason.lower()

    def test_validate_position_size_too_small_fails(self, sample_kalshi_market, sample_polymarket_market):
        """Test that position size below minimum fails"""
        tiny_position_opp = Opportunity(
            market_kalshi=sample_kalshi_market,
            market_polymarket=sample_polymarket_market,
            outcome=Outcome.YES,
            spread=0.05,
            expected_profit=5.0,
            expected_profit_pct=0.05,
            confidence_score=0.8,
            recommended_size=constants.MIN_POSITION_SIZE - 1,  # Too small
            max_size=500
        )

        validator = Validator(available_capital=10000.0)
        result = validator.validate(tiny_position_opp)

        assert result.valid is False
        assert "below minimum" in result.reason.lower()

    def test_update_available_capital(self):
        """Test updating available capital"""
        validator = Validator(available_capital=10000.0)
        validator.update_available_capital(8000.0)
        assert validator.available_capital == 8000.0
