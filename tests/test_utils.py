"""
Comprehensive unit tests for utility functions.
Tests mathematical calculations, probability conversions, and helper functions.
"""
import pytest
import math

from src.utils.math import (
    calculate_profit,
    price_to_probability,
    probability_to_price,
    calculate_implied_odds,
    kelly_criterion,
    calculate_spread_percentage
)


@pytest.mark.unit
class TestCalculateProfit:
    """Test profit calculation function"""

    def test_profit_no_fees(self):
        """Test profit calculation without fees"""
        profit = calculate_profit(
            buy_price=0.40,
            sell_price=0.50,
            quantity=100,
            buy_fee_pct=0.0,
            sell_fee_pct=0.0
        )
        # (100 * 0.50) - (100 * 0.40) = 10.0
        assert profit == 10.0

    def test_profit_with_buy_fee(self):
        """Test profit calculation with buy fee"""
        profit = calculate_profit(
            buy_price=0.40,
            sell_price=0.50,
            quantity=100,
            buy_fee_pct=0.01,  # 1% buy fee
            sell_fee_pct=0.0
        )
        # Buy cost: 100 * 0.40 * 1.01 = 40.4
        # Sell revenue: 100 * 0.50 = 50.0
        # Profit: 50.0 - 40.4 = 9.6
        assert abs(profit - 9.6) < 0.001

    def test_profit_with_sell_fee(self):
        """Test profit calculation with sell fee"""
        profit = calculate_profit(
            buy_price=0.40,
            sell_price=0.50,
            quantity=100,
            buy_fee_pct=0.0,
            sell_fee_pct=0.02  # 2% sell fee
        )
        # Buy cost: 100 * 0.40 = 40.0
        # Sell revenue: 100 * 0.50 * 0.98 = 49.0
        # Profit: 49.0 - 40.0 = 9.0
        assert abs(profit - 9.0) < 0.001

    def test_profit_with_both_fees(self):
        """Test profit calculation with both fees"""
        profit = calculate_profit(
            buy_price=0.40,
            sell_price=0.50,
            quantity=100,
            buy_fee_pct=0.01,  # 1% buy fee
            sell_fee_pct=0.02  # 2% sell fee
        )
        # Buy cost: 100 * 0.40 * 1.01 = 40.4
        # Sell revenue: 100 * 0.50 * 0.98 = 49.0
        # Profit: 49.0 - 40.4 = 8.6
        assert abs(profit - 8.6) < 0.001

    def test_profit_negative_loss(self):
        """Test profit calculation resulting in loss"""
        profit = calculate_profit(
            buy_price=0.50,
            sell_price=0.40,
            quantity=100,
            buy_fee_pct=0.01,
            sell_fee_pct=0.02
        )
        # Buy cost: 100 * 0.50 * 1.01 = 50.5
        # Sell revenue: 100 * 0.40 * 0.98 = 39.2
        # Profit: 39.2 - 50.5 = -11.3
        assert profit < 0
        assert abs(profit - (-11.3)) < 0.001

    def test_profit_zero_quantity(self):
        """Test profit calculation with zero quantity"""
        profit = calculate_profit(
            buy_price=0.40,
            sell_price=0.50,
            quantity=0,
            buy_fee_pct=0.01,
            sell_fee_pct=0.02
        )
        assert profit == 0.0

    def test_profit_large_quantity(self):
        """Test profit calculation with large quantity"""
        profit = calculate_profit(
            buy_price=0.40,
            sell_price=0.50,
            quantity=10000,
            buy_fee_pct=0.01,
            sell_fee_pct=0.02
        )
        # Buy cost: 10000 * 0.40 * 1.01 = 4040.0
        # Sell revenue: 10000 * 0.50 * 0.98 = 4900.0
        # Profit: 4900.0 - 4040.0 = 860.0
        assert abs(profit - 860.0) < 0.1


@pytest.mark.unit
class TestProbabilityConversions:
    """Test probability and price conversion functions"""

    def test_price_to_probability_valid(self):
        """Test converting valid price to probability"""
        prob = price_to_probability(0.65)
        assert prob == 0.65

    def test_price_to_probability_zero(self):
        """Test converting price of 0 to probability"""
        prob = price_to_probability(0.0)
        assert prob == 0.0

    def test_price_to_probability_one(self):
        """Test converting price of 1 to probability"""
        prob = price_to_probability(1.0)
        assert prob == 1.0

    def test_price_to_probability_invalid_negative(self):
        """Test that negative price raises ValueError"""
        with pytest.raises(ValueError, match="Price must be between 0 and 1"):
            price_to_probability(-0.1)

    def test_price_to_probability_invalid_too_high(self):
        """Test that price > 1 raises ValueError"""
        with pytest.raises(ValueError, match="Price must be between 0 and 1"):
            price_to_probability(1.5)

    def test_probability_to_price_valid(self):
        """Test converting valid probability to price"""
        price = probability_to_price(0.75)
        assert price == 0.75

    def test_probability_to_price_zero(self):
        """Test converting probability of 0 to price"""
        price = probability_to_price(0.0)
        assert price == 0.0

    def test_probability_to_price_one(self):
        """Test converting probability of 1 to price"""
        price = probability_to_price(1.0)
        assert price == 1.0

    def test_probability_to_price_invalid_negative(self):
        """Test that negative probability raises ValueError"""
        with pytest.raises(ValueError, match="Probability must be between 0 and 1"):
            probability_to_price(-0.1)

    def test_probability_to_price_invalid_too_high(self):
        """Test that probability > 1 raises ValueError"""
        with pytest.raises(ValueError, match="Probability must be between 0 and 1"):
            probability_to_price(1.5)

    def test_price_probability_roundtrip(self):
        """Test that converting price to probability and back works"""
        original_price = 0.42
        prob = price_to_probability(original_price)
        result_price = probability_to_price(prob)
        assert result_price == original_price


@pytest.mark.unit
class TestCalculateImpliedOdds:
    """Test implied odds calculation"""

    def test_implied_odds_even_odds(self):
        """Test implied odds for 50/50 market"""
        yes_odds, no_odds = calculate_implied_odds(0.50, 0.50)
        assert yes_odds == 2.0  # 1/0.5 = 2.0
        assert no_odds == 2.0

    def test_implied_odds_biased_market(self):
        """Test implied odds for biased market"""
        yes_odds, no_odds = calculate_implied_odds(0.25, 0.75)
        assert yes_odds == 4.0  # 1/0.25 = 4.0
        assert no_odds == pytest.approx(1.333, rel=0.01)  # 1/0.75 ≈ 1.333

    def test_implied_odds_extreme_market(self):
        """Test implied odds for extreme market"""
        yes_odds, no_odds = calculate_implied_odds(0.01, 0.99)
        assert yes_odds == 100.0  # 1/0.01 = 100.0
        assert no_odds == pytest.approx(1.0101, rel=0.01)  # 1/0.99 ≈ 1.0101

    def test_implied_odds_zero_price(self):
        """Test implied odds with zero price returns infinity"""
        yes_odds, no_odds = calculate_implied_odds(0.0, 1.0)
        assert yes_odds == float('inf')
        assert no_odds == 1.0

    def test_implied_odds_near_zero(self):
        """Test implied odds with near-zero price"""
        yes_odds, no_odds = calculate_implied_odds(0.001, 0.999)
        assert yes_odds == 1000.0
        assert no_odds == pytest.approx(1.001, rel=0.001)


@pytest.mark.unit
class TestKellyCriterion:
    """Test Kelly Criterion position sizing"""

    def test_kelly_favorable_odds(self):
        """Test Kelly criterion with favorable odds"""
        kelly = kelly_criterion(
            win_probability=0.6,
            win_amount=100.0,
            loss_amount=100.0,
            kelly_fraction=1.0
        )
        # Kelly = (0.6 * 1 - 0.4) / 1 = 0.2 (20% of bankroll)
        assert abs(kelly - 0.2) < 0.001

    def test_kelly_fractional_conservative(self):
        """Test Kelly criterion with fractional Kelly for risk management"""
        kelly = kelly_criterion(
            win_probability=0.6,
            win_amount=100.0,
            loss_amount=100.0,
            kelly_fraction=0.25  # Quarter Kelly
        )
        # Full Kelly = 0.2, Quarter Kelly = 0.05
        assert abs(kelly - 0.05) < 0.001

    def test_kelly_unfavorable_odds(self):
        """Test Kelly criterion with unfavorable odds returns 0"""
        kelly = kelly_criterion(
            win_probability=0.4,
            win_amount=100.0,
            loss_amount=100.0,
            kelly_fraction=1.0
        )
        # Kelly = (0.4 * 1 - 0.6) / 1 = -0.2, but capped at 0
        assert kelly == 0.0

    def test_kelly_fifty_fifty(self):
        """Test Kelly criterion with 50/50 odds"""
        kelly = kelly_criterion(
            win_probability=0.5,
            win_amount=100.0,
            loss_amount=100.0,
            kelly_fraction=1.0
        )
        # Kelly = (0.5 * 1 - 0.5) / 1 = 0.0
        assert kelly == 0.0

    def test_kelly_asymmetric_payoff(self):
        """Test Kelly criterion with asymmetric win/loss amounts"""
        kelly = kelly_criterion(
            win_probability=0.5,
            win_amount=200.0,  # Win 2x
            loss_amount=100.0,  # Lose 1x
            kelly_fraction=1.0
        )
        # Kelly = (0.5 * 2 - 0.5) / 2 = 0.25
        assert abs(kelly - 0.25) < 0.001

    def test_kelly_capped_at_one(self):
        """Test that Kelly criterion never exceeds 100% of bankroll"""
        kelly = kelly_criterion(
            win_probability=0.99,
            win_amount=1000.0,
            loss_amount=1.0,
            kelly_fraction=1.0
        )
        # Even with extreme odds, should be capped at 1.0
        assert kelly <= 1.0

    def test_kelly_zero_loss_amount(self):
        """Test Kelly criterion with zero loss amount"""
        kelly = kelly_criterion(
            win_probability=0.6,
            win_amount=100.0,
            loss_amount=0.0,  # No risk
            kelly_fraction=1.0
        )
        # Should return 0 to avoid division by zero
        assert kelly == 0.0

    def test_kelly_invalid_probability_negative(self):
        """Test that invalid probability raises ValueError"""
        with pytest.raises(ValueError, match="Win probability must be 0-1"):
            kelly_criterion(
                win_probability=-0.1,
                win_amount=100.0,
                loss_amount=100.0,
                kelly_fraction=1.0
            )

    def test_kelly_invalid_probability_too_high(self):
        """Test that probability > 1 raises ValueError"""
        with pytest.raises(ValueError, match="Win probability must be 0-1"):
            kelly_criterion(
                win_probability=1.5,
                win_amount=100.0,
                loss_amount=100.0,
                kelly_fraction=1.0
            )


@pytest.mark.unit
class TestCalculateSpreadPercentage:
    """Test spread percentage calculation"""

    def test_spread_percentage_equal_prices(self):
        """Test spread percentage for equal prices"""
        spread = calculate_spread_percentage(0.50, 0.50)
        assert spread == 0.0

    def test_spread_percentage_small_difference(self):
        """Test spread percentage for small difference"""
        spread = calculate_spread_percentage(0.50, 0.55)
        # |0.50 - 0.55| / 0.55 = 0.05 / 0.55 ≈ 0.0909
        assert abs(spread - 0.0909) < 0.001

    def test_spread_percentage_large_difference(self):
        """Test spread percentage for large difference"""
        spread = calculate_spread_percentage(0.30, 0.70)
        # |0.30 - 0.70| / 0.70 = 0.40 / 0.70 ≈ 0.5714
        assert abs(spread - 0.5714) < 0.001

    def test_spread_percentage_symmetric(self):
        """Test that spread percentage is symmetric"""
        spread1 = calculate_spread_percentage(0.40, 0.60)
        spread2 = calculate_spread_percentage(0.60, 0.40)
        assert spread1 == spread2

    def test_spread_percentage_zero_prices(self):
        """Test spread percentage with zero prices"""
        spread = calculate_spread_percentage(0.0, 0.0)
        assert spread == 0.0

    def test_spread_percentage_one_zero_price(self):
        """Test spread percentage with one zero price"""
        spread = calculate_spread_percentage(0.0, 0.50)
        # |0.0 - 0.50| / 0.50 = 1.0
        assert spread == 1.0

    def test_spread_percentage_near_one(self):
        """Test spread percentage for prices near 1"""
        spread = calculate_spread_percentage(0.95, 0.99)
        # |0.95 - 0.99| / 0.99 = 0.04 / 0.99 ≈ 0.0404
        assert abs(spread - 0.0404) < 0.001
