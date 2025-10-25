"""
Fixed arbitrage strategy that works with actual constraints
"""

from typing import Dict, List
import itertools


class FixedArbitrageStrategy:
    """
    Arbitrage strategy that accounts for real trading constraints
    """
    
    def __init__(self, min_spread: float = 0.05):
        self.min_spread = min_spread
    
    def find_opportunities(self, markets_data: Dict[str, List[Dict]]) -> List[Dict]:
        """Find profitable arbitrage opportunities"""
        opportunities = []
        
        # Get all platform combinations
        platforms = list(markets_data.keys())
        if len(platforms) < 2:
            return opportunities
        
        # Try to match markets across platforms
        for platform_a, platform_b in itertools.combinations(platforms, 2):
            markets_a = markets_data[platform_a]
            markets_b = markets_data[platform_b]
            
            # Find matching markets (simplified matching by similar titles)
            matches = self._find_matching_markets(markets_a, markets_b)
            
            for match in matches:
                market_a, market_b = match
                
                # Strategy 1: Directional Arbitrage (most common)
                # Buy YES on cheaper platform, buy NO on more expensive platform
                yes_a = market_a['yes_price']
                no_a = market_a['no_price']
                yes_b = market_b['yes_price']
                no_b = market_b['no_price']
                
                # Check if we can buy YES on A and NO on B for profit
                cost_yes_a_no_b = yes_a + no_b
                if cost_yes_a_no_b < 1.0:  # Should sum to less than $1
                    profit = 1.0 - cost_yes_a_no_b
                    if profit >= self.min_spread:
                        opportunities.append({
                            'type': 'directional',
                            'platform_a': platform_a,
                            'platform_b': platform_b,
                            'market_a': market_a,
                            'market_b': market_b,
                            'strategy': 'YES_A_NO_B',
                            'yes_price_a': yes_a,
                            'no_price_b': no_b,
                            'total_cost': cost_yes_a_no_b,
                            'expected_profit': profit,
                            'spread': profit,
                            'trade_amount': 100,  # Fixed for now
                            'outcome': f"YES {market_a['title'][:30]}... vs NO {market_b['title'][:30]}..."
                        })
                
                # Check if we can buy NO on A and YES on B for profit
                cost_no_a_yes_b = no_a + yes_b
                if cost_no_a_yes_b < 1.0:
                    profit = 1.0 - cost_no_a_yes_b
                    if profit >= self.min_spread:
                        opportunities.append({
                            'type': 'directional',
                            'platform_a': platform_a,
                            'platform_b': platform_b,
                            'market_a': market_a,
                            'market_b': market_b,
                            'strategy': 'NO_A_YES_B',
                            'no_price_a': no_a,
                            'yes_price_b': yes_b,
                            'total_cost': cost_no_a_yes_b,
                            'expected_profit': profit,
                            'spread': profit,
                            'trade_amount': 100,
                            'outcome': f"NO {market_a['title'][:30]}... vs YES {market_b['title'][:30]}..."
                        })
        
        # Sort by expected profit
        opportunities.sort(key=lambda x: x['expected_profit'], reverse=True)
        return opportunities
    
    def _find_matching_markets(self, markets_a: List[Dict], markets_b: List[Dict]) -> List[tuple]:
        """Find markets that are about the same event"""
        matches = []
        
        for market_a in markets_a:
            for market_b in markets_b:
                # Simple matching: look for similar keywords
                title_a = market_a['title'].lower()
                title_b = market_b['title'].lower()
                
                # Check for common keywords
                keywords_a = set(title_a.split())
                keywords_b = set(title_b.split())
                
                # If they share significant keywords, consider them a match
                common_keywords = keywords_a.intersection(keywords_b)
                if len(common_keywords) >= 2:  # At least 2 common words
                    matches.append((market_a, market_b))
        
        return matches