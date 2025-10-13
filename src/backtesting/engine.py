"""
Backtesting engine for testing strategies on historical data.
"""
import pandas as pd
import numpy as np
from typing import Dict, List, Optional, Any, Tuple
from datetime import datetime, timedelta
from dataclasses import dataclass, field
from src.strategies.base import BaseStrategy, TradingSignal, ArbitrageOpportunity
from src.data.providers import MarketData, MarketStatus
from src.risk.manager import RiskManager
from src.core.logger import get_logger

logger = get_logger(__name__)


@dataclass
class BacktestResult:
    """Backtest result summary."""
    strategy_name: str
    start_date: datetime
    end_date: datetime
    initial_capital: float
    final_capital: float
    total_return: float
    annual_return: float
    max_drawdown: float
    sharpe_ratio: float
    win_rate: float
    total_trades: int
    winning_trades: int
    losing_trades: int
    avg_win: float
    avg_loss: float
    profit_factor: float
    daily_returns: List[float]
    equity_curve: List[Tuple[datetime, float]]
    trade_log: List[Dict[str, Any]]
    risk_metrics: Dict[str, Any]


@dataclass
class BacktestTrade:
    """Individual backtest trade."""
    trade_id: str
    timestamp: datetime
    platform: str
    market_id: str
    side: str
    outcome: str
    quantity: float
    entry_price: float
    exit_price: Optional[float] = None
    exit_timestamp: Optional[datetime] = None
    pnl: Optional[float] = None
    status: str = "open"  # open, closed
    strategy: str = ""
    metadata: Dict[str, Any] = field(default_factory=dict)


class BacktestEngine:
    """Backtesting engine for strategy evaluation."""
    
    def __init__(self, initial_capital: float = 100000.0):
        self.initial_capital = initial_capital
        self.current_capital = initial_capital
        self.positions: Dict[str, BacktestTrade] = {}
        self.closed_trades: List[BacktestTrade] = []
        self.equity_curve: List[Tuple[datetime, float]] = []
        self.daily_returns: List[float] = []
        self.risk_manager = RiskManager()
        self.trade_counter = 0
        self.commission_rate = 0.001  # 0.1% commission
        self.slippage = 0.005  # 0.5% slippage
    
    async def run_backtest(
        self,
        strategy: BaseStrategy,
        historical_data: Dict[str, pd.DataFrame],
        start_date: datetime,
        end_date: datetime,
        rebalance_frequency: str = "1H"  # hourly
    ) -> BacktestResult:
        """
        Run backtest for a strategy.
        
        Args:
            strategy: Strategy to test
            historical_data: Historical market data {platform: DataFrame}
            start_date: Backtest start date
            end_date: Backtest end date
            rebalance_frequency: How often to run strategy
            
        Returns:
            Backtest results
        """
        logger.info(f"Starting backtest for {strategy.name} from {start_date} to {end_date}")
        
        # Reset state
        self._reset_backtest()
        
        # Generate time periods
        time_periods = pd.date_range(start=start_date, end=end_date, freq=rebalance_frequency)
        
        for current_time in time_periods:
            try:
                # Get market data for this time period
                current_markets = self._get_markets_at_time(historical_data, current_time)
                
                if not current_markets:
                    continue
                
                # Run strategy
                signals, opportunities = await strategy.run_all_strategies(current_markets)
                
                # Execute signals
                await self._execute_backtest_signals(signals, current_time, current_markets)
                
                # Execute opportunities
                await self._execute_backtest_opportunities(opportunities, current_time, current_markets)
                
                # Update positions and calculate PnL
                self._update_positions_pnl(current_markets, current_time)
                
                # Record equity curve
                self.equity_curve.append((current_time, self.current_capital))
                
                # Calculate daily returns
                if len(self.equity_curve) > 1:
                    prev_capital = self.equity_curve[-2][1]
                    daily_return = (self.current_capital - prev_capital) / prev_capital
                    self.daily_returns.append(daily_return)
            
            except Exception as e:
                logger.error(f"Error in backtest at {current_time}: {e}")
                continue
        
        # Generate results
        return self._generate_backtest_results(strategy.name, start_date, end_date)
    
    def _reset_backtest(self) -> None:
        """Reset backtest state."""
        self.current_capital = self.initial_capital
        self.positions.clear()
        self.closed_trades.clear()
        self.equity_curve.clear()
        self.daily_returns.clear()
        self.trade_counter = 0
    
    def _get_markets_at_time(
        self,
        historical_data: Dict[str, pd.DataFrame],
        timestamp: datetime
    ) -> Dict[str, List[MarketData]]:
        """Get market data at a specific timestamp."""
        markets = {}
        
        for platform, df in historical_data.items():
            platform_markets = []
            
            # Get data closest to timestamp
            try:
                # Assume timestamp column exists
                closest_time = df['timestamp'].iloc[(df['timestamp'] - timestamp).abs().argsort()[:1]]
                
                if len(closest_time) > 0:
                    time_data = df[df['timestamp'] == closest_time.iloc[0]]
                    
                    for _, row in time_data.iterrows():
                        market = MarketData(
                            platform=platform,
                            market_id=row.get('market_id', ''),
                            title=row.get('title', ''),
                            category=row.get('category', ''),
                            yes_price=row.get('yes_price'),
                            no_price=row.get('no_price'),
                            volume=row.get('volume', 0.0),
                            close_date=row.get('close_date'),
                            status=MarketStatus.ACTIVE,
                            last_updated=timestamp
                        )
                        platform_markets.append(market)
            
            except Exception as e:
                logger.warning(f"Error getting market data for {platform} at {timestamp}: {e}")
                continue
            
            markets[platform] = platform_markets
        
        return markets
    
    async def _execute_backtest_signals(
        self,
        signals: List[TradingSignal],
        timestamp: datetime,
        current_markets: Dict[str, List[MarketData]]
    ) -> None:
        """Execute trading signals in backtest."""
        for signal in signals:
            try:
                # Check risk limits
                risk_check, risk_message = self.risk_manager.check_signal_risk(signal)
                if not risk_check:
                    logger.debug(f"Signal rejected by risk manager: {risk_message}")
                    continue
                
                # Find market data for this signal
                market_data = self._find_market_data(signal.platform, signal.market_id, current_markets)
                if not market_data:
                    continue
                
                # Calculate execution price with slippage
                execution_price = self._calculate_execution_price(signal, market_data)
                
                # Check if we have enough capital
                trade_cost = signal.suggested_size * execution_price
                commission = trade_cost * self.commission_rate
                
                if trade_cost + commission > self.current_capital:
                    logger.debug(f"Insufficient capital for signal: {signal.market_id}")
                    continue
                
                # Execute trade
                trade = self._create_backtest_trade(signal, timestamp, execution_price)
                
                if signal.signal_type.value == "buy":
                    self.positions[trade.trade_id] = trade
                    self.current_capital -= (trade_cost + commission)
                else:  # sell
                    # For sells, we need to close existing positions or short
                    self._handle_sell_signal(signal, timestamp, execution_price)
                
                logger.debug(f"Executed signal: {signal.market_id} {signal.signal_type.value} @ {execution_price}")
            
            except Exception as e:
                logger.error(f"Error executing signal: {e}")
    
    async def _execute_backtest_opportunities(
        self,
        opportunities: List[ArbitrageOpportunity],
        timestamp: datetime,
        current_markets: Dict[str, List[MarketData]]
    ) -> None:
        """Execute arbitrage opportunities in backtest."""
        for opportunity in opportunities:
            try:
                # Check risk limits
                risk_check, risk_message = self.risk_manager.check_opportunity_risk(opportunity)
                if not risk_check:
                    logger.debug(f"Opportunity rejected by risk manager: {risk_message}")
                    continue
                
                # Execute opportunity trades
                await self._execute_arbitrage_opportunity(opportunity, timestamp, current_markets)
            
            except Exception as e:
                logger.error(f"Error executing opportunity: {e}")
    
    def _find_market_data(
        self,
        platform: str,
        market_id: str,
        current_markets: Dict[str, List[MarketData]]
    ) -> Optional[MarketData]:
        """Find market data for a specific market."""
        platform_markets = current_markets.get(platform, [])
        for market in platform_markets:
            if market.market_id == market_id:
                return market
        return None
    
    def _calculate_execution_price(self, signal: TradingSignal, market_data: MarketData) -> float:
        """Calculate execution price with slippage."""
        if signal.outcome == "yes":
            base_price = market_data.yes_price or 0.5
        else:
            base_price = market_data.no_price or 0.5
        
        # Apply slippage
        if signal.signal_type.value == "buy":
            # Buying increases price
            execution_price = base_price * (1 + self.slippage)
        else:
            # Selling decreases price
            execution_price = base_price * (1 - self.slippage)
        
        return max(0.01, min(0.99, execution_price))
    
    def _create_backtest_trade(
        self,
        signal: TradingSignal,
        timestamp: datetime,
        execution_price: float
    ) -> BacktestTrade:
        """Create a backtest trade from a signal."""
        self.trade_counter += 1
        
        return BacktestTrade(
            trade_id=f"BT_{timestamp.strftime('%Y%m%d%H%M%S')}_{self.trade_counter:04d}",
            timestamp=timestamp,
            platform=signal.platform,
            market_id=signal.market_id,
            side=signal.signal_type.value,
            outcome=signal.outcome,
            quantity=signal.suggested_size,
            entry_price=execution_price,
            strategy=signal.strategy_name,
            metadata=signal.metadata or {}
        )
    
    def _handle_sell_signal(
        self,
        signal: TradingSignal,
        timestamp: datetime,
        execution_price: float
    ) -> None:
        """Handle sell signal by closing positions."""
        # Find matching positions to close
        positions_to_close = []
        
        for trade_id, position in self.positions.items():
            if (position.platform == signal.platform and 
                position.market_id == signal.market_id and 
                position.outcome == signal.outcome):
                positions_to_close.append(trade_id)
        
        # Close positions
        for trade_id in positions_to_close:
            position = self.positions[trade_id]
            
            # Calculate PnL
            pnl = position.quantity * (execution_price - position.entry_price)
            commission = position.quantity * execution_price * self.commission_rate
            
            # Update position
            position.exit_price = execution_price
            position.exit_timestamp = timestamp
            position.pnl = pnl - commission
            position.status = "closed"
            
            # Add to closed trades
            self.closed_trades.append(position)
            
            # Update capital
            self.current_capital += (position.quantity * execution_price - commission)
            
            # Remove from positions
            del self.positions[trade_id]
    
    async def _execute_arbitrage_opportunity(
        self,
        opportunity: ArbitrageOpportunity,
        timestamp: datetime,
        current_markets: Dict[str, List[MarketData]]
    ) -> None:
        """Execute arbitrage opportunity trades."""
        # Simplified implementation - execute trades for each market in opportunity
        for market_info in opportunity.markets:
            platform = market_info["platform"]
            market_id = market_info["market_id"]
            
            market_data = self._find_market_data(platform, market_id, current_markets)
            if not market_data:
                continue
            
            # Create synthetic signal for this leg
            # This is simplified - real implementation would be more sophisticated
            position_size = min(100.0, opportunity.required_capital / len(opportunity.markets))
            
            # Determine signal direction based on opportunity type and market
            signal_type = "buy"  # Simplified
            
            # Create and execute trade
            execution_price = market_data.yes_price or 0.5
            trade = BacktestTrade(
                trade_id=f"ARB_{timestamp.strftime('%Y%m%d%H%M%S')}_{self.trade_counter:04d}",
                timestamp=timestamp,
                platform=platform,
                market_id=market_id,
                side=signal_type,
                outcome="yes",
                quantity=position_size,
                entry_price=execution_price,
                strategy=opportunity.strategy_name,
                metadata={"opportunity_id": opportunity.opportunity_id}
            )
            
            self.trade_counter += 1
            self.positions[trade.trade_id] = trade
            
            # Update capital
            trade_cost = position_size * execution_price
            commission = trade_cost * self.commission_rate
            self.current_capital -= (trade_cost + commission)
    
    def _update_positions_pnl(
        self,
        current_markets: Dict[str, List[MarketData]],
        timestamp: datetime
    ) -> None:
        """Update unrealized PnL for open positions."""
        for position in self.positions.values():
            market_data = self._find_market_data(position.platform, position.market_id, current_markets)
            
            if market_data:
                if position.outcome == "yes":
                    current_price = market_data.yes_price or position.entry_price
                else:
                    current_price = market_data.no_price or position.entry_price
                
                # Calculate unrealized PnL
                unrealized_pnl = position.quantity * (current_price - position.entry_price)
                position.metadata["unrealized_pnl"] = unrealized_pnl
                position.metadata["current_price"] = current_price
    
    def _generate_backtest_results(
        self,
        strategy_name: str,
        start_date: datetime,
        end_date: datetime
    ) -> BacktestResult:
        """Generate comprehensive backtest results."""
        try:
            # Calculate basic metrics
            total_return = (self.current_capital - self.initial_capital) / self.initial_capital
            
            # Calculate annual return
            days = (end_date - start_date).days
            annual_return = (1 + total_return) ** (365 / max(days, 1)) - 1 if days > 0 else 0.0
            
            # Calculate Sharpe ratio
            if len(self.daily_returns) > 1:
                daily_return_mean = np.mean(self.daily_returns)
                daily_return_std = np.std(self.daily_returns)
                sharpe_ratio = (daily_return_mean / daily_return_std) * np.sqrt(252) if daily_return_std > 0 else 0.0
            else:
                sharpe_ratio = 0.0
            
            # Calculate max drawdown
            max_drawdown = self._calculate_max_drawdown()
            
            # Calculate trade statistics
            total_trades = len(self.closed_trades)
            winning_trades = len([t for t in self.closed_trades if t.pnl and t.pnl > 0])
            losing_trades = total_trades - winning_trades
            
            win_rate = winning_trades / total_trades if total_trades > 0 else 0.0
            
            wins = [t.pnl for t in self.closed_trades if t.pnl and t.pnl > 0]
            losses = [t.pnl for t in self.closed_trades if t.pnl and t.pnl < 0]
            
            avg_win = np.mean(wins) if wins else 0.0
            avg_loss = np.mean(losses) if losses else 0.0
            
            profit_factor = abs(avg_win * winning_trades / (avg_loss * losing_trades)) if avg_loss != 0 and losing_trades > 0 else 0.0
            
            # Create trade log
            trade_log = []
            for trade in self.closed_trades:
                trade_log.append({
                    "trade_id": trade.trade_id,
                    "timestamp": trade.timestamp,
                    "platform": trade.platform,
                    "market_id": trade.market_id,
                    "side": trade.side,
                    "outcome": trade.outcome,
                    "quantity": trade.quantity,
                    "entry_price": trade.entry_price,
                    "exit_price": trade.exit_price,
                    "pnl": trade.pnl,
                    "strategy": trade.strategy
                })
            
            return BacktestResult(
                strategy_name=strategy_name,
                start_date=start_date,
                end_date=end_date,
                initial_capital=self.initial_capital,
                final_capital=self.current_capital,
                total_return=total_return,
                annual_return=annual_return,
                max_drawdown=max_drawdown,
                sharpe_ratio=sharpe_ratio,
                win_rate=win_rate,
                total_trades=total_trades,
                winning_trades=winning_trades,
                losing_trades=losing_trades,
                avg_win=avg_win,
                avg_loss=avg_loss,
                profit_factor=profit_factor,
                daily_returns=self.daily_returns,
                equity_curve=self.equity_curve,
                trade_log=trade_log,
                risk_metrics={}
            )
        
        except Exception as e:
            logger.error(f"Error generating backtest results: {e}")
            return BacktestResult(
                strategy_name=strategy_name,
                start_date=start_date,
                end_date=end_date,
                initial_capital=self.initial_capital,
                final_capital=self.current_capital,
                total_return=0.0,
                annual_return=0.0,
                max_drawdown=0.0,
                sharpe_ratio=0.0,
                win_rate=0.0,
                total_trades=0,
                winning_trades=0,
                losing_trades=0,
                avg_win=0.0,
                avg_loss=0.0,
                profit_factor=0.0,
                daily_returns=[],
                equity_curve=[],
                trade_log=[],
                risk_metrics={}
            )
    
    def _calculate_max_drawdown(self) -> float:
        """Calculate maximum drawdown from equity curve."""
        if len(self.equity_curve) < 2:
            return 0.0
        
        equity_values = [point[1] for point in self.equity_curve]
        
        max_dd = 0.0
        peak = equity_values[0]
        
        for value in equity_values:
            if value > peak:
                peak = value
            
            drawdown = (peak - value) / peak if peak > 0 else 0.0
            max_dd = max(max_dd, drawdown)
        
        return max_dd