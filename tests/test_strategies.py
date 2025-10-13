"""
Test configuration and sample strategies.
"""
import pytest
import asyncio
from datetime import datetime, timedelta
from src.strategies.cross_platform import CrossPlatformArbitrageStrategy
from src.strategies.correlation import CorrelationArbitrageStrategy
from src.data.providers import MarketData, MarketStatus


@pytest.fixture
def sample_market_data():
    """Create sample market data for testing."""
    return {
        "kalshi": [
            MarketData(
                platform="kalshi",
                market_id="KALSHI_ELECTION_001",
                title="Will Biden win the 2024 election?",
                category="politics",
                yes_price=0.65,
                no_price=0.35,
                volume=1000.0,
                close_date=datetime.utcnow() + timedelta(days=30),
                status=MarketStatus.ACTIVE
            ),
            MarketData(
                platform="kalshi",
                market_id="KALSHI_SPORTS_001",
                title="Will Lakers win NBA championship?",
                category="sports",
                yes_price=0.42,
                no_price=0.58,
                volume=800.0,
                close_date=datetime.utcnow() + timedelta(days=60),
                status=MarketStatus.ACTIVE
            )
        ],
        "polymarket": [
            MarketData(
                platform="polymarket",
                market_id="POLY_ELECTION_001",
                title="Biden 2024 Election Winner",
                category="politics",
                yes_price=0.68,
                no_price=0.32,
                volume=1200.0,
                close_date=datetime.utcnow() + timedelta(days=30),
                status=MarketStatus.ACTIVE
            )
        ]
    }


@pytest.mark.asyncio
async def test_cross_platform_strategy(sample_market_data):
    """Test cross-platform arbitrage strategy."""
    strategy = CrossPlatformArbitrageStrategy()
    
    # Test signal generation
    signals = await strategy.analyze_markets(sample_market_data)
    
    # Should detect arbitrage opportunity between Biden markets
    assert len(signals) > 0
    
    # Test opportunity detection
    opportunities = await strategy.find_opportunities(sample_market_data)
    
    assert len(opportunities) > 0
    assert opportunities[0].opportunity_type == "cross_platform"


@pytest.mark.asyncio
async def test_correlation_strategy():
    """Test correlation arbitrage strategy."""
    strategy = CorrelationArbitrageStrategy()
    
    # Create sample data with single platform
    single_platform_data = {
        "kalshi": [
            MarketData(
                platform="kalshi",
                market_id="KALSHI_CORR_A",
                title="Market A",
                yes_price=0.60,
                volume=500.0,
                status=MarketStatus.ACTIVE
            ),
            MarketData(
                platform="kalshi",
                market_id="KALSHI_CORR_B",
                title="Market B",
                yes_price=0.45,
                volume=400.0,
                status=MarketStatus.ACTIVE
            )
        ]
    }
    
    # Test with limited data (should not generate signals due to insufficient history)
    signals = await strategy.analyze_markets(single_platform_data)
    opportunities = await strategy.find_opportunities(single_platform_data)
    
    # With no price history, should not generate signals
    assert len(signals) == 0
    assert len(opportunities) == 0


def test_strategy_configuration():
    """Test strategy configuration."""
    config = {
        "min_spread": 0.05,
        "max_position_size": 500.0,
        "similarity_threshold": 0.9
    }
    
    strategy = CrossPlatformArbitrageStrategy(config)
    
    assert strategy.min_spread == 0.05
    assert strategy.max_position_size == 500.0
    assert strategy.similarity_threshold == 0.9


def test_strategy_status():
    """Test strategy status reporting."""
    strategy = CrossPlatformArbitrageStrategy()
    
    status = strategy.get_status()
    
    assert "name" in status
    assert "status" in status
    assert status["name"] == "cross_platform_arbitrage"


if __name__ == "__main__":
    pytest.main([__file__])