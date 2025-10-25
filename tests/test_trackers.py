"""
Tests for portfolio tracking components
"""
from unittest.mock import MagicMock
from src.trackers.portfolio_tracker import PortfolioTracker


class TestPortfolioTracker:
    """Test the portfolio tracker"""
    
    def test_initialization_empty(self):
        """Test tracker initialization with no initial balances"""
        tracker = PortfolioTracker()
        
        assert len(tracker.virtual_balances) == 0
        assert len(tracker.positions) == 0
        assert len(tracker.trade_history) == 0
    
    def test_initialization_with_balances(self):
        """Test tracker initialization with initial balances"""
        initial_balances = {'polymarket': 10000, 'kalshi': 8000}
        tracker = PortfolioTracker(initial_balances)
        
        assert tracker.virtual_balances['polymarket'] == 10000
        assert tracker.virtual_balances['kalshi'] == 8000
    
    def test_initialize_platform(self):
        """Test platform initialization"""
        tracker = PortfolioTracker()
        tracker.initialize_platform('polymarket', 15000)
        
        assert tracker.virtual_balances['polymarket'] == 15000
        assert 'polymarket' in tracker.positions
    
    def test_update_balance(self):
        """Test balance updates"""
        tracker = PortfolioTracker()
        tracker.initialize_platform('polymarket', 10000)
        
        # Add money
        tracker.update_balance('polymarket', 500)
        assert tracker.virtual_balances['polymarket'] == 10500
        
        # Subtract money
        tracker.update_balance('polymarket', -200)
        assert tracker.virtual_balances['polymarket'] == 10300
    
    def test_update_position_buy(self):
        """Test position update for buy order"""
        tracker = PortfolioTracker()
        tracker.initialize_platform('polymarket', 10000)
        
        # Buy 100 shares at $0.50 each
        tracker.update_position('polymarket', 'market_1', 'YES', 100, 0.50, 'buy')
        
        # Check position
        position_key = 'market_1_YES'
        assert position_key in tracker.positions['polymarket']
        position = tracker.positions['polymarket'][position_key]
        assert position['shares'] == 100
        assert position['avg_price'] == 0.50
        assert position['total_cost'] == 50
        
        # Check balance reduction
        assert tracker.virtual_balances['polymarket'] == 9950  # 10000 - 50
        
        # Check trade history
        assert len(tracker.trade_history) == 1
        trade = tracker.trade_history[0]
        assert trade['action'] == 'buy'
        assert trade['shares'] == 100
        assert trade['price'] == 0.50
    
    def test_update_position_sell_partial(self):
        """Test position update for partial sell"""
        tracker = PortfolioTracker()
        tracker.initialize_platform('polymarket', 10000)
        
        # First buy 100 shares
        tracker.update_position('polymarket', 'market_1', 'YES', 100, 0.50, 'buy')
        
        # Then sell 40 shares at $0.60
        tracker.update_position('polymarket', 'market_1', 'YES', 40, 0.60, 'sell')
        
        # Check remaining position
        position_key = 'market_1_YES'
        position = tracker.positions['polymarket'][position_key]
        assert position['shares'] == 60  # 100 - 40
        assert position['avg_price'] == 0.50  # Same avg price
        
        # Check balance update
        # Started with 10000, spent 50 on buy, got 24 from sell
        assert tracker.virtual_balances['polymarket'] == 9974  # 10000 - 50 + 24
    
    def test_update_position_sell_complete(self):
        """Test position update for complete sell"""
        tracker = PortfolioTracker()
        tracker.initialize_platform('polymarket', 10000)
        
        # Buy 100 shares
        tracker.update_position('polymarket', 'market_1', 'YES', 100, 0.50, 'buy')
        
        # Sell all 100 shares at $0.70
        tracker.update_position('polymarket', 'market_1', 'YES', 100, 0.70, 'sell')
        
        # Check position is removed
        position_key = 'market_1_YES'
        assert position_key not in tracker.positions['polymarket']
        
        # Check balance (10000 - 50 + 70 = 10020)
        assert tracker.virtual_balances['polymarket'] == 10020
    
    def test_get_portfolio_summary(self):
        """Test portfolio summary generation"""
        tracker = PortfolioTracker()
        tracker.initialize_platform('polymarket', 10000)
        tracker.initialize_platform('kalshi', 8000)
        
        # Add some positions
        tracker.update_position('polymarket', 'market_1', 'YES', 100, 0.50, 'buy')
        tracker.update_position('kalshi', 'market_2', 'NO', 50, 0.40, 'buy')
        
        summary = tracker.get_portfolio_summary()
        
        # Check structure
        assert 'polymarket' in summary
        assert 'kalshi' in summary
        assert 'total_portfolio_value' in summary
        
        # Check polymarket data
        poly_data = summary['polymarket']
        assert poly_data['cash'] == 9950  # 10000 - 50
        assert poly_data['position_value'] == 50  # 100 * 0.50
        assert poly_data['total_value'] == 10000
        assert len(poly_data['positions']) == 1
        
        # Check kalshi data
        kalshi_data = summary['kalshi']
        assert kalshi_data['cash'] == 7980  # 8000 - 20
        assert kalshi_data['position_value'] == 20  # 50 * 0.40
        assert kalshi_data['total_value'] == 8000
        
        # Check total
        assert summary['total_portfolio_value'] == 18000
    
    def test_get_trade_history(self):
        """Test trade history retrieval"""
        tracker = PortfolioTracker()
        tracker.initialize_platform('polymarket', 10000)
        
        # Make several trades
        tracker.update_position('polymarket', 'market_1', 'YES', 100, 0.50, 'buy')
        tracker.update_position('polymarket', 'market_2', 'NO', 50, 0.30, 'buy')
        tracker.update_position('polymarket', 'market_1', 'YES', 30, 0.60, 'sell')
        
        # Get all history
        history = tracker.get_trade_history()
        assert len(history) == 3
        
        # Should be in reverse chronological order (most recent first)
        assert history[0]['action'] == 'sell'
        assert history[1]['action'] == 'buy'
        assert history[2]['action'] == 'buy'
        
        # Get limited history
        limited_history = tracker.get_trade_history(limit=2)
        assert len(limited_history) == 2
    
    def test_clear_position(self):
        """Test position clearing"""
        tracker = PortfolioTracker()
        tracker.initialize_platform('polymarket', 10000)
        
        # Create position
        tracker.update_position('polymarket', 'market_1', 'YES', 100, 0.50, 'buy')
        
        # Clear position
        position_key = 'market_1_YES'
        result = tracker.clear_position('polymarket', position_key)
        
        assert result is True
        assert position_key not in tracker.positions['polymarket']
        
        # Try to clear non-existent position
        result = tracker.clear_position('polymarket', 'nonexistent')
        assert result is False