import re
from typing import Dict, List, Optional, Tuple, Union
from datetime import datetime
from .planning import PortfolioPlanner, RiskManager
from ..types import Market, ArbitrageOpportunity, Opportunities, Outcome
from ..adapters import MarketAdapter, OpportunityAdapter, LegacyCompat


class BaseStrategy:
    """Base class for trading strategies"""
    
    def __init__(self, name: str):
        self.name = name
    
    def find_opportunities(self, markets_by_platform: Dict[str, List[Dict]]) -> List[ArbitrageOpportunity]:
        """Find arbitrage opportunities across platforms"""
        raise NotImplementedError


class ArbitrageStrategy(BaseStrategy):
    """Arbitrage strategy with intelligent position sizing and risk management"""
    
    def __init__(self, min_spread: float = 0.05, use_planning: bool = True):
        super().__init__("arbitrage")
        self.min_spread = min_spread
        self.use_planning = use_planning
        
        if use_planning:
            self.planner = PortfolioPlanner(
                max_position_pct=0.15,  # Max 15% per position
                max_platform_pct=0.65,  # Max 65% per platform
                correlation_threshold=0.7,
                min_cash_reserve=0.25    # Keep 25% cash
            )
            self.risk_manager = RiskManager()
        else:
            self.planner = None
            self.risk_manager = None
    
    def find_opportunities(self, markets_by_platform: Dict[str, List], 
                          portfolio_summary: Dict = None) -> List[ArbitrageOpportunity]:
        """Find arbitrage opportunities with optional portfolio-aware planning
        
        Args:
            markets_by_platform: Dict mapping platform names to market lists (dict or Market objects)
            portfolio_summary: Current portfolio state for planning
            
        Returns:
            List of ArbitrageOpportunity objects
        """
        # Convert input to typed format if needed
        typed_markets = {}
        for platform_name, markets_list in markets_by_platform.items():
            if markets_list and isinstance(markets_list[0], dict):
                # Convert legacy dict format to typed format
                typed_markets[platform_name] = MarketAdapter.from_dict_list(markets_list)
            else:
                # Already in typed format
                typed_markets[platform_name] = markets_list
        
        # Find opportunities using typed system
        typed_opportunities = self._find_typed_opportunities(typed_markets, portfolio_summary)
        
        # Return typed objects directly (no more legacy conversion!)
        return typed_opportunities
    
    def _find_typed_opportunities(self, markets_by_platform: Dict[str, List[Market]], 
                                portfolio_summary: Dict = None) -> List[ArbitrageOpportunity]:
        """Find opportunities using typed system"""
        opportunities = []
        
        platforms = list(markets_by_platform.keys())
        if len(platforms) < 2:
            return opportunities
        
        # Find basic arbitrage opportunities
        raw_opportunities = self._find_raw_typed_opportunities(markets_by_platform)
        
        # Apply strategic planning if enabled and portfolio data available
        if self.use_planning and self.planner and portfolio_summary:
            print(f"\n🎯 Found {len(raw_opportunities)} raw opportunities")
            
            # Convert to legacy format for planner (temporary compatibility)
            legacy_raw = OpportunityAdapter.to_dict_list(raw_opportunities)
            planned_legacy = self.planner.plan_trades(legacy_raw, portfolio_summary)
            planned_opportunities = OpportunityAdapter.from_dict_list(planned_legacy)
            
            # Show planning results
            if planned_opportunities:
                print(f"\n📋 Strategic Planning Results:")
                for i, opp in enumerate(planned_opportunities[:3], 1):
                    kelly_pct = (opp.kelly_fraction or 0) * 100
                    risk_adj_pct = (opp.risk_adjustment or 1) * 100
                    print(f"   {i}. {opp.outcome.value} | Size: {opp.recommended_quantity} shares | "
                          f"Kelly: {kelly_pct:.1f}% | Risk Adj: {risk_adj_pct:.1f}%")
                    print(f"      Expected: ${opp.expected_profit:.2f} | "
                          f"Win Prob: {(opp.win_probability or 0)*100:.1f}%")
            
            return planned_opportunities
        else:
            # Use simple fixed-size approach
            return raw_opportunities[:3]  # Limit to top 3
    
    def _find_raw_typed_opportunities(self, markets_by_platform: Dict[str, List[Market]]) -> List[ArbitrageOpportunity]:
        """Find basic arbitrage opportunities using typed system"""
        opportunities = []
        platforms = list(markets_by_platform.keys())
        
        # Compare markets between all platform pairs
        for i in range(len(platforms)):
            for j in range(i + 1, len(platforms)):
                platform1, platform2 = platforms[i], platforms[j]
                markets1 = markets_by_platform[platform1]
                markets2 = markets_by_platform[platform2]
                
                # Find matching markets
                matches = self._find_typed_market_matches(markets1, markets2)
                
                # Calculate arbitrage opportunities
                for market1, market2 in matches:
                    arb_ops = self._calculate_typed_arbitrage(market1, market2)
                    opportunities.extend(arb_ops)
        
        # Sort by profitability
        opportunities.sort(key=lambda x: x.expected_profit_per_share, reverse=True)
        return opportunities
    
    def _find_typed_market_matches(self, markets1: List[Market], markets2: List[Market]) -> List[Tuple[Market, Market]]:
        """Find matching markets between two platforms using typed system"""
        matches = []
        
        for market1 in markets1:
            for market2 in markets2:
                if self._are_markets_similar(market1.title, market2.title):
                    matches.append((market1, market2))
        
        return matches
    
    def _calculate_typed_arbitrage(self, market1: Market, market2: Market) -> List[ArbitrageOpportunity]:
        """Calculate arbitrage opportunities between two typed markets"""
        opportunities = []
        
        # Check YES arbitrage
        yes_spread = abs(market1.yes_price - market2.yes_price)
        if yes_spread >= self.min_spread:
            if market1.yes_price < market2.yes_price:
                buy_market, sell_market = market1, market2
                buy_price, sell_price = market1.yes_price, market2.yes_price
            else:
                buy_market, sell_market = market2, market1
                buy_price, sell_price = market2.yes_price, market1.yes_price
            
            profit_per_share = sell_price - buy_price
            opp_id = f"{buy_market.id}_{sell_market.id}_YES_{int(datetime.now().timestamp())}"
            
            opportunity = ArbitrageOpportunity(
                id=opp_id,
                buy_market=buy_market,
                sell_market=sell_market,
                outcome=Outcome.YES,
                buy_price=buy_price,
                sell_price=sell_price,
                spread=yes_spread,
                expected_profit_per_share=profit_per_share,
                confidence_score=min(1.0, yes_spread * 10),
                max_quantity=100
            )
            opportunities.append(opportunity)
        
        # Check NO arbitrage
        no_spread = abs(market1.no_price - market2.no_price)
        if no_spread >= self.min_spread:
            if market1.no_price < market2.no_price:
                buy_market, sell_market = market1, market2
                buy_price, sell_price = market1.no_price, market2.no_price
            else:
                buy_market, sell_market = market2, market1
                buy_price, sell_price = market2.no_price, market1.no_price
            
            profit_per_share = sell_price - buy_price
            opp_id = f"{buy_market.id}_{sell_market.id}_NO_{int(datetime.now().timestamp())}"
            
            opportunity = ArbitrageOpportunity(
                id=opp_id,
                buy_market=buy_market,
                sell_market=sell_market,
                outcome=Outcome.NO,
                buy_price=buy_price,
                sell_price=sell_price,
                spread=no_spread,
                expected_profit_per_share=profit_per_share,
                confidence_score=min(1.0, no_spread * 10),
                max_quantity=100
            )
            opportunities.append(opportunity)
        
        return opportunities
        """Find basic arbitrage opportunities without planning"""
        opportunities = []
        platforms = list(markets_by_platform.keys())
        
        # Compare markets between all platform pairs
        for i in range(len(platforms)):
            for j in range(i + 1, len(platforms)):
                platform1, platform2 = platforms[i], platforms[j]
                markets1 = markets_by_platform[platform1]
                markets2 = markets_by_platform[platform2]
                
                # Find matching markets
                matches = self._find_market_matches(markets1, markets2)
                
                # Calculate arbitrage opportunities
                for match in matches:
                    market1, market2 = match
                    arb_ops = self._calculate_arbitrage(market1, market2)
                    opportunities.extend(arb_ops)
        
        # Sort by profitability
        opportunities.sort(key=lambda x: x['expected_profit'], reverse=True)
        return opportunities
    
    def _find_market_matches(self, markets1: List[Dict], markets2: List[Dict]) -> List[Tuple[Dict, Dict]]:
        """Find matching markets between two platforms using multiple strategies"""
        matches = []
        
        # Strategy 1: Direct title similarity (existing approach)
        for market1 in markets1:
            for market2 in markets2:
                if self._are_markets_similar(market1['title'], market2['title']):
                    matches.append((market1, market2))
        
        # Strategy 2: Entity-based matching
        matches.extend(self._find_matches_by_entities(markets1, markets2))
        
        # Strategy 3: Event search API (for new markets)
        matches.extend(self._find_matches_by_search(markets1, markets2))
        
        # Remove duplicates by market IDs
        seen = set()
        unique_matches = []
        for match in matches:
            market1, market2 = match
            key = (market1['id'], market2['id'])
            if key not in seen:
                seen.add(key)
                unique_matches.append(match)
        return unique_matches
    
    def _are_markets_similar(self, title1: str, title2: str, threshold: float = 0.6) -> bool:
        """Check if two market titles are similar enough to be the same event"""
        # Simple similarity check using common keywords
        
        # Clean and normalize titles
        title1_clean = self._clean_title(title1.lower())
        title2_clean = self._clean_title(title2.lower())
        
        # Extract key words (longer than 3 characters)
        words1 = set([w for w in title1_clean.split() if len(w) > 3])
        words2 = set([w for w in title2_clean.split() if len(w) > 3])
        
        if not words1 or not words2:
            return False
        
        # Calculate Jaccard similarity
        intersection = words1.intersection(words2)
        union = words1.union(words2)
        
        similarity = len(intersection) / len(union) if union else 0
        return similarity >= threshold
    
    def _clean_title(self, title: str) -> str:
        """Clean market title for comparison"""
        # Remove common prediction market phrases
        title = re.sub(r'\b(will|by|before|after|in|on|the|a|an|and|or)\b', '', title)
        # Remove punctuation and extra spaces
        title = re.sub(r'[^\w\s]', ' ', title)
        title = re.sub(r'\s+', ' ', title).strip()
        return title
    
    def _find_matches_by_entities(self, markets1: List[Dict], markets2: List[Dict]) -> List[Tuple[Dict, Dict]]:
        """Find matches by extracting entities from market titles"""
        matches = []
        
        # Common entities and their variations
        entity_patterns = {
            'trump': r'\b(trump|donald trump|president trump|djt)\b',
            'biden': r'\b(biden|joe biden|president biden)\b',  
            'fed': r'\b(fed|federal reserve|jerome powell|fomc|interest rate)\b',
            'apple': r'\b(apple|aapl|apple inc)\b',
            'tesla': r'\b(tesla|tsla)\b',
            'election_2024': r'\b(2024|election|president|presidential)\b',
        }
        
        # Extract entities for each market
        for market1 in markets1:
            entities1 = self._extract_entities(market1['title'], entity_patterns)
            if not entities1:
                continue
                
            for market2 in markets2:
                entities2 = self._extract_entities(market2['title'], entity_patterns)
                
                # If they share any entities, they might be related
                if entities1.intersection(entities2):
                    # Additional check: similar event type
                    if self._similar_event_type(market1['title'], market2['title']):
                        matches.append((market1, market2))
        
        return matches
    
    def _find_matches_by_search(self, markets1: List[Dict], markets2: List[Dict]) -> List[Tuple[Dict, Dict]]:
        """Find matches by searching each platform for related events"""
        matches = []
        
        # For each new market, search other platform for related events
        for market1 in markets1:
            # Extract key search terms from market title
            search_terms = self._extract_search_terms(market1['title'])
            
            for market2 in markets2:
                # Check if market2 matches any of the search terms
                if self._matches_search_terms(market2['title'], search_terms):
                    matches.append((market1, market2))
        
        return matches
    
    def _extract_entities(self, title: str, patterns: dict) -> set:
        """Extract entities from title using regex patterns"""
        entities = set()
        title_lower = title.lower()
        
        for entity, pattern in patterns.items():
            if re.search(pattern, title_lower):
                entities.add(entity)
        
        return entities
    
    def _similar_event_type(self, title1: str, title2: str) -> bool:
        """Check if two titles describe similar types of events"""
        event_type_patterns = {
            'win_lose': r'\b(wins?|loses?|defeats?|victory|beats?)\b',
            'price_target': r'\b(\$\d+|above|below|reaches?|hits?)\b',
            'rate_change': r'\b(cuts?|raises?|increases?|decreases?|rate)\b',
            'earnings': r'\b(earnings|revenue|beats?|misses?|exceeds?)\b',
        }
        
        for event_type, pattern in event_type_patterns.items():
            if (re.search(pattern, title1.lower()) and 
                re.search(pattern, title2.lower())):
                return True
        
        return False
    
    def _extract_search_terms(self, title: str) -> List[str]:
        """Extract key search terms from a market title"""
        # Remove common prediction market words
        stop_words = {'will', 'be', 'by', 'before', 'after', 'on', 'the', 'a', 'an', 'and', 'or', 'in'}
        
        # Extract meaningful words (3+ characters)
        words = re.findall(r'\b\w{3,}\b', title.lower())
        search_terms = [word for word in words if word not in stop_words]
        
        # Take most important terms (first half, assuming they're more relevant)
        return search_terms[:len(search_terms)//2 + 1]
    
    def _matches_search_terms(self, title: str, search_terms: List[str]) -> bool:
        """Check if title matches any of the search terms"""
        title_lower = title.lower()
        
        # Count how many search terms appear in the title
        matches = sum(1 for term in search_terms if term in title_lower)
        
        # Require at least 50% of search terms to match
        threshold = max(1, len(search_terms) * 0.5)
        return matches >= threshold
    
    def _calculate_arbitrage(self, market1: Dict, market2: Dict) -> List[Dict]:
        """Calculate arbitrage opportunities between two markets"""
        opportunities = []
        
        # Check YES arbitrage (buy YES on one, sell YES on other)
        yes_spread = abs(market1['yes_price'] - market2['yes_price'])
        if yes_spread >= self.min_spread:
            # Determine which market to buy/sell
            if market1['yes_price'] < market2['yes_price']:
                buy_market, sell_market = market1, market2
                buy_price, sell_price = market1['yes_price'], market2['yes_price']
            else:
                buy_market, sell_market = market2, market1
                buy_price, sell_price = market2['yes_price'], market1['yes_price']
            
                profit = sell_price - buy_price
                opportunities.append({
                    'type': 'arbitrage',
                    'outcome': 'YES',
                    'buy_market': buy_market,
                    'sell_market': sell_market,
                    'buy_price': buy_price,
                    'sell_price': sell_price,
                    'spread': yes_spread,
                    'expected_profit': profit,
                    'trade_amount': 100,  # Will be overridden by planner
                    'base_position_size': 100  # Default size before planning
                })        # Check NO arbitrage
        no_spread = abs(market1['no_price'] - market2['no_price'])
        if no_spread >= self.min_spread:
            if market1['no_price'] < market2['no_price']:
                buy_market, sell_market = market1, market2
                buy_price, sell_price = market1['no_price'], market2['no_price']
            else:
                buy_market, sell_market = market2, market1
                buy_price, sell_price = market2['no_price'], market1['no_price']
            
                profit = sell_price - buy_price
                opportunities.append({
                    'type': 'arbitrage',
                    'outcome': 'NO',
                    'buy_market': buy_market,
                    'sell_market': sell_market,
                    'buy_price': buy_price,
                    'sell_price': sell_price,
                    'spread': no_spread,
                    'expected_profit': profit,
                    'trade_amount': 100,  # Will be overridden by planner
                    'base_position_size': 100  # Default size before planning
                })
        
        return opportunities


# Registry for strategies
STRATEGIES = {
    'arbitrage': ArbitrageStrategy
}


def get_strategy(strategy_name: str, **kwargs) -> BaseStrategy:
    """Factory function to get strategy instance"""
    if strategy_name not in STRATEGIES:
        raise ValueError(f"Unsupported strategy: {strategy_name}")
    
    return STRATEGIES[strategy_name](**kwargs)