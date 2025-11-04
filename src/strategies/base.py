"""
Base strategy interface - all trading strategies must implement this.
Open/Closed Principle - add new strategies by extending, not modifying.
"""

from abc import ABC, abstractmethod
from typing import List
from ..models import Opportunity, Position
from ..utils import get_logger
from .config import StrategyConfig

logger = get_logger(__name__)


class BaseStrategy(ABC):
    """
    Abstract base class for all trading strategies.
    Defines the interface that all strategies must implement.
    """

    def __init__(self, config: StrategyConfig):
        """
        Initialize strategy with configuration.

        Args:
            config: Strategy configuration with trading parameters
        """
        self.config = config
        self.name = config.name
        logger.info(f"Strategy initialized: {self.name}")

    @abstractmethod
    def filter_opportunities(self, opportunities: List[Opportunity]) -> List[Opportunity]:
        """
        Filter opportunities based on strategy-specific criteria.

        Args:
            opportunities: List of all available opportunities

        Returns:
            Filtered list of opportunities that meet strategy criteria
        """
        pass

    @abstractmethod
    def rank_opportunities(self, opportunities: List[Opportunity]) -> List[Opportunity]:
        """
        Rank opportunities by desirability.

        Args:
            opportunities: List of filtered opportunities

        Returns:
            Opportunities sorted by preference (best first)
        """
        pass

    @abstractmethod
    def should_close_position(self, position: Position) -> bool:
        """
        Determine if a position should be closed.

        Args:
            position: Open position to evaluate

        Returns:
            True if position should be closed
        """
        pass

    def select_best_opportunity(self, opportunities: List[Opportunity]) -> Opportunity:
        """
        Main strategy method - select the best opportunity to execute.

        Args:
            opportunities: List of all available opportunities

        Returns:
            Best opportunity to execute (or None if none suitable)
        """
        # Apply strategy-specific filtering
        filtered = self.filter_opportunities(opportunities)

        if not filtered:
            logger.info(f"{self.name}: No opportunities passed filters")
            return None

        # Rank by strategy criteria
        ranked = self.rank_opportunities(filtered)

        # Return best opportunity
        best = ranked[0] if ranked else None

        if best:
            logger.info(
                f"{self.name}: Selected opportunity with "
                f"${best.expected_profit:.2f} profit ({best.expected_profit_pct:.2%})"
            )

        return best
