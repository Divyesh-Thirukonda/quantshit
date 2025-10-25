"""
Capital management and risk control for arbitrage trading
"""

import time
from typing import Dict, List
from decimal import Decimal


class CapitalManager:
    """Manages capital allocation and risk for arbitrage trading"""
    
    def __init__(self, max_position_size: float = 1000, max_total_exposure: float = 5000):
        self.max_position_size = max_position_size
        self.max_total_exposure = max_total_exposure
        self.current_exposure = 0.0
        self.platform_balances = {}
        self.active_positions = {}
    
    def update_platform_balance(self, platform: str, balance: float):
        """Update balance for a platform"""
        self.platform_balances[platform] = balance
    
    def check_arbitrage_feasibility(self, opportunity: Dict) -> Dict:
        """Check if we can actually execute an arbitrage opportunity"""
        buy_platform = opportunity['buy_market']['platform']
        sell_platform = opportunity['sell_market']['platform']
        trade_amount = opportunity['trade_amount']
        buy_price = opportunity['buy_price']
        sell_price = opportunity['sell_price']
        
        # Calculate required capital
        buy_cost = trade_amount * buy_price
        
        # Check if this is a pure arbitrage (sell existing shares) or requires short selling
        sell_type = self._determine_sell_type(sell_platform, opportunity)
        
        checks = {
            'feasible': True,
            'reasons': [],
            'buy_cost': buy_cost,
            'sell_type': sell_type
        }
        
        # Check buy platform balance
        buy_balance = self.platform_balances.get(buy_platform, 0)
        if buy_balance < buy_cost:
            checks['feasible'] = False
            checks['reasons'].append(
                f"Insufficient funds on {buy_platform}: need ${buy_cost:.2f}, have ${buy_balance:.2f}"
            )
        
        # Check sell capability
        if sell_type == 'short_sell':
            # For short selling, we need margin/collateral
            margin_required = trade_amount * (1 - sell_price)  # Cost to buy back if wrong
            sell_balance = self.platform_balances.get(sell_platform, 0)
            if sell_balance < margin_required:
                checks['feasible'] = False
                checks['reasons'].append(
                    f"Insufficient margin on {sell_platform}: need ${margin_required:.2f}, have ${sell_balance:.2f}"
                )
        elif sell_type == 'sell_existing':
            # Check if we own enough shares
            position_key = f"{sell_platform}_{opportunity['sell_market']['id']}_{opportunity['outcome']}"
            owned_shares = self.active_positions.get(position_key, 0)
            if owned_shares < trade_amount:
                checks['feasible'] = False
                checks['reasons'].append(
                    f"Insufficient shares on {sell_platform}: need {trade_amount}, own {owned_shares}"
                )
        
        # Check position size limits
        if trade_amount > self.max_position_size:
            checks['feasible'] = False
            checks['reasons'].append(
                f"Trade size too large: ${trade_amount:.2f} > max ${self.max_position_size:.2f}"
            )
        
        # Check total exposure
        if self.current_exposure + buy_cost > self.max_total_exposure:
            checks['feasible'] = False
            checks['reasons'].append(
                f"Would exceed max exposure: current ${self.current_exposure:.2f} + ${buy_cost:.2f} > max ${self.max_total_exposure:.2f}"
            )
        
        return checks
    
    def _determine_sell_type(self, platform: str, opportunity: Dict) -> str:
        """Determine if we're selling existing shares or short selling"""
        market_id = opportunity['sell_market']['id']
        outcome = opportunity['outcome']
        position_key = f"{platform}_{market_id}_{outcome}"
        
        owned_shares = self.active_positions.get(position_key, 0)
        trade_amount = opportunity['trade_amount']
        
        if owned_shares >= trade_amount:
            return 'sell_existing'
        else:
            return 'short_sell'
    
    def reserve_capital(self, opportunity: Dict) -> bool:
        """Reserve capital for a trade"""
        feasibility = self.check_arbitrage_feasibility(opportunity)
        if not feasibility['feasible']:
            return False
        
        buy_cost = feasibility['buy_cost']
        buy_platform = opportunity['buy_market']['platform']
        
        # Reserve the capital
        self.platform_balances[buy_platform] -= buy_cost
        self.current_exposure += buy_cost
        
        return True
    
    def release_capital(self, opportunity: Dict, trade_result: Dict):
        """Release capital after trade completion"""
        buy_cost = opportunity['trade_amount'] * opportunity['buy_price']
        buy_platform = opportunity['buy_market']['platform']
        
        if trade_result['success']:
            # Trade succeeded - update balances with P&L
            profit = opportunity['expected_profit']
            self.platform_balances[buy_platform] += profit
        else:
            # Trade failed - return reserved capital
            self.platform_balances[buy_platform] += buy_cost
        
        self.current_exposure -= buy_cost
    
    def get_platform_summary(self) -> Dict:
        """Get summary of all platform balances and positions"""
        return {
            'balances': self.platform_balances.copy(),
            'total_balance': sum(self.platform_balances.values()),
            'current_exposure': self.current_exposure,
            'available_capital': sum(self.platform_balances.values()) - self.current_exposure,
            'active_positions': len(self.active_positions),
            'max_position_size': self.max_position_size,
            'max_total_exposure': self.max_total_exposure
        }


class RiskManager:
    """Additional risk management for arbitrage trading"""
    
    def __init__(self, max_daily_trades: int = 10, max_loss_per_day: float = 500):
        self.max_daily_trades = max_daily_trades
        self.max_loss_per_day = max_loss_per_day
        self.daily_trades = 0
        self.daily_pnl = 0.0
        self.failed_trades = []
    
    def can_trade(self) -> Dict:
        """Check if we can continue trading today"""
        checks = {
            'can_trade': True,
            'reasons': []
        }
        
        if self.daily_trades >= self.max_daily_trades:
            checks['can_trade'] = False
            checks['reasons'].append(f"Daily trade limit reached: {self.daily_trades}/{self.max_daily_trades}")
        
        if self.daily_pnl <= -self.max_loss_per_day:
            checks['can_trade'] = False
            checks['reasons'].append(f"Daily loss limit reached: ${self.daily_pnl:.2f}")
        
        # Stop trading if too many recent failures
        recent_failures = sum(1 for failure_time in self.failed_trades if time.time() - failure_time < 3600)  # Last hour
        if recent_failures >= 3:
            checks['can_trade'] = False
            checks['reasons'].append(f"Too many recent failures: {recent_failures} in last hour")
        
        return checks
    
    def record_trade(self, profit: float, success: bool):
        """Record a completed trade"""
        self.daily_trades += 1
        self.daily_pnl += profit
        
        if not success:
            self.failed_trades.append(time.time())
    
    def reset_daily_limits(self):
        """Reset daily counters (call at start of each day)"""
        self.daily_trades = 0
        self.daily_pnl = 0.0
        self.failed_trades = []