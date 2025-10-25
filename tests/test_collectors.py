"""
Tests for data collection components
"""
from unittest.mock import MagicMock, patch
from src.collectors.market_data_collector import MarketDataCollector


class TestMarketDataCollector:
    """Test the market data collector"""
    
    def test_initialization(self, mock_api_keys, patch_get_market_api):
        """Test collector initialization with API keys"""
        collector = MarketDataCollector(mock_api_keys)
        
        # Verify APIs were initialized
        assert len(collector.apis) == 2
        assert 'polymarket' in collector.apis
        assert 'kalshi' in collector.apis
    
    def test_collect_market_data_success(self, mock_api_keys, mock_market_data, patch_get_market_api):
        """Test successful market data collection"""
        collector = MarketDataCollector(mock_api_keys)
        
        # Mock API responses using patch_get_market_api
        with patch.object(collector.apis['polymarket'], 'get_recent_markets', return_value=mock_market_data['polymarket']), \
             patch.object(collector.apis['kalshi'], 'get_recent_markets', return_value=mock_market_data['kalshi']):
            
            # Collect data
            result = collector.collect_market_data(min_volume=1000)
        
            # Verify result structure
            assert 'polymarket' in result
            assert 'kalshi' in result
            assert len(result['polymarket']) == 2
            assert len(result['kalshi']) == 2
    
    def test_collect_platform_data_api_error(self, mock_api_keys, patch_get_market_api):
        """Test handling of API errors during data collection"""
        collector = MarketDataCollector(mock_api_keys)
        
        # Mock API to raise exception
        with patch.object(collector.apis['polymarket'], 'get_recent_markets', side_effect=Exception("API Error")):
            with patch.object(collector.apis['kalshi'], 'get_recent_markets', return_value=[]):
                # Collect data
                result = collector.collect_market_data(min_volume=1000)
        
        # Verify error handling
        assert result['polymarket'] == []  # Empty due to error
        assert result['kalshi'] == []  # Empty but no error
    
    def test_get_available_platforms(self, mock_api_keys, patch_get_market_api):
        """Test getting list of available platforms"""
        collector = MarketDataCollector(mock_api_keys)
        
        platforms = collector.get_available_platforms()
        
        assert 'polymarket' in platforms
        assert 'kalshi' in platforms
        assert len(platforms) == 2
    
    def test_is_platform_available(self, mock_api_keys, patch_get_market_api):
        """Test checking if specific platform is available"""
        collector = MarketDataCollector(mock_api_keys)
        
        assert collector.is_platform_available('polymarket') is True
        assert collector.is_platform_available('kalshi') is True
        assert collector.is_platform_available('nonexistent') is False