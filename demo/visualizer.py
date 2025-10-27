#!/usr/bin/env python3
"""
Visualization module for backtest results.
"""

import matplotlib
matplotlib.use('Agg')  # Use non-interactive backend for serverless
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
from datetime import datetime
from typing import Dict, List
import io
import base64

from backtester import BacktestResult


class BacktestVisualizer:
    """Create visualizations for backtest results"""

    def __init__(self, backtest_result: BacktestResult):
        self.result = backtest_result

    def plot_cumulative_returns(self, figsize=(12, 6)) -> plt.Figure:
        """Plot cumulative profit over time"""
        fig, ax = plt.subplots(figsize=figsize)

        dates = [datetime.strptime(d["date"], "%Y-%m-%d") for d in self.result.daily_returns]
        cumulative_profits = [d["cumulative_profit"] for d in self.result.daily_returns]

        ax.plot(dates, cumulative_profits, linewidth=2, color='#2E86AB', label='Cumulative Profit')
        ax.axhline(y=0, color='gray', linestyle='--', alpha=0.5)

        # Formatting
        ax.set_xlabel('Date', fontsize=12)
        ax.set_ylabel('Cumulative Profit ($)', fontsize=12)
        ax.set_title('Cumulative Profit Over Time', fontsize=14, fontweight='bold')
        ax.grid(True, alpha=0.3)
        ax.legend()

        # Format x-axis dates
        ax.xaxis.set_major_formatter(mdates.DateFormatter('%m/%d'))
        plt.xticks(rotation=45)
        plt.tight_layout()

        return fig

    def plot_daily_profits(self, figsize=(12, 6)) -> plt.Figure:
        """Plot daily profit distribution"""
        fig, ax = plt.subplots(figsize=figsize)

        dates = [datetime.strptime(d["date"], "%Y-%m-%d") for d in self.result.daily_returns]
        daily_profits = [d["daily_profit"] for d in self.result.daily_returns]

        colors = ['#06A77D' if p >= 0 else '#D74E09' for p in daily_profits]
        ax.bar(dates, daily_profits, color=colors, alpha=0.7)
        ax.axhline(y=0, color='black', linestyle='-', linewidth=0.8)

        # Formatting
        ax.set_xlabel('Date', fontsize=12)
        ax.set_ylabel('Daily Profit ($)', fontsize=12)
        ax.set_title('Daily Profit Distribution', fontsize=14, fontweight='bold')
        ax.grid(True, alpha=0.3, axis='y')

        # Format x-axis dates
        ax.xaxis.set_major_formatter(mdates.DateFormatter('%m/%d'))
        plt.xticks(rotation=45)
        plt.tight_layout()

        return fig

    def plot_spread_distribution(self, figsize=(10, 6)) -> plt.Figure:
        """Plot distribution of spreads captured"""
        fig, ax = plt.subplots(figsize=figsize)

        spreads = [t.spread * 100 for t in self.result.trades]  # Convert to percentage

        ax.hist(spreads, bins=20, color='#A23B72', alpha=0.7, edgecolor='black')

        # Formatting
        ax.set_xlabel('Spread (%)', fontsize=12)
        ax.set_ylabel('Frequency', fontsize=12)
        ax.set_title('Distribution of Arbitrage Spreads', fontsize=14, fontweight='bold')
        ax.grid(True, alpha=0.3, axis='y')

        # Add mean line
        mean_spread = sum(spreads) / len(spreads) if spreads else 0
        ax.axvline(x=mean_spread, color='red', linestyle='--', linewidth=2,
                   label=f'Mean: {mean_spread:.2f}%')
        ax.legend()

        plt.tight_layout()
        return fig

    def plot_trades_per_day(self, figsize=(12, 6)) -> plt.Figure:
        """Plot number of trades executed per day"""
        fig, ax = plt.subplots(figsize=figsize)

        dates = [datetime.strptime(d["date"], "%Y-%m-%d") for d in self.result.daily_returns]
        trades_per_day = [d["trades"] for d in self.result.daily_returns]

        ax.bar(dates, trades_per_day, color='#F18F01', alpha=0.7, edgecolor='black')

        # Formatting
        ax.set_xlabel('Date', fontsize=12)
        ax.set_ylabel('Number of Trades', fontsize=12)
        ax.set_title('Trading Activity Over Time', fontsize=14, fontweight='bold')
        ax.grid(True, alpha=0.3, axis='y')

        # Format x-axis dates
        ax.xaxis.set_major_formatter(mdates.DateFormatter('%m/%d'))
        plt.xticks(rotation=45)
        plt.tight_layout()

        return fig

    def plot_platform_distribution(self, figsize=(10, 6)) -> plt.Figure:
        """Plot distribution of trades by platform"""
        fig, (ax1, ax2) = plt.subplots(1, 2, figsize=figsize)

        # Buy platform distribution
        buy_platforms = {}
        for trade in self.result.trades:
            platform = trade.buy_platform
            buy_platforms[platform] = buy_platforms.get(platform, 0) + 1

        ax1.pie(buy_platforms.values(), labels=buy_platforms.keys(), autopct='%1.1f%%',
                startangle=90, colors=['#2E86AB', '#A23B72', '#F18F01'])
        ax1.set_title('Buy Side Platform Distribution', fontsize=12, fontweight='bold')

        # Sell platform distribution
        sell_platforms = {}
        for trade in self.result.trades:
            platform = trade.sell_platform
            sell_platforms[platform] = sell_platforms.get(platform, 0) + 1

        ax2.pie(sell_platforms.values(), labels=sell_platforms.keys(), autopct='%1.1f%%',
                startangle=90, colors=['#06A77D', '#D74E09', '#F4D35E'])
        ax2.set_title('Sell Side Platform Distribution', fontsize=12, fontweight='bold')

        plt.tight_layout()
        return fig

    def create_dashboard(self, output_path: str = None) -> plt.Figure:
        """Create comprehensive dashboard with all metrics"""
        fig = plt.figure(figsize=(16, 12))
        gs = fig.add_gridspec(3, 2, hspace=0.3, wspace=0.3)

        # Cumulative returns
        ax1 = fig.add_subplot(gs[0, :])
        dates = [datetime.strptime(d["date"], "%Y-%m-%d") for d in self.result.daily_returns]
        cumulative_profits = [d["cumulative_profit"] for d in self.result.daily_returns]
        ax1.plot(dates, cumulative_profits, linewidth=2, color='#2E86AB')
        ax1.fill_between(dates, 0, cumulative_profits, alpha=0.3, color='#2E86AB')
        ax1.axhline(y=0, color='gray', linestyle='--', alpha=0.5)
        ax1.set_title('Cumulative Profit Over Time', fontsize=14, fontweight='bold')
        ax1.set_xlabel('Date')
        ax1.set_ylabel('Profit ($)')
        ax1.grid(True, alpha=0.3)
        ax1.xaxis.set_major_formatter(mdates.DateFormatter('%m/%d'))
        plt.setp(ax1.xaxis.get_majorticklabels(), rotation=45)

        # Daily profits
        ax2 = fig.add_subplot(gs[1, 0])
        daily_profits = [d["daily_profit"] for d in self.result.daily_returns]
        colors = ['#06A77D' if p >= 0 else '#D74E09' for p in daily_profits]
        ax2.bar(dates, daily_profits, color=colors, alpha=0.7)
        ax2.axhline(y=0, color='black', linestyle='-', linewidth=0.8)
        ax2.set_title('Daily Profit', fontsize=12, fontweight='bold')
        ax2.set_ylabel('Profit ($)')
        ax2.grid(True, alpha=0.3, axis='y')
        ax2.xaxis.set_major_formatter(mdates.DateFormatter('%m/%d'))
        plt.setp(ax2.xaxis.get_majorticklabels(), rotation=45)

        # Spread distribution
        ax3 = fig.add_subplot(gs[1, 1])
        spreads = [t.spread * 100 for t in self.result.trades]
        ax3.hist(spreads, bins=15, color='#A23B72', alpha=0.7, edgecolor='black')
        mean_spread = sum(spreads) / len(spreads) if spreads else 0
        ax3.axvline(x=mean_spread, color='red', linestyle='--', linewidth=2,
                   label=f'Mean: {mean_spread:.2f}%')
        ax3.set_title('Spread Distribution', fontsize=12, fontweight='bold')
        ax3.set_xlabel('Spread (%)')
        ax3.set_ylabel('Frequency')
        ax3.legend()
        ax3.grid(True, alpha=0.3, axis='y')

        # Trading activity
        ax4 = fig.add_subplot(gs[2, 0])
        trades_per_day = [d["trades"] for d in self.result.daily_returns]
        ax4.bar(dates, trades_per_day, color='#F18F01', alpha=0.7, edgecolor='black')
        ax4.set_title('Trading Activity', fontsize=12, fontweight='bold')
        ax4.set_ylabel('Trades per Day')
        ax4.grid(True, alpha=0.3, axis='y')
        ax4.xaxis.set_major_formatter(mdates.DateFormatter('%m/%d'))
        plt.setp(ax4.xaxis.get_majorticklabels(), rotation=45)

        # Performance metrics
        ax5 = fig.add_subplot(gs[2, 1])
        ax5.axis('off')

        metrics_text = f"""
        PERFORMANCE METRICS

        Total Profit: ${self.result.total_profit:,.2f}
        Total Trades: {self.result.total_trades}
        Profit/Trade: ${self.result.total_profit/max(self.result.total_trades, 1):,.2f}

        Win Rate: {self.result.win_rate:.1%}
        Avg Spread: {self.result.avg_spread:.2%}
        Sharpe Ratio: {self.result.sharpe_ratio:.2f}
        Max Drawdown: {self.result.max_drawdown:.1%}
        """

        ax5.text(0.1, 0.5, metrics_text, fontsize=11, family='monospace',
                verticalalignment='center', bbox=dict(boxstyle='round', facecolor='wheat', alpha=0.3))

        if output_path:
            plt.savefig(output_path, dpi=150, bbox_inches='tight')

        return fig

    def fig_to_base64(self, fig: plt.Figure) -> str:
        """Convert matplotlib figure to base64 string for API responses"""
        buf = io.BytesIO()
        fig.savefig(buf, format='png', dpi=100, bbox_inches='tight')
        buf.seek(0)
        img_base64 = base64.b64encode(buf.read()).decode('utf-8')
        buf.close()
        plt.close(fig)
        return img_base64

    def generate_all_plots(self) -> Dict[str, str]:
        """Generate all plots and return as base64-encoded images"""
        plots = {}

        # Generate each plot
        plots['cumulative_returns'] = self.fig_to_base64(self.plot_cumulative_returns())
        plots['daily_profits'] = self.fig_to_base64(self.plot_daily_profits())
        plots['spread_distribution'] = self.fig_to_base64(self.plot_spread_distribution())
        plots['trades_per_day'] = self.fig_to_base64(self.plot_trades_per_day())
        plots['platform_distribution'] = self.fig_to_base64(self.plot_platform_distribution())
        plots['dashboard'] = self.fig_to_base64(self.create_dashboard())

        return plots


if __name__ == "__main__":
    # Example usage
    from backtester import Backtester

    backtester = Backtester(
        min_spread=0.05,
        min_volume=1000000,
        max_trades_per_day=3,
        trade_amount=1000
    )

    result = backtester.run_backtest()

    visualizer = BacktestVisualizer(result)

    # Save dashboard
    visualizer.create_dashboard(output_path='demo/backtest_dashboard.png')
    print("\nDashboard saved to demo/backtest_dashboard.png")

    # Save individual plots
    visualizer.plot_cumulative_returns()
    plt.savefig('demo/cumulative_returns.png', dpi=150, bbox_inches='tight')

    visualizer.plot_daily_profits()
    plt.savefig('demo/daily_profits.png', dpi=150, bbox_inches='tight')

    print("Individual plots saved to demo/ directory")
