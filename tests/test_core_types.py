"""Tests for core data types."""

import sys
from pathlib import Path

# Add the project root to the Python path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

import pytest
from decimal import Decimal
from datetime import datetime

from src.core import (
    Platform, Outcome, Market, Quote, ArbitrageOpportunity,
    OrderType, Order, OrderStatus, MarketStatus
)


class TestMarket:
    """Test Market data type."""
    
    def test_market_creation(self, sample_market_kalshi):
        """Test creating a market instance."""
        market = sample_market_kalshi
        
        assert market.platform == Platform.KALSHI
        assert market.title == "Will Bitcoin hit $100k by end of 2024?"
        assert market.status == MarketStatus.ACTIVE
        assert isinstance(market.yes_price, Decimal)
        assert isinstance(market.no_price, Decimal)
        assert market.yes_price + market.no_price == Decimal('1.0')
    
    def test_market_timestamps(self, sample_market_kalshi):
        """Test market timestamp fields."""
        market = sample_market_kalshi
        
        assert isinstance(market.created_at, datetime)
        assert isinstance(market.updated_at, datetime)
        assert isinstance(market.close_time, datetime)


class TestQuote:
    """Test Quote data type."""
    
    def test_quote_creation(self, sample_quote_kalshi):
        """Test creating a quote instance."""
        quote = sample_quote_kalshi
        
        assert quote.platform == Platform.KALSHI
        assert quote.outcome == Outcome.YES
        assert isinstance(quote.bid_price, Decimal)
        assert isinstance(quote.ask_price, Decimal)
        assert quote.ask_price > quote.bid_price  # Spread check
    
    def test_quote_spread(self, sample_quote_kalshi):
        """Test quote spread calculation."""
        quote = sample_quote_kalshi
        spread = quote.ask_price - quote.bid_price
        
        assert spread > 0
        assert spread == Decimal('0.02')  # Based on fixture data


class TestArbitrageOpportunity:
    """Test ArbitrageOpportunity data type."""
    
    def test_opportunity_creation(self, sample_arbitrage_opportunity):
        """Test creating an arbitrage opportunity."""
        opp = sample_arbitrage_opportunity
        
        assert opp.market_a.platform != opp.market_b.platform
        assert isinstance(opp.expected_profit, Decimal)
        assert isinstance(opp.profit_percentage, Decimal)
        assert 0 <= opp.confidence_score <= 1
    
    def test_opportunity_profit_calculation(self, sample_arbitrage_opportunity):
        """Test profit calculations are reasonable."""
        opp = sample_arbitrage_opportunity
        
        # Profit percentage should be reasonable (not negative, not too high)
        assert opp.profit_percentage > 0
        assert opp.profit_percentage < Decimal('1.0')  # Less than 100%


class TestOrder:
    """Test Order data type."""
    
    def test_order_creation(self):
        """Test creating an order."""
        order = Order(
            market_id="TEST_MARKET",
            platform=Platform.KALSHI,
            order_type=OrderType.LIMIT,
            outcome=Outcome.YES,
            quantity=Decimal('100'),
            price=Decimal('0.65'),
            status=OrderStatus.PENDING
        )
        
        assert order.platform == Platform.KALSHI
        assert order.order_type == OrderType.LIMIT
        assert order.status == OrderStatus.PENDING
        assert order.filled_quantity == Decimal('0')
    
    def test_order_fill_tracking(self):
        """Test order fill tracking."""
        order = Order(
            market_id="TEST_MARKET",
            platform=Platform.KALSHI,
            order_type=OrderType.LIMIT,
            outcome=Outcome.YES,
            quantity=Decimal('100'),
            price=Decimal('0.65'),
            status=OrderStatus.PARTIAL
        )
        
        # Simulate partial fill
        order.filled_quantity = Decimal('50')
        order.average_fill_price = Decimal('0.64')
        
        assert order.filled_quantity < order.quantity
        assert order.status == OrderStatus.PARTIAL