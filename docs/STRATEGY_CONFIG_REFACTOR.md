# Strategy Configuration Refactoring

**Date**: October 31, 2025
**Purpose**: Move trading parameters from environment variables to strategy-specific configurations

## Problem

Previously, trading parameters like `MIN_VOLUME` and `MIN_SPREAD` were configured globally via environment variables in `.env`. This approach had several issues:

1. **Not strategy-specific**: All strategies had to use the same parameters
2. **Mixed concerns**: Infrastructure config (API keys) mixed with trading logic (parameters)
3. **Hard to test**: Changing parameters required env var changes
4. **Not extensible**: Adding new strategies with different parameters was awkward

## Solution

Implemented a strategy configuration system where each strategy owns its trading parameters:

### Architecture Changes

```
Before:
.env → settings.py → ArbitrageBot → uses global MIN_VOLUME/MIN_SPREAD
                                  → Strategy (no parameters)

After:
.env → settings.py (infrastructure only)
                  ↓
ArbitrageBot → StrategyConfig → Strategy (owns parameters)
            ↓
         Uses strategy.config.min_volume
```

### New Files

**`src/strategies/config.py`** - Strategy configuration dataclasses:

```python
@dataclass
class StrategyConfig:
    """Base configuration for all strategies"""
    min_volume: float = 1000.0
    min_profit_pct: float = 0.02
    min_confidence: float = 0.7
    max_position_size: int = 1000
    # ... etc

@dataclass
class SimpleArbitrageConfig(StrategyConfig):
    """Configuration specific to simple arbitrage"""
    min_volume: float = 1000.0
    min_profit_pct: float = 0.05  # 5% minimum
    require_both_markets_open: bool = True
    max_slippage_pct: float = 0.01
    # ... etc
```

### Modified Files

#### 1. `src/strategies/base.py`
- Changed `__init__` to accept `StrategyConfig`
- Strategies now store `self.config`

#### 2. `src/strategies/simple_arb.py`
- Accepts `SimpleArbitrageConfig` instead of individual parameters
- Uses `self.config.min_volume`, `self.config.min_profit_pct`, etc.
- Includes config validation

#### 3. `src/main.py` (ArbitrageBot)
- Creates `SimpleArbitrageConfig` when initializing strategy
- Gets `min_volume` from `strategy.config` instead of `settings`
- Pass min_volume to exchange clients when fetching markets

#### 4. `src/config/settings.py`
- Removed `MIN_VOLUME` and `MIN_SPREAD`
- Now only contains infrastructure config (API keys, endpoints, etc.)

#### 5. `.env.example`
- Removed `MIN_VOLUME=1000` and `MIN_SPREAD=0.05`
- Added note directing users to `src/strategies/config.py`

## Benefits

### 1. Clear Separation of Concerns

```python
# Infrastructure config (how to connect)
settings.KALSHI_API_KEY
settings.PAPER_TRADING
settings.LOG_LEVEL

# Trading logic config (what to trade)
strategy.config.min_volume
strategy.config.min_profit_pct
strategy.config.max_position_size
```

### 2. Strategy-Specific Parameters

Different strategies can have different parameters:

```python
# Conservative strategy
conservative = SimpleArbitrageConfig(
    min_volume=10000.0,
    min_profit_pct=0.10,  # 10% minimum
    max_position_size=100
)

# Aggressive strategy
aggressive = SimpleArbitrageConfig(
    min_volume=500.0,
    min_profit_pct=0.02,  # 2% minimum
    max_position_size=1000
)

# Use different strategies
bot1 = ArbitrageBot(strategy=SimpleArbitrageStrategy(conservative))
bot2 = ArbitrageBot(strategy=SimpleArbitrageStrategy(aggressive))
```

### 3. Easier Testing

```python
# Test with specific config
test_config = SimpleArbitrageConfig(
    min_volume=100.0,
    min_profit_pct=0.01
)
strategy = SimpleArbitrageStrategy(test_config)

# No need to mock environment variables!
```

### 4. Type Safety & Validation

```python
config = SimpleArbitrageConfig(
    min_profit_pct=1.5  # Invalid!
)

errors = config.validate()
# → ["min_profit_pct must be between 0 and 1, got 1.5"]
```

## Migration Guide

### For Users

**Before** (`.env` file):
```bash
KALSHI_API_KEY=...
POLYMARKET_API_KEY=...
MIN_VOLUME=1000
MIN_SPREAD=0.05
```

**After** (`.env` file):
```bash
KALSHI_API_KEY=...
POLYMARKET_API_KEY=...
# MIN_VOLUME and MIN_SPREAD removed
```

**To customize trading parameters**, edit the strategy initialization in `src/main.py`:

```python
strategy_config = SimpleArbitrageConfig(
    min_volume=5000.0,      # Your custom value
    min_profit_pct=0.03,    # Your custom value
    min_confidence=0.6,     # Your custom value
)
bot.strategy = SimpleArbitrageStrategy(config=strategy_config)
```

### For Developers

**Creating a new strategy:**

```python
from dataclasses import dataclass
from .config import StrategyConfig
from .base import BaseStrategy

@dataclass
class MyStrategyConfig(StrategyConfig):
    # Add strategy-specific parameters
    my_parameter: float = 0.5
    another_param: int = 100

class MyStrategy(BaseStrategy):
    def __init__(self, config: MyStrategyConfig = None):
        if config is None:
            config = MyStrategyConfig()

        super().__init__(config)
        self.config: MyStrategyConfig = config

    # Use self.config.my_parameter in your logic
```

## Configuration Hierarchy

```
StrategyConfig (base)
├── min_volume
├── min_profit_pct
├── min_confidence
├── max_position_size
├── take_profit_pct
├── stop_loss_pct
└── ...

SimpleArbitrageConfig (extends StrategyConfig)
├── All base fields (can override defaults)
├── require_both_markets_open
├── max_slippage_pct
├── min_time_to_expiry_hours
└── validate() method

YourCustomStrategyConfig (extends StrategyConfig)
├── All base fields
├── your_custom_parameter
└── your_custom_logic
```

## Testing Results

✅ All tests passing:
- Strategy config creation works
- Config validation works
- Strategy initialization with config works
- ArbitrageBot uses strategy config correctly
- API servers import successfully

## Files Changed

### Created
- ✨ `src/strategies/config.py` - Strategy configuration dataclasses
- ✨ `docs/STRATEGY_CONFIG_REFACTOR.md` - This document

### Modified
- ✏️ `src/strategies/base.py` - Accept StrategyConfig in __init__
- ✏️ `src/strategies/simple_arb.py` - Use SimpleArbitrageConfig
- ✏️ `src/strategies/__init__.py` - Export config classes
- ✏️ `src/main.py` - Create strategy config, use strategy.config.min_volume
- ✏️ `src/config/settings.py` - Remove MIN_VOLUME and MIN_SPREAD
- ✏️ `.env.example` - Remove MIN_VOLUME and MIN_SPREAD, add note
- ✏️ `api/app.py` - Remove MIN_VOLUME/MIN_SPREAD from status endpoint
- ✏️ `README.md` - Update configuration documentation
- ✏️ `CLAUDE.md` - Update configuration documentation

### Not Modified (intentionally)
- ⏸️ `tests/conftest.py` - Test configs still reference old env vars (tests may need update)
- ⏸️ `tests/run_tests.py` - Test configs still reference old env vars (tests may need update)

## Future Enhancements

1. **Add strategy config to API**
   - Allow changing strategy parameters via API
   - Return current strategy config in `/status` endpoint

2. **Config persistence**
   - Save strategy configs to database
   - Load last-used config on startup

3. **Config presets**
   - Pre-defined configs for common scenarios
   - "conservative", "balanced", "aggressive" presets

4. **Dynamic config updates**
   - Change strategy parameters without restarting bot
   - Hot-reload strategy configs

5. **Config UI**
   - Dashboard to adjust strategy parameters
   - Real-time config updates

## Related Documentation

- `src/strategies/config.py` - Configuration classes
- `CLAUDE.md` - Project documentation (updated)
- `README.md` - User documentation (updated)
