"""
Tests for strategy components
"""
from unittest.mock import MagicMock, patch
from src.strategies.arbitrage import ArbitrageStrategy, get_strategy
from src.types import Market, ArbitrageOpportunity, Platform, Outcome


class TestArbitrageStrategy:
    """Test the arbitrage strategy"""
    
    def test_strategy_initialization(self):
        """Test strategy initialization with parameters"""
        strategy = ArbitrageStrategy(min_spread=0.03)
        
        assert strategy.name == "Arbitrage Strategy"
        assert strategy.min_spread == 0.03
        assert strategy.use_planning is False
    
    def test_find_opportunities_single_platform(self, mock_market_data):
        """Test that no opportunities are found with single platform"""
        strategy = ArbitrageStrategy(min_spread=0.01)
        
        # Only one platform
        single_platform_data = {'polymarket': mock_market_data['polymarket']}
        
        opportunities = strategy.find_opportunities(single_platform_data)
        
        assert len(opportunities) == 0
    
    def test_find_opportunities_with_arbitrage(self, mock_market_data):
        """Test finding arbitrage opportunities between platforms"""
        strategy = ArbitrageStrategy(min_spread=0.01)
        
        # Modify test data to create arbitrage opportunity
        test_data = {
            'polymarket': [
                {
                    'id': 'poly_1',
                    'title': 'Will Trump win 2024',
                    'yes_price': 0.40,  # Lower YES price
                    'no_price': 0.60,
                    'volume': 5000,
                    'platform': 'polymarket'
                }
            ],
            'kalshi': [
                {
                    'id': 'kalshi_1', 
                    'title': 'Will Trump win 2024',
                    'yes_price': 0.65,  # Higher YES price - arbitrage opportunity!
                    'no_price': 0.35,
                    'volume': 4000,
                    'platform': 'kalshi'
                }
            ]
        }
        
        opportunities = strategy.find_opportunities(test_data)
        
        # Should find at least one opportunity
        assert len(opportunities) > 0
        
        # Check first opportunity
        opp = opportunities[0]
        assert isinstance(opp, ArbitrageOpportunity)
        assert opp.spread >= strategy.min_spread
        assert opp.expected_profit_per_share > 0
    
    def test_find_opportunities_no_matches(self):
        """Test no opportunities when markets don't match"""
        strategy = ArbitrageStrategy(min_spread=0.01)
        
        # Different market titles - no matches
        test_data = {
            'polymarket': [
                {
                    'id': 'poly_1',
                    'title': 'Will Trump win 2024',
                    'yes_price': 0.50,
                    'no_price': 0.50,
                    'volume': 5000,
                    'platform': 'polymarket'
                }
            ],
            'kalshi': [
                {
                    'id': 'kalshi_1',
                    'title': 'Will Biden win 2024',  # Different title
                    'yes_price': 0.50,
                    'no_price': 0.50,
                    'volume': 4000,
                    'platform': 'kalshi'
                }
            ]
        }
        
        opportunities = strategy.find_opportunities(test_data)
        
        assert len(opportunities) == 0
    
    def test_are_markets_similar(self):
        """Test market similarity detection"""
        strategy = ArbitrageStrategy()
        
        # Similar titles should match (need >50% word overlap after removing stop words)
        assert strategy._are_markets_similar(
            "Trump win 2024 election",
            "Trump wins 2024 election"
        ) is True
        
        # Different titles should not match
        assert strategy._are_markets_similar(
            "Will Trump win 2024",
            "Will Biden win 2024"
        ) is False
        
        # Very different titles should not match
        assert strategy._are_markets_similar(
            "Stock market goes up",
            "Trump wins election"
        ) is False
    
    def test_calculate_arbitrage(self):
        """Test arbitrage calculation between two markets"""
        strategy = ArbitrageStrategy(min_spread=0.01)
        
        market1 = {
            'id': 'market1',
            'title': 'Test Market',
            'yes_price': 0.40,
            'no_price': 0.60,
            'volume': 5000,
            'platform': 'polymarket'
        }
        
        market2 = {
            'id': 'market2',
            'title': 'Test Market',
            'yes_price': 0.65,  # Higher YES price
            'no_price': 0.35,   # Lower NO price
            'volume': 4000,
            'platform': 'kalshi'
        }
        
        opportunities = strategy._calculate_arbitrage(market1, market2)
        
        # Should find both YES and NO arbitrage
        assert len(opportunities) == 2
        
        # Check YES arbitrage
        yes_opp = next(opp for opp in opportunities if opp['outcome'] == 'YES')
        assert yes_opp['buy_price'] == 0.40  # Buy from market1
        assert yes_opp['sell_price'] == 0.65  # Sell on market2
        assert yes_opp['expected_profit'] == 0.25
        
        # Check NO arbitrage
        no_opp = next(opp for opp in opportunities if opp['outcome'] == 'NO')
        assert no_opp['buy_price'] == 0.35  # Buy from market2
        assert no_opp['sell_price'] == 0.60  # Sell on market1
        assert no_opp['expected_profit'] == 0.25


class TestStrategyFactory:
    """Test strategy factory function"""
    
    def test_get_strategy_arbitrage(self):
        """Test getting arbitrage strategy from factory"""
        strategy = get_strategy('arbitrage', min_spread=0.02)
        
        assert isinstance(strategy, ArbitrageStrategy)
        assert strategy.min_spread == 0.02
    
    def test_get_strategy_invalid(self):
        """Test getting invalid strategy raises error"""
        try:
            get_strategy('nonexistent')
            assert False, "Should have raised exception"
        except ValueError as e:
            assert "Unsupported strategy" in str(e)