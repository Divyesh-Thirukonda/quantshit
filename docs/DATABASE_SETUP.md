# Database Setup - Quick Start

## What You Get

A complete database system that:
- ✅ Fetches all open markets from Kalshi and Polymarket
- ✅ Stores them in a SQLite database
- ✅ Finds matching markets between exchanges
- ✅ Identifies arbitrage opportunities
- ✅ Provides tools to query and analyze data

## Quick Start

### 1. Run Your First Scan

```bash
python -m src.scanner
```

This will:
- Fetch markets from both exchanges
- Store them in `quantshit.db`
- Find matches
- Identify opportunities
- Show results

### 2. View the Data

```bash
# Show statistics
python scripts/db_query.py stats

# Show top markets
python scripts/db_query.py markets

# Show opportunities
python scripts/db_query.py opportunities
```

### 3. Query with SQL

```bash
sqlite3 quantshit.db

# Count markets
SELECT exchange, COUNT(*) FROM markets GROUP BY exchange;

# Show high-volume markets
SELECT title, volume FROM markets WHERE volume > 1000 ORDER BY volume DESC LIMIT 10;

# Show best opportunities
SELECT outcome, expected_profit_pct FROM opportunities ORDER BY expected_profit_pct DESC;
```

## Use in Your Code

```python
from src.scanner import MarketScanner

# Initialize
scanner = MarketScanner(db_path='quantshit.db')

# Fetch and store everything
result = scanner.run_full_scan(min_volume=1000)

# Get best opportunities
opportunities = scanner.get_best_opportunities(limit=5)

for opp in opportunities:
    print(f"{opp['expected_profit_pct']:.2%} profit")
    print(f"Buy {opp['buy_exchange']} @ ${opp['buy_price']}")
    print(f"Sell {opp['sell_exchange']} @ ${opp['sell_price']}")
```

## Run on Schedule

### Cron (every 30 minutes)
```bash
*/30 * * * * cd /path/to/quantshit && python -m src.scanner
```

### Python Scheduler
```python
import schedule
from src.scanner import MarketScanner

scanner = MarketScanner()
schedule.every(30).minutes.do(lambda: scanner.run_full_scan())

while True:
    schedule.run_pending()
    time.sleep(60)
```

## Database Schema

**markets** - All markets from both exchanges
```
id, exchange, title, yes_price, no_price, volume, liquidity, status
```

**market_matches** - Equivalent markets
```
kalshi_market_id, polymarket_market_id, confidence_score
```

**opportunities** - Arbitrage setups
```
outcome, expected_profit, expected_profit_pct, buy_exchange, sell_exchange
```

## File Locations

- **Database**: `quantshit.db` (auto-created)
- **Scanner**: `src/scanner.py`
- **Query Tool**: `scripts/db_query.py`
- **Docs**: `docs/DATABASE_SYSTEM.md`

## Common Commands

```bash
# Full scan with custom min volume
python -m src.scanner 500

# Show database stats
python scripts/db_query.py stats

# Show top 10 markets from Kalshi
python scripts/db_query.py markets kalshi 10

# Show top 20 opportunities
python scripts/db_query.py opportunities 20

# Show market matches
python scripts/db_query.py matches

# Clean up old data (7+ days)
python -c "from src.scanner import MarketScanner; MarketScanner().clear_old_data(7)"
```

## Complete Documentation

See `docs/DATABASE_SYSTEM.md` for:
- Detailed architecture
- Full API reference
- Advanced queries
- Integration examples
- Performance tuning
- Troubleshooting

## What's in the Database Now?

After the test scan:
- **300 markets** (200 Kalshi + 100 Polymarket)
- **0 matches** (markets cover different topics)
- **0 opportunities** (no price differences found yet)

Run more scans to populate with current data!
