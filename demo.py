#!/usr/bin/env python3
"""
Demo script with mock data to show how the arbitrage bot works
"""

import sys
import os

# Add the current directory to Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from strategies import ArbitrageStrategy
from executor import TradeExecutor

def create_mock_markets():
    """Create mock market data to demonstrate arbitrage detection"""
    
    # Mock markets from Polymarket
    polymarket_markets = [
        {
            'id': 'poly_election_2024',
            'title': 'Will Donald Trump win the 2024 US Presidential Election?',
            'platform': 'polymarket',
            'volume': 5000000,
            'yes_price': 0.52,
            'no_price': 0.48,
            'raw_data': {}
        },
        {
            'id': 'poly_btc_100k',
            'title': 'Will Bitcoin reach $100,000 by end of 2024?',
            'platform': 'polymarket',
            'volume': 2500000,
            'yes_price': 0.35,
            'no_price': 0.65,
            'raw_data': {}
        }
    ]
    
    # Mock markets from Manifold (with slight price differences for arbitrage)
    manifold_markets = [
        {
            'id': 'mani_trump_2024',
            'title': 'Trump wins 2024 Presidential Election',
            'platform': 'manifold',
            'volume': 1500000,
            'yes_price': 0.48,  # Lower than Polymarket - arbitrage opportunity!
            'no_price': 0.52,
            'raw_data': {}
        },
        {
            'id': 'mani_bitcoin_100k',
            'title': 'Bitcoin hits $100k before 2025',
            'platform': 'manifold',
            'volume': 800000,
            'yes_price': 0.42,  # Higher than Polymarket - arbitrage opportunity!
            'no_price': 0.58,
            'raw_data': {}
        }
    ]
    
    return {
        'polymarket': polymarket_markets,
        'manifold': manifold_markets
    }

def demo_arbitrage():
    """Demonstrate the arbitrage bot with mock data"""
    print("🎭 Arbitrage Bot Demo with Mock Data")
    print("=" * 60)
    
    # Create mock market data
    print("\n📊 Mock Market Data:")
    markets_data = create_mock_markets()
    
    for platform, markets in markets_data.items():
        print(f"\n{platform.upper()}:")
        for market in markets:
            print(f"  • {market['title'][:50]}...")
            print(f"    YES: ${market['yes_price']:.2f}, NO: ${market['no_price']:.2f}, Volume: ${market['volume']:,.0f}")
    
    # Initialize strategy
    strategy = ArbitrageStrategy(min_spread=0.03)  # 3% minimum spread
    
    # Find opportunities
    print(f"\n🎯 Finding Arbitrage Opportunities:")
    opportunities = strategy.find_opportunities(markets_data)
    
    print(f"Found {len(opportunities)} arbitrage opportunities:")
    
    for i, opp in enumerate(opportunities):
        print(f"\n--- Opportunity #{i+1} ---")
        print(f"Market Pair:")
        print(f"  Buy:  [{opp['buy_market']['platform']}] {opp['buy_market']['title'][:45]}...")
        print(f"  Sell: [{opp['sell_market']['platform']}] {opp['sell_market']['title'][:45]}...")
        print(f"Trade Details:")
        print(f"  Outcome: {opp['outcome']}")
        print(f"  Buy Price: ${opp['buy_price']:.4f}")
        print(f"  Sell Price: ${opp['sell_price']:.4f}")
        print(f"  Spread: {opp['spread']:.4f} ({opp['spread']*100:.2f}%)")
        print(f"  Expected Profit: ${opp['expected_profit']:.4f}")
        print(f"  Trade Amount: {opp['trade_amount']} shares")
    
    # Demonstrate execution
    if opportunities:
        print(f"\n🔄 Demonstrating Trade Execution:")
        
        # Create executor with mock API keys
        executor = TradeExecutor({'polymarket': 'demo_key', 'manifold': 'demo_key'})
        
        # Execute the best opportunity
        best_opportunity = opportunities[0]
        result = executor.execute_arbitrage(best_opportunity)
        
        print(f"\nExecution Result:")
        print(f"  Success: {result['success']}")
        if result['buy_result']:
            print(f"  Buy Order: {result['buy_result']['message']}")
        if result['sell_result']:
            print(f"  Sell Order: {result['sell_result']['message']}")
    
    print(f"\n🎉 Demo completed!")
    print(f"\nThis shows how the bot would:")
    print(f"  1. Collect market data from multiple platforms")
    print(f"  2. Find similar markets using text matching")  
    print(f"  3. Calculate profitable arbitrage opportunities")
    print(f"  4. Execute trades to capture the spread")

if __name__ == "__main__":
    demo_arbitrage()