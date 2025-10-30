"""
Quick deployment test for Vercel
"""

import sys
import os

# Add the parent directory to the path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

def test_imports():
    """Test if all imports work correctly"""
    try:
        from src.coordinators.trading_orchestrator import TradingOrchestrator
        print("✓ TradingOrchestrator imported successfully")
        
        from src.platforms.registry import get_all_platforms
        print("✓ Platform registry imported successfully")
        
        from src.types import Platform, Outcome
        print("✓ Types imported successfully")
        
        return True
    except Exception as e:
        print(f"✗ Import failed: {e}")
        return False

def test_basic_functionality():
    """Test basic system functionality"""
    try:
        from src.coordinators.trading_orchestrator import TradingOrchestrator
        
        orchestrator = TradingOrchestrator()
        print("✓ TradingOrchestrator initialized successfully")
        
        # Test environment variables
        env_check = {
            "POLYMARKET_API_KEY": os.getenv("POLYMARKET_API_KEY"),
            "KALSHI_API_KEY": os.getenv("KALSHI_API_KEY"),
        }
        
        for key, value in env_check.items():
            if value:
                print(f"✓ {key} is set")
            else:
                print(f"✗ {key} is missing")
        
        return True
    except Exception as e:
        print(f"✗ Basic functionality test failed: {e}")
        return False

if __name__ == "__main__":
    print("Running deployment readiness test...")
    
    imports_ok = test_imports()
    functionality_ok = test_basic_functionality()
    
    if imports_ok and functionality_ok:
        print("\n✓ System ready for deployment!")
    else:
        print("\n✗ System has issues that need to be fixed before deployment")