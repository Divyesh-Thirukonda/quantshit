"""
Tests for execution components
"""
from unittest.mock import MagicMock, patch
from src.executors.order_executor import OrderExecutor
from src.coordinators.execution_coordinator import ExecutionCoordinator


class TestOrderExecutor:
    """Test the order executor"""
    
    def test_initialization(self, mock_api_keys, patch_get_market_api):
        """Test executor initialization"""
        executor = OrderExecutor(mock_api_keys)
        
        assert len(executor.apis) == 2
        assert 'polymarket' in executor.apis
        assert 'kalshi' in executor.apis
    
    def test_execute_buy_order_success(self, mock_api_keys, patch_get_market_api):
        """Test successful buy order execution"""
        executor = OrderExecutor(mock_api_keys)
        
        # Mock successful API response
        with patch.object(executor.apis['polymarket'], 'place_buy_order', return_value={
            'success': True,
            'order_id': 'buy_123'
        }):
            result = executor.execute_buy_order('polymarket', 'market_1', 'YES', 100, 0.50)
        
            # Verify result
            assert result['success'] is True
            assert result['platform'] == 'polymarket'
            assert result['action'] == 'buy'
            assert result['amount'] == 100
            assert result['price'] == 0.50
    
    def test_execute_sell_order_success(self, mock_api_keys, patch_get_market_api):
        """Test successful sell order execution"""
        executor = OrderExecutor(mock_api_keys)
        
        # Mock successful API response
        with patch.object(executor.apis['kalshi'], 'place_sell_order', return_value={
            'success': True,
            'order_id': 'sell_456'
        }):
            result = executor.execute_sell_order('kalshi', 'market_2', 'NO', 50, 0.75)
        
        # Verify result
        assert result['success'] is True
        assert result['platform'] == 'kalshi'
        assert result['action'] == 'sell'
        assert result['amount'] == 50
        assert result['price'] == 0.75
    
    def test_execute_order_api_failure(self, mock_api_keys, patch_get_market_api):
        """Test handling of API failure"""
        executor = OrderExecutor(mock_api_keys)
        
        # Mock API failure
        with patch.object(executor.apis['polymarket'], 'place_buy_order', return_value={
            'success': False,
            'error': 'Insufficient funds'
        }):
            result = executor.execute_buy_order('polymarket', 'market_1', 'YES', 100, 0.50)
        
        assert result['success'] is False
    
    def test_execute_order_platform_unavailable(self, mock_api_keys, patch_get_market_api):
        """Test handling of unavailable platform"""
        executor = OrderExecutor(mock_api_keys)
        
        result = executor.execute_buy_order('nonexistent', 'market_1', 'YES', 100, 0.50)
        
        assert result['success'] is False
        assert 'not available' in result['error']
    
    def test_execute_arbitrage_legs_success(self, mock_api_keys, patch_get_market_api):
        """Test successful arbitrage leg execution"""
        executor = OrderExecutor(mock_api_keys)
        
        # Mock successful responses for both legs
        with patch.object(executor.apis['polymarket'], 'place_buy_order', return_value={'success': True}), \
             patch.object(executor.apis['kalshi'], 'place_sell_order', return_value={'success': True}):
            
            buy_details = {
                'platform': 'polymarket',
                'market_id': 'market_1',
                'outcome': 'YES',
                'amount': 100,
                'price': 0.40
            }
        
        sell_details = {
            'platform': 'kalshi',
            'market_id': 'market_2',
            'outcome': 'YES',
            'amount': 100,
            'price': 0.60
        }
        
        result = executor.execute_arbitrage_legs(buy_details, sell_details)
        
        assert result['success'] is True
        assert result['buy_result']['success'] is True
        assert result['sell_result']['success'] is True
    
    def test_execute_arbitrage_legs_partial_failure(self, mock_api_keys, patch_get_market_api):
        """Test arbitrage with one leg failing"""
        executor = OrderExecutor(mock_api_keys)
        
        # Mock one success, one failure
        with patch.object(executor.apis['polymarket'], 'place_buy_order', return_value={'success': True}), \
             patch.object(executor.apis['kalshi'], 'place_sell_order', return_value={'success': False, 'error': 'Market closed'}):
            
            buy_details = {
                'platform': 'polymarket',
                'market_id': 'market_1',
                'outcome': 'YES',
                'amount': 100,
                'price': 0.40
            }
            
            sell_details = {
                'platform': 'kalshi',
                'market_id': 'market_2',
                'outcome': 'YES',
                'amount': 100,
                'price': 0.60
            }
            
            result = executor.execute_arbitrage_legs(buy_details, sell_details)
            
            assert result['success'] is False
            assert 'Sell failed' in result['error']


class TestExecutionCoordinator:
    """Test the execution coordinator"""
    
    @patch('src.coordinators.execution_coordinator.OrderExecutor')
    @patch('src.coordinators.execution_coordinator.PortfolioTracker')
    @patch('src.coordinators.execution_coordinator.PositionManager')
    def test_initialization(self, mock_position_manager, mock_portfolio_tracker,
                           mock_order_executor, mock_api_keys):
        """Test coordinator initialization"""
        # Mock the tracker to have a proper virtual_balances dict
        mock_tracker_instance = MagicMock()
        mock_tracker_instance.virtual_balances = {'polymarket': 10000.0, 'kalshi': 10000.0}
        mock_portfolio_tracker.return_value = mock_tracker_instance
        
        coordinator = ExecutionCoordinator(mock_api_keys)        # Verify components were created
        mock_order_executor.assert_called_once()
        mock_portfolio_tracker.assert_called_once()
        mock_position_manager.assert_called_once()
    
    @patch('src.coordinators.execution_coordinator.OrderExecutor')
    @patch('src.coordinators.execution_coordinator.PortfolioTracker')
    @patch('src.coordinators.execution_coordinator.PositionManager')
    def test_get_portfolio_value(self, mock_position_manager_class, mock_portfolio_tracker_class,
                                mock_order_executor, mock_api_keys):
        """Test portfolio value calculation"""
        # Setup mocks
        mock_portfolio_tracker = MagicMock()
        mock_portfolio_tracker.get_virtual_balances.return_value = {'polymarket': 10000, 'kalshi': 9500}
        mock_portfolio_tracker.virtual_balances = {'polymarket': 10000.0, 'kalshi': 9500.0}
        mock_portfolio_tracker_class.return_value = mock_portfolio_tracker

        mock_position_manager = MagicMock()
        mock_position_manager.get_active_positions.return_value = []
        mock_position_manager_class.return_value = mock_position_manager

        coordinator = ExecutionCoordinator(mock_api_keys)
        
        portfolio_value = coordinator.get_portfolio_value()
        
        assert portfolio_value == 19500.0  # 10000 + 9500