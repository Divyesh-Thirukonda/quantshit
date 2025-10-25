import os
import time
from datetime import datetime
from typing import Dict, List

from dotenv import load_dotenv

from .executor import TradeExecutor
from ..platforms import get_market_api
from ..strategies import get_strategy


class ArbitrageBot:
    """Main arbitrage bot for paper trading (simulation mode only)"""
    
    def __init__(self):
        # Load environment variables
        load_dotenv()
        
        print("🧪 Quantshit Arbitrage Engine - Paper Trading Mode")
        print("   📄 This is a simulation-only system with virtual money")
        
        # Configuration
        self.min_volume = float(os.getenv('MIN_VOLUME', 1000))
        self.min_spread = float(os.getenv('MIN_SPREAD', 0.01))  # Lower threshold for testing
        
        # Get API keys from environment (mock keys for paper trading)
        self.api_keys = {
            'polymarket': os.getenv('POLYMARKET_API_KEY', 'paper_trading_key'),
            'kalshi': os.getenv('KALSHI_API_KEY', 'paper_trading_key')
        }
        
        # Initialize components
        self.strategy = get_strategy('arbitrage', min_spread=self.min_spread)
        self.executor = TradeExecutor(self.api_keys, paper_trading=True)
        
        print(f"   Platforms: {list(self.api_keys.keys())} (simulated)")
        print(f"   Min volume: ${self.min_volume}")
        print(f"   Min spread: {self.min_spread}")
        print(f"   💰 Starting with $10,000 virtual money per platform")
    
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
    
    def search_events(self, keyword: str, platforms: List[str] = None, limit: int = 10) -> Dict[str, List[Dict]]:
        """Search for events across all or specified platforms"""
        if platforms is None:
            platforms = list(self.api_keys.keys())
        
        results = {}
        print(f"\n🔍 Searching for '{keyword}' across platforms...")
        
        for platform in platforms:
            if platform not in self.api_keys:
                print(f"   ⚠️  {platform}: No API key configured")
                continue
                
            try:
                api = get_market_api(platform, self.api_keys[platform])
                events = api.find_event(keyword, limit)
                results[platform] = events
                print(f"   📊 {platform}: Found {len(events)} events")
            except Exception as e:
                print(f"   ❌ {platform}: Error - {e}")
                results[platform] = []
        
        return results
    
    def execute_trade(self, platform: str, event_id: str, outcome: str, action: str, amount: float, price: float = None) -> Dict:
        """Execute a trade on a specific platform and event"""
        if platform not in self.api_keys:
            return {'success': False, 'error': f'No API key for platform: {platform}'}
        
        try:
            api = get_market_api(platform, self.api_keys[platform])
            result = api.execute_event(event_id, outcome, action, amount, price)
            
            print(f"\n🔄 Trade Execution:")
            print(f"   Platform: {platform}")
            print(f"   Event: {event_id}")
            print(f"   Action: {action} {amount} shares of {outcome}")
            if price:
                print(f"   Price: ${price}")
            print(f"   Result: {'✅ Success' if result.get('success') else '❌ Failed'}")
            if result.get('message'):
                print(f"   Message: {result['message']}")
            
            return result
        except Exception as e:
            error_msg = f"Trade execution failed: {str(e)}"
            print(f"   ❌ {error_msg}")
            return {'success': False, 'error': error_msg}
    
    def run_once(self):
        """Run a single arbitrage scan (for testing)"""
        print(f"\n🔍 Running single arbitrage scan...")
        
        # Collect data
        markets_data = self.collect_market_data()
        
        # Find opportunities
        opportunities = self.find_opportunities(markets_data)
        
        # Show virtual balances
        balances = self.executor.get_virtual_balances()
        print(f"\n💰 Virtual Balances:")
        for platform, balance in balances.items():
            print(f"   {platform}: ${balance:,.2f}")
        
        # Execute opportunities
        if opportunities:
            executed = self.executor.execute_opportunities(opportunities, max_trades=3)
            
            # Show final balances
            final_balances = self.executor.get_virtual_balances()
            print(f"\n💰 Final Virtual Balances:")
            for platform, balance in final_balances.items():
                print(f"   {platform}: ${balance:,.2f}")
        else:
            print("No profitable arbitrage opportunities found.")
    
    def find_opportunities(self, markets_data: Dict[str, List[Dict]]) -> List[Dict]:
        """Find arbitrage opportunities using the strategy"""
        print(f"\n🎯 Analyzing arbitrage opportunities...")
        
        opportunities = self.strategy.find_opportunities(markets_data)
        
        if opportunities:
            print(f"   Found {len(opportunities)} potential arbitrage opportunities")
            # Show top 3 opportunities
            for i, opp in enumerate(opportunities[:3]):
                print(f"   {i+1}. {opp['outcome']} | Spread: {opp['spread']:.3f} | Profit: ${opp['expected_profit']:.2f}")
        else:
            print(f"   No arbitrage opportunities found")
        
        return opportunities


def main():
    """Main entry point for paper trading"""
    print("🚀 Quantshit Arbitrage Engine")
    print("📄 Paper Trading Mode Only")
    print("")
    
    bot = ArbitrageBot()
    
    # Check if we want to run once or start scheduling
    import sys
    if '--once' in sys.argv or '--test' in sys.argv:
        bot.run_once()
    else:
        print("🔄 Starting continuous paper trading...")
        print("Press Ctrl+C to stop")
        try:
            while True:
                bot.run_once()
                print("\n💤 Waiting 30 seconds before next scan...")
                time.sleep(30)
        except KeyboardInterrupt:
            print("\n🛑 Paper trading stopped by user")


if __name__ == "__main__":
    main()