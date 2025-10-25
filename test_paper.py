#!/usr/bin/env python3
"""
Simple test script for paper trading
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from src.platforms.kalshi import KalshiPaperAPI
from src.platforms.polymarket import PolymarketPaperAPI

def test_paper_trading():
    print("🧪 Testing Paper Trading APIs...")
    
    # Test Kalshi paper API
    print("\n📊 Testing Kalshi Paper API:")
    kalshi_api = KalshiPaperAPI(initial_balance=10000)
    
    # Check balance
    balance = kalshi_api.get_balance()
    print(f"   Balance: ${balance['available_balance']:.2f}")
    
    # Get markets
    markets = kalshi_api.get_recent_markets()
    print(f"   Markets: {len(markets)}")
    
    # Test a buy order
    if markets:
        market = markets[0]
        buy_result = kalshi_api.place_buy_order(
            market['id'], 'YES', 10, 0.50
        )
        print(f"   Buy order: {buy_result['success']} - {buy_result.get('message', 'No message')}")
        
        # Check balance after buy
        new_balance = kalshi_api.get_balance()
        print(f"   New balance: ${new_balance['available_balance']:.2f}")
    
    # Test Polymarket paper API
    print("\n📊 Testing Polymarket Paper API:")
    poly_api = PolymarketPaperAPI(initial_balance=10000)
    
    # Check balance
    balance = poly_api.get_balance()
    print(f"   Balance: ${balance['available_balance']:.2f}")
    
    # Get markets
    markets = poly_api.get_recent_markets()
    print(f"   Markets: {len(markets)}")
    
    print("\n✅ Paper trading APIs working!")

if __name__ == "__main__":
    test_paper_trading()