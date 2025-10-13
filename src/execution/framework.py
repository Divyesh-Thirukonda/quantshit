"""
Simplified execution framework for easy order management.

This module provides simple interfaces for executing trades without
dealing with complex order management details.
"""
from abc import ABC, abstractmethod
from typing import Dict, List, Any, Optional, Callable, Union
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
import asyncio
from functools import wraps

from src.execution.engine import Order, OrderStatus, OrderType
from src.strategies.base import TradingSignal, ArbitrageOpportunity
from src.data.providers import MarketData
from src.core.logger import get_logger

logger = get_logger(__name__)


class ExecutionMode(Enum):
    """Execution modes for different trading scenarios."""
    PAPER = "paper"         # Paper trading (simulation)
    LIVE = "live"          # Live trading with real money
    BACKTEST = "backtest"  # Backtesting mode


@dataclass
class TradeResult:
    """Result of a trade execution."""
    success: bool
    order_id: Optional[str] = None
    message: str = ""
    executed_price: Optional[float] = None
    executed_quantity: Optional[float] = None
    execution_time: Optional[datetime] = None
    fees: float = 0.0
    
    def __post_init__(self):
        if self.execution_time is None:
            self.execution_time = datetime.utcnow()


@dataclass
class Portfolio:
    """Simple portfolio representation."""
    cash: float
    positions: Dict[str, float] = field(default_factory=dict)  # market_id -> quantity
    total_value: float = 0.0
    unrealized_pnl: float = 0.0
    realized_pnl: float = 0.0
    
    def get_position(self, market_id: str) -> float:
        """Get position size for a market."""
        return self.positions.get(market_id, 0.0)
    
    def add_position(self, market_id: str, quantity: float):
        """Add to position."""
        if market_id in self.positions:
            self.positions[market_id] += quantity
        else:
            self.positions[market_id] = quantity
    
    def close_position(self, market_id: str):
        """Close position entirely."""
        if market_id in self.positions:
            del self.positions[market_id]


def execution_rule(
    max_position_size: float = 1000.0,
    max_daily_trades: int = 100,
    platforms: List[str] = None
):
    """
    Decorator to add execution rules to trading functions.
    
    Args:
        max_position_size: Maximum position size per market
        max_daily_trades: Maximum trades per day
        platforms: Allowed platforms
    
    Example:
        @execution_rule(max_position_size=500.0, max_daily_trades=50)
        async def execute_signal(signal: TradingSignal) -> TradeResult:
            # Your execution logic here
            pass
    """
    def decorator(func):
        func._execution_rules = {
            'max_position_size': max_position_size,
            'max_daily_trades': max_daily_trades,
            'platforms': platforms or ["all"]
        }
        
        @wraps(func)
        async def wrapper(*args, **kwargs):
            try:
                # Apply execution rules here if needed
                result = await func(*args, **kwargs)
                return result
            except Exception as e:
                logger.error(f"Error in execution function {func.__name__}: {e}")
                return TradeResult(success=False, message=str(e))
        
        return wrapper
    return decorator


def risk_check(
    max_loss_per_trade: float = 100.0,
    max_portfolio_risk: float = 0.1,  # 10% of portfolio
    check_correlation: bool = True
):
    """
    Decorator to add risk checks to execution functions.
    
    Example:
        @risk_check(max_loss_per_trade=50.0, max_portfolio_risk=0.05)
        async def safe_execute(signal: TradingSignal) -> TradeResult:
            # Execution logic with automatic risk checks
            pass
    """
    def decorator(func):
        func._risk_rules = {
            'max_loss_per_trade': max_loss_per_trade,
            'max_portfolio_risk': max_portfolio_risk,
            'check_correlation': check_correlation
        }
        
        @wraps(func)
        async def wrapper(*args, **kwargs):
            try:
                # Risk checks would be implemented here
                result = await func(*args, **kwargs)
                return result
            except Exception as e:
                logger.error(f"Risk check failed in {func.__name__}: {e}")
                return TradeResult(success=False, message=f"Risk check failed: {e}")
        
        return wrapper
    return decorator


class EasyExecutor(ABC):
    """
    Simplified base class for trade execution.
    
    This handles the complexity of order management and lets developers
    focus on execution logic.
    """
    
    def __init__(
        self,
        name: str,
        mode: ExecutionMode = ExecutionMode.PAPER,
        initial_capital: float = 10000.0,
        config: Optional[Dict[str, Any]] = None
    ):
        self.name = name
        self.mode = mode
        self.config = config or {}
        self.portfolio = Portfolio(cash=initial_capital)
        self.trade_history: List[TradeResult] = []
        self.daily_trades = 0
        self.last_trade_date = None
        self.is_active = False
    
    @abstractmethod
    async def execute_signal(self, signal: TradingSignal) -> TradeResult:
        """Execute a trading signal. Override this method."""
        pass
    
    async def execute_opportunity(self, opportunity: ArbitrageOpportunity) -> List[TradeResult]:
        """Execute an arbitrage opportunity. Override if needed."""
        # Default implementation: execute as individual signals
        results = []
        
        # This would need the actual opportunity structure
        # For now, return empty list
        return results
    
    async def close_position(self, market_id: str, reason: str = "manual") -> TradeResult:
        """Close a position."""
        current_position = self.portfolio.get_position(market_id)
        
        if current_position == 0:
            return TradeResult(
                success=False,
                message=f"No position to close for {market_id}"
            )
        
        # Create closing signal
        closing_signal = TradingSignal(
            strategy_name=f"{self.name}_close",
            market_id=market_id,
            platform="unknown",  # Would need to track this
            signal_type=SignalType.SELL if current_position > 0 else SignalType.BUY,
            outcome="yes",
            confidence=1.0,
            suggested_size=abs(current_position)
        )
        
        result = await self.execute_signal(closing_signal)
        
        if result.success:
            self.portfolio.close_position(market_id)
            logger.info(f"Closed position for {market_id}: {reason}")
        
        return result
    
    async def close_all_positions(self, reason: str = "shutdown") -> List[TradeResult]:
        """Close all open positions."""
        results = []
        
        for market_id in list(self.portfolio.positions.keys()):
            result = await self.close_position(market_id, reason)
            results.append(result)
        
        return results
    
    def get_portfolio_value(self, current_prices: Dict[str, float]) -> float:
        """Calculate current portfolio value."""
        total_value = self.portfolio.cash
        
        for market_id, quantity in self.portfolio.positions.items():
            if market_id in current_prices:
                total_value += quantity * current_prices[market_id]
        
        self.portfolio.total_value = total_value
        return total_value
    
    def get_trade_stats(self) -> Dict[str, Any]:
        """Get trading statistics."""
        if not self.trade_history:
            return {
                'total_trades': 0,
                'successful_trades': 0,
                'win_rate': 0.0,
                'total_fees': 0.0,
                'average_trade_size': 0.0
            }
        
        successful_trades = sum(1 for trade in self.trade_history if trade.success)
        total_fees = sum(trade.fees for trade in self.trade_history)
        total_quantity = sum(trade.executed_quantity or 0 for trade in self.trade_history if trade.executed_quantity)
        
        return {
            'total_trades': len(self.trade_history),
            'successful_trades': successful_trades,
            'win_rate': successful_trades / len(self.trade_history),
            'total_fees': total_fees,
            'average_trade_size': total_quantity / len(self.trade_history) if self.trade_history else 0
        }
    
    def _reset_daily_counter(self):
        """Reset daily trade counter if needed."""
        today = datetime.utcnow().date()
        if self.last_trade_date != today:
            self.daily_trades = 0
            self.last_trade_date = today
    
    def _can_trade(self, signal: TradingSignal) -> Tuple[bool, str]:
        """Check if trading is allowed."""
        if not self.is_active:
            return False, "Executor is not active"
        
        self._reset_daily_counter()
        
        max_daily = self.config.get('max_daily_trades', 100)
        if self.daily_trades >= max_daily:
            return False, f"Daily trade limit reached ({max_daily})"
        
        max_position = self.config.get('max_position_size', 1000.0)
        current_position = abs(self.portfolio.get_position(signal.market_id))
        if current_position + signal.suggested_size > max_position:
            return False, f"Position size limit exceeded (max: {max_position})"
        
        return True, ""


class SimpleExecutor(EasyExecutor):
    """
    Simple executor for basic trading.
    
    Example:
        executor = SimpleExecutor("my_executor", ExecutionMode.PAPER)
        result = await executor.execute_signal(my_signal)
    """
    
    async def execute_signal(self, signal: TradingSignal) -> TradeResult:
        """Execute a trading signal with paper trading."""
        
        # Check if we can trade
        can_trade, reason = self._can_trade(signal)
        if not can_trade:
            return TradeResult(success=False, message=reason)
        
        try:
            if self.mode == ExecutionMode.PAPER:
                # Paper trading simulation
                result = await self._paper_execute(signal)
            elif self.mode == ExecutionMode.LIVE:
                # Would integrate with real trading APIs
                result = TradeResult(success=False, message="Live trading not implemented")
            else:
                result = TradeResult(success=False, message=f"Unsupported mode: {self.mode}")
            
            # Track the trade
            self.trade_history.append(result)
            if result.success:
                self.daily_trades += 1
            
            return result
            
        except Exception as e:
            logger.error(f"Execution error: {e}")
            return TradeResult(success=False, message=str(e))
    
    async def _paper_execute(self, signal: TradingSignal) -> TradeResult:
        """Simulate trade execution for paper trading."""
        
        # Simulate execution delay
        await asyncio.sleep(0.1)
        
        # Use a simulated price (in real implementation, would get current market price)
        simulated_price = 0.5  # Would get from market data
        
        # Calculate trade cost
        trade_value = signal.suggested_size * simulated_price
        fee = trade_value * 0.001  # 0.1% fee
        
        # Check if we have enough cash
        if signal.signal_type.value == "buy" and self.portfolio.cash < trade_value + fee:
            return TradeResult(
                success=False,
                message=f"Insufficient cash. Need: ${trade_value + fee:.2f}, Have: ${self.portfolio.cash:.2f}"
            )
        
        # Execute the trade
        if signal.signal_type.value == "buy":
            self.portfolio.cash -= (trade_value + fee)
            self.portfolio.add_position(signal.market_id, signal.suggested_size)
        else:  # sell
            current_position = self.portfolio.get_position(signal.market_id)
            if current_position < signal.suggested_size:
                return TradeResult(
                    success=False,
                    message=f"Insufficient position. Trying to sell {signal.suggested_size}, have {current_position}"
                )
            
            self.portfolio.cash += (trade_value - fee)
            self.portfolio.add_position(signal.market_id, -signal.suggested_size)
        
        return TradeResult(
            success=True,
            order_id=f"paper_{int(datetime.utcnow().timestamp())}",
            message="Paper trade executed successfully",
            executed_price=simulated_price,
            executed_quantity=signal.suggested_size,
            fees=fee
        )


class BatchExecutor(EasyExecutor):
    """
    Executor that can handle multiple signals at once.
    
    Example:
        executor = BatchExecutor("batch_executor")
        results = await executor.execute_batch([signal1, signal2, signal3])
    """
    
    async def execute_signal(self, signal: TradingSignal) -> TradeResult:
        """Execute a single signal."""
        return await self.execute_batch([signal])[0]
    
    async def execute_batch(self, signals: List[TradingSignal]) -> List[TradeResult]:
        """Execute multiple signals."""
        results = []
        
        for signal in signals:
            # Check trading rules
            can_trade, reason = self._can_trade(signal)
            if not can_trade:
                results.append(TradeResult(success=False, message=reason))
                continue
            
            # Execute (paper trading for now)
            if self.mode == ExecutionMode.PAPER:
                result = await self._paper_execute(signal)
            else:
                result = TradeResult(success=False, message="Only paper trading supported")
            
            results.append(result)
            self.trade_history.append(result)
            
            if result.success:
                self.daily_trades += 1
        
        return results
    
    async def _paper_execute(self, signal: TradingSignal) -> TradeResult:
        """Paper trading execution (same as SimpleExecutor for now)."""
        await asyncio.sleep(0.01)  # Faster for batch
        
        simulated_price = 0.5
        trade_value = signal.suggested_size * simulated_price
        fee = trade_value * 0.001
        
        if signal.signal_type.value == "buy" and self.portfolio.cash < trade_value + fee:
            return TradeResult(success=False, message="Insufficient cash")
        
        if signal.signal_type.value == "buy":
            self.portfolio.cash -= (trade_value + fee)
            self.portfolio.add_position(signal.market_id, signal.suggested_size)
        else:
            current_position = self.portfolio.get_position(signal.market_id)
            if current_position < signal.suggested_size:
                return TradeResult(success=False, message="Insufficient position")
            
            self.portfolio.cash += (trade_value - fee)
            self.portfolio.add_position(signal.market_id, -signal.suggested_size)
        
        return TradeResult(
            success=True,
            order_id=f"batch_{int(datetime.utcnow().timestamp())}",
            executed_price=simulated_price,
            executed_quantity=signal.suggested_size,
            fees=fee
        )


class QuickTrader:
    """
    Ultra-simple interface for quick trading without setup complexity.
    
    Example:
        trader = QuickTrader(initial_cash=5000.0)
        
        # Buy a market
        result = await trader.buy("MARKET_001", quantity=100, max_price=0.6)
        
        # Sell a market
        result = await trader.sell("MARKET_001", quantity=50, min_price=0.7)
        
        # Check portfolio
        print(f"Cash: ${trader.cash:.2f}")
        print(f"Positions: {trader.positions}")
    """
    
    def __init__(
        self,
        initial_cash: float = 10000.0,
        mode: ExecutionMode = ExecutionMode.PAPER
    ):
        self.executor = SimpleExecutor("quick_trader", mode, initial_cash)
        self.executor.is_active = True
    
    @property
    def cash(self) -> float:
        return self.executor.portfolio.cash
    
    @property
    def positions(self) -> Dict[str, float]:
        return self.executor.portfolio.positions.copy()
    
    async def buy(
        self,
        market_id: str,
        quantity: float,
        max_price: Optional[float] = None,
        confidence: float = 0.7
    ) -> TradeResult:
        """Buy a market."""
        signal = TradingSignal(
            strategy_name="quick_trader",
            market_id=market_id,
            platform="unknown",
            signal_type=SignalType.BUY,
            outcome="yes",
            confidence=confidence,
            suggested_size=quantity,
            price_target=max_price
        )
        
        return await self.executor.execute_signal(signal)
    
    async def sell(
        self,
        market_id: str,
        quantity: float,
        min_price: Optional[float] = None,
        confidence: float = 0.7
    ) -> TradeResult:
        """Sell a market."""
        signal = TradingSignal(
            strategy_name="quick_trader",
            market_id=market_id,
            platform="unknown",
            signal_type=SignalType.SELL,
            outcome="yes",
            confidence=confidence,
            suggested_size=quantity,
            price_target=min_price
        )
        
        return await self.executor.execute_signal(signal)
    
    async def close_position(self, market_id: str) -> TradeResult:
        """Close entire position in a market."""
        return await self.executor.close_position(market_id)
    
    async def close_all(self) -> List[TradeResult]:
        """Close all positions."""
        return await self.executor.close_all_positions()
    
    def get_stats(self) -> Dict[str, Any]:
        """Get trading statistics."""
        stats = self.executor.get_trade_stats()
        stats['current_cash'] = self.cash
        stats['total_positions'] = len(self.positions)
        stats['portfolio_value'] = self.executor.portfolio.total_value
        return stats


# Example usage functions
async def example_simple_execution():
    """Example of simple execution."""
    
    # Create a quick trader
    trader = QuickTrader(initial_cash=1000.0)
    
    # Buy some markets
    result1 = await trader.buy("TEST_001", quantity=100, max_price=0.6)
    result2 = await trader.buy("TEST_002", quantity=50, max_price=0.4)
    
    print(f"Trade 1: {result1.success} - {result1.message}")
    print(f"Trade 2: {result2.success} - {result2.message}")
    
    # Check portfolio
    print(f"Cash remaining: ${trader.cash:.2f}")
    print(f"Positions: {trader.positions}")
    
    return trader


async def example_batch_execution():
    """Example of batch execution."""
    
    # Create batch executor
    executor = BatchExecutor("batch_test", ExecutionMode.PAPER, 5000.0)
    executor.is_active = True
    
    # Create multiple signals
    signals = []
    for i in range(5):
        signals.append(TradingSignal(
            strategy_name="batch_test",
            market_id=f"BATCH_{i:03d}",
            platform="test",
            signal_type=SignalType.BUY,
            outcome="yes",
            confidence=0.8,
            suggested_size=100.0
        ))
    
    # Execute all at once
    results = await executor.execute_batch(signals)
    
    successful = sum(1 for r in results if r.success)
    print(f"Executed {successful}/{len(results)} trades successfully")
    
    return executor