"""
Tests for backtesting models
"""

import pytest
from datetime import datetime

from quantshit.backtesting.models import (
    Market, Position, Order, Trade, OrderType, OrderStatus
)


class TestMarket:
    def test_market_creation(self):
        """Test creating a market"""
        market = Market(
            id="test_market",
            question="Will it rain tomorrow?",
            current_yes_price=0.6,
            current_no_price=0.4
        )
        
        assert market.id == "test_market"
        assert market.question == "Will it rain tomorrow?"
        assert market.current_yes_price == 0.6
        assert market.current_no_price == 0.4
        assert not market.resolved
        assert market.resolution is None
        assert market.timestamp is not None
    
    def test_market_resolution(self):
        """Test market resolution"""
        market = Market(
            id="test_market",
            question="Test question",
            current_yes_price=1.0,
            current_no_price=0.0,
            resolved=True,
            resolution=True
        )
        
        assert market.resolved
        assert market.resolution is True


class TestPosition:
    def test_position_creation(self):
        """Test creating a position"""
        position = Position(
            market_id="test_market",
            outcome=True,
            shares=100.0,
            avg_price=0.6
        )
        
        assert position.market_id == "test_market"
        assert position.outcome is True
        assert position.shares == 100.0
        assert position.avg_price == 0.6
        assert position.realized_pnl == 0.0
    
    def test_unrealized_pnl(self):
        """Test unrealized P&L calculation"""
        position = Position(
            market_id="test_market",
            outcome=True,
            shares=100.0,
            avg_price=0.6
        )
        
        # Price goes up
        pnl = position.unrealized_pnl(0.7)
        assert abs(pnl - 10.0) < 0.01  # 100 * (0.7 - 0.6)
        
        # Price goes down
        pnl = position.unrealized_pnl(0.5)
        assert abs(pnl - (-10.0)) < 0.01  # 100 * (0.5 - 0.6)
    
    def test_total_pnl(self):
        """Test total P&L calculation"""
        position = Position(
            market_id="test_market",
            outcome=True,
            shares=100.0,
            avg_price=0.6,
            realized_pnl=5.0
        )
        
        total_pnl = position.total_pnl(0.7)
        assert abs(total_pnl - 15.0) < 0.01  # 5.0 + 100 * (0.7 - 0.6)


class TestOrder:
    def test_order_creation(self):
        """Test creating an order"""
        order = Order(
            market_id="test_market",
            order_type=OrderType.BUY,
            outcome=True,
            shares=100.0,
            price=0.6
        )
        
        assert order.market_id == "test_market"
        assert order.order_type == OrderType.BUY
        assert order.outcome is True
        assert order.shares == 100.0
        assert order.price == 0.6
        assert order.status == OrderStatus.PENDING
        assert order.order_id is not None
    
    def test_order_id_generation(self):
        """Test order ID is unique"""
        order1 = Order(
            market_id="test_market",
            order_type=OrderType.BUY,
            outcome=True,
            shares=100.0,
            price=0.6
        )
        
        order2 = Order(
            market_id="test_market",
            order_type=OrderType.BUY,
            outcome=True,
            shares=100.0,
            price=0.6
        )
        
        assert order1.order_id != order2.order_id


class TestTrade:
    def test_trade_creation(self):
        """Test creating a trade"""
        trade = Trade(
            order_id="order_123",
            market_id="test_market",
            order_type=OrderType.BUY,
            outcome=True,
            shares=100.0,
            price=0.6,
            commission=0.6
        )
        
        assert trade.order_id == "order_123"
        assert trade.market_id == "test_market"
        assert trade.order_type == OrderType.BUY
        assert trade.outcome is True
        assert trade.shares == 100.0
        assert trade.price == 0.6
        assert trade.commission == 0.6
    
    def test_trade_total_cost_buy(self):
        """Test total cost calculation for buy order"""
        trade = Trade(
            order_id="order_123",
            market_id="test_market",
            order_type=OrderType.BUY,
            outcome=True,
            shares=100.0,
            price=0.6,
            commission=0.6
        )
        
        total_cost = trade.total_cost()
        assert total_cost == 60.6  # 100 * 0.6 + 0.6
    
    def test_trade_total_cost_sell(self):
        """Test total cost calculation for sell order"""
        trade = Trade(
            order_id="order_123",
            market_id="test_market",
            order_type=OrderType.SELL,
            outcome=True,
            shares=100.0,
            price=0.7,
            commission=0.7
        )
        
        total_cost = trade.total_cost()
        assert total_cost == 69.3  # 100 * 0.7 - 0.7
