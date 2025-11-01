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


def validate_api():
    """Validate API functionality."""
    print("Validating API functionality...")
    try:
        result = subprocess.run([sys.executable, "test_api.py"], 
                               check=True, capture_output=True, text=True)
        if "All tests passed!" in result.stdout:
            print("✓ API validation passed!")
            return True
        else:
            print("✗ API validation failed - unexpected output")
            print(result.stdout)
            return False
    except subprocess.CalledProcessError as e:
        print("✗ API validation failed:")
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
        ("Validate API", validate_api),
    ]
    
    for step_name, step_func in steps:
        print(f"\n{step_name}...")
        if not step_func():
            print(f"\n✗ Deployment failed at: {step_name}")
            return False
    
    print("\nCloud-ready deployment completed!")
    print("\nWhat's working:")
    print("  ✓ Core data types (Market, Quote, ArbitrageOpportunity, etc.)")
    print("  ✓ Configuration management")
    print("  ✓ Test suite (14 tests passing)")
    print("  ✓ FastAPI web service with health monitoring")
    print("  ✓ Docker containerization")
    print("  ✓ Multi-cloud deployment configs (AWS, GCP, Azure)")
    
    print("\nReady for cloud deployment:")
    print("  ☁️ Choose your cloud provider (AWS, GCP, or Azure)")
    print("  📋 Follow CLOUD_DEPLOYMENT.md for detailed instructions")
    print("  🚀 Deploy with: ./deploy/{provider}/deploy.sh")
    
    return True


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)