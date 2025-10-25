import os
import time
from datetime import datetime
from typing import Dict, List

from dotenv import load_dotenv

from .executor import TradeExecutor
from ..platforms import get_market_api
from ..strategies import get_strategy
from ..types import ArbitrageOpportunity


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
        
        # Initialize components with planning enabled
        self.strategy = get_strategy('arbitrage', min_spread=self.min_spread, use_planning=True)
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
        
        # Show portfolio summary
        portfolio = self.executor.get_portfolio_summary()
        print(f"\n💰 Portfolio Summary:")
        for platform, data in portfolio.items():
            if platform != 'total_portfolio_value':
                print(f"   {platform}:")
                print(f"      Cash: ${data['cash']:,.2f}")
                print(f"      Positions: ${data['position_value']:,.2f}")
                print(f"      Total: ${data['total_value']:,.2f}")
                
                if data['positions']:
                    print(f"      Holdings:")
                    for pos in data['positions']:
                        print(f"        • {pos['market']}: {pos['shares']} shares @ ${pos['avg_price']:.4f}")
        
        print(f"\n💎 Total Portfolio Value: ${portfolio['total_portfolio_value']:,.2f}")
        
        # Show risk assessment if we have positions
        if any(data.get('positions') for platform, data in portfolio.items() if platform != 'total_portfolio_value'):
            from ..strategies.planning import RiskManager
            risk_mgr = RiskManager()
            risk_metrics = risk_mgr.assess_portfolio_risk(portfolio, [])
            
            print(f"\n⚠️ Risk Assessment:")
            print(f"   Correlation Risk: {risk_metrics['correlation_risk']*100:.1f}%")
            print(f"   Concentration Risk: {risk_metrics['concentration_risk']*100:.1f}%")
            print(f"   Overall Risk Score: {risk_metrics['overall_risk_score']*100:.1f}%")
        
        # Execute opportunities
        if opportunities:
            executed = self.executor.execute_opportunities(opportunities, max_trades=3)
            
            # Show final portfolio summary
            final_portfolio = self.executor.get_portfolio_summary()
            print(f"\n💰 Final Portfolio Summary:")
            for platform, data in final_portfolio.items():
                if platform != 'total_portfolio_value':
                    print(f"   {platform}:")
                    print(f"      Cash: ${data['cash']:,.2f}")
                    print(f"      Positions: ${data['position_value']:,.2f}")
                    print(f"      Total: ${data['total_value']:,.2f}")
                    
                    if data['positions']:
                        print(f"      Active Positions:")
                        for pos in data['positions']:
                            pnl = pos['current_value'] - (pos['shares'] * pos['avg_price'])
                            pnl_str = f"(+${pnl:.2f})" if pnl >= 0 else f"(-${abs(pnl):.2f})"
                            print(f"        • {pos['market']}: {pos['shares']} shares @ ${pos['avg_price']:.4f} = ${pos['current_value']:.2f} {pnl_str}")
            
            print(f"\n💎 Total Portfolio Value: ${final_portfolio['total_portfolio_value']:,.2f}")
            
            # Show trade history
            if hasattr(self.executor, 'trade_history') and self.executor.trade_history:
                print(f"\n📊 Trade History ({len(self.executor.trade_history)} trades):")
                for i, trade in enumerate(self.executor.trade_history[-5:], 1):  # Show last 5 trades
                    print(f"   {i}. {trade['action'].upper()} {trade['shares']} {trade['outcome']} on {trade['platform']} @ ${trade['price']:.4f}")
        else:
            print("No profitable arbitrage opportunities found.")
    
    def find_opportunities(self, markets_data: Dict[str, List[Dict]]) -> List:
        """Find arbitrage opportunities using the strategy with portfolio awareness"""
        print(f"\n🎯 Analyzing arbitrage opportunities...")
        
        # Get current portfolio summary for planning
        portfolio_summary = self.executor.get_portfolio_summary()
        
        # Use portfolio-aware strategy - now returns ArbitrageOpportunity objects
        opportunities = self.strategy.find_opportunities(markets_data, portfolio_summary)
        
        if opportunities:
            print(f"   Final selected opportunities: {len(opportunities)}")
            # Show top opportunities using typed object properties
            for i, opp in enumerate(opportunities[:3]):
                size = opp.recommended_quantity or opp.max_quantity
                expected_return = opp.expected_profit_per_share * size
                print(f"   {i+1}. {opp.outcome.value} | Size: {size} shares | "
                      f"Spread: {opp.spread:.3f} | Expected: ${expected_return:.2f}")
                print(f"      Risk: {opp.risk_level.value} | Confidence: {opp.confidence_score:.2f}")
        else:
            print(f"   No arbitrage opportunities found")
        
        return opportunities
    
    def show_portfolio_status(self):
        """Display current portfolio status"""
        portfolio = self.executor.get_portfolio_summary()
        
        print(f"\n💼 Current Portfolio Status:")
        print(f"{'='*50}")
        
        total_initial = len(self.api_keys) * 10000  # $10k per platform initially
        total_current = portfolio['total_portfolio_value']
        total_pnl = total_current - total_initial
        
        print(f"📊 Overall Performance:")
        print(f"   Initial Value: ${total_initial:,.2f}")
        print(f"   Current Value: ${total_current:,.2f}")
        pnl_color = "+" if total_pnl >= 0 else ""
        print(f"   P&L: {pnl_color}${total_pnl:,.2f} ({((total_current/total_initial - 1) * 100):+.2f}%)")
        
        print(f"\n🏦 By Platform:")
        for platform, data in portfolio.items():
            if platform != 'total_portfolio_value':
                initial_value = 10000
                current_value = data['total_value']
                platform_pnl = current_value - initial_value
                
                print(f"   {platform.upper()}:")
                print(f"      Cash: ${data['cash']:,.2f}")
                print(f"      Positions: ${data['position_value']:,.2f}")
                print(f"      Total: ${data['total_value']:,.2f}")
                pnl_color = "+" if platform_pnl >= 0 else ""
                print(f"      P&L: {pnl_color}${platform_pnl:,.2f}")
                
                if data['positions']:
                    print(f"      Active Positions ({len(data['positions'])}):")
                    for pos in data['positions']:
                        print(f"        • {pos['shares']} shares of {pos['market']} @ ${pos['avg_price']:.4f}")
                print()
        
        print(f"{'='*50}")


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