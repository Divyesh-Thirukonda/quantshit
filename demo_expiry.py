#!/usr/bin/env python3
"""
Demo script to show how the expiry strategy works with mock data
"""

import sys
import os
from datetime import datetime, timedelta

# Add the current directory to Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from strategies import ExpiryStrategy

def create_mock_expiry_markets():
    """Create mock market data with different expiry dates"""
    
    current_time = datetime.now()
    
    markets = [
        {
            'id': 'market_1_day',
            'title': 'Will the Federal Reserve cut rates in the next FOMC meeting?',
            'platform': 'polymarket',
            'volume': 5000000,
            'yes_price': 0.92,  # Very high confidence - might be overconfident
            'no_price': 0.08,
            'close_time': current_time + timedelta(days=1),  # 1 day to expiry
            'raw_data': {}
        },
        {
            'id': 'market_3_days',
            'title': 'Bitcoin above $70k by Friday?',
            'platform': 'manifold',
            'volume': 2500000,
            'yes_price': 0.12,  # Very low - might be undervalued
            'no_price': 0.88,
            'close_time': current_time + timedelta(days=3),  # 3 days to expiry
            'raw_data': {}
        },
        {
            'id': 'market_5_days',
            'title': 'Will there be a major tech announcement this week?',
            'platform': 'polymarket',
            'volume': 1800000,
            'yes_price': 0.49,  # Very uncertain - 50/50
            'no_price': 0.51,
            'close_time': current_time + timedelta(days=5),  # 5 days to expiry
            'raw_data': {}
        },
        {
            'id': 'market_12_hours',
            'title': 'Stock market up tomorrow?',
            'platform': 'manifold',
            'volume': 800000,
            'yes_price': 0.87,  # High confidence, very short time
            'no_price': 0.13,
            'close_time': current_time + timedelta(hours=12),  # 12 hours to expiry
            'raw_data': {}
        },
        {
            'id': 'market_6_hours',
            'title': 'Will it rain in NYC today?',
            'platform': 'polymarket',
            'volume': 300000,  # Low volume - should be filtered out
            'yes_price': 0.51,
            'no_price': 0.49,
            'close_time': current_time + timedelta(hours=6),
            'raw_data': {}
        },
        {
            'id': 'market_30_days',
            'title': 'Election outcome by end of month?',
            'platform': 'manifold',
            'volume': 10000000,
            'yes_price': 0.55,
            'no_price': 0.45,
            'close_time': current_time + timedelta(days=30),  # Too far out
            'raw_data': {}
        }
    ]
    
    return {'polymarket': [m for m in markets if m['platform'] == 'polymarket'],
            'manifold': [m for m in markets if m['platform'] == 'manifold']}

def demo_expiry_strategy():
    """Demonstrate the expiry strategy with mock data"""
    print("⏰ Expiry Strategy Demo")
    print("=" * 60)
    
    # Create mock market data
    print("\n📊 Mock Markets with Different Expiry Times:")
    markets_data = create_mock_expiry_markets()
    current_time = datetime.now()
    
    all_markets = []
    for platform, markets in markets_data.items():
        all_markets.extend(markets)
    
    # Sort by expiry time for display
    all_markets.sort(key=lambda x: x['close_time'])
    
    for market in all_markets:
        time_to_expiry = market['close_time'] - current_time
        hours_to_expiry = time_to_expiry.total_seconds() / 3600
        days_to_expiry = time_to_expiry.days
        
        print(f"\n• {market['title'][:50]}...")
        print(f"  Platform: {market['platform']}, Volume: ${market['volume']:,.0f}")
        print(f"  YES: {market['yes_price']:.3f}, NO: {market['no_price']:.3f}")
        if days_to_expiry > 0:
            print(f"  Expires in: {days_to_expiry} days {int(hours_to_expiry % 24)} hours")
        else:
            print(f"  Expires in: {int(hours_to_expiry)} hours")
    
    # Initialize expiry strategy
    strategy = ExpiryStrategy(max_days_to_expiry=7, min_volume=1000)
    
    # Find opportunities
    print(f"\n🎯 Finding Expiry-Based Opportunities:")
    opportunities = strategy.find_opportunities(markets_data)
    
    print(f"\nFound {len(opportunities)} expiry-based opportunities:")
    
    for i, opp in enumerate(opportunities):
        market = opp['market']
        print(f"\n--- Opportunity #{i+1} ---")
        print(f"Market: {market['title'][:60]}...")
        print(f"Platform: {market['platform']}")
        print(f"Type: {opp['subtype'].replace('_', ' ').title()}")
        print(f"Time to Expiry: {opp['days_to_expiry']:.1f} days ({opp['hours_to_expiry']:.1f} hours)")
        print(f"Current Prices: YES ${opp['yes_price']:.3f}, NO ${opp['no_price']:.3f}")
        print(f"Confidence Score: {opp['confidence_score']:.3f}")
        print(f"Urgency Multiplier: {opp['urgency_multiplier']:.3f}")
        print(f"Final Score: {opp['final_score']:.3f}")
        print(f"Expected Profit: ${opp['expected_profit']:.4f}")
        print(f"Recommendation: {opp['recommended_action']}")
    
    if opportunities:
        print(f"\n🏆 Best Opportunity:")
        best = opportunities[0]
        market = best['market']
        print(f"Market: {market['title']}")
        print(f"Strategy: Focus on {best['subtype'].replace('_', ' ')}")
        print(f"Reason: Market expires in {best['days_to_expiry']:.1f} days with {best['subtype']} pattern")
        print(f"Action: {best['recommended_action']}")
    
    print(f"\n🎉 Expiry Strategy Demo completed!")
    print(f"\nThis strategy identifies:")
    print(f"  • Markets close to expiration (within 7 days by default)")
    print(f"  • Overconfident markets (very high/low probabilities)")
    print(f"  • Uncertain markets (close to 50/50) that might swing")
    print(f"  • Higher urgency for markets expiring sooner")
    print(f"  • Only markets with sufficient volume")

if __name__ == "__main__":
    demo_expiry_strategy()