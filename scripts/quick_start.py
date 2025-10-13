#!/usr/bin/env python3
"""
Quick start script to demonstrate the simplified frameworks.
Run this to see all the new developer-friendly features in action.
"""
import sys
import os
import asyncio
from datetime import datetime

# Add src to path
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

from src.data.framework import (
    data_source, EasyDataProvider, QuickDataFetcher, 
    data_registry, auto_discover_data_sources
)
from src.strategies.framework import (
    strategy, EasyStrategy, StrategyTester, 
    strategy_registry, StrategyDifficulty, auto_discover_strategies
)
from src.execution.framework import (
    QuickTrader, SimpleExecutor, ExecutionMode
)
from src.data.providers import MarketData, MarketStatus
from src.strategies.base import TradingSignal, SignalType


async def demo_data_sources():
    """Demonstrate easy data source creation."""
    print("🔄 Demo: Easy Data Sources")
    print("=" * 50)
    
    # Example 1: Simple data source function
    @data_source("demo_prices", platforms=["demo"], refresh_interval=30)
    async def get_demo_prices(symbols):
        """Demo data source that generates sample prices."""
        markets = []
        for i, symbol in enumerate(symbols):
            price = 0.3 + (i * 0.4 / len(symbols))  # Prices from 0.3 to 0.7
            markets.append(MarketData(
                platform="demo",
                market_id=symbol,
                title=f"Demo Market {symbol}",
                category="demo",
                yes_price=price,
                no_price=1.0 - price,
                volume=100 + (i * 50),
                status=MarketStatus.ACTIVE
            ))
        return markets
    
    # Register the data source
    data_registry.register_data_source(get_demo_prices)
    
    # Example 2: Data provider class
    class DemoProvider(EasyDataProvider):
        def __init__(self):
            super().__init__("demo_provider")
        
        async def connect(self):
            print("📡 Connected to demo data provider")
            self.is_connected = True
            return True
        
        async def get_markets(self, symbols=None):
            symbols = symbols or ["DEMO_001", "DEMO_002", "DEMO_003"]
            return await get_demo_prices(symbols)
    
    # Register the provider
    provider = DemoProvider()
    data_registry.register_provider(provider)
    
    # Test the data sources
    fetcher = QuickDataFetcher()
    markets = await fetcher.get_markets("demo_provider", ["TEST_A", "TEST_B", "TEST_C"])
    
    print(f"✅ Fetched {len(markets)} markets:")
    for market in markets:
        print(f"  - {market.market_id}: ${market.yes_price:.2f} (Volume: {market.volume})")
    
    return markets


async def demo_strategies():
    """Demonstrate easy strategy creation."""
    print("\n🧠 Demo: Easy Strategies")
    print("=" * 50)
    
    # Example 1: Simple strategy function
    @strategy(
        name="Buy Low Sell High",
        description="Classic reversal strategy",
        difficulty=StrategyDifficulty.BEGINNER,
        tags=["reversal", "simple"]
    )
    def buy_low_sell_high(market):
        """Simple reversal strategy."""
        if market.yes_price < 0.35:
            return TradingSignal(
                strategy_name="buy_low_sell_high",
                market_id=market.market_id,
                platform=market.platform,
                signal_type=SignalType.BUY,
                outcome="yes",
                confidence=0.8,
                suggested_size=100.0
            )
        elif market.yes_price > 0.65:
            return TradingSignal(
                strategy_name="buy_low_sell_high",
                market_id=market.market_id,
                platform=market.platform,
                signal_type=SignalType.SELL,
                outcome="yes",
                confidence=0.8,
                suggested_size=100.0
            )
        return None
    
    # Example 2: Strategy class
    class VolumeStrategy(EasyStrategy):
        def __init__(self):
            super().__init__(
                name="Volume Momentum",
                description="Trade based on volume spikes",
                difficulty=StrategyDifficulty.BEGINNER
            )
            self.volume_threshold = 120
        
        def should_buy(self, market):
            return market.volume > self.volume_threshold and market.yes_price < 0.6
        
        def should_sell(self, market):
            return market.volume > self.volume_threshold and market.yes_price > 0.4
        
        def get_confidence(self, market):
            # Higher confidence for higher volume
            volume_factor = min(market.volume / 200, 1.0)
            return 0.5 + (0.4 * volume_factor)
    
    # Register strategies
    strategy_registry.register(buy_low_sell_high)
    volume_strategy = VolumeStrategy()
    strategy_registry.register(volume_strategy)
    
    # Test strategies
    tester = StrategyTester()
    test_markets = tester.generate_test_markets(count=8, platform="demo")
    
    print(f"📊 Testing strategies with {len(test_markets)} sample markets:")
    
    # Test simple function strategy
    results1 = await tester.test_strategy(buy_low_sell_high, test_markets)
    print(f"  - {results1.strategy_name}: {len(results1.signals)} signals generated")
    
    # Test class strategy
    results2 = await tester.test_strategy(volume_strategy, test_markets)
    print(f"  - {results2.strategy_name}: {len(results2.signals)} signals generated")
    
    # Show some sample signals
    all_signals = results1.signals + results2.signals
    if all_signals:
        print(f"📈 Sample signals:")
        for signal in all_signals[:3]:  # Show first 3
            print(f"  - {signal.signal_type.value.upper()} {signal.market_id} "
                  f"@ confidence {signal.confidence:.1f} for ${signal.suggested_size}")
    
    return all_signals


async def demo_execution():
    """Demonstrate easy execution."""
    print("\n💰 Demo: Easy Execution")
    print("=" * 50)
    
    # Create a simple trader
    trader = QuickTrader(initial_cash=1000.0, mode=ExecutionMode.PAPER)
    
    print(f"🏦 Starting with ${trader.cash:.2f} cash")
    
    # Execute some trades
    trades = [
        ("BUY", "DEMO_001", 100, 0.4),
        ("BUY", "DEMO_002", 150, 0.3),
        ("SELL", "DEMO_001", 50, 0.6),
        ("BUY", "DEMO_003", 75, 0.5)
    ]
    
    for action, market_id, quantity, price in trades:
        if action == "BUY":
            result = await trader.buy(market_id, quantity, max_price=price)
        else:
            result = await trader.sell(market_id, quantity, min_price=price)
        
        status = "✅" if result.success else "❌"
        print(f"  {status} {action} {quantity} of {market_id} - {result.message}")
    
    # Show portfolio
    print(f"\n💼 Final Portfolio:")
    print(f"  - Cash: ${trader.cash:.2f}")
    print(f"  - Positions: {trader.positions}")
    
    # Show stats
    stats = trader.get_stats()
    print(f"  - Total trades: {stats['total_trades']}")
    print(f"  - Successful: {stats['successful_trades']}")
    print(f"  - Win rate: {stats['win_rate']:.1%}")
    
    return trader


async def demo_end_to_end():
    """Demonstrate complete end-to-end workflow."""
    print("\n🚀 Demo: End-to-End Workflow")
    print("=" * 50)
    
    # 1. Get data
    fetcher = QuickDataFetcher()
    markets = await fetcher.get_markets("demo_provider", ["E2E_001", "E2E_002", "E2E_003"])
    print(f"📊 Fetched {len(markets)} markets for analysis")
    
    # 2. Run strategy
    @strategy(name="Demo E2E Strategy", difficulty=StrategyDifficulty.BEGINNER)
    def demo_strategy(market):
        # Buy if price is attractive and volume is good
        if market.yes_price < 0.4 and market.volume > 100:
            return TradingSignal(
                strategy_name="demo_e2e",
                market_id=market.market_id,
                platform=market.platform,
                signal_type=SignalType.BUY,
                outcome="yes",
                confidence=0.75,
                suggested_size=100.0
            )
        return None
    
    signals = []
    for market in markets:
        signal = demo_strategy(market)
        if signal:
            signals.append(signal)
    
    print(f"🧠 Strategy generated {len(signals)} trading signals")
    
    # 3. Execute trades
    trader = QuickTrader(initial_cash=2000.0)
    execution_results = []
    
    for signal in signals:
        if signal.signal_type == SignalType.BUY:
            result = await trader.buy(
                signal.market_id, 
                signal.suggested_size, 
                max_price=signal.price_target
            )
        else:
            result = await trader.sell(
                signal.market_id, 
                signal.suggested_size, 
                min_price=signal.price_target
            )
        execution_results.append(result)
    
    successful_trades = sum(1 for r in execution_results if r.success)
    print(f"💰 Executed {successful_trades}/{len(execution_results)} trades successfully")
    
    # 4. Show results
    print(f"\n📈 End-to-End Results:")
    print(f"  - Markets analyzed: {len(markets)}")
    print(f"  - Signals generated: {len(signals)}")
    print(f"  - Trades executed: {successful_trades}")
    print(f"  - Final cash: ${trader.cash:.2f}")
    print(f"  - Active positions: {len(trader.positions)}")
    
    return {
        'markets': markets,
        'signals': signals,
        'results': execution_results,
        'trader': trader
    }


async def main():
    """Run all demos."""
    print("🎯 Quantshit Developer Framework Demo")
    print("=" * 60)
    print("This demo shows how easy it is to build trading components!\n")
    
    try:
        # Run all demos
        await demo_data_sources()
        await demo_strategies()
        await demo_execution()
        await demo_end_to_end()
        
        print("\n" + "=" * 60)
        print("🎉 All demos completed successfully!")
        print("\nNext steps:")
        print("1. Check out docs/QUICK_START.md for detailed guides")
        print("2. Look at the framework files in src/*/framework.py")
        print("3. Try building your own strategies in src/strategies/")
        print("4. Add new data sources in src/data/")
        print("5. Run 'python scripts/test_strategy.py' to test your code")
        
    except Exception as e:
        print(f"\n❌ Demo failed: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    asyncio.run(main())