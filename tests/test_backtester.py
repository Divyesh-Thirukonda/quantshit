"""
Tests for backtesting engine
"""

import pytest
from datetime import datetime, timedelta

from quantshit import Backtester, Market, Portfolio
from quantshit.backtesting.models import Order, OrderType, OrderStatus
from quantshit.strategies.base import Strategy


class SimpleTestStrategy(Strategy):
    """Simple strategy for testing"""
    
    def __init__(self):
        super().__init__(name="SimpleTestStrategy")
        self.generated_signals = []
    
    def generate_signals(self, markets, portfolio, timestamp):
        """Generate simple test signals"""
        orders = []
        
        # Buy if price < 0.5
        for market_id, market in markets.items():
            if not market.resolved and market.current_yes_price < 0.5:
                if portfolio.get_position(market_id, True) is None:
                    orders.append(Order(
                        market_id=market_id,
                        order_type=OrderType.BUY,
                        outcome=True,
                        shares=10.0,
                        price=market.current_yes_price,
                        timestamp=timestamp
                    ))
        
        self.generated_signals.extend(orders)
        return orders


class TestBacktester:
    def test_backtester_initialization(self):
        """Test backtester initialization"""
        backtester = Backtester(
            initial_capital=10000,
            commission_rate=0.01,
            slippage=0.005
        )
        
        assert backtester.initial_capital == 10000
        assert backtester.commission_rate == 0.01
        assert backtester.slippage == 0.005
        assert backtester.portfolio.initial_capital == 10000
        assert len(backtester.markets) == 0
    
    def test_set_strategy(self):
        """Test setting a strategy"""
        backtester = Backtester(initial_capital=10000)
        strategy = SimpleTestStrategy()
        
        backtester.set_strategy(strategy)
        assert backtester.strategy == strategy
    
    def test_update_market(self):
        """Test updating market data"""
        backtester = Backtester(initial_capital=10000)
        
        market = Market(
            id="market_1",
            question="Test",
            current_yes_price=0.5,
            current_no_price=0.5
        )
        
        backtester.update_market(market)
        assert "market_1" in backtester.markets
        assert backtester.markets["market_1"] == market
    
    def test_process_order_buy_fills(self):
        """Test processing a buy order that fills"""
        backtester = Backtester(initial_capital=10000, slippage=0.0)
        
        # Add market
        market = Market(
            id="market_1",
            question="Test",
            current_yes_price=0.5,
            current_no_price=0.5
        )
        backtester.update_market(market)
        
        # Create buy order at market price
        order = Order(
            market_id="market_1",
            order_type=OrderType.BUY,
            outcome=True,
            shares=100.0,
            price=0.5
        )
        
        trade = backtester.process_order(order)
        
        assert trade is not None
        assert order.status == OrderStatus.FILLED
        assert trade.shares == 100.0
        assert trade.price == 0.5
    
    def test_process_order_buy_no_fill(self):
        """Test processing a buy order that doesn't fill"""
        backtester = Backtester(initial_capital=10000)
        
        market = Market(
            id="market_1",
            question="Test",
            current_yes_price=0.6,
            current_no_price=0.4
        )
        backtester.update_market(market)
        
        # Buy order with limit below market
        order = Order(
            market_id="market_1",
            order_type=OrderType.BUY,
            outcome=True,
            shares=100.0,
            price=0.5  # Below market price
        )
        
        trade = backtester.process_order(order)
        
        assert trade is None
        assert order.status == OrderStatus.CANCELLED
    
    def test_process_order_sell_fills(self):
        """Test processing a sell order that fills"""
        backtester = Backtester(initial_capital=10000, slippage=0.0)
        
        # First buy shares
        market = Market(
            id="market_1",
            question="Test",
            current_yes_price=0.5,
            current_no_price=0.5
        )
        backtester.update_market(market)
        
        buy_order = Order(
            market_id="market_1",
            order_type=OrderType.BUY,
            outcome=True,
            shares=100.0,
            price=0.5
        )
        backtester.process_order(buy_order)
        
        # Update market price for sell
        market_updated = Market(
            id="market_1",
            question="Test",
            current_yes_price=0.6,
            current_no_price=0.4
        )
        backtester.update_market(market_updated)
        
        # Now sell at or below market price
        sell_order = Order(
            market_id="market_1",
            order_type=OrderType.SELL,
            outcome=True,
            shares=50.0,
            price=0.6  # At market price
        )
        
        trade = backtester.process_order(sell_order)
        
        assert trade is not None
        assert sell_order.status == OrderStatus.FILLED
    
    def test_process_order_market_not_found(self):
        """Test processing order for non-existent market"""
        backtester = Backtester(initial_capital=10000)
        
        order = Order(
            market_id="nonexistent",
            order_type=OrderType.BUY,
            outcome=True,
            shares=100.0,
            price=0.5
        )
        
        trade = backtester.process_order(order)
        
        assert trade is None
        assert order.status == OrderStatus.REJECTED
    
    def test_run_backtest(self):
        """Test running a full backtest"""
        backtester = Backtester(
            initial_capital=10000,
            commission_rate=0.01,
            slippage=0.0
        )
        
        # Create market data
        start_time = datetime.now()
        market_data = []
        
        for i in range(10):
            price = 0.4 + i * 0.02  # Price goes from 0.4 to 0.58
            market_data.append(Market(
                id="market_1",
                question="Test",
                current_yes_price=price,
                current_no_price=1.0 - price,
                timestamp=start_time + timedelta(hours=i)
            ))
        
        # Add resolution
        market_data.append(Market(
            id="market_1",
            question="Test",
            current_yes_price=1.0,
            current_no_price=0.0,
            resolved=True,
            resolution=True,
            timestamp=start_time + timedelta(hours=11)
        ))
        
        # Run with strategy
        strategy = SimpleTestStrategy()
        performance_df = backtester.run(market_data, strategy)
        
        assert len(performance_df) > 0
        assert "total_value" in performance_df.columns
        assert "cash" in performance_df.columns
        assert len(backtester.portfolio.trades) > 0
    
    def test_run_backtest_without_strategy(self):
        """Test running backtest without setting strategy"""
        backtester = Backtester(initial_capital=10000)
        
        market_data = [
            Market(
                id="market_1",
                question="Test",
                current_yes_price=0.5,
                current_no_price=0.5
            )
        ]
        
        with pytest.raises(ValueError):
            backtester.run(market_data)
    
    def test_get_results(self):
        """Test getting backtest results"""
        backtester = Backtester(initial_capital=10000, slippage=0.0)
        
        # Run simple backtest
        market_data = [
            Market(
                id="market_1",
                question="Test",
                current_yes_price=0.4,
                current_no_price=0.6,
                timestamp=datetime.now()
            ),
            Market(
                id="market_1",
                question="Test",
                current_yes_price=0.6,
                current_no_price=0.4,
                timestamp=datetime.now() + timedelta(hours=1)
            )
        ]
        
        strategy = SimpleTestStrategy()
        backtester.run(market_data, strategy)
        
        results = backtester.get_results()
        
        assert "initial_capital" in results
        assert "total_value" in results
        assert "total_pnl" in results
        assert "returns" in results
        assert "num_trades" in results
        assert results["initial_capital"] == 10000
    
    def test_slippage_applied(self):
        """Test that slippage is applied to trades"""
        backtester = Backtester(
            initial_capital=10000,
            commission_rate=0.0,
            slippage=0.01
        )
        
        market = Market(
            id="market_1",
            question="Test",
            current_yes_price=0.5,
            current_no_price=0.5
        )
        backtester.update_market(market)
        
        order = Order(
            market_id="market_1",
            order_type=OrderType.BUY,
            outcome=True,
            shares=100.0,
            price=0.6  # Above market
        )
        
        trade = backtester.process_order(order)
        
        assert trade is not None
        # Execution price should be market + slippage
        assert trade.price == 0.51  # 0.5 + 0.01
