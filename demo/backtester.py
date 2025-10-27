#!/usr/bin/env python3
"""
Backtesting framework for arbitrage strategies.
"""

import sys
from pathlib import Path
from datetime import datetime, timedelta
from typing import Dict, List, Tuple
import json

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.strategies.arbitrage import ArbitrageStrategy


class Trade:
    """Represents a completed trade"""

    def __init__(
        self,
        date: str,
        buy_platform: str,
        sell_platform: str,
        buy_price: float,
        sell_price: float,
        quantity: int,
        spread: float
    ):
        self.date = date
        self.buy_platform = buy_platform
        self.sell_platform = sell_platform
        self.buy_price = buy_price
        self.sell_price = sell_price
        self.quantity = quantity
        self.spread = spread
        self.profit = (sell_price - buy_price) * quantity

    def to_dict(self) -> Dict:
        return {
            "date": self.date,
            "buy_platform": self.buy_platform,
            "sell_platform": self.sell_platform,
            "buy_price": self.buy_price,
            "sell_price": self.sell_price,
            "quantity": self.quantity,
            "spread": self.spread,
            "profit": self.profit
        }


class BacktestResult:
    """Results from a backtest run"""

    def __init__(
        self,
        trades: List[Trade],
        daily_returns: List[Dict],
        total_profit: float,
        total_trades: int,
        win_rate: float,
        sharpe_ratio: float,
        max_drawdown: float,
        avg_spread: float
    ):
        self.trades = trades
        self.daily_returns = daily_returns
        self.total_profit = total_profit
        self.total_trades = total_trades
        self.win_rate = win_rate
        self.sharpe_ratio = sharpe_ratio
        self.max_drawdown = max_drawdown
        self.avg_spread = avg_spread

    def to_dict(self) -> Dict:
        return {
            "summary": {
                "total_profit": self.total_profit,
                "total_trades": self.total_trades,
                "win_rate": self.win_rate,
                "sharpe_ratio": self.sharpe_ratio,
                "max_drawdown": self.max_drawdown,
                "avg_spread": self.avg_spread,
                "profit_per_trade": self.total_profit / max(self.total_trades, 1)
            },
            "trades": [t.to_dict() for t in self.trades],
            "daily_returns": self.daily_returns
        }


class Backtester:
    """Backtest arbitrage strategies on historical data"""

    def __init__(
        self,
        min_spread: float = 0.05,
        min_volume: float = 1000000,
        max_trades_per_day: int = 5,
        trade_amount: float = 1000
    ):
        self.min_spread = min_spread
        self.min_volume = min_volume
        self.max_trades_per_day = max_trades_per_day
        self.trade_amount = trade_amount

    def load_historical_data(self, demo_dir: str = "demo") -> Dict[str, List[Dict]]:
        """Load market data with history"""
        demo_path = Path(demo_dir)

        with open(demo_path / "polymarket_markets.json", "r") as f:
            polymarket_data = json.load(f)

        with open(demo_path / "kalshi_markets.json", "r") as f:
            kalshi_data = json.load(f)

        return {
            "polymarket": polymarket_data,
            "kalshi": kalshi_data
        }

    def _reconstruct_markets_for_date(
        self,
        markets_with_history: Dict[str, List[Dict]],
        date_str: str
    ) -> Dict[str, List[Dict]]:
        """Reconstruct market state for a specific date"""
        markets_by_platform = {}

        for platform, markets in markets_with_history.items():
            platform_markets = []

            for market in markets:
                # Find historical data point for this date
                history_point = None
                for hist in market.get("history", []):
                    if hist["date"] == date_str:
                        history_point = hist
                        break

                if history_point:
                    # Create market snapshot for this date
                    platform_markets.append({
                        "id": market["id"],
                        "title": market["title"],
                        "platform": platform,
                        "category": market.get("category", "unknown"),
                        "volume": history_point["volume"],
                        "yes_price": history_point["yes_price"],
                        "no_price": history_point["no_price"],
                        "liquidity": history_point["liquidity"]
                    })

            markets_by_platform[platform] = platform_markets

        return markets_by_platform

    def _get_historical_dates(
        self,
        markets_with_history: Dict[str, List[Dict]]
    ) -> List[str]:
        """Extract list of dates from historical data"""
        # Get dates from first market in first platform
        for platform, markets in markets_with_history.items():
            if markets and markets[0].get("history"):
                return [h["date"] for h in markets[0]["history"]]
        return []

    def run_backtest(self) -> BacktestResult:
        """Run backtest over historical data"""
        print("\n" + "="*80)
        print("BACKTESTING ARBITRAGE STRATEGY")
        print("="*80)

        # Load historical data
        markets_with_history = self.load_historical_data()

        # Get dates to backtest
        dates = self._get_historical_dates(markets_with_history)
        print(f"\nBacktesting over {len(dates)} days")
        print(f"Strategy parameters:")
        print(f"  Min Spread: {self.min_spread:.1%}")
        print(f"  Min Volume: ${self.min_volume:,.0f}")
        print(f"  Max Trades/Day: {self.max_trades_per_day}")
        print(f"  Trade Amount: ${self.trade_amount:,.0f}")

        # Initialize strategy
        strategy = ArbitrageStrategy(
            min_spread=self.min_spread,
            min_volume=self.min_volume
        )

        # Run backtest day by day
        all_trades = []
        daily_returns = []
        cumulative_profit = 0

        for date in dates:
            # Reconstruct market state for this date
            markets = self._reconstruct_markets_for_date(markets_with_history, date)

            # Find opportunities
            opportunities = strategy.find_opportunities(markets)

            # Execute top opportunities (limited by max_trades_per_day)
            daily_profit = 0
            trades_today = 0

            for opp in opportunities[:self.max_trades_per_day]:
                # Simulate trade execution
                quantity = min(
                    int(self.trade_amount / opp.buy_price),
                    opp.max_quantity
                )

                if quantity > 0:
                    trade = Trade(
                        date=date,
                        buy_platform=opp.buy_market.platform.value,
                        sell_platform=opp.sell_market.platform.value,
                        buy_price=opp.buy_price,
                        sell_price=opp.sell_price,
                        quantity=quantity,
                        spread=opp.spread
                    )

                    all_trades.append(trade)
                    daily_profit += trade.profit
                    trades_today += 1

            cumulative_profit += daily_profit

            # Record daily performance
            daily_returns.append({
                "date": date,
                "trades": trades_today,
                "daily_profit": daily_profit,
                "cumulative_profit": cumulative_profit
            })

        # Calculate performance metrics
        total_trades = len(all_trades)
        total_profit = cumulative_profit

        # Win rate (profitable trades)
        winning_trades = sum(1 for t in all_trades if t.profit > 0)
        win_rate = winning_trades / max(total_trades, 1)

        # Average spread
        avg_spread = sum(t.spread for t in all_trades) / max(total_trades, 1)

        # Sharpe ratio (annualized)
        daily_profits = [d["daily_profit"] for d in daily_returns]
        if daily_profits and len(daily_profits) > 1:
            import numpy as np
            daily_returns_pct = np.array(daily_profits) / self.trade_amount
            sharpe_ratio = np.mean(daily_returns_pct) / (np.std(daily_returns_pct) + 1e-6) * np.sqrt(252)
        else:
            sharpe_ratio = 0

        # Max drawdown
        cumulative_profits = [d["cumulative_profit"] for d in daily_returns]
        max_drawdown = 0
        peak = 0
        for profit in cumulative_profits:
            if profit > peak:
                peak = profit
            drawdown = (peak - profit) / (peak + 1)
            if drawdown > max_drawdown:
                max_drawdown = drawdown

        result = BacktestResult(
            trades=all_trades,
            daily_returns=daily_returns,
            total_profit=total_profit,
            total_trades=total_trades,
            win_rate=win_rate,
            sharpe_ratio=sharpe_ratio,
            max_drawdown=max_drawdown,
            avg_spread=avg_spread
        )

        print("\n" + "="*80)
        print("BACKTEST RESULTS")
        print("="*80)
        print(f"\nTotal Trades: {total_trades}")
        print(f"Total Profit: ${total_profit:,.2f}")
        print(f"Profit per Trade: ${total_profit/max(total_trades, 1):,.2f}")
        print(f"Win Rate: {win_rate:.1%}")
        print(f"Average Spread: {avg_spread:.2%}")
        print(f"Sharpe Ratio: {sharpe_ratio:.2f}")
        print(f"Max Drawdown: {max_drawdown:.1%}")

        return result

    def project_returns(self, backtest_result: BacktestResult, days_forward: int = 30) -> Dict:
        """Project future returns based on historical performance"""
        import numpy as np

        daily_profits = [d["daily_profit"] for d in backtest_result.daily_returns]

        if not daily_profits:
            return {
                "days_forward": days_forward,
                "expected_profit": 0,
                "confidence_interval_95": (0, 0),
                "probability_positive": 0
            }

        # Calculate statistics
        mean_daily_profit = np.mean(daily_profits)
        std_daily_profit = np.std(daily_profits)

        # Project forward
        expected_profit = mean_daily_profit * days_forward

        # 95% confidence interval
        std_error = std_daily_profit * np.sqrt(days_forward)
        ci_lower = expected_profit - 1.96 * std_error
        ci_upper = expected_profit + 1.96 * std_error

        # Probability of positive returns
        if std_error > 0:
            z_score = expected_profit / std_error
            from scipy.stats import norm
            prob_positive = norm.cdf(z_score)
        else:
            prob_positive = 1.0 if expected_profit > 0 else 0.0

        return {
            "days_forward": days_forward,
            "expected_profit": expected_profit,
            "confidence_interval_95": (ci_lower, ci_upper),
            "probability_positive": prob_positive,
            "expected_daily_profit": mean_daily_profit,
            "daily_profit_std": std_daily_profit
        }


if __name__ == "__main__":
    # Run backtest with default parameters
    backtester = Backtester(
        min_spread=0.05,
        min_volume=1000000,
        max_trades_per_day=3,
        trade_amount=1000
    )

    result = backtester.run_backtest()

    # Project returns
    print("\n" + "="*80)
    print("PROJECTED RETURNS (Next 30 Days)")
    print("="*80)

    projection = backtester.project_returns(result, days_forward=30)
    print(f"\nExpected Profit: ${projection['expected_profit']:,.2f}")
    print(f"95% Confidence Interval: ${projection['confidence_interval_95'][0]:,.2f} to ${projection['confidence_interval_95'][1]:,.2f}")
    print(f"Expected Daily Profit: ${projection['expected_daily_profit']:,.2f}")
    print(f"Daily Profit Std Dev: ${projection['daily_profit_std']:,.2f}")
