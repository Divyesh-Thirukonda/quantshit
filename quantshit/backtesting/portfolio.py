"""
Portfolio management for backtesting
"""

from typing import Dict, List, Optional
from datetime import datetime
from .models import Position, Trade, OrderType, Market


class Portfolio:
    """
    Manages portfolio state including positions, cash, and P&L tracking
    
    Attributes:
        initial_capital: Starting capital
        cash: Current available cash
        positions: Dictionary of active positions by market_id and outcome
        trades: List of all executed trades
        commission_rate: Trading commission as a percentage (default 0.01 = 1%)
    """
    
    def __init__(self, initial_capital: float, commission_rate: float = 0.01):
        """
        Initialize portfolio
        
        Args:
            initial_capital: Starting capital amount
            commission_rate: Trading commission rate (default 0.01 = 1%)
        """
        self.initial_capital = initial_capital
        self.cash = initial_capital
        self.positions: Dict[tuple, Position] = {}  # (market_id, outcome) -> Position
        self.trades: List[Trade] = []
        self.commission_rate = commission_rate
    
    def get_position(self, market_id: str, outcome: bool) -> Optional[Position]:
        """Get position for a specific market and outcome"""
        return self.positions.get((market_id, outcome))
    
    def execute_trade(self, trade: Trade) -> bool:
        """
        Execute a trade and update portfolio state
        
        Args:
            trade: Trade to execute
            
        Returns:
            True if trade was successfully executed, False otherwise
        """
        key = (trade.market_id, trade.outcome)
        
        # Calculate costs
        total_cost = trade.total_cost()
        
        if trade.order_type == OrderType.BUY:
            # Check if we have enough cash
            if total_cost > self.cash:
                return False
            
            # Deduct cash
            self.cash -= total_cost
            
            # Update or create position
            if key in self.positions:
                position = self.positions[key]
                # Update average price with new shares
                total_shares = position.shares + trade.shares
                position.avg_price = (
                    (position.shares * position.avg_price + trade.shares * trade.price) 
                    / total_shares
                )
                position.shares = total_shares
            else:
                self.positions[key] = Position(
                    market_id=trade.market_id,
                    outcome=trade.outcome,
                    shares=trade.shares,
                    avg_price=trade.price
                )
        
        elif trade.order_type == OrderType.SELL:
            # Check if we have the position
            if key not in self.positions:
                return False
            
            position = self.positions[key]
            
            # Check if we have enough shares
            if trade.shares > position.shares:
                return False
            
            # Add cash
            self.cash += total_cost
            
            # Update position
            pnl = trade.shares * (trade.price - position.avg_price) - trade.commission
            position.realized_pnl += pnl
            position.shares -= trade.shares
            
            # Remove position if fully closed
            if position.shares <= 0:
                del self.positions[key]
        
        # Record trade
        self.trades.append(trade)
        return True
    
    def resolve_market(self, market: Market) -> float:
        """
        Resolve a market and settle positions
        
        Args:
            market: Resolved market
            
        Returns:
            P&L from settlement
        """
        if not market.resolved or market.resolution is None:
            return 0.0
        
        pnl = 0.0
        
        # Settle all positions in this market
        for outcome in [True, False]:
            key = (market.id, outcome)
            if key in self.positions:
                position = self.positions[key]
                
                # If position outcome matches resolution, shares are worth 1.0 each
                # Otherwise, they're worth 0.0
                if outcome == market.resolution:
                    settlement_value = position.shares * 1.0
                else:
                    settlement_value = 0.0
                
                # Calculate P&L
                cost_basis = position.shares * position.avg_price
                pnl += settlement_value - cost_basis
                
                # Add settlement to cash
                self.cash += settlement_value
                
                # Remove position
                del self.positions[key]
        
        return pnl
    
    def get_total_value(self, markets: Dict[str, Market]) -> float:
        """
        Calculate total portfolio value (cash + positions marked to market)
        
        Args:
            markets: Dictionary of current market states
            
        Returns:
            Total portfolio value
        """
        value = self.cash
        
        for (market_id, outcome), position in self.positions.items():
            if market_id in markets:
                market = markets[market_id]
                current_price = market.current_yes_price if outcome else market.current_no_price
                value += position.shares * current_price
        
        return value
    
    def get_total_pnl(self, markets: Dict[str, Market]) -> float:
        """Calculate total profit/loss"""
        return self.get_total_value(markets) - self.initial_capital
    
    def get_returns(self, markets: Dict[str, Market]) -> float:
        """Calculate percentage returns"""
        return self.get_total_pnl(markets) / self.initial_capital
    
    def get_summary(self, markets: Dict[str, Market]) -> Dict:
        """
        Get portfolio summary
        
        Returns:
            Dictionary with portfolio statistics
        """
        total_value = self.get_total_value(markets)
        total_pnl = self.get_total_pnl(markets)
        
        return {
            "initial_capital": self.initial_capital,
            "cash": self.cash,
            "total_value": total_value,
            "total_pnl": total_pnl,
            "returns": total_pnl / self.initial_capital,
            "num_positions": len(self.positions),
            "num_trades": len(self.trades),
        }
