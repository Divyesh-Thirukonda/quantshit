import time
import uuid
from typing import Dict, List, Union, Optional
from datetime import datetime

from ..platforms import get_market_api
from ..types import (
    ArbitrageOpportunity, TradePlan, TradeLeg, Order, OrderStatus, 
    ExecutionResult, PlanStatus, LegType, OrderType, Fill, OrderAck,
    create_order_from_leg, TradeExecution
)


class TradeExecutor:
    """Handles paper trading execution (simulation only)"""
    
    def __init__(self, api_keys: Dict[str, str], paper_trading: bool = True):
        self.api_keys = api_keys
        self.apis = {}
        self.paper_trading = paper_trading
        self.virtual_balances = {}  # Cash balances
        self.positions = {}  # Position tracking
        self.trade_history = []  # Track all trades
        
        # Initialize APIs for each platform
        for platform, api_key in api_keys.items():
            try:
                self.apis[platform] = get_market_api(platform, api_key)
                # Initialize virtual balance and positions for paper trading
                self.virtual_balances[platform] = 10000.0  # Start with $10k per platform
                self.positions[platform] = {}  # Track positions per platform
                print(f"✓ Initialized {platform} API (Paper Trading)")
                print(f"  └─ Virtual Balance: ${self.virtual_balances[platform]:,.2f}")
            except Exception as e:
                print(f"✗ Failed to initialize {platform} API: {e}")
    
    def get_virtual_balances(self) -> Dict[str, float]:
        """Get current virtual balances for all platforms"""
        return self.virtual_balances.copy()
    
    def get_positions(self) -> Dict[str, Dict]:
        """Get current positions for all platforms"""
        return self.positions.copy()
    
    def get_portfolio_summary(self) -> Dict[str, Dict]:
        """Get complete portfolio summary including cash and positions"""
        summary = {}
        total_value = 0
        
        for platform in self.virtual_balances.keys():
            cash = self.virtual_balances[platform]
            positions = self.positions[platform]
            
            # Calculate position values (using current market price estimates)
            position_value = 0
            position_details = []
            
            for position_key, position in positions.items():
                shares = position['shares']
                avg_price = position['avg_price']
                current_value = shares * avg_price  # Simplified - in reality would use current market price
                position_value += current_value
                
                position_details.append({
                    'market': position_key,
                    'shares': shares,
                    'avg_price': avg_price,
                    'current_value': current_value,
                    'unrealized_pnl': current_value - (shares * avg_price)
                })
            
            platform_total = cash + position_value
            total_value += platform_total
            
            summary[platform] = {
                'cash': cash,
                'position_value': position_value,
                'total_value': platform_total,
                'positions': position_details
            }
        
        summary['total_portfolio_value'] = total_value
        return summary
    
    def update_position(self, platform: str, market_id: str, outcome: str, shares: float, price: float, action: str):
        """Update position after a trade"""
        position_key = f"{market_id}_{outcome}"
        
        if platform not in self.positions:
            self.positions[platform] = {}
        
        current_position = self.positions[platform].get(position_key, {
            'shares': 0,
            'avg_price': 0,
            'total_cost': 0
        })
        
        if action == 'buy':
            # Add to position
            new_shares = current_position['shares'] + shares
            new_cost = current_position['total_cost'] + (shares * price)
            new_avg_price = new_cost / new_shares if new_shares > 0 else 0
            
            self.positions[platform][position_key] = {
                'shares': new_shares,
                'avg_price': new_avg_price,
                'total_cost': new_cost
            }
            
            # Reduce cash balance
            self.virtual_balances[platform] -= shares * price
            
        elif action == 'sell':
            # Reduce position
            if current_position['shares'] >= shares:
                new_shares = current_position['shares'] - shares
                
                if new_shares > 0:
                    # Partial sale - reduce proportionally
                    remaining_cost = current_position['total_cost'] * (new_shares / current_position['shares'])
                    self.positions[platform][position_key] = {
                        'shares': new_shares,
                        'avg_price': current_position['avg_price'],
                        'total_cost': remaining_cost
                    }
                else:
                    # Full sale - remove position
                    del self.positions[platform][position_key]
                
                # Add cash from sale
                self.virtual_balances[platform] += shares * price
                
            else:
                # Short selling or error - for now just add cash
                self.virtual_balances[platform] += shares * price
        
        # Record trade
        self.trade_history.append({
            'timestamp': time.time(),
            'platform': platform,
            'market_id': market_id,
            'outcome': outcome,
            'action': action,
            'shares': shares,
            'price': price,
            'value': shares * price
        })
    
    def execute_arbitrage(self, opportunity) -> Dict:
        """Execute an arbitrage opportunity (accepts both ArbitrageOpportunity objects and dicts)"""
        # Handle both typed objects and legacy dicts
        if hasattr(opportunity, 'to_legacy_dict'):
            # ArbitrageOpportunity object - convert to dict for execution
            opp_dict = opportunity.to_legacy_dict()
            print(f"\n🔄 Executing arbitrage opportunity (ID: {opportunity.id}):")
            print(f"   Outcome: {opportunity.outcome.value}")
            print(f"   Expected profit per share: ${opportunity.expected_profit_per_share:.4f}")
            print(f"   Spread: {opportunity.spread:.4f}")
            print(f"   Risk Level: {opportunity.risk_level.value}")
            print(f"   Confidence: {opportunity.confidence_score:.2f}")
        else:
            # Legacy dict format
            opp_dict = opportunity
            print(f"\n🔄 Executing arbitrage opportunity:")
            print(f"   Outcome: {opp_dict['outcome']}")
            print(f"   Expected profit: ${opp_dict['expected_profit']:.4f}")
            print(f"   Spread: {opp_dict['spread']:.4f}")
        
        results = {
            'success': False,
            'buy_result': None,
            'sell_result': None,
            'error': None
        }
        
        try:
            # Get trade details with planned sizing - works with both types
            if hasattr(opportunity, 'buy_market'):
                # ArbitrageOpportunity object
                buy_market = opportunity.buy_market.to_dict()
                sell_market = opportunity.sell_market.to_dict()
                outcome = opportunity.outcome.value
                amount = opportunity.recommended_quantity or opportunity.max_quantity
                buy_price = opportunity.buy_price
                sell_price = opportunity.sell_price
            else:
                # Legacy dict format
                buy_market = opportunity['buy_market']
                sell_market = opportunity['sell_market']
                outcome = opportunity['outcome']
                amount = opportunity.get('position_size', opportunity.get('trade_amount', 100))
                buy_price = opportunity['buy_price']
                sell_price = opportunity['sell_price']
            
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
            print(f"   📈 Buying {amount} shares of {outcome} on {buy_platform} at ${buy_price:.4f}")
            buy_result = buy_api.place_buy_order(
                buy_market['id'],
                outcome,
                amount,
                buy_price
            )
            results['buy_result'] = buy_result
            
            if not buy_result.get('success'):
                results['error'] = f"Buy order failed: {buy_result.get('message', 'Unknown error')}"
                return results
            
            # Update position for buy
            self.update_position(
                buy_platform, 
                buy_market['id'], 
                outcome, 
                amount, 
                buy_price, 
                'buy'
            )
            
            # Small delay between orders
            time.sleep(1)
            
            # Execute sell order
            print(f"   📉 Selling {amount} shares of {outcome} on {sell_platform} at ${sell_price:.4f}")
            sell_result = sell_api.place_sell_order(
                sell_market['id'],
                outcome,
                amount,
                sell_price
            )
            results['sell_result'] = sell_result
            
            if not sell_result.get('success'):
                results['error'] = f"Sell order failed: {sell_result.get('message', 'Unknown error')}"
                return results
            
            # Update position for sell
            self.update_position(
                sell_platform, 
                sell_market['id'], 
                outcome, 
                amount, 
                sell_price, 
                'sell'
            )
            
            results['success'] = True
            print(f"   ✅ Arbitrage executed successfully!")
            
            # Show updated balances after trade
            print(f"   💰 Updated Balances:")
            print(f"      {buy_platform}: ${self.virtual_balances[buy_platform]:,.2f}")
            print(f"      {sell_platform}: ${self.virtual_balances[sell_platform]:,.2f}")
            
        except Exception as e:
            results['error'] = f"Execution error: {str(e)}"
            print(f"   ❌ Execution failed: {e}")
        
        return results
    
    def execute_opportunities(self, opportunities: List, max_trades: int = 3) -> List[Dict]:
        """Execute multiple arbitrage opportunities (handles both typed objects and dicts)"""
        if not opportunities:
            print("No arbitrage opportunities found.")
            return []
        
        print(f"\n🎯 Found {len(opportunities)} arbitrage opportunities")
        
        executed_trades = []
        trades_executed = 0
        
        for i, opportunity in enumerate(opportunities[:max_trades]):
            print(f"\n--- Trade {i + 1}/{min(len(opportunities), max_trades)} ---")
            
            # Show opportunity details - handle both types
            if hasattr(opportunity, 'buy_market'):
                # ArbitrageOpportunity object
                buy_market = opportunity.buy_market
                sell_market = opportunity.sell_market
                print(f"Market Match:")
                print(f"  Buy:  [{buy_market.platform.value}] {buy_market.title[:60]}...")
                print(f"  Sell: [{sell_market.platform.value}] {sell_market.title[:60]}...")
            else:
                # Legacy dict format
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
    
    def place(self, executable_item: Union[TradePlan, ArbitrageOpportunity, List[ArbitrageOpportunity]]) -> Union[ExecutionResult, TradeExecution, List[TradeExecution]]:
        """
        Universal place() method that takes TradePlan, ArbitrageOpportunity, or list of opportunities
        Returns appropriate execution result type
        """
        if isinstance(executable_item, TradePlan):
            return self.execute_plan(executable_item)
        elif isinstance(executable_item, ArbitrageOpportunity):
            return self.execute_arbitrage(executable_item)
        elif isinstance(executable_item, list):
            return self.execute_opportunities(executable_item)
        else:
            raise ValueError(f"Unsupported executable item type: {type(executable_item)}")
    
    def execute_plan(self, plan: TradePlan) -> ExecutionResult:
        """
        Execute a complete TradePlan with proper leg sequencing and dependency management
        """
        print(f"\n🎯 Executing Trade Plan: {plan.name}")
        print(f"   Plan ID: {plan.plan_id}")
        print(f"   Strategy: {plan.strategy_type}")
        print(f"   Legs: {plan.num_legs}")
        print(f"   Expected Return: ${plan.expected_total_return:.2f} ({plan.expected_return_pct:.1f}%)")
        
        plan.status = PlanStatus.EXECUTING
        plan.start_time = datetime.now()
        
        executed_legs = []
        failed_legs = []
        error_messages = []
        warnings = []
        total_profit = 0.0
        total_fees = 0.0
        
        start_time = time.time()
        
        try:
            # Execute legs in dependency order
            remaining_legs = plan.legs.copy()
            max_iterations = len(plan.legs) * 2  # Prevent infinite loops
            iteration = 0
            
            while remaining_legs and iteration < max_iterations:
                iteration += 1
                executed_leg_ids = [leg.leg_id for leg in executed_legs]
                
                # Find legs that can be executed now
                executable_legs = [
                    leg for leg in remaining_legs 
                    if leg.can_execute(executed_leg_ids)
                ]
                
                if not executable_legs:
                    # Check if we're waiting on failed legs
                    failed_leg_ids = [leg.leg_id for leg in failed_legs]
                    waiting_on_failed = any(
                        any(dep in failed_leg_ids for dep in leg.dependency_legs)
                        for leg in remaining_legs
                    )
                    
                    if waiting_on_failed:
                        warnings.append("Some legs depend on failed legs - skipping")
                        failed_legs.extend(remaining_legs)
                        break
                    else:
                        warnings.append("Circular dependency detected or unresolvable dependencies")
                        break
                
                # Execute legs in priority order
                executable_legs.sort(key=lambda x: x.priority)
                
                for leg in executable_legs:
                    print(f"\n   🔄 Executing Leg: {leg.leg_id} ({leg.leg_type.value})")
                    print(f"      Market: [{leg.market.platform.value}] {leg.market.title[:50]}...")
                    print(f"      {leg.order_type.value.upper()} {leg.target_quantity} {leg.outcome.value} @ ${leg.target_price:.4f}")
                    
                    try:
                        # Create and execute order for this leg
                        order_id = f"{plan.plan_id}_{leg.leg_id}_{int(time.time())}"
                        order = create_order_from_leg(leg, order_id)
                        
                        # Execute the order using platform API
                        platform_api = self.apis[leg.market.platform.value]
                        
                        if leg.order_type == OrderType.BUY:
                            api_result = platform_api.place_buy_order(
                                leg.market.id,
                                leg.outcome.value,
                                leg.target_quantity,
                                leg.target_price
                            )
                        else:
                            api_result = platform_api.place_sell_order(
                                leg.market.id,
                                leg.outcome.value,
                                leg.target_quantity,
                                leg.target_price
                            )
                        
                        if api_result.get('success'):
                            # Simulate fill
                            fill = Fill(
                                fill_id=f"fill_{order_id}",
                                order_id=order_id,
                                quantity=leg.target_quantity,
                                price=leg.target_price,
                                timestamp=datetime.now(),
                                fees=leg.target_quantity * leg.target_price * 0.01  # 1% fee
                            )
                            
                            order.add_fill(fill)
                            order.status = OrderStatus.FILLED
                            leg.order = order
                            
                            # Update virtual balances and positions
                            self.update_position(
                                leg.market.platform.value,
                                leg.market.id,
                                leg.outcome.value,
                                leg.target_quantity,
                                leg.target_price,
                                leg.order_type.value
                            )
                            
                            executed_legs.append(leg)
                            total_profit += fill.total_value if leg.leg_type == LegType.SELL_LEG else -fill.total_value
                            total_fees += fill.fees
                            
                            print(f"      ✅ Leg executed successfully!")
                            print(f"      💰 Balance: ${self.virtual_balances[leg.market.platform.value]:,.2f}")
                            
                        else:
                            error_msg = f"API execution failed for leg {leg.leg_id}: {api_result.get('message', 'Unknown error')}"
                            error_messages.append(error_msg)
                            failed_legs.append(leg)
                            print(f"      ❌ Leg failed: {api_result.get('message', 'Unknown error')}")
                    
                    except Exception as e:
                        error_msg = f"Exception executing leg {leg.leg_id}: {str(e)}"
                        error_messages.append(error_msg)
                        failed_legs.append(leg)
                        print(f"      ❌ Leg failed: {e}")
                    
                    # Remove from remaining legs
                    remaining_legs.remove(leg)
                    
                    # Small delay between legs
                    time.sleep(0.5)
        
        except Exception as e:
            error_messages.append(f"Plan execution error: {str(e)}")
            plan.status = PlanStatus.FAILED
        
        # Determine final status
        if not failed_legs and executed_legs:
            plan.status = PlanStatus.COMPLETED
        elif executed_legs:
            plan.status = PlanStatus.COMPLETED  # Partial success still counts as completed
        else:
            plan.status = PlanStatus.FAILED
        
        plan.completion_time = datetime.now()
        execution_time = (time.time() - start_time) * 1000
        
        result = ExecutionResult(
            plan_id=plan.plan_id,
            status=plan.status,
            executed_legs=executed_legs,
            failed_legs=failed_legs,
            total_profit=total_profit,
            total_fees=total_fees,
            execution_time_ms=execution_time,
            error_messages=error_messages,
            warnings=warnings,
            start_time=plan.start_time,
            end_time=plan.completion_time
        )
        
        print(f"\n📊 Plan Execution Summary:")
        print(f"   Status: {plan.status.value}")
        print(f"   Executed: {len(executed_legs)}/{plan.num_legs} legs")
        print(f"   Total Profit: ${result.net_profit:.2f}")
        print(f"   Execution Time: {execution_time:.1f}ms")
        
        if error_messages:
            print(f"   Errors: {len(error_messages)}")
        if warnings:
            print(f"   Warnings: {len(warnings)}")
        
        return result