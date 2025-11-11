"""
Matching service - finds equivalent markets across exchanges and scores arbitrage opportunities.
Refactored to follow SOLID and DRY principles with modular components.
"""

from .matcher import Matcher
from .scorer import Scorer
from .similarity import (
    SimilarityStrategy,
    JaccardSimilarity,
    WeightedJaccardSimilarity,
    CompositeSimilarity,
    ExactMatchSimilarity,
    CategoryAwareSimilarity
)
from .text_processing import (
    TextNormalizer,
    WordTokenizer,
    StopWordsFilter,
    KeyTermsMatcher,
    TextProcessor
)
from .pricing import (
    PriceInfo,
    PriceExtractor,
    FeeCalculator,
    SlippageCalculator,
    PositionSizer
)
from .opportunity_builder import (
    OpportunityBuilder,
    OpportunityValidator
)

__all__ = [
    # Main service classes
    'Matcher',
    'Scorer',
    # Similarity strategies
    'SimilarityStrategy',
    'JaccardSimilarity',
    'WeightedJaccardSimilarity',
    'CompositeSimilarity',
    'ExactMatchSimilarity',
    'CategoryAwareSimilarity',
    # Text processing
    'TextNormalizer',
    'WordTokenizer',
    'StopWordsFilter',
    'KeyTermsMatcher',
    'TextProcessor',
    # Pricing utilities
    'PriceInfo',
    'PriceExtractor',
    'FeeCalculator',
    'SlippageCalculator',
    'PositionSizer',
    # Opportunity construction
    'OpportunityBuilder',
    'OpportunityValidator',
]
