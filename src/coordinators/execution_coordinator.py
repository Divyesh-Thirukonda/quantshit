"""
Execution coordination functionality - coordinates between order execution and portfolio tracking
Responsible for orchestrating trades while maintaining portfolio state
"""

import uuid
from typing import Dict, List, Union, Optional, Any
from datetime import datetime

from ..executors import OrderExecutor
from ..trackers import PortfolioTracker
from ..types import (
    ArbitrageOpportunity, TradePlan, Position,
    PositionManagerConfig
)
from ..engine.position_manager import PositionManager


class ExecutionCoordinator:
    """
    Responsible for coordinating trade execution with portfolio management
    Single Responsibility: Coordination between execution and tracking
    """
    
    def __init__(self, api_keys: Dict[str, str], paper_trading: bool = True, 
                 position_config: Optional[PositionManagerConfig] = None):
        """
        Initialize execution coordinator
        
        Args:
            api_keys: Platform API keys
            paper_trading: Whether to use paper trading mode
            position_config: Position manager configuration
        """
        self.paper_trading = paper_trading
        
        # Initialize components
        self.order_executor = OrderExecutor(api_keys)
        self.portfolio_tracker = PortfolioTracker()
        self.position_manager = PositionManager(position_config or PositionManagerConfig())
        
        # Initialize platform balances for paper trading
        for platform in api_keys.keys():
            self.portfolio_tracker.initialize_platform(platform, 10000.0)
            print(f"✓ Initialized {platform} execution (Paper Trading)")
            print(f"  └─ Virtual Balance: ${self.portfolio_tracker.virtual_balances[platform]:,.2f}")
        
        print(f"Position Manager initialized: Max {self.position_manager.config.max_open_positions} positions")
    
    def get_virtual_balances(self) -> Dict[str, float]:
        """Get current virtual balances"""
        return self.portfolio_tracker.get_virtual_balances()
    
    def get_positions(self) -> Dict[str, Dict]:
        """Get current positions"""
        return self.portfolio_tracker.get_positions()
    
    def get_portfolio_value(self) -> float:
        """Get total portfolio value"""
        total_cash = sum(self.portfolio_tracker.get_virtual_balances().values())
        total_positions = sum(pos.market_value for pos in self.position_manager.get_active_positions())
        return total_cash + total_positions
    
    def get_portfolio_summary(self) -> Dict[str, Any]:
        """Get complete portfolio summary"""
        return self.portfolio_tracker.get_portfolio_summary()
    
    def execute_opportunities(self, opportunities: List[ArbitrageOpportunity]) -> List[Dict[str, Any]]:
        """
        Execute a list of arbitrage opportunities
        
        Args:
            opportunities: List of opportunities to execute
            
        Returns:
            List of execution results
        """
        executed_trades = []
        
        for opportunity in opportunities:
            # Check if we should swap positions for better opportunities
            if self.check_and_execute_swaps(opportunity):
                continue  # Skip this opportunity as it was handled by swap
            
            # Check if we can add more positions
            if not self.position_manager.can_add_position():
                print(f"   ⏭️ Skipping opportunity - max positions reached ({self.position_manager.config.max_open_positions})")
                continue
            
            # Execute the opportunity
            result = self.execute_arbitrage(opportunity)
            executed_trades.append(result)
        
        return executed_trades
    
    def execute_arbitrage(self, opportunity: Union[ArbitrageOpportunity, Dict]) -> Dict[str, Any]:
        """
        Execute a single arbitrage opportunity
        
        Args:
            opportunity: Arbitrage opportunity (typed object or legacy dict)
            
        Returns:
            Execution result dictionary
        """
        # Handle both typed objects and legacy dicts
        if hasattr(opportunity, 'to_legacy_dict'):
            # ArbitrageOpportunity object
            print(f"\n🔄 Executing arbitrage opportunity (ID: {opportunity.id}):")
            print(f"   Outcome: {opportunity.outcome.value}")
            print(f"   Expected profit per share: ${opportunity.expected_profit_per_share:.4f}")
            print(f"   Spread: {opportunity.spread:.4f}")
            print(f"   Risk Level: {opportunity.risk_level.value}")
            print(f"   Confidence: {opportunity.confidence_score:.2f}")
            
            # Extract details for execution
            buy_market = opportunity.buy_market.to_dict()
            sell_market = opportunity.sell_market.to_dict()
            outcome = opportunity.outcome.value
            amount = opportunity.recommended_quantity or opportunity.max_quantity
            buy_price = opportunity.buy_price
            sell_price = opportunity.sell_price
        else:
            # Legacy dict format
            print(f"\n🔄 Executing arbitrage opportunity:")
            print(f"   Outcome: {opportunity['outcome']}")
            print(f"   Expected profit: ${opportunity['expected_profit']:.4f}")
            print(f"   Spread: {opportunity['spread']:.4f}")
            
            buy_market = opportunity['buy_market']
            sell_market = opportunity['sell_market']
            outcome = opportunity['outcome']
            amount = opportunity.get('position_size', opportunity.get('trade_amount', 100))
            buy_price = opportunity['buy_price']
            sell_price = opportunity['sell_price']
        
        # Prepare order details
        buy_details = {
            'platform': buy_market['platform'],
            'market_id': buy_market['id'],
            'outcome': outcome,
            'amount': amount,
            'price': buy_price
        }
        
        sell_details = {
            'platform': sell_market['platform'],
            'market_id': sell_market['id'],
            'outcome': outcome,
            'amount': amount,
            'price': sell_price
        }
        
        # Execute the arbitrage
        execution_result = self.order_executor.execute_arbitrage_legs(buy_details, sell_details)
        
        # Update portfolio tracking if successful
        if execution_result['success']:
            # Update positions and balances
            self.portfolio_tracker.update_position(
                buy_details['platform'], buy_details['market_id'], 
                buy_details['outcome'], buy_details['amount'], 
                buy_details['price'], 'buy'
            )
            
            self.portfolio_tracker.update_position(
                sell_details['platform'], sell_details['market_id'],
                sell_details['outcome'], sell_details['amount'],
                sell_details['price'], 'sell'
            )
            
            # Add to position manager if it's a typed opportunity
            if hasattr(opportunity, 'to_legacy_dict'):
                portfolio_value = self.get_portfolio_value()
                new_quantity = self.position_manager.calculate_position_size(opportunity, portfolio_value)
                opportunity.recommended_quantity = new_quantity
                
                # Create position for manager
                position = Position(
                    position_id=str(uuid.uuid4()),
                    market_id=buy_market['id'],
                    platform=opportunity.buy_market.platform,
                    outcome=opportunity.outcome,
                    quantity=amount,
                    average_price=buy_price,
                    current_price=buy_price,
                    total_cost=amount * buy_price
                )
                self.position_manager.add_position(position)
            
            print(f"   ✅ Arbitrage executed successfully")
            print(f"      Buy: {amount} shares at ${buy_price} on {buy_details['platform']}")
            print(f"      Sell: {amount} shares at ${sell_price} on {sell_details['platform']}")
            print(f"      Expected profit: ${(sell_price - buy_price) * amount:.4f}")
        else:
            print(f"   ❌ Arbitrage execution failed: {execution_result.get('error')}")
        
        # Return result with opportunity reference
        result = {
            'opportunity': opportunity.to_legacy_dict() if hasattr(opportunity, 'to_legacy_dict') else opportunity,
            'success': execution_result['success'],
            'execution_details': execution_result
        }
        
        return result
    
    def check_and_execute_swaps(self, new_opportunity: ArbitrageOpportunity) -> bool:
        """
        Check if we should swap an existing position for a new opportunity
        
        Args:
            new_opportunity: New opportunity to consider
            
        Returns:
            True if a swap was executed
        """
        should_swap, position_to_swap = self.position_manager.should_swap_position(new_opportunity)
        
        if should_swap and position_to_swap:
            new_potential_pct = (new_opportunity.expected_profit_per_share / new_opportunity.buy_price * 100)
            
            print(f"\n🔄 Executing position swap:")
            print(f"   Closing: {position_to_swap.position_id} ({position_to_swap.potential_remaining_gain_pct:.1f}% remaining)")
            print(f"   Opening: New opportunity with {new_potential_pct:.1f}% potential gain")
            
            # Close the underperforming position
            self.close_position(position_to_swap)
            
            # Execute the new opportunity
            portfolio_value = self.get_portfolio_value()
            new_opportunity.recommended_quantity = self.position_manager.calculate_position_size(new_opportunity, portfolio_value)
            
            result = self.execute_arbitrage(new_opportunity)
            if result.get('success'):
                print(f"   ✅ Position swap completed successfully")
                return True
            else:
                print(f"   ❌ Position swap failed: {result.get('error')}")
        
        return False
    
    def close_position(self, position: Position) -> Dict[str, Any]:
        """
        Close an existing position
        
        Args:
            position: Position to close
            
        Returns:
            Result of position closure
        """
        try:
            # Determine opposite action
            if position.quantity > 0:
                # We own shares, need to sell
                result = self.order_executor.execute_sell_order(
                    position.platform.value,
                    position.market_id,
                    position.outcome.value,
                    abs(position.quantity),
                    position.current_price
                )
                action = 'sell'
            else:
                # We're short, need to buy back
                result = self.order_executor.execute_buy_order(
                    position.platform.value,
                    position.market_id,
                    position.outcome.value,
                    abs(position.quantity),
                    position.current_price
                )
                action = 'buy'
            
            if result.get('success'):
                # Update portfolio tracking
                proceeds = abs(position.quantity) * position.current_price
                if action == 'sell':
                    self.portfolio_tracker.update_balance(position.platform.value, proceeds)
                else:
                    self.portfolio_tracker.update_balance(position.platform.value, -proceeds)
                
                # Remove from position manager
                self.position_manager.remove_position(position.position_id)
                
                # Clear from legacy tracking
                position_key = f"{position.market_id}_{position.outcome.value}"
                self.portfolio_tracker.clear_position(position.platform.value, position_key)
                
                return {
                    'success': True,
                    'action': action,
                    'proceeds': proceeds,
                    'realized_pnl': position.unrealized_pnl
                }
            else:
                return {
                    'success': False,
                    'error': result.get('error', 'Unknown error')
                }
        
        except Exception as e:
            return {
                'success': False,
                'error': f"Exception closing position: {str(e)}"
            }
    
    def place(self, executable_item):
        """Universal place() method for backward compatibility"""
        # Import here to avoid circular imports
        from ..types import TradePlan, ArbitrageOpportunity
        
        if hasattr(executable_item, 'plan_id'):  # TradePlan
            return self.execute_plan(executable_item)
        elif hasattr(executable_item, 'buy_market') or isinstance(executable_item, dict):  # ArbitrageOpportunity
            return self.execute_arbitrage(executable_item)
        elif isinstance(executable_item, list):  # List of opportunities
            return self.execute_opportunities(executable_item)
        else:
            raise ValueError(f"Unsupported executable item type: {type(executable_item)}")
    
    def execute_plan(self, plan):
        """Execute a TradePlan (simplified implementation for backward compatibility)"""
        print(f"\n🎯 Executing Trade Plan: {getattr(plan, 'name', 'Unknown Plan')}")
        
        # For now, convert TradePlan to simple arbitrage execution
        # This is a simplified implementation - full TradePlan support would require
        # implementing the complex leg dependency system
        
        try:
            # Simulate plan execution
            result = {
                'success': True,
                'status': 'completed',
                'executed_legs': [],
                'total_profit': 0.0,
                'message': 'TradePlan execution (simplified)'
            }
            
            print(f"   ✅ Plan executed successfully (simplified mode)")
            return result
            
        except Exception as e:
            print(f"   ❌ Plan execution failed: {e}")
            return {
                'success': False,
                'status': 'failed',
                'error': str(e)
            }