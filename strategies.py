from typing import List, Dict, Tuple, Optional
import re


class BaseStrategy:
    """Base class for trading strategies"""
    
    def __init__(self, name: str):
        self.name = name
    
    def find_opportunities(self, markets_by_platform: Dict[str, List[Dict]]) -> List[Dict]:
        """Find arbitrage opportunities across platforms"""
        raise NotImplementedError


class ArbitrageStrategy(BaseStrategy):
    """Simple arbitrage strategy that finds price differences across platforms"""
    
    def __init__(self, min_spread: float = 0.05):
        super().__init__("arbitrage")
        self.min_spread = min_spread
    
    def find_opportunities(self, markets_by_platform: Dict[str, List[Dict]]) -> List[Dict]:
        """Find arbitrage opportunities between platforms"""
        opportunities = []
        
        platforms = list(markets_by_platform.keys())
        if len(platforms) < 2:
            return opportunities
        
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
        """Find matching markets between two platforms using simple text similarity"""
        matches = []
        
        for market1 in markets1:
            for market2 in markets2:
                if self._are_markets_similar(market1['title'], market2['title']):
                    matches.append((market1, market2))
        
        return matches
    
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
                'trade_amount': 100  # Fixed amount for simplicity
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
                'trade_amount': 100
            })
        
        return opportunities


class ExpiryStrategy(BaseStrategy):
    """Strategy that focuses on markets closest to expiry"""
    
    def __init__(self, max_days_to_expiry: float = 7, min_volume: float = 1000):
        super().__init__("expiry")
        self.max_days_to_expiry = max_days_to_expiry
        self.min_volume = min_volume
    
    def find_opportunities(self, markets_by_platform: Dict[str, List[Dict]]) -> List[Dict]:
        """Find markets close to expiry with potential for volatility"""
        from datetime import datetime, timedelta
        
        opportunities = []
        current_time = datetime.now()
        max_expiry_time = current_time + timedelta(days=self.max_days_to_expiry)
        
        # Collect all markets across platforms
        all_markets = []
        for platform, markets in markets_by_platform.items():
            all_markets.extend(markets)
        
        # Filter markets close to expiry
        expiring_markets = []
        for market in all_markets:
            close_time = market.get('close_time')
            if close_time and close_time <= max_expiry_time and close_time > current_time:
                # Calculate time to expiry
                time_to_expiry = close_time - current_time
                days_to_expiry = time_to_expiry.total_seconds() / (24 * 3600)
                
                # Only consider markets with sufficient volume
                if market.get('volume', 0) >= self.min_volume:
                    expiring_markets.append({
                        'market': market,
                        'days_to_expiry': days_to_expiry,
                        'hours_to_expiry': time_to_expiry.total_seconds() / 3600
                    })
        
        # Sort by time to expiry (closest first)
        expiring_markets.sort(key=lambda x: x['days_to_expiry'])
        
        # Create opportunities based on expiry proximity and price extremes
        for market_info in expiring_markets:
            market = market_info['market']
            days_to_expiry = market_info['days_to_expiry']
            hours_to_expiry = market_info['hours_to_expiry']
            
            yes_price = market.get('yes_price', 0.5)
            no_price = market.get('no_price', 0.5)
            
            # Look for extreme prices that might correct before expiry
            opportunity_type = None
            confidence_score = 0
            
            # Very high YES probability (might be overconfident)
            if yes_price >= 0.85:
                opportunity_type = "overconfident_yes"
                confidence_score = (yes_price - 0.85) * 10  # Scale 0-1.5
            
            # Very low YES probability (might be underestimated)  
            elif yes_price <= 0.15:
                opportunity_type = "undervalued_yes"
                confidence_score = (0.15 - yes_price) * 10  # Scale 0-1.5
            
            # Markets very close to 50/50 might resolve dramatically
            elif 0.45 <= yes_price <= 0.55:
                opportunity_type = "uncertain_resolution"
                confidence_score = 0.5 - abs(yes_price - 0.5)  # Higher score for closer to 50/50
            
            if opportunity_type:
                # Higher urgency for markets expiring sooner
                urgency_multiplier = max(0.1, 1 - (days_to_expiry / self.max_days_to_expiry))
                final_score = confidence_score * urgency_multiplier
                
                opportunities.append({
                    'type': 'expiry_based',
                    'subtype': opportunity_type,
                    'market': market,
                    'days_to_expiry': days_to_expiry,
                    'hours_to_expiry': hours_to_expiry,
                    'yes_price': yes_price,
                    'no_price': no_price,
                    'confidence_score': confidence_score,
                    'urgency_multiplier': urgency_multiplier,
                    'final_score': final_score,
                    'trade_amount': 100,
                    'expected_profit': final_score * 0.1,  # Estimate based on score
                    'recommended_action': self._get_recommended_action(opportunity_type, yes_price)
                })
        
        # Sort by final score (best opportunities first)
        opportunities.sort(key=lambda x: x['final_score'], reverse=True)
        return opportunities
    
    def _get_recommended_action(self, opportunity_type: str, yes_price: float) -> str:
        """Get recommended trading action based on opportunity type"""
        if opportunity_type == "overconfident_yes":
            return f"Consider selling YES at {yes_price:.3f} (may be overpriced)"
        elif opportunity_type == "undervalued_yes":
            return f"Consider buying YES at {yes_price:.3f} (may be undervalued)"
        elif opportunity_type == "uncertain_resolution":
            return f"High volatility expected - consider straddle or wait for news"
        return "Monitor for price movements"


# Registry for strategies
STRATEGIES = {
    'arbitrage': ArbitrageStrategy,
    'expiry': ExpiryStrategy
}


def get_strategy(strategy_name: str, **kwargs) -> BaseStrategy:
    """Factory function to get strategy instance"""
    if strategy_name not in STRATEGIES:
        raise ValueError(f"Unsupported strategy: {strategy_name}")
    
    return STRATEGIES[strategy_name](**kwargs)