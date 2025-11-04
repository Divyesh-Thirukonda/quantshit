"""
Trading strategies - different approaches to arbitrage.
Strategy pattern for extensibility - add new strategies by extending base.
"""

from .base import BaseStrategy
from .simple_arb import SimpleArbitrageStrategy
from .config import StrategyConfig, SimpleArbitrageConfig

__all__ = [
    'BaseStrategy',
    'SimpleArbitrageStrategy',
    'StrategyConfig',
    'SimpleArbitrageConfig'
]
