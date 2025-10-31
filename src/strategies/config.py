"""
Strategy configuration - defines parameters for trading strategies.
Each strategy can define its own configuration class with specific parameters.
"""

from dataclasses import dataclass
from typing import Optional


@dataclass
class StrategyConfig:
    """
    Base configuration for trading strategies.
    Extend this for strategy-specific configurations.
    """

    # Market filtering parameters
    min_volume: float = 1000.0  # Minimum market volume to consider ($)
    min_liquidity: float = 0.0  # Minimum liquidity required

    # Opportunity filtering parameters
    min_profit_pct: float = 0.02  # Minimum profit percentage (2%)
    min_confidence: float = 0.7  # Minimum confidence score for matches

    # Position sizing
    max_position_size: int = 1000  # Maximum contracts per position
    min_position_size: int = 10  # Minimum contracts per position
    default_position_size: int = 100  # Default position size

    # Risk management
    take_profit_pct: float = 0.10  # Take profit at 10% gain
    stop_loss_pct: float = -0.05  # Stop loss at -5% loss
    max_positions: int = 10  # Maximum concurrent positions

    # Strategy metadata
    name: str = "Base Strategy"
    description: str = "Base strategy configuration"


@dataclass
class SimpleArbitrageConfig(StrategyConfig):
    """
    Configuration for simple arbitrage strategy.
    Buy low on one exchange, sell high on another.
    """

    # Override defaults for simple arbitrage
    min_volume: float = 1000.0  # $1000 minimum volume
    min_profit_pct: float = 0.05  # 5% minimum spread
    min_confidence: float = 0.5  # 50% title similarity

    # Position sizing for arbitrage
    max_position_size: int = 1000
    min_position_size: int = 10
    default_position_size: int = 100

    # Risk management
    take_profit_pct: float = 0.10  # Close at 10% profit
    stop_loss_pct: float = -0.05  # Close at -5% loss

    # Arbitrage-specific parameters
    max_slippage_pct: float = 0.01  # 1% max slippage
    require_both_markets_open: bool = True  # Both markets must be open
    min_time_to_expiry_hours: int = 24  # Minimum 24h to market close

    # Metadata
    name: str = "Simple Arbitrage"
    description: str = "Basic cross-exchange arbitrage strategy"

    def validate(self) -> list[str]:
        """Validate configuration parameters"""
        errors = []

        if self.min_volume < 0:
            errors.append(f"min_volume must be non-negative, got {self.min_volume}")

        if self.min_profit_pct < 0 or self.min_profit_pct > 1:
            errors.append(f"min_profit_pct must be between 0 and 1, got {self.min_profit_pct}")

        if self.min_confidence < 0 or self.min_confidence > 1:
            errors.append(f"min_confidence must be between 0 and 1, got {self.min_confidence}")

        if self.max_position_size < self.min_position_size:
            errors.append(
                f"max_position_size ({self.max_position_size}) must be >= "
                f"min_position_size ({self.min_position_size})"
            )

        if self.take_profit_pct <= 0:
            errors.append(f"take_profit_pct must be positive, got {self.take_profit_pct}")

        if self.stop_loss_pct >= 0:
            errors.append(f"stop_loss_pct must be negative, got {self.stop_loss_pct}")

        return errors
