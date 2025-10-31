"""Simple CLI for testing and development."""

import asyncio
import sys
from pathlib import Path

# Add src to path for imports
sys.path.insert(0, str(Path(__file__).parent / "src"))

from src.core import Platform, Market, Quote, ArbitrageOpportunity
from config.settings import config


def test_types():
    """Test that our core types work correctly."""
    print("🔧 Testing Core Types...")
    
    # Test enum
    print(f"Platform: {Platform.KALSHI}")
    print(f"Available platforms: {[p.value for p in Platform]}")
    
    # Test config
    print(f"\n⚙️ Configuration:")
    print(f"Environment: {config.environment}")
    print(f"Debug: {config.debug}")
    print(f"Paper trading: {config.trading.paper_trading}")
    print(f"Max position size: ${config.trading.max_position_size}")
    
    # Test platform configs
    kalshi_config = config.get_platform_config(Platform.KALSHI)
    poly_config = config.get_platform_config(Platform.POLYMARKET)
    
    print(f"\n🔑 Platform Configurations:")
    print(f"Kalshi configured: {'✅' if kalshi_config else '❌'}")
    print(f"Polymarket configured: {'✅' if poly_config else '❌'}")
    
    print("\n✅ Core types test completed!")


def show_project_status():
    """Show current project status."""
    print("📊 Project Status - Phase 1: Foundation & Types")
    print("=" * 50)
    
    completed = [
        "✅ Core enums (Platform, Outcome, OrderType, etc.)",
        "✅ Data types (Market, Quote, ArbitrageOpportunity, etc.)",
        "✅ Configuration management",
        "✅ Basic test suite",
        "✅ Project structure"
    ]
    
    next_phase = [
        "🔄 Data Acquisition (Phase 2):",
        "   - Kalshi API integration",
        "   - Polymarket API integration", 
        "   - Market data fetching",
        "   - Database models"
    ]
    
    for item in completed:
        print(item)
    
    print("\n📋 Next Phase:")
    for item in next_phase:
        print(item)
    
    print(f"\n💡 To continue: Set up your API keys in .env file")
    print(f"💡 Then run: pytest tests/ to validate everything works")


def main():
    """Main CLI entry point."""
    if len(sys.argv) > 1:
        command = sys.argv[1]
        
        if command == "test":
            test_types()
        elif command == "status":
            show_project_status()
        else:
            print(f"Unknown command: {command}")
    else:
        print("🚀 Quantshit - Prediction Market Arbitrage System")
        print("Available commands:")
        print("  python main.py test    - Test core functionality")
        print("  python main.py status  - Show project status")


if __name__ == "__main__":
    main()