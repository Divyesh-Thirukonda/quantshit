"""
Base classes for market data providers.
"""
from abc import ABC, abstractmethod
from typing import List, Dict, Any, Optional
from datetime import datetime
from dataclasses import dataclass
from enum import Enum


class MarketStatus(Enum):
    """Market status enumeration."""
    ACTIVE = "active"
    CLOSED = "closed"
    SETTLED = "settled"
    SUSPENDED = "suspended"


@dataclass
class MarketData:
    """Market data structure."""
    platform: str
    market_id: str
    title: str
    category: Optional[str] = None
    description: Optional[str] = None
    yes_price: Optional[float] = None
    no_price: Optional[float] = None
    volume: float = 0.0
    open_interest: float = 0.0
    close_date: Optional[datetime] = None
    status: MarketStatus = MarketStatus.ACTIVE
    last_updated: datetime = None
    
    def __post_init__(self):
        if self.last_updated is None:
            self.last_updated = datetime.utcnow()


@dataclass
class OrderBookEntry:
    """Order book entry."""
    price: float
    quantity: float
    side: str  # 'bid' or 'ask'


@dataclass
class OrderBook:
    """Order book data."""
    market_id: str
    platform: str
    bids: List[OrderBookEntry]
    asks: List[OrderBookEntry]
    timestamp: datetime
    
    def best_bid(self) -> Optional[float]:
        """Get best bid price."""
        return max([bid.price for bid in self.bids]) if self.bids else None
    
    def best_ask(self) -> Optional[float]:
        """Get best ask price."""
        return min([ask.price for ask in self.asks]) if self.asks else None
    
    def spread(self) -> Optional[float]:
        """Calculate bid-ask spread."""
        best_bid = self.best_bid()
        best_ask = self.best_ask()
        if best_bid and best_ask:
            return best_ask - best_bid
        return None


class BaseDataProvider(ABC):
    """Base class for data providers."""
    
    def __init__(self, platform_name: str):
        self.platform_name = platform_name
        self._is_connected = False
    
    @abstractmethod
    async def connect(self) -> bool:
        """Connect to the data source."""
        pass
    
    @abstractmethod
    async def disconnect(self) -> None:
        """Disconnect from the data source."""
        pass
    
    @abstractmethod
    async def get_markets(self, category: Optional[str] = None) -> List[MarketData]:
        """Get all available markets."""
        pass
    
    @abstractmethod
    async def get_market_data(self, market_id: str) -> Optional[MarketData]:
        """Get data for a specific market."""
        pass
    
    @abstractmethod
    async def get_order_book(self, market_id: str) -> Optional[OrderBook]:
        """Get order book for a market."""
        pass
    
    @abstractmethod
    async def subscribe_to_market(self, market_id: str, callback) -> bool:
        """Subscribe to real-time market updates."""
        pass
    
    @abstractmethod
    async def unsubscribe_from_market(self, market_id: str) -> bool:
        """Unsubscribe from market updates."""
        pass
    
    @property
    def is_connected(self) -> bool:
        """Check if connected to data source."""
        return self._is_connected
    
    async def health_check(self) -> bool:
        """Perform health check."""
        return self._is_connected


class DataAggregator:
    """Aggregates data from multiple providers."""
    
    def __init__(self):
        self.providers: Dict[str, BaseDataProvider] = {}
        self.subscriptions: Dict[str, List[str]] = {}  # market_id -> list of platforms
    
    def add_provider(self, provider: BaseDataProvider) -> None:
        """Add a data provider."""
        self.providers[provider.platform_name] = provider
    
    def remove_provider(self, platform_name: str) -> None:
        """Remove a data provider."""
        if platform_name in self.providers:
            del self.providers[platform_name]
    
    async def connect_all(self) -> Dict[str, bool]:
        """Connect to all providers."""
        results = {}
        for platform, provider in self.providers.items():
            try:
                results[platform] = await provider.connect()
            except Exception as e:
                results[platform] = False
                print(f"Failed to connect to {platform}: {e}")
        return results
    
    async def disconnect_all(self) -> None:
        """Disconnect from all providers."""
        for provider in self.providers.values():
            try:
                await provider.disconnect()
            except Exception as e:
                print(f"Error disconnecting: {e}")
    
    async def get_all_markets(self, category: Optional[str] = None) -> Dict[str, List[MarketData]]:
        """Get markets from all providers."""
        all_markets = {}
        for platform, provider in self.providers.items():
            if provider.is_connected:
                try:
                    markets = await provider.get_markets(category)
                    all_markets[platform] = markets
                except Exception as e:
                    print(f"Error getting markets from {platform}: {e}")
                    all_markets[platform] = []
        return all_markets
    
    async def find_cross_platform_markets(self, similarity_threshold: float = 0.8) -> List[Dict[str, Any]]:
        """Find similar markets across platforms."""
        all_markets = await self.get_all_markets()
        cross_platform_matches = []
        
        # Simple title-based matching (can be enhanced with NLP)
        platforms = list(all_markets.keys())
        for i, platform1 in enumerate(platforms):
            for platform2 in platforms[i+1:]:
                markets1 = all_markets[platform1]
                markets2 = all_markets[platform2]
                
                for market1 in markets1:
                    for market2 in markets2:
                        # Simple similarity check
                        similarity = self._calculate_similarity(market1.title, market2.title)
                        if similarity >= similarity_threshold:
                            cross_platform_matches.append({
                                'platform1': platform1,
                                'market1': market1,
                                'platform2': platform2,
                                'market2': market2,
                                'similarity': similarity
                            })
        
        return cross_platform_matches
    
    def _calculate_similarity(self, text1: str, text2: str) -> float:
        """Calculate similarity between two texts."""
        # Simple Jaccard similarity
        words1 = set(text1.lower().split())
        words2 = set(text2.lower().split())
        intersection = words1.intersection(words2)
        union = words1.union(words2)
        return len(intersection) / len(union) if union else 0.0