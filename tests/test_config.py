"""Tests for configuration management."""

import sys
from pathlib import Path

# Add the project root to the Python path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

import pytest
import os
from unittest.mock import patch

from config.settings import Config, TradingConfig, PlatformCredentials
from src.core import Platform, RiskLevel


class TestConfig:
    """Test configuration management."""
    
    def test_default_config(self):
        """Test default configuration values."""
        config = Config()
        
        assert config.environment == "development"
        assert config.debug is True
        assert isinstance(config.trading, TradingConfig)
    
    def test_trading_config_defaults(self):
        """Test trading configuration defaults."""
        trading = TradingConfig()
        
        assert trading.max_position_size == 1000.0
        assert trading.max_total_exposure == 10000.0
        assert trading.min_profit_threshold == 0.02
        assert trading.paper_trading is True
        assert trading.default_risk_level == RiskLevel.MEDIUM
    
    @patch.dict(os.environ, {
        'KALSHI_API_KEY': 'test_kalshi_key',
        'KALSHI_API_SECRET': 'test_kalshi_secret',
        'POLYMARKET_API_KEY': 'test_poly_key'
    })
    def test_platform_credentials_from_env(self):
        """Test loading platform credentials from environment."""
        config = Config()
        
        kalshi_config = config.get_platform_config(Platform.KALSHI)
        assert kalshi_config is not None
        assert kalshi_config.api_key == 'test_kalshi_key'
        assert kalshi_config.api_secret == 'test_kalshi_secret'
        
        poly_config = config.get_platform_config(Platform.POLYMARKET)
        assert poly_config is not None
        assert poly_config.api_key == 'test_poly_key'
    
    def test_missing_platform_config(self):
        """Test handling of missing platform configuration."""
        config = Config()
        
        # Should return None if no credentials are configured
        kalshi_config = config.get_platform_config(Platform.KALSHI)
        if 'KALSHI_API_KEY' not in os.environ:
            assert kalshi_config is None


class TestPlatformCredentials:
    """Test platform credentials handling."""
    
    def test_credentials_creation(self):
        """Test creating platform credentials."""
        creds = PlatformCredentials(
            api_key="test_key",
            api_secret="test_secret",
            base_url="https://api.test.com",
            is_testnet=True
        )
        
        assert creds.api_key == "test_key"
        assert creds.api_secret == "test_secret"
        assert creds.is_testnet is True
    
    def test_credentials_without_secret(self):
        """Test credentials that don't require a secret."""
        creds = PlatformCredentials(
            api_key="test_key",
            base_url="https://api.test.com"
        )
        
        assert creds.api_key == "test_key"
        assert creds.api_secret is None