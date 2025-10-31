# Module Explanations - Theoretical Design

## `types.py` (Universal Types at src/ root)

**Purpose**: Central type definitions used across the entire application

**Contains**:
- `Exchange` enum: KALSHI, POLYMARKET
- `OrderSide` enum: BUY, SELL
- `OrderStatus` enum: PENDING, FILLED, CANCELLED, REJECTED
- `MarketStatus` enum: OPEN, CLOSED, SETTLED
- Type aliases: `Price = float`, `Quantity = int`, `Probability = float`
- Protocol/Interface definitions that enforce structure across modules

**Why here?**: Single source of truth for types. Every module imports from here instead of redefining.

---

## `models/` - Domain Models (Data Structures)

**Purpose**: Pure data classes representing business entities. No logic, just structure.

### `market.py`
**Represents**: A prediction market on either exchange
**Contains**:
- `id`: Unique identifier
- `exchange`: Which exchange (KALSHI or POLYMARKET)
- `title`: Market question
- `yes_price`: Current YES price
- `no_price`: Current NO price
- `volume`: Trading volume
- `liquidity`: Available liquidity
- `expiry`: Market close time
- `status`: OPEN/CLOSED/SETTLED

**Why separate?**: Both exchanges have markets, but with different field names. This normalizes them.

### `order.py`
**Represents**: A buy/sell order
**Contains**:
- `id`: Order ID
- `exchange`: Where order was placed
- `market_id`: Which market
- `side`: BUY or SELL
- `quantity`: Number of contracts
- `price`: Limit price
- `status`: Order state
- `filled_quantity`: How much filled
- `timestamp`: When created

**Why separate?**: Orders are created by executor, tracked by monitor, stored in DB. One definition.

### `position.py`
**Represents**: Current holdings in a market
**Contains**:
- `market_id`: Which market
- `exchange`: Which exchange
- `quantity`: Number of contracts held
- `side`: LONG (YES) or SHORT (NO)
- `avg_entry_price`: Average buy price
- `current_value`: Current market value
- `unrealized_pnl`: Paper profit/loss

**Why separate?**: Monitor tracks positions, executor updates them. Shared structure.

### `opportunity.py`
**Represents**: An arbitrage opportunity found between exchanges
**Contains**:
- `market_kalshi`: Kalshi market object
- `market_polymarket`: Polymarket market object
- `spread`: Price difference (%)
- `expected_profit`: Estimated profit after fees
- `confidence_score`: How confident we are markets are equivalent
- `expiry`: When opportunity expires
- `recommended_size`: Suggested trade size

**Why separate?**: Matcher creates these, scorer ranks them, executor acts on them.

---

## `services/` - Business Logic

**Purpose**: Where the actual work happens. Services coordinate between models and exchanges.

### `matching/`

#### `matcher.py`
**Purpose**: Find markets on both exchanges about the same event
**Logic**:
- Fetch all markets from Kalshi
- Fetch all markets from Polymarket
- Compare titles/descriptions using fuzzy matching or ML
- Return pairs of potentially equivalent markets

**Input**: Market lists from both exchanges
**Output**: List of `(kalshi_market, polymarket_market, similarity_score)` tuples

**Why here?**: Core arbitrage logic. Needs to be separate for testing and tuning.

#### `scorer.py`
**Purpose**: Calculate profitability of each matched pair
**Logic**:
- Take matched market pairs
- Calculate spread: `|kalshi_price - polymarket_price|`
- Subtract fees from both exchanges
- Account for slippage
- Calculate expected profit %
- Rank opportunities by profit potential

**Input**: Matched market pairs
**Output**: List of `Opportunity` objects, ranked by profitability

**Why here?**: Complex calculations. Separate from matching so we can update scoring without touching match logic.

### `execution/`

#### `validator.py`
**Purpose**: Safety checks before executing trades
**Logic**:
- Check account balance sufficient
- Verify market still open
- Check if opportunity still exists (prices didn't move)
- Validate trade size within risk limits
- Ensure we're not already in this position

**Input**: Opportunity + proposed trade size
**Output**: `ValidationResult` (pass/fail + reason)

**Why here?**: Never execute without validation. Prevents losing money on invalid trades.

#### `executor.py`
**Purpose**: Actually place orders on both exchanges
**Logic**:
- Receive validated opportunity
- Place order on Exchange A
- Wait for confirmation
- Place offsetting order on Exchange B
- If either fails, cancel the other
- Update position tracking

**Input**: Validated opportunity
**Output**: Execution result (success/failure + order IDs)

**Why here?**: Actual execution is separate from validation. Can have multiple execution strategies (aggressive, conservative).

### `monitoring/`

#### `tracker.py`
**Purpose**: Track all open positions and their P&L
**Logic**:
- Maintain list of all positions
- Periodically fetch current prices
- Calculate unrealized P&L
- Check if positions should be closed
- Update database with position changes

**Input**: Current positions + market data
**Output**: Updated positions with P&L

**Why here?**: Need constant monitoring separate from execution. Runs continuously.

#### `alerter.py`
**Purpose**: Send notifications when important events occur
**Logic**:
- Monitor opportunities above profit threshold
- Alert when profitable opportunity found
- Alert when position P&L crosses thresholds
- Alert on errors or failures
- Send to Telegram/Discord/Email

**Input**: Events (opportunity found, error occurred, etc.)
**Output**: Notifications sent

**Why here?**: Separate concern from monitoring. Can change notification method without touching tracking.

---

## `strategies/` - Trading Strategies

**Purpose**: Different approaches to arbitrage. Strategy pattern for extensibility.

### `base.py`
**Purpose**: Abstract interface all strategies must implement
**Defines**:
- `find_opportunities()` - method signature
- `calculate_position_size()` - method signature
- `should_close_position()` - method signature
- Configuration options every strategy needs

**Why here?**: Open/Closed Principle. Add new strategies by extending, not modifying.

### `simple_arb.py`
**Purpose**: Basic arbitrage strategy
**Logic**:
- Find price differences > threshold
- Buy on cheaper exchange, sell on expensive
- Close when spread narrows below threshold
- Equal position sizes on both sides

**Why separate from base?**: This is ONE way to arbitrage. Others exist.

### `hedged_arb.py`
**Purpose**: Market-neutral arbitrage
**Logic**:
- Take offsetting positions to be delta-neutral
- Profit from spread convergence, not price movement
- More complex position sizing
- Lower risk but potentially lower profit

**Why separate?**: Different strategy, different risk profile. User can choose.

---

## `database/` - Data Persistence

**Purpose**: Store and retrieve data. Abstract away database specifics.

### `repository.py`
**Purpose**: Data access layer - all DB operations go through here
**Contains**:
- `save_opportunity(opportunity)` - store opportunity
- `get_positions()` - fetch all positions
- `save_order(order)` - store order
- `get_historical_trades()` - fetch past trades
- `update_position(position)` - update position

**Why here?**: Dependency Inversion. Services don't know if we use Postgres, SQLite, or MongoDB. Just call repository methods.

### `schema.py`
**Purpose**: Database table/collection definitions
**Contains**:
- Table schemas for opportunities, orders, positions
- Indexes for fast queries
- Relationships between tables
- Migration definitions

**Why here?**: When changing DB structure, only modify this file. Services don't care about schema.

---

## `config/` - Configuration

**Purpose**: All configurable values in one place. Easy to change without touching code.

### `settings.py`
**Purpose**: Environment-specific configuration
**Contains**:
- API keys (from environment variables)
- Database connection strings
- Exchange endpoints (prod vs testnet)
- Logging levels
- Feature flags (enable/disable strategies)

**Why here?**: Change configuration without code changes. Different configs for dev/staging/prod.

### `constants.py`
**Purpose**: Business logic constants and thresholds
**Contains**:
- `MIN_PROFIT_THRESHOLD = 0.02` (2%)
- `MAX_POSITION_SIZE = 1000`
- `FEE_KALSHI = 0.007` (0.7%)
- `FEE_POLYMARKET = 0.02` (2%)
- `PRICE_TOLERANCE = 0.01`
- Timeout values, retry limits

**Why here?**: DRY. These numbers appear everywhere. Change once, affects everywhere.

---

## `utils/` - Shared Utilities

**Purpose**: Helper functions used across multiple modules. Avoid duplication.

### `logger.py`
**Purpose**: Centralized logging configuration
**Contains**:
- `setup_logger()` - configure log format, level, output
- Log rotation setup
- Structured logging helpers
- Different loggers for different modules

**Why here?**: Consistent logging everywhere. Change log format once.

### `math.py`
**Purpose**: Mathematical calculations used throughout app
**Contains**:
- `calculate_profit(buy_price, sell_price, quantity, fees)` - net profit
- `price_to_probability(price)` - convert price to probability
- `probability_to_price(prob)` - reverse conversion
- `calculate_implied_odds(yes_price, no_price)` - arbitrage detection
- `kelly_criterion(win_prob, odds)` - position sizing

**Why here?**: Math is reused in scorer, executor, monitor. One implementation.

### `decorators.py`
**Purpose**: Reusable function decorators
**Contains**:
- `@retry(max_attempts=3, backoff=2)` - retry failed API calls
- `@rate_limit(calls=10, period=1)` - prevent API rate limiting
- `@log_execution_time` - performance monitoring
- `@cache(ttl=60)` - cache results for N seconds

**Why here?**: DRY. Add `@retry` to any function without reimplementing retry logic.

---

## `main.py` - Application Entry Point

**Purpose**: Wire everything together and start the bot

**Flow**:
```
1. Load configuration from config/settings.py
2. Initialize logger from utils/logger.py
3. Create exchange clients (kalshi, polymarket)
4. Initialize database repository
5. Create services:
   - matcher = Matcher(kalshi_client, polymarket_client)
   - scorer = Scorer(config.constants)
   - validator = Validator(repository)
   - executor = Executor(kalshi_client, polymarket_client)
   - tracker = Tracker(repository)
   - alerter = Alerter(config.notification_settings)
6. Choose strategy (simple_arb or hedged_arb)
7. Start main loop:
   - Fetch markets
   - Find matches
   - Score opportunities
   - Validate best opportunity
   - Execute if valid
   - Monitor positions
   - Repeat
```

**Why here?**: Single entry point. Everything gets initialized and connected here. Easy to understand entire flow.

---

## Data Flow Example

```
User runs: python src/main.py

main.py:
  ↓ initializes all services
  
LOOP:
  exchanges/kalshi/client.py fetches markets
  exchanges/polymarket/client.py fetches markets
    ↓ both return raw API responses
  
  exchanges/*/parser.py converts to models/market.py objects
    ↓ normalized market objects
  
  services/matching/matcher.py finds equivalent markets
    ↓ matched pairs
  
  services/matching/scorer.py calculates profitability
    ↓ ranked opportunities (models/opportunity.py)
  
  services/execution/validator.py checks if tradeable
    ↓ validation result
  
  IF VALID:
    services/execution/executor.py places orders
      ↓ creates models/order.py objects
    
    database/repository.py saves orders and positions
  
  services/monitoring/tracker.py monitors positions
    ↓ calculates P&L
  
  services/monitoring/alerter.py sends notifications
  
  utils/logger.py logs everything
```

---

## Key Insights

1. **Models** = "What data looks like"
2. **Services** = "What we do with the data"
3. **Strategies** = "How we decide what to do"
4. **Database** = "Where we remember things"
5. **Config** = "What we can change easily"
6. **Utils** = "Code we use everywhere"
7. **Main** = "Putting it all together"

Each module has ONE job. Easy to test, modify, and extend.
