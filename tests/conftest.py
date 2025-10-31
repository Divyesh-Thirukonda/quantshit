"""
Comprehensive test configuration and fixtures for the entire test suite.
Provides reusable mocks, fixtures, and test data for all test modules.
"""
import os
import sys
import pytest
from datetime import datetime, timedelta
from unittest.mock import MagicMock, Mock, patch
from decimal import Decimal

# Add src to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from src.types import Exchange, OrderSide, OrderStatus, MarketStatus, Outcome
from src.models import Market, Order, Position, Opportunity
from src.config import constants


# =============================================================================
# TEST DATA - Reusable across all tests
# =============================================================================

@pytest.fixture
def sample_kalshi_market():
    """Create a sample Kalshi market for testing"""
    return Market(
        id="kalshi_test_001",
        exchange=Exchange.KALSHI,
        title="Will Bitcoin reach $100k by end of 2025?",
        yes_price=0.45,
        no_price=0.55,
        volume=50000.0,
        liquidity=25000.0,
        status=MarketStatus.OPEN,
        expiry=datetime.now() + timedelta(days=60),
        category="crypto"
    )


@pytest.fixture
def sample_polymarket_market():
    """Create a sample Polymarket market for testing"""
    return Market(
        id="poly_test_001",
        exchange=Exchange.POLYMARKET,
        title="Bitcoin to hit $100k by December 2025",
        yes_price=0.40,
        no_price=0.60,
        volume=75000.0,
        liquidity=30000.0,
        status=MarketStatus.OPEN,
        expiry=datetime.now() + timedelta(days=58),
        category="cryptocurrency"
    )


@pytest.fixture
def sample_kalshi_markets():
    """Create a list of Kalshi markets for testing matching"""
    return [
        Market(
            id="kalshi_001",
            exchange=Exchange.KALSHI,
            title="Donald Trump wins 2024 Presidential Election",
            yes_price=0.52,
            no_price=0.48,
            volume=1000000.0,
            liquidity=500000.0,
            status=MarketStatus.OPEN,
            expiry=datetime(2024, 11, 5),
            category="politics"
        ),
        Market(
            id="kalshi_002",
            exchange=Exchange.KALSHI,
            title="S&P 500 above 6000 by end of 2025",
            yes_price=0.35,
            no_price=0.65,
            volume=250000.0,
            liquidity=100000.0,
            status=MarketStatus.OPEN,
            expiry=datetime(2025, 12, 31),
            category="finance"
        ),
        Market(
            id="kalshi_003",
            exchange=Exchange.KALSHI,
            title="Chiefs win Super Bowl 2025",
            yes_price=0.28,
            no_price=0.72,
            volume=150000.0,
            liquidity=75000.0,
            status=MarketStatus.OPEN,
            expiry=datetime(2025, 2, 9),
            category="sports"
        )
    ]


@pytest.fixture
def sample_polymarket_markets():
    """Create a list of Polymarket markets for testing matching"""
    return [
        Market(
            id="poly_001",
            exchange=Exchange.POLYMARKET,
            title="Trump to win 2024 Presidential Election",
            yes_price=0.48,
            no_price=0.52,
            volume=2000000.0,
            liquidity=750000.0,
            status=MarketStatus.OPEN,
            expiry=datetime(2024, 11, 5),
            category="politics"
        ),
        Market(
            id="poly_002",
            exchange=Exchange.POLYMARKET,
            title="S&P 500 reaches 6000 before 2026",
            yes_price=0.38,
            no_price=0.62,
            volume=180000.0,
            liquidity=90000.0,
            status=MarketStatus.OPEN,
            expiry=datetime(2025, 12, 31),
            category="stocks"
        ),
        Market(
            id="poly_003",
            exchange=Exchange.POLYMARKET,
            title="Tesla stock above $500 by Q4 2025",
            yes_price=0.42,
            no_price=0.58,
            volume=300000.0,
            liquidity=120000.0,
            status=MarketStatus.OPEN,
            expiry=datetime(2025, 12, 31),
            category="stocks"
        )
    ]


@pytest.fixture
def sample_opportunity(sample_kalshi_market, sample_polymarket_market):
    """Create a sample arbitrage opportunity for testing"""
    return Opportunity(
        market_kalshi=sample_kalshi_market,
        market_polymarket=sample_polymarket_market,
        outcome=Outcome.YES,
        spread=0.05,
        expected_profit=125.50,
        expected_profit_pct=0.0315,
        confidence_score=0.85,
        recommended_size=100,
        max_size=500,
        timestamp=datetime.now(),
        expiry=datetime.now() + timedelta(days=58)
    )


@pytest.fixture
def sample_buy_order(sample_kalshi_market):
    """Create a sample buy order for testing"""
    return Order(
        order_id="order_buy_001",
        market_id=sample_kalshi_market.id,
        exchange=Exchange.KALSHI,
        side=OrderSide.BUY,
        outcome=Outcome.YES,
        quantity=100,
        price=0.40,
        status=OrderStatus.PENDING,
        timestamp=datetime.now()
    )


@pytest.fixture
def sample_sell_order(sample_polymarket_market):
    """Create a sample sell order for testing"""
    return Order(
        order_id="order_sell_001",
        market_id=sample_polymarket_market.id,
        exchange=Exchange.POLYMARKET,
        side=OrderSide.SELL,
        outcome=Outcome.YES,
        quantity=100,
        price=0.45,
        status=OrderStatus.PENDING,
        timestamp=datetime.now()
    )


@pytest.fixture
def sample_position(sample_kalshi_market):
    """Create a sample position for testing"""
    return Position(
        position_id="pos_001",
        market_id=sample_kalshi_market.id,
        exchange=Exchange.KALSHI,
        outcome=Outcome.YES,
        quantity=100,
        avg_entry_price=0.40,
        current_price=0.45,
        timestamp=datetime.now(),
        total_cost=40.0
    )


# =============================================================================
# MOCK EXCHANGE CLIENTS
# =============================================================================

@pytest.fixture
def mock_kalshi_client():
    """Mock Kalshi client with typical responses"""
    mock_client = Mock()
    mock_client.exchange = Exchange.KALSHI

    # Mock get_markets method
    mock_client.get_markets.return_value = [
        Market(
            id="kalshi_mock_001",
            exchange=Exchange.KALSHI,
            title="Test Market Kalshi",
            yes_price=0.50,
            no_price=0.50,
            volume=10000.0,
            liquidity=5000.0,
            status=MarketStatus.OPEN,
            expiry=datetime.now() + timedelta(days=30)
        )
    ]

    # Mock place_order method
    mock_client.place_order.return_value = Order(
        order_id="kalshi_order_001",
        market_id="kalshi_mock_001",
        exchange=Exchange.KALSHI,
        side=OrderSide.BUY,
        quantity=100,
        price=0.50,
        status=OrderStatus.FILLED,
        timestamp=datetime.now(),
        filled_at=datetime.now()
    )

    return mock_client


@pytest.fixture
def mock_polymarket_client():
    """Mock Polymarket client with typical responses"""
    mock_client = Mock()
    mock_client.exchange = Exchange.POLYMARKET

    # Mock get_markets method
    mock_client.get_markets.return_value = [
        Market(
            id="poly_mock_001",
            exchange=Exchange.POLYMARKET,
            title="Test Market Polymarket",
            yes_price=0.50,
            no_price=0.50,
            volume=20000.0,
            liquidity=10000.0,
            status=MarketStatus.OPEN,
            expiry=datetime.now() + timedelta(days=30)
        )
    ]

    # Mock place_order method
    mock_client.place_order.return_value = Order(
        order_id="poly_order_001",
        market_id="poly_mock_001",
        exchange=Exchange.POLYMARKET,
        side=OrderSide.SELL,
        quantity=100,
        price=0.55,
        status=OrderStatus.FILLED,
        timestamp=datetime.now(),
        filled_at=datetime.now()
    )

    return mock_client


# =============================================================================
# MOCK API RESPONSES
# =============================================================================

@pytest.fixture
def mock_kalshi_api_response():
    """Mock raw API response from Kalshi"""
    return {
        "markets": [
            {
                "ticker": "KALSHI-TEST-001",
                "title": "Test market question?",
                "yes_bid": 45,
                "yes_ask": 47,
                "no_bid": 53,
                "no_ask": 55,
                "volume": 50000,
                "open_interest": 25000,
                "status": "open",
                "close_time": (datetime.now() + timedelta(days=30)).isoformat(),
                "category": "test"
            }
        ]
    }


@pytest.fixture
def mock_polymarket_api_response():
    """Mock raw API response from Polymarket"""
    return {
        "data": [
            {
                "id": "0xtest123",
                "question": "Test market question?",
                "outcomes": ["Yes", "No"],
                "outcomePrices": ["0.45", "0.55"],
                "volume": "75000",
                "liquidity": "30000",
                "closed": False,
                "endDate": (datetime.now() + timedelta(days=30)).isoformat()
            }
        ]
    }


# =============================================================================
# ENVIRONMENT AND CONFIGURATION
# =============================================================================

@pytest.fixture
def mock_env_vars():
    """Mock environment variables for testing"""
    env_vars = {
        'KALSHI_API_KEY': 'test_kalshi_key_123',
        'POLYMARKET_API_KEY': 'test_poly_key_456',
        'MIN_VOLUME': '1000',
        'MIN_SPREAD': '0.02',
        'PAPER_TRADING': 'true',
        'ENABLE_ALERTS': 'false',
        'LOG_LEVEL': 'DEBUG',
        'DATABASE_URL': 'sqlite:///:memory:'
    }
    with patch.dict(os.environ, env_vars, clear=False):
        yield env_vars


@pytest.fixture
def test_config():
    """Provide test configuration constants"""
    return {
        'min_profit_threshold': 0.02,
        'min_volume': 1000,
        'min_spread': 0.02,
        'kalshi_fee': 0.007,
        'polymarket_fee': 0.02,
        'slippage': 0.01,
        'max_position_size': 1000,
        'min_position_size': 10,
        'similarity_threshold': 0.5,
        'initial_capital': 10000.0
    }


# =============================================================================
# DATABASE AND REPOSITORY MOCKS
# =============================================================================

@pytest.fixture
def mock_repository():
    """Mock repository for testing"""
    from src.database.repository import Repository
    repo = Repository()
    return repo


@pytest.fixture
def in_memory_repository():
    """In-memory repository for integration tests"""
    from src.database.repository import Repository
    return Repository()


# =============================================================================
# SERVICE LAYER FIXTURES
# =============================================================================

@pytest.fixture
def mock_matcher():
    """Mock matcher service"""
    from src.services.matching.matcher import Matcher
    return Matcher(similarity_threshold=0.5)


@pytest.fixture
def mock_scorer():
    """Mock scorer service"""
    from src.services.matching.scorer import Scorer
    return Scorer()


@pytest.fixture
def mock_validator():
    """Mock validator service"""
    from src.services.execution.validator import Validator
    return Validator(available_capital=10000.0)


@pytest.fixture
def mock_executor():
    """Mock executor service"""
    from src.services.execution.executor import Executor
    mock_repo = Mock()
    return Executor(
        kalshi_client=Mock(),
        polymarket_client=Mock(),
        repository=mock_repo
    )


# =============================================================================
# EDGE CASE DATA
# =============================================================================

@pytest.fixture
def closed_market():
    """Market that is closed for testing edge cases"""
    return Market(
        id="closed_001",
        exchange=Exchange.KALSHI,
        title="Closed market for testing",
        yes_price=0.95,
        no_price=0.05,
        volume=100000.0,
        liquidity=0.0,
        status=MarketStatus.CLOSED,
        expiry=datetime.now() - timedelta(days=1),
        category="test"
    )


@pytest.fixture
def expired_opportunity(sample_kalshi_market, sample_polymarket_market):
    """Expired opportunity for testing validation"""
    return Opportunity(
        market_kalshi=sample_kalshi_market,
        market_polymarket=sample_polymarket_market,
        outcome=Outcome.YES,
        spread=0.05,
        expected_profit=100.0,
        expected_profit_pct=0.025,
        confidence_score=0.8,
        recommended_size=100,
        max_size=500,
        timestamp=datetime.now() - timedelta(hours=2),
        expiry=datetime.now() - timedelta(hours=1)  # Already expired
    )


@pytest.fixture
def low_confidence_opportunity(sample_kalshi_market, sample_polymarket_market):
    """Low confidence opportunity for testing validation"""
    return Opportunity(
        market_kalshi=sample_kalshi_market,
        market_polymarket=sample_polymarket_market,
        outcome=Outcome.YES,
        spread=0.02,
        expected_profit=50.0,
        expected_profit_pct=0.015,
        confidence_score=0.3,  # Low confidence
        recommended_size=100,
        max_size=500,
        timestamp=datetime.now(),
        expiry=datetime.now() + timedelta(days=30)
    )


# =============================================================================
# PYTEST CONFIGURATION
# =============================================================================

def pytest_configure(config):
    """Configure pytest with custom markers"""
    config.addinivalue_line(
        "markers", "unit: Unit tests for individual components"
    )
    config.addinivalue_line(
        "markers", "integration: Integration tests for full workflows"
    )
    config.addinivalue_line(
        "markers", "slow: Tests that take longer to run"
    )
    config.addinivalue_line(
        "markers", "api: Tests that interact with external APIs"
    )
    config.addinivalue_line(
        "markers", "database: Tests that require database access"
    )


@pytest.fixture(autouse=True)
def reset_test_state():
    """Reset any global state before each test"""
    yield
    # Cleanup after test if needed
    pass


# =============================================================================
# UTILITY FIXTURES
# =============================================================================

@pytest.fixture
def freeze_time():
    """Freeze time for consistent testing"""
    frozen_time = datetime(2025, 1, 15, 12, 0, 0)
    with patch('src.models.opportunity.datetime') as mock_datetime:
        mock_datetime.now.return_value = frozen_time
        mock_datetime.side_effect = lambda *args, **kwargs: datetime(*args, **kwargs)
        yield frozen_time


@pytest.fixture
def capture_logs():
    """Capture log output for testing"""
    import logging
    from io import StringIO

    log_stream = StringIO()
    handler = logging.StreamHandler(log_stream)
    logger = logging.getLogger('src')
    logger.addHandler(handler)
    logger.setLevel(logging.DEBUG)

    yield log_stream

    logger.removeHandler(handler)
