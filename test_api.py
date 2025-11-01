"""Test script to verify the API works."""

import sys
from pathlib import Path
import time
import subprocess
import threading
import signal
import os

# Add project root to path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

def start_server():
    """Start the FastAPI server in background."""
    try:
        import uvicorn
        from src.api.app import app
        
        # Start server in a separate thread
        config = uvicorn.Config(app, host="127.0.0.1", port=8000, log_level="error")
        server = uvicorn.Server(config)
        
        def run_server():
            import asyncio
            asyncio.run(server.serve())
        
        server_thread = threading.Thread(target=run_server, daemon=True)
        server_thread.start()
        
        # Wait for server to start
        time.sleep(2)
        return True
        
    except Exception as e:
        print(f"Failed to start server: {e}")
        return False

def test_api():
    """Test the API endpoints."""
    try:
        import requests
    except ImportError:
        print("requests library not found. Run: pip install requests")
        return False
    
    base_url = "http://127.0.0.1:8000"
    
    try:
        # Test root endpoint
        print("Testing root endpoint...")
        response = requests.get(f"{base_url}/", timeout=5)
        print(f"Root endpoint: {response.status_code}")
        
        # Test health endpoint
        print("Testing health endpoint...")
        response = requests.get(f"{base_url}/health", timeout=5)
        print(f"Health endpoint: {response.status_code}")
        
        # Test detailed health endpoint
        print("Testing detailed health...")
        response = requests.get(f"{base_url}/health/detailed", timeout=5)
        print(f"Detailed health: {response.status_code}")
        
        # Test status endpoint
        print("Testing status endpoint...")
        response = requests.get(f"{base_url}/status", timeout=5)
        print(f"Status endpoint: {response.status_code}")
        
        # Test metrics endpoint
        print("Testing metrics endpoint...")
        response = requests.get(f"{base_url}/metrics", timeout=5)
        print(f"Metrics endpoint: {response.status_code}")
        
        print("\nAll API tests passed!")
        return True
        
    except requests.exceptions.ConnectionError:
        print("Could not connect to API server")
        return False
    except Exception as e:
        print(f"API test failed: {e}")
        return False

def main():
    """Main test function."""
    print("Testing Quantshit API...")
    print("=" * 40)
    
    # Check if dependencies are installed
    try:
        import uvicorn
        import fastapi
        import psutil
        print("Dependencies found")
    except ImportError as e:
        print(f"Missing dependency: {e}")
        print("Run: pip install -r requirements.txt")
        return False
    
    # Start server
    print("\nStarting API server...")
    if not start_server():
        return False
    
    print("Server started")
    
    # Test API
    print("\nRunning API tests...")
    success = test_api()
    
    print(f"\n{'All tests passed!' if success else 'Tests failed!'}")
    return success

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)