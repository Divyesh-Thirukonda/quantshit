"""
NLP and sentiment analysis utilities for prediction markets.
"""
import re
from typing import List, Dict, Any, Optional, Tuple
from textblob import TextBlob
from vaderSentiment.vaderSentiment import SentimentIntensityAnalyzer
from src.core.logger import get_logger

logger = get_logger(__name__)


class TextProcessor:
    """Text processing utilities for market analysis."""
    
    def __init__(self):
        self.vader_analyzer = SentimentIntensityAnalyzer()
        
        # Political keywords for prediction markets
        self.political_keywords = {
            'election', 'vote', 'candidate', 'poll', 'democrat', 'republican',
            'biden', 'trump', 'harris', 'desantis', 'primary', 'campaign',
            'senate', 'house', 'congress', 'electoral', 'ballot'
        }
        
        # Economic keywords
        self.economic_keywords = {
            'inflation', 'gdp', 'unemployment', 'recession', 'fed', 'interest',
            'market', 'stock', 'economy', 'trade', 'tariff', 'dollar'
        }
        
        # Sports keywords
        self.sports_keywords = {
            'championship', 'playoff', 'season', 'team', 'player', 'game',
            'score', 'win', 'lose', 'mvp', 'coach', 'draft'
        }
        
        # Weather/climate keywords
        self.weather_keywords = {
            'hurricane', 'storm', 'temperature', 'climate', 'weather',
            'rainfall', 'drought', 'flood', 'tornado', 'blizzard'
        }
    
    def clean_text(self, text: str) -> str:
        """
        Clean and normalize text.
        
        Args:
            text: Raw text
            
        Returns:
            Cleaned text
        """
        try:
            # Convert to lowercase
            text = text.lower()
            
            # Remove special characters but keep alphanumeric and spaces
            text = re.sub(r'[^a-zA-Z0-9\s]', '', text)
            
            # Remove extra whitespace
            text = ' '.join(text.split())
            
            return text
        
        except Exception as e:
            logger.error(f"Error cleaning text: {e}")
            return text
    
    def extract_keywords(self, text: str, top_n: int = 10) -> List[str]:
        """
        Extract key terms from text.
        
        Args:
            text: Input text
            top_n: Number of top keywords to return
            
        Returns:
            List of keywords
        """
        try:
            cleaned_text = self.clean_text(text)
            
            # Use TextBlob for noun phrase extraction
            blob = TextBlob(cleaned_text)
            
            # Get noun phrases and individual words
            noun_phrases = blob.noun_phrases
            words = [word for word in blob.words if len(word) > 3]
            
            # Combine and count frequency
            all_terms = list(noun_phrases) + words
            term_freq = {}
            
            for term in all_terms:
                term_freq[term] = term_freq.get(term, 0) + 1
            
            # Sort by frequency and return top N
            sorted_terms = sorted(term_freq.items(), key=lambda x: x[1], reverse=True)
            
            return [term for term, freq in sorted_terms[:top_n]]
        
        except Exception as e:
            logger.error(f"Error extracting keywords: {e}")
            return []
    
    def analyze_sentiment(self, text: str) -> Dict[str, Any]:
        """
        Analyze sentiment using multiple methods.
        
        Args:
            text: Input text
            
        Returns:
            Dictionary with sentiment scores
        """
        try:
            # TextBlob sentiment
            blob = TextBlob(text)
            textblob_polarity = blob.sentiment.polarity
            textblob_subjectivity = blob.sentiment.subjectivity
            
            # VADER sentiment
            vader_scores = self.vader_analyzer.polarity_scores(text)
            
            # Combined sentiment score
            combined_score = (textblob_polarity + vader_scores['compound']) / 2
            
            # Determine overall sentiment
            if combined_score > 0.1:
                overall_sentiment = "positive"
            elif combined_score < -0.1:
                overall_sentiment = "negative"
            else:
                overall_sentiment = "neutral"
            
            return {
                "textblob": {
                    "polarity": textblob_polarity,
                    "subjectivity": textblob_subjectivity
                },
                "vader": vader_scores,
                "combined_score": combined_score,
                "overall_sentiment": overall_sentiment,
                "confidence": abs(combined_score)
            }
        
        except Exception as e:
            logger.error(f"Error analyzing sentiment: {e}")
            return {
                "textblob": {"polarity": 0.0, "subjectivity": 0.0},
                "vader": {"compound": 0.0, "pos": 0.0, "neu": 1.0, "neg": 0.0},
                "combined_score": 0.0,
                "overall_sentiment": "neutral",
                "confidence": 0.0
            }
    
    def categorize_market(self, title: str, description: str = "") -> str:
        """
        Categorize a prediction market based on its title and description.
        
        Args:
            title: Market title
            description: Market description
            
        Returns:
            Category string
        """
        try:
            combined_text = f"{title} {description}".lower()
            
            # Count keyword matches for each category
            category_scores = {
                "politics": len([w for w in combined_text.split() if w in self.political_keywords]),
                "economics": len([w for w in combined_text.split() if w in self.economic_keywords]),
                "sports": len([w for w in combined_text.split() if w in self.sports_keywords]),
                "weather": len([w for w in combined_text.split() if w in self.weather_keywords])
            }
            
            # Return category with highest score
            if max(category_scores.values()) > 0:
                return max(category_scores, key=category_scores.get)
            else:
                return "other"
        
        except Exception as e:
            logger.error(f"Error categorizing market: {e}")
            return "other"
    
    def calculate_text_similarity(self, text1: str, text2: str) -> float:
        """
        Calculate semantic similarity between two texts.
        
        Args:
            text1: First text
            text2: Second text
            
        Returns:
            Similarity score (0-1)
        """
        try:
            # Clean texts
            clean1 = self.clean_text(text1)
            clean2 = self.clean_text(text2)
            
            # Get word sets
            words1 = set(clean1.split())
            words2 = set(clean2.split())
            
            # Calculate Jaccard similarity
            intersection = words1.intersection(words2)
            union = words1.union(words2)
            
            jaccard_similarity = len(intersection) / len(union) if union else 0.0
            
            # Enhanced similarity using noun phrases
            blob1 = TextBlob(clean1)
            blob2 = TextBlob(clean2)
            
            phrases1 = set(blob1.noun_phrases)
            phrases2 = set(blob2.noun_phrases)
            
            phrase_intersection = phrases1.intersection(phrases2)
            phrase_union = phrases1.union(phrases2)
            
            phrase_similarity = len(phrase_intersection) / len(phrase_union) if phrase_union else 0.0
            
            # Weighted combination
            combined_similarity = 0.6 * jaccard_similarity + 0.4 * phrase_similarity
            
            return combined_similarity
        
        except Exception as e:
            logger.error(f"Error calculating text similarity: {e}")
            return 0.0
    
    def detect_market_signals(self, text: str) -> Dict[str, Any]:
        """
        Detect trading signals from text content.
        
        Args:
            text: Input text (news, social media, etc.)
            
        Returns:
            Dictionary with signal information
        """
        try:
            # Analyze sentiment
            sentiment = self.analyze_sentiment(text)
            
            # Extract keywords
            keywords = self.extract_keywords(text)
            
            # Categorize content
            category = self.categorize_market("", text)
            
            # Detect urgency indicators
            urgency_words = ['breaking', 'urgent', 'alert', 'now', 'just', 'confirmed']
            urgency_score = len([w for w in text.lower().split() if w in urgency_words])
            
            # Detect certainty indicators
            certainty_words = ['will', 'definitely', 'confirmed', 'announced', 'decided']
            uncertainty_words = ['might', 'could', 'possibly', 'maybe', 'rumor']
            
            certainty_score = len([w for w in text.lower().split() if w in certainty_words])
            uncertainty_score = len([w for w in text.lower().split() if w in uncertainty_words])
            
            net_certainty = certainty_score - uncertainty_score
            
            # Generate signal strength
            signal_strength = abs(sentiment['combined_score']) * (1 + urgency_score * 0.1) * (1 + max(0, net_certainty) * 0.1)
            
            return {
                "sentiment": sentiment,
                "keywords": keywords,
                "category": category,
                "urgency_score": urgency_score,
                "certainty_score": net_certainty,
                "signal_strength": signal_strength,
                "actionable": signal_strength > 0.3,
                "direction": "bullish" if sentiment['combined_score'] > 0 else "bearish"
            }
        
        except Exception as e:
            logger.error(f"Error detecting market signals: {e}")
            return {
                "sentiment": {"combined_score": 0.0, "overall_sentiment": "neutral"},
                "keywords": [],
                "category": "other",
                "urgency_score": 0,
                "certainty_score": 0,
                "signal_strength": 0.0,
                "actionable": False,
                "direction": "neutral"
            }
    
    def find_related_markets(
        self,
        target_market: str,
        market_list: List[str],
        threshold: float = 0.3
    ) -> List[Tuple[str, float]]:
        """
        Find markets related to a target market.
        
        Args:
            target_market: Target market description
            market_list: List of other market descriptions
            threshold: Minimum similarity threshold
            
        Returns:
            List of (market, similarity_score) tuples
        """
        try:
            related_markets = []
            
            for market in market_list:
                if market == target_market:
                    continue
                
                similarity = self.calculate_text_similarity(target_market, market)
                
                if similarity >= threshold:
                    related_markets.append((market, similarity))
            
            # Sort by similarity score
            related_markets.sort(key=lambda x: x[1], reverse=True)
            
            return related_markets
        
        except Exception as e:
            logger.error(f"Error finding related markets: {e}")
            return []
    
    def extract_entities(self, text: str) -> Dict[str, List[str]]:
        """
        Extract named entities from text.
        
        Args:
            text: Input text
            
        Returns:
            Dictionary with entity types and lists
        """
        try:
            # Simple entity extraction using TextBlob
            blob = TextBlob(text)
            
            # Get noun phrases as potential entities
            entities = {
                "organizations": [],
                "persons": [],
                "locations": [],
                "other": []
            }
            
            # Extract noun phrases
            for phrase in blob.noun_phrases:
                phrase = phrase.strip()
                
                # Simple heuristics for entity classification
                if any(word in phrase.lower() for word in ['inc', 'corp', 'llc', 'company', 'organization']):
                    entities["organizations"].append(phrase)
                elif any(word in phrase.lower() for word in ['president', 'senator', 'governor', 'minister']):
                    entities["persons"].append(phrase)
                elif phrase.istitle() and len(phrase.split()) == 1:
                    # Single capitalized word might be a location
                    entities["locations"].append(phrase)
                else:
                    entities["other"].append(phrase)
            
            return entities
        
        except Exception as e:
            logger.error(f"Error extracting entities: {e}")
            return {"organizations": [], "persons": [], "locations": [], "other": []}