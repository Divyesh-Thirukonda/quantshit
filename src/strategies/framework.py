"""
Simple strategy development framework.

This module provides decorators and base classes to make strategy development
as easy as possible for new developers.
"""
from abc import ABC, abstractmethod
from typing import Dict, List, Any, Optional, Callable, Union, Tuple
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
import asyncio
import inspect
from functools import wraps

from src.strategies.base import TradingSignal, ArbitrageOpportunity, SignalType, BaseStrategy
from src.data.providers import MarketData, OrderBook
from src.core.logger import get_logger

logger = get_logger(__name__)


class StrategyDifficulty(Enum):
    """Strategy difficulty levels for developers."""
    BEGINNER = "beginner"       # Simple buy/sell signals
    INTERMEDIATE = "intermediate"  # Multi-market analysis
    ADVANCED = "advanced"       # Complex arbitrage and ML


@dataclass
class StrategyMetadata:
    """Metadata for strategies to help developers understand and categorize them."""
    name: str
    description: str
    difficulty: StrategyDifficulty
    author: str = "Anonymous"
    version: str = "1.0.0"
    tags: List[str] = field(default_factory=list)
    platforms: List[str] = field(default_factory=lambda: ["all"])
    min_capital: float = 100.0
    risk_level: str = "medium"  # low, medium, high
    expected_return: str = "5-15%"  # annual return estimate
    max_positions: int = 10
    created_date: datetime = field(default_factory=datetime.utcnow)


def strategy(
    name: str,
    description: str = "",
    difficulty: StrategyDifficulty = StrategyDifficulty.BEGINNER,
    platforms: List[str] = None,
    tags: List[str] = None,
    **metadata_kwargs
):
    """
    Decorator to register a function as a simple strategy.
    
    Args:
        name: Strategy name
        description: What the strategy does
        difficulty: Difficulty level for developers
        platforms: Supported platforms
        tags: Strategy tags for categorization
        **metadata_kwargs: Additional metadata
    
    Example:
        @strategy(
            name="Simple Price Reversal",
            description="Buy when price drops below 0.3, sell when above 0.7",
            difficulty=StrategyDifficulty.BEGINNER,
            tags=["reversal", "simple"]
        )
        def price_reversal_strategy(market: MarketData) -> Optional[TradingSignal]:
            if market.yes_price < 0.3:
                return TradingSignal(
                    strategy_name="price_reversal",
                    market_id=market.market_id,
                    platform=market.platform,
                    signal_type=SignalType.BUY,
                    outcome="yes",
                    confidence=0.7,
                    suggested_size=100.0
                )
            elif market.yes_price > 0.7:
                return TradingSignal(
                    strategy_name="price_reversal",
                    market_id=market.market_id,
                    platform=market.platform,
                    signal_type=SignalType.SELL,
                    outcome="yes",
                    confidence=0.7,
                    suggested_size=100.0
                )
            return None
    """
    def decorator(func):
        # Create metadata
        metadata = StrategyMetadata(
            name=name,
            description=description,
            difficulty=difficulty,
            platforms=platforms or ["all"],
            tags=tags or [],
            **metadata_kwargs
        )
        
        func._strategy_metadata = metadata
        func._is_simple_strategy = True
        
        @wraps(func)
        async def wrapper(*args, **kwargs):
            try:
                logger.debug(f"Running strategy: {name}")
                result = await func(*args, **kwargs) if asyncio.iscoroutinefunction(func) else func(*args, **kwargs)
                return result
            except Exception as e:
                logger.error(f"Error in strategy {name}: {e}")
                raise
        
        return wrapper
    return decorator


def market_analyzer(platforms: List[str] = None, min_confidence: float = 0.5):
    """
    Decorator for market analysis functions.
    
    Example:
        @market_analyzer(platforms=["kalshi"], min_confidence=0.6)
        def analyze_political_markets(markets: List[MarketData]) -> List[TradingSignal]:
            signals = []
            for market in markets:
                if "POTUS" in market.title and market.yes_price < 0.4:
                    signals.append(TradingSignal(...))
            return signals
    """
    def decorator(func):
        func._is_market_analyzer = True
        func._analyzer_platforms = platforms or ["all"]
        func._min_confidence = min_confidence
        
        @wraps(func)
        async def wrapper(*args, **kwargs):
            try:
                result = await func(*args, **kwargs) if asyncio.iscoroutinefunction(func) else func(*args, **kwargs)
                # Filter by confidence
                if isinstance(result, list):
                    result = [s for s in result if hasattr(s, 'confidence') and s.confidence >= min_confidence]
                return result
            except Exception as e:
                logger.error(f"Error in market analyzer {func.__name__}: {e}")
                raise
        
        return wrapper
    return decorator


def arbitrage_finder(min_spread: float = 0.02, platforms: List[str] = None):
    """
    Decorator for arbitrage opportunity finders.
    
    Example:
        @arbitrage_finder(min_spread=0.03, platforms=["kalshi", "polymarket"])
        def find_cross_platform_arb(market_groups: Dict[str, List[MarketData]]) -> List[ArbitrageOpportunity]:
            opportunities = []
            # Your arbitrage logic here
            return opportunities
    """
    def decorator(func):
        func._is_arbitrage_finder = True
        func._min_spread = min_spread
        func._arb_platforms = platforms or ["all"]
        
        @wraps(func)
        async def wrapper(*args, **kwargs):
            try:
                result = await func(*args, **kwargs) if asyncio.iscoroutinefunction(func) else func(*args, **kwargs)
                # Filter by spread
                if isinstance(result, list):
                    result = [opp for opp in result if hasattr(opp, 'expected_profit') and opp.expected_profit >= min_spread]
                return result
            except Exception as e:
                logger.error(f"Error in arbitrage finder {func.__name__}: {e}")
                raise
        
        return wrapper
    return decorator


class EasyStrategy(ABC):
    """
    Simplified base class for creating strategies.
    
    This class handles all the boilerplate and lets developers focus on the core logic.
    """
    
    def __init__(
        self,
        name: str,
        description: str = "",
        config: Optional[Dict[str, Any]] = None,
        difficulty: StrategyDifficulty = StrategyDifficulty.BEGINNER
    ):
        self.metadata = StrategyMetadata(
            name=name,
            description=description,
            difficulty=difficulty
        )
        self.config = config or {}
        self.is_active = False
        self.performance_stats = {
            'total_signals': 0,
            'winning_signals': 0,
            'total_profit': 0.0,
            'last_signal': None
        }
    
    @abstractmethod
    def should_buy(self, market: MarketData) -> bool:
        """Return True if strategy should buy this market."""
        pass
    
    @abstractmethod
    def should_sell(self, market: MarketData) -> bool:
        """Return True if strategy should sell this market."""
        pass
    
    def get_confidence(self, market: MarketData) -> float:
        """Return confidence level (0.0 to 1.0). Override for custom logic."""
        return 0.7
    
    def get_position_size(self, market: MarketData) -> float:
        """Return position size. Override for custom logic."""
        return self.config.get('default_size', 100.0)
    
    def get_outcome(self, market: MarketData, signal_type: SignalType) -> str:
        """Return 'yes' or 'no'. Override for custom logic."""
        return 'yes'
    
    async def analyze_market(self, market: MarketData) -> Optional[TradingSignal]:
        """Analyze a single market and return signal if any."""
        try:
            signal_type = None
            
            if self.should_buy(market):
                signal_type = SignalType.BUY
            elif self.should_sell(market):
                signal_type = SignalType.SELL
            
            if signal_type:
                signal = TradingSignal(
                    strategy_name=self.metadata.name,
                    market_id=market.market_id,
                    platform=market.platform,
                    signal_type=signal_type,
                    outcome=self.get_outcome(market, signal_type),
                    confidence=self.get_confidence(market),
                    suggested_size=self.get_position_size(market)
                )
                
                self.performance_stats['total_signals'] += 1
                self.performance_stats['last_signal'] = datetime.utcnow()
                
                return signal
        
        except Exception as e:
            logger.error(f"Error analyzing market in {self.metadata.name}: {e}")
        
        return None
    
    async def analyze_markets(self, markets: List[MarketData]) -> List[TradingSignal]:
        """Analyze multiple markets."""
        signals = []
        
        for market in markets:
            signal = await self.analyze_market(market)
            if signal:
                signals.append(signal)
        
        return signals
    
    def get_stats(self) -> Dict[str, Any]:
        """Get performance statistics."""
        stats = self.performance_stats.copy()
        if stats['total_signals'] > 0:
            stats['win_rate'] = stats['winning_signals'] / stats['total_signals']
        else:
            stats['win_rate'] = 0.0
        return stats


class StrategyTester:
    """
    Simple strategy testing framework.
    
    Example:
        tester = StrategyTester()
        results = await tester.test_strategy(my_strategy, sample_markets)
        print(f"Generated {len(results.signals)} signals")
    """
    
    @dataclass
    class TestResults:
        strategy_name: str
        signals: List[TradingSignal]
        opportunities: List[ArbitrageOpportunity]
        execution_time: float
        error_count: int
        test_markets: int
    
    async def test_strategy(
        self,
        strategy: Union[EasyStrategy, Callable],
        test_markets: List[MarketData],
        test_order_books: Optional[Dict[str, OrderBook]] = None
    ) -> TestResults:
        """Test a strategy with sample data."""
        start_time = datetime.utcnow()
        signals = []
        opportunities = []
        error_count = 0
        
        try:
            if isinstance(strategy, EasyStrategy):
                signals = await strategy.analyze_markets(test_markets)
                strategy_name = strategy.metadata.name
            elif hasattr(strategy, '_is_simple_strategy'):
                # Simple strategy function
                for market in test_markets:
                    try:
                        signal = await strategy(market) if asyncio.iscoroutinefunction(strategy) else strategy(market)
                        if signal:
                            signals.append(signal)
                    except Exception as e:
                        error_count += 1
                        logger.warning(f"Error testing market {market.market_id}: {e}")
                strategy_name = strategy._strategy_metadata.name
            else:
                # Regular strategy object
                if hasattr(strategy, 'analyze_markets'):
                    signals = await strategy.analyze_markets({'test': test_markets}, test_order_books)
                if hasattr(strategy, 'find_opportunities'):
                    opportunities = await strategy.find_opportunities({'test': test_markets}, test_order_books)
                strategy_name = getattr(strategy, 'name', strategy.__class__.__name__)
        
        except Exception as e:
            logger.error(f"Error testing strategy: {e}")
            error_count += 1
        
        execution_time = (datetime.utcnow() - start_time).total_seconds()
        
        return self.TestResults(
            strategy_name=strategy_name,
            signals=signals,
            opportunities=opportunities,
            execution_time=execution_time,
            error_count=error_count,
            test_markets=len(test_markets)
        )
    
    def generate_test_markets(self, count: int = 10, platform: str = "test") -> List[MarketData]:
        """Generate sample markets for testing."""
        markets = []
        
        for i in range(count):
            price = 0.2 + (i * 0.6 / count)  # Prices from 0.2 to 0.8
            
            markets.append(MarketData(
                platform=platform,
                market_id=f"TEST_{i:03d}",
                title=f"Test Market {i}",
                category="test",
                description=f"Test market for strategy development #{i}",
                yes_price=price,
                no_price=1.0 - price,
                volume=100.0 + (i * 50),
                open_interest=200.0 + (i * 100),
                close_date=datetime.utcnow() + timedelta(days=30),
                status=MarketStatus.ACTIVE
            ))
        
        return markets


class StrategyRegistry:
    """Registry for strategies with categorization and discovery."""
    
    def __init__(self):
        self.strategies: Dict[str, Any] = {}
        self.metadata: Dict[str, StrategyMetadata] = {}
        self.categories: Dict[StrategyDifficulty, List[str]] = {
            StrategyDifficulty.BEGINNER: [],
            StrategyDifficulty.INTERMEDIATE: [],
            StrategyDifficulty.ADVANCED: []
        }
    
    def register(self, strategy: Any):
        """Register a strategy."""
        if hasattr(strategy, '_strategy_metadata'):
            # Simple strategy function
            metadata = strategy._strategy_metadata
            name = metadata.name
        elif hasattr(strategy, 'metadata'):
            # EasyStrategy instance
            metadata = strategy.metadata
            name = metadata.name
        else:
            # Regular strategy
            name = getattr(strategy, 'name', strategy.__class__.__name__)
            metadata = StrategyMetadata(
                name=name,
                description="No description provided",
                difficulty=StrategyDifficulty.INTERMEDIATE
            )
        
        self.strategies[name] = strategy
        self.metadata[name] = metadata
        self.categories[metadata.difficulty].append(name)
        
        logger.info(f"Registered strategy: {name} ({metadata.difficulty.value})")
    
    def get_by_difficulty(self, difficulty: StrategyDifficulty) -> List[Tuple[str, Any]]:
        """Get strategies by difficulty level."""
        return [(name, self.strategies[name]) for name in self.categories[difficulty]]
    
    def get_by_tags(self, tags: List[str]) -> List[Tuple[str, Any]]:
        """Get strategies by tags."""
        results = []
        for name, metadata in self.metadata.items():
            if any(tag in metadata.tags for tag in tags):
                results.append((name, self.strategies[name]))
        return results
    
    def get_beginner_strategies(self) -> List[Tuple[str, Any]]:
        """Get beginner-friendly strategies."""
        return self.get_by_difficulty(StrategyDifficulty.BEGINNER)
    
    def list_all(self) -> Dict[str, StrategyMetadata]:
        """List all strategies with metadata."""
        return self.metadata.copy()


# Global registry
strategy_registry = StrategyRegistry()


def auto_discover_strategies(module_path: str):
    """
    Automatically discover and register strategies in a module.
    
    Args:
        module_path: Python module path (e.g., "src.strategies.custom")
    """
    import importlib
    
    try:
        module = importlib.import_module(module_path)
        
        for name in dir(module):
            obj = getattr(module, name)
            
            # Register simple strategies
            if hasattr(obj, '_is_simple_strategy'):
                strategy_registry.register(obj)
            
            # Register EasyStrategy classes
            if isinstance(obj, type) and issubclass(obj, EasyStrategy) and obj != EasyStrategy:
                try:
                    instance = obj()
                    strategy_registry.register(instance)
                except Exception as e:
                    logger.warning(f"Could not instantiate strategy {name}: {e}")
        
        logger.info(f"Auto-discovered strategies from {module_path}")
        
    except Exception as e:
        logger.error(f"Failed to auto-discover from {module_path}: {e}")


# Example strategies for documentation
class ExampleSimpleStrategy(EasyStrategy):
    """Example of a simple strategy for documentation."""
    
    def __init__(self):
        super().__init__(
            name="Simple Price Reversal",
            description="Buy low, sell high strategy",
            difficulty=StrategyDifficulty.BEGINNER
        )
        self.buy_threshold = 0.3
        self.sell_threshold = 0.7
    
    def should_buy(self, market: MarketData) -> bool:
        return market.yes_price is not None and market.yes_price < self.buy_threshold
    
    def should_sell(self, market: MarketData) -> bool:
        return market.yes_price is not None and market.yes_price > self.sell_threshold


@strategy(
    name="Volume Spike",
    description="Buy when volume spikes above average",
    difficulty=StrategyDifficulty.BEGINNER,
    tags=["volume", "momentum"]
)
def volume_spike_strategy(market: MarketData) -> Optional[TradingSignal]:
    """Example simple strategy using decorator."""
    if market.volume > 1000:  # Simple volume threshold
        return TradingSignal(
            strategy_name="volume_spike",
            market_id=market.market_id,
            platform=market.platform,
            signal_type=SignalType.BUY,
            outcome="yes",
            confidence=0.6,
            suggested_size=100.0
        )
    return None