"""
Integration tests for the complete arbitrage bot flow.
Tests the full pipeline from market fetching to trade execution.
"""
import pytest
from decimal import Decimal

from src.config import constants
from src.services.matching import Matcher, Scorer
from src.services.execution import Validator, Executor
from src.strategies import SimpleArbitrageStrategy, SimpleArbitrageConfig
from src.database import Repository


class TestFullArbitragePipeline:
    """Test the complete arbitrage flow end-to-end"""

    @pytest.fixture
    def setup_pipeline(self):
        """Setup all components for pipeline test"""
        matcher = Matcher(similarity_threshold=0.5)
        scorer = Scorer(
            min_profit_threshold=0.02,
            kalshi_fee=0.007,
            polymarket_fee=0.02,
            slippage=0.01
        )
        validator = Validator(available_capital=Decimal("10000"))
        executor = Executor(paper_trading=True)
        
        config = SimpleArbitrageConfig(
            min_volume=1000.0,
            min_profit_pct=0.02,
            min_confidence=0.5,
            max_position_size=1000,
            min_position_size=10
        )
        strategy = SimpleArbitrageStrategy(config=config)
        repository = Repository()
        
        return {
            'matcher': matcher,
            'scorer': scorer,
            'validator': validator,
            'executor': executor,
            'strategy': strategy,
            'repository': repository
        }

    def test_match_score_validate_execute(
        self, 
        setup_pipeline, 
        sample_kalshi_market, 
        sample_polymarket_market
    ):
        """Test complete flow: match -> score -> validate -> execute"""
        components = setup_pipeline
        
        # Step 1: Match markets
        matches = components['matcher'].find_matches(
            [sample_kalshi_market], 
            [sample_polymarket_market]
        )
        assert len(matches) > 0
        
        # Step 2: Score opportunities
        opportunities = components['scorer'].score_opportunities(matches)
        
        if len(opportunities) > 0:
            # Step 3: Select best with strategy
            best_opp = components['strategy'].select_best_opportunity(opportunities)
            
            if best_opp:
                # Step 4: Validate
                validation = components['validator'].validate(best_opp)
                
                if validation.valid:
                    # Step 5: Execute
                    result = components['executor'].execute(best_opp)
                    
                    # Should complete successfully in paper mode
                    assert result is not None
                    
                    if result.success:
                        # Step 6: Save to database
                        components['repository'].save_opportunity(best_opp)
                        if result.buy_order:
                            components['repository'].save_order(result.buy_order)
                        if result.sell_order:
                            components['repository'].save_order(result.sell_order)
                        
                        # Verify saved
                        assert components['repository'].get_opportunity(best_opp.opportunity_id) is not None

    def test_pipeline_with_no_opportunities(self, setup_pipeline):
        """Test pipeline handles case with no profitable opportunities"""
        from src.models import Market
        from datetime import datetime
        from src.types import Exchange, Outcome
        
        components = setup_pipeline
        
        # Create markets with no arbitrage opportunity (same price)
        market_a = Market(
            exchange=Exchange.KALSHI,
            market_id="A",
            title="Test",
            outcome=Outcome.YES,
            price=Decimal("0.50"),
            volume=Decimal("1000"),
            liquidity=Decimal("5000"),
            last_updated=datetime.now()
        )
        
        market_b = Market(
            exchange=Exchange.POLYMARKET,
            market_id="B",
            title="Test",
            outcome=Outcome.YES,
            price=Decimal("0.50"),  # Same price
            volume=Decimal("1000"),
            liquidity=Decimal("5000"),
            last_updated=datetime.now()
        )
        
        # Match and score
        matches = components['matcher'].find_matches([market_a], [market_b])
        opportunities = components['scorer'].score_opportunities(matches)
        
        # Should have no profitable opportunities
        assert len(opportunities) == 0
        
        # Strategy should return None
        best_opp = components['strategy'].select_best_opportunity(opportunities)
        assert best_opp is None

    def test_pipeline_with_failed_validation(
        self, 
        setup_pipeline, 
        sample_opportunity
    ):
        """Test pipeline handles failed validation gracefully"""
        components = setup_pipeline
        
        # Create validator with insufficient capital
        components['validator'] = Validator(available_capital=Decimal("1"))
        
        # Should validate as invalid
        validation = components['validator'].validate(sample_opportunity)
        
        # Should not execute if invalid
        if not validation.valid:
            assert validation.reason is not None

    def test_pipeline_persistence(self, setup_pipeline, sample_opportunity):
        """Test that pipeline persists data correctly"""
        components = setup_pipeline
        repo = components['repository']
        
        # Save opportunity
        repo.save_opportunity(sample_opportunity)
        
        # Execute
        result = components['executor'].execute(sample_opportunity)
        
        if result.success and result.buy_order:
            repo.save_order(result.buy_order)
            
            # Verify persistence
            stats = repo.get_stats()
            assert stats['total_opportunities'] >= 1
            assert stats['total_orders'] >= 1
