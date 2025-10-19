from typing import List, Dict, Tuple
import re
from . import BaseStrategy

class ArbitrageStrategy(BaseStrategy):
    """Simple arbitrage strategy that finds price differences across platforms"""
    def __init__(self, min_spread: float = 0.05):
        super().__init__("arbitrage")
        self.min_spread = min_spread

    def find_opportunities(self, markets_by_platform: Dict[str, List[Dict]]) -> List[Dict]:
        opportunities = []
        platforms = list(markets_by_platform.keys())
        if len(platforms) < 2:
            return opportunities
        for i in range(len(platforms)):
            for j in range(i + 1, len(platforms)):
                platform1, platform2 = platforms[i], platforms[j]
                markets1 = markets_by_platform[platform1]
                markets2 = markets_by_platform[platform2]
                matches = self._find_market_matches(markets1, markets2)
                for match in matches:
                    market1, market2 = match
                    arb_ops = self._calculate_arbitrage(market1, market2)
                    opportunities.extend(arb_ops)
        opportunities.sort(key=lambda x: x['expected_profit'], reverse=True)
        return opportunities

    def _find_market_matches(self, markets1: List[Dict], markets2: List[Dict]) -> List[Tuple[Dict, Dict]]:
        matches = []
        for market1 in markets1:
            for market2 in markets2:
                if self._are_markets_similar(market1['title'], market2['title']):
                    matches.append((market1, market2))
        return matches

    def _are_markets_similar(self, title1: str, title2: str, threshold: float = 0.6) -> bool:
        title1_clean = self._clean_title(title1.lower())
        title2_clean = self._clean_title(title2.lower())
        words1 = set([w for w in title1_clean.split() if len(w) > 3])
        words2 = set([w for w in title2_clean.split() if len(w) > 3])
        if not words1 or not words2:
            return False
        intersection = words1.intersection(words2)
        union = words1.union(words2)
        similarity = len(intersection) / len(union) if union else 0
        return similarity >= threshold

    def _clean_title(self, title: str) -> str:
        title = re.sub(r'\b(will|by|before|after|in|on|the|a|an|and|or)\b', '', title)
        title = re.sub(r'[^\w\s]', ' ', title)
        title = re.sub(r'\s+', ' ', title).strip()
        return title

    def _calculate_arbitrage(self, market1: Dict, market2: Dict) -> List[Dict]:
        opportunities = []
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
                'trade_amount': 100
            })
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
