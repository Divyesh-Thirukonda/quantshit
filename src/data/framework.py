"""
Developer-friendly data acquisition framework.

This module provides simple decorators and base classes to make it easy
for developers to add new data sources and providers.
"""
from abc import ABC, abstractmethod
from typing import Dict, List, Any, Optional, Callable, Union
from dataclasses import dataclass
from datetime import datetime, timedelta
import asyncio
import inspect
from functools import wraps

from src.data.providers import MarketData, OrderBook, MarketStatus
from src.core.logger import get_logger

logger = get_logger(__name__)


def data_source(name: str, platforms: List[str] = None, refresh_interval: int = 60):
    """
    Decorator to register a function as a data source.
    
    Args:
        name: Unique name for the data source
        platforms: List of platforms this source supports (default: all)
        refresh_interval: How often to refresh data in seconds
    
    Example:
        @data_source("market_prices", platforms=["kalshi"], refresh_interval=30)
        async def get_kalshi_prices(market_ids: List[str]) -> List[MarketData]:
            # Your implementation here
            pass
    """
    def decorator(func):
        func._data_source_name = name
        func._data_source_platforms = platforms or ["all"]
        func._data_source_refresh = refresh_interval
        
        @wraps(func)
        async def wrapper(*args, **kwargs):
            try:
                logger.debug(f"Fetching data from source: {name}")
                result = await func(*args, **kwargs)
                logger.debug(f"Successfully fetched {len(result) if hasattr(result, '__len__') else 'data'} items from {name}")
                return result
            except Exception as e:
                logger.error(f"Error in data source {name}: {e}")
                raise
        
        wrapper._is_data_source = True
        return wrapper
    return decorator


def real_time_feed(platforms: List[str] = None, buffer_size: int = 1000):
    """
    Decorator for real-time data feeds.
    
    Args:
        platforms: List of platforms this feed supports
        buffer_size: Number of updates to buffer
    
    Example:
        @real_time_feed(platforms=["kalshi"])
        async def kalshi_price_stream():
            # Yield real-time price updates
            while True:
                yield market_data_update
    """
    def decorator(func):
        func._real_time_feed = True
        func._feed_platforms = platforms or ["all"]
        func._feed_buffer_size = buffer_size
        
        @wraps(func)
        async def wrapper(*args, **kwargs):
            try:
                logger.info(f"Starting real-time feed: {func.__name__}")
                async for data in func(*args, **kwargs):
                    yield data
            except Exception as e:
                logger.error(f"Error in real-time feed {func.__name__}: {e}")
                raise
        
        return wrapper
    return decorator


class EasyDataProvider(ABC):
    """
    Simplified base class for creating data providers.
    
    Inherit from this class and implement the required methods.
    The framework handles registration, error handling, and caching automatically.
    """
    
    def __init__(self, name: str, config: Optional[Dict[str, Any]] = None):
        self.name = name
        self.config = config or {}
        self.is_connected = False
        self._cache = {}
        self._last_update = {}
    
    @abstractmethod
    async def connect(self) -> bool:
        """Connect to the data source. Return True if successful."""
        pass
    
    @abstractmethod
    async def get_markets(self, symbols: Optional[List[str]] = None) -> List[MarketData]:
        """Get current market data."""
        pass
    
    async def get_order_book(self, market_id: str) -> Optional[OrderBook]:
        """Get order book data. Override if supported."""
        return None
    
    async def get_historical_data(
        self, 
        market_id: str, 
        start_date: datetime, 
        end_date: datetime
    ) -> List[MarketData]:
        """Get historical data. Override if supported."""
        return []
    
    async def start_real_time_feed(self) -> None:
        """Start real-time data feed. Override if supported."""
        pass
    
    def cache_data(self, key: str, data: Any, ttl_seconds: int = 300) -> None:
        """Cache data with TTL."""
        self._cache[key] = {
            'data': data,
            'expires': datetime.utcnow() + timedelta(seconds=ttl_seconds)
        }
    
    def get_cached_data(self, key: str) -> Optional[Any]:
        """Get cached data if not expired."""
        if key in self._cache:
            if datetime.utcnow() < self._cache[key]['expires']:
                return self._cache[key]['data']
            else:
                del self._cache[key]
        return None


@dataclass
class DataRequest:
    """Standardized data request."""
    provider: str
    data_type: str  # 'markets', 'orderbook', 'historical'
    parameters: Dict[str, Any]
    priority: int = 1  # 1=high, 2=medium, 3=low
    max_age_seconds: int = 60  # Max age of cached data to accept


class DataRegistry:
    """Registry for data sources and providers."""
    
    def __init__(self):
        self.providers: Dict[str, EasyDataProvider] = {}
        self.data_sources: Dict[str, Callable] = {}
        self.real_time_feeds: Dict[str, Callable] = {}
    
    def register_provider(self, provider: EasyDataProvider):
        """Register a data provider."""
        self.providers[provider.name] = provider
        logger.info(f"Registered data provider: {provider.name}")
    
    def register_data_source(self, func: Callable):
        """Register a data source function."""
        if hasattr(func, '_is_data_source'):
            name = func._data_source_name
            self.data_sources[name] = func
            logger.info(f"Registered data source: {name}")
    
    def register_real_time_feed(self, func: Callable):
        """Register a real-time feed."""
        if hasattr(func, '_real_time_feed'):
            name = func.__name__
            self.real_time_feeds[name] = func
            logger.info(f"Registered real-time feed: {name}")
    
    def get_provider(self, name: str) -> Optional[EasyDataProvider]:
        """Get a provider by name."""
        return self.providers.get(name)
    
    def list_providers(self) -> List[str]:
        """List all registered providers."""
        return list(self.providers.keys())
    
    def list_data_sources(self) -> List[str]:
        """List all registered data sources."""
        return list(self.data_sources.keys())


# Global registry instance
data_registry = DataRegistry()


class QuickDataFetcher:
    """
    Simple interface for fetching data without dealing with providers directly.
    
    Example:
        fetcher = QuickDataFetcher()
        markets = await fetcher.get_markets("kalshi", ["POTUS", "HOUSE"])
        prices = await fetcher.get_prices(["market_1", "market_2"])
    """
    
    def __init__(self):
        self.registry = data_registry
    
    async def get_markets(
        self, 
        platform: str = "all", 
        symbols: Optional[List[str]] = None
    ) -> List[MarketData]:
        """Get markets from specified platform or all platforms."""
        markets = []
        
        if platform == "all":
            for provider in self.registry.providers.values():
                try:
                    if not provider.is_connected:
                        await provider.connect()
                    platform_markets = await provider.get_markets(symbols)
                    markets.extend(platform_markets)
                except Exception as e:
                    logger.warning(f"Failed to get markets from {provider.name}: {e}")
        else:
            provider = self.registry.get_provider(platform)
            if provider:
                if not provider.is_connected:
                    await provider.connect()
                markets = await provider.get_markets(symbols)
        
        return markets
    
    async def get_prices(self, market_ids: List[str]) -> Dict[str, float]:
        """Get current prices for market IDs."""
        markets = await self.get_markets()
        prices = {}
        
        for market in markets:
            if market.market_id in market_ids:
                prices[market.market_id] = market.yes_price or 0.0
        
        return prices
    
    async def get_order_book(self, market_id: str, platform: str = None) -> Optional[OrderBook]:
        """Get order book for a specific market."""
        if platform:
            provider = self.registry.get_provider(platform)
            if provider and provider.is_connected:
                return await provider.get_order_book(market_id)
        else:
            # Try all providers
            for provider in self.registry.providers.values():
                if provider.is_connected:
                    try:
                        book = await provider.get_order_book(market_id)
                        if book:
                            return book
                    except Exception:
                        continue
        return None


def auto_discover_data_sources(module_path: str):
    """
    Automatically discover and register data sources in a module.
    
    Args:
        module_path: Python module path (e.g., "src.data.custom_sources")
    """
    import importlib
    
    try:
        module = importlib.import_module(module_path)
        
        for name in dir(module):
            obj = getattr(module, name)
            
            # Register data sources
            if hasattr(obj, '_is_data_source'):
                data_registry.register_data_source(obj)
            
            # Register real-time feeds
            if hasattr(obj, '_real_time_feed'):
                data_registry.register_real_time_feed(obj)
            
            # Register providers
            if isinstance(obj, type) and issubclass(obj, EasyDataProvider) and obj != EasyDataProvider:
                try:
                    instance = obj()
                    data_registry.register_provider(instance)
                except Exception as e:
                    logger.warning(f"Could not instantiate provider {name}: {e}")
        
        logger.info(f"Auto-discovered data sources from {module_path}")
        
    except Exception as e:
        logger.error(f"Failed to auto-discover from {module_path}: {e}")


# Example usage functions for documentation
async def example_simple_data_source():
    """Example of how to create a simple data source."""
    
    @data_source("example_prices", platforms=["demo"], refresh_interval=30)
    async def get_demo_prices(symbols: List[str]) -> List[MarketData]:
        """Fetch demo market prices."""
        markets = []
        for symbol in symbols:
            markets.append(MarketData(
                platform="demo",
                market_id=symbol,
                title=f"Demo Market {symbol}",
                yes_price=0.5,
                no_price=0.5,
                volume=1000.0
            ))
        return markets
    
    # Register the source
    data_registry.register_data_source(get_demo_prices)
    
    # Use it
    fetcher = QuickDataFetcher()
    markets = await fetcher.get_markets("demo", ["TEST1", "TEST2"])
    return markets


class ExampleProvider(EasyDataProvider):
    """Example of how to create a simple provider."""
    
    def __init__(self):
        super().__init__("example", {"api_key": "your_key_here"})
    
    async def connect(self) -> bool:
        """Connect to the example API."""
        # Your connection logic here
        self.is_connected = True
        return True
    
    async def get_markets(self, symbols: Optional[List[str]] = None) -> List[MarketData]:
        """Get markets from the example API."""
        # Check cache first
        cache_key = f"markets_{symbols}"
        cached = self.get_cached_data(cache_key)
        if cached:
            return cached
        
        # Fetch fresh data
        markets = []
        # Your API calls here...
        
        # Cache the results
        self.cache_data(cache_key, markets, ttl_seconds=60)
        return markets