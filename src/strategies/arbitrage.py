"""
Simplified arbitrage strategy - clean and uncomplicated
"""

import re
import uuid
from typing import Dict, List, Optional, Tuple, Union
from datetime import datetime
from ..types import Market, ArbitrageOpportunity, Outcome, Platform, RiskLevel


class BaseStrategy:
    """Base class for trading strategies"""
    
    def __init__(self, name: str):
        self.name = name
    
    def find_opportunities(self, markets_by_platform: Dict[str, List[Dict]]) -> List[ArbitrageOpportunity]:
        """Find arbitrage opportunities - to be implemented by subclasses"""
        raise NotImplementedError


class ArbitrageStrategy(BaseStrategy):
    """Simplified arbitrage strategy focusing on core functionality"""
    
    def __init__(self, min_spread: float = 0.05, **kwargs):
        super().__init__("Arbitrage Strategy")
        self.min_spread = min_spread
        # Simplified - remove complex planning for now
        self.use_planning = False
    
    def find_opportunities(self, markets_by_platform: Dict[str, List], 
                          portfolio_summary: Dict = None) -> List[ArbitrageOpportunity]:
        """Find arbitrage opportunities using simple dict-based approach"""
        opportunities = []
        
        platforms = list(markets_by_platform.keys())
        if len(platforms) < 2:
            return opportunities
        
        # Find basic arbitrage opportunities
        for i in range(len(platforms)):
            for j in range(i + 1, len(platforms)):
                platform1, platform2 = platforms[i], platforms[j]
                markets1 = markets_by_platform[platform1]
                markets2 = markets_by_platform[platform2]
                
                # Find matching markets
                matches = self._find_market_matches(markets1, markets2)
                
                # Calculate arbitrage opportunities
                for market1, market2 in matches:
                    arb_ops = self._calculate_arbitrage(market1, market2)
                    for opp_dict in arb_ops:
                        # Convert dict to typed opportunity
                        opportunity = self._dict_to_opportunity(opp_dict)
                        opportunities.append(opportunity)
        
        # Sort by profitability and return top opportunities
        opportunities.sort(key=lambda x: x.expected_profit_per_share, reverse=True)
        return opportunities[:10]  # Limit to top 10 for simplicity
    
    def _dict_to_opportunity(self, opp_dict: Dict) -> ArbitrageOpportunity:
        """Convert dict opportunity to typed ArbitrageOpportunity object"""
        from ..types import Quote
        
        # Create Market objects from dicts
        buy_market = Market(
            id=opp_dict['buy_market']['id'],
            title=opp_dict['buy_market']['title'],
            platform=Platform(opp_dict['buy_market']['platform']),
            yes_quote=Quote(
                price=opp_dict['buy_market']['yes_price'],
                volume=100,  # Default volume
                liquidity=100  # Default liquidity
            ),
            no_quote=Quote(
                price=opp_dict['buy_market']['no_price'],
                volume=100,  # Default volume
                liquidity=100  # Default liquidity
            ),
            total_volume=opp_dict['buy_market'].get('volume', 1000),
            total_liquidity=opp_dict['buy_market'].get('volume', 1000)
        )
        
        sell_market = Market(
            id=opp_dict['sell_market']['id'],
            title=opp_dict['sell_market']['title'],
            platform=Platform(opp_dict['sell_market']['platform']),
            yes_quote=Quote(
                price=opp_dict['sell_market']['yes_price'],
                volume=100,  # Default volume
                liquidity=100  # Default liquidity
            ),
            no_quote=Quote(
                price=opp_dict['sell_market']['no_price'],
                volume=100,  # Default volume
                liquidity=100  # Default liquidity
            ),
            total_volume=opp_dict['sell_market'].get('volume', 1000),
            total_liquidity=opp_dict['sell_market'].get('volume', 1000)
        )
        
        return ArbitrageOpportunity(
            id=str(uuid.uuid4()),
            buy_market=buy_market,
            sell_market=sell_market,
            outcome=Outcome(opp_dict['outcome']),
            buy_price=opp_dict['buy_price'],
            sell_price=opp_dict['sell_price'],
            spread=opp_dict['spread'],
            expected_profit_per_share=opp_dict['expected_profit'],
            max_quantity=opp_dict.get('trade_amount', 100),
            confidence_score=1.0,
            risk_level=RiskLevel.MEDIUM,
            timestamp=datetime.now()
        )
    
    def _find_market_matches(self, markets1: List[Dict], markets2: List[Dict]) -> List[Tuple[Dict, Dict]]:
        """Find matching markets between two platforms using simple similarity"""
        matches = []
        
        for market1 in markets1:
            for market2 in markets2:
                if self._are_markets_similar(market1['title'], market2['title']):
                    matches.append((market1, market2))
        
        return matches
    
    def _are_markets_similar(self, title1: str, title2: str) -> bool:
        """Simple market similarity check"""
        # Normalize titles for comparison
        norm1 = re.sub(r'[^a-zA-Z0-9\s]', '', title1.lower())
        norm2 = re.sub(r'[^a-zA-Z0-9\s]', '', title2.lower())
        
        # Split into words
        words1 = set(norm1.split())
        words2 = set(norm2.split())
        
        # Remove common stop words
        stop_words = {'the', 'a', 'an', 'and', 'or', 'but', 'in', 'on', 'at', 'to', 'for', 'of', 'with', 'by', 'will', 'be'}
        words1 = words1 - stop_words
        words2 = words2 - stop_words
        
        if not words1 or not words2:
            return False
        
        # Calculate similarity
        intersection = len(words1.intersection(words2))
        union = len(words1.union(words2))
        
        similarity = intersection / union if union > 0 else 0
        return similarity > 0.5  # At least 50% word overlap
    
    def _calculate_arbitrage(self, market1: Dict, market2: Dict) -> List[Dict]:
        """Calculate arbitrage opportunities between two markets"""
        opportunities = []
        
        # Check YES arbitrage
        yes_spread = abs(market1['yes_price'] - market2['yes_price'])
        if yes_spread >= self.min_spread:
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
                'trade_amount': 100,  # Simple fixed amount
                'base_position_size': 100
            })
        
        # Check NO arbitrage
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
                'trade_amount': 100,  # Simple fixed amount
                'base_position_size': 100
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