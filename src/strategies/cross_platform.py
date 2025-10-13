"""
Cross-platform arbitrage strategy.

This strategy looks for the same market/bet across different platforms
and identifies arbitrage opportunities when prices differ.
"""
from typing import List, Dict, Any, Optional
import asyncio
from datetime import datetime, timedelta
from src.strategies.base import BaseStrategy, TradingSignal, ArbitrageOpportunity, SignalType
from src.data.providers import MarketData, OrderBook
from src.core.logger import get_logger
from src.core.config import get_settings

logger = get_logger(__name__)


class CrossPlatformArbitrageStrategy(BaseStrategy):
    """Strategy for finding arbitrage opportunities across platforms."""
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        super().__init__("cross_platform_arbitrage", config)
        self.settings = get_settings()
        self.min_spread = self.config.get("min_spread", self.settings.cross_platform_min_spread)
        self.max_position_size = self.config.get("max_position_size", 1000.0)
        self.similarity_threshold = self.config.get("similarity_threshold", 0.8)
        self.min_volume = self.config.get("min_volume", 100.0)
        self.found_opportunities = {}
    
    async def analyze_markets(
        self,
        markets: Dict[str, List[MarketData]],
        order_books: Optional[Dict[str, OrderBook]] = None
    ) -> List[TradingSignal]:
        """Analyze markets for cross-platform arbitrage signals."""
        signals = []
        
        try:
            # Find matching markets across platforms
            matches = await self._find_matching_markets(markets)
            
            for match in matches:
                platform1 = match["platform1"]
                market1 = match["market1"]
                platform2 = match["platform2"]
                market2 = match["market2"]
                
                # Calculate arbitrage opportunity
                arbitrage_signals = self._calculate_arbitrage(
                    platform1, market1, platform2, market2, order_books
                )
                signals.extend(arbitrage_signals)
        
        except Exception as e:
            logger.error(f"Error in cross-platform analysis: {e}")
            self.set_error(str(e))
        
        return signals
    
    async def find_opportunities(
        self,
        markets: Dict[str, List[MarketData]],
        order_books: Optional[Dict[str, OrderBook]] = None
    ) -> List[ArbitrageOpportunity]:
        """Find cross-platform arbitrage opportunities."""
        opportunities = []
        
        try:
            matches = await self._find_matching_markets(markets)
            
            for match in matches:
                platform1 = match["platform1"]
                market1 = match["market1"]
                platform2 = match["platform2"]
                market2 = match["market2"]
                similarity = match["similarity"]
                
                opportunity = self._evaluate_arbitrage_opportunity(
                    platform1, market1, platform2, market2, similarity, order_books
                )
                
                if opportunity:
                    opportunities.append(opportunity)
        
        except Exception as e:
            logger.error(f"Error finding opportunities: {e}")
            self.set_error(str(e))
        
        return opportunities
    
    async def _find_matching_markets(self, markets: Dict[str, List[MarketData]]) -> List[Dict[str, Any]]:
        """Find markets that match across platforms."""
        matches = []
        platforms = list(markets.keys())
        
        for i, platform1 in enumerate(platforms):
            for platform2 in platforms[i+1:]:
                markets1 = markets.get(platform1, [])
                markets2 = markets.get(platform2, [])
                
                for market1 in markets1:
                    for market2 in markets2:
                        # Skip if either market doesn't have prices
                        if not (market1.yes_price and market2.yes_price):
                            continue
                        
                        # Calculate similarity
                        similarity = self._calculate_market_similarity(market1, market2)
                        
                        if similarity >= self.similarity_threshold:
                            matches.append({
                                "platform1": platform1,
                                "market1": market1,
                                "platform2": platform2,
                                "market2": market2,
                                "similarity": similarity
                            })
        
        return matches
    
    def _calculate_market_similarity(self, market1: MarketData, market2: MarketData) -> float:
        """Calculate similarity between two markets."""
        # Simple text similarity (can be enhanced with NLP)
        title1_words = set(market1.title.lower().split())
        title2_words = set(market2.title.lower().split())
        
        # Jaccard similarity
        intersection = title1_words.intersection(title2_words)
        union = title1_words.union(title2_words)
        text_similarity = len(intersection) / len(union) if union else 0.0
        
        # Category similarity
        category_similarity = 1.0 if market1.category == market2.category else 0.0
        
        # Time similarity (markets should close around the same time)
        time_similarity = 1.0
        if market1.close_date and market2.close_date:
            time_diff = abs((market1.close_date - market2.close_date).total_seconds())
            # Penalize if close dates differ by more than 1 day
            if time_diff > 86400:  # 1 day in seconds
                time_similarity = max(0.0, 1.0 - time_diff / (7 * 86400))  # Decay over a week
        
        # Weighted average
        return (0.7 * text_similarity + 0.2 * category_similarity + 0.1 * time_similarity)
    
    def _calculate_arbitrage(
        self,
        platform1: str,
        market1: MarketData,
        platform2: str,
        market2: MarketData,
        order_books: Optional[Dict[str, OrderBook]] = None
    ) -> List[TradingSignal]:
        """Calculate arbitrage signals between two markets."""
        signals = []
        
        try:
            # Get prices (use order book if available, otherwise market data)
            price1_yes = market1.yes_price
            price1_no = market1.no_price or (1.0 - market1.yes_price) if market1.yes_price else None
            price2_yes = market2.yes_price
            price2_no = market2.no_price or (1.0 - market2.yes_price) if market2.yes_price else None
            
            if not all([price1_yes, price1_no, price2_yes, price2_no]):
                return signals
            
            # Check for arbitrage opportunities
            # Opportunity 1: Buy YES on platform1, sell YES on platform2
            if price2_yes - price1_yes > self.min_spread:
                profit = price2_yes - price1_yes
                confidence = min(1.0, profit / self.min_spread)
                
                # Buy signal for platform 1
                signals.append(TradingSignal(
                    strategy_name=self.name,
                    market_id=market1.market_id,
                    platform=platform1,
                    signal_type=SignalType.BUY,
                    outcome="yes",
                    confidence=confidence,
                    suggested_size=self._calculate_position_size(profit, price1_yes),
                    price_target=price1_yes,
                    metadata={
                        "arbitrage_pair": f"{platform2}:{market2.market_id}",
                        "expected_profit": profit,
                        "arbitrage_type": "cross_platform"
                    }
                ))
                
                # Sell signal for platform 2
                signals.append(TradingSignal(
                    strategy_name=self.name,
                    market_id=market2.market_id,
                    platform=platform2,
                    signal_type=SignalType.SELL,
                    outcome="yes",
                    confidence=confidence,
                    suggested_size=self._calculate_position_size(profit, price2_yes),
                    price_target=price2_yes,
                    metadata={
                        "arbitrage_pair": f"{platform1}:{market1.market_id}",
                        "expected_profit": profit,
                        "arbitrage_type": "cross_platform"
                    }
                ))
            
            # Opportunity 2: Buy YES on platform2, sell YES on platform1
            elif price1_yes - price2_yes > self.min_spread:
                profit = price1_yes - price2_yes
                confidence = min(1.0, profit / self.min_spread)
                
                # Buy signal for platform 2
                signals.append(TradingSignal(
                    strategy_name=self.name,
                    market_id=market2.market_id,
                    platform=platform2,
                    signal_type=SignalType.BUY,
                    outcome="yes",
                    confidence=confidence,
                    suggested_size=self._calculate_position_size(profit, price2_yes),
                    price_target=price2_yes,
                    metadata={
                        "arbitrage_pair": f"{platform1}:{market1.market_id}",
                        "expected_profit": profit,
                        "arbitrage_type": "cross_platform"
                    }
                ))
                
                # Sell signal for platform 1
                signals.append(TradingSignal(
                    strategy_name=self.name,
                    market_id=market1.market_id,
                    platform=platform1,
                    signal_type=SignalType.SELL,
                    outcome="yes",
                    confidence=confidence,
                    suggested_size=self._calculate_position_size(profit, price1_yes),
                    price_target=price1_yes,
                    metadata={
                        "arbitrage_pair": f"{platform2}:{market2.market_id}",
                        "expected_profit": profit,
                        "arbitrage_type": "cross_platform"
                    }
                ))
        
        except Exception as e:
            logger.error(f"Error calculating arbitrage: {e}")
        
        return signals
    
    def _evaluate_arbitrage_opportunity(
        self,
        platform1: str,
        market1: MarketData,
        platform2: str,
        market2: MarketData,
        similarity: float,
        order_books: Optional[Dict[str, OrderBook]] = None
    ) -> Optional[ArbitrageOpportunity]:
        """Evaluate and create arbitrage opportunity."""
        try:
            price1_yes = market1.yes_price
            price2_yes = market2.yes_price
            
            if not (price1_yes and price2_yes):
                return None
            
            # Calculate potential profit
            profit = abs(price2_yes - price1_yes)
            
            if profit < self.min_spread:
                return None
            
            # Calculate required capital (assuming equal position sizes)
            required_capital = min(price1_yes, price2_yes) * self.max_position_size
            
            # Calculate confidence score
            confidence_score = min(1.0, (profit / self.min_spread) * similarity)
            
            # Check volume requirements
            if market1.volume < self.min_volume or market2.volume < self.min_volume:
                confidence_score *= 0.5
            
            opportunity_id = f"cross_{platform1}_{market1.market_id}_{platform2}_{market2.market_id}"
            
            return ArbitrageOpportunity(
                opportunity_id=opportunity_id,
                strategy_name=self.name,
                opportunity_type="cross_platform",
                markets=[
                    {
                        "platform": platform1,
                        "market_id": market1.market_id,
                        "title": market1.title,
                        "yes_price": price1_yes,
                        "volume": market1.volume
                    },
                    {
                        "platform": platform2,
                        "market_id": market2.market_id,
                        "title": market2.title,
                        "yes_price": price2_yes,
                        "volume": market2.volume
                    }
                ],
                expected_profit=profit,
                required_capital=required_capital,
                confidence_score=confidence_score,
                expiry_time=datetime.utcnow() + timedelta(minutes=5),  # 5-minute window
                metadata={
                    "similarity_score": similarity,
                    "price_spread": profit,
                    "min_volume": min(market1.volume, market2.volume)
                }
            )
        
        except Exception as e:
            logger.error(f"Error evaluating opportunity: {e}")
            return None
    
    def _calculate_position_size(self, expected_profit: float, price: float) -> float:
        """Calculate appropriate position size based on profit and risk."""
        # Simple Kelly criterion approximation
        win_probability = 0.8  # Assume high probability for arbitrage
        win_amount = expected_profit
        loss_amount = price  # Maximum loss is the price paid
        
        if loss_amount > 0:
            kelly_fraction = (win_probability * win_amount - (1 - win_probability) * loss_amount) / loss_amount
            # Conservative approach: use 25% of Kelly
            position_fraction = max(0.0, min(0.25, kelly_fraction * 0.25))
            position_size = position_fraction * self.max_position_size
        else:
            position_size = self.max_position_size * 0.1  # Default to 10%
        
        return min(position_size, self.max_position_size)