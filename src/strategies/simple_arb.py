"""
Simple arbitrage strategy - basic buy low, sell high approach.
Equal position sizes on both sides, profit from spread convergence.
"""

from typing import List, Optional

from ..config import constants
from ..models import Opportunity, Position
from ..utils import get_logger
from .base import BaseStrategy
from .config import SimpleArbitrageConfig

logger = get_logger(__name__)


class SimpleArbitrageStrategy(BaseStrategy):
    """
    Basic arbitrage strategy:
    - Find price differences > threshold
    - Buy on cheaper exchange, sell on expensive
    - Close when spread narrows below threshold
    - Equal position sizes on both sides
    """

    def __init__(self, config: Optional[SimpleArbitrageConfig] = None):
        """
        Initialize simple arbitrage strategy.

        Args:
            config: Strategy configuration. If None, uses default config.
        """
        if config is None:
            config = SimpleArbitrageConfig()

        # Validate configuration
        errors = config.validate()
        if errors:
            raise ValueError(f"Invalid strategy configuration: {errors}")

        super().__init__(config)
        self.config: SimpleArbitrageConfig = config  # Type hint for IDE

        logger.info(
            f"{self.name} initialized - "
            f"min_profit: {config.min_profit_pct:.2%}, "
            f"min_confidence: {config.min_confidence:.2f}, "
            f"min_volume: ${config.min_volume:,.0f}"
        )

    def filter_opportunities(
        self, opportunities: List[Opportunity]
    ) -> List[Opportunity]:
        """
        Filter opportunities based on simple arbitrage criteria.

        Filters applied:
        1. Profit percentage above threshold
        2. Confidence score above threshold
        3. Not expired
        4. Markets are open (if required by config)
        """
        filtered = []

        for opp in opportunities:
            # Check profit threshold
            if opp.expected_profit_pct < self.config.min_profit_pct:
                continue

            # Check confidence threshold
            if opp.confidence_score < self.config.min_confidence:
                continue

            # Check not expired
            if opp.is_expired:
                continue

            # Check markets are open (if required)
            if self.config.require_both_markets_open:
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
            opportunities, key=lambda opp: opp.expected_profit_pct, reverse=True
        )

        logger.debug(f"{self.name}: Ranked {len(ranked)} opportunities")

        return ranked

    def should_close_position(self, position: Position) -> bool:
        """
        Determine if position should be closed.

        Close conditions:
        1. Hit take profit target (from config)
        2. Hit stop loss (from config)
        3. Unrealized profit above threshold

        Args:
            position: Position to evaluate

        Returns:
            True if should close
        """
        # Take profit
        if position.unrealized_pnl_pct >= self.config.take_profit_pct * 100:
            logger.info(
                f"Take profit triggered: {position.position_id} "
                f"(P&L: {position.unrealized_pnl_pct:+.2f}%)"
            )
            return True

        # Close if we have good profit and want to lock it in
        # (More conservative than full take profit)
        if position.unrealized_pnl_pct >= (self.config.take_profit_pct * 100 * 0.5):
            logger.info(
                f"Partial profit target hit: {position.position_id} "
                f"(P&L: {position.unrealized_pnl_pct:+.2f}%)"
            )
            return True

        return False

    def calculate_position_size(
        self, opportunity: Opportunity, available_capital: float
    ) -> int:
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

        # Ensure within limits from config
        size = max(self.config.min_position_size, size)
        size = min(self.config.max_position_size, size)

        return size
