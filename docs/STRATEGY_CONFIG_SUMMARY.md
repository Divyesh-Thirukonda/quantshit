# Strategy Configuration Refactoring - Summary

**Date**: October 31, 2025
**Status**: ✅ Complete and tested

## What Changed

Trading parameters (`MIN_VOLUME`, `MIN_SPREAD`, position sizes, profit thresholds, etc.) have been moved from environment variables (`.env`) to strategy-specific configurations in code.

## Why This Is Better

### Before ❌
```bash
# .env file
MIN_VOLUME=1000
MIN_SPREAD=0.05
```

**Problems:**
- All strategies forced to use same parameters
- Trading logic mixed with infrastructure config
- Hard to test different parameter combinations
- Required environment changes to experiment

### After ✅
```python
# src/strategies/config.py
config = SimpleArbitrageConfig(
    min_volume=1000.0,
    min_profit_pct=0.05,
    min_confidence=0.5,
    # ... all trading parameters
)
strategy = SimpleArbitrageStrategy(config)
```

**Benefits:**
- ✅ Different strategies can have different parameters
- ✅ Clear separation: infrastructure vs. trading logic
- ✅ Easy to test with different configs
- ✅ Type-safe with validation
- ✅ No environment variable changes needed

## Quick Start

### 1. Environment Variables (Simplified)

Your `.env` file is now simpler - only infrastructure config:

```bash
# API Keys
KALSHI_API_KEY=your_key_here
POLYMARKET_API_KEY=your_key_here

# System settings
PAPER_TRADING=true
LOG_LEVEL=INFO
```

### 2. Trading Parameters (In Code)

Customize trading parameters in your bot initialization:

```python
from src.strategies import SimpleArbitrageStrategy, SimpleArbitrageConfig

# Conservative trading
config = SimpleArbitrageConfig(
    min_volume=10000.0,      # High volume only
    min_profit_pct=0.10,     # 10% minimum profit
    max_position_size=100    # Small positions
)

strategy = SimpleArbitrageStrategy(config)
bot = ArbitrageBot()
bot.strategy = strategy
```

### 3. Run Example

See `examples/custom_strategy_config.py` for complete examples:

```bash
python examples/custom_strategy_config.py
```

This shows conservative, aggressive, and balanced configurations.

## Configuration Reference

### Available Parameters

All parameters with defaults in `SimpleArbitrageConfig`:

```python
# Market filtering
min_volume: float = 1000.0              # Min market volume ($)
min_liquidity: float = 0.0              # Min liquidity required

# Opportunity filtering
min_profit_pct: float = 0.05            # 5% minimum profit
min_confidence: float = 0.5             # 50% title similarity

# Position sizing
max_position_size: int = 1000           # Max contracts
min_position_size: int = 10             # Min contracts
default_position_size: int = 100        # Default size

# Risk management
take_profit_pct: float = 0.10           # Take profit at 10%
stop_loss_pct: float = -0.05            # Stop loss at -5%
max_positions: int = 10                 # Max concurrent positions

# Strategy-specific
require_both_markets_open: bool = True  # Both must be open
max_slippage_pct: float = 0.01          # 1% max slippage
min_time_to_expiry_hours: int = 24      # 24h minimum to close
```

### Example Configurations

**Conservative (Low Risk)**
```python
SimpleArbitrageConfig(
    min_volume=10000.0,
    min_profit_pct=0.10,      # 10% only
    min_confidence=0.8,        # High confidence
    max_position_size=100,     # Small positions
    take_profit_pct=0.15,
    stop_loss_pct=-0.03
)
```

**Aggressive (High Volume)**
```python
SimpleArbitrageConfig(
    min_volume=500.0,          # Accept low volume
    min_profit_pct=0.02,       # 2% is ok
    min_confidence=0.4,        # Lenient matching
    max_position_size=1000,    # Large positions
    take_profit_pct=0.08,
    stop_loss_pct=-0.08
)
```

**Balanced (Default)**
```python
SimpleArbitrageConfig()  # Use all defaults
```

## File Changes

### New Files ✨
- `src/strategies/config.py` - Configuration dataclasses
- `examples/custom_strategy_config.py` - Usage examples
- `docs/STRATEGY_CONFIG_REFACTOR.md` - Detailed documentation
- `STRATEGY_CONFIG_SUMMARY.md` - This file

### Modified Files ✏️
- `src/strategies/base.py` - Accept config in __init__
- `src/strategies/simple_arb.py` - Use config for all parameters
- `src/strategies/__init__.py` - Export config classes
- `src/main.py` - Create strategy config, use strategy.config
- `src/config/settings.py` - Removed MIN_VOLUME, MIN_SPREAD
- `.env.example` - Removed trading parameters
- `api/app.py` - Updated status endpoint
- `README.md` - Updated configuration docs
- `CLAUDE.md` - Updated configuration docs

## Testing

All systems tested and working:

```bash
✅ Strategy config creation
✅ Config validation
✅ Strategy initialization with config
✅ ArbitrageBot uses strategy config
✅ API servers import successfully
✅ Example script runs correctly
```

## Migration Guide

### For Existing Users

1. **Update your `.env` file**:
   - Remove `MIN_VOLUME=1000`
   - Remove `MIN_SPREAD=0.05`
   - Keep only API keys and system settings

2. **Customize parameters in code** (optional):
   - Edit `src/main.py` to customize `SimpleArbitrageConfig`
   - Or use the bot with default config (no changes needed)

3. **No code changes required** if you're happy with defaults!

### For Developers

1. **Creating new strategies**:
   - Create a config class extending `StrategyConfig`
   - Accept config in your strategy's `__init__`
   - Use `self.config.parameter_name` in your logic

2. **Testing strategies**:
   - Create test configs with specific values
   - No need to mock environment variables

## Next Steps

Potential future enhancements:

1. **Config API endpoints** - Change parameters via API
2. **Config persistence** - Save/load configs from database
3. **Config presets** - Pre-defined conservative/balanced/aggressive
4. **Config UI** - Dashboard to adjust parameters
5. **Multiple strategies** - Run different strategies simultaneously

## Questions?

- See `docs/STRATEGY_CONFIG_REFACTOR.md` for detailed documentation
- See `examples/custom_strategy_config.py` for code examples
- See `src/strategies/config.py` for all available parameters

---

**Summary**: Trading parameters are now owned by strategies, not environment variables. This makes the system more flexible, testable, and maintainable. 🎉
