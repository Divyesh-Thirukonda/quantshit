#!/usr/bin/env python3
"""
Test script for the REST API endpoints
"""

import requests
import json
import time
from datetime import datetime

API_BASE = "http://localhost:8000"

def test_api_endpoints():
    """Test all API endpoints"""
    print("🧪 Testing REST API Endpoints")
    print("=" * 50)
    
    # Test health endpoint
    print("\n1️⃣ Testing Health Endpoint")
    try:
        response = requests.get(f"{API_BASE}/health", timeout=5)
        if response.status_code == 200:
            data = response.json()
            print(f"   ✅ Status: {data['status']}")
            print(f"   📊 Strategies: {data['strategies']}")
            print(f"   🏢 Platforms: {data['platforms']}")
        else:
            print(f"   ❌ Failed with status: {response.status_code}")
    except Exception as e:
        print(f"   ❌ Error: {e}")
    
    # Test markets endpoint
    print("\n2️⃣ Testing Markets Endpoint")
    try:
        response = requests.get(f"{API_BASE}/markets", timeout=10)
        if response.status_code == 200:
            data = response.json()
            print(f"   ✅ Success: {data['success']}")
            print(f"   📈 Total markets: {data['summary']['total_markets']}")
            print(f"   🏢 By platform: {data['summary']['by_platform']}")
        else:
            print(f"   ❌ Failed with status: {response.status_code}")
    except Exception as e:
        print(f"   ❌ Error: {e}")
    
    # Test opportunities endpoint
    print("\n3️⃣ Testing Opportunities Endpoint")
    try:
        response = requests.get(f"{API_BASE}/strategy/opportunities", timeout=10)
        if response.status_code == 200:
            data = response.json()
            print(f"   ✅ Success: {data['success']}")
            print(f"   🎯 Opportunities found: {data['total_count']}")
            
            if data['opportunities']:
                print("   Top opportunities:")
                for i, opp in enumerate(data['opportunities'][:3]):
                    profit = opp.get('expected_profit', 0)
                    strategy = opp.get('strategy', 'unknown')
                    print(f"     {i+1}. [{strategy}] ${profit:.4f} profit")
        else:
            print(f"   ❌ Failed with status: {response.status_code}")
    except Exception as e:
        print(f"   ❌ Error: {e}")
    
    # Test positions endpoint
    print("\n4️⃣ Testing Positions Endpoint")
    try:
        response = requests.get(f"{API_BASE}/positions", timeout=5)
        if response.status_code == 200:
            data = response.json()
            print(f"   ✅ Success: {data['success']}")
            print(f"   💼 Open positions: {data['count']}")
            
            if data['positions']:
                print("   Positions:")
                for pos in data['positions']:
                    pnl = pos.get('unrealized_pnl', 0)
                    print(f"     • {pos['platform']}: {pos['shares']} {pos['outcome']} (${pnl:.2f} P&L)")
        else:
            print(f"   ❌ Failed with status: {response.status_code}")
    except Exception as e:
        print(f"   ❌ Error: {e}")
    
    # Test portfolio summary
    print("\n5️⃣ Testing Portfolio Summary")
    try:
        response = requests.get(f"{API_BASE}/positions/summary", timeout=5)
        if response.status_code == 200:
            data = response.json()
            summary = data['summary']
            print(f"   ✅ Success: {data['success']}")
            print(f"   📊 Positions: {summary['total_positions']}")
            print(f"   📈 Total P&L: ${summary['total_pnl']:.2f}")
            print(f"   📋 Total Trades: {summary['total_trades']}")
        else:
            print(f"   ❌ Failed with status: {response.status_code}")
    except Exception as e:
        print(f"   ❌ Error: {e}")
    
    # Test trade history
    print("\n6️⃣ Testing Trade History")
    try:
        response = requests.get(f"{API_BASE}/trades?limit=5", timeout=5)
        if response.status_code == 200:
            data = response.json()
            print(f"   ✅ Success: {data['success']}")
            print(f"   📜 Trades returned: {data['count']}")
            
            if data['trades']:
                print("   Recent trades:")
                for trade in data['trades'][:3]:
                    action_icon = "📈" if trade['action'] == 'BUY' else "📉"
                    print(f"     {action_icon} {trade['action']} {trade['shares']} {trade['outcome']} @ ${trade['price']:.3f}")
        else:
            print(f"   ❌ Failed with status: {response.status_code}")
    except Exception as e:
        print(f"   ❌ Error: {e}")
    
    print(f"\n🎉 API Testing Complete!")
    print(f"\nThe REST API provides:")
    print(f"  ✅ Real-time health and status information")
    print(f"  ✅ Current market data from all platforms") 
    print(f"  ✅ Live trading opportunities from all strategies")
    print(f"  ✅ Open positions with P&L tracking")
    print(f"  ✅ Portfolio summaries and statistics")
    print(f"  ✅ Complete trade history with filters")

if __name__ == "__main__":
    print("🚀 Starting API Test...")
    print("Make sure the API server is running: python api.py")
    print("Waiting 3 seconds for server startup...")
    time.sleep(3)
    
    test_api_endpoints()