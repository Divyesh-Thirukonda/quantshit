"""
Example usage of the backtesting engine
"""

from datetime import datetime, timedelta
import random

from quantshit import Backtester, Market, Portfolio
from quantshit.strategies.examples import MeanReversionStrategy, MomentumStrategy


def generate_sample_market_data(
    market_id: str,
    question: str,
    num_periods: int = 100,
    initial_price: float = 0.5,
    volatility: float = 0.05,
    resolve_at_end: bool = True
) -> list:
    """
    Generate sample market data for backtesting
    
    Args:
        market_id: Market identifier
        question: Market question
        num_periods: Number of time periods to generate
        initial_price: Starting YES price
        volatility: Price volatility
        resolve_at_end: Whether to resolve market at end
        
    Returns:
        List of Market objects representing historical data
    """
    markets = []
    current_price = initial_price
    start_time = datetime.now()
    
    for i in range(num_periods):
        # Random walk with mean reversion
        change = random.gauss(0, volatility)
        mean_reversion = (0.5 - current_price) * 0.1
        current_price += change + mean_reversion
        
        # Keep price in valid range
        current_price = max(0.01, min(0.99, current_price))
        
        timestamp = start_time + timedelta(hours=i)
        
        # Create market
        market = Market(
            id=market_id,
            question=question,
            current_yes_price=current_price,
            current_no_price=1.0 - current_price,
            timestamp=timestamp
        )
        
        markets.append(market)
    
    # Resolve market at end
    if resolve_at_end and len(markets) > 0:
        final_market = markets[-1]
        # Resolve based on final price (higher probability of YES if price was high)
        resolution = random.random() < final_market.current_yes_price
        
        resolved_market = Market(
            id=market_id,
            question=question,
            current_yes_price=1.0 if resolution else 0.0,
            current_no_price=0.0 if resolution else 1.0,
            resolved=True,
            resolution=resolution,
            timestamp=final_market.timestamp + timedelta(hours=1)
        )
        markets.append(resolved_market)
    
    return markets


def run_example():
    """Run example backtest"""
    print("=" * 70)
    print("Prediction Market Backtesting Engine - Example")
    print("=" * 70)
    print()
    
    # Generate sample data for multiple markets
    print("Generating sample market data...")
    all_market_data = []
    
    markets_config = [
        ("market_1", "Will candidate A win the election?", 100, 0.6, 0.08),
        ("market_2", "Will GDP grow by more than 3%?", 100, 0.4, 0.06),
        ("market_3", "Will the stock market reach new highs?", 100, 0.5, 0.10),
    ]
    
    for market_id, question, periods, initial_price, volatility in markets_config:
        market_data = generate_sample_market_data(
            market_id, question, periods, initial_price, volatility
        )
        all_market_data.extend(market_data)
    
    # Sort by timestamp
    all_market_data.sort(key=lambda m: m.timestamp)
    
    print(f"Generated {len(all_market_data)} market data points")
    print()
    
    # Run backtest with Mean Reversion strategy
    print("Running backtest with Mean Reversion Strategy...")
    print("-" * 70)
    
    backtester = Backtester(
        initial_capital=10000,
        commission_rate=0.01,
        slippage=0.005
    )
    
    strategy = MeanReversionStrategy()
    strategy.set_params(
        threshold=0.5,
        deviation=0.15,
        position_size=0.2,
        max_price=0.75,
        min_price=0.25
    )
    
    performance_df = backtester.run(all_market_data, strategy)
    results = backtester.get_results()
    
    print(f"\nStrategy: {strategy.name}")
    print(f"Initial Capital: ${results['initial_capital']:,.2f}")
    print(f"Final Value: ${results['total_value']:,.2f}")
    print(f"Total P&L: ${results['total_pnl']:,.2f}")
    print(f"Returns: {results['returns']*100:.2f}%")
    print(f"Number of Trades: {results['num_trades']}")
    print(f"Sharpe Ratio: {results.get('sharpe_ratio', 0):.2f}")
    print(f"Max Drawdown: {results.get('max_drawdown', 0)*100:.2f}%")
    print()
    
    # Run backtest with Momentum strategy
    print("Running backtest with Momentum Strategy...")
    print("-" * 70)
    
    backtester2 = Backtester(
        initial_capital=10000,
        commission_rate=0.01,
        slippage=0.005
    )
    
    strategy2 = MomentumStrategy()
    strategy2.set_params(
        lookback_periods=10,
        momentum_threshold=0.08,
        position_size=0.15
    )
    
    performance_df2 = backtester2.run(all_market_data, strategy2)
    results2 = backtester2.get_results()
    
    print(f"\nStrategy: {strategy2.name}")
    print(f"Initial Capital: ${results2['initial_capital']:,.2f}")
    print(f"Final Value: ${results2['total_value']:,.2f}")
    print(f"Total P&L: ${results2['total_pnl']:,.2f}")
    print(f"Returns: {results2['returns']*100:.2f}%")
    print(f"Number of Trades: {results2['num_trades']}")
    print(f"Sharpe Ratio: {results2.get('sharpe_ratio', 0):.2f}")
    print(f"Max Drawdown: {results2.get('max_drawdown', 0)*100:.2f}%")
    print()
    
    print("=" * 70)
    print("Backtest Complete!")
    print("=" * 70)
    
    # Display performance over time
    if len(performance_df) > 0:
        print("\nPerformance Summary (Mean Reversion):")
        print(performance_df.head(10).to_string(index=False))
        print("...")
        print(performance_df.tail(10).to_string(index=False))


if __name__ == "__main__":
    run_example()
