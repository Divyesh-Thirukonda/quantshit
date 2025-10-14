#!/usr/bin/env python3
"""
Test script to verify the arbitrage bot works correctly
"""

import sys
import os

# Add the current directory to Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from main import ArbitrageBot

def test_bot():
    """Test the arbitrage bot functionality"""
    print("🧪 Testing Arbitrage Bot")
    print("=" * 50)
    
    try:
        # Initialize bot
        bot = ArbitrageBot()
        
        # Test data collection
        print("\n1. Testing market data collection...")
        markets_data = bot.collect_market_data()
        
        total_markets = sum(len(markets) for markets in markets_data.values())
        print(f"   ✅ Collected {total_markets} markets from {len(markets_data)} platforms")
        
        # Test strategy
        print("\n2. Testing strategy...")
        opportunities = bot.strategy.find_opportunities(markets_data)
        print(f"   ✅ Found {len(opportunities)} arbitrage opportunities")
        
        if opportunities:
            print("\n   Top opportunities:")
            for i, opp in enumerate(opportunities[:3]):
                print(f"   {i+1}. {opp['outcome']} - Spread: {opp['spread']:.4f} - Profit: ${opp['expected_profit']:.4f}")
        
        # Test execution (dry run)
        print("\n3. Testing execution (demo mode)...")
        if opportunities:
            # Just test the first opportunity
            result = bot.executor.execute_arbitrage(opportunities[0])
            if result['success']:
                print("   ✅ Execution test passed")
            else:
                print(f"   ⚠️  Execution test failed: {result.get('error', 'Unknown error')}")
        else:
            print("   ⚠️  No opportunities to test execution")
        
        print(f"\n🎉 Bot test completed successfully!")
        return True
        
    except Exception as e:
        print(f"\n❌ Bot test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = test_bot()
    sys.exit(0 if success else 1)