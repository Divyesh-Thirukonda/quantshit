"""
QuantShit - Quantitative Trading Library

A comprehensive library for quantitative trading strategies including:
- Options market-making and volatility capture
- Momentum trading and trend following
"""

__version__ = '0.1.0'

from . import options
from . import momentum

__all__ = ['options', 'momentum']
