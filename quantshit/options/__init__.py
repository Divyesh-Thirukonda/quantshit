"""
Options Trading Module

This module provides functionality for options market-making and volatility capture.
"""

from .black_scholes import BlackScholes
from .volatility import (
    historical_volatility,
    rolling_historical_volatility,
    implied_volatility,
    volatility_surface,
    volatility_smile,
    realized_volatility
)
from .risk_management import (
    PortfolioRiskManager,
    calculate_var,
    calculate_cvar,
    position_size_kelly,
    sharpe_ratio
)
from .market_data import (
    OrderBook,
    MarketDataFeed,
    OptionChainData
)

__all__ = [
    'BlackScholes',
    'historical_volatility',
    'rolling_historical_volatility',
    'implied_volatility',
    'volatility_surface',
    'volatility_smile',
    'realized_volatility',
    'PortfolioRiskManager',
    'calculate_var',
    'calculate_cvar',
    'position_size_kelly',
    'sharpe_ratio',
    'OrderBook',
    'MarketDataFeed',
    'OptionChainData'
]
