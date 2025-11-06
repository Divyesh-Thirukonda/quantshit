"""
Tests for monitoring services (Tracker, Alerter).
"""
import pytest
from decimal import Decimal

from src.services.monitoring import Tracker, Alerter


class TestTracker:
    """Test Tracker service for position monitoring"""

    @pytest.fixture
    def tracker(self):
        """Create tracker instance"""
        return Tracker()

    def test_add_position(self, tracker, sample_position):
        """Test adding a position to tracker"""
        tracker.add_position(sample_position)
        
        positions = tracker.get_positions()
        assert len(positions) >= 1

    def test_update_position(self, tracker, sample_position):
        """Test updating position with current prices"""
        tracker.add_position(sample_position)
        
        # Update with new prices
        tracker.update_position(
            sample_position.position_id,
            current_price_kalshi=Decimal("0.70"),
            current_price_polymarket=Decimal("0.62")
        )
        
        # Position should be updated
        positions = tracker.get_positions()
        assert len(positions) >= 1

    def test_get_summary(self, tracker, sample_position):
        """Test getting portfolio summary"""
        tracker.add_position(sample_position)
        
        summary = tracker.get_summary()
        
        assert 'total_positions' in summary
        assert 'total_unrealized_pnl' in summary
        assert 'total_realized_pnl' in summary
        assert summary['total_positions'] >= 1

    def test_remove_position(self, tracker, sample_position):
        """Test removing a position"""
        tracker.add_position(sample_position)
        
        # Verify it exists
        positions = tracker.get_positions()
        assert len(positions) >= 1
        
        # Remove it
        tracker.remove_position(sample_position.position_id)
        
        # Should have fewer positions
        positions_after = tracker.get_positions()
        assert len(positions_after) < len(positions)


class TestAlerter:
    """Test Alerter service for notifications"""

    @pytest.fixture
    def alerter_enabled(self):
        """Create alerter with alerts enabled"""
        return Alerter(enabled=True)

    @pytest.fixture
    def alerter_disabled(self):
        """Create alerter with alerts disabled"""
        return Alerter(enabled=False)

    def test_alert_trade_executed_enabled(self, alerter_enabled):
        """Test trade execution alert when enabled"""
        # Should not crash
        alerter_enabled.alert_trade_executed(
            profit=Decimal("30.00"),
            market_title="Test Market",
            success=True
        )

    def test_alert_trade_executed_disabled(self, alerter_disabled):
        """Test trade execution alert when disabled"""
        # Should not crash and do nothing
        alerter_disabled.alert_trade_executed(
            profit=Decimal("30.00"),
            market_title="Test Market",
            success=True
        )

    def test_alert_error_enabled(self, alerter_enabled):
        """Test error alert when enabled"""
        # Should not crash
        alerter_enabled.alert_error(
            error="Test error",
            context="Test context"
        )

    def test_alert_error_disabled(self, alerter_disabled):
        """Test error alert when disabled"""
        # Should not crash and do nothing
        alerter_disabled.alert_error(
            error="Test error",
            context="Test context"
        )

    def test_alert_opportunity_found(self, alerter_enabled, sample_opportunity):
        """Test opportunity alert"""
        # Should not crash
        alerter_enabled.alert_opportunity_found(sample_opportunity)
