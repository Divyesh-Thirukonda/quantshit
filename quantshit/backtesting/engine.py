"""
Event-driven backtesting engine for prediction markets
"""

from typing import List, Dict, Callable, Optional
from datetime import datetime
import pandas as pd

from .models import Market, Order, Trade, OrderType, OrderStatus
from .portfolio import Portfolio
from ..strategies.base import Strategy


class Backtester:
    """
    Event-driven backtesting engine for prediction markets
    
    The backtester simulates trading on historical prediction market data,
    executing a given strategy and tracking performance.
    """
    
    def __init__(
        self, 
        initial_capital: float,
        commission_rate: float = 0.01,
        slippage: float = 0.0
    ):
        """
        Initialize backtester
        
        Args:
            initial_capital: Starting capital
            commission_rate: Trading commission rate (default 0.01 = 1%)
            slippage: Price slippage per trade (default 0.0)
        """
        self.initial_capital = initial_capital
        self.commission_rate = commission_rate
        self.slippage = slippage
        self.portfolio = Portfolio(initial_capital, commission_rate)
        self.markets: Dict[str, Market] = {}
        self.strategy: Optional[Strategy] = None
        self.performance_history: List[Dict] = []
    
    def set_strategy(self, strategy: Strategy):
        """
        Set the trading strategy
        
        Args:
            strategy: Strategy instance to use
        """
        self.strategy = strategy
    
    def update_market(self, market: Market):
        """
        Update market data
        
        Args:
            market: Updated market state
        """
        self.markets[market.id] = market
    
    def process_order(self, order: Order) -> Optional[Trade]:
        """
        Process an order and potentially execute a trade
        
        Args:
            order: Order to process
            
        Returns:
            Trade if executed, None otherwise
        """
        if order.market_id not in self.markets:
            order.status = OrderStatus.REJECTED
            return None
        
        market = self.markets[order.market_id]
        
        # Get current market price
        if order.outcome:
            market_price = market.current_yes_price
        else:
            market_price = market.current_no_price
        
        # Check if order can be filled
        can_fill = False
        execution_price = order.price
        
        if order.order_type == OrderType.BUY:
            # Buy order fills if limit price >= market price
            if order.price >= market_price:
                can_fill = True
                execution_price = market_price + self.slippage
        else:  # SELL
            # Sell order fills if limit price <= market price
            if order.price <= market_price:
                can_fill = True
                execution_price = market_price - self.slippage
        
        if not can_fill:
            order.status = OrderStatus.CANCELLED
            return None
        
        # Create trade
        commission = execution_price * order.shares * self.commission_rate
        trade = Trade(
            order_id=order.order_id,
            market_id=order.market_id,
            order_type=order.order_type,
            outcome=order.outcome,
            shares=order.shares,
            price=execution_price,
            timestamp=order.timestamp,
            commission=commission
        )
        
        # Execute trade
        if self.portfolio.execute_trade(trade):
            order.status = OrderStatus.FILLED
            return trade
        else:
            order.status = OrderStatus.REJECTED
            return None
    
    def run(
        self, 
        market_data: List[Market],
        strategy: Optional[Strategy] = None
    ) -> pd.DataFrame:
        """
        Run backtest on historical market data
        
        Args:
            market_data: List of market states in chronological order
            strategy: Strategy to use (overrides previously set strategy)
            
        Returns:
            DataFrame with performance history
        """
        if strategy is not None:
            self.set_strategy(strategy)
        
        if self.strategy is None:
            raise ValueError("No strategy set. Use set_strategy() or pass strategy to run()")
        
        # Reset state
        self.portfolio = Portfolio(self.initial_capital, self.commission_rate)
        self.markets = {}
        self.performance_history = []
        
        # Process each market update
        for market in market_data:
            # Update market state
            self.update_market(market)
            
            # Handle market resolution
            if market.resolved and market.resolution is not None:
                pnl = self.portfolio.resolve_market(market)
                self.strategy.on_market_resolved(market)
            
            # Generate signals from strategy
            orders = self.strategy.generate_signals(
                self.markets,
                self.portfolio,
                market.timestamp
            )
            
            # Process orders
            for order in orders:
                trade = self.process_order(order)
                if trade is not None:
                    self.strategy.on_trade_executed(trade)
            
            # Record performance snapshot
            snapshot = {
                "timestamp": market.timestamp,
                "total_value": self.portfolio.get_total_value(self.markets),
                "cash": self.portfolio.cash,
                "num_positions": len(self.portfolio.positions),
                "num_trades": len(self.portfolio.trades),
            }
            self.performance_history.append(snapshot)
        
        return pd.DataFrame(self.performance_history)
    
    def get_results(self) -> Dict:
        """
        Get backtest results and statistics
        
        Returns:
            Dictionary with performance metrics
        """
        summary = self.portfolio.get_summary(self.markets)
        
        if len(self.performance_history) > 0:
            df = pd.DataFrame(self.performance_history)
            
            # Calculate additional metrics
            returns_series = df["total_value"].pct_change()
            
            summary.update({
                "sharpe_ratio": self._calculate_sharpe_ratio(returns_series),
                "max_drawdown": self._calculate_max_drawdown(df["total_value"]),
                "win_rate": self._calculate_win_rate(),
            })
        
        return summary
    
    def _calculate_sharpe_ratio(self, returns: pd.Series, risk_free_rate: float = 0.0) -> float:
        """Calculate Sharpe ratio"""
        if len(returns) == 0 or returns.std() == 0:
            return 0.0
        excess_returns = returns.mean() - risk_free_rate
        return excess_returns / returns.std()
    
    def _calculate_max_drawdown(self, values: pd.Series) -> float:
        """Calculate maximum drawdown"""
        if len(values) == 0:
            return 0.0
        cummax = values.cummax()
        drawdown = (values - cummax) / cummax
        return drawdown.min()
    
    def _calculate_win_rate(self) -> float:
        """Calculate win rate from trades"""
        if len(self.portfolio.trades) == 0:
            return 0.0
        
        # Count profitable round-trip trades
        # This is simplified - in practice would need to match buy/sell pairs
        winning_trades = 0
        total_trades = 0
        
        for position in self.portfolio.positions.values():
            if position.realized_pnl > 0:
                winning_trades += 1
            if position.realized_pnl != 0:
                total_trades += 1
        
        return winning_trades / total_trades if total_trades > 0 else 0.0
