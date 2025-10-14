#!/usr/bin/env python3
"""
Combined demo to show both arbitrage and expiry strategies working together
"""

import sys
import os
from datetime import datetime, timedelta

# Add the current directory to Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from main import ArbitrageBot

def create_comprehensive_mock_data():
    """Create mock data that works for both arbitrage and expiry strategies"""
    current_time = datetime.now()
    
    # Polymarket markets
    polymarket_markets = [
        {
            'id': 'poly_election_2024',
            'title': 'Will Donald Trump win the 2024 US Presidential Election?',
            'platform': 'polymarket',
            'volume': 5000000,
            'yes_price': 0.52,  # For arbitrage
            'no_price': 0.48,
            'close_time': current_time + timedelta(days=45),  # Too far for expiry strategy
            'raw_data': {}
        },
        {
            'id': 'poly_fed_meeting',
            'title': 'Will the Fed cut rates at next FOMC meeting?',
            'platform': 'polymarket',
            'volume': 3000000,
            'yes_price': 0.89,  # Very high - good for expiry strategy
            'no_price': 0.11,
            'close_time': current_time + timedelta(days=2),  # Soon expiry
            'raw_data': {}
        },
        {
            'id': 'poly_btc_short_term',
            'title': 'Bitcoin above $70k this week?',
            'platform': 'polymarket',
            'volume': 2000000,
            'yes_price': 0.51,  # Very uncertain - good for expiry strategy
            'no_price': 0.49,
            'close_time': current_time + timedelta(days=4),
            'raw_data': {}
        }
    ]
    
    # Manifold markets (with slight price differences for arbitrage)
    manifold_markets = [
        {
            'id': 'mani_trump_2024',
            'title': 'Trump wins 2024 Presidential Election',
            'platform': 'manifold',
            'volume': 1500000,
            'yes_price': 0.48,  # Lower than Polymarket - arbitrage opportunity!
            'no_price': 0.52,
            'close_time': current_time + timedelta(days=45),
            'raw_data': {}
        },
        {
            'id': 'mani_fed_rates',
            'title': 'Federal Reserve cuts rates at upcoming meeting',
            'platform': 'manifold',
            'volume': 1800000,
            'yes_price': 0.85,  # Slightly different but still high
            'no_price': 0.15,
            'close_time': current_time + timedelta(days=2),
            'raw_data': {}
        },
        {
            'id': 'mani_btc_week',
            'title': 'BTC hits $70k+ before Friday',
            'platform': 'manifold',
            'volume': 900000,
            'yes_price': 0.08,  # Very low - good for expiry strategy
            'no_price': 0.92,
            'close_time': current_time + timedelta(days=3),
            'raw_data': {}
        }
    ]
    
    return {
        'polymarket': polymarket_markets,
        'manifold': manifold_markets
    }

def demo_multi_strategy():
    """Demonstrate both strategies working together"""
    print("🚀 Multi-Strategy Trading Bot Demo")
    print("=" * 70)
    
    # Mock the bot's data collection
    print("\n📊 Mock Market Data:")
    markets_data = create_comprehensive_mock_data()
    current_time = datetime.now()
    
    for platform, markets in markets_data.items():
        print(f"\n{platform.upper()}:")
        for market in markets:
            time_to_expiry = market['close_time'] - current_time
            days_to_expiry = time_to_expiry.days
            
            print(f"  • {market['title'][:50]}...")
            print(f"    YES: {market['yes_price']:.3f}, NO: {market['no_price']:.3f}")
            print(f"    Volume: ${market['volume']:,.0f}, Expires in: {days_to_expiry} days")
    
    # Create bot and override its data collection method for demo
    class MockBot(ArbitrageBot):
        def collect_market_data(self):
            return markets_data
    
    # Initialize bot
    bot = MockBot()
    
    # Run strategy cycle
    print(f"\n🎯 Running All Strategies:")
    print("=" * 50)
    
    # Manually run each strategy for detailed output
    from strategies import ArbitrageStrategy, ExpiryStrategy
    
    arbitrage_strategy = ArbitrageStrategy(min_spread=0.03)
    expiry_strategy = ExpiryStrategy(max_days_to_expiry=7, min_volume=1000)
    
    print(f"\n1️⃣ ARBITRAGE STRATEGY")
    print("-" * 30)
    arb_opportunities = arbitrage_strategy.find_opportunities(markets_data)
    
    if arb_opportunities:
        print(f"Found {len(arb_opportunities)} arbitrage opportunities:")
        for i, opp in enumerate(arb_opportunities):
            print(f"\n  #{i+1}: {opp['outcome']} spread")
            print(f"    Buy:  [{opp['buy_market']['platform']}] {opp['buy_market']['title'][:40]}...")
            print(f"    Sell: [{opp['sell_market']['platform']}] {opp['sell_market']['title'][:40]}...")
            print(f"    Spread: {opp['spread']:.4f} ({opp['spread']*100:.2f}%)")
            print(f"    Profit: ${opp['expected_profit']:.4f}")
    else:
        print("  No arbitrage opportunities found")
    
    print(f"\n2️⃣ EXPIRY STRATEGY")
    print("-" * 30)
    expiry_opportunities = expiry_strategy.find_opportunities(markets_data)
    
    if expiry_opportunities:
        print(f"Found {len(expiry_opportunities)} expiry-based opportunities:")
        for i, opp in enumerate(expiry_opportunities):
            market = opp['market']
            print(f"\n  #{i+1}: {opp['subtype'].replace('_', ' ').title()}")
            print(f"    Market: {market['title'][:45]}...")
            print(f"    Platform: {market['platform']}")
            print(f"    Expires: {opp['days_to_expiry']:.1f} days")
            print(f"    Price: YES {opp['yes_price']:.3f}")
            print(f"    Score: {opp['final_score']:.3f}")
            print(f"    Action: {opp['recommended_action'][:50]}...")
    else:
        print("  No expiry opportunities found")
    
    # Combined results
    all_opportunities = arb_opportunities + expiry_opportunities
    
    print(f"\n📊 COMBINED RESULTS")
    print("-" * 30)
    print(f"Total opportunities: {len(all_opportunities)}")
    
    if all_opportunities:
        # Add strategy type and sort by profit
        for opp in arb_opportunities:
            opp['strategy_type'] = 'Arbitrage'
        for opp in expiry_opportunities:
            opp['strategy_type'] = 'Expiry'
        
        all_opportunities.sort(key=lambda x: x.get('expected_profit', 0), reverse=True)
        
        print(f"\nTop opportunities by expected profit:")
        for i, opp in enumerate(all_opportunities[:5]):
            strategy_type = opp['strategy_type']
            profit = opp.get('expected_profit', 0)
            print(f"  {i+1}. [{strategy_type}] ${profit:.4f} expected profit")
    
    print(f"\n🎉 Multi-Strategy Demo Completed!")
    print(f"\nThe bot successfully:")
    print(f"  ✅ Collected market data from multiple platforms")
    print(f"  ✅ Ran arbitrage strategy to find price differences")
    print(f"  ✅ Ran expiry strategy to find time-sensitive opportunities")
    print(f"  ✅ Combined and ranked all opportunities by profitability")
    print(f"  ✅ Ready to execute the most profitable trades")
    
    return all_opportunities

if __name__ == "__main__":
    demo_multi_strategy()