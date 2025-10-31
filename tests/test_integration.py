"""
Integration tests for the full arbitrage workflow.
Tests end-to-end flow from market data fetching to trade execution.
"""
import pytest
from datetime import datetime, timedelta
from unittest.mock import Mock, patch, MagicMock

from src.types import Exchange, OrderSide, OrderStatus, MarketStatus, Outcome
from src.models import Market, Order, Opportunity
from src.services.matching.matcher import Matcher
from src.services.matching.scorer import Scorer
from src.services.execution.validator import Validator
from src.services.execution.executor import Executor
from src.strategies.simple_arb import SimpleArbitrageStrategy
from src.database.repository import Repository


@pytest.mark.integration
class TestFullArbitrageWorkflow:
    """Test the complete arbitrage workflow from end to end"""

    def test_complete_workflow_with_profitable_opportunity(
        self,
        mock_kalshi_client,
        mock_polymarket_client,
        in_memory_repository
    ):
        """Test full workflow: fetch markets -> match -> score -> validate -> execute"""

        # Step 1: Setup mock exchange clients with overlapping markets
        kalshi_markets = [
            Market(
                id="k_btc_100k",
                exchange=Exchange.KALSHI,
                title="Bitcoin to reach $100,000 by end of 2025",
                yes_price=0.40,  # Cheaper
                no_price=0.60,
                volume=100000.0,
                liquidity=50000.0,
                status=MarketStatus.OPEN,
                expiry=datetime(2025, 12, 31)
            )
        ]

        poly_markets = [
            Market(
                id="p_btc_100k",
                exchange=Exchange.POLYMARKET,
                title="Bitcoin reaches $100k by December 2025",
                yes_price=0.50,  # More expensive - arbitrage opportunity!
                no_price=0.50,
                volume=150000.0,
                liquidity=75000.0,
                status=MarketStatus.OPEN,
                expiry=datetime(2025, 12, 31)
            )
        ]

        mock_kalshi_client.get_markets.return_value = kalshi_markets
        mock_polymarket_client.get_markets.return_value = poly_markets

        # Step 2: Match markets
        matcher = Matcher(similarity_threshold=0.5)
        matched_pairs = matcher.find_matches(kalshi_markets, poly_markets)

        assert len(matched_pairs) > 0, "Should find at least one matching market pair"
        kalshi_market, poly_market, confidence = matched_pairs[0]
        assert confidence > 0.5

        # Step 3: Score opportunities
        scorer = Scorer()
        opportunities = scorer.score_opportunities(matched_pairs)

        assert len(opportunities) > 0, "Should find profitable opportunities"
        best_opp = opportunities[0]
        assert best_opp.is_profitable
        assert best_opp.expected_profit > 0

        # Step 4: Filter and rank with strategy
        strategy = SimpleArbitrageStrategy()
        filtered_opportunities = strategy.filter_opportunities(opportunities)
        ranked_opportunities = strategy.rank_opportunities(filtered_opportunities)

        assert len(ranked_opportunities) > 0, "Should have opportunities after filtering"
        best_opportunity = ranked_opportunities[0]

        # Step 5: Validate opportunity
        validator = Validator(available_capital=10000.0)
        validation_result = validator.validate(best_opportunity)

        assert validation_result.valid, f"Opportunity should be valid: {validation_result.reason}"

        # Step 6: Execute trades (mocked)
        executor = Executor(
            kalshi_client=mock_kalshi_client,
            polymarket_client=mock_polymarket_client,
            repository=in_memory_repository
        )

        # Mock the order placement to return successful orders
        mock_kalshi_client.place_order.return_value = Order(
            order_id="k_order_001",
            market_id=kalshi_markets[0].id,
            exchange=Exchange.KALSHI,
            side=OrderSide.BUY,
            quantity=100,
            price=0.40,
            status=OrderStatus.FILLED,
            timestamp=datetime.now(),
            filled_at=datetime.now()
        )

        mock_polymarket_client.place_order.return_value = Order(
            order_id="p_order_001",
            market_id=poly_markets[0].id,
            exchange=Exchange.POLYMARKET,
            side=OrderSide.SELL,
            quantity=100,
            price=0.50,
            status=OrderStatus.FILLED,
            timestamp=datetime.now(),
            filled_at=datetime.now()
        )

        # Execute the opportunity
        result = executor.execute(best_opportunity)

        # Verify execution
        assert result.success
        assert result.buy_order is not None
        assert result.sell_order is not None
        assert result.buy_order.status == OrderStatus.FILLED
        assert result.sell_order.status == OrderStatus.FILLED

        # Verify orders were placed
        mock_kalshi_client.place_order.assert_called_once()
        mock_polymarket_client.place_order.assert_called_once()

    def test_workflow_with_no_opportunities(
        self,
        mock_kalshi_client,
        mock_polymarket_client
    ):
        """Test workflow when no profitable opportunities exist"""

        # Markets with no arbitrage opportunity (same prices)
        kalshi_markets = [
            Market(
                id="k_1",
                exchange=Exchange.KALSHI,
                title="Test market",
                yes_price=0.50,
                no_price=0.50,
                volume=10000.0,
                liquidity=5000.0,
                status=MarketStatus.OPEN
            )
        ]

        poly_markets = [
            Market(
                id="p_1",
                exchange=Exchange.POLYMARKET,
                title="Test market",
                yes_price=0.50,  # Same price - no arbitrage
                no_price=0.50,
                volume=10000.0,
                liquidity=5000.0,
                status=MarketStatus.OPEN
            )
        ]

        mock_kalshi_client.get_markets.return_value = kalshi_markets
        mock_polymarket_client.get_markets.return_value = poly_markets

        # Match and score
        matcher = Matcher()
        matched_pairs = matcher.find_matches(kalshi_markets, poly_markets)

        scorer = Scorer()
        opportunities = scorer.score_opportunities(matched_pairs)

        # Filter for profitable ones
        strategy = SimpleArbitrageStrategy()
        filtered = strategy.filter_opportunities(opportunities)

        # Should have no profitable opportunities after filtering
        assert len(filtered) == 0

    def test_workflow_rejects_invalid_opportunity(
        self,
        mock_kalshi_client,
        mock_polymarket_client
    ):
        """Test that invalid opportunities are rejected by validator"""

        # Create opportunity with closed market
        closed_market = Market(
            id="k_closed",
            exchange=Exchange.KALSHI,
            title="Closed market",
            yes_price=0.95,
            no_price=0.05,
            volume=10000.0,
            liquidity=0.0,
            status=MarketStatus.CLOSED,  # Closed!
            expiry=datetime.now() - timedelta(days=1)
        )

        poly_market = Market(
            id="p_open",
            exchange=Exchange.POLYMARKET,
            title="Closed market",
            yes_price=0.90,
            no_price=0.10,
            volume=10000.0,
            liquidity=5000.0,
            status=MarketStatus.OPEN
        )

        invalid_opp = Opportunity(
            market_kalshi=closed_market,
            market_polymarket=poly_market,
            outcome=Outcome.YES,
            spread=0.05,
            expected_profit=100.0,
            expected_profit_pct=0.05,
            confidence_score=0.9,
            recommended_size=100,
            max_size=500
        )

        # Validate
        validator = Validator(available_capital=10000.0)
        result = validator.validate(invalid_opp)

        # Should be rejected
        assert result.valid is False
        assert "closed" in result.reason.lower()


@pytest.mark.integration
class TestErrorHandling:
    """Test error handling throughout the workflow"""

    def test_handles_exchange_api_failure(self, mock_kalshi_client):
        """Test graceful handling of exchange API failures"""
        # Simulate API failure
        mock_kalshi_client.get_markets.side_effect = Exception("API Error")

        # Should not crash, return empty list
        try:
            markets = mock_kalshi_client.get_markets()
            assert False, "Should have raised exception"
        except Exception as e:
            assert "API Error" in str(e)

    def test_handles_invalid_market_data(self):
        """Test handling of malformed market data"""
        matcher = Matcher()

        # Pass empty lists
        matches = matcher.find_matches([], [])
        assert matches == []

    def test_handles_scorer_edge_cases(self):
        """Test scorer handles edge cases gracefully"""
        scorer = Scorer()

        # Empty matched pairs
        opportunities = scorer.score_opportunities([])
        assert opportunities == []


@pytest.mark.integration
class TestRepositoryIntegration:
    """Test integration with repository for data persistence"""

    def test_save_and_retrieve_opportunities(self, in_memory_repository):
        """Test saving and retrieving opportunities"""
        kalshi_market = Market(
            id="k1",
            exchange=Exchange.KALSHI,
            title="Test",
            yes_price=0.40,
            no_price=0.60,
            volume=10000.0,
            liquidity=5000.0,
            status=MarketStatus.OPEN
        )

        poly_market = Market(
            id="p1",
            exchange=Exchange.POLYMARKET,
            title="Test",
            yes_price=0.50,
            no_price=0.50,
            volume=10000.0,
            liquidity=5000.0,
            status=MarketStatus.OPEN
        )

        opp = Opportunity(
            market_kalshi=kalshi_market,
            market_polymarket=poly_market,
            outcome=Outcome.YES,
            spread=0.10,
            expected_profit=200.0,
            expected_profit_pct=0.05,
            confidence_score=0.9,
            recommended_size=100,
            max_size=500
        )

        # Save opportunity
        in_memory_repository.save_opportunity(opp)

        # Retrieve opportunities
        opportunities = in_memory_repository.get_opportunities()
        assert len(opportunities) > 0

    def test_save_and_retrieve_orders(self, in_memory_repository):
        """Test saving and retrieving orders"""
        order = Order(
            order_id="test_order",
            market_id="test_market",
            exchange=Exchange.KALSHI,
            side=OrderSide.BUY,
            quantity=100,
            price=0.50,
            status=OrderStatus.FILLED,
            timestamp=datetime.now(),
            filled_at=datetime.now()
        )

        # Save order
        in_memory_repository.save_order(order)

        # Retrieve orders
        orders = in_memory_repository.get_orders()
        assert len(orders) > 0
        assert orders[0].order_id == "test_order"


@pytest.mark.integration
@pytest.mark.slow
class TestPerformance:
    """Test performance with larger datasets"""

    def test_matcher_performance_with_many_markets(self):
        """Test matcher handles many markets efficiently"""
        # Create 100 markets on each exchange
        kalshi_markets = [
            Market(
                id=f"k_{i}",
                exchange=Exchange.KALSHI,
                title=f"Market {i % 10}",  # Some overlap
                yes_price=0.50,
                no_price=0.50,
                volume=10000.0,
                liquidity=5000.0,
                status=MarketStatus.OPEN
            )
            for i in range(100)
        ]

        poly_markets = [
            Market(
                id=f"p_{i}",
                exchange=Exchange.POLYMARKET,
                title=f"Market {i % 10}",  # Some overlap
                yes_price=0.50,
                no_price=0.50,
                volume=10000.0,
                liquidity=5000.0,
                status=MarketStatus.OPEN
            )
            for i in range(100)
        ]

        # Should complete in reasonable time
        matcher = Matcher()
        import time
        start = time.time()
        matches = matcher.find_matches(kalshi_markets, poly_markets)
        duration = time.time() - start

        assert duration < 5.0, "Matching should complete within 5 seconds"
        assert len(matches) > 0, "Should find some matches"
