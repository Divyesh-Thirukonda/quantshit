"""
Similarity calculation strategies for market matching.
Strategy Pattern: Different algorithms implement common interface.
Open/Closed Principle: Add new strategies without modifying existing code.
"""

from abc import ABC, abstractmethod
from typing import Set, List
from ...models import Market
from .text_processing import TextProcessor, KeyTermsMatcher


class SimilarityStrategy(ABC):
    """
    Abstract base class for similarity calculation strategies.
    Dependency Inversion: Depend on abstraction, not concrete implementation.
    """
    
    @abstractmethod
    def calculate(self, market1: Market, market2: Market) -> float:
        """
        Calculate similarity score between two markets.
        
        Args:
            market1: First market
            market2: Second market
            
        Returns:
            Similarity score between 0 and 1
        """
        pass


class JaccardSimilarity(SimilarityStrategy):
    """
    Jaccard similarity: intersection over union of word sets.
    Single Responsibility: Only calculates Jaccard similarity.
    """
    
    def __init__(
        self,
        text_processor: TextProcessor = None,
        key_terms_matcher: KeyTermsMatcher = None
    ):
        """
        Initialize with text processing components.
        Dependency Injection: easy to test and configure.
        
        Args:
            text_processor: Text processor for normalization and filtering
            key_terms_matcher: Matcher for key terms bonus
        """
        self.text_processor = text_processor or TextProcessor()
        self.key_terms_matcher = key_terms_matcher or KeyTermsMatcher()
    
    def calculate(self, market1: Market, market2: Market) -> float:
        """
        Calculate Jaccard similarity with key terms bonus.
        
        Args:
            market1: First market
            market2: Second market
            
        Returns:
            Similarity score between 0 and 1
        """
        # Process titles
        words1 = self.text_processor.process(market1.title)
        words2 = self.text_processor.process(market2.title)
        
        # Handle empty word sets
        if not words1 or not words2:
            return 0.0
        
        # Calculate Jaccard similarity: |intersection| / |union|
        intersection = len(words1.intersection(words2))
        union = len(words1.union(words2))
        
        similarity = intersection / union if union > 0 else 0.0
        
        # Add key terms bonus
        bonus = self.key_terms_matcher.calculate_bonus(words1, words2)
        similarity = min(1.0, similarity + bonus)
        
        return similarity


class WeightedJaccardSimilarity(SimilarityStrategy):
    """
    Jaccard similarity with weights for different word types.
    Extension example: more sophisticated matching without changing interface.
    """
    
    def __init__(
        self,
        text_processor: TextProcessor = None,
        important_words_weight: float = 2.0
    ):
        """
        Initialize with text processor and weights.
        
        Args:
            text_processor: Text processor
            important_words_weight: Weight multiplier for important words
        """
        self.text_processor = text_processor or TextProcessor()
        self.important_words_weight = important_words_weight
    
    def calculate(self, market1: Market, market2: Market) -> float:
        """
        Calculate weighted Jaccard similarity.
        
        Args:
            market1: First market
            market2: Second market
            
        Returns:
            Similarity score between 0 and 1
        """
        words1 = self.text_processor.process(market1.title)
        words2 = self.text_processor.process(market2.title)
        
        if not words1 or not words2:
            return 0.0
        
        # Simple implementation: all words have weight 1.0 for now
        # Can be extended to use NLP for important word detection
        weighted_intersection = len(words1.intersection(words2))
        weighted_union = len(words1.union(words2))
        
        similarity = weighted_intersection / weighted_union if weighted_union > 0 else 0.0
        return min(1.0, similarity)


class CompositeSimilarity(SimilarityStrategy):
    """
    Combines multiple similarity strategies with weights.
    Composite Pattern: treat single strategies and combinations uniformly.
    """
    
    def __init__(self, strategies: List[tuple[SimilarityStrategy, float]]):
        """
        Initialize with list of strategies and their weights.
        
        Args:
            strategies: List of (strategy, weight) tuples
                       Weights should sum to 1.0
        """
        if not strategies:
            raise ValueError("At least one strategy required")
        
        total_weight = sum(weight for _, weight in strategies)
        if abs(total_weight - 1.0) > 0.01:
            raise ValueError(f"Weights must sum to 1.0, got {total_weight}")
        
        self.strategies = strategies
    
    def calculate(self, market1: Market, market2: Market) -> float:
        """
        Calculate weighted combination of multiple strategies.
        
        Args:
            market1: First market
            market2: Second market
            
        Returns:
            Combined similarity score between 0 and 1
        """
        total_score = 0.0
        
        for strategy, weight in self.strategies:
            score = strategy.calculate(market1, market2)
            total_score += score * weight
        
        return min(1.0, total_score)


class ExactMatchSimilarity(SimilarityStrategy):
    """
    Simple exact string match (case-insensitive).
    Useful for testing or as part of composite strategy.
    """
    
    def calculate(self, market1: Market, market2: Market) -> float:
        """
        Check if titles match exactly (case-insensitive).
        
        Args:
            market1: First market
            market2: Second market
            
        Returns:
            1.0 if exact match, 0.0 otherwise
        """
        return 1.0 if market1.title.lower() == market2.title.lower() else 0.0


class CategoryAwareSimilarity(SimilarityStrategy):
    """
    Similarity strategy that considers market categories.
    Only matches markets in the same category.
    """
    
    def __init__(
        self,
        base_strategy: SimilarityStrategy,
        require_same_category: bool = True
    ):
        """
        Initialize with base strategy and category requirements.
        Decorator Pattern: adds category checking to existing strategy.
        
        Args:
            base_strategy: Underlying similarity strategy
            require_same_category: Whether to require matching categories
        """
        self.base_strategy = base_strategy
        self.require_same_category = require_same_category
    
    def calculate(self, market1: Market, market2: Market) -> float:
        """
        Calculate similarity, considering categories.
        
        Args:
            market1: First market
            market2: Second market
            
        Returns:
            Similarity score (0.0 if categories don't match and required)
        """
        # Check category requirement
        if self.require_same_category:
            if market1.category and market2.category:
                if market1.category.lower() != market2.category.lower():
                    return 0.0
        
        # Delegate to base strategy
        return self.base_strategy.calculate(market1, market2)



