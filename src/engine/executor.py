from typing import List, Dict
import time
from ..platforms import get_market_api


class TradeExecutor:
    """Handles trade execution across different platforms"""
    
    def __init__(self, api_keys: Dict[str, str]):
        self.api_keys = api_keys
        self.apis = {}
        
        # Initialize APIs for each platform
        for platform, api_key in api_keys.items():
            try:
                self.apis[platform] = get_market_api(platform, api_key)
                print(f"✓ Initialized {platform} API")
            except Exception as e:
                print(f"✗ Failed to initialize {platform} API: {e}")
    
    def execute_arbitrage(self, opportunity: Dict) -> Dict:
        """Execute an arbitrage opportunity"""
        print(f"\n🔄 Executing arbitrage opportunity:")
        print(f"   Outcome: {opportunity['outcome']}")
        print(f"   Expected profit: ${opportunity['expected_profit']:.4f}")
        print(f"   Spread: {opportunity['spread']:.4f}")
        
        results = {
            'success': False,
            'buy_result': None,
            'sell_result': None,
            'error': None
        }
        
        try:
            # Get market info
            buy_market = opportunity['buy_market']
            sell_market = opportunity['sell_market']
            outcome = opportunity['outcome']
            amount = opportunity['trade_amount']
            
            # Get APIs
            buy_platform = buy_market['platform']
            sell_platform = sell_market['platform']
            
            if buy_platform not in self.apis:
                results['error'] = f"No API for buy platform: {buy_platform}"
                return results
            
            if sell_platform not in self.apis:
                results['error'] = f"No API for sell platform: {sell_platform}"
                return results
            
            buy_api = self.apis[buy_platform]
            sell_api = self.apis[sell_platform]
            
            # Execute buy order
            print(f"   📈 Buying {amount} shares of {outcome} on {buy_platform} at ${opportunity['buy_price']:.4f}")
            buy_result = buy_api.place_buy_order(
                buy_market['id'],
                outcome,
                amount,
                opportunity['buy_price']
            )
            results['buy_result'] = buy_result
            
            if not buy_result.get('success'):
                results['error'] = f"Buy order failed: {buy_result.get('message', 'Unknown error')}"
                return results
            
            # Small delay between orders
            time.sleep(1)
            
            # Execute sell order
            print(f"   📉 Selling {amount} shares of {outcome} on {sell_platform} at ${opportunity['sell_price']:.4f}")
            sell_result = sell_api.place_sell_order(
                sell_market['id'],
                outcome,
                amount,
                opportunity['sell_price']
            )
            results['sell_result'] = sell_result
            
            if not sell_result.get('success'):
                results['error'] = f"Sell order failed: {sell_result.get('message', 'Unknown error')}"
                return results
            
            results['success'] = True
            print(f"   ✅ Arbitrage executed successfully!")
            
        except Exception as e:
            results['error'] = f"Execution error: {str(e)}"
            print(f"   ❌ Execution failed: {e}")
        
        return results
    
    def execute_opportunities(self, opportunities: List[Dict], max_trades: int = 3) -> List[Dict]:
        """Execute multiple arbitrage opportunities"""
        if not opportunities:
            print("No arbitrage opportunities found.")
            return []
        
        print(f"\n🎯 Found {len(opportunities)} arbitrage opportunities")
        
        executed_trades = []
        trades_executed = 0
        
        for i, opportunity in enumerate(opportunities[:max_trades]):
            print(f"\n--- Trade {i + 1}/{min(len(opportunities), max_trades)} ---")
            
            # Show opportunity details
            buy_market = opportunity['buy_market']
            sell_market = opportunity['sell_market']
            
            print(f"Market Match:")
            print(f"  Buy:  [{buy_market['platform']}] {buy_market['title'][:60]}...")
            print(f"  Sell: [{sell_market['platform']}] {sell_market['title'][:60]}...")
            
            # Execute the trade
            result = self.execute_arbitrage(opportunity)
            result['opportunity'] = opportunity
            executed_trades.append(result)
            
            if result['success']:
                trades_executed += 1
            
            # Delay between trades to avoid rate limits
            if i < len(opportunities) - 1:
                time.sleep(2)
        
        print(f"\n📊 Summary: {trades_executed}/{len(executed_trades)} trades executed successfully")
        return executed_trades