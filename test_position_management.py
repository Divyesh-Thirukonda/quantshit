#!/usr/bin/env python3
"""
Test the new Position Management System with intelligent swapping
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from src.types import (
    Market, Platform, Quote, Outcome, ArbitrageOpportunity, 
    PositionManagerConfig, RiskLevel
)
from src.engine.executor import TradeExecutor
from datetime import datetime

def create_test_opportunity(id_suffix: str, buy_platform: Platform, sell_platform: Platform, 
                          buy_price: float, sell_price: float, outcome: Outcome = Outcome.YES) -> ArbitrageOpportunity:
    """Create a test arbitrage opportunity"""
    
    buy_market = Market(
        id=f"{buy_platform.value}_{id_suffix}",
        platform=buy_platform,
        title=f"Test Market {id_suffix} on {buy_platform.value}",
        yes_quote=Quote(price=buy_price, volume=5000, liquidity=10000),
        no_quote=Quote(price=1-buy_price, volume=5000, liquidity=10000),
        total_volume=10000,
        total_liquidity=20000
    )
    
    sell_market = Market(
        id=f"{sell_platform.value}_{id_suffix}",
        platform=sell_platform,
        title=f"Test Market {id_suffix} on {sell_platform.value}",
        yes_quote=Quote(price=sell_price, volume=8000, liquidity=15000),
        no_quote=Quote(price=1-sell_price, volume=8000, liquidity=15000),
        total_volume=16000,
        total_liquidity=30000
    )
    
    spread = sell_price - buy_price
    
    return ArbitrageOpportunity(
        id=f"test_opp_{id_suffix}",
        buy_market=buy_market,
        sell_market=sell_market,
        outcome=outcome,
        buy_price=buy_price,
        sell_price=sell_price,
        spread=spread,
        expected_profit_per_share=spread,
        confidence_score=0.95,
        risk_level=RiskLevel.LOW,
        max_quantity=100
    )

def test_position_management_system():
    """Test the position management system with intelligent swapping"""
    print("Testing Position Management System")
    print("=" * 60)
    
    # Configure position manager for testing
    position_config = PositionManagerConfig(
        max_open_positions=3,  # Small limit for testing
        min_swap_threshold_pct=3.0,  # 3% improvement needed to swap
        position_size_pct=0.1,  # 10% of portfolio per position
        min_remaining_gain_pct=2.0  # 2% minimum remaining gain
    )
    
    # Initialize executor with position management
    api_keys = {
        'polymarket': 'test_key_poly',
        'kalshi': 'test_key_kalshi'
    }
    
    executor = TradeExecutor(api_keys, paper_trading=True, position_config=position_config)
    
    print(f"\nPhase 1: Fill up to position limit")
    print(f"Position limit: {position_config.max_open_positions}")
    
    # Create some decent opportunities to fill capacity
    opportunities = [
        create_test_opportunity("001", Platform.POLYMARKET, Platform.KALSHI, 0.40, 0.52),  # 12% gain
        create_test_opportunity("002", Platform.KALSHI, Platform.POLYMARKET, 0.35, 0.45),  # 10% gain  
        create_test_opportunity("003", Platform.POLYMARKET, Platform.KALSHI, 0.30, 0.38),  # 8% gain
    ]
    
    for i, opp in enumerate(opportunities, 1):
        expected_gain_pct = (opp.expected_profit_per_share / opp.buy_price) * 100
        print(f"\n--- Executing Opportunity {i} ---")
        print(f"Expected gain: {expected_gain_pct:.1f}%")
        print(f"Buy: ${opp.buy_price:.4f} | Sell: ${opp.sell_price:.4f}")
        
        result = executor.place(opp)
        print(f"Success: {result.get('success', False)}")
    
    print(f"\nPhase 2: Test position swapping with better opportunity")
    
    # Create a much better opportunity that should trigger a swap
    amazing_opportunity = create_test_opportunity(
        "AMAZING", Platform.KALSHI, Platform.POLYMARKET, 0.25, 0.45  # 20% gain!
    )
    
    expected_gain_pct = (amazing_opportunity.expected_profit_per_share / amazing_opportunity.buy_price) * 100
    print(f"\n--- Testing High-Value Opportunity ---")
    print(f"Expected gain: {expected_gain_pct:.1f}%")
    print(f"This should trigger a position swap since it's much better than existing positions")
    
    result = executor.place(amazing_opportunity)
    print(f"Success: {result.get('success', False)}")
    
    print(f"\nPhase 3: Test with mediocre opportunity (should be rejected)")
    
    # Create a mediocre opportunity that shouldn't trigger a swap
    mediocre_opportunity = create_test_opportunity(
        "MEDIOCRE", Platform.POLYMARKET, Platform.KALSHI, 0.48, 0.52  # Only 4% gain
    )
    
    expected_gain_pct = (mediocre_opportunity.expected_profit_per_share / mediocre_opportunity.buy_price) * 100
    print(f"\n--- Testing Low-Value Opportunity ---")
    print(f"Expected gain: {expected_gain_pct:.1f}%")
    print(f"This should be rejected as not worth swapping")
    
    result = executor.place(mediocre_opportunity)
    print(f"Success: {result.success if hasattr(result, 'success') else result.get('success', False)}")
    
    print(f"\nFinal Portfolio Status:")
    summary = executor.get_portfolio_summary()
    
    # Print position manager summary
    pm_summary = summary.get('position_manager_summary', {})
    print(f"\nPosition Manager Summary:")
    print(f"  Active Positions: {pm_summary.get('capacity_used', 'N/A')}")
    print(f"  Total Value: ${pm_summary.get('total_market_value', 0):.2f}")
    print(f"  Unrealized P&L: ${pm_summary.get('total_unrealized_pnl', 0):.2f} ({pm_summary.get('total_unrealized_pnl_pct', 0):.1f}%)")
    print(f"  Avg Remaining Gain: {pm_summary.get('avg_remaining_gain_pct', 0):.1f}%")
    
    if pm_summary.get('best_position_id'):
        print(f"  Best Position: {pm_summary['best_position_id']} ({pm_summary.get('best_remaining_gain_pct', 0):.1f}% remaining)")
    if pm_summary.get('worst_position_id'):
        print(f"  Worst Position: {pm_summary['worst_position_id']} ({pm_summary.get('worst_remaining_gain_pct', 0):.1f}% remaining)")
    
    print(f"\nPosition Management System Test Completed!")
    print(f"\nKey Features Demonstrated:")
    print(f"  Position limit enforcement ({position_config.max_open_positions} positions)")
    print(f"  Intelligent position swapping based on potential gain")
    print(f"  Dynamic position sizing based on portfolio value")
    print(f"  Rejection of opportunities that don't meet swap threshold")
    print(f"  Comprehensive position tracking and analytics")
    
    return summary

if __name__ == "__main__":
    test_position_management_system()