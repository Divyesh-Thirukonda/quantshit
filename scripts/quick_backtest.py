#!/usr/bin/env python3
"""
Quick start script for running backtests.
"""
import sys
import os
import asyncio
import pandas as pd
from datetime import datetime, timedelta

# Add src to path
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

from src.strategies.cross_platform import CrossPlatformArbitrageStrategy
from src.strategies.correlation import CorrelationArbitrageStrategy
from src.backtesting.engine import BacktestEngine
from src.data.providers import MarketData, MarketStatus


def create_sample_data():
    """Create sample historical data for backtesting."""
    print("Creating sample historical data...")
    
    # Generate sample price data
    dates = pd.date_range(start='2024-01-01', end='2024-01-31', freq='H')
    
    # Sample market data for Kalshi
    kalshi_data = []
    for i, date in enumerate(dates):
        # Simulate price movements
        base_price = 0.5 + 0.2 * (i % 10) / 10
        noise = 0.05 * (i % 3 - 1)
        
        kalshi_data.append({
            'timestamp': date,
            'market_id': 'KALSHI_TEST_001',
            'title': 'Test Market A',
            'category': 'politics',
            'yes_price': max(0.01, min(0.99, base_price + noise)),
            'no_price': max(0.01, min(0.99, 1 - (base_price + noise))),
            'volume': 100 + (i % 20) * 50,
            'close_date': datetime(2024, 2, 1)
        })
    
    kalshi_df = pd.DataFrame(kalshi_data)
    
    return {'kalshi': kalshi_df}


async def run_sample_backtest():
    """Run a sample backtest."""
    print("🔄 Running sample backtest...")
    
    # Create sample data
    historical_data = create_sample_data()
    
    # Initialize backtest engine
    engine = BacktestEngine(initial_capital=10000.0)
    
    # Create strategy
    strategy = CrossPlatformArbitrageStrategy({
        'min_spread': 0.02,
        'max_position_size': 100.0,
        'similarity_threshold': 0.8
    })
    
    # Run backtest
    start_date = datetime(2024, 1, 1)
    end_date = datetime(2024, 1, 31)
    
    try:
        results = await engine.run_backtest(
            strategy=strategy,
            historical_data=historical_data,
            start_date=start_date,
            end_date=end_date,
            rebalance_frequency='4H'
        )
        
        # Display results
        print("\n📊 Backtest Results:")
        print(f"Strategy: {results.strategy_name}")
        print(f"Period: {results.start_date.date()} to {results.end_date.date()}")
        print(f"Initial Capital: ${results.initial_capital:,.2f}")
        print(f"Final Capital: ${results.final_capital:,.2f}")
        print(f"Total Return: {results.total_return:.2%}")
        print(f"Annual Return: {results.annual_return:.2%}")
        print(f"Max Drawdown: {results.max_drawdown:.2%}")
        print(f"Sharpe Ratio: {results.sharpe_ratio:.2f}")
        print(f"Win Rate: {results.win_rate:.2%}")
        print(f"Total Trades: {results.total_trades}")
        
        if results.total_trades > 0:
            print(f"Average Win: ${results.avg_win:.2f}")
            print(f"Average Loss: ${results.avg_loss:.2f}")
            print(f"Profit Factor: {results.profit_factor:.2f}")
        
        print("\n✅ Sample backtest completed successfully!")
        
    except Exception as e:
        print(f"❌ Error running backtest: {e}")


def main():
    """Main function."""
    print("🎯 Arbitrage System - Quick Start Backtest")
    print("=" * 50)
    
    try:
        asyncio.run(run_sample_backtest())
    except KeyboardInterrupt:
        print("\n⚠️  Backtest interrupted by user")
    except Exception as e:
        print(f"❌ Error: {e}")


if __name__ == "__main__":
    main()