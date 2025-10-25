"""
Trading logging and reporting functionality separated from bot logic
Responsible for all output formatting, progress tracking, and result reporting
"""

from typing import List, Dict, Any
from datetime import datetime
from ..types import ArbitrageOpportunity


class TradingLogger:
    """
    Responsible solely for logging, reporting, and output formatting
    Single Responsibility: Logging and user feedback
    """
    
    def __init__(self, min_volume: float, min_spread: float, platforms: List[str]):
        """
        Initialize logger with trading configuration for context
        
        Args:
            min_volume: Minimum volume for context in logs
            min_spread: Minimum spread for context in logs  
            platforms: List of platform names for context
        """
        self.min_volume = min_volume
        self.min_spread = min_spread
        self.platforms = platforms
    
    def log_startup(self):
        """Log startup information and configuration"""
        print("🧪 Quantshit Arbitrage Engine - Paper Trading Mode")
        print("   📄 This is a simulation-only system with virtual money")
        print(f"   Platforms: {self.platforms} (simulated)")
        print(f"   Min volume: ${self.min_volume}")
        print(f"   Min spread: {self.min_spread}")
        print(f"   💰 Starting with $10,000 virtual money per platform")
    
    def log_cycle_start(self):
        """Log the start of a new trading cycle"""
        print(f"\n🔄 Starting arbitrage cycle at {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print("=" * 60)
    
    def log_cycle_end(self):
        """Log the end of a trading cycle"""
        print("=" * 60)
        print(f"Cycle completed. Next run in 1 hour.\n")
    
    def log_strategy_execution(self, strategy_name: str, opportunities: List[ArbitrageOpportunity]):
        """Log strategy execution results"""
        print(f"\n🎯 Running {strategy_name} strategy...")
        if opportunities:
            print(f"   Found {len(opportunities)} opportunities")
        else:
            print(f"   💤 No arbitrage opportunities found this cycle")
    
    def log_execution_results(self, executed_trades: List[Dict[str, Any]]):
        """
        Log trade execution results
        
        Args:
            executed_trades: List of trade execution results
        """
        if not executed_trades:
            return
            
        successful_trades = sum(1 for trade in executed_trades if trade['success'])
        total_profit = sum(
            trade['opportunity']['expected_profit'] 
            for trade in executed_trades 
            if trade['success']
        )
        
        print(f"\n📈 Cycle Results:")
        print(f"   Opportunities found: {len(executed_trades)}")
        print(f"   Trades executed: {successful_trades}/{len(executed_trades)}")
        print(f"   Expected profit: ${total_profit:.4f}")
    
    def log_error(self, operation: str, error: Exception):
        """
        Log errors with context
        
        Args:
            operation: Description of what operation failed
            error: The exception that occurred
        """
        print(f"\n❌ {operation} failed: {error}")
    
    def log_platform_status(self, platform: str, success: bool, message: str = ""):
        """
        Log platform initialization or operation status
        
        Args:
            platform: Platform name
            success: Whether operation succeeded
            message: Additional context message
        """
        status = "✓" if success else "✗"
        print(f"{status} {platform}: {message}")
    
    def log_portfolio_value(self, total_value: float):
        """Log current portfolio value"""
        print(f"💼 Total Portfolio Value: ${total_value:,.2f}")
    
    def log_position_swap(self, old_position_id: str, old_remaining_pct: float, new_potential_pct: float):
        """Log position swap operations"""
        print(f"\n🔄 Executing position swap:")
        print(f"   Closing: {old_position_id} ({old_remaining_pct:.1f}% remaining)")
        print(f"   Opening: New opportunity with {new_potential_pct:.1f}% potential gain")