"""
Base strategy class for prediction market trading
"""

from abc import ABC, abstractmethod
from typing import List, Dict, Optional
from datetime import datetime

from ..backtesting.models import Market, Order, Position
from ..backtesting.portfolio import Portfolio


class Strategy(ABC):
    """
    Abstract base class for trading strategies
    
    Subclasses must implement the generate_signals method to define
    their trading logic.
    """
    
    def __init__(self, name: str = "BaseStrategy"):
        """
        Initialize strategy
        
        Args:
            name: Strategy name
        """
        self.name = name
        self.params = {}
    
    @abstractmethod
    def generate_signals(
        self, 
        markets: Dict[str, Market], 
        portfolio: Portfolio,
        timestamp: datetime
    ) -> List[Order]:
        """
        Generate trading signals based on current market state
        
        Args:
            markets: Dictionary of current market states
            portfolio: Current portfolio state
            timestamp: Current timestamp
            
        Returns:
            List of orders to execute
        """
        pass
    
    def on_trade_executed(self, trade):
        """
        Callback when a trade is executed
        
        Args:
            trade: Executed trade
        """
        pass
    
    def on_market_resolved(self, market: Market):
        """
        Callback when a market is resolved
        
        Args:
            market: Resolved market
        """
        pass
    
    def set_params(self, **kwargs):
        """
        Set strategy parameters
        
        Args:
            **kwargs: Parameter key-value pairs
        """
        self.params.update(kwargs)
    
    def get_params(self) -> Dict:
        """Get strategy parameters"""
        return self.params.copy()
