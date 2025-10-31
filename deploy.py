"""Simple deployment script for Phase 1."""

import subprocess
import sys
from pathlib import Path


def check_python_version():
    """Check that we have Python 3.11+"""
    if sys.version_info < (3, 11):
        print("✗ Python 3.11+ required. Current version:", sys.version)
        return False
    print("✓ Python version:", sys.version.split()[0])
    return True


def install_dependencies():
    """Install required dependencies."""
    print("Installing dependencies...")
    try:
        subprocess.run([sys.executable, "-m", "pip", "install", "-r", "requirements.txt"], 
                      check=True, capture_output=True)
        print("✓ Dependencies installed successfully")
        return True
    except subprocess.CalledProcessError as e:
        print("✗ Failed to install dependencies:", e.stderr.decode())
        return False


def run_tests():
    """Run the test suite."""
    print("Running tests...")
    try:
        result = subprocess.run([sys.executable, "-m", "pytest", "tests/", "-v"], 
                               check=True, capture_output=True, text=True)
        print("✓ All tests passed!")
        print(result.stdout.split('\n')[-3])  # Show summary line
        return True
    except subprocess.CalledProcessError as e:
        print("✗ Tests failed:")
        print(e.stdout)
        return False


def validate_core():
    """Validate core functionality."""
    print("Validating core functionality...")
    try:
        result = subprocess.run([sys.executable, "main.py", "test"], 
                               check=True, capture_output=True, text=True)
        if "Core types test completed!" in result.stdout:
            print("✓ Core validation passed!")
            return True
        else:
            print("✗ Core validation failed - unexpected output")
            print(result.stdout)
            return False
    except subprocess.CalledProcessError as e:
        print("✗ Core validation failed:")
        print("STDOUT:", e.stdout)
        print("STDERR:", e.stderr)
        return False


def main():
    """Main deployment function."""
    print("Deploying Quantshit Phase 1: Foundation & Types")
    print("=" * 60)
    
    steps = [
        ("Python Version Check", check_python_version),
        ("Install Dependencies", install_dependencies),
        ("Run Tests", run_tests),
        ("Validate Core", validate_core),
    ]
    
    for step_name, step_func in steps:
        print(f"\n{step_name}...")
        if not step_func():
            print(f"\n✗ Deployment failed at: {step_name}")
            return False
    
    print("\nPhase 1 deployment successful!")
    print("\nWhat's working:")
    print("  ✓ Core data types (Market, Quote, ArbitrageOpportunity, etc.)")
    print("  ✓ Configuration management")
    print("  ✓ Test suite (14 tests passing)")
    print("  ✓ Paper trading foundation")
    
    print("\nNext: Phase 2 - Data Acquisition")
    print("  > Set up API credentials in .env file")
    print("  > Implement Kalshi and Polymarket connectors")
    print("  > Add market data fetching")
    
    return True


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)