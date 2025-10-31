"""
Matcher service - finds markets on both exchanges about the same event.
Core arbitrage logic - needs to be separate for testing and tuning.
"""

import re
from typing import List, Tuple
from ...models import Market
from ...config import constants
from ...utils import get_logger

logger = get_logger(__name__)


class Matcher:
    """
    Find equivalent markets across exchanges using fuzzy matching.
    """

    def __init__(self, similarity_threshold: float = constants.TITLE_SIMILARITY_THRESHOLD):
        """
        Initialize matcher.

        Args:
            similarity_threshold: Minimum similarity score (0-1) to consider markets equivalent
        """
        self.similarity_threshold = similarity_threshold
        logger.info(f"Matcher initialized with similarity threshold: {similarity_threshold}")

    def find_matches(
        self,
        kalshi_markets: List[Market],
        polymarket_markets: List[Market]
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

        logger.info(f"Matching {len(kalshi_markets)} Kalshi markets with {len(polymarket_markets)} Polymarket markets")

        for kalshi_market in kalshi_markets:
            for poly_market in polymarket_markets:
                # Calculate similarity score
                similarity = self._calculate_similarity(kalshi_market, poly_market)

                if similarity >= self.similarity_threshold:
                    matches.append((kalshi_market, poly_market, similarity))
                    logger.debug(
                        f"Match found (similarity={similarity:.2f}): "
                        f"'{kalshi_market.title}' <-> '{poly_market.title}'"
                    )

        logger.info(f"Found {len(matches)} market matches")
        return matches

    def _calculate_similarity(self, market1: Market, market2: Market) -> float:
        """
        Calculate similarity score between two markets.
        Uses word-based Jaccard similarity on normalized titles.

        Args:
            market1: First market
            market2: Second market

        Returns:
            Similarity score between 0 and 1
        """
        # Normalize titles
        title1_normalized = self._normalize_title(market1.title)
        title2_normalized = self._normalize_title(market2.title)

        # Split into words
        words1 = set(title1_normalized.split())
        words2 = set(title2_normalized.split())

        # Remove common stop words
        stop_words = {
            'the', 'a', 'an', 'and', 'or', 'but', 'in', 'on', 'at', 'to',
            'for', 'of', 'with', 'by', 'will', 'be', 'is', 'are', 'was', 'were'
        }
        words1 = words1 - stop_words
        words2 = words2 - stop_words

        # Handle empty word sets
        if not words1 or not words2:
            return 0.0

        # Jaccard similarity: intersection / union
        intersection = len(words1.intersection(words2))
        union = len(words1.union(words2))

        similarity = intersection / union if union > 0 else 0.0

        # Bonus for matching key terms (can be extended)
        key_terms_bonus = self._check_key_terms_match(words1, words2)
        similarity = min(1.0, similarity + key_terms_bonus)

        return similarity

    def _normalize_title(self, title: str) -> str:
        """
        Normalize market title for comparison.
        Remove special characters, convert to lowercase.

        Args:
            title: Raw market title

        Returns:
            Normalized title
        """
        # Convert to lowercase
        normalized = title.lower()

        # Remove special characters but keep spaces
        normalized = re.sub(r'[^a-z0-9\s]', '', normalized)

        # Normalize whitespace
        normalized = ' '.join(normalized.split())

        return normalized

    def _check_key_terms_match(self, words1: set, words2: set) -> float:
        """
        Check if markets share important key terms.
        Can boost similarity for matches on names, dates, specific events.

        Args:
            words1: Word set from first market
            words2: Word set from second market

        Returns:
            Bonus score (0-0.2)
        """
        # Define important terms that indicate strong match
        # This is a simple version - can be extended with NLP
        key_terms = {
            # Political names
            'trump', 'biden', 'harris', 'desantis',
            # Sports teams
            'chiefs', 'eagles', '49ers', 'ravens',
            # Companies
            'tesla', 'apple', 'google', 'microsoft',
            # Events
            'election', 'championship', 'olympics'
        }

        # Check if both markets mention the same key terms
        key_matches = 0
        for term in key_terms:
            if term in words1 and term in words2:
                key_matches += 1

        # Small bonus per key term match (max 0.2)
        return min(0.2, key_matches * 0.1)
