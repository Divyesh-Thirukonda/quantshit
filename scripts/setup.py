#!/usr/bin/env python3
"""
Setup script for initializing the arbitrage system.
"""
import os
import sys
import subprocess
from pathlib import Path

def install_dependencies():
    """Install required dependencies."""
    print("Installing dependencies...")
    try:
        subprocess.check_call([sys.executable, "-m", "pip", "install", "-r", "requirements.txt"])
        print("✅ Dependencies installed successfully")
        return True
    except subprocess.CalledProcessError as e:
        print(f"❌ Error installing dependencies: {e}")
        return False

def create_env_file():
    """Create .env file from template."""
    env_example = Path(".env.example")
    env_file = Path(".env")
    
    if env_file.exists():
        print("⚠️  .env file already exists, skipping creation")
        return True
    
    if env_example.exists():
        try:
            with open(env_example, 'r') as f:
                content = f.read()
            
            with open(env_file, 'w') as f:
                f.write(content)
            
            print("✅ .env file created from template")
            print("📝 Please edit .env file with your API keys and settings")
            return True
        except Exception as e:
            print(f"❌ Error creating .env file: {e}")
            return False
    else:
        print("❌ .env.example not found")
        return False

def create_directories():
    """Create necessary directories."""
    directories = [
        "logs",
        "data",
        "backtest_results"
    ]
    
    for directory in directories:
        Path(directory).mkdir(exist_ok=True)
        print(f"✅ Created directory: {directory}")
    
    return True

def run_tests():
    """Run basic tests."""
    print("Running tests...")
    try:
        subprocess.check_call([sys.executable, "-m", "pytest", "tests/", "-v"])
        print("✅ All tests passed")
        return True
    except subprocess.CalledProcessError as e:
        print(f"❌ Some tests failed: {e}")
        return False
    except FileNotFoundError:
        print("⚠️  pytest not found, skipping tests")
        return True

def main():
    """Main setup function."""
    print("🚀 Setting up Arbitrage Trading System")
    print("=" * 50)
    
    # Check Python version
    if sys.version_info < (3, 8):
        print("❌ Python 3.8 or higher is required")
        sys.exit(1)
    
    success = True
    
    # Install dependencies
    if not install_dependencies():
        success = False
    
    # Create .env file
    if not create_env_file():
        success = False
    
    # Create directories
    if not create_directories():
        success = False
    
    # Run tests
    if not run_tests():
        print("⚠️  Tests failed, but setup can continue")
    
    print("\n" + "=" * 50)
    if success:
        print("✅ Setup completed successfully!")
        print("\nNext steps:")
        print("1. Edit .env file with your API credentials")
        print("2. Run 'python main.py run' to start the system")
        print("3. Run 'python main.py dashboard' to open the web interface")
    else:
        print("❌ Setup completed with errors")
        print("Please check the error messages above")

if __name__ == "__main__":
    main()