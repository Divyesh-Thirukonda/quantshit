"""
Tests for portfolio management
"""

import pytest
from datetime import datetime

from quantshit.backtesting.portfolio import Portfolio
from quantshit.backtesting.models import Trade, OrderType, Market, Position


class TestPortfolio:
    def test_portfolio_initialization(self):
        """Test portfolio initialization"""
        portfolio = Portfolio(initial_capital=10000, commission_rate=0.01)
        
        assert portfolio.initial_capital == 10000
        assert portfolio.cash == 10000
        assert portfolio.commission_rate == 0.01
        assert len(portfolio.positions) == 0
        assert len(portfolio.trades) == 0
    
    def test_execute_buy_trade(self):
        """Test executing a buy trade"""
        portfolio = Portfolio(initial_capital=10000)
        
        trade = Trade(
            order_id="order_1",
            market_id="market_1",
            order_type=OrderType.BUY,
            outcome=True,
            shares=100.0,
            price=0.6,
            commission=0.6
        )
        
        result = portfolio.execute_trade(trade)
        assert result is True
        
        # Check cash deducted
        assert portfolio.cash == 10000 - 60.6
        
        # Check position created
        position = portfolio.get_position("market_1", True)
        assert position is not None
        assert position.shares == 100.0
        assert position.avg_price == 0.6
        
        # Check trade recorded
        assert len(portfolio.trades) == 1
    
    def test_execute_buy_insufficient_funds(self):
        """Test executing a buy trade with insufficient funds"""
        portfolio = Portfolio(initial_capital=50)
        
        trade = Trade(
            order_id="order_1",
            market_id="market_1",
            order_type=OrderType.BUY,
            outcome=True,
            shares=100.0,
            price=0.6,
            commission=0.6
        )
        
        result = portfolio.execute_trade(trade)
        assert result is False
        assert portfolio.cash == 50
        assert len(portfolio.positions) == 0
    
    def test_execute_sell_trade(self):
        """Test executing a sell trade"""
        portfolio = Portfolio(initial_capital=10000)
        
        # First buy
        buy_trade = Trade(
            order_id="order_1",
            market_id="market_1",
            order_type=OrderType.BUY,
            outcome=True,
            shares=100.0,
            price=0.6,
            commission=0.6
        )
        portfolio.execute_trade(buy_trade)
        
        # Then sell
        sell_trade = Trade(
            order_id="order_2",
            market_id="market_1",
            order_type=OrderType.SELL,
            outcome=True,
            shares=50.0,
            price=0.7,
            commission=0.35
        )
        
        result = portfolio.execute_trade(sell_trade)
        assert result is True
        
        # Check cash increased
        expected_cash = 10000 - 60.6 + 35.0 - 0.35
        assert abs(portfolio.cash - expected_cash) < 0.01
        
        # Check position updated
        position = portfolio.get_position("market_1", True)
        assert position.shares == 50.0
        
        # Check realized PnL
        expected_pnl = 50.0 * (0.7 - 0.6) - 0.35
        assert abs(position.realized_pnl - expected_pnl) < 0.01
    
    def test_execute_sell_no_position(self):
        """Test executing a sell trade without position"""
        portfolio = Portfolio(initial_capital=10000)
        
        sell_trade = Trade(
            order_id="order_1",
            market_id="market_1",
            order_type=OrderType.SELL,
            outcome=True,
            shares=100.0,
            price=0.7,
            commission=0.7
        )
        
        result = portfolio.execute_trade(sell_trade)
        assert result is False
    
    def test_execute_sell_insufficient_shares(self):
        """Test executing a sell trade with insufficient shares"""
        portfolio = Portfolio(initial_capital=10000)
        
        # Buy 50 shares
        buy_trade = Trade(
            order_id="order_1",
            market_id="market_1",
            order_type=OrderType.BUY,
            outcome=True,
            shares=50.0,
            price=0.6,
            commission=0.3
        )
        portfolio.execute_trade(buy_trade)
        
        # Try to sell 100 shares
        sell_trade = Trade(
            order_id="order_2",
            market_id="market_1",
            order_type=OrderType.SELL,
            outcome=True,
            shares=100.0,
            price=0.7,
            commission=0.7
        )
        
        result = portfolio.execute_trade(sell_trade)
        assert result is False
    
    def test_resolve_market_winning_position(self):
        """Test resolving a market with winning position"""
        portfolio = Portfolio(initial_capital=10000)
        
        # Buy YES shares
        trade = Trade(
            order_id="order_1",
            market_id="market_1",
            order_type=OrderType.BUY,
            outcome=True,
            shares=100.0,
            price=0.6,
            commission=0.6
        )
        portfolio.execute_trade(trade)
        
        # Resolve market to YES
        market = Market(
            id="market_1",
            question="Test",
            current_yes_price=1.0,
            current_no_price=0.0,
            resolved=True,
            resolution=True
        )
        
        pnl = portfolio.resolve_market(market)
        
        # P&L = settlement - cost_basis
        # Settlement = 100 * 1.0 = 100
        # Cost basis = 100 * 0.6 = 60 (commission already deducted from cash)
        expected_pnl = 100.0 - 60.0
        assert abs(pnl - expected_pnl) < 0.01
        
        # Position should be removed
        assert portfolio.get_position("market_1", True) is None
        
        # Cash should include settlement
        expected_cash = 10000 - 60.6 + 100.0
        assert abs(portfolio.cash - expected_cash) < 0.01
    
    def test_resolve_market_losing_position(self):
        """Test resolving a market with losing position"""
        portfolio = Portfolio(initial_capital=10000)
        
        # Buy YES shares
        trade = Trade(
            order_id="order_1",
            market_id="market_1",
            order_type=OrderType.BUY,
            outcome=True,
            shares=100.0,
            price=0.6,
            commission=0.6
        )
        portfolio.execute_trade(trade)
        
        # Resolve market to NO
        market = Market(
            id="market_1",
            question="Test",
            current_yes_price=0.0,
            current_no_price=1.0,
            resolved=True,
            resolution=False
        )
        
        pnl = portfolio.resolve_market(market)
        
        # P&L = settlement - cost_basis
        # Settlement = 0
        # Cost basis = 100 * 0.6 = 60
        expected_pnl = 0.0 - 60.0
        assert abs(pnl - expected_pnl) < 0.01
        
        # Position should be removed
        assert portfolio.get_position("market_1", True) is None
        
        # Cash should be unchanged (no settlement, commission already deducted)
        expected_cash = 10000 - 60.6
        assert abs(portfolio.cash - expected_cash) < 0.01
    
    def test_get_total_value(self):
        """Test calculating total portfolio value"""
        portfolio = Portfolio(initial_capital=10000)
        
        # Buy position
        trade = Trade(
            order_id="order_1",
            market_id="market_1",
            order_type=OrderType.BUY,
            outcome=True,
            shares=100.0,
            price=0.6,
            commission=0.6
        )
        portfolio.execute_trade(trade)
        
        # Create market with updated price
        markets = {
            "market_1": Market(
                id="market_1",
                question="Test",
                current_yes_price=0.7,
                current_no_price=0.3
            )
        }
        
        total_value = portfolio.get_total_value(markets)
        
        # Cash + (100 shares * 0.7 price)
        expected_value = (10000 - 60.6) + (100 * 0.7)
        assert abs(total_value - expected_value) < 0.01
    
    def test_get_total_pnl(self):
        """Test calculating total P&L"""
        portfolio = Portfolio(initial_capital=10000)
        
        trade = Trade(
            order_id="order_1",
            market_id="market_1",
            order_type=OrderType.BUY,
            outcome=True,
            shares=100.0,
            price=0.6,
            commission=0.6
        )
        portfolio.execute_trade(trade)
        
        markets = {
            "market_1": Market(
                id="market_1",
                question="Test",
                current_yes_price=0.7,
                current_no_price=0.3
            )
        }
        
        pnl = portfolio.get_total_pnl(markets)
        
        # (100 * 0.7) - 60.6 = 9.4
        expected_pnl = 70 - 60.6
        assert abs(pnl - expected_pnl) < 0.01
    
    def test_get_returns(self):
        """Test calculating returns"""
        portfolio = Portfolio(initial_capital=10000)
        
        trade = Trade(
            order_id="order_1",
            market_id="market_1",
            order_type=OrderType.BUY,
            outcome=True,
            shares=100.0,
            price=0.6,
            commission=0.6
        )
        portfolio.execute_trade(trade)
        
        markets = {
            "market_1": Market(
                id="market_1",
                question="Test",
                current_yes_price=0.8,
                current_no_price=0.2
            )
        }
        
        returns = portfolio.get_returns(markets)
        
        # P&L = 80 - 60.6 = 19.4
        # Returns = 19.4 / 10000
        expected_returns = 19.4 / 10000
        assert abs(returns - expected_returns) < 0.0001
