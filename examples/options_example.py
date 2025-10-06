"""
Options Market-Making Example

This example demonstrates how to use the options module for market-making
and volatility capture strategies.
"""

import numpy as np
from quantshit.options import (
    BlackScholes,
    historical_volatility,
    implied_volatility,
    PortfolioRiskManager,
    MarketDataFeed,
    OptionChainData
)


def example_black_scholes():
    """Example: Calculate option price and Greeks using Black-Scholes"""
    print("=" * 60)
    print("Black-Scholes Option Pricing Example")
    print("=" * 60)
    
    # Parameters
    S = 100  # Current stock price
    K = 105  # Strike price
    T = 0.25  # Time to expiration (3 months)
    r = 0.05  # Risk-free rate (5%)
    sigma = 0.2  # Volatility (20%)
    
    # Create Black-Scholes model for call option
    bs_call = BlackScholes(S, K, T, r, sigma, option_type='call')
    
    print(f"\nCall Option:")
    print(f"  Stock Price: ${S}")
    print(f"  Strike Price: ${K}")
    print(f"  Time to Expiration: {T} years")
    print(f"  Risk-Free Rate: {r*100}%")
    print(f"  Volatility: {sigma*100}%")
    print(f"\n  Price: ${bs_call.price():.4f}")
    
    # Calculate Greeks
    greeks = bs_call.greeks()
    print(f"\n  Greeks:")
    print(f"    Delta: {greeks['delta']:.4f}")
    print(f"    Gamma: {greeks['gamma']:.4f}")
    print(f"    Theta: {greeks['theta']:.4f}")
    print(f"    Vega: {greeks['vega']:.4f}")
    print(f"    Rho: {greeks['rho']:.4f}")
    
    # Put option
    bs_put = BlackScholes(S, K, T, r, sigma, option_type='put')
    print(f"\nPut Option:")
    print(f"  Price: ${bs_put.price():.4f}")
    print(f"  Delta: {bs_put.delta():.4f}")


def example_volatility():
    """Example: Calculate historical and implied volatility"""
    print("\n" + "=" * 60)
    print("Volatility Calculation Example")
    print("=" * 60)
    
    # Generate sample price data
    np.random.seed(42)
    prices = 100 * np.exp(np.cumsum(np.random.normal(0, 0.01, 100)))
    
    # Calculate historical volatility
    hist_vol = historical_volatility(prices, window=30)
    print(f"\nHistorical Volatility (30-day): {hist_vol*100:.2f}%")
    
    # Calculate implied volatility from market price
    S = 100
    K = 105
    T = 0.25
    r = 0.05
    market_price = 3.5
    
    try:
        imp_vol = implied_volatility(market_price, S, K, T, r, option_type='call')
        print(f"Implied Volatility: {imp_vol*100:.2f}%")
        
        # Compare
        print(f"\nVolatility Spread: {(imp_vol - hist_vol)*100:.2f}%")
        if imp_vol > hist_vol:
            print("  -> Options may be overpriced (sell volatility)")
        else:
            print("  -> Options may be underpriced (buy volatility)")
    except ValueError as e:
        print(f"Could not calculate implied volatility: {e}")


def example_risk_management():
    """Example: Portfolio risk management and hedging"""
    print("\n" + "=" * 60)
    print("Portfolio Risk Management Example")
    print("=" * 60)
    
    # Create portfolio manager
    portfolio = PortfolioRiskManager()
    
    # Add some positions
    # Long 10 call options
    contract1 = {'strike': 100, 'expiry': 0.25, 'type': 'call'}
    greeks1 = {'delta': 0.6, 'gamma': 0.03, 'theta': -0.05, 'vega': 0.2, 'rho': 0.1}
    portfolio.add_position(contract1, quantity=10, greeks=greeks1)
    
    # Short 5 put options
    contract2 = {'strike': 95, 'expiry': 0.25, 'type': 'put'}
    greeks2 = {'delta': -0.4, 'gamma': 0.025, 'theta': -0.04, 'vega': 0.18, 'rho': -0.08}
    portfolio.add_position(contract2, quantity=-5, greeks=greeks2)
    
    # Calculate portfolio Greeks
    portfolio_greeks = portfolio.portfolio_greeks()
    print("\nPortfolio Greeks:")
    for greek, value in portfolio_greeks.items():
        print(f"  {greek.capitalize()}: {value:.4f}")
    
    # Calculate delta hedge
    hedge_shares = portfolio.delta_hedge_quantity()
    print(f"\nDelta Hedge: {'Sell' if hedge_shares < 0 else 'Buy'} {abs(hedge_shares):.2f} shares")
    
    # Risk metrics
    metrics = portfolio.risk_metrics()
    print(f"\nRisk Metrics:")
    print(f"  Delta Neutral: {metrics['is_delta_neutral']}")
    print(f"  Gamma Neutral: {metrics['is_gamma_neutral']}")
    print(f"  Position Count: {metrics['position_count']}")


def example_market_data():
    """Example: Order book and market data feed"""
    print("\n" + "=" * 60)
    print("Market Data Feed Example")
    print("=" * 60)
    
    # Create market data feed
    feed = MarketDataFeed('AAPL', initial_price=150.0, volatility=0.25)
    
    print(f"\nInitial Price: ${feed.get_current_price():.2f}")
    
    # Generate some price ticks
    print("\nGenerating 5 price ticks:")
    for i in range(5):
        new_price = feed.generate_tick()
        order_book = feed.get_order_book()
        
        print(f"\n  Tick {i+1}:")
        print(f"    Price: ${new_price:.2f}")
        print(f"    Best Bid: ${order_book.best_bid():.2f}")
        print(f"    Best Ask: ${order_book.best_ask():.2f}")
        print(f"    Spread: ${order_book.bid_ask_spread():.4f}")
        print(f"    Mid Price: ${order_book.mid_price():.2f}")


def example_option_chain():
    """Example: Working with option chains"""
    print("\n" + "=" * 60)
    print("Option Chain Example")
    print("=" * 60)
    
    # Create option chain
    chain = OptionChainData('SPY', underlying_price=450.0)
    
    # Add some options
    strikes = [440, 445, 450, 455, 460]
    for strike in strikes:
        # Call options
        call_bid = max(0, 450 - strike - 2)
        call_ask = max(0, 450 - strike + 2)
        chain.add_option(strike, 0.25, 'call', call_bid, call_ask, volume=100)
        
        # Put options
        put_bid = max(0, strike - 450 - 2)
        put_ask = max(0, strike - 450 + 2)
        chain.add_option(strike, 0.25, 'put', put_bid, put_ask, volume=80)
    
    # Get all calls
    calls = chain.get_options(option_type='call')
    print(f"\nCall Options ({len(calls)} total):")
    for opt in calls:
        print(f"  Strike ${opt['strike']}: Bid ${opt['bid']:.2f}, Ask ${opt['ask']:.2f}, "
              f"Spread ${opt['spread']:.2f}")
    
    # Calculate theoretical prices
    theoretical_prices = {}
    for opt in chain.options:
        bs = BlackScholes(450, opt['strike'], opt['expiry'], 0.05, 0.2, opt['type'])
        key = (opt['strike'], opt['expiry'], opt['type'])
        theoretical_prices[key] = bs.price()
    
    # Find mispriced options
    mispriced = chain.find_mispriced_options(theoretical_prices, threshold=0.1)
    print(f"\nMispriced Options (>10% difference):")
    for item in mispriced[:3]:  # Show top 3
        opt = item['option']
        print(f"  {opt['type'].upper()} Strike ${opt['strike']}: "
              f"Market ${item['market_price']:.2f}, "
              f"Theoretical ${item['theoretical_price']:.2f}, "
              f"Diff {item['difference_pct']*100:.1f}%")


if __name__ == '__main__':
    example_black_scholes()
    example_volatility()
    example_risk_management()
    example_market_data()
    example_option_chain()
    
    print("\n" + "=" * 60)
    print("Examples completed successfully!")
    print("=" * 60)
