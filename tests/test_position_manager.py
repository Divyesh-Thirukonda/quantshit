"""
Tests for position management
"""
from unittest.mock import MagicMock
from datetime import datetime, timedelta
from src.engine.position_manager import PositionManager
from src.types import Position, PositionManagerConfig, Platform, Outcome, ArbitrageOpportunity


class TestPositionManager:
    """Test the position manager"""
    
    def test_initialization(self):
        """Test position manager initialization"""
        config = PositionManagerConfig(max_open_positions=5)
        manager = PositionManager(config)
        
        assert manager.config.max_open_positions == 5
        assert len(manager.active_positions) == 0
    
    def test_has_capacity(self):
        """Test capacity checking"""
        config = PositionManagerConfig(max_open_positions=2)
        manager = PositionManager(config)
        
        # Initially has capacity
        assert manager.has_capacity() is True
        
        # Add one position
        position1 = Position(
            position_id="pos_1",
            market_id="market_1",
            platform=Platform.POLYMARKET,
            outcome=Outcome.YES,
            quantity=100,
            average_price=0.50,
            current_price=0.50,
            total_cost=50
        )
        manager.add_position(position1)
        
        # Still has capacity
        assert manager.has_capacity() is True
        assert manager.get_position_count() == 1
        
        # Add second position
        position2 = Position(
            position_id="pos_2",
            market_id="market_2",
            platform=Platform.KALSHI,
            outcome=Outcome.NO,
            quantity=50,
            average_price=0.40,
            current_price=0.40,
            total_cost=20
        )
        manager.add_position(position2)
        
        # Now at capacity
        assert manager.has_capacity() is False
        assert manager.get_position_count() == 2
    
    def test_add_remove_position(self):
        """Test adding and removing positions"""
        config = PositionManagerConfig()
        manager = PositionManager(config)
        
        position = Position(
            position_id="pos_1",
            market_id="market_1",
            platform=Platform.POLYMARKET,
            outcome=Outcome.YES,
            quantity=100,
            average_price=0.50,
            current_price=0.55,
            total_cost=50
        )
        
        # Add position
        manager.add_position(position)
        assert manager.get_position_count() == 1
        assert "pos_1" in manager.active_positions
        
        # Remove position
        removed = manager.remove_position("pos_1")
        assert removed is not None
        assert removed.position_id == "pos_1"
        assert manager.get_position_count() == 0
        
        # Try to remove non-existent position
        removed = manager.remove_position("nonexistent")
        assert removed is None
    
    def test_get_worst_performing_position(self):
        """Test finding worst performing position"""
        config = PositionManagerConfig()
        manager = PositionManager(config)
        
        # Add positions with different performance
        position1 = Position(
            position_id="pos_1",
            market_id="market_1",
            platform=Platform.POLYMARKET,
            outcome=Outcome.YES,
            quantity=100,
            average_price=0.50,
            current_price=0.60,  # Good performance
            total_cost=50,
            max_potential_price=0.80
        )
        
        position2 = Position(
            position_id="pos_2",
            market_id="market_2",
            platform=Platform.KALSHI,
            outcome=Outcome.NO,
            quantity=50,
            average_price=0.40,
            current_price=0.42,  # Poor performance
            total_cost=20,
            max_potential_price=0.70
        )
        
        manager.add_position(position1)
        manager.add_position(position2)
        
        worst = manager.get_worst_performing_position()
        # The algorithm picks based on remaining gain percentage
        # Position 1: (0.80 - 0.60) / (0.80 - 0.50) = 0.20/0.30 = 66.7%
        # Position 2: (0.70 - 0.42) / (0.70 - 0.40) = 0.28/0.30 = 93.3%
        # Position 1 has lower remaining gain percentage, so it should be worst
        assert worst.position_id == "pos_1"
    
    def test_calculate_position_size(self):
        """Test position size calculation"""
        config = PositionManagerConfig(position_size_pct=0.05)  # 5% of portfolio
        manager = PositionManager(config)
        
        # Mock opportunity
        opportunity = MagicMock()
        opportunity.buy_price = 0.50
        opportunity.max_quantity = 1000
        
        # Calculate size for $20,000 portfolio
        size = manager.calculate_position_size(opportunity, 20000.0)
        
        # Should be 5% of 20000 = 1000, divided by 0.50 = 2000 shares
        # But capped at max_quantity of 1000
        assert size == 1000
    
    def test_should_swap_position_with_capacity(self):
        """Test swap decision when there's still capacity"""
        config = PositionManagerConfig(max_open_positions=5)
        manager = PositionManager(config)
        
        # Add one position (still has capacity)
        position = Position(
            position_id="pos_1",
            market_id="market_1",
            platform=Platform.POLYMARKET,
            outcome=Outcome.YES,
            quantity=100,
            average_price=0.50,
            current_price=0.50,
            total_cost=50
        )
        manager.add_position(position)
        
        # Mock opportunity
        opportunity = MagicMock()
        opportunity.expected_profit_per_share = 0.20
        opportunity.buy_price = 0.50
        
        should_swap, position_to_swap = manager.should_swap_position(opportunity)
        
        # Should not swap when there's capacity
        assert should_swap is False
        assert position_to_swap is None
    
    def test_should_swap_position_at_capacity(self):
        """Test swap decision when at capacity"""
        config = PositionManagerConfig(max_open_positions=1, min_swap_threshold_pct=5.0)
        manager = PositionManager(config)
        
        # Add position at capacity
        position = Position(
            position_id="pos_1",
            market_id="market_1",
            platform=Platform.POLYMARKET,
            outcome=Outcome.YES,
            quantity=100,
            average_price=0.50,
            current_price=0.52,  # Small gain
            total_cost=50,
            max_potential_price=0.55  # Low potential
        )
        manager.add_position(position)
        
        # Mock much better opportunity
        opportunity = MagicMock()
        opportunity.expected_profit_per_share = 0.25  # 25 cents profit
        opportunity.buy_price = 0.40  # 62.5% potential return
        
        should_swap, position_to_swap = manager.should_swap_position(opportunity)
        
        # Should swap for much better opportunity
        assert should_swap is True
        assert position_to_swap is not None
        assert position_to_swap.position_id == "pos_1"


class TestPositionManagerConfig:
    """Test position manager configuration"""
    
    def test_default_config(self):
        """Test default configuration values"""
        config = PositionManagerConfig()
        
        assert config.max_open_positions == 10
        assert config.min_swap_threshold_pct == 5.0
        assert config.position_size_pct == 0.05
        assert config.min_remaining_gain_pct == 2.0
        assert config.force_close_threshold_pct == -10.0
        assert config.max_hold_time_hours == 24  # 1 day
    
    def test_custom_config(self):
        """Test custom configuration"""
        config = PositionManagerConfig(
            max_open_positions=5,
            min_swap_threshold_pct=3.0,
            position_size_pct=0.10
        )
        
        assert config.max_open_positions == 5
        assert config.min_swap_threshold_pct == 3.0
        assert config.position_size_pct == 0.10