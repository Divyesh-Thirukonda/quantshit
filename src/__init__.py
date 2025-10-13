"""
Arbitrage Trading System

A comprehensive platform-agnostic arbitrage system for prediction markets.
"""

__version__ = "0.1.0"
__author__ = "Arbitrage Team"

from src.core.config import get_settings
from src.core.logger import get_logger

# Initialize logging
logger = get_logger(__name__)

# Load configuration
settings = get_settings()

logger.info(f"Arbitrage System v{__version__} initialized")