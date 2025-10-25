"""
Test configuration and fixtures for the test suite
"""
import os
import sys
import pytest
from unittest.mock import MagicMock, patch

# Add src to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

# Test configuration
TEST_API_KEYS = {
    'polymarket': 'test_poly_key',
    'kalshi': 'test_kalshi_key'
}

TEST_MARKET_DATA = {
    'polymarket': [
        {
            'id': 'poly_market_1',
            'title': 'Test Market 1',
            'yes_price': 0.45,
            'no_price': 0.55,
            'volume': 5000,
            'liquidity': 2500,
            'platform': 'polymarket'
        },
        {
            'id': 'poly_market_2',
            'title': 'Test Market 2',
            'yes_price': 0.30,
            'no_price': 0.70,
            'volume': 3000,
            'liquidity': 1500,
            'platform': 'polymarket'
        }
    ],
    'kalshi': [
        {
            'id': 'kalshi_market_1',
            'title': 'Test Market 1',
            'yes_price': 0.40,
            'no_price': 0.60,
            'volume': 4000,
            'liquidity': 2000,
            'platform': 'kalshi'
        },
        {
            'id': 'kalshi_market_2',
            'title': 'Test Market 2',
            'yes_price': 0.25,
            'no_price': 0.75,
            'volume': 2500,
            'liquidity': 1250,
            'platform': 'kalshi'
        }
    ]
}

@pytest.fixture
def mock_api_keys():
    """Provide test API keys"""
    return TEST_API_KEYS.copy()

@pytest.fixture
def mock_market_data():
    """Provide test market data"""
    return TEST_MARKET_DATA.copy()

@pytest.fixture
def mock_platform_api():
    """Mock platform API for testing"""
    mock_api = MagicMock()
    mock_api.get_recent_markets.return_value = TEST_MARKET_DATA['polymarket']
    mock_api.place_buy_order.return_value = {'success': True, 'order_id': 'test_buy_123'}
    mock_api.place_sell_order.return_value = {'success': True, 'order_id': 'test_sell_456'}
    mock_api.find_event.return_value = TEST_MARKET_DATA['polymarket'][:1]
    return mock_api

@pytest.fixture
def patch_get_market_api(mock_platform_api):
    """Patch the get_market_api function to return mock API"""
    with patch('src.platforms.get_market_api', return_value=mock_platform_api):
        yield mock_platform_api

@pytest.fixture
def patch_env_vars():
    """Patch environment variables for testing"""
    env_vars = {
        'MIN_VOLUME': '1000',
        'MIN_SPREAD': '0.05',
        'POLYMARKET_API_KEY': 'test_poly_key',
        'KALSHI_API_KEY': 'test_kalshi_key'
    }
    with patch.dict(os.environ, env_vars):
        yield env_vars