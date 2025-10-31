# Visual Data Flow & Interactions

## Architecture Diagram

```
┌─────────────────────────────────────────────────────────────────┐
│                            main.py                              │
│                    (Orchestrator / Entry Point)                 │
└────────────┬────────────────────────────────────┬───────────────┘
             │                                    │
             ▼                                    ▼
    ┌────────────────┐                  ┌────────────────┐
    │   config/      │                  │   database/    │
    │                │                  │                │
    │ settings.py    │◄─────────────────┤ repository.py  │
    │ constants.py   │                  │ schema.py      │
    └────────────────┘                  └────────────────┘
             │                                    ▲
             │                                    │
             ▼                                    │
    ┌─────────────────────────────────────────────┼──────┐
    │              services/                      │      │
    │                                             │      │
    │  ┌──────────────┐     ┌──────────────┐     │      │
    │  │  matching/   │     │ execution/   │     │      │
    │  │  matcher.py  │────▶│ validator.py │─────┘      │
    │  │  scorer.py   │     │ executor.py  │            │
    │  └──────────────┘     └──────────────┘            │
    │         │                     │                    │
    │         │              ┌──────────────┐            │
    │         │              │ monitoring/  │            │
    │         │              │ tracker.py   │            │
    │         └─────────────▶│ alerter.py   │            │
    │                        └──────────────┘            │
    └────────┬──────────────────────┬────────────────────┘
             │                      │
             ▼                      ▼
    ┌────────────────┐     ┌────────────────┐
    │  exchanges/    │     │   strategies/  │
    │                │     │                │
    │  kalshi/       │     │  base.py       │
    │    client.py   │     │  simple_arb.py │
    │    parser.py   │     │  hedged_arb.py │
    │    types.py    │     │                │
    │                │     └────────────────┘
    │  polymarket/   │              │
    │    client.py   │              │
    │    parser.py   │◄─────────────┘
    │    types.py    │
    └────────────────┘
             │
             ▼
    ┌────────────────┐
    │   models/      │
    │                │
    │  market.py     │
    │  order.py      │
    │  position.py   │
    │  opportunity.py│
    └────────────────┘
             ▲
             │
    ┌────────┴────────┐
    │    types.py     │  (Universal Types)
    │    utils/       │
    │   logger.py     │
    │   math.py       │
    │   decorators.py │
    └─────────────────┘
```

## Request Flow: Finding & Executing an Arbitrage

```
┌──────────────────────────────────────────────────────────────────┐
│ 1. FETCH MARKETS                                                 │
└──────────────────────────────────────────────────────────────────┘

main.py
  │
  ├─→ exchanges/kalshi/client.py.get_markets()
  │     └─→ API Call → Raw JSON
  │           └─→ exchanges/kalshi/parser.py.parse_markets()
  │                 └─→ List[models/market.py] (Kalshi Markets)
  │
  └─→ exchanges/polymarket/client.py.get_markets()
        └─→ API Call → Raw JSON
              └─→ exchanges/polymarket/parser.py.parse_markets()
                    └─→ List[models/market.py] (Polymarket Markets)

┌──────────────────────────────────────────────────────────────────┐
│ 2. MATCH MARKETS                                                 │
└──────────────────────────────────────────────────────────────────┘

main.py passes both market lists to:
  │
  └─→ services/matching/matcher.py.find_matches()
        │
        │ Logic: Compare market titles/descriptions
        │ - Fuzzy string matching
        │ - Check if about same event
        │ - Filter by expiry date similarity
        │
        └─→ List[(kalshi_market, polymarket_market, confidence)]

┌──────────────────────────────────────────────────────────────────┐
│ 3. SCORE OPPORTUNITIES                                           │
└──────────────────────────────────────────────────────────────────┘

main.py passes matched pairs to:
  │
  └─→ services/matching/scorer.py.score_opportunities()
        │
        │ For each matched pair:
        │   1. Calculate spread = |price_A - price_B|
        │   2. Subtract fees (uses config/constants.py)
        │   3. Account for slippage (uses utils/math.py)
        │   4. Calculate profit % (uses utils/math.py)
        │   5. Create models/opportunity.py object
        │
        └─→ List[models/opportunity.py] (sorted by profit)

┌──────────────────────────────────────────────────────────────────┐
│ 4. SELECT STRATEGY                                               │
└──────────────────────────────────────────────────────────────────┘

main.py selects strategy based on config:
  │
  └─→ strategies/simple_arb.py.evaluate(opportunities)
        │
        │ Logic: Pick best opportunity over threshold
        │ - Filter by min profit (config/constants.py)
        │ - Calculate position size (Kelly criterion)
        │ - Return recommended trade
        │
        └─→ (opportunity, trade_size)

┌──────────────────────────────────────────────────────────────────┐
│ 5. VALIDATE TRADE                                                │
└──────────────────────────────────────────────────────────────────┘

main.py passes opportunity to:
  │
  └─→ services/execution/validator.py.validate()
        │
        │ Checks:
        │   ✓ Account balance sufficient?
        │   ✓ Markets still open?
        │   ✓ Prices haven't moved too much?
        │   ✓ Within risk limits?
        │   ✓ Not already in this position?
        │     (queries database/repository.py)
        │
        └─→ ValidationResult(valid=True/False, reason="...")

┌──────────────────────────────────────────────────────────────────┐
│ 6. EXECUTE TRADE                                                 │
└──────────────────────────────────────────────────────────────────┘

If valid, main.py calls:
  │
  └─→ services/execution/executor.py.execute()
        │
        │ Step 1: Place order on Kalshi
        │   └─→ exchanges/kalshi/client.py.place_order()
        │         └─→ API Call → Order confirmation
        │               └─→ exchanges/kalshi/parser.py.parse_order()
        │                     └─→ models/order.py (Order A)
        │
        │ Step 2: Place offsetting order on Polymarket
        │   └─→ exchanges/polymarket/client.py.place_order()
        │         └─→ API Call → Order confirmation
        │               └─→ exchanges/polymarket/parser.py.parse_order()
        │                     └─→ models/order.py (Order B)
        │
        │ Step 3: Save to database
        │   └─→ database/repository.py.save_orders([Order A, Order B])
        │   └─→ database/repository.py.create_position(...)
        │         └─→ models/position.py created and saved
        │
        └─→ ExecutionResult(success=True, orders=[...])

┌──────────────────────────────────────────────────────────────────┐
│ 7. MONITOR POSITION                                              │
└──────────────────────────────────────────────────────────────────┘

Background task running continuously:
  │
  └─→ services/monitoring/tracker.py.monitor_positions()
        │
        │ Loop:
        │   1. Get all positions from database/repository.py
        │   2. Fetch current prices from exchanges
        │   3. Calculate unrealized P&L (uses utils/math.py)
        │   4. Check if should close (uses strategy logic)
        │   5. Update position in database
        │   6. If threshold crossed:
        │      └─→ services/monitoring/alerter.py.send_alert()
        │            └─→ Sends notification (Telegram/Discord)
        │
        └─→ Repeats every N seconds

┌──────────────────────────────────────────────────────────────────┐
│ 8. LOGGING & OBSERVABILITY                                       │
└──────────────────────────────────────────────────────────────────┘

Throughout entire flow:
  │
  └─→ Every module uses utils/logger.py
        │
        ├─→ Logs opportunities found
        ├─→ Logs validation results
        ├─→ Logs executions (success/failure)
        ├─→ Logs P&L updates
        └─→ Logs errors (with stack traces)

All functions decorated with:
  @retry (utils/decorators.py) - retry on API failures
  @rate_limit (utils/decorators.py) - prevent rate limiting
  @log_execution_time (utils/decorators.py) - performance tracking
```

## Module Interaction Matrix

| Module      | Depends On                          | Used By                      |
|-------------|-------------------------------------|------------------------------|
| `types.py`  | Nothing (base types)                | Everything                   |
| `models/`   | `types.py`                          | All services, exchanges      |
| `utils/`    | `types.py`, `config/`               | Everything                   |
| `config/`   | Nothing                             | All services, main           |
| `exchanges/`| `models/`, `utils/`, `types.py`     | Services, main               |
| `services/` | `models/`, `exchanges/`, `database/`| Main, other services         |
| `strategies/`| `models/`, `utils/`, `config/`     | Main, services               |
| `database/` | `models/`, `config/`                | Services, main               |
| `main.py`   | Everything                          | Nothing (entry point)        |

## Dependency Rules

1. **Types** → Used by everyone, depends on no one
2. **Models** → Can import types, utils, config. NOT services or exchanges
3. **Utils** → Can import types, config. NOT services or models
4. **Exchanges** → Can import models, utils, types. NOT services
5. **Services** → Can import everything except main
6. **Main** → Imports everything, orchestrates

This prevents circular dependencies and keeps architecture clean!
