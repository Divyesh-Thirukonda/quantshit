"""
Validator service - safety checks before executing trades.
Never execute without validation - prevents losing money on invalid trades.
"""

from dataclasses import dataclass
from typing import Optional
from ...models import Opportunity
from ...config import constants, settings
from ...utils import get_logger

logger = get_logger(__name__)


@dataclass
class ValidationResult:
    """Result of validating a trading opportunity"""
    valid: bool
    reason: Optional[str] = None


class Validator:
    """
    Performs safety checks before trade execution.
    """

    def __init__(self, available_capital: float = constants.INITIAL_CAPITAL_PER_EXCHANGE * 2):
        """
        Initialize validator.

        Args:
            available_capital: Total available capital for trading
        """
        self.available_capital = available_capital
        logger.info(f"Validator initialized with ${available_capital:,.2f} available capital")

    def validate(self, opportunity: Opportunity) -> ValidationResult:
        """
        Run all validation checks on an opportunity.

        Args:
            opportunity: Opportunity to validate

        Returns:
            ValidationResult indicating if trade is safe to execute
        """
        logger.debug(f"Validating opportunity: {opportunity.outcome.value} on {opportunity.market_kalshi.title}")

        # Check 1: Is opportunity still profitable?
        if not opportunity.is_profitable:
            return ValidationResult(
                valid=False,
                reason=f"Opportunity no longer profitable (profit: ${opportunity.expected_profit:.2f})"
            )

        # Check 2: Is profit above minimum threshold?
        if opportunity.expected_profit_pct < constants.MIN_PROFIT_THRESHOLD:
            return ValidationResult(
                valid=False,
                reason=f"Profit {opportunity.expected_profit_pct:.2%} below threshold {constants.MIN_PROFIT_THRESHOLD:.2%}"
            )

        # Check 3: Do markets still exist and are open?
        if not opportunity.market_kalshi.is_open or not opportunity.market_polymarket.is_open:
            return ValidationResult(
                valid=False,
                reason="One or both markets are closed"
            )

        # Check 4: Is opportunity expired?
        if opportunity.is_expired:
            return ValidationResult(
                valid=False,
                reason="Opportunity has expired"
            )

        # Check 5: Confidence score high enough?
        if opportunity.confidence_score < constants.MIN_CONFIDENCE_SCORE:
            return ValidationResult(
                valid=False,
                reason=f"Confidence {opportunity.confidence_score:.2f} below threshold {constants.MIN_CONFIDENCE_SCORE:.2f}"
            )

        # Check 6: Sufficient capital for the trade?
        # Calculate capital required (buy side cost)
        capital_required = opportunity.recommended_size * (
            opportunity.buy_price if opportunity.buy_price else 0.5
        )

        if capital_required > self.available_capital:
            return ValidationResult(
                valid=False,
                reason=f"Insufficient capital (need ${capital_required:.2f}, have ${self.available_capital:.2f})"
            )

        # Check 7: Position size within limits?
        if opportunity.recommended_size > constants.MAX_POSITION_SIZE:
            return ValidationResult(
                valid=False,
                reason=f"Position size {opportunity.recommended_size} exceeds maximum {constants.MAX_POSITION_SIZE}"
            )

        if opportunity.recommended_size < constants.MIN_POSITION_SIZE:
            return ValidationResult(
                valid=False,
                reason=f"Position size {opportunity.recommended_size} below minimum {constants.MIN_POSITION_SIZE}"
            )

        # All checks passed
        logger.info(
            f"✓ Validation passed for {opportunity.outcome.value}: "
            f"{opportunity.market_kalshi.title[:50]}... "
            f"(profit: ${opportunity.expected_profit:.2f}, {opportunity.expected_profit_pct:.2%})"
        )

        return ValidationResult(valid=True, reason="All validation checks passed")

    def update_available_capital(self, capital: float):
        """Update available capital (after trades executed)"""
        self.available_capital = capital
        logger.debug(f"Available capital updated to ${capital:,.2f}")
