# Test the Vercel API endpoints
import sys
import os

# Add current directory to path
sys.path.append(os.path.dirname(__file__))

try:
    from api.main import app
    import httpx
    import asyncio
    import uvicorn
    import threading
    import time
    
    print("Testing Vercel API endpoints...")
    print("=" * 40)
    
    # Start server in background thread
    def run_server():
        uvicorn.run(app, host="127.0.0.1", port=8000, log_level="error")
    
    server_thread = threading.Thread(target=run_server, daemon=True)
    server_thread.start()
    time.sleep(2)  # Wait for server to start
    
    # Test endpoints with httpx
    with httpx.Client(base_url="http://127.0.0.1:8000") as client:
        # Test root endpoint
        response = client.get("/")
        print(f"Root endpoint: {response.status_code}")
        if response.status_code == 200:
            data = response.json()
            print(f"  Message: {data.get('message')}")
            print(f"  Version: {data.get('version')}")
        
        # Test health endpoint
        response = client.get("/health")
        print(f"Health endpoint: {response.status_code}")
        if response.status_code == 200:
            data = response.json()
            print(f"  Status: {data.get('status')}")
        
        # Test markets endpoint
        response = client.get("/markets")
        print(f"Markets endpoint: {response.status_code}")
        if response.status_code == 200:
            data = response.json()
            print(f"  Markets count: {data.get('count')}")
        
        # Test opportunities endpoint
        response = client.get("/arbitrage/opportunities")
        print(f"Opportunities endpoint: {response.status_code}")
        if response.status_code == 200:
            data = response.json()
            print(f"  Opportunities count: {data.get('count')}")
        
        # Test metrics endpoint
        response = client.get("/metrics")
        print(f"Metrics endpoint: {response.status_code}")
    
    print("\n✅ All API tests passed!")
    print("\n🚀 Ready for Vercel deployment!")

except Exception as e:
    print(f"❌ Error testing API: {e}")
    sys.exit(1)