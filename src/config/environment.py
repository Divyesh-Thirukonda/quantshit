"""
Environment configuration for test (paper trading) vs production (real money)
"""

import os
from enum import Enum
from typing import Dict, Any


class TradingMode(Enum):
    PAPER = "paper"
    LIVE = "live"


class Environment:
    """Environment configuration manager"""
    
    def __init__(self):
        # Get environment from env var, default to paper trading
        self.mode = TradingMode(os.getenv('TRADING_MODE', 'paper'))
        self.environment = os.getenv('ENVIRONMENT', 'development')
        
    def is_paper_trading(self) -> bool:
        """Check if we're in paper trading mode"""
        return self.mode == TradingMode.PAPER
    
    def is_live_trading(self) -> bool:
        """Check if we're in live trading mode"""
        return self.mode == TradingMode.LIVE
    
    def get_api_config(self) -> Dict[str, Any]:
        """Get API configuration based on environment"""
        if self.is_paper_trading():
            return {
                'use_mock_apis': True,
                'initial_balance_per_platform': 10000,  # $10k paper money per platform
                'max_position_size': 1000,
                'max_total_exposure': 5000,
                'enable_real_orders': False
            }
        else:
            return {
                'use_mock_apis': False,
                'initial_balance_per_platform': 0,  # Must load from real APIs
                'max_position_size': float(os.getenv('MAX_POSITION_SIZE', '500')),
                'max_total_exposure': float(os.getenv('MAX_TOTAL_EXPOSURE', '2000')),
                'enable_real_orders': True
            }
    
    def get_platform_credentials(self) -> Dict[str, str]:
        """Get platform API credentials"""
        if self.is_paper_trading():
            # Paper trading - use dummy credentials
            return {
                'kalshi': 'paper_trading_key',
                'polymarket': 'paper_trading_key'
            }
        else:
            # Live trading - use real credentials from environment
            return {
                'kalshi': os.getenv('KALSHI_API_KEY', ''),
                'polymarket': os.getenv('POLYMARKET_API_KEY', ''),
                'kalshi_private_key': os.getenv('KALSHI_PRIVATE_KEY', ''),
                'polymarket_private_key': os.getenv('POLYMARKET_PRIVATE_KEY', '')
            }
    
    def get_risk_limits(self) -> Dict[str, Any]:
        """Get risk management limits"""
        if self.is_paper_trading():
            return {
                'max_daily_trades': 50,  # More lenient for testing
                'max_loss_per_day': 1000,  # Paper money
                'min_profit_threshold': 0.01  # Lower threshold for testing
            }
        else:
            return {
                'max_daily_trades': int(os.getenv('MAX_DAILY_TRADES', '10')),
                'max_loss_per_day': float(os.getenv('MAX_LOSS_PER_DAY', '200')),
                'min_profit_threshold': float(os.getenv('MIN_PROFIT_THRESHOLD', '0.05'))
            }
    
    def __str__(self):
        return f"Environment(mode={self.mode.value}, env={self.environment})"


# Global environment instance
env = Environment()