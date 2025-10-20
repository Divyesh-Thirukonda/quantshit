"""
Advanced Event Matching Strategies for Arbitrage Detection

This module provides multiple approaches to find related events across platforms
beyond simple title matching.
"""

import json
import re
import requests
from collections import defaultdict
from dataclasses import dataclass
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Set, Tuple

@dataclass
class EventEntity:
    """Represents a standardized event entity"""
    entity_type: str  # person, election, company, sports_team, etc.
    entity_name: str  # Trump, 2024_election, Apple, etc.
    event_type: str   # win, rate_cut, earnings, etc.
    deadline: datetime
    market_text: str
    platform: str
    market_id: str

class EventMatcher:
    """Advanced event matching using multiple strategies"""
    
    def __init__(self):
        # Common entities and their variations
        self.entity_aliases = {
            'trump': ['trump', 'donald trump', 'president trump', 'djt'],
            'biden': ['biden', 'joe biden', 'president biden'],
            'fed': ['fed', 'federal reserve', 'jerome powell', 'fomc'],
            'apple': ['apple', 'aapl', 'apple inc'],
            'tesla': ['tesla', 'tsla', 'elon musk tesla'],
            # Add more as needed
        }
        
        self.event_patterns = {
            'election_win': r'(wins?|victory|elected|defeats?)',
            'rate_cut': r'(cuts?|lowers?|reduces?|rate)',
            'earnings_beat': r'(beats?|exceeds?|earnings|revenue)',
            'stock_price': r'(\$\d+|above|below|reaches?)',
        }

    # Strategy 1: Entity-Based Matching
    def find_related_by_entities(self, markets: List[Dict]) -> List[Tuple[Dict, Dict]]:
        """Group markets by extracted entities (people, companies, events)"""
        entity_groups = defaultdict(list)
        
        for market in markets:
            entities = self._extract_entities(market['title'])
            for entity in entities:
                entity_groups[entity].append(market)
        
        # Find pairs within each entity group
        pairs = []
        for entity, group_markets in entity_groups.items():
            if len(group_markets) >= 2:
                # Compare all pairs within the group
                for i in range(len(group_markets)):
                    for j in range(i + 1, len(group_markets)):
                        if group_markets[i]['platform'] != group_markets[j]['platform']:
                            pairs.append((group_markets[i], group_markets[j]))
        
        return pairs

    # Strategy 2: Semantic Search (requires external API)
    def find_related_by_semantic_search(self, new_market_title: str, all_markets: List[Dict]) -> List[Dict]:
        """Use semantic similarity to find related markets"""
        # This would use OpenAI embeddings or similar
        # For now, return enhanced keyword matching
        
        keywords = self._extract_keywords(new_market_title)
        related = []
        
        for market in all_markets:
            market_keywords = self._extract_keywords(market['title'])
            overlap_score = len(keywords.intersection(market_keywords)) / len(keywords.union(market_keywords))
            
            if overlap_score > 0.3:  # 30% keyword overlap
                market['similarity_score'] = overlap_score
                related.append(market)
        
        return sorted(related, key=lambda x: x['similarity_score'], reverse=True)

    # Strategy 3: Event Timeline Matching  
    def find_related_by_timeline(self, markets: List[Dict], time_window_days: int = 7) -> List[Tuple[Dict, Dict]]:
        """Find markets with similar deadlines (same event, different platforms)"""
        pairs = []
        
        # Group by deadline clusters
        deadline_groups = defaultdict(list)
        
        for market in markets:
            if 'deadline' in market:
                deadline = datetime.fromisoformat(market['deadline'].replace('Z', '+00:00'))
                # Round to week for clustering
                week_key = deadline.strftime('%Y-%W')
                deadline_groups[week_key].append(market)
        
        # Find cross-platform pairs in same time window
        for group_markets in deadline_groups.values():
            platforms_in_group = set(m['platform'] for m in group_markets)
            if len(platforms_in_group) >= 2:
                for i in range(len(group_markets)):
                    for j in range(i + 1, len(group_markets)):
                        m1, m2 = group_markets[i], group_markets[j]
                        if (m1['platform'] != m2['platform'] and 
                            self._titles_related(m1['title'], m2['title'])):
                            pairs.append((m1, m2))
        
        return pairs

    # Strategy 4: Real-time Event Detection
    def find_related_by_news_events(self, markets: List[Dict]) -> List[Tuple[Dict, Dict]]:
        """Match markets based on current news events"""
        # This would integrate with news APIs to find trending topics
        # For now, simulate with common trending keywords
        
        trending_topics = self._get_trending_topics()  # Mock function
        pairs = []
        
        for topic in trending_topics:
            topic_markets = []
            for market in markets:
                if any(keyword in market['title'].lower() for keyword in topic['keywords']):
                    topic_markets.append(market)
            
            # Find cross-platform pairs for this topic
            for i in range(len(topic_markets)):
                for j in range(i + 1, len(topic_markets)):
                    m1, m2 = topic_markets[i], topic_markets[j]
                    if m1['platform'] != m2['platform']:
                        pairs.append((m1, m2))
        
        return pairs

    # Strategy 5: API-Based Event Search
    def search_related_markets_api(self, event_description: str, platforms: List[str]) -> Dict[str, List[Dict]]:
        """Search each platform API for markets related to an event"""
        results = {}
        
        for platform in platforms:
            if platform == 'polymarket':
                results[platform] = self._search_polymarket(event_description)
            elif platform == 'kalshi':
                results[platform] = self._search_kalshi(event_description)
            elif platform == 'manifold':
                results[platform] = self._search_manifold(event_description)
        
        return results

    def _search_polymarket(self, query: str) -> List[Dict]:
        """Search Polymarket API for related markets"""
        try:
            # Polymarket search endpoint (example)
            url = "https://gamma-api.polymarket.com/markets"
            params = {
                'q': query,
                'limit': 20,
                'active': 'true'
            }
            
            response = requests.get(url, params=params, timeout=10)
            if response.status_code == 200:
                return response.json()
            else:
                return []
        except:
            return []

    def _search_kalshi(self, query: str) -> List[Dict]:
        """Search Kalshi API for related markets"""
        try:
            # Kalshi search would go here
            # url = "https://trading-api.kalshi.com/trade-api/v2/markets/search"
            return []  # Placeholder
        except:
            return []

    def _search_manifold(self, query: str) -> List[Dict]:
        """Search Manifold API for related markets"""
        try:
            url = "https://manifold.markets/api/v0/search-markets"
            params = {'terms': query, 'limit': 20}
            
            response = requests.get(url, params=params, timeout=10)
            if response.status_code == 200:
                return response.json()
            else:
                return []
        except:
            return []

    # Helper methods
    def _extract_entities(self, text: str) -> Set[str]:
        """Extract named entities from market text"""
        entities = set()
        text_lower = text.lower()
        
        # Check for known entity aliases
        for entity, aliases in self.entity_aliases.items():
            if any(alias in text_lower for alias in aliases):
                entities.add(entity)
        
        return entities

    def _extract_keywords(self, text: str) -> Set[str]:
        """Extract meaningful keywords from text"""
        # Remove common words and extract important terms
        stop_words = {'will', 'be', 'the', 'a', 'an', 'and', 'or', 'but', 'in', 'on', 'at', 'to', 'for', 'of', 'with', 'by'}
        
        words = re.findall(r'\b\w{3,}\b', text.lower())
        keywords = set(word for word in words if word not in stop_words)
        
        return keywords

    def _titles_related(self, title1: str, title2: str, threshold: float = 0.4) -> bool:
        """Check if two titles are related using improved similarity"""
        keywords1 = self._extract_keywords(title1)
        keywords2 = self._extract_keywords(title2)
        
        if not keywords1 or not keywords2:
            return False
            
        intersection = keywords1.intersection(keywords2)
        union = keywords1.union(keywords2)
        
        jaccard_sim = len(intersection) / len(union) if union else 0
        return jaccard_sim >= threshold

    def _get_trending_topics(self) -> List[Dict]:
        """Get trending topics (mock implementation)"""
        # This would integrate with news APIs or social media trends
        return [
            {'keywords': ['election', '2024', 'president'], 'topic': '2024_election'},
            {'keywords': ['fed', 'rate', 'cut', 'interest'], 'topic': 'fed_policy'},
            {'keywords': ['earnings', 'apple', 'tesla'], 'topic': 'tech_earnings'},
        ]

# Usage Example
def enhanced_arbitrage_strategy(markets_by_platform: Dict[str, List[Dict]]) -> List[Dict]:
    """Enhanced arbitrage strategy using multiple matching approaches"""
    matcher = EventMatcher()
    all_markets = []
    
    # Flatten all markets
    for platform_markets in markets_by_platform.values():
        all_markets.extend(platform_markets)
    
    opportunities = []
    
    # Strategy 1: Entity-based matching
    entity_pairs = matcher.find_related_by_entities(all_markets)
    
    # Strategy 2: Timeline-based matching  
    timeline_pairs = matcher.find_related_by_timeline(all_markets)
    
    # Strategy 3: News event matching
    news_pairs = matcher.find_related_by_news_events(all_markets)
    
    # Combine all pairs and remove duplicates
    all_pairs = list(set(entity_pairs + timeline_pairs + news_pairs))
    
    # Calculate arbitrage for each pair
    for market1, market2 in all_pairs:
        arb_opportunity = calculate_arbitrage_opportunity(market1, market2)
        if arb_opportunity:
            opportunities.append(arb_opportunity)
    
    return sorted(opportunities, key=lambda x: x['expected_profit'], reverse=True)

def calculate_arbitrage_opportunity(market1: Dict, market2: Dict) -> Optional[Dict]:
    """Calculate arbitrage opportunity between two markets"""
    # Implementation would go here
    pass