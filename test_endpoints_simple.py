"""
Simple test of the pipeline endpoints without external dependencies
"""

import sys
import os
sys.path.append('.')

from api.app import app
from fastapi.testclient import TestClient

def test_pipeline_endpoints():
    """Test all pipeline endpoints"""
    
    client = TestClient(app)
    
    print("🧪 Testing Pipeline Endpoints")
    print("=" * 40)
    
    # Test root endpoint
    print("\n1. Testing root endpoint...")
    response = client.get("/")
    if response.status_code == 200:
        data = response.json()
        print(f"✅ Root endpoint working - Version {data['version']}")
        print(f"   System available: {data['system_available']}")
    else:
        print(f"❌ Root endpoint failed: {response.status_code}")
        
    # Test health
    print("\n2. Testing health endpoint...")
    response = client.get("/health")
    if response.status_code == 200:
        print("✅ Health endpoint working")
    else:
        print(f"❌ Health endpoint failed: {response.status_code}")
    
    # Test pipeline endpoints
    pipeline_endpoints = [
        ("scan-markets", "POST"),
        ("detect-opportunities", "POST"),
        ("portfolio-management", "POST"),
        ("execute-trades", "POST")
    ]
    
    for endpoint, method in pipeline_endpoints:
        print(f"\n3. Testing /pipeline/{endpoint}...")
        try:
            if method == "POST":
                response = client.post(f"/pipeline/{endpoint}")
            else:
                response = client.get(f"/pipeline/{endpoint}")
                
            if response.status_code == 200:
                data = response.json()
                if data.get("success"):
                    print(f"✅ {endpoint} working")
                    if "summary" in data:
                        print(f"   Summary: {data['summary']}")
                else:
                    print(f"⚠️  {endpoint} returned success=False: {data.get('error', 'Unknown error')}")
            else:
                print(f"❌ {endpoint} failed: {response.status_code}")
        except Exception as e:
            print(f"❌ {endpoint} error: {e}")
    
    # Test dashboard endpoints
    dashboard_endpoints = [
        "overview",
        "opportunities", 
        "positions",
        "performance"
    ]
    
    for endpoint in dashboard_endpoints:
        print(f"\n4. Testing /dashboard/{endpoint}...")
        try:
            response = client.get(f"/dashboard/{endpoint}")
            if response.status_code == 200:
                data = response.json()
                if data.get("success"):
                    print(f"✅ dashboard/{endpoint} working")
                else:
                    print(f"⚠️  dashboard/{endpoint} returned success=False")
            else:
                print(f"❌ dashboard/{endpoint} failed: {response.status_code}")
        except Exception as e:
            print(f"❌ dashboard/{endpoint} error: {e}")
    
    print("\n🎉 Pipeline endpoint testing complete!")

if __name__ == "__main__":
    test_pipeline_endpoints()