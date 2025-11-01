"""
Development utilities and scripts.
"""

import asyncio
import os
import sys
from pathlib import Path

# Add the project root to Python path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from api.main import app
import uvicorn


def run_dev_server():
    """Run the development server."""
    print("🚀 Starting Prediction Market Arbitrage API...")
    print("📊 Dashboard will be available at: http://localhost:8000")
    print("📖 API docs available at: http://localhost:8000/docs")
    print("🔍 Alternative docs at: http://localhost:8000/redoc")
    print()
    
    uvicorn.run(
        "api.main:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        reload_dirs=["api", "shared"]
    )


def run_tests():
    """Run the test suite."""
    import pytest
    print("🧪 Running test suite...")
    pytest.main(["-v", "tests/"])


def check_environment():
    """Check if all required environment variables are set."""
    required_vars = [
        "SUPABASE_URL",
        "SUPABASE_KEY",
    ]
    
    missing_vars = []
    for var in required_vars:
        if not os.getenv(var):
            missing_vars.append(var)
    
    if missing_vars:
        print("❌ Missing environment variables:")
        for var in missing_vars:
            print(f"   - {var}")
        print("\n💡 Copy .env.example to .env and fill in your values")
        return False
    else:
        print("✅ All required environment variables are set")
        return True


if __name__ == "__main__":
    import sys
    
    if len(sys.argv) > 1:
        command = sys.argv[1]
        
        if command == "dev":
            run_dev_server()
        elif command == "test":
            run_tests()
        elif command == "check":
            check_environment()
        else:
            print(f"Unknown command: {command}")
            print("Available commands: dev, test, check")
    else:
        print("Prediction Market Arbitrage System")
        print("Available commands:")
        print("  python dev.py dev   - Start development server")
        print("  python dev.py test  - Run test suite")
        print("  python dev.py check - Check environment setup")