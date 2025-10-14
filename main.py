import os
import time
from datetime import datetime
from typing import Dict, List
from dotenv import load_dotenv

from market_apis import get_market_api
from strategies import get_strategy
from executor import TradeExecutor


class ArbitrageBot:
    """Main arbitrage bot that orchestrates data collection, strategy, and execution"""
    
    def __init__(self):
        # Load environment variables
        load_dotenv()
        
        # Configuration
        self.min_volume = float(os.getenv('MIN_VOLUME', 1000))
        self.min_spread = float(os.getenv('MIN_SPREAD', 0.05))
        
        # API Keys
        self.api_keys = {
            'polymarket': os.getenv('POLYMARKET_API_KEY'),
            'manifold': os.getenv('MANIFOLD_API_KEY')
        }
        
        # Remove platforms without API keys
        self.api_keys = {k: v for k, v in self.api_keys.items() if v}
        
        if not self.api_keys:
            print("⚠️  No API keys found. Running in demo mode.")
        
        # Initialize components
        self.strategy = get_strategy('arbitrage', min_spread=self.min_spread)
        self.executor = TradeExecutor(self.api_keys)
        
        print(f"🤖 Arbitrage Bot initialized")
        print(f"   Platforms: {list(self.api_keys.keys())}")
        print(f"   Min volume: ${self.min_volume}")
        print(f"   Min spread: {self.min_spread}")
    
    def collect_market_data(self) -> Dict[str, List[Dict]]:
        """Collect market data from all configured platforms"""
        print(f"\n📊 Collecting market data...")
        
        markets_by_platform = {}
        
        for platform in self.api_keys.keys():
            try:
                api = get_market_api(platform, self.api_keys[platform])
                markets = api.get_recent_markets(self.min_volume)
                markets_by_platform[platform] = markets
                print(f"   {platform}: {len(markets)} markets (volume > ${self.min_volume})")
            except Exception as e:
                print(f"   ❌ {platform}: Error - {e}")
                markets_by_platform[platform] = []
        
        total_markets = sum(len(markets) for markets in markets_by_platform.values())
        print(f"   Total: {total_markets} markets collected")
        
        return markets_by_platform
    
    def run_strategy_cycle(self):
        """Run one complete cycle of the arbitrage strategy"""
        print(f"\n🔄 Starting arbitrage cycle at {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print("=" * 60)
        
        try:
            # 1. Data Collection
            markets_data = self.collect_market_data()
            
            # 2. Strategy Execution
            print(f"\n🎯 Running {self.strategy.name} strategy...")
            opportunities = self.strategy.find_opportunities(markets_data)
            
            # 3. Trade Execution
            if opportunities:
                executed_trades = self.executor.execute_opportunities(opportunities)
                
                # Log results
                successful_trades = sum(1 for trade in executed_trades if trade['success'])
                total_profit = sum(
                    trade['opportunity']['expected_profit'] 
                    for trade in executed_trades 
                    if trade['success']
                )
                
                print(f"\n📈 Cycle Results:")
                print(f"   Opportunities found: {len(opportunities)}")
                print(f"   Trades executed: {successful_trades}/{len(executed_trades)}")
                print(f"   Expected profit: ${total_profit:.4f}")
            else:
                print(f"\n💤 No arbitrage opportunities found this cycle")
        
        except Exception as e:
            print(f"\n❌ Strategy cycle failed: {e}")
        
        print("=" * 60)
        print(f"Cycle completed. Next run in 1 hour.\n")
    
    def start_scheduling(self):
        """Start the bot with simple hourly scheduling"""
        print(f"\n⏰ Starting scheduled execution (every hour)...")
        
        try:
            while True:
                self.run_strategy_cycle()
                print("Waiting 1 hour for next cycle...")
                time.sleep(3600)  # Wait 1 hour
        except KeyboardInterrupt:
            print("\n🛑 Bot stopped by user")
    
    def run_once(self):
        """Run the bot once for testing"""
        print("🧪 Running bot once for testing...")
        self.run_strategy_cycle()


def main():
    """Main entry point"""
    bot = ArbitrageBot()
    
    # Check if we want to run once or start scheduling
    import sys
    if '--once' in sys.argv or '--test' in sys.argv:
        bot.run_once()
    else:
        bot.start_scheduling()


if __name__ == "__main__":
    main()