"""
Tests for the types system
"""
import pytest
from datetime import datetime
from src.types import (
    Market, Quote, Platform, Outcome, ArbitrageOpportunity, Position,
    RiskLevel, PositionManagerConfig
)


class TestQuote:
    """Test Quote dataclass"""
    
    def test_quote_creation(self):
        """Test creating a quote"""
        quote = Quote(price=0.65, volume=1000, liquidity=500)
        
        assert quote.price == 0.65
        assert quote.volume == 1000
        assert quote.liquidity == 500
    
    def test_quote_validation(self):
        """Test quote price validation"""
        # Valid quote - should create successfully
        quote = Quote(price=0.5, volume=100, liquidity=50)
        assert quote.price == 0.5
        
        # Invalid quotes should raise during creation
        with pytest.raises(ValueError, match="Price must be between 0 and 1"):
            Quote(price=-0.1, volume=100, liquidity=50)
        
        with pytest.raises(ValueError, match="Price must be between 0 and 1"):
            Quote(price=1.5, volume=100, liquidity=50)


class TestMarket:
    """Test Market dataclass"""
    
    def test_market_creation(self):
        """Test creating a market"""
        yes_quote = Quote(price=0.65, volume=1000, liquidity=500)
        no_quote = Quote(price=0.35, volume=800, liquidity=400)
        
        market = Market(
            id="test_market_1",
            platform=Platform.POLYMARKET,
            title="Test Market",
            yes_quote=yes_quote,
            no_quote=no_quote,
            total_volume=1800,
            total_liquidity=900
        )
        
        assert market.id == "test_market_1"
        assert market.platform == Platform.POLYMARKET
        assert market.title == "Test Market"
        assert market.yes_quote.price == 0.65
        assert market.no_quote.price == 0.35
    
    def test_market_properties(self):
        """Test market calculated properties"""
        yes_quote = Quote(price=0.60, volume=1000, liquidity=500)
        no_quote = Quote(price=0.40, volume=800, liquidity=400)
        
        market = Market(
            id="test_market",
            platform=Platform.KALSHI,
            title="Test Market",
            yes_quote=yes_quote,
            no_quote=no_quote,
            total_volume=1800,
            total_liquidity=900
        )
        
        # Test calculated properties
        assert market.yes_price == 0.60
        assert market.no_price == 0.40
        # The spread formula is abs((yes_price + no_price) - 1.0)
        # 0.60 + 0.40 = 1.00, so |1.00 - 1.0| = 0.0
        assert market.spread == 0.0
    
    def test_market_to_dict(self):
        """Test converting market to dictionary"""
        yes_quote = Quote(price=0.55, volume=1000, liquidity=500)
        no_quote = Quote(price=0.45, volume=800, liquidity=400)
        
        market = Market(
            id="test_market",
            platform=Platform.POLYMARKET,
            title="Test Market",
            yes_quote=yes_quote,
            no_quote=no_quote,
            total_volume=1800,
            total_liquidity=900
        )
        
        market_dict = market.to_dict()
        
        assert market_dict['id'] == "test_market"
        assert market_dict['platform'] == "polymarket"
        assert market_dict['title'] == "Test Market"
        assert market_dict['yes_price'] == 0.55
        assert market_dict['no_price'] == 0.45
        assert market_dict['volume'] == 1800


class TestArbitrageOpportunity:
    """Test ArbitrageOpportunity dataclass"""
    
    def test_opportunity_creation(self):
        """Test creating an arbitrage opportunity"""
        # Create markets
        buy_market = Market(
            id="buy_market",
            platform=Platform.KALSHI,
            title="Test Market",
            yes_quote=Quote(price=0.40, volume=1000, liquidity=500),
            no_quote=Quote(price=0.60, volume=800, liquidity=400),
            total_volume=1800,
            total_liquidity=900
        )
        
        sell_market = Market(
            id="sell_market",
            platform=Platform.POLYMARKET,
            title="Test Market",
            yes_quote=Quote(price=0.60, volume=1200, liquidity=600),
            no_quote=Quote(price=0.40, volume=900, liquidity=450),
            total_volume=2100,
            total_liquidity=1050
        )
        
        opportunity = ArbitrageOpportunity(
            id="test_opp_1",
            buy_market=buy_market,
            sell_market=sell_market,
            outcome=Outcome.YES,
            buy_price=0.40,
            sell_price=0.65,
            spread=0.25,
            expected_profit_per_share=0.25,
            max_quantity=100,
            confidence_score=0.95,
            risk_level=RiskLevel.LOW
        )
        
        assert opportunity.id == "test_opp_1"
        assert opportunity.outcome == Outcome.YES
        assert opportunity.buy_price == 0.40
        assert opportunity.sell_price == 0.65
        assert opportunity.spread == 0.25
        assert opportunity.expected_profit_per_share == 0.25
        assert opportunity.confidence_score == 0.95
        assert opportunity.risk_level == RiskLevel.LOW
    
    def test_opportunity_properties(self):
        """Test opportunity calculated properties"""
        buy_market = Market(
            id="buy_market",
            platform=Platform.KALSHI,
            title="Test",
            yes_quote=Quote(price=0.40, volume=1000, liquidity=500),
            no_quote=Quote(price=0.60, volume=800, liquidity=400),
            total_volume=1800,
            total_liquidity=900
        )
        
        sell_market = Market(
            id="sell_market",
            platform=Platform.POLYMARKET,
            title="Test",
            yes_quote=Quote(price=0.65, volume=1200, liquidity=600),
            no_quote=Quote(price=0.35, volume=900, liquidity=450),
            total_volume=2100,
            total_liquidity=1050
        )
        
        opportunity = ArbitrageOpportunity(
            id="test_opp",
            buy_market=buy_market,
            sell_market=sell_market,
            outcome=Outcome.YES,
            buy_price=0.40,
            sell_price=0.65,
            spread=0.25,
            expected_profit_per_share=0.25,
            max_quantity=100,
            recommended_quantity=50
        )
        
        # Test expected profit calculation
        assert opportunity.expected_profit == 12.5  # 0.25 * 50
        
        # Test profitability
        assert opportunity.is_profitable is True
    
    def test_opportunity_to_legacy_dict(self):
        """Test converting opportunity to legacy dict format"""
        buy_market = Market(
            id="buy_market",
            platform=Platform.KALSHI,
            title="Test Market",
            yes_quote=Quote(price=0.40, volume=1000, liquidity=500),
            no_quote=Quote(price=0.60, volume=800, liquidity=400),
            total_volume=1800,
            total_liquidity=900
        )
        
        sell_market = Market(
            id="sell_market",
            platform=Platform.POLYMARKET,
            title="Test Market",
            yes_quote=Quote(price=0.60, volume=1200, liquidity=600),
            no_quote=Quote(price=0.40, volume=900, liquidity=450),
            total_volume=2100,
            total_liquidity=1050
        )
        
        opportunity = ArbitrageOpportunity(
            id="test_opp",
            buy_market=buy_market,
            sell_market=sell_market,
            outcome=Outcome.YES,
            buy_price=0.40,
            sell_price=0.65,
            spread=0.25,
            expected_profit_per_share=0.25,
            max_quantity=100
        )
        
        legacy_dict = opportunity.to_legacy_dict()
        
        assert legacy_dict['outcome'] == 'YES'
        assert legacy_dict['buy_price'] == 0.40
        assert legacy_dict['sell_price'] == 0.65
        assert legacy_dict['spread'] == 0.25
        assert legacy_dict['expected_profit'] == 0.25
        assert 'buy_market' in legacy_dict
        assert 'sell_market' in legacy_dict


class TestPosition:
    """Test Position dataclass"""
    
    def test_position_creation(self):
        """Test creating a position"""
        position = Position(
            position_id="pos_1",
            market_id="market_1",
            platform=Platform.POLYMARKET,
            outcome=Outcome.YES,
            quantity=100,
            average_price=0.50,
            current_price=0.60,
            total_cost=50.0
        )
        
        assert position.position_id == "pos_1"
        assert position.market_id == "market_1"
        assert position.platform == Platform.POLYMARKET
        assert position.outcome == Outcome.YES
        assert position.quantity == 100
        assert position.average_price == 0.50
        assert position.current_price == 0.60
        assert position.total_cost == 50.0
    
    def test_position_calculated_properties(self):
        """Test position calculated properties"""
        position = Position(
            position_id="pos_1",
            market_id="market_1",
            platform=Platform.POLYMARKET,
            outcome=Outcome.YES,
            quantity=100,
            average_price=0.50,
            current_price=0.60,
            total_cost=50.0,
            max_potential_price=0.80
        )
        
        # Test market value
        assert position.market_value == 60.0  # 100 * 0.60
        
        # Test unrealized P&L
        assert position.unrealized_pnl == 10.0  # 60 - 50
        
        # Test unrealized P&L percentage
        assert position.unrealized_pnl_pct == 20.0  # (10 / 50) * 100
        
        # Test potential remaining gain percentage
        expected_remaining = ((0.80 - 0.60) / 0.60) * 100
        assert abs(position.potential_remaining_gain_pct - expected_remaining) < 0.01


class TestEnums:
    """Test enum types"""
    
    def test_platform_enum(self):
        """Test Platform enum"""
        assert Platform.POLYMARKET.value == "polymarket"
        assert Platform.KALSHI.value == "kalshi"
        
        # Test creation from string
        assert Platform("polymarket") == Platform.POLYMARKET
        assert Platform("kalshi") == Platform.KALSHI
    
    def test_outcome_enum(self):
        """Test Outcome enum"""
        assert Outcome.YES.value == "YES"
        assert Outcome.NO.value == "NO"
        
        # Test creation from string
        assert Outcome("YES") == Outcome.YES
        assert Outcome("NO") == Outcome.NO
    
    def test_risk_level_enum(self):
        """Test RiskLevel enum"""
        assert RiskLevel.LOW.value == "low"
        assert RiskLevel.MEDIUM.value == "medium"
        assert RiskLevel.HIGH.value == "high"


class TestPositionManagerConfig:
    """Test PositionManagerConfig dataclass"""
    
    def test_config_defaults(self):
        """Test default configuration values"""
        config = PositionManagerConfig()
        
        assert config.max_open_positions == 10
        assert config.min_swap_threshold_pct == 5.0
        assert config.position_size_pct == 0.05
        assert config.min_remaining_gain_pct == 2.0
        assert config.force_close_threshold_pct == -10.0
        assert config.max_hold_time_hours == 24
    
    def test_config_custom_values(self):
        """Test custom configuration values"""
        config = PositionManagerConfig(
            max_open_positions=5,
            min_swap_threshold_pct=3.0,
            position_size_pct=0.10,
            min_remaining_gain_pct=1.0,
            force_close_threshold_pct=-15.0,
            max_hold_time_hours=72
        )
        
        assert config.max_open_positions == 5
        assert config.min_swap_threshold_pct == 3.0
        assert config.position_size_pct == 0.10
        assert config.min_remaining_gain_pct == 1.0
        assert config.force_close_threshold_pct == -15.0
        assert config.max_hold_time_hours == 72