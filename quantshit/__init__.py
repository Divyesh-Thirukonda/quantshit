"""
quantshit - Trading bot for prediction markets with backtesting engine
"""

__version__ = "0.1.0"

from .backtesting.engine import Backtester
from .backtesting.portfolio import Portfolio
from .backtesting.models import Market, Position, Order, Trade
from .strategies.base import Strategy

__all__ = [
    "Backtester",
    "Portfolio",
    "Market",
    "Position",
    "Order",
    "Trade",
    "Strategy",
]
