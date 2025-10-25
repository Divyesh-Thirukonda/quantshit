"""
Trading orchestration - coordinates between data collection, strategy execution, and trade execution
Responsible for high-level workflow coordination without doing the actual work
"""

import os
import time
from typing import Dict, List
from datetime import datetime
from dotenv import load_dotenv

from ..collectors import MarketDataCollector
from ..core import TradingLogger
from ..engine.executor import TradeExecutor
from ..strategies import get_strategy


class TradingOrchestrator:
    """
    Responsible solely for coordinating the trading workflow
    Single Responsibility: High-level orchestration and coordination
    """
    
    def __init__(self):
        """Initialize orchestrator and all coordinated components"""
        # Load environment variables
        load_dotenv()
        
        # Configuration
        self.min_volume = float(os.getenv('MIN_VOLUME', 1000))
        self.min_spread = float(os.getenv('MIN_SPREAD', 0.01))
        
        # Get API keys from environment 
        self.api_keys = {
            'polymarket': os.getenv('POLYMARKET_API_KEY', 'paper_trading_key'),
            'kalshi': os.getenv('KALSHI_API_KEY', 'paper_trading_key')
        }
        
        # Initialize coordinated components
        self.data_collector = MarketDataCollector(self.api_keys)
        self.logger = TradingLogger(self.min_volume, self.min_spread, list(self.api_keys.keys()))
        self.strategy = get_strategy('arbitrage', min_spread=self.min_spread, use_planning=True)
        self.executor = TradeExecutor(self.api_keys, paper_trading=True)
        
        # Log startup
        self.logger.log_startup()
    
    def run_strategy_cycle(self):
        """
        Orchestrate one complete cycle of the arbitrage strategy
        Coordinates data collection -> strategy execution -> trade execution
        """
        self.logger.log_cycle_start()
        
        try:
            # 1. Coordinate data collection
            markets_data = self.data_collector.collect_market_data(self.min_volume)
            
            # 2. Coordinate strategy execution
            opportunities = self.strategy.find_opportunities(markets_data)
            self.logger.log_strategy_execution(self.strategy.name, opportunities)
            
            # 3. Coordinate trade execution
            if opportunities:
                executed_trades = self.executor.execute_opportunities(opportunities)
                self.logger.log_execution_results(executed_trades)
            
        except Exception as e:
            self.logger.log_error("Strategy cycle", e)
        
        self.logger.log_cycle_end()
    
    def run_continuous(self, cycle_interval_hours: int = 1):
        """
        Run continuous trading cycles
        
        Args:
            cycle_interval_hours: Hours between cycles
        """
        while True:
            self.run_strategy_cycle()
            time.sleep(cycle_interval_hours * 3600)  # Convert hours to seconds
    
    def get_portfolio_summary(self) -> Dict:
        """Get summary of current portfolio state"""
        return {
            'balances': self.executor.get_virtual_balances(),
            'positions': self.executor.get_positions(),
            'total_value': self.executor.get_portfolio_value()
        }
    
    def get_available_platforms(self) -> List[str]:
        """Get list of available platforms"""
        return self.data_collector.get_available_platforms()
    
    def start_scheduling(self):
        """Start the bot with simple hourly scheduling"""
        print(f"\n⏰ Starting scheduled execution (every hour)...")
        
        try:
            while True:
                self.run_strategy_cycle()
                print("Waiting 1 hour for next cycle...")
                time.sleep(3600)  # Wait 1 hour
        except KeyboardInterrupt:
            print("\nBot stopped by user")
    
    def run_once(self):
        """Run the bot once for testing"""
        print("Running bot once for testing...")
        self.run_strategy_cycle()
        
        # Show portfolio summary after run
        portfolio = self.executor.get_portfolio_summary()
        print(f"\nPortfolio Summary:")
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
                # Use data collector's APIs
                if platform in self.data_collector.apis:
                    api = self.data_collector.apis[platform]
                    events = api.find_event(keyword, limit)
                    results[platform] = events
                    print(f"   {platform}: Found {len(events)} events")
                else:
                    print(f"   ❌ {platform}: API not initialized")
                    results[platform] = []
            except Exception as e:
                print(f"   ❌ {platform}: Error - {e}")
                results[platform] = []
        
        return results
    
    def execute_trade(self, platform: str, event_id: str, outcome: str, action: str, amount: float, price: float = None) -> Dict:
        """Execute a trade on a specific platform and event"""
        if platform not in self.api_keys:
            return {'success': False, 'error': f'No API key for platform: {platform}'}
        
        try:
            # Use data collector's APIs
            if platform in self.data_collector.apis:
                api = self.data_collector.apis[platform]
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
                
                # Update portfolio tracking if successful
                if result.get('success'):
                    self.executor.portfolio_tracker.update_position(
                        platform, event_id, outcome, amount, 
                        price or result.get('executed_price', 0), action
                    )
                
                return result
            else:
                return {'success': False, 'error': f'Platform {platform} not initialized'}
        except Exception as e:
            error_msg = f"Trade execution failed: {str(e)}"
            print(f"   ❌ {error_msg}")
            return {'success': False, 'error': error_msg}
    
    def find_opportunities(self, markets_data: Dict[str, List[Dict]]) -> List:
        """Find arbitrage opportunities using the strategy with portfolio awareness"""
        print(f"\n🎯 Analyzing arbitrage opportunities...")
        
        # Get current portfolio summary for planning
        portfolio_summary = self.executor.get_portfolio_summary()
        
        # Use portfolio-aware strategy
        opportunities = self.strategy.find_opportunities(markets_data, portfolio_summary)
        
        if opportunities:
            print(f"   Final selected opportunities: {len(opportunities)}")
            # Show top opportunities
            for i, opp in enumerate(opportunities[:3]):
                if hasattr(opp, 'recommended_quantity'):
                    # Typed opportunity
                    size = opp.recommended_quantity or opp.max_quantity
                    expected_return = opp.expected_profit_per_share * size
                    print(f"   {i+1}. {opp.outcome.value} | Size: {size} shares | "
                          f"Spread: {opp.spread:.3f} | Expected: ${expected_return:.2f}")
                    print(f"      Risk: {opp.risk_level.value} | Confidence: {opp.confidence_score:.2f}")
                else:
                    # Legacy dict format
                    print(f"   {i+1}. {opp.get('outcome', 'N/A')} | "
                          f"Expected: ${opp.get('expected_profit', 0):.2f}")
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
        
        print(f"Overall Performance:")
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


# Backward compatibility: expose main function at module level
def main():
    """Main entry point for backward compatibility"""
    orchestrator = TradingOrchestrator()
    try:
        orchestrator.run_continuous()
    except KeyboardInterrupt:
        print("\n👋 Shutting down Quantshit Arbitrage Engine")
    except Exception as e:
        print(f"\n💥 Critical error: {e}")


# Alias for backward compatibility
ArbitrageBot = TradingOrchestrator