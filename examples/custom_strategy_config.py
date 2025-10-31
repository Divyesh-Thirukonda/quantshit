"""
Example: Custom Strategy Configuration

This example shows how to customize trading parameters for different
strategies without modifying environment variables.
"""

import sys
import os
# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.main import ArbitrageBot
from src.strategies import SimpleArbitrageStrategy, SimpleArbitrageConfig


def conservative_bot():
    """
    Conservative trading bot with high thresholds and smaller positions.
    Good for risk-averse trading with high-confidence opportunities only.
    """
    config = SimpleArbitrageConfig(
        # Market filtering
        min_volume=10000.0,          # Only high-volume markets ($10k+)
        min_profit_pct=0.10,         # Only 10%+ profit opportunities
        min_confidence=0.8,          # 80% title similarity required

        # Position sizing
        max_position_size=100,       # Small positions
        min_position_size=10,
        default_position_size=50,

        # Risk management
        take_profit_pct=0.15,        # Take profit at 15% gain
        stop_loss_pct=-0.03,         # Stop loss at -3%
        max_positions=3,             # Only 3 concurrent positions

        # Additional constraints
        require_both_markets_open=True,
        min_time_to_expiry_hours=48,  # At least 2 days to close

        # Metadata
        name="Conservative Arbitrage",
        description="Low risk, high confidence arbitrage"
    )

    strategy = SimpleArbitrageStrategy(config=config)
    bot = ArbitrageBot()
    bot.strategy = strategy  # Override default strategy

    print(f"Conservative bot initialized:")
    print(f"  Min volume: ${config.min_volume:,.0f}")
    print(f"  Min profit: {config.min_profit_pct:.1%}")
    print(f"  Max position size: {config.max_position_size}")

    return bot


def aggressive_bot():
    """
    Aggressive trading bot with lower thresholds and larger positions.
    Good for maximizing opportunities and higher volume trading.
    """
    config = SimpleArbitrageConfig(
        # Market filtering
        min_volume=500.0,            # Accept lower volume markets
        min_profit_pct=0.02,         # Even 2% profit is acceptable
        min_confidence=0.4,          # More lenient matching

        # Position sizing
        max_position_size=1000,      # Large positions
        min_position_size=50,
        default_position_size=250,

        # Risk management
        take_profit_pct=0.08,        # Take profit at 8% (exit faster)
        stop_loss_pct=-0.08,         # Wider stop loss
        max_positions=20,            # Many concurrent positions

        # Less constraints
        require_both_markets_open=False,  # Trade even if one closed
        min_time_to_expiry_hours=12,      # Accept markets closing soon

        # Metadata
        name="Aggressive Arbitrage",
        description="High volume, lower thresholds"
    )

    strategy = SimpleArbitrageStrategy(config=config)
    bot = ArbitrageBot()
    bot.strategy = strategy

    print(f"Aggressive bot initialized:")
    print(f"  Min volume: ${config.min_volume:,.0f}")
    print(f"  Min profit: {config.min_profit_pct:.1%}")
    print(f"  Max position size: {config.max_position_size}")

    return bot


def balanced_bot():
    """
    Balanced trading bot with moderate thresholds.
    Default configuration - good starting point for most users.
    """
    # Using default config (no customization needed)
    config = SimpleArbitrageConfig()  # All defaults

    strategy = SimpleArbitrageStrategy(config=config)
    bot = ArbitrageBot()
    bot.strategy = strategy

    print(f"Balanced bot initialized (default config):")
    print(f"  Min volume: ${config.min_volume:,.0f}")
    print(f"  Min profit: {config.min_profit_pct:.1%}")
    print(f"  Max position size: {config.max_position_size}")

    return bot


def main():
    """Run example bots with different configurations"""

    print("=" * 60)
    print("Strategy Configuration Examples")
    print("=" * 60)

    # Example 1: Conservative
    print("\n1. Conservative Strategy:")
    print("-" * 40)
    conservative = conservative_bot()

    # Example 2: Aggressive
    print("\n2. Aggressive Strategy:")
    print("-" * 40)
    aggressive = aggressive_bot()

    # Example 3: Balanced (default)
    print("\n3. Balanced Strategy (Default):")
    print("-" * 40)
    balanced = balanced_bot()

    # Show how parameters differ
    print("\n" + "=" * 60)
    print("Parameter Comparison:")
    print("=" * 60)
    print(f"{'Parameter':<25} {'Conservative':<15} {'Aggressive':<15} {'Balanced':<15}")
    print("-" * 70)
    print(f"{'Min Volume':<25} ${conservative.strategy.config.min_volume:>13,.0f} "
          f"${aggressive.strategy.config.min_volume:>13,.0f} "
          f"${balanced.strategy.config.min_volume:>13,.0f}")
    print(f"{'Min Profit %':<25} {conservative.strategy.config.min_profit_pct:>14.1%} "
          f"{aggressive.strategy.config.min_profit_pct:>14.1%} "
          f"{balanced.strategy.config.min_profit_pct:>14.1%}")
    print(f"{'Max Position Size':<25} {conservative.strategy.config.max_position_size:>14} "
          f"{aggressive.strategy.config.max_position_size:>14} "
          f"{balanced.strategy.config.max_position_size:>14}")
    print(f"{'Take Profit %':<25} {conservative.strategy.config.take_profit_pct:>14.1%} "
          f"{aggressive.strategy.config.take_profit_pct:>14.1%} "
          f"{balanced.strategy.config.take_profit_pct:>14.1%}")

    print("\n✓ All configurations valid and ready to use!")


if __name__ == "__main__":
    main()
