"""
Simple arbitrage strategy - basic buy low, sell high approach.
Equal position sizes on both sides, profit from spread convergence.
"""

from typing import List
from .base import BaseStrategy
from ..models import Opportunity, Position
from ..config import constants
from ..utils import get_logger

logger = get_logger(__name__)


class SimpleArbitrageStrategy(BaseStrategy):
    """
    Basic arbitrage strategy:
    - Find price differences > threshold
    - Buy on cheaper exchange, sell on expensive
    - Close when spread narrows below threshold
    - Equal position sizes on both sides
    """

    def __init__(
        self,
        min_profit_pct: float = constants.MIN_PROFIT_THRESHOLD,
        min_confidence: float = constants.MIN_CONFIDENCE_SCORE
    ):
        """
        Initialize simple arbitrage strategy.

        Args:
            min_profit_pct: Minimum profit percentage to consider
            min_confidence: Minimum confidence score for market match
        """
        super().__init__("Simple Arbitrage")
        self.min_profit_pct = min_profit_pct
        self.min_confidence = min_confidence

        logger.info(
            f"{self.name} initialized - "
            f"min_profit: {min_profit_pct:.2%}, "
            f"min_confidence: {min_confidence:.2f}"
        )

    def filter_opportunities(self, opportunities: List[Opportunity]) -> List[Opportunity]:
        """
        Filter opportunities based on simple arbitrage criteria.

        Filters applied:
        1. Profit percentage above threshold
        2. Confidence score above threshold
        3. Not expired
        4. Markets are open
        """
        filtered = []

        for opp in opportunities:
            # Check profit threshold
            if opp.expected_profit_pct < self.min_profit_pct:
                continue

            # Check confidence threshold
            if opp.confidence_score < self.min_confidence:
                continue

            # Check not expired
            if opp.is_expired:
                continue

            # Check markets are open
            if not opp.market_kalshi.is_open or not opp.market_polymarket.is_open:
                continue

            filtered.append(opp)

        logger.debug(
            f"{self.name}: Filtered {len(opportunities)} -> {len(filtered)} opportunities"
        )

        return filtered

    def rank_opportunities(self, opportunities: List[Opportunity]) -> List[Opportunity]:
        """
        Rank opportunities by expected profit percentage (highest first).
        Simple strategy prioritizes pure profit.
        """
        ranked = sorted(
            opportunities,
            key=lambda opp: opp.expected_profit_pct,
            reverse=True
        )

        logger.debug(f"{self.name}: Ranked {len(ranked)} opportunities")

        return ranked

    def should_close_position(self, position: Position) -> bool:
        """
        Determine if position should be closed.

        Close conditions:
        1. Hit take profit target (10% gain)
        2. Hit stop loss (-5% loss)
        3. Unrealized profit above threshold

        Args:
            position: Position to evaluate

        Returns:
            True if should close
        """
        # Take profit
        if position.unrealized_pnl_pct >= constants.DEFAULT_TAKE_PROFIT_PCT * 100:
            logger.info(
                f"Take profit triggered: {position.position_id} "
                f"(P&L: {position.unrealized_pnl_pct:+.2f}%)"
            )
            return True

        # Stop loss
        if position.unrealized_pnl_pct <= constants.DEFAULT_STOP_LOSS_PCT * 100:
            logger.warning(
                f"Stop loss triggered: {position.position_id} "
                f"(P&L: {position.unrealized_pnl_pct:+.2f}%)"
            )
            return True

        # Close if we have good profit and want to lock it in
        # (More conservative than full take profit)
        if position.unrealized_pnl_pct >= (constants.DEFAULT_TAKE_PROFIT_PCT * 100 * 0.5):
            logger.info(
                f"Partial profit target hit: {position.position_id} "
                f"(P&L: {position.unrealized_pnl_pct:+.2f}%)"
            )
            return True

        return False

    def calculate_position_size(self, opportunity: Opportunity, available_capital: float) -> int:
        """
        Calculate appropriate position size for opportunity.

        For simple arbitrage, use the recommended size from the opportunity,
        capped by available capital.

        Args:
            opportunity: Opportunity to size
            available_capital: Available trading capital

        Returns:
            Number of contracts to trade
        """
        # Use recommended size from opportunity (already considers liquidity)
        size = opportunity.recommended_size

        # Calculate capital required
        capital_required = size * (opportunity.buy_price or 0.5)

        # If not enough capital, reduce size
        if capital_required > available_capital:
            size = int(available_capital / (opportunity.buy_price or 0.5))
            logger.debug(
                f"Reduced position size from {opportunity.recommended_size} to {size} "
                f"due to capital constraints"
            )

        # Ensure within limits
        size = max(constants.MIN_POSITION_SIZE, size)
        size = min(constants.MAX_POSITION_SIZE, size)

        return size
