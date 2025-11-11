"""
Matcher service - finds markets on both exchanges about the same event.
Refactored to follow SOLID principles and use composition.
"""

from typing import List, Tuple

from ...config import constants
from ...models import Market
from ...utils import get_logger
from .similarity import JaccardSimilarity, SimilarityStrategy

logger = get_logger(__name__)


class Matcher:
    """
    Find equivalent markets across exchanges using configurable similarity strategies.
    """

    def __init__(
        self,
        similarity_strategy: SimilarityStrategy = None,
        similarity_threshold: float = constants.TITLE_SIMILARITY_THRESHOLD,
    ):
        """
        Initialize matcher with similarity strategy.
        Dependency Injection: strategy is configurable and testable.

        Args:
            similarity_strategy: Strategy for calculating similarity (default: JaccardSimilarity)
            similarity_threshold: Minimum similarity score (0-1) to consider markets equivalent
        """
        self.similarity_strategy = similarity_strategy or JaccardSimilarity()
        self.similarity_threshold = similarity_threshold
        logger.info(
            f"Matcher initialized with {self.similarity_strategy.__class__.__name__} "
            f"and threshold {similarity_threshold}"
        )

    def find_matches(
        self, kalshi_markets: List[Market], polymarket_markets: List[Market]
    ) -> List[Tuple[Market, Market, float]]:
        """
        Find matching markets between Kalshi and Polymarket.

        Args:
            kalshi_markets: List of markets from Kalshi
            polymarket_markets: List of markets from Polymarket

        Returns:
            List of tuples: (kalshi_market, polymarket_market, confidence_score)
        """
        matches = []

        logger.info(
            f"Matching {len(kalshi_markets)} Kalshi markets with "
            f"{len(polymarket_markets)} Polymarket markets"
        )

        for kalshi_market in kalshi_markets:
            for poly_market in polymarket_markets:
                # Delegate similarity calculation to strategy
                similarity = self.similarity_strategy.calculate(
                    kalshi_market, poly_market
                )

                if similarity >= self.similarity_threshold:
                    matches.append((kalshi_market, poly_market, similarity))
                    logger.debug(
                        f"Match found (similarity={similarity:.2f}): "
                        f"'{kalshi_market.title}' <-> '{poly_market.title}'"
                    )

        logger.info(f"Found {len(matches)} market matches")
        return matches
