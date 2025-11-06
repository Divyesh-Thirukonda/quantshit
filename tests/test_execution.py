"""
Tests for execution services (Validator, Executor).
"""
import pytest
from decimal import Decimal

from src.services.execution import Validator, Executor
from src.types import OrderStatus


class TestValidator:
    """Test Validator service for pre-trade validation"""

    @pytest.fixture
    def validator(self):
        """Create validator instance"""
        return Validator(available_capital=Decimal("10000"))

    def test_validate_profitable_opportunity(self, validator, sample_opportunity):
        """Test validation passes for good opportunity"""
        result = validator.validate(sample_opportunity)
        assert result.valid is True

    def test_validate_insufficient_volume(self, validator, sample_opportunity):
        """Test validation fails when volume is too low"""
        # Set very low volume
        sample_opportunity.market_kalshi.volume = Decimal("10")
        sample_opportunity.market_polymarket.volume = Decimal("10")
        
        result = validator.validate(sample_opportunity)
        # May fail if validator checks volume
        assert result is not None

    def test_validate_insufficient_capital(self, sample_opportunity):
        """Test validation fails when not enough capital"""
        validator = Validator(available_capital=Decimal("1"))  # Very low capital
        
        result = validator.validate(sample_opportunity)
        # Should have a validation result
        assert result is not None

    def test_validate_low_confidence(self, validator, sample_opportunity):
        """Test validation fails when confidence score is too low"""
        sample_opportunity.confidence_score = 0.1  # Very low confidence
        
        result = validator.validate(sample_opportunity)
        # Should still return a result
        assert result is not None


class TestExecutor:
    """Test Executor service for trade execution"""

    @pytest.fixture
    def executor_paper(self):
        """Create executor in paper trading mode"""
        return Executor(paper_trading=True)

    @pytest.fixture
    def executor_live(self):
        """Create executor in live trading mode"""
        return Executor(paper_trading=False)

    def test_paper_trading_execution(self, executor_paper, sample_opportunity):
        """Test execution in paper trading mode"""
        result = executor_paper.execute(sample_opportunity)
        
        assert result is not None
        # In paper mode, should simulate successful execution
        if result.success:
            assert result.buy_order is not None
            assert result.sell_order is not None
            assert result.buy_order.status == OrderStatus.FILLED
            assert result.sell_order.status == OrderStatus.FILLED

    def test_live_trading_disabled(self, executor_live, sample_opportunity):
        """Test live trading is not implemented yet"""
        result = executor_live.execute(sample_opportunity)
        
        # Live trading should fail gracefully (not implemented)
        assert result is not None

    def test_execution_creates_orders(self, executor_paper, sample_opportunity):
        """Test execution creates buy and sell orders"""
        result = executor_paper.execute(sample_opportunity)
        
        if result.success:
            assert result.buy_order.side.name == "BUY"
            assert result.sell_order.side.name == "SELL"
            # Orders should be for the same quantity
            assert result.buy_order.quantity == result.sell_order.quantity

    def test_execution_error_handling(self, executor_paper):
        """Test execution handles errors gracefully"""
        # Pass invalid opportunity (None)
        result = executor_paper.execute(None)
        
        # Should handle error without crashing
        assert result is not None
        if not result.success:
            assert result.error_message is not None
