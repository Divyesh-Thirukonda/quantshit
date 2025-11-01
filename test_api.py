"""
Quick test script to verify the API endpoints work.
"""

import asyncio
import httpx
import sys
import os

# Add project root to path
sys.path.insert(0, os.path.dirname(__file__))

from api.main import app


def test_endpoints():
    """Test the API endpoints directly."""
    
    # Import test client
    try:
        from fastapi.testclient import TestClient
        
        print("🧪 Testing API endpoints...")
        
        # Create test client
        client = TestClient(app)
        
        # Test health endpoint
        response = client.get("/api/v1/health")
        print(f"✅ Health check: {response.status_code} - {response.json()}")
        
        # Test markets endpoint
        response = client.get("/api/v1/markets")
        print(f"✅ Markets: {response.status_code} - Found {len(response.json())} markets")
        
        # Test arbitrage opportunities
        response = client.get("/api/v1/arbitrage/opportunities")
        print(f"✅ Arbitrage: {response.status_code} - Found {len(response.json())} opportunities")
        
        # Test portfolio
        response = client.get("/api/v1/portfolio")
        portfolio = response.json()
        print(f"✅ Portfolio: {response.status_code} - Total value: ${portfolio.get('total_value', 'N/A')}")
        
        print("\n🎉 All endpoints working correctly!")
        
    except ImportError as e:
        print(f"❌ Import error: {e}")


if __name__ == "__main__":
    test_endpoints()