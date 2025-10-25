"""
Portfolio tracking functionality separated from trade execution
Responsible for tracking balances, positions, and portfolio state
"""

import time
from typing import Dict, List, Any
from ..types import Position


class PortfolioTracker:
    """
    Responsible solely for tracking portfolio state, balances, and positions
    Single Responsibility: Portfolio state management and tracking
    """
    
    def __init__(self, initial_balances: Dict[str, float] = None):
        """
        Initialize portfolio tracker
        
        Args:
            initial_balances: Starting balances for each platform
        """
        self.virtual_balances = initial_balances or {}
        self.positions = {}  # Legacy position tracking
        self.trade_history = []  # Track all trades
        
        # Set default balances if not provided
        if not self.virtual_balances:
            self.virtual_balances = {}
    
    def initialize_platform(self, platform: str, initial_balance: float = 10000.0):
        """
        Initialize tracking for a new platform
        
        Args:
            platform: Platform name
            initial_balance: Starting virtual balance
        """
        self.virtual_balances[platform] = initial_balance
        self.positions[platform] = {}
    
    def get_virtual_balances(self) -> Dict[str, float]:
        """Get current virtual balances for all platforms"""
        return self.virtual_balances.copy()
    
    def get_positions(self) -> Dict[str, Dict]:
        """Get current positions for all platforms"""
        return self.positions.copy()
    
    def get_portfolio_value(self) -> float:
        """Get total portfolio value including cash and positions"""
        total_cash = sum(self.virtual_balances.values())
        
        # Calculate position values
        total_position_value = 0
        for platform_positions in self.positions.values():
            for position in platform_positions.values():
                shares = position['shares']
                avg_price = position['avg_price']
                total_position_value += shares * avg_price
        
        return total_cash + total_position_value
    
    def get_portfolio_summary(self) -> Dict[str, Any]:
        """Get complete portfolio summary including cash and positions"""
        summary = {}
        total_value = 0
        
        for platform in self.virtual_balances.keys():
            cash = self.virtual_balances[platform]
            positions = self.positions[platform]
            
            # Calculate position values
            position_value = 0
            position_details = []
            
            for position_key, position in positions.items():
                shares = position['shares']
                avg_price = position['avg_price']
                current_value = shares * avg_price
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
    
    def update_balance(self, platform: str, amount: float):
        """
        Update cash balance for a platform
        
        Args:
            platform: Platform name
            amount: Amount to add (negative to subtract)
        """
        if platform not in self.virtual_balances:
            self.initialize_platform(platform)
        
        self.virtual_balances[platform] += amount
    
    def update_position(self, platform: str, market_id: str, outcome: str, 
                       shares: float, price: float, action: str):
        """
        Update position after a trade
        
        Args:
            platform: Platform name
            market_id: Market identifier
            outcome: Trade outcome (YES/NO)
            shares: Number of shares
            price: Price per share
            action: 'buy' or 'sell'
        """
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
            self.update_balance(platform, -(shares * price))
            
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
                self.update_balance(platform, shares * price)
            else:
                # Short selling or error - for now just add cash
                self.update_balance(platform, shares * price)
        
        # Record trade
        self.record_trade(platform, market_id, outcome, action, shares, price)
    
    def record_trade(self, platform: str, market_id: str, outcome: str, 
                    action: str, shares: float, price: float):
        """
        Record a trade in history
        
        Args:
            platform: Platform name
            market_id: Market identifier
            outcome: Trade outcome
            action: 'buy' or 'sell'
            shares: Number of shares
            price: Price per share
        """
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
    
    def get_trade_history(self, limit: int = None) -> List[Dict[str, Any]]:
        """
        Get trade history
        
        Args:
            limit: Maximum number of trades to return
            
        Returns:
            List of trade records
        """
        history = self.trade_history.copy()
        history.reverse()  # Most recent first
        
        if limit:
            history = history[:limit]
            
        return history
    
    def clear_position(self, platform: str, position_key: str) -> bool:
        """
        Clear a specific position
        
        Args:
            platform: Platform name
            position_key: Position identifier
            
        Returns:
            True if position was found and cleared
        """
        if platform in self.positions and position_key in self.positions[platform]:
            del self.positions[platform][position_key]
            return True
        return False