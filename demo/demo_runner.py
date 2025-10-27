#!/usr/bin/env python3
"""
Demo runner for the arbitrage bot using fake market data.
This script loads fake market data from JSON files and runs the arbitrage strategy.
"""

import json
import os
import sys
from pathlib import Path

# Add parent directory to path to import bot modules
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.strategies.arbitrage import ArbitrageStrategy


def load_demo_markets():
    """Load fake market data from JSON files."""
    demo_dir = Path(__file__).parent

    with open(demo_dir / "polymarket_markets.json", "r") as f:
        polymarket_data = json.load(f)

    with open(demo_dir / "kalshi_markets.json", "r") as f:
        kalshi_data = json.load(f)

    return {
        "polymarket": polymarket_data,
        "kalshi": kalshi_data
    }


def print_market_summary(markets_by_platform):
    """Print a summary of loaded markets."""
    print("\n" + "="*80)
    print("DEMO MODE - Loaded Market Data")
    print("="*80)

    for platform, markets in markets_by_platform.items():
        print(f"\n{platform.upper()}:")
        print(f"  Total markets: {len(markets)}")
        total_volume = sum(m['volume'] for m in markets)
        print(f"  Total volume: ${total_volume:,.0f}")
        print(f"\n  Markets:")
        for market in markets:
            print(f"    - {market['title']}")
            print(f"      YES: ${market['yes_price']:.2f} | NO: ${market['no_price']:.2f} | Volume: ${market['volume']:,.0f}")


def print_opportunities(opportunities):
    """Print found arbitrage opportunities."""
    print("\n" + "="*80)
    print("ARBITRAGE OPPORTUNITIES FOUND")
    print("="*80)

    if not opportunities:
        print("\nNo arbitrage opportunities found with current parameters.")
        print("Try adjusting MIN_SPREAD or MIN_VOLUME in demo/.env.demo")
        return

    for i, opp in enumerate(opportunities, 1):
        print(f"\nOpportunity #{i}:")
        print(f"  ID: {opp.id}")
        print(f"  Outcome: {opp.outcome.value}")
        print(f"  Buy Market: {opp.buy_market.title} ({opp.buy_market.platform.value})")
        print(f"  Sell Market: {opp.sell_market.title} ({opp.sell_market.platform.value})")
        print(f"  Buy Price: ${opp.buy_price:.4f}")
        print(f"  Sell Price: ${opp.sell_price:.4f}")
        print(f"  Spread: {opp.spread:.2%}")
        print(f"  Expected Profit/Share: ${opp.expected_profit_per_share:.4f}")
        print(f"  Max Quantity: {opp.max_quantity}")
        print(f"  Confidence Score: {opp.confidence_score:.2f}")
        print(f"  Risk Level: {opp.risk_level.value}")


def run_demo():
    """Run the demo arbitrage bot."""
    print("\n" + "="*80)
    print("ARBITRAGE BOT - DEMO MODE")
    print("="*80)
    print("\nRunning with fake market data from demo/ folder")

    # Load environment variables from demo config
    from dotenv import load_dotenv
    demo_env_path = Path(__file__).parent / ".env.demo"
    load_dotenv(demo_env_path)

    print(f"Configuration:")
    print(f"  MIN_VOLUME: ${float(os.getenv('MIN_VOLUME', 1000000)):,.0f}")
    print(f"  MIN_SPREAD: {float(os.getenv('MIN_SPREAD', 0.05)):.1%}")

    # Load demo market data
    markets_by_platform = load_demo_markets()
    print_market_summary(markets_by_platform)

    # Initialize strategy
    min_spread = float(os.getenv('MIN_SPREAD', 0.05))
    min_volume = float(os.getenv('MIN_VOLUME', 1000000))

    print("\n" + "="*80)
    print("RUNNING ARBITRAGE STRATEGY")
    print("="*80)

    strategy = ArbitrageStrategy(
        min_spread=min_spread,
        min_volume=min_volume
    )

    # Find opportunities
    opportunities = strategy.find_opportunities(markets_by_platform)

    # Print results
    print_opportunities(opportunities)

    # Summary
    print("\n" + "="*80)
    print("DEMO COMPLETE")
    print("="*80)
    print(f"\nTotal opportunities found: {len(opportunities)}")

    if opportunities:
        total_profit = sum(opp.expected_profit_per_share * opp.max_quantity for opp in opportunities)
        print(f"Total expected profit: ${total_profit:.2f}")
        print("\nNote: In demo mode, no actual trades are executed.")
        print("To run with real data, configure API keys in .env and run: python main.py --once")

    print("\n")


if __name__ == "__main__":
    try:
        run_demo()
    except Exception as e:
        print(f"\nError running demo: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
