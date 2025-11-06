"""
Tests for database repository.
"""
import pytest

from src.database import Repository


class TestRepository:
    """Test Repository for data persistence"""

    @pytest.fixture
    def repo(self):
        """Create a fresh repository instance for each test"""
        return Repository()

    def test_save_and_get_opportunity(self, repo, sample_opportunity):
        """Test saving and retrieving an opportunity"""
        repo.save_opportunity(sample_opportunity)
        
        opportunities = repo.get_opportunities()
        assert len(opportunities) >= 1
        
        retrieved = repo.get_opportunity(sample_opportunity.opportunity_id)
        assert retrieved is not None
        assert retrieved.opportunity_id == sample_opportunity.opportunity_id

    def test_save_and_get_order(self, repo, sample_order):
        """Test saving and retrieving an order"""
        repo.save_order(sample_order)
        
        orders = repo.get_orders()
        assert len(orders) >= 1
        
        retrieved = repo.get_order(sample_order.order_id)
        assert retrieved is not None
        assert retrieved.order_id == sample_order.order_id

    def test_save_and_get_position(self, repo, sample_position):
        """Test saving and retrieving a position"""
        repo.save_position(sample_position)
        
        positions = repo.get_positions()
        assert len(positions) >= 1
        
        retrieved = repo.get_position(sample_position.position_id)
        assert retrieved is not None
        assert retrieved.position_id == sample_position.position_id

    def test_delete_position(self, repo, sample_position):
        """Test deleting a position"""
        repo.save_position(sample_position)
        
        # Verify it exists
        assert repo.get_position(sample_position.position_id) is not None
        
        # Delete it
        repo.delete_position(sample_position.position_id)
        
        # Verify it's gone
        assert repo.get_position(sample_position.position_id) is None

    def test_get_stats(self, repo, sample_opportunity, sample_order):
        """Test getting repository statistics"""
        repo.save_opportunity(sample_opportunity)
        repo.save_order(sample_order)
        
        stats = repo.get_stats()
        
        assert 'total_opportunities' in stats
        assert 'total_orders' in stats
        assert 'total_positions' in stats
        assert stats['total_opportunities'] >= 1
        assert stats['total_orders'] >= 1

    def test_isolation_between_instances(self):
        """Test that different repository instances are isolated"""
        repo1 = Repository()
        repo2 = Repository()
        
        from src.models import Opportunity
        from datetime import datetime
        from decimal import Decimal
        from src.types import Outcome
        
        # Create test opportunity
        opp = Opportunity(
            opportunity_id="ISOLATION-TEST",
            market_kalshi=None,
            market_polymarket=None,
            outcome=Outcome.YES,
            price_difference=Decimal("0.05"),
            expected_profit=Decimal("30.00"),
            expected_profit_pct=Decimal("0.05"),
            confidence_score=0.85,
            discovered_at=datetime.now()
        )
        
        repo1.save_opportunity(opp)
        
        # Should not be in repo2
        assert repo2.get_opportunity("ISOLATION-TEST") is None
