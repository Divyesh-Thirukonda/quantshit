"""
Paper trading API - simulates real trading without actual money
"""

import time
import random
from typing import Dict, List
from .base import BaseMarketAPI


class PaperTradingAPI(BaseMarketAPI):
    """Paper trading implementation that simulates real trading"""
    
    def __init__(self, platform_name: str, initial_balance: float = 10000):
        super().__init__("paper_trading_key")
        self.platform_name = platform_name
        self.balance = initial_balance
        self.available_balance = initial_balance
        self.positions = {}  # {market_id_outcome: shares}
        self.orders = {}  # {order_id: order_details}
        self.order_counter = 0
        self.trade_history = []
        
        # Simulate some slippage and failure rates for realism
        self.slippage_rate = 0.001  # 0.1% average slippage
        self.failure_rate = 0.02   # 2% order failure rate
        
    def get_balance(self) -> Dict:
        """Get current account balance"""
        return {
            'success': True,
            'balance': self.balance,
            'available_balance': self.available_balance
        }
    
    def get_positions(self, market_id: str = None) -> Dict:
        """Get current positions"""
        if market_id:
            # Filter positions for specific market
            market_positions = {
                key: shares for key, shares in self.positions.items() 
                if key.startswith(f"{market_id}_")
            }
            return {'success': True, 'positions': market_positions}
        
        return {'success': True, 'positions': self.positions.copy()}
    
    def _simulate_order_execution(self, order_type: str, amount: float, price: float) -> Dict:
        """Simulate realistic order execution with slippage and potential failures"""
        
        # Simulate random failures
        if random.random() < self.failure_rate:
            failure_reasons = [
                "Insufficient liquidity",
                "Price moved beyond limit",
                "Market temporarily suspended",
                "Order rejected by exchange"
            ]
            return {
                'success': False,
                'message': f'Order failed: {random.choice(failure_reasons)}'
            }
        
        # Simulate slippage (price moves slightly against us)
        slippage = random.gauss(0, self.slippage_rate)
        if order_type == 'buy':
            executed_price = price * (1 + abs(slippage))  # Buy higher
        else:
            executed_price = price * (1 - abs(slippage))  # Sell lower
        
        # Keep price within reasonable bounds
        executed_price = max(0.01, min(0.99, executed_price))
        
        self.order_counter += 1
        order_id = f"{self.platform_name}_paper_{self.order_counter}"
        
        return {
            'success': True,
            'order_id': order_id,
            'executed_price': executed_price,
            'executed_amount': amount,
            'slippage': executed_price - price
        }
    
    def place_buy_order(self, market_id: str, outcome: str, amount: float, price: float) -> Dict:
        """Simulate buy order execution"""
        try:
            required_funds = amount * price
            
            # Check if we have enough balance
            if self.available_balance < required_funds:
                return {
                    'success': False,
                    'message': f'Insufficient funds. Need ${required_funds:.2f}, have ${self.available_balance:.2f}'
                }
            
            # Simulate order execution
            execution_result = self._simulate_order_execution('buy', amount, price)
            
            if not execution_result['success']:
                return execution_result
            
            # Execute the trade
            executed_price = execution_result['executed_price']
            actual_cost = amount * executed_price
            
            # Update balance
            self.available_balance -= actual_cost
            self.balance -= actual_cost
            
            # Update positions
            position_key = f"{market_id}_{outcome}"
            self.positions[position_key] = self.positions.get(position_key, 0) + amount
            
            # Record trade
            trade_record = {
                'timestamp': time.time(),
                'type': 'buy',
                'market_id': market_id,
                'outcome': outcome,
                'amount': amount,
                'price': executed_price,
                'cost': actual_cost,
                'slippage': execution_result['slippage']
            }
            self.trade_history.append(trade_record)
            
            return {
                'success': True,
                'order_id': execution_result['order_id'],
                'status': 'filled',
                'executed_price': executed_price,
                'slippage': execution_result['slippage'],
                'message': f'Buy order filled: {amount} shares of {outcome} at ${executed_price:.4f} (slippage: ${execution_result["slippage"]:.4f})'
            }
            
        except Exception as e:
            return {'success': False, 'message': f'Buy order error: {str(e)}'}
    
    def place_sell_order(self, market_id: str, outcome: str, amount: float, price: float) -> Dict:
        """Simulate sell order execution"""
        try:
            position_key = f"{market_id}_{outcome}"
            owned_shares = self.positions.get(position_key, 0)
            
            # Check if we own enough shares
            if owned_shares < amount:
                return {
                    'success': False,
                    'message': f'Insufficient shares. Need {amount}, own {owned_shares}'
                }
            
            # Simulate order execution
            execution_result = self._simulate_order_execution('sell', amount, price)
            
            if not execution_result['success']:
                return execution_result
            
            # Execute the trade
            executed_price = execution_result['executed_price']
            proceeds = amount * executed_price
            
            # Update balance
            self.available_balance += proceeds
            self.balance += proceeds
            
            # Update positions
            self.positions[position_key] -= amount
            if self.positions[position_key] <= 0:
                del self.positions[position_key]
            
            # Record trade
            trade_record = {
                'timestamp': time.time(),
                'type': 'sell',
                'market_id': market_id,
                'outcome': outcome,
                'amount': amount,
                'price': executed_price,
                'proceeds': proceeds,
                'slippage': execution_result['slippage']
            }
            self.trade_history.append(trade_record)
            
            return {
                'success': True,
                'order_id': execution_result['order_id'],
                'status': 'filled',
                'executed_price': executed_price,
                'slippage': execution_result['slippage'],
                'message': f'Sell order filled: {amount} shares of {outcome} at ${executed_price:.4f} (slippage: ${execution_result["slippage"]:.4f})'
            }
            
        except Exception as e:
            return {'success': False, 'message': f'Sell order error: {str(e)}'}
    
    def get_recent_markets(self, min_volume: float = 1000) -> List[Dict]:
        """Get mock market data - delegate to platform-specific implementations"""
        # This should be overridden by platform-specific paper trading classes
        return []
    
    def get_trade_history(self) -> List[Dict]:
        """Get trading history for analysis"""
        return self.trade_history.copy()
    
    def get_performance_summary(self) -> Dict:
        """Get performance summary"""
        if not self.trade_history:
            return {
                'total_trades': 0,
                'total_pnl': 0,
                'win_rate': 0,
                'avg_trade_pnl': 0
            }
        
        total_trades = len(self.trade_history)
        total_cost = sum(t['cost'] for t in self.trade_history if t['type'] == 'buy')
        total_proceeds = sum(t['proceeds'] for t in self.trade_history if t['type'] == 'sell')
        total_pnl = total_proceeds - total_cost
        
        # Calculate win rate (simplified)
        profitable_trades = sum(1 for t in self.trade_history if t.get('slippage', 0) < 0.01)
        win_rate = profitable_trades / total_trades if total_trades > 0 else 0
        
        return {
            'total_trades': total_trades,
            'total_pnl': total_pnl,
            'win_rate': win_rate,
            'avg_trade_pnl': total_pnl / total_trades if total_trades > 0 else 0,
            'current_balance': self.balance
        }