"""
Correlation arbitrage strategy.

This strategy looks for related/correlated markets on the same platform
where price discrepancies indicate arbitrage opportunities.
"""
from typing import List, Dict, Any, Optional, Tuple
import numpy as np
from datetime import datetime, timedelta
from src.strategies.base import BaseStrategy, TradingSignal, ArbitrageOpportunity, SignalType
from src.data.providers import MarketData, OrderBook
from src.core.logger import get_logger
from src.core.config import get_settings

logger = get_logger(__name__)


class CorrelationArbitrageStrategy(BaseStrategy):
    """Strategy for finding arbitrage opportunities between correlated markets."""
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        super().__init__("correlation_arbitrage", config)
        self.settings = get_settings()
        self.min_correlation = self.config.get("min_correlation", self.settings.correlation_min_threshold)
        self.max_correlation = self.config.get("max_correlation", self.settings.correlation_max_threshold)
        self.price_deviation_threshold = self.config.get("price_deviation_threshold", 0.05)
        self.min_volume = self.config.get("min_volume", 50.0)
        self.correlation_cache = {}
        self.price_history = {}
    
    async def analyze_markets(
        self,
        markets: Dict[str, List[MarketData]],
        order_books: Optional[Dict[str, OrderBook]] = None
    ) -> List[TradingSignal]:
        """Analyze markets for correlation arbitrage signals."""
        signals = []
        
        try:
            # Analyze each platform separately
            for platform, platform_markets in markets.items():
                platform_signals = await self._analyze_platform_correlations(platform, platform_markets)
                signals.extend(platform_signals)
        
        except Exception as e:
            logger.error(f"Error in correlation analysis: {e}")
            self.set_error(str(e))
        
        return signals
    
    async def find_opportunities(
        self,
        markets: Dict[str, List[MarketData]],
        order_books: Optional[Dict[str, OrderBook]] = None
    ) -> List[ArbitrageOpportunity]:
        """Find correlation arbitrage opportunities."""
        opportunities = []
        
        try:
            for platform, platform_markets in markets.items():
                platform_opportunities = await self._find_platform_opportunities(platform, platform_markets)
                opportunities.extend(platform_opportunities)
        
        except Exception as e:
            logger.error(f"Error finding correlation opportunities: {e}")
            self.set_error(str(e))
        
        return opportunities
    
    async def _analyze_platform_correlations(
        self,
        platform: str,
        markets: List[MarketData]
    ) -> List[TradingSignal]:
        """Analyze correlations within a single platform."""
        signals = []
        
        # Update price history
        self._update_price_history(platform, markets)
        
        # Find correlated market pairs
        correlated_pairs = self._find_correlated_pairs(platform, markets)
        
        for pair in correlated_pairs:
            market1, market2, correlation = pair
            
            # Calculate price signals based on correlation
            pair_signals = self._calculate_correlation_signals(platform, market1, market2, correlation)
            signals.extend(pair_signals)
        
        return signals
    
    async def _find_platform_opportunities(
        self,
        platform: str,
        markets: List[MarketData]
    ) -> List[ArbitrageOpportunity]:
        """Find opportunities within a platform."""
        opportunities = []
        
        correlated_pairs = self._find_correlated_pairs(platform, markets)
        
        for pair in correlated_pairs:
            market1, market2, correlation = pair
            opportunity = self._evaluate_correlation_opportunity(platform, market1, market2, correlation)
            
            if opportunity:
                opportunities.append(opportunity)
        
        return opportunities
    
    def _update_price_history(self, platform: str, markets: List[MarketData]) -> None:
        """Update price history for correlation analysis."""
        if platform not in self.price_history:
            self.price_history[platform] = {}
        
        current_time = datetime.utcnow()
        
        for market in markets:
            if market.yes_price is not None:
                market_key = market.market_id
                
                if market_key not in self.price_history[platform]:
                    self.price_history[platform][market_key] = []
                
                # Add current price point
                self.price_history[platform][market_key].append({
                    'timestamp': current_time,
                    'price': market.yes_price,
                    'volume': market.volume
                })
                
                # Keep only last 100 data points
                if len(self.price_history[platform][market_key]) > 100:
                    self.price_history[platform][market_key] = self.price_history[platform][market_key][-100:]
    
    def _find_correlated_pairs(
        self,
        platform: str,
        markets: List[MarketData]
    ) -> List[Tuple[MarketData, MarketData, float]]:
        """Find pairs of correlated markets."""
        correlated_pairs = []
        
        # Create combinations of markets
        for i, market1 in enumerate(markets):
            for market2 in markets[i+1:]:
                # Skip if either market doesn't have enough price history
                if not self._has_sufficient_history(platform, market1.market_id) or \
                   not self._has_sufficient_history(platform, market2.market_id):
                    continue
                
                # Calculate correlation
                correlation = self._calculate_correlation(platform, market1.market_id, market2.market_id)
                
                # Check if correlation is in our target range
                if self.min_correlation <= abs(correlation) <= self.max_correlation:
                    correlated_pairs.append((market1, market2, correlation))
        
        return correlated_pairs
    
    def _has_sufficient_history(self, platform: str, market_id: str) -> bool:
        """Check if market has sufficient price history."""
        if platform not in self.price_history or market_id not in self.price_history[platform]:
            return False
        
        return len(self.price_history[platform][market_id]) >= 10
    
    def _calculate_correlation(self, platform: str, market1_id: str, market2_id: str) -> float:
        """Calculate correlation between two markets."""
        cache_key = f"{platform}_{market1_id}_{market2_id}"
        
        # Check cache
        if cache_key in self.correlation_cache:
            cache_entry = self.correlation_cache[cache_key]
            # Use cached value if less than 5 minutes old
            if (datetime.utcnow() - cache_entry['timestamp']).seconds < 300:
                return cache_entry['correlation']
        
        # Get price histories
        history1 = self.price_history[platform].get(market1_id, [])
        history2 = self.price_history[platform].get(market2_id, [])
        
        if len(history1) < 10 or len(history2) < 10:
            return 0.0
        
        # Align timestamps and get price arrays
        prices1, prices2 = self._align_price_series(history1, history2)
        
        if len(prices1) < 5:
            return 0.0
        
        # Calculate correlation
        try:
            correlation = np.corrcoef(prices1, prices2)[0, 1]
            if np.isnan(correlation):
                correlation = 0.0
        except Exception:
            correlation = 0.0
        
        # Cache result
        self.correlation_cache[cache_key] = {
            'correlation': correlation,
            'timestamp': datetime.utcnow()
        }
        
        return correlation
    
    def _align_price_series(self, history1: List[Dict], history2: List[Dict]) -> Tuple[List[float], List[float]]:
        """Align two price series by timestamp."""
        # Convert to dictionaries for easier lookup
        dict1 = {h['timestamp']: h['price'] for h in history1}
        dict2 = {h['timestamp']: h['price'] for h in history2}
        
        # Find common timestamps (within 1 minute tolerance)
        aligned_prices1 = []
        aligned_prices2 = []
        
        for ts1, price1 in dict1.items():
            for ts2, price2 in dict2.items():
                if abs((ts1 - ts2).total_seconds()) <= 60:  # 1-minute tolerance
                    aligned_prices1.append(price1)
                    aligned_prices2.append(price2)
                    break
        
        return aligned_prices1, aligned_prices2
    
    def _calculate_correlation_signals(
        self,
        platform: str,
        market1: MarketData,
        market2: MarketData,
        correlation: float
    ) -> List[TradingSignal]:
        """Calculate trading signals based on correlation."""
        signals = []
        
        try:
            price1 = market1.yes_price
            price2 = market2.yes_price
            
            if not (price1 and price2):
                return signals
            
            # Calculate expected price based on correlation
            # This is a simplified model - in practice you'd use more sophisticated techniques
            expected_price2 = self._calculate_expected_price(platform, market1.market_id, market2.market_id, price1)
            
            if expected_price2 is None:
                return signals
            
            # Calculate price deviation
            price_deviation = abs(price2 - expected_price2) / expected_price2
            
            if price_deviation > self.price_deviation_threshold:
                confidence = min(1.0, price_deviation / self.price_deviation_threshold)
                
                # Determine signal direction
                if price2 > expected_price2:
                    # Market 2 is overpriced, sell it
                    signals.append(TradingSignal(
                        strategy_name=self.name,
                        market_id=market2.market_id,
                        platform=platform,
                        signal_type=SignalType.SELL,
                        outcome="yes",
                        confidence=confidence,
                        suggested_size=self._calculate_position_size(price_deviation, price2),
                        price_target=expected_price2,
                        metadata={
                            "correlation": correlation,
                            "expected_price": expected_price2,
                            "price_deviation": price_deviation,
                            "correlated_market": market1.market_id
                        }
                    ))
                    
                    # If correlation is positive, buy market 1
                    if correlation > 0:
                        signals.append(TradingSignal(
                            strategy_name=self.name,
                            market_id=market1.market_id,
                            platform=platform,
                            signal_type=SignalType.BUY,
                            outcome="yes",
                            confidence=confidence * 0.7,  # Lower confidence for the hedge
                            suggested_size=self._calculate_position_size(price_deviation, price1),
                            metadata={
                                "correlation": correlation,
                                "hedge_for": market2.market_id,
                                "arbitrage_type": "correlation"
                            }
                        ))
                
                else:
                    # Market 2 is underpriced, buy it
                    signals.append(TradingSignal(
                        strategy_name=self.name,
                        market_id=market2.market_id,
                        platform=platform,
                        signal_type=SignalType.BUY,
                        outcome="yes",
                        confidence=confidence,
                        suggested_size=self._calculate_position_size(price_deviation, price2),
                        price_target=expected_price2,
                        metadata={
                            "correlation": correlation,
                            "expected_price": expected_price2,
                            "price_deviation": price_deviation,
                            "correlated_market": market1.market_id
                        }
                    ))
                    
                    # If correlation is positive, sell market 1
                    if correlation > 0:
                        signals.append(TradingSignal(
                            strategy_name=self.name,
                            market_id=market1.market_id,
                            platform=platform,
                            signal_type=SignalType.SELL,
                            outcome="yes",
                            confidence=confidence * 0.7,
                            suggested_size=self._calculate_position_size(price_deviation, price1),
                            metadata={
                                "correlation": correlation,
                                "hedge_for": market2.market_id,
                                "arbitrage_type": "correlation"
                            }
                        ))
        
        except Exception as e:
            logger.error(f"Error calculating correlation signals: {e}")
        
        return signals
    
    def _calculate_expected_price(
        self,
        platform: str,
        market1_id: str,
        market2_id: str,
        current_price1: float
    ) -> Optional[float]:
        """Calculate expected price for market2 based on market1's price."""
        try:
            # Get historical relationship
            history1 = self.price_history[platform].get(market1_id, [])
            history2 = self.price_history[platform].get(market2_id, [])
            
            if len(history1) < 5 or len(history2) < 5:
                return None
            
            # Align price series
            prices1, prices2 = self._align_price_series(history1, history2)
            
            if len(prices1) < 5:
                return None
            
            # Simple linear regression to find relationship
            prices1_array = np.array(prices1)
            prices2_array = np.array(prices2)
            
            # Calculate linear relationship: price2 = a * price1 + b
            A = np.vstack([prices1_array, np.ones(len(prices1_array))]).T
            coefficients = np.linalg.lstsq(A, prices2_array, rcond=None)[0]
            
            a, b = coefficients
            expected_price = a * current_price1 + b
            
            # Ensure price is within reasonable bounds
            return max(0.01, min(0.99, expected_price))
        
        except Exception as e:
            logger.error(f"Error calculating expected price: {e}")
            return None
    
    def _evaluate_correlation_opportunity(
        self,
        platform: str,
        market1: MarketData,
        market2: MarketData,
        correlation: float
    ) -> Optional[ArbitrageOpportunity]:
        """Evaluate correlation arbitrage opportunity."""
        try:
            price1 = market1.yes_price
            price2 = market2.yes_price
            
            if not (price1 and price2):
                return None
            
            expected_price2 = self._calculate_expected_price(platform, market1.market_id, market2.market_id, price1)
            
            if expected_price2 is None:
                return None
            
            price_deviation = abs(price2 - expected_price2) / expected_price2
            
            if price_deviation < self.price_deviation_threshold:
                return None
            
            # Calculate potential profit
            expected_profit = abs(price2 - expected_price2)
            
            # Calculate required capital
            required_capital = max(price1, price2) * 1000  # Assume 1000 shares
            
            # Calculate confidence score
            confidence_score = min(1.0, (price_deviation / self.price_deviation_threshold) * abs(correlation))
            
            # Reduce confidence if volume is low
            min_volume = min(market1.volume, market2.volume)
            if min_volume < self.min_volume:
                confidence_score *= 0.5
            
            opportunity_id = f"corr_{platform}_{market1.market_id}_{market2.market_id}"
            
            return ArbitrageOpportunity(
                opportunity_id=opportunity_id,
                strategy_name=self.name,
                opportunity_type="correlation",
                markets=[
                    {
                        "platform": platform,
                        "market_id": market1.market_id,
                        "title": market1.title,
                        "yes_price": price1,
                        "volume": market1.volume
                    },
                    {
                        "platform": platform,
                        "market_id": market2.market_id,
                        "title": market2.title,
                        "yes_price": price2,
                        "expected_price": expected_price2,
                        "volume": market2.volume
                    }
                ],
                expected_profit=expected_profit,
                required_capital=required_capital,
                confidence_score=confidence_score,
                expiry_time=datetime.utcnow() + timedelta(minutes=10),
                metadata={
                    "correlation": correlation,
                    "price_deviation": price_deviation,
                    "expected_price": expected_price2,
                    "min_volume": min_volume
                }
            )
        
        except Exception as e:
            logger.error(f"Error evaluating correlation opportunity: {e}")
            return None
    
    def _calculate_position_size(self, price_deviation: float, price: float) -> float:
        """Calculate position size based on price deviation."""
        # Size position based on conviction (price deviation)
        base_size = 100.0  # Base position size
        deviation_multiplier = min(3.0, price_deviation / self.price_deviation_threshold)
        
        return base_size * deviation_multiplier