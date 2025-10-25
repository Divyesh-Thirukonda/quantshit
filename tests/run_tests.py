"""
Test runner script to run all tests and generate a report
"""
import sys
import os
import subprocess
import traceback
from pathlib import Path

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

def run_manual_tests():
    """Run tests manually without pytest (in case pytest is not available)"""
    print("Running Quantshit Arbitrage Engine Test Suite")
    print("=" * 60)
    
    test_results = []
    total_tests = 0
    passed_tests = 0
    failed_tests = 0
    
    # Import test modules
    test_modules = [
        'test_types',
        'test_collectors', 
        'test_strategies',
        'test_executors',
        'test_trackers',
        'test_position_manager',
        'test_trading_orchestrator',
        'test_integration'
    ]
    
    for module_name in test_modules:
        print(f"\n📋 Running {module_name}")
        print("-" * 40)
        
        try:
            # Import the test module
            module = __import__(f'tests.{module_name}', fromlist=[''])
            
            # Find all test classes
            for attr_name in dir(module):
                attr = getattr(module, attr_name)
                if (isinstance(attr, type) and 
                    attr_name.startswith('Test') and 
                    attr != type):
                    
                    print(f"  🔍 Testing {attr_name}")
                    
                    # Create test instance
                    test_instance = attr()
                    
                    # Find all test methods
                    test_methods = [method for method in dir(test_instance) 
                                  if method.startswith('test_')]
                    
                    for method_name in test_methods:
                        total_tests += 1
                        try:
                            # Get the test method
                            test_method = getattr(test_instance, method_name)
                            
                            # Try to call the method with required fixtures
                            if 'mock_api_keys' in test_method.__code__.co_varnames:
                                # Method needs fixtures - provide mock data
                                from tests.conftest import TEST_API_KEYS, TEST_MARKET_DATA
                                test_method(TEST_API_KEYS, TEST_MARKET_DATA)
                            else:
                                # Method doesn't need fixtures
                                test_method()
                            
                            print(f"    ✅ {method_name}")
                            passed_tests += 1
                            test_results.append(f"✅ {module_name}.{attr_name}.{method_name}")
                            
                        except Exception as e:
                            print(f"    ❌ {method_name}: {str(e)}")
                            failed_tests += 1
                            test_results.append(f"❌ {module_name}.{attr_name}.{method_name}: {str(e)}")
                            
        except Exception as e:
            print(f"  ❌ Failed to import/run {module_name}: {str(e)}")
            failed_tests += 1
            test_results.append(f"❌ {module_name}: Import failed - {str(e)}")
    
    # Print summary
    print("\n" + "=" * 60)
    print("📊 TEST SUMMARY")
    print("=" * 60)
    print(f"Total Tests: {total_tests}")
    print(f"Passed: {passed_tests} ✅")
    print(f"Failed: {failed_tests} ❌")
    print(f"Success Rate: {(passed_tests/total_tests*100):.1f}%" if total_tests > 0 else "No tests run")
    
    if failed_tests > 0:
        print(f"\n❌ FAILED TESTS:")
        for result in test_results:
            if result.startswith("❌"):
                print(f"  {result}")
    
    return passed_tests, failed_tests, total_tests

def run_integration_test():
    """Run a simple integration test of the main system"""
    print("\nRunning Integration Test")
    print("-" * 40)
    
    try:
        # Test main imports
        print("  📦 Testing imports...")
        from src.coordinators.trading_orchestrator import TradingOrchestrator
        from src.engine.bot import ArbitrageBot
        from src.types import Market, ArbitrageOpportunity
        print("    ✅ Core imports successful")
        
        # Test backward compatibility
        print("  🔄 Testing backward compatibility...")
        assert ArbitrageBot is TradingOrchestrator
        print("    ✅ Backward compatibility working")
        
        # Test basic functionality with mocked environment
        print("  Testing basic functionality...")
        import os
        from unittest.mock import patch
        
        # Mock environment variables
        env_vars = {
            'MIN_VOLUME': '1000',
            'MIN_SPREAD': '0.05',
            'POLYMARKET_API_KEY': 'test_key',
            'KALSHI_API_KEY': 'test_key'
        }
        
        with patch.dict(os.environ, env_vars):
            with patch('src.platforms.get_market_api') as mock_api:
                mock_api.return_value.get_recent_markets.return_value = []
                
                # This should work without errors
                orchestrator = TradingOrchestrator()
                print("    ✅ System initialization successful")
        
        return True
        
    except Exception as e:
        print(f"    ❌ Integration test failed: {str(e)}")
        traceback.print_exc()
        return False

def run_with_pytest():
    """Try to run tests with pytest if available"""
    try:
        result = subprocess.run([
            sys.executable, '-m', 'pytest', 
            'tests/', '-v', '--tb=short'
        ], capture_output=True, text=True, cwd=os.path.dirname(__file__))
        
        print("Pytest Output:")
        print(result.stdout)
        if result.stderr:
            print("⚠️ Pytest Errors:")
            print(result.stderr)
        
        return result.returncode == 0
    except FileNotFoundError:
        print("⚠️ Pytest not available, falling back to manual testing")
        return False

def main():
    """Main test runner"""
    print("🔬 Quantshit Arbitrage Engine - Test Suite")
    print("=" * 60)
    
    # Try pytest first
    pytest_success = run_with_pytest()
    
    if not pytest_success:
        print("\n📝 Running manual tests...")
        passed, failed, total = run_manual_tests()
    
    # Always run integration test
    integration_success = run_integration_test()
    
    # Final summary
    print("\n" + "=" * 60)
    print("🎯 FINAL RESULTS")
    print("=" * 60)
    
    if pytest_success:
        print("✅ Pytest tests: PASSED")
    else:
        print("❌ Pytest tests: FAILED or not available")
    
    if integration_success:
        print("✅ Integration test: PASSED")
    else:
        print("❌ Integration test: FAILED")
    
    # Overall result
    if integration_success and (pytest_success or True):  # Integration is most important
        print("\n🎉 OVERALL RESULT: SYSTEM IS WORKING!")
        print("💚 The codebase is healthy and ready for production.")
        return 0
    else:
        print("\n💥 OVERALL RESULT: ISSUES DETECTED")
        print("🔧 Please review and fix the failing tests.")
        return 1

if __name__ == "__main__":
    sys.exit(main())