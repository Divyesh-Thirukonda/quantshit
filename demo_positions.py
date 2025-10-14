#!/usr/bin/env python3
"""
Demo script to show position tracking and API endpoints
"""

import sys
import os
from datetime import datetime

# Add the current directory to Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from position_tracker import PositionTracker

def demo_position_tracking():
    """Demonstrate position tracking functionality"""
    print("📊 Position Tracking Demo")
    print("=" * 50)
    
    # Initialize tracker
    tracker = PositionTracker("demo_positions.json")
    
    print("\n1️⃣ Adding some demo trades...")
    
    # Simulate some trades from different strategies
    trades = [
        {
            'market_id': 'trump_election_2024',
            'market_title': 'Will Trump win 2024 election?',
            'platform': 'polymarket',
            'action': 'BUY',
            'outcome': 'YES',
            'shares': 100,
            'price': 0.52,
            'strategy': 'arbitrage'
        },
        {
            'market_id': 'trump_election_2024_mani',
            'market_title': 'Trump wins 2024 election',
            'platform': 'manifold',
            'action': 'SELL',
            'outcome': 'YES',
            'shares': 100,
            'price': 0.56,
            'strategy': 'arbitrage'
        },
        {
            'market_id': 'fed_meeting_rates',
            'market_title': 'Fed cuts rates at next meeting?',
            'platform': 'polymarket',
            'action': 'SELL',
            'outcome': 'YES',
            'shares': 50,
            'price': 0.89,
            'strategy': 'expiry'
        },
        {
            'market_id': 'btc_70k_friday',
            'market_title': 'Bitcoin above $70k by Friday?',
            'platform': 'manifold',
            'action': 'BUY',
            'outcome': 'YES',
            'shares': 200,
            'price': 0.12,
            'strategy': 'expiry'
        }
    ]
    
    trade_ids = []
    for trade in trades:
        trade_id = tracker.add_trade(**trade)
        trade_ids.append(trade_id)
        print(f"   ✅ Added {trade['action']} {trade['shares']} {trade['outcome']} @ ${trade['price']:.3f}")
    
    print(f"\n2️⃣ Current Positions:")
    positions = tracker.get_open_positions()
    
    if positions:
        for pos in positions:
            pnl_indicator = "📈" if pos['unrealized_pnl'] >= 0 else "📉"
            print(f"   {pnl_indicator} [{pos['platform']}] {pos['market_title'][:40]}...")
            print(f"      {pos['shares']} {pos['outcome']} shares @ ${pos['entry_price']:.3f}")
            print(f"      Strategy: {pos['strategy']}")
            print(f"      Unrealized P&L: ${pos['unrealized_pnl']:.2f}")
    else:
        print("   No open positions")
    
    print(f"\n3️⃣ Simulating price updates...")
    
    # Simulate price updates
    price_updates = {
        'trump_election_2024': {'yes_price': 0.54, 'no_price': 0.46},
        'fed_meeting_rates': {'yes_price': 0.87, 'no_price': 0.13},
        'btc_70k_friday': {'yes_price': 0.15, 'no_price': 0.85}
    }
    
    tracker.update_market_prices(price_updates)
    
    print(f"\n4️⃣ Updated Positions:")
    positions = tracker.get_open_positions()
    
    for pos in positions:
        pnl_indicator = "📈" if pos['unrealized_pnl'] >= 0 else "📉"
        print(f"   {pnl_indicator} [{pos['platform']}] {pos['market_title'][:40]}...")
        print(f"      {pos['shares']} {pos['outcome']} @ ${pos['entry_price']:.3f} → ${pos['current_price']:.3f}")
        print(f"      Unrealized P&L: ${pos['unrealized_pnl']:.2f}")
    
    print(f"\n5️⃣ Trade History:")
    history = tracker.get_trade_history(limit=10)
    
    for trade in history[:5]:  # Show last 5 trades
        action_icon = "📈" if trade['action'] == 'BUY' else "📉"
        pnl = f" (P&L: ${trade['realized_pnl']:.2f})" if trade['realized_pnl'] != 0 else ""
        print(f"   {action_icon} {trade['action']} {trade['shares']} {trade['outcome']} @ ${trade['price']:.3f}{pnl}")
        print(f"      [{trade['platform']}] {trade['market_title'][:45]}...")
        print(f"      Strategy: {trade['strategy']}, Time: {trade['timestamp'][:19]}")
    
    print(f"\n6️⃣ Portfolio Summary:")
    summary = tracker.get_portfolio_summary()
    
    print(f"   📊 Overview:")
    print(f"      Open Positions: {summary['total_positions']}")
    print(f"      Total Trades: {summary['total_trades']}")
    print(f"      Unrealized P&L: ${summary['total_unrealized_pnl']:.2f}")
    print(f"      Realized P&L: ${summary['total_realized_pnl']:.2f}")
    print(f"      Total P&L: ${summary['total_pnl']:.2f}")
    
    print(f"   📈 By Strategy:")
    for strategy, stats in summary['strategy_breakdown'].items():
        print(f"      {strategy}: {stats['trades']} trades, ${stats['total_pnl']:.2f} P&L")
    
    print(f"   🏢 By Platform:")
    for platform, stats in summary['platform_breakdown'].items():
        print(f"      {platform}: {stats['positions']} positions, ${stats['total_unrealized_pnl']:.2f} unrealized P&L")
    
    print(f"\n🎉 Position Tracking Demo Complete!")
    print(f"\nThe system now tracks:")
    print(f"  ✅ All trades executed by the bot")
    print(f"  ✅ Open positions with real-time P&L")
    print(f"  ✅ Portfolio statistics and breakdowns")
    print(f"  ✅ Historical performance by strategy")
    print(f"  ✅ Data persistence across bot restarts")
    
    # Cleanup demo file
    if os.path.exists("demo_positions.json"):
        os.remove("demo_positions.json")
        print(f"\n🧹 Cleaned up demo data file")

if __name__ == "__main__":
    demo_position_tracking()