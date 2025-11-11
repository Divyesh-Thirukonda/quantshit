"""
Scorer service - calculates profitability of matched market pairs.
Refactored to follow SOLID and DRY principles using composition.
"""

from typing import List, Tuple
from ...models import Market, Opportunity
from ...fin_types import Outcome
from ...config import constants
from ...utils import get_logger
from .opportunity_builder import OpportunityBuilder, OpportunityValidator
from .pricing import FeeCalculator, SlippageCalculator, PositionSizer

logger = get_logger(__name__)


class Scorer:
    """
    Calculate profitability of arbitrage opportunities.
    
    SOLID Principles Applied:
    - Single Responsibility: Only coordinates scoring, delegates to specialized classes
    - Open/Closed: Can extend with new builders/validators without modification
    - Dependency Inversion: Depends on abstractions (builder, validator)
    
    DRY Principle Applied:
    - Eliminates duplicated price extraction and fee calculation logic
    - Reuses OpportunityBuilder for construction
    """

    def __init__(
        self,
        opportunity_builder: OpportunityBuilder = None,
        opportunity_validator: OpportunityValidator = None,
        min_profit_threshold: float = constants.MIN_PROFIT_THRESHOLD
    ):
        """
        Initialize scorer with builder and validator.
        Dependency Injection: components are configurable and testable.

        Args:
            opportunity_builder: Builder for constructing opportunities
            opportunity_validator: Validator for filtering opportunities
            min_profit_threshold: Minimum profit percentage to consider
        """
        self.opportunity_builder = opportunity_builder or OpportunityBuilder()
        self.opportunity_validator = opportunity_validator or OpportunityValidator(
            min_profit_threshold=min_profit_threshold
        )
        self.min_profit_threshold = min_profit_threshold

        logger.info(f"Scorer initialized with min_profit: {min_profit_threshold:.2%}")

    def score_opportunities(
        self,
        matched_pairs: List[Tuple[Market, Market, float]]
    ) -> List[Opportunity]:
        """
        Score all matched pairs and return profitable opportunities.

        Args:
            matched_pairs: List of (kalshi_market, polymarket_market, confidence)

        Returns:
            List of Opportunity objects, sorted by expected profit (highest first)
        """
        opportunities = []

        logger.info(f"Scoring {len(matched_pairs)} matched pairs")

        for kalshi_market, poly_market, confidence in matched_pairs:
            # Check both YES and NO outcomes for arbitrage
            for outcome in [Outcome.YES, Outcome.NO]:
                opportunity = self.opportunity_builder.build(
                    market_kalshi=kalshi_market,
                    market_polymarket=poly_market,
                    outcome=outcome,
                    confidence_score=confidence
                )
                
                # Only include if it passes validation
                if self.opportunity_validator.is_valid(opportunity):
                    opportunities.append(opportunity)

        # Sort by expected profit (descending)
        opportunities.sort(key=lambda opp: opp.expected_profit, reverse=True)

        logger.info(f"Found {len(opportunities)} profitable opportunities")
        return opportunities
