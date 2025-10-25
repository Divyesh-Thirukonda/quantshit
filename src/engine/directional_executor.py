"""
Fixed trade executor for directional arbitrage
"""

import time
from typing import Dict, List

from ..platforms import get_market_api
from .capital_manager import CapitalManager, RiskManager


class DirectionalTradeExecutor:
    """Handles directional arbitrage execution (buy on both platforms)"""
    
    def __init__(self, api_keys: Dict[str, str], initial_balances: Dict[str, float] = None):
        self.api_keys = api_keys
        self.apis = {}
        
        # Initialize capital and risk management
        self.capital_manager = CapitalManager()
        self.risk_manager = RiskManager()
        
        # Initialize APIs for each platform
        for platform, api_key in api_keys.items():
            try:
                self.apis[platform] = get_market_api(platform, api_key)
                print(f"✓ Initialized {platform} API")
                
                # Get and store real balance from platform
                if hasattr(self.apis[platform], 'get_balance'):
                    balance_result = self.apis[platform].get_balance()
                    if balance_result.get('success'):
                        balance = balance_result.get('available_balance', 0)
                        self.capital_manager.update_platform_balance(platform, balance)
                        print(f"  └─ Balance: ${balance:.2f}")
                    else:
                        print(f"  └─ Could not fetch balance: {balance_result.get('error', 'Unknown error')}")
                        # Use provided initial balance or default to 0
                        initial_balance = initial_balances.get(platform, 0) if initial_balances else 0
                        self.capital_manager.update_platform_balance(platform, initial_balance)
                        print(f"  └─ Using initial balance: ${initial_balance:.2f}")
                        
            except Exception as e:
                print(f"✗ Failed to initialize {platform} API: {e}")
    
    def execute_directional_arbitrage(self, opportunity: Dict) -> Dict:
        """Execute a directional arbitrage opportunity (buy on both platforms)"""
        print(f"\n🔄 Executing directional arbitrage:")
        print(f"   Strategy: {opportunity['strategy']}")
        print(f"   Expected profit: ${opportunity['expected_profit']:.4f}")
        print(f"   Total cost: ${opportunity['total_cost']:.4f}")
        
        results = {
            'success': False,
            'trade_a_result': None,
            'trade_b_result': None,
            'error': None
        }
        
        try:
            # Check if we can trade today
            risk_check = self.risk_manager.can_trade()
            if not risk_check['can_trade']:
                results['error'] = f"Risk limits exceeded: {', '.join(risk_check['reasons'])}"
                return results
            
            platform_a = opportunity['platform_a']
            platform_b = opportunity['platform_b']
            market_a = opportunity['market_a']
            market_b = opportunity['market_b']
            amount = opportunity['trade_amount']
            
            # Get APIs
            if platform_a not in self.apis or platform_b not in self.apis:
                results['error'] = f"Missing API for platforms: {platform_a}, {platform_b}"
                return results
            
            api_a = self.apis[platform_a]
            api_b = self.apis[platform_b]
            
            # Calculate required funds for both trades
            if opportunity['strategy'] == 'YES_A_NO_B':
                cost_a = amount * opportunity['yes_price_a']
                cost_b = amount * opportunity['no_price_b']
                
                print(f"   📈 Buying {amount} YES shares on {platform_a} at ${opportunity['yes_price_a']:.4f}")
                trade_a_result = api_a.place_buy_order(
                    market_a['id'], 'YES', amount, opportunity['yes_price_a']
                )
                results['trade_a_result'] = trade_a_result
                
                if not trade_a_result.get('success'):
                    results['error'] = f"Trade A failed: {trade_a_result.get('message', 'Unknown error')}"
                    return results
                
                time.sleep(1)  # Brief delay
                
                print(f"   📉 Buying {amount} NO shares on {platform_b} at ${opportunity['no_price_b']:.4f}")
                trade_b_result = api_b.place_buy_order(
                    market_b['id'], 'NO', amount, opportunity['no_price_b']
                )
                results['trade_b_result'] = trade_b_result
                
            elif opportunity['strategy'] == 'NO_A_YES_B':
                cost_a = amount * opportunity['no_price_a']
                cost_b = amount * opportunity['yes_price_b']
                
                print(f"   📉 Buying {amount} NO shares on {platform_a} at ${opportunity['no_price_a']:.4f}")
                trade_a_result = api_a.place_buy_order(
                    market_a['id'], 'NO', amount, opportunity['no_price_a']
                )
                results['trade_a_result'] = trade_a_result
                
                if not trade_a_result.get('success'):
                    results['error'] = f"Trade A failed: {trade_a_result.get('message', 'Unknown error')}"
                    return results
                
                time.sleep(1)  # Brief delay
                
                print(f"   📈 Buying {amount} YES shares on {platform_b} at ${opportunity['yes_price_b']:.4f}")
                trade_b_result = api_b.place_buy_order(
                    market_b['id'], 'YES', amount, opportunity['yes_price_b']
                )
                results['trade_b_result'] = trade_b_result
            
            if not trade_b_result.get('success'):
                results['error'] = f"Trade B failed: {trade_b_result.get('message', 'Unknown error')}"
                return results
            
            results['success'] = True
            print(f"   ✅ Directional arbitrage executed successfully!")
            print(f"   💰 Profit when event resolves: ${opportunity['expected_profit']:.4f}")
            
            # Record successful trade
            self.risk_manager.record_trade(opportunity['expected_profit'], True)
            
        except Exception as e:
            results['error'] = f"Execution error: {str(e)}"
            print(f"   ❌ Execution failed: {e}")
            self.risk_manager.record_trade(0, False)
        
        return results
    
    def execute_opportunities(self, opportunities: List[Dict], max_trades: int = 3) -> List[Dict]:
        """Execute multiple directional arbitrage opportunities"""
        if not opportunities:
            print("No arbitrage opportunities found.")
            return []
        
        print(f"\n🎯 Found {len(opportunities)} directional arbitrage opportunities")
        
        executed_trades = []
        trades_executed = 0
        
        for i, opportunity in enumerate(opportunities[:max_trades]):
            print(f"\n--- Trade {i + 1}/{min(len(opportunities), max_trades)} ---")
            
            # Show opportunity details
            print(f"Strategy: {opportunity['strategy']}")
            print(f"  Platform A: [{opportunity['platform_a']}] {opportunity['market_a']['title'][:50]}...")
            print(f"  Platform B: [{opportunity['platform_b']}] {opportunity['market_b']['title'][:50]}...")
            print(f"  Expected profit: ${opportunity['expected_profit']:.4f}")
            
            # Execute the trade
            result = self.execute_directional_arbitrage(opportunity)
            result['opportunity'] = opportunity
            executed_trades.append(result)
            
            if result['success']:
                trades_executed += 1
            
            # Delay between trades to avoid rate limits
            if i < len(opportunities) - 1:
                time.sleep(2)
        
        print(f"\n📊 Summary: {trades_executed}/{len(executed_trades)} trades executed successfully")
        return executed_trades
    
    def get_capital_status(self) -> Dict:
        """Get current capital and risk status"""
        capital_summary = self.capital_manager.get_platform_summary()
        
        print("\n💰 Capital Status:")
        print(f"   Total Balance: ${capital_summary['total_balance']:.2f}")
        print(f"   Available Capital: ${capital_summary['available_capital']:.2f}")
        print(f"   Current Exposure: ${capital_summary['current_exposure']:.2f}")
        print(f"   Active Positions: {capital_summary['active_positions']}")
        
        print("\n📊 Platform Balances:")
        for platform, balance in capital_summary['balances'].items():
            print(f"   {platform}: ${balance:.2f}")
        
        print(f"\n⚠️  Risk Status:")
        print(f"   Daily Trades: {self.risk_manager.daily_trades}/{self.risk_manager.max_daily_trades}")
        print(f"   Daily P&L: ${self.risk_manager.daily_pnl:.2f}")
        print(f"   Recent Failures: {len([f for f in self.risk_manager.failed_trades if time.time() - f < 3600])}")
        
        return capital_summary