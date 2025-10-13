#!/usr/bin/env python3
"""
Test strategy script for developers.
Easily test your custom strategies with sample data.
"""
import sys
import os
import asyncio
import argparse
from datetime import datetime, timedelta

# Add src to path
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

from src.strategies.framework import (
    StrategyTester, strategy_registry, auto_discover_strategies,
    StrategyDifficulty
)
from src.data.framework import QuickDataFetcher, data_registry, auto_discover_data_sources
from src.data.providers import MarketData, MarketStatus


async def test_strategy_by_name(strategy_name: str, num_markets: int = 10):
    """Test a strategy by name."""
    print(f"🧪 Testing strategy: {strategy_name}")
    print("-" * 50)
    
    # Get the strategy
    if strategy_name not in strategy_registry.strategies:
        print(f"❌ Strategy '{strategy_name}' not found")
        print(f"Available strategies: {list(strategy_registry.strategies.keys())}")
        return
    
    strategy = strategy_registry.strategies[strategy_name]
    metadata = strategy_registry.metadata[strategy_name]
    
    # Show strategy info
    print(f"📋 Strategy Info:")
    print(f"  - Name: {metadata.name}")
    print(f"  - Description: {metadata.description}")
    print(f"  - Difficulty: {metadata.difficulty.value}")
    print(f"  - Tags: {', '.join(metadata.tags)}")
    print(f"  - Platforms: {', '.join(metadata.platforms)}")
    
    # Generate test data
    tester = StrategyTester()
    test_markets = tester.generate_test_markets(count=num_markets, platform="test")
    
    print(f"\n📊 Test Data Generated:")
    print(f"  - {len(test_markets)} sample markets")
    print(f"  - Price range: ${min(m.yes_price for m in test_markets):.2f} - ${max(m.yes_price for m in test_markets):.2f}")
    print(f"  - Volume range: {min(m.volume for m in test_markets):.0f} - {max(m.volume for m in test_markets):.0f}")
    
    # Test the strategy
    results = await tester.test_strategy(strategy, test_markets)
    
    print(f"\n🎯 Test Results:")
    print(f"  - Execution time: {results.execution_time:.3f}s")
    print(f"  - Signals generated: {len(results.signals)}")
    print(f"  - Arbitrage opportunities: {len(results.opportunities)}")
    print(f"  - Errors: {results.error_count}")
    
    if results.signals:
        print(f"\n📈 Sample Signals:")
        for i, signal in enumerate(results.signals[:5]):  # Show first 5
            print(f"  {i+1}. {signal.signal_type.value.upper()} {signal.market_id} "
                  f"@ {signal.confidence:.1f} confidence for ${signal.suggested_size}")
        
        if len(results.signals) > 5:
            print(f"  ... and {len(results.signals) - 5} more signals")
        
        # Signal statistics
        buy_signals = sum(1 for s in results.signals if s.signal_type.value == "buy")
        sell_signals = sum(1 for s in results.signals if s.signal_type.value == "sell")
        avg_confidence = sum(s.confidence for s in results.signals) / len(results.signals)
        
        print(f"\n📊 Signal Statistics:")
        print(f"  - Buy signals: {buy_signals}")
        print(f"  - Sell signals: {sell_signals}")
        print(f"  - Average confidence: {avg_confidence:.2f}")
    else:
        print("\n⚠️  No signals generated. Consider:")
        print("  - Adjusting strategy parameters")
        print("  - Using different test data")
        print("  - Checking strategy logic")


async def discover_and_list_strategies():
    """Discover and list all available strategies."""
    print("🔍 Discovering strategies...")
    
    # Try to auto-discover from common locations
    discovery_paths = [
        "src.strategies.custom",
        "src.strategies.examples", 
        "src.strategies.user"
    ]
    
    for path in discovery_paths:
        try:
            auto_discover_strategies(path)
        except:
            pass  # Module doesn't exist, that's fine
    
    print(f"\n📚 Available Strategies ({len(strategy_registry.strategies)}):")
    print("=" * 60)
    
    if not strategy_registry.strategies:
        print("No strategies found. Create one first!")
        print("\nExample:")
        print("# Create src/strategies/my_strategy.py")
        print("from src.strategies.framework import strategy, StrategyDifficulty")
        print("@strategy(name='My Strategy', difficulty=StrategyDifficulty.BEGINNER)")
        print("def my_strategy(market): return None  # Your logic here")
        return
    
    # Group by difficulty
    for difficulty in StrategyDifficulty:
        strategies = strategy_registry.get_by_difficulty(difficulty)
        if strategies:
            print(f"\n{difficulty.value.upper()} ({len(strategies)} strategies):")
            for name, strategy in strategies:
                metadata = strategy_registry.metadata[name]
                tags_str = f" #{' #'.join(metadata.tags)}" if metadata.tags else ""
                print(f"  • {name}: {metadata.description}{tags_str}")


async def create_example_strategy():
    """Create an example strategy file for developers."""
    example_code = '''"""
Example custom strategy - copy and modify this!
"""
from src.strategies.framework import strategy, EasyStrategy, StrategyDifficulty
from src.strategies.base import TradingSignal, SignalType
from src.data.providers import MarketData
from typing import Optional

# Example 1: Simple function strategy
@strategy(
    name="Price Momentum",
    description="Buy on upward momentum, sell on downward momentum",
    difficulty=StrategyDifficulty.BEGINNER,
    tags=["momentum", "simple"]
)
def price_momentum_strategy(market: MarketData) -> Optional[TradingSignal]:
    """
    Simple momentum strategy.
    
    Logic: 
    - Buy if price is between 0.4-0.6 (momentum zone)
    - Higher volume = higher confidence
    """
    if 0.4 <= market.yes_price <= 0.6:
        # Calculate confidence based on volume
        volume_factor = min(market.volume / 200, 1.0)
        confidence = 0.5 + (0.4 * volume_factor)
        
        return TradingSignal(
            strategy_name="price_momentum",
            market_id=market.market_id,
            platform=market.platform,
            signal_type=SignalType.BUY,
            outcome="yes",
            confidence=confidence,
            suggested_size=100.0
        )
    
    return None


# Example 2: Class-based strategy (more features)
class ContrarianStrategy(EasyStrategy):
    """
    Contrarian strategy - buy when others are selling.
    """
    
    def __init__(self):
        super().__init__(
            name="Contrarian",
            description="Buy extreme lows, sell extreme highs",
            difficulty=StrategyDifficulty.BEGINNER
        )
        self.buy_threshold = 0.25   # Buy when price is very low
        self.sell_threshold = 0.75  # Sell when price is very high
        self.min_volume = 50        # Require minimum volume
    
    def should_buy(self, market: MarketData) -> bool:
        """Buy when price is extremely low with good volume."""
        return (market.yes_price < self.buy_threshold and 
                market.volume > self.min_volume)
    
    def should_sell(self, market: MarketData) -> bool:
        """Sell when price is extremely high with good volume."""
        return (market.yes_price > self.sell_threshold and 
                market.volume > self.min_volume)
    
    def get_confidence(self, market: MarketData) -> float:
        """Higher confidence for more extreme prices."""
        if market.yes_price < self.buy_threshold:
            # More extreme = higher confidence
            extremeness = (self.buy_threshold - market.yes_price) / self.buy_threshold
            return 0.6 + (0.3 * extremeness)
        elif market.yes_price > self.sell_threshold:
            extremeness = (market.yes_price - self.sell_threshold) / (1 - self.sell_threshold)
            return 0.6 + (0.3 * extremeness)
        return 0.5
    
    def get_position_size(self, market: MarketData) -> float:
        """Larger positions for higher confidence trades."""
        confidence = self.get_confidence(market)
        base_size = 100.0
        return base_size * (1 + confidence)


# To test your strategies:
# python scripts/test_strategy.py --strategy "Price Momentum"
# python scripts/test_strategy.py --strategy "Contrarian"
'''
    
    example_path = "src/strategies/example_custom.py"
    
    try:
        os.makedirs(os.path.dirname(example_path), exist_ok=True)
        with open(example_path, 'w') as f:
            f.write(example_code)
        print(f"✅ Created example strategy file: {example_path}")
        print("Edit this file to create your own strategies!")
    except Exception as e:
        print(f"❌ Failed to create example file: {e}")


async def run_strategy_comparison(strategies: list, num_markets: int = 20):
    """Compare multiple strategies side by side."""
    print(f"⚖️  Comparing {len(strategies)} strategies")
    print("=" * 60)
    
    # Generate test data
    tester = StrategyTester()
    test_markets = tester.generate_test_markets(count=num_markets, platform="test")
    
    results = []
    
    for strategy_name in strategies:
        if strategy_name not in strategy_registry.strategies:
            print(f"❌ Strategy '{strategy_name}' not found, skipping")
            continue
        
        strategy = strategy_registry.strategies[strategy_name]
        result = await tester.test_strategy(strategy, test_markets)
        results.append((strategy_name, result))
    
    if not results:
        print("No valid strategies to compare")
        return
    
    # Display comparison
    print(f"\n📊 Strategy Comparison (tested on {num_markets} markets):")
    print("-" * 80)
    print(f"{'Strategy':<20} {'Signals':<8} {'Errors':<8} {'Time(s)':<10} {'Avg Confidence'}")
    print("-" * 80)
    
    for name, result in results:
        avg_conf = (sum(s.confidence for s in result.signals) / len(result.signals)) if result.signals else 0
        print(f"{name:<20} {len(result.signals):<8} {result.error_count:<8} {result.execution_time:<10.3f} {avg_conf:.2f}")
    
    # Show best performing strategy
    if results:
        best_signals = max(results, key=lambda x: len(x[1].signals))
        fastest = min(results, key=lambda x: x[1].execution_time)
        
        print(f"\n🏆 Performance Highlights:")
        print(f"  - Most signals: {best_signals[0]} ({len(best_signals[1].signals)} signals)")
        print(f"  - Fastest execution: {fastest[0]} ({fastest[1].execution_time:.3f}s)")


async def main():
    """Main test script."""
    parser = argparse.ArgumentParser(description="Test trading strategies")
    parser.add_argument("--strategy", "-s", help="Strategy name to test")
    parser.add_argument("--list", "-l", action="store_true", help="List all available strategies")
    parser.add_argument("--create-example", "-c", action="store_true", help="Create example strategy file")
    parser.add_argument("--compare", "-comp", nargs="+", help="Compare multiple strategies")
    parser.add_argument("--markets", "-m", type=int, default=10, help="Number of test markets (default: 10)")
    
    args = parser.parse_args()
    
    print("🧪 Strategy Testing Tool")
    print("=" * 50)
    
    try:
        if args.create_example:
            await create_example_strategy()
        elif args.list:
            await discover_and_list_strategies()
        elif args.compare:
            await discover_and_list_strategies()
            await run_strategy_comparison(args.compare, args.markets)
        elif args.strategy:
            # Discover strategies first
            await discover_and_list_strategies()
            await test_strategy_by_name(args.strategy, args.markets)
        else:
            # Default: list strategies and show help
            await discover_and_list_strategies()
            print(f"\n💡 Usage examples:")
            print(f"  python {sys.argv[0]} --strategy 'Strategy Name'")
            print(f"  python {sys.argv[0]} --list")
            print(f"  python {sys.argv[0]} --create-example")
            print(f"  python {sys.argv[0]} --compare 'Strategy1' 'Strategy2'")
    
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    asyncio.run(main())