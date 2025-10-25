"""
Position Management System for Quantshit Arbitrage Engine
Handles position limits, intelligent swapping, and portfolio optimization
"""

from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass
from datetime import datetime, timedelta
import time

from ..types import (
    Position, TradePlan, ArbitrageOpportunity, Platform, Outcome,
    PositionManagerConfig, ExecutionResult, LegType
)


class PositionManager:
    """
    Manages portfolio positions with intelligent swapping and risk controls
    """
    
    def __init__(self, config: PositionManagerConfig):
        self.config = config
        self.active_positions: Dict[str, Position] = {}
        self.position_history: List[Position] = []
        self.last_rebalance: datetime = datetime.now()
    
    def get_active_positions(self) -> List[Position]:
        """Get all currently active positions"""
        return list(self.active_positions.values())
    
    def get_position_count(self) -> int:
        """Get number of active positions"""
        return len(self.active_positions)
    
    def has_capacity(self) -> bool:
        """Check if we can open new positions"""
        return self.get_position_count() < self.config.max_open_positions
    
    def add_position(self, position: Position):
        """Add a new position to active tracking"""
        if not position.position_id:
            position.position_id = f"pos_{position.platform.value}_{position.market_id}_{int(time.time())}"
        
        # Set default max potential price for prediction markets
        if position.max_potential_price is None:
            position.max_potential_price = 1.0
        
        self.active_positions[position.position_id] = position
        print(f"   📍 Added position {position.position_id}: {position.quantity} {position.outcome.value} @ ${position.average_price:.4f}")
    
    def remove_position(self, position_id: str) -> Optional[Position]:
        """Remove and return a position"""
        position = self.active_positions.pop(position_id, None)
        if position:
            self.position_history.append(position)
            print(f"   📤 Removed position {position_id}: P&L ${position.unrealized_pnl:.2f} ({position.unrealized_pnl_pct:.1f}%)")
        return position
    
    def update_position_prices(self, market_prices: Dict[str, Dict[str, float]]):
        """
        Update current prices for all positions
        market_prices format: {platform: {market_id: {outcome: price}}}
        """
        for position in self.active_positions.values():
            platform_key = position.platform.value
            if platform_key in market_prices and position.market_id in market_prices[platform_key]:
                market_data = market_prices[platform_key][position.market_id]
                outcome_key = position.outcome.value.lower()
                if outcome_key in market_data:
                    position.current_price = market_data[outcome_key]
    
    def get_worst_performing_position(self) -> Optional[Position]:
        """Get position with lowest potential remaining gain percentage"""
        if not self.active_positions:
            return None
        
        return min(
            self.active_positions.values(),
            key=lambda p: p.potential_remaining_gain_pct
        )
    
    def get_underperforming_positions(self) -> List[Position]:
        """Get positions with remaining gain below threshold"""
        return [
            pos for pos in self.active_positions.values()
            if pos.potential_remaining_gain_pct < self.config.min_remaining_gain_pct
        ]
    
    def should_swap_position(self, new_opportunity: ArbitrageOpportunity) -> Tuple[bool, Optional[Position]]:
        """
        Determine if we should swap a position for a new opportunity
        Returns (should_swap, position_to_swap)
        """
        if self.has_capacity():
            return False, None  # No need to swap if we have capacity
        
        worst_position = self.get_worst_performing_position()
        if not worst_position:
            return False, None
        
        # Calculate potential gain of new opportunity
        new_opportunity_gain_pct = (new_opportunity.expected_profit_per_share / new_opportunity.buy_price) * 100
        
        # Check if new opportunity is significantly better
        gain_difference = new_opportunity_gain_pct - worst_position.potential_remaining_gain_pct
        
        should_swap = gain_difference >= self.config.min_swap_threshold_pct
        
        if should_swap:
            print(f"   🔄 Swap candidate found:")
            print(f"      New opportunity: {new_opportunity_gain_pct:.1f}% potential gain")
            print(f"      Current worst: {worst_position.potential_remaining_gain_pct:.1f}% remaining gain")
            print(f"      Difference: +{gain_difference:.1f}%")
        
        return should_swap, worst_position if should_swap else None
    
    def calculate_position_size(self, opportunity: ArbitrageOpportunity, portfolio_value: float) -> int:
        """Calculate appropriate position size based on portfolio percentage"""
        target_value = portfolio_value * self.config.position_size_pct
        position_size = int(target_value / opportunity.buy_price)
        
        # Don't exceed the opportunity's max quantity
        position_size = min(position_size, opportunity.max_quantity)
        
        # Ensure minimum position size
        position_size = max(position_size, 1)
        
        return position_size
    
    def check_forced_exits(self) -> List[Position]:
        """Check for positions that should be force-closed due to losses or time"""
        positions_to_close = []
        current_time = datetime.now()
        
        for position in self.active_positions.values():
            # Force close on excessive losses
            if position.unrealized_pnl_pct < self.config.force_close_threshold_pct:
                print(f"   ⚠️  Force closing {position.position_id} due to {position.unrealized_pnl_pct:.1f}% loss")
                positions_to_close.append(position)
                continue
            
            # Force close on max hold time
            hold_time = current_time - position.timestamp
            max_hold_time = timedelta(hours=self.config.max_hold_time_hours)
            if hold_time > max_hold_time:
                print(f"   ⏰ Force closing {position.position_id} due to max hold time ({hold_time})")
                positions_to_close.append(position)
                continue
        
        return positions_to_close
    
    def should_rebalance(self) -> bool:
        """Check if it's time to rebalance positions"""
        time_since_rebalance = datetime.now() - self.last_rebalance
        rebalance_interval = timedelta(minutes=self.config.rebalance_frequency_minutes)
        return time_since_rebalance >= rebalance_interval
    
    def create_position_from_plan(self, plan: TradePlan, execution_result: ExecutionResult) -> List[Position]:
        """Create Position objects from executed TradePlan"""
        positions = []
        
        for leg in execution_result.executed_legs:
            if leg.order and leg.order.is_filled:
                # Create position from executed leg
                position = Position(
                    market_id=leg.market.id,
                    platform=leg.market.platform,
                    outcome=leg.outcome,
                    quantity=leg.order.filled_quantity,
                    average_price=leg.order.average_fill_price,
                    current_price=leg.order.average_fill_price,  # Start with fill price
                    total_cost=leg.order.total_cost,
                    timestamp=leg.order.timestamp,
                    origin_plan_id=plan.plan_id,
                    max_potential_price=1.0  # Prediction markets max at 1.0
                )
                
                # Set target exit price based on leg type and plan strategy
                if leg.leg_type == LegType.BUY_LEG:
                    # For buy legs, we expect to sell higher
                    position.target_exit_price = leg.target_price * 1.1  # 10% target gain
                elif leg.leg_type == LegType.SELL_LEG:
                    # For sell legs, we expect price to fall
                    position.target_exit_price = leg.target_price * 0.9  # Expect 10% price drop
                
                positions.append(position)
                self.add_position(position)
        
        return positions
    
    def get_portfolio_summary(self) -> Dict:
        """Get comprehensive portfolio summary with position analytics"""
        total_value = sum(pos.market_value for pos in self.active_positions.values())
        total_cost = sum(pos.total_cost for pos in self.active_positions.values())
        total_unrealized_pnl = sum(pos.unrealized_pnl for pos in self.active_positions.values())
        total_potential_remaining = sum(pos.potential_remaining_gain for pos in self.active_positions.values())
        
        avg_remaining_gain_pct = 0.0
        if self.active_positions:
            avg_remaining_gain_pct = sum(pos.potential_remaining_gain_pct for pos in self.active_positions.values()) / len(self.active_positions)
        
        # Get best and worst positions
        best_position = max(self.active_positions.values(), key=lambda p: p.potential_remaining_gain_pct) if self.active_positions else None
        worst_position = min(self.active_positions.values(), key=lambda p: p.potential_remaining_gain_pct) if self.active_positions else None
        
        return {
            'total_positions': len(self.active_positions),
            'capacity_used': f"{len(self.active_positions)}/{self.config.max_open_positions}",
            'total_market_value': total_value,
            'total_cost': total_cost,
            'total_unrealized_pnl': total_unrealized_pnl,
            'total_unrealized_pnl_pct': (total_unrealized_pnl / total_cost * 100) if total_cost > 0 else 0.0,
            'total_potential_remaining': total_potential_remaining,
            'avg_remaining_gain_pct': avg_remaining_gain_pct,
            'best_position_id': best_position.position_id if best_position else None,
            'best_remaining_gain_pct': best_position.potential_remaining_gain_pct if best_position else 0.0,
            'worst_position_id': worst_position.position_id if worst_position else None,
            'worst_remaining_gain_pct': worst_position.potential_remaining_gain_pct if worst_position else 0.0,
            'underperforming_count': len(self.get_underperforming_positions()),
            'forced_exits_needed': len(self.check_forced_exits())
        }
    
    def print_portfolio_status(self):
        """Print detailed portfolio status"""
        summary = self.get_portfolio_summary()
        
        print(f"\n📊 Position Manager Status:")
        print(f"   Active Positions: {summary['capacity_used']}")
        print(f"   Total Value: ${summary['total_market_value']:.2f}")
        print(f"   Unrealized P&L: ${summary['total_unrealized_pnl']:.2f} ({summary['total_unrealized_pnl_pct']:.1f}%)")
        print(f"   Potential Remaining: ${summary['total_potential_remaining']:.2f}")
        print(f"   Avg Remaining Gain: {summary['avg_remaining_gain_pct']:.1f}%")
        
        if summary['best_position_id']:
            print(f"   Best Position: {summary['best_position_id']} ({summary['best_remaining_gain_pct']:.1f}% remaining)")
        if summary['worst_position_id']:
            print(f"   Worst Position: {summary['worst_position_id']} ({summary['worst_remaining_gain_pct']:.1f}% remaining)")
        
        if summary['underperforming_count'] > 0:
            print(f"   ⚠️  {summary['underperforming_count']} underperforming positions")
        if summary['forced_exits_needed'] > 0:
            print(f"   🚨 {summary['forced_exits_needed']} positions need forced exit")