#!/usr/bin/env python3
"""
Test the new TradePlan execution system
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from src.types import (
    Market, Platform, Quote, Outcome, TradePlan, TradeLeg, LegType, OrderType,
    create_arbitrage_plan, ExecutionMode
)
from src.engine.executor import TradeExecutor
from datetime import datetime

def test_trade_plan_execution():
    """Test executing a TradePlan through the executor"""
    print("🧪 Testing TradePlan Execution System")
    print("=" * 50)
    
    # Create mock markets
    polymarket_quote_yes = Quote(price=0.35, volume=5000, liquidity=10000)
    polymarket_quote_no = Quote(price=0.65, volume=5000, liquidity=10000)
    
    polymarket_market = Market(
        id="poly_1",
        platform=Platform.POLYMARKET,
        title="Will Trump win the 2024 presidential election?",
        yes_quote=polymarket_quote_yes,
        no_quote=polymarket_quote_no,
        total_volume=10000,
        total_liquidity=20000
    )
    
    kalshi_quote_yes = Quote(price=0.58, volume=8000, liquidity=15000)
    kalshi_quote_no = Quote(price=0.42, volume=8000, liquidity=15000)
    
    kalshi_market = Market(
        id="kalshi_1",
        platform=Platform.KALSHI,
        title="Trump to win 2024 Presidential Election",
        yes_quote=kalshi_quote_yes,
        no_quote=kalshi_quote_no,
        total_volume=16000,
        total_liquidity=30000
    )
    
    # Create TradePlan using factory function
    plan = create_arbitrage_plan(
        plan_id="test_plan_001",
        buy_market=polymarket_market,
        sell_market=kalshi_market,
        outcome=Outcome.YES,
        buy_quantity=50,
        sell_quantity=50,
        buy_price=0.35,
        sell_price=0.58,
        name="Test Arbitrage Plan - Trump 2024"
    )
    
    print(f"📋 Created TradePlan:")
    print(f"   Plan ID: {plan.plan_id}")
    print(f"   Name: {plan.name}")
    print(f"   Strategy: {plan.strategy_type}")
    print(f"   Legs: {plan.num_legs}")
    print(f"   Capital Required: ${plan.total_capital_required:.2f}")
    print(f"   Expected Return: ${plan.expected_total_return:.2f} ({plan.expected_return_pct:.1f}%)")
    
    print(f"\n🔧 Plan Legs:")
    for i, leg in enumerate(plan.legs, 1):
        print(f"   {i}. {leg.leg_id} ({leg.leg_type.value})")
        print(f"      Market: [{leg.market.platform.value}] {leg.market.title[:40]}...")
        print(f"      Action: {leg.order_type.value.upper()} {leg.target_quantity} {leg.outcome.value} @ ${leg.target_price:.4f}")
        print(f"      Priority: {leg.priority}")
        if leg.dependency_legs:
            print(f"      Dependencies: {leg.dependency_legs}")
    
    # Initialize executor
    print(f"\n🚀 Initializing Executor...")
    api_keys = {
        'polymarket': 'test_key_poly',
        'kalshi': 'test_key_kalshi'
    }
    
    executor = TradeExecutor(api_keys, paper_trading=True)
    
    # Test the new place() method with TradePlan
    print(f"\n🎯 Executing Plan via place() method...")
    result = executor.place(plan)
    
    print(f"\n📊 Execution Result:")
    print(f"   Plan ID: {result.plan_id}")
    print(f"   Status: {result.status.value}")
    print(f"   Success: {result.is_successful}")
    print(f"   Executed Legs: {len(result.executed_legs)}")
    print(f"   Failed Legs: {len(result.failed_legs)}")
    print(f"   Total Profit: ${result.total_profit:.2f}")
    print(f"   Total Fees: ${result.total_fees:.2f}")
    print(f"   Net Profit: ${result.net_profit:.2f}")
    print(f"   Success Rate: {result.success_rate:.1f}%")
    print(f"   Execution Time: {result.execution_time_ms:.1f}ms")
    
    if result.error_messages:
        print(f"   Errors: {result.error_messages}")
    
    if result.warnings:
        print(f"   Warnings: {result.warnings}")
    
    # Test backwards compatibility - convert plan to opportunities
    print(f"\n🔄 Testing Backwards Compatibility...")
    opportunities = plan.to_opportunities()
    print(f"   Converted to {len(opportunities)} ArbitrageOpportunity objects")
    
    for i, opp in enumerate(opportunities, 1):
        print(f"   {i}. ID: {opp.id}")
        print(f"      Outcome: {opp.outcome.value}")
        print(f"      Buy: [{opp.buy_market.platform.value}] @ ${opp.buy_price:.4f}")
        print(f"      Sell: [{opp.sell_market.platform.value}] @ ${opp.sell_price:.4f}")
        print(f"      Expected Profit: ${opp.expected_profit:.2f}")
    
    # Test place() method with ArbitrageOpportunity
    if opportunities:
        print(f"\n🎯 Testing place() with ArbitrageOpportunity...")
        legacy_result = executor.place(opportunities[0])
        print(f"   Legacy Result Success: {legacy_result.get('success', False)}")
    
    print(f"\n✅ TradePlan execution test completed!")
    return result

if __name__ == "__main__":
    test_trade_plan_execution()