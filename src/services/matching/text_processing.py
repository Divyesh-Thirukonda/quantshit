"""
Text processing utilities for market matching.
Single Responsibility: Each class handles one aspect of text processing.
"""

import re
from typing import Set
from abc import ABC, abstractmethod


class TextNormalizer:
    """
    Normalizes text for comparison.
    Single responsibility: text normalization only.
    """
    
    def normalize(self, text: str) -> str:
        """
        Normalize text to lowercase and remove special characters.
        
        Args:
            text: Raw text
            
        Returns:
            Normalized text
        """
        # Convert to lowercase
        normalized = text.lower()
        
        # Remove special characters but keep spaces and numbers
        normalized = re.sub(r'[^a-z0-9\s]', '', normalized)
        
        # Normalize whitespace
        normalized = ' '.join(normalized.split())
        
        return normalized


class WordTokenizer:
    """
    Tokenizes text into words.
    Single responsibility: tokenization only.
    """
    
    def tokenize(self, text: str) -> Set[str]:
        """
        Split text into word tokens.
        
        Args:
            text: Text to tokenize
            
        Returns:
            Set of word tokens
        """
        return set(text.split())


class StopWordsFilter:
    """
    Filters out common stop words.
    Open/Closed: Can configure stop words without modifying code.
    """
    
    DEFAULT_STOP_WORDS = {
        'the', 'a', 'an', 'and', 'or', 'but', 'in', 'on', 'at', 'to',
        'for', 'of', 'with', 'by', 'will', 'be', 'is', 'are', 'was', 
        'were', 'been', 'being', 'have', 'has', 'had', 'do', 'does',
        'did', 'can', 'could', 'should', 'would', 'may', 'might', 'must',
        'shall', 'this', 'that', 'these', 'those', 'from', 'as', 'it'
    }
    
    def __init__(self, stop_words: Set[str] = None):
        """
        Initialize with custom or default stop words.
        
        Args:
            stop_words: Custom stop words set, or None for defaults
        """
        self.stop_words = stop_words if stop_words is not None else self.DEFAULT_STOP_WORDS
    
    def filter(self, words: Set[str]) -> Set[str]:
        """
        Remove stop words from word set.
        
        Args:
            words: Set of words
            
        Returns:
            Filtered set without stop words
        """
        return words - self.stop_words


class KeyTermsMatcher:
    """
    Matches important key terms between word sets.
    Open/Closed: Can configure key terms without modifying code.
    """
    
    DEFAULT_KEY_TERMS = {
        # Political figures
        'trump', 'biden', 'harris', 'desantis', 'pence', 'obama',
        # Sports teams (NFL)
        'chiefs', 'eagles', '49ers', 'ravens', 'cowboys', 'packers',
        # Sports teams (NBA)
        'warriors', 'lakers', 'celtics', 'heat', 'bulls', 'nets',
        # Companies
        'tesla', 'apple', 'google', 'microsoft', 'amazon', 'meta',
        # Event types
        'election', 'championship', 'olympics', 'superbowl', 'worldcup',
        # Outcomes
        'win', 'lose', 'champion', 'winner', 'defeat'
    }
    
    def __init__(self, key_terms: Set[str] = None, bonus_per_match: float = 0.1, max_bonus: float = 0.2):
        """
        Initialize with custom or default key terms.
        
        Args:
            key_terms: Custom key terms set, or None for defaults
            bonus_per_match: Bonus score per key term match
            max_bonus: Maximum total bonus
        """
        self.key_terms = key_terms if key_terms is not None else self.DEFAULT_KEY_TERMS
        self.bonus_per_match = bonus_per_match
        self.max_bonus = max_bonus
    
    def calculate_bonus(self, words1: Set[str], words2: Set[str]) -> float:
        """
        Calculate bonus score for matching key terms.
        
        Args:
            words1: First word set
            words2: Second word set
            
        Returns:
            Bonus score (0 to max_bonus)
        """
        # Count how many key terms appear in both sets
        key_matches = sum(1 for term in self.key_terms if term in words1 and term in words2)
        
        # Return bonus, capped at maximum
        return min(self.max_bonus, key_matches * self.bonus_per_match)


class TextProcessor:
    """
    Facade that combines all text processing steps.
    Composition over inheritance - delegates to specialized classes.
    """
    
    def __init__(
        self,
        normalizer: TextNormalizer = None,
        tokenizer: WordTokenizer = None,
        stop_words_filter: StopWordsFilter = None
    ):
        """
        Initialize with processing components.
        Dependency Injection: accepts abstractions, easy to test and extend.
        
        Args:
            normalizer: Text normalizer (default: TextNormalizer)
            tokenizer: Word tokenizer (default: WordTokenizer)
            stop_words_filter: Stop words filter (default: StopWordsFilter)
        """
        self.normalizer = normalizer or TextNormalizer()
        self.tokenizer = tokenizer or WordTokenizer()
        self.stop_words_filter = stop_words_filter or StopWordsFilter()
    
    def process(self, text: str) -> Set[str]:
        """
        Process text through full pipeline: normalize -> tokenize -> filter.
        
        Args:
            text: Raw text
            
        Returns:
            Processed word set
        """
        normalized = self.normalizer.normalize(text)
        words = self.tokenizer.tokenize(normalized)
        filtered = self.stop_words_filter.filter(words)
        return filtered



