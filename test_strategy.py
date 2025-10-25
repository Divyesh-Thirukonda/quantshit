#!/usr/bin/env python3
"""Test opportunity detection with typed objects"""

from src.strategies.arbitrage import ArbitrageStrategy

# Test market data with significant spread
market_data = {
    'polymarket': [{
        'id': 'poly_1',
        'platform': 'polymarket', 
        'title': 'Trump wins the 2024 election',
        'yes_price': 0.65,
        'no_price': 0.35,
        'volume': 2000,
        'liquidity': 1000
    }],
    'kalshi': [{
        'id': 'kalshi_1',
        'platform': 'kalshi',
        'title': 'Trump wins 2024 election', 
        'yes_price': 0.42,
        'no_price': 0.58,
        'volume': 1500,
        'liquidity': 800
    }]
}

try:
    strategy = ArbitrageStrategy(min_spread=0.05, use_planning=False)
    opportunities = strategy.find_opportunities(market_data)
    print(f'Found {len(opportunities)} opportunities')
    print(f'Type of first opportunity: {type(opportunities[0]) if opportunities else "N/A"}')
    
    for i, opp in enumerate(opportunities):
        print(f'\n--- Opportunity {i+1} ---')
        print(f'  ID: {opp.id}')
        print(f'  Outcome: {opp.outcome.value}')
        print(f'  Spread: {opp.spread:.3f}')
        print(f'  Profit per share: ${opp.expected_profit_per_share:.3f}')
        print(f'  Expected profit: ${opp.expected_profit:.2f}')
        print(f'  Risk level: {opp.risk_level.value}')
        print(f'  Confidence: {opp.confidence_score:.2f}')
        print(f'  Max quantity: {opp.max_quantity}')
        print(f'  Buy: {opp.buy_market.platform.value} @ ${opp.buy_price:.3f}')
        print(f'  Sell: {opp.sell_market.platform.value} @ ${opp.sell_price:.3f}')
        
except Exception as e:
    print(f'Error: {e}')
    import traceback
    traceback.print_exc()