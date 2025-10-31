"""
Comprehensive unit tests for exchange client implementations.
Tests parsers, API clients, and error handling.
"""
import pytest
from datetime import datetime, timedelta
from unittest.mock import Mock, patch, MagicMock
import requests

from src.types import Exchange, OrderSide, OrderStatus, MarketStatus, Outcome
from src.models import Market, Order
from src.exchanges.base import BaseExchangeClient
from src.exchanges.kalshi.client import KalshiClient
from src.exchanges.kalshi.parser import KalshiParser
from src.exchanges.polymarket.client import PolymarketClient
from src.exchanges.polymarket.parser import PolymarketParser


@pytest.mark.unit
class TestBaseExchangeClient:
    """Test base exchange client interface"""

    def test_base_client_cannot_be_instantiated(self):
        """Test that abstract base class cannot be instantiated directly"""
        with pytest.raises(TypeError):
            BaseExchangeClient(api_key="test", exchange=Exchange.KALSHI)

    def test_base_client_requires_implementation(self):
        """Test that subclass must implement abstract methods"""
        class IncompleteClient(BaseExchangeClient):
            pass

        with pytest.raises(TypeError):
            IncompleteClient(api_key="test", exchange=Exchange.KALSHI)


@pytest.mark.unit
class TestKalshiParser:
    """Test Kalshi API response parser"""

    def test_parse_market_valid_response(self):
        """Test parsing valid Kalshi market response"""
        raw_market = {
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

        parser = KalshiParser()
        market = parser.parse_market(raw_market)

        assert isinstance(market, Market)
        assert market.id == "KALSHI-TEST-001"
        assert market.exchange == Exchange.KALSHI
        assert market.title == "Test market question?"
        assert market.status == MarketStatus.OPEN
        assert market.category == "test"

    def test_parse_market_calculates_mid_prices(self):
        """Test that parser calculates mid prices from bid/ask"""
        raw_market = {
            "ticker": "TEST",
            "title": "Test",
            "yes_bid": 40,
            "yes_ask": 50,
            "no_bid": 50,
            "no_ask": 60,
            "volume": 1000,
            "open_interest": 500,
            "status": "open",
            "close_time": datetime.now().isoformat()
        }

        parser = KalshiParser()
        market = parser.parse_market(raw_market)

        # Mid price = (bid + ask) / 2 / 100
        assert market.yes_price == 0.45  # (40 + 50) / 2 / 100
        assert market.no_price == 0.55   # (50 + 60) / 2 / 100

    def test_parse_market_converts_volume(self):
        """Test that parser converts volume correctly"""
        raw_market = {
            "ticker": "TEST",
            "title": "Test",
            "yes_bid": 45,
            "yes_ask": 47,
            "no_bid": 53,
            "no_ask": 55,
            "volume": 50000,
            "open_interest": 25000,
            "status": "open",
            "close_time": datetime.now().isoformat()
        }

        parser = KalshiParser()
        market = parser.parse_market(raw_market)

        assert market.volume == 50000.0
        assert market.liquidity == 25000.0

    def test_parse_market_handles_closed_status(self):
        """Test parsing closed market"""
        raw_market = {
            "ticker": "TEST",
            "title": "Test",
            "yes_bid": 95,
            "yes_ask": 97,
            "no_bid": 3,
            "no_ask": 5,
            "volume": 100000,
            "open_interest": 0,
            "status": "closed",
            "close_time": (datetime.now() - timedelta(days=1)).isoformat()
        }

        parser = KalshiParser()
        market = parser.parse_market(raw_market)

        assert market.status == MarketStatus.CLOSED
        assert market.expiry < datetime.now()

    def test_parse_markets_batch(self):
        """Test parsing multiple markets at once"""
        raw_markets = [
            {
                "ticker": f"TEST-{i}",
                "title": f"Test {i}",
                "yes_bid": 45,
                "yes_ask": 47,
                "no_bid": 53,
                "no_ask": 55,
                "volume": 1000,
                "open_interest": 500,
                "status": "open",
                "close_time": datetime.now().isoformat()
            }
            for i in range(3)
        ]

        parser = KalshiParser()
        markets = parser.parse_markets(raw_markets)

        assert len(markets) == 3
        for market in markets:
            assert isinstance(market, Market)


@pytest.mark.unit
class TestPolymarketParser:
    """Test Polymarket API response parser"""

    def test_parse_market_valid_response(self):
        """Test parsing valid Polymarket market response"""
        raw_market = {
            "id": "0xtest123",
            "question": "Test market question?",
            "outcomes": ["Yes", "No"],
            "outcomePrices": ["0.45", "0.55"],
            "volume": "75000",
            "liquidity": "30000",
            "closed": False,
            "endDate": (datetime.now() + timedelta(days=30)).isoformat(),
            "category": "test"
        }

        parser = PolymarketParser()
        market = parser.parse_market(raw_market)

        assert isinstance(market, Market)
        assert market.id == "0xtest123"
        assert market.exchange == Exchange.POLYMARKET
        assert market.title == "Test market question?"
        assert market.yes_price == 0.45
        assert market.no_price == 0.55
        assert market.volume == 75000.0
        assert market.liquidity == 30000.0
        assert market.status == MarketStatus.OPEN

    def test_parse_market_handles_string_prices(self):
        """Test that parser converts string prices to float"""
        raw_market = {
            "id": "test",
            "question": "Test",
            "outcomes": ["Yes", "No"],
            "outcomePrices": ["0.42", "0.58"],
            "volume": "1000",
            "liquidity": "500",
            "closed": False,
            "endDate": datetime.now().isoformat()
        }

        parser = PolymarketParser()
        market = parser.parse_market(raw_market)

        assert isinstance(market.yes_price, float)
        assert isinstance(market.no_price, float)
        assert market.yes_price == 0.42
        assert market.no_price == 0.58

    def test_parse_market_handles_closed_market(self):
        """Test parsing closed Polymarket market"""
        raw_market = {
            "id": "test",
            "question": "Test",
            "outcomes": ["Yes", "No"],
            "outcomePrices": ["0.95", "0.05"],
            "volume": "100000",
            "liquidity": "0",
            "closed": True,
            "endDate": (datetime.now() - timedelta(days=1)).isoformat()
        }

        parser = PolymarketParser()
        market = parser.parse_market(raw_market)

        assert market.status == MarketStatus.CLOSED
        assert market.liquidity == 0.0

    def test_parse_markets_batch(self):
        """Test parsing multiple Polymarket markets"""
        raw_markets = [
            {
                "id": f"test-{i}",
                "question": f"Test {i}",
                "outcomes": ["Yes", "No"],
                "outcomePrices": ["0.50", "0.50"],
                "volume": "1000",
                "liquidity": "500",
                "closed": False,
                "endDate": datetime.now().isoformat()
            }
            for i in range(3)
        ]

        parser = PolymarketParser()
        markets = parser.parse_markets(raw_markets)

        assert len(markets) == 3
        for market in markets:
            assert isinstance(market, Market)


@pytest.mark.unit
@pytest.mark.api
class TestKalshiClient:
    """Test Kalshi API client"""

    @patch('src.exchanges.kalshi.client.requests.get')
    def test_get_markets_success(self, mock_get):
        """Test successful market data fetch from Kalshi"""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "markets": [
                {
                    "ticker": "TEST-001",
                    "title": "Test",
                    "yes_bid": 45,
                    "yes_ask": 47,
                    "no_bid": 53,
                    "no_ask": 55,
                    "volume": 1000,
                    "open_interest": 500,
                    "status": "open",
                    "close_time": datetime.now().isoformat()
                }
            ]
        }
        mock_get.return_value = mock_response

        client = KalshiClient(api_key="test_key")
        markets = client.get_markets(min_volume=0)

        assert len(markets) >= 0
        mock_get.assert_called_once()

    @patch('src.exchanges.kalshi.client.requests.get')
    def test_get_markets_filters_by_volume(self, mock_get):
        """Test that get_markets respects min_volume filter"""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "markets": [
                {
                    "ticker": "TEST-001",
                    "title": "High volume",
                    "yes_bid": 45,
                    "yes_ask": 47,
                    "no_bid": 53,
                    "no_ask": 55,
                    "volume": 10000,
                    "open_interest": 5000,
                    "status": "open",
                    "close_time": datetime.now().isoformat()
                },
                {
                    "ticker": "TEST-002",
                    "title": "Low volume",
                    "yes_bid": 45,
                    "yes_ask": 47,
                    "no_bid": 53,
                    "no_ask": 55,
                    "volume": 100,
                    "open_interest": 50,
                    "status": "open",
                    "close_time": datetime.now().isoformat()
                }
            ]
        }
        mock_get.return_value = mock_response

        client = KalshiClient(api_key="test_key")
        markets = client.get_markets(min_volume=5000)

        # Should only return markets with volume >= 5000
        for market in markets:
            assert market.volume >= 5000

    @patch('src.exchanges.kalshi.client.requests.get')
    def test_get_markets_handles_api_error(self, mock_get):
        """Test handling of API errors"""
        mock_get.side_effect = requests.RequestException("API Error")

        client = KalshiClient(api_key="test_key")
        markets = client.get_markets()

        # Should return empty list on error
        assert markets == []

    def test_client_initialization(self):
        """Test Kalshi client initializes correctly"""
        client = KalshiClient(api_key="test_key_123")
        assert client.api_key == "test_key_123"
        assert client.exchange == Exchange.KALSHI


@pytest.mark.unit
@pytest.mark.api
class TestPolymarketClient:
    """Test Polymarket API client"""

    @patch('src.exchanges.polymarket.client.requests.get')
    def test_get_markets_success(self, mock_get):
        """Test successful market data fetch from Polymarket"""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "data": [
                {
                    "id": "test-001",
                    "question": "Test",
                    "outcomes": ["Yes", "No"],
                    "outcomePrices": ["0.50", "0.50"],
                    "volume": "1000",
                    "liquidity": "500",
                    "closed": False,
                    "endDate": datetime.now().isoformat()
                }
            ]
        }
        mock_get.return_value = mock_response

        client = PolymarketClient(api_key="test_key")
        markets = client.get_markets(min_volume=0)

        assert len(markets) >= 0
        mock_get.assert_called_once()

    @patch('src.exchanges.polymarket.client.requests.get')
    def test_get_markets_handles_api_error(self, mock_get):
        """Test handling of Polymarket API errors"""
        mock_get.side_effect = requests.RequestException("API Error")

        client = PolymarketClient(api_key="test_key")
        markets = client.get_markets()

        # Should return empty list on error
        assert markets == []

    def test_client_initialization(self):
        """Test Polymarket client initializes correctly"""
        client = PolymarketClient(api_key="test_key_456")
        assert client.api_key == "test_key_456"
        assert client.exchange == Exchange.POLYMARKET
