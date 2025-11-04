"""
Check if the pipeline endpoints are properly added to the FastAPI app
"""

import sys
import os
sys.path.append('.')

from api.app import app

def check_endpoints():
    """Check what endpoints are available"""
    
    print("🔍 Checking Available Endpoints")
    print("=" * 40)
    
    print(f"App title: {app.title}")
    print(f"App version: {app.version}")
    
    print("\nAvailable routes:")
    for route in app.routes:
        if hasattr(route, 'path') and hasattr(route, 'methods'):
            methods = list(route.methods) if route.methods else ['GET']
            print(f"  {', '.join(methods)} {route.path}")
    
    print("\n✅ Pipeline endpoints check complete!")
    
    # Check if our new endpoints are there
    pipeline_endpoints = ['/pipeline/scan-markets', '/pipeline/detect-opportunities', 
                         '/pipeline/portfolio-management', '/pipeline/execute-trades']
    
    dashboard_endpoints = ['/dashboard/overview', '/dashboard/opportunities',
                          '/dashboard/positions', '/dashboard/performance']
    
    existing_paths = [route.path for route in app.routes if hasattr(route, 'path')]
    
    print("\n📊 Pipeline Endpoints Status:")
    for endpoint in pipeline_endpoints:
        status = "✅ Found" if endpoint in existing_paths else "❌ Missing"
        print(f"  {status}: {endpoint}")
    
    print("\n📈 Dashboard Endpoints Status:")
    for endpoint in dashboard_endpoints:
        status = "✅ Found" if endpoint in existing_paths else "❌ Missing"
        print(f"  {status}: {endpoint}")

if __name__ == "__main__":
    check_endpoints()