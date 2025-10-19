
from typing import List, Dict, Tuple, Optional

class BaseStrategy:
    """Base class for trading strategies"""
    def __init__(self, name: str):
        self.name = name
    def find_opportunities(self, markets_by_platform: Dict[str, List[Dict]]) -> List[Dict]:
        """Find arbitrage opportunities across platforms"""
        raise NotImplementedError

from .arbitrage import ArbitrageStrategy

# Registry for strategies
STRATEGIES = {
    'arbitrage': ArbitrageStrategy
}

def get_strategy(strategy_name: str, **kwargs) -> BaseStrategy:
    """Factory function to get strategy instance"""
    if strategy_name not in STRATEGIES:
        raise ValueError(f"Unsupported strategy: {strategy_name}")
    return STRATEGIES[strategy_name](**kwargs)
