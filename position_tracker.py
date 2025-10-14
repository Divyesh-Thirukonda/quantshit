import json
import os
from datetime import datetime
from typing import Dict, List, Optional
from dataclasses import dataclass, asdict
import uuid


@dataclass
class Position:
    """Represents an open trading position"""
    id: str
    market_id: str
    market_title: str
    platform: str
    outcome: str  # "YES" or "NO"
    shares: float
    entry_price: float
    current_price: float
    entry_time: str
    strategy: str
    unrealized_pnl: float = 0.0
    
    def update_current_price(self, new_price: float):
        """Update current price and calculate unrealized PnL"""
        self.current_price = new_price
        if self.outcome == "YES":
            self.unrealized_pnl = (new_price - self.entry_price) * self.shares
        else:
            self.unrealized_pnl = (self.entry_price - new_price) * self.shares


@dataclass 
class Trade:
    """Represents a completed trade (bet)"""
    id: str
    market_id: str
    market_title: str
    platform: str
    action: str  # "BUY" or "SELL"
    outcome: str  # "YES" or "NO"
    shares: float
    price: float
    timestamp: str
    strategy: str
    order_id: str = ""
    realized_pnl: float = 0.0
    fees: float = 0.0


class PositionTracker:
    """Tracks open positions and trade history"""
    
    def __init__(self, data_file: str = "positions_data.json"):
        self.data_file = data_file
        self.positions: Dict[str, Position] = {}
        self.trade_history: List[Trade] = []
        self.load_data()
    
    def load_data(self):
        """Load positions and trade history from file"""
        if os.path.exists(self.data_file):
            try:
                with open(self.data_file, 'r') as f:
                    data = json.load(f)
                
                # Load positions
                positions_data = data.get('positions', {})
                self.positions = {
                    pos_id: Position(**pos_data) 
                    for pos_id, pos_data in positions_data.items()
                }
                
                # Load trade history
                trades_data = data.get('trade_history', [])
                self.trade_history = [Trade(**trade_data) for trade_data in trades_data]
                
                print(f"📁 Loaded {len(self.positions)} positions and {len(self.trade_history)} trades")
                
            except Exception as e:
                print(f"⚠️  Error loading position data: {e}")
                self.positions = {}
                self.trade_history = []
    
    def save_data(self):
        """Save positions and trade history to file"""
        try:
            data = {
                'positions': {pos_id: asdict(pos) for pos_id, pos in self.positions.items()},
                'trade_history': [asdict(trade) for trade in self.trade_history],
                'last_updated': datetime.now().isoformat()
            }
            
            with open(self.data_file, 'w') as f:
                json.dump(data, f, indent=2)
                
        except Exception as e:
            print(f"❌ Error saving position data: {e}")
    
    def add_trade(self, market_id: str, market_title: str, platform: str, 
                  action: str, outcome: str, shares: float, price: float, 
                  strategy: str, order_id: str = "") -> str:
        """Add a new trade and update positions"""
        
        trade_id = str(uuid.uuid4())[:8]
        trade = Trade(
            id=trade_id,
            market_id=market_id,
            market_title=market_title,
            platform=platform,
            action=action,
            outcome=outcome,
            shares=shares,
            price=price,
            timestamp=datetime.now().isoformat(),
            strategy=strategy,
            order_id=order_id
        )
        
        self.trade_history.append(trade)
        
        # Update positions
        position_key = f"{platform}_{market_id}_{outcome}"
        
        if action == "BUY":
            if position_key in self.positions:
                # Add to existing position (average price)
                pos = self.positions[position_key]
                total_value = (pos.shares * pos.entry_price) + (shares * price)
                pos.shares += shares
                pos.entry_price = total_value / pos.shares
            else:
                # Create new position
                self.positions[position_key] = Position(
                    id=position_key,
                    market_id=market_id,
                    market_title=market_title,
                    platform=platform,
                    outcome=outcome,
                    shares=shares,
                    entry_price=price,
                    current_price=price,
                    entry_time=datetime.now().isoformat(),
                    strategy=strategy
                )
        
        elif action == "SELL":
            if position_key in self.positions:
                pos = self.positions[position_key]
                if pos.shares >= shares:
                    # Calculate realized PnL
                    if outcome == "YES":
                        trade.realized_pnl = (price - pos.entry_price) * shares
                    else:
                        trade.realized_pnl = (pos.entry_price - price) * shares
                    
                    # Reduce position
                    pos.shares -= shares
                    if pos.shares <= 0:
                        del self.positions[position_key]
                else:
                    print(f"⚠️  Warning: Trying to sell {shares} shares but only have {pos.shares}")
        
        self.save_data()
        return trade_id
    
    def update_market_prices(self, market_prices: Dict[str, Dict[str, float]]):
        """Update current prices for all positions
        
        Args:
            market_prices: Dict of {market_id: {"yes_price": float, "no_price": float}}
        """
        for pos in self.positions.values():
            if pos.market_id in market_prices:
                prices = market_prices[pos.market_id]
                if pos.outcome == "YES" and "yes_price" in prices:
                    pos.update_current_price(prices["yes_price"])
                elif pos.outcome == "NO" and "no_price" in prices:
                    pos.update_current_price(prices["no_price"])
        
        self.save_data()
    
    def get_open_positions(self) -> List[Dict]:
        """Get all open positions"""
        return [asdict(pos) for pos in self.positions.values()]
    
    def get_trade_history(self, limit: Optional[int] = None) -> List[Dict]:
        """Get trade history, optionally limited to recent trades"""
        trades = sorted(self.trade_history, key=lambda t: t.timestamp, reverse=True)
        if limit:
            trades = trades[:limit]
        return [asdict(trade) for trade in trades]
    
    def get_portfolio_summary(self) -> Dict:
        """Get portfolio summary statistics"""
        total_unrealized_pnl = sum(pos.unrealized_pnl for pos in self.positions.values())
        total_realized_pnl = sum(trade.realized_pnl for trade in self.trade_history)
        
        total_positions = len(self.positions)
        total_trades = len(self.trade_history)
        
        # Strategy breakdown
        strategy_stats = {}
        for trade in self.trade_history:
            if trade.strategy not in strategy_stats:
                strategy_stats[trade.strategy] = {
                    'trades': 0,
                    'total_pnl': 0.0
                }
            strategy_stats[trade.strategy]['trades'] += 1
            strategy_stats[trade.strategy]['total_pnl'] += trade.realized_pnl
        
        # Platform breakdown  
        platform_stats = {}
        for pos in self.positions.values():
            if pos.platform not in platform_stats:
                platform_stats[pos.platform] = {
                    'positions': 0,
                    'total_unrealized_pnl': 0.0
                }
            platform_stats[pos.platform]['positions'] += 1
            platform_stats[pos.platform]['total_unrealized_pnl'] += pos.unrealized_pnl
        
        return {
            'total_positions': total_positions,
            'total_trades': total_trades,
            'total_unrealized_pnl': total_unrealized_pnl,
            'total_realized_pnl': total_realized_pnl,
            'total_pnl': total_unrealized_pnl + total_realized_pnl,
            'strategy_breakdown': strategy_stats,
            'platform_breakdown': platform_stats,
            'last_updated': datetime.now().isoformat()
        }