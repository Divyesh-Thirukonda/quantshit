import os
import time
from datetime import datetime
from typing import Dict, List

from dotenv import load_dotenv

from .directional_executor import DirectionalTradeExecutor
from ..platforms import get_market_api
from ..strategies.fixed_arbitrage import FixedArbitrageStrategy
from ..config.environment import env


class ArbitrageBot:
    """Main arbitrage bot that orchestrates data collection, strategy, and execution"""
    
    def __init__(self):
        # Load environment variables
        load_dotenv()
        
        # Get environment-specific configuration
        config = env.get_api_config()
        risk_limits = env.get_risk_limits()
        
        print(f"🤖 Arbitrage Bot initializing in {env.mode.value.upper()} mode")
        print(f"   Environment: {env.environment}")
        
        # Configuration
        self.min_volume = float(os.getenv('MIN_VOLUME', 1000))
        self.min_spread = risk_limits['min_profit_threshold']
        
        # API Keys (environment-dependent)
        if env.is_paper_trading():
            # Paper trading - use dummy keys for all platforms
            self.api_keys = {
                'polymarket': 'paper_trading',
                'kalshi': 'paper_trading'
            }
            print(f"   💰 Paper trading with ${config['initial_balance_per_platform']:.0f} per platform")
        else:
            # Live trading - use real API keys
            credentials = env.get_platform_credentials()
            self.api_keys = {k: v for k, v in credentials.items() if v and not k.endswith('_private_key')}
            if not self.api_keys:
                print("⚠️  No API keys found. Running in demo mode.")
        
        # Initialize components
        self.strategy = FixedArbitrageStrategy(min_spread=self.min_spread)
        
        # Pass initial balances for paper trading
        initial_balances = None
        if env.is_paper_trading():
            initial_balances = {platform: config['initial_balance_per_platform'] for platform in self.api_keys.keys()}
        
        self.executor = DirectionalTradeExecutor(self.api_keys, initial_balances)
        
        print(f"   Platforms: {list(self.api_keys.keys())}")
        print(f"   Min volume: ${self.min_volume}")
        print(f"   Min spread: {self.min_spread}")
        
        if env.is_paper_trading():
            print(f"   📈 Paper trading limits: max ${config['max_position_size']}/trade, ${config['max_total_exposure']} total exposure")
    
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
        """Run arbitrage detection once (for testing)"""
        print(f"\n🔍 Running single arbitrage scan...")
        
        # Collect data
        markets_data = self.collect_market_data()
        
        # Find opportunities
        opportunities = self.find_opportunities(markets_data)
        
        # Show capital status if available
        if hasattr(self.executor, 'get_capital_status'):
            self.executor.get_capital_status()
        
        # Execute opportunities (in paper trading or live based on environment)
        if opportunities:
            executed = self.executor.execute_opportunities(opportunities, max_trades=3)
            
            # Show final capital status
            if hasattr(self.executor, 'get_capital_status'):
                print(f"\n💰 Final Capital Status:")
                self.executor.get_capital_status()
        else:
            print("No profitable arbitrage opportunities found.")
    
    def start_scheduling(self):
        """Start scheduled arbitrage scanning (for production)"""
        print(f"\n⏰ Starting scheduled arbitrage scanning...")
        print(f"   Trading mode: {env.mode.value}")
        print(f"   Scan interval: 30 seconds")
        print(f"   Press Ctrl+C to stop")
        
        try:
            while True:
                self.run_once()
                print(f"\n💤 Waiting 30 seconds before next scan...")
                time.sleep(30)
        except KeyboardInterrupt:
            print(f"\n🛑 Arbitrage bot stopped by user")


def main():
    """Main entry point with environment selection"""
    import sys
    
    print("🚀 Quantshit Arbitrage Engine")
    print(f"Environment: {env}")
    
    # Check command line arguments
    if '--paper' in sys.argv:
        os.environ['TRADING_MODE'] = 'paper'
        print("🧪 Forced paper trading mode")
    elif '--live' in sys.argv:
        os.environ['TRADING_MODE'] = 'live'
        print("💰 Forced live trading mode")
    
    # Initialize bot
    bot = ArbitrageBot()
    
    # Check if we want to run once or start scheduling
    if '--once' in sys.argv or '--test' in sys.argv:
        bot.run_once()
    else:
        if env.is_live_trading():
            print("⚠️  WARNING: You are about to start LIVE TRADING with real money!")
            response = input("Are you sure you want to continue? (yes/no): ")
            if response.lower() != 'yes':
                print("Exiting...")
                return
        
        bot.start_scheduling()


if __name__ == "__main__":
    main()