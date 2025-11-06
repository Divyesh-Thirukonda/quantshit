#!/usr/bin/env python3
"""
Test runner script for Quantshit.
Provides easy commands to run the full test suite or specific test categories.
"""
import sys
import subprocess


def run_tests(args=None):
    """Run pytest with specified arguments"""
    cmd = ["python", "-m", "pytest"]
    
    if args:
        cmd.extend(args)
    else:
        # Default: run all tests with verbose output and coverage
        cmd.extend([
            "tests/",
            "-v",
            "--cov=src",
            "--cov-report=term-missing",
            "--cov-report=html"
        ])
    
    print(f"Running: {' '.join(cmd)}")
    print("=" * 60)
    
    result = subprocess.run(cmd)
    return result.returncode


def main():
    """Main entry point"""
    if len(sys.argv) > 1:
        command = sys.argv[1]
        
        if command == "all":
            # Run all tests with coverage
            return run_tests([
                "tests/",
                "-v",
                "--cov=src",
                "--cov-report=term-missing",
                "--cov-report=html"
            ])
        
        elif command == "fast":
            # Run all tests without coverage (faster)
            return run_tests(["tests/", "-v"])
        
        elif command == "models":
            # Test domain models only
            return run_tests(["tests/test_models.py", "-v"])
        
        elif command == "matching":
            # Test matching services
            return run_tests(["tests/test_matching.py", "-v"])
        
        elif command == "execution":
            # Test execution services
            return run_tests(["tests/test_execution.py", "-v"])
        
        elif command == "strategies":
            # Test strategies
            return run_tests(["tests/test_strategies.py", "-v"])
        
        elif command == "integration":
            # Test full integration
            return run_tests(["tests/test_integration.py", "-v"])
        
        elif command == "help":
            print("Quantshit Test Runner")
            print("=" * 60)
            print("Usage: python run_tests.py [command]")
            print()
            print("Commands:")
            print("  all          - Run all tests with coverage (default)")
            print("  fast         - Run all tests without coverage")
            print("  models       - Test domain models only")
            print("  matching     - Test matching services")
            print("  execution    - Test execution services")
            print("  strategies   - Test trading strategies")
            print("  integration  - Test full integration")
            print("  help         - Show this help message")
            return 0
        
        else:
            print(f"Unknown command: {command}")
            print("Run 'python run_tests.py help' for usage")
            return 1
    
    else:
        # No arguments: run all tests with coverage
        return run_tests()


if __name__ == "__main__":
    sys.exit(main())
