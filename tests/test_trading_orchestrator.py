"""
Tests for the trading orchestrator - main coordination component
"""
import pytest
from unittest.mock import MagicMock, patch
from src.coordinators.trading_orchestrator import TradingOrchestrator


class TestTradingOrchestrator:
    """Test the main trading orchestrator"""
    
    @patch('src.coordinators.trading_orchestrator.load_dotenv')
    @patch('src.coordinators.trading_orchestrator.get_strategy')
    @patch('src.coordinators.trading_orchestrator.TradeExecutor')
    @patch('src.coordinators.trading_orchestrator.MarketDataCollector')
    @patch('src.coordinators.trading_orchestrator.TradingLogger')
    def test_orchestrator_initialization(self, mock_logger, mock_collector, 
                                       mock_executor, mock_strategy, mock_dotenv, patch_env_vars):
        """Test that orchestrator initializes all components correctly"""
        # Setup mocks
        mock_strategy.return_value = MagicMock()
        mock_executor.return_value = MagicMock()
        mock_collector.return_value = MagicMock()
        mock_logger.return_value = MagicMock()
        
        # Create orchestrator
        orchestrator = TradingOrchestrator()
        
        # Verify initialization
        assert orchestrator.min_volume == 1000.0
        assert orchestrator.min_spread == 0.05
        assert 'polymarket' in orchestrator.api_keys
        assert 'kalshi' in orchestrator.api_keys
        
        # Verify components were created
        mock_collector.assert_called_once()
        mock_logger.assert_called_once()
        mock_strategy.assert_called_once()
        mock_executor.assert_called_once()
    
    @patch('src.coordinators.trading_orchestrator.load_dotenv')
    @patch('src.coordinators.trading_orchestrator.get_strategy')
    @patch('src.coordinators.trading_orchestrator.TradeExecutor')
    @patch('src.coordinators.trading_orchestrator.MarketDataCollector')
    @patch('src.coordinators.trading_orchestrator.TradingLogger')
    def test_run_strategy_cycle_success(self, mock_logger, mock_collector, 
                                      mock_executor, mock_strategy, mock_dotenv, 
                                      patch_env_vars, mock_market_data):
        """Test successful strategy cycle execution"""
        # Setup mocks
        mock_strategy_instance = MagicMock()
        mock_strategy_instance.find_opportunities.return_value = [{'test': 'opportunity'}]
        mock_strategy.return_value = mock_strategy_instance
        
        mock_executor_instance = MagicMock()
        mock_executor_instance.execute_opportunities.return_value = [{'success': True}]
        mock_executor.return_value = mock_executor_instance
        
        mock_collector_instance = MagicMock()
        mock_collector_instance.collect_market_data.return_value = mock_market_data
        mock_collector.return_value = mock_collector_instance
        
        mock_logger_instance = MagicMock()
        mock_logger.return_value = mock_logger_instance
        
        # Create orchestrator and run cycle
        orchestrator = TradingOrchestrator()
        orchestrator.run_strategy_cycle()
        
        # Verify execution flow
        mock_collector_instance.collect_market_data.assert_called_once()
        mock_strategy_instance.find_opportunities.assert_called_once()
        mock_executor_instance.execute_opportunities.assert_called_once()
        mock_logger_instance.log_cycle_start.assert_called_once()
        mock_logger_instance.log_cycle_end.assert_called_once()
    
    @patch('src.coordinators.trading_orchestrator.load_dotenv')
    @patch('src.coordinators.trading_orchestrator.get_strategy')
    @patch('src.coordinators.trading_orchestrator.TradeExecutor')
    @patch('src.coordinators.trading_orchestrator.MarketDataCollector')
    @patch('src.coordinators.trading_orchestrator.TradingLogger')
    def test_run_strategy_cycle_no_opportunities(self, mock_logger, mock_collector, 
                                               mock_executor, mock_strategy, mock_dotenv, 
                                               patch_env_vars, mock_market_data):
        """Test strategy cycle with no opportunities found"""
        # Setup mocks
        mock_strategy_instance = MagicMock()
        mock_strategy_instance.find_opportunities.return_value = []  # No opportunities
        mock_strategy.return_value = mock_strategy_instance
        
        mock_executor_instance = MagicMock()
        mock_executor.return_value = mock_executor_instance
        
        mock_collector_instance = MagicMock()
        mock_collector_instance.collect_market_data.return_value = mock_market_data
        mock_collector.return_value = mock_collector_instance
        
        mock_logger_instance = MagicMock()
        mock_logger.return_value = mock_logger_instance
        
        # Create orchestrator and run cycle
        orchestrator = TradingOrchestrator()
        orchestrator.run_strategy_cycle()
        
        # Verify no execution attempt when no opportunities
        mock_executor_instance.execute_opportunities.assert_not_called()
    
    @patch('src.coordinators.trading_orchestrator.load_dotenv')
    @patch('src.coordinators.trading_orchestrator.get_strategy')
    @patch('src.coordinators.trading_orchestrator.TradeExecutor')
    @patch('src.coordinators.trading_orchestrator.MarketDataCollector')
    @patch('src.coordinators.trading_orchestrator.TradingLogger')
    def test_get_portfolio_summary(self, mock_logger, mock_collector, 
                                 mock_executor, mock_strategy, mock_dotenv, patch_env_vars):
        """Test portfolio summary retrieval"""
        # Setup mocks
        mock_executor_instance = MagicMock()
        mock_executor_instance.get_virtual_balances.return_value = {'polymarket': 10000, 'kalshi': 9500}
        mock_executor_instance.get_positions.return_value = {'polymarket': {}, 'kalshi': {}}
        mock_executor_instance.get_portfolio_value.return_value = 19500.0
        mock_executor.return_value = mock_executor_instance
        
        mock_strategy.return_value = MagicMock()
        mock_collector.return_value = MagicMock()
        mock_logger.return_value = MagicMock()
        
        # Create orchestrator and get summary
        orchestrator = TradingOrchestrator()
        summary = orchestrator.get_portfolio_summary()
        
        # Verify summary structure
        assert 'balances' in summary
        assert 'positions' in summary
        assert 'total_value' in summary
        assert summary['total_value'] == 19500.0


class TestBackwardCompatibility:
    """Test backward compatibility features"""
    
    def test_arbitrage_bot_alias(self):
        """Test that ArbitrageBot is properly aliased"""
        from src.coordinators.trading_orchestrator import ArbitrageBot, TradingOrchestrator
        assert ArbitrageBot is TradingOrchestrator
    
    def test_main_function_exists(self):
        """Test that main function is available for backward compatibility"""
        from src.coordinators.trading_orchestrator import main
        assert callable(main)