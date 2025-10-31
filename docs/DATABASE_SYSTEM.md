# Database System Documentation

**Status**: ✅ Fully Functional
**Date**: October 31, 2025

## Overview

The quantshit arbitrage engine now includes a complete database system that:
- Fetches and stores markets from Kalshi and Polymarket
- Performs matching between equivalent markets
- Identifies and stores arbitrage opportunities
- Provides query tools for analysis

## Architecture

```
┌─────────────────────────────────────────────────────────┐
│                    Market Scanner                       │
│  Orchestrates: Fetch → Match → Score → Store           │
└──────────┬──────────────────────────────────────────────┘
           │
           ├──> Exchange Clients (Kalshi, Polymarket)
           │
           ├──> Matcher (finds equivalent markets)
           │
           ├──> Scorer (identifies profitable opportunities)
           │
           └──> SQLite Database
                  │
                  ├── markets (all markets from both exchanges)
                  ├── market_matches (pairs of equivalent markets)
                  ├── opportunities (profitable arbitrage setups)
                  ├── orders (executed trades)
                  └── positions (open positions)
```

## Database Schema

### Tables

**1. markets** - All markets from both exchanges
```sql
CREATE TABLE markets (
    id TEXT PRIMARY KEY,           -- Market ID
    exchange TEXT NOT NULL,         -- 'kalshi' or 'polymarket'
    title TEXT NOT NULL,            -- Market question
    yes_price REAL NOT NULL,        -- YES price (0.0-1.0)
    no_price REAL NOT NULL,         -- NO price (0.0-1.0)
    volume REAL DEFAULT 0.0,        -- Dollar volume
    liquidity REAL DEFAULT 0.0,     -- Available liquidity
    status TEXT NOT NULL,           -- 'open', 'closed', 'settled'
    category TEXT,                  -- Market category
    expiry TIMESTAMP,               -- When market closes
    created_at TIMESTAMP NOT NULL,  -- First seen
    updated_at TIMESTAMP NOT NULL   -- Last updated
);
```

**2. market_matches** - Pairs of equivalent markets
```sql
CREATE TABLE market_matches (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    kalshi_market_id TEXT NOT NULL,
    polymarket_market_id TEXT NOT NULL,
    confidence_score REAL NOT NULL,    -- Similarity 0.0-1.0
    kalshi_title TEXT NOT NULL,
    polymarket_title TEXT NOT NULL,
    created_at TIMESTAMP NOT NULL,
    UNIQUE(kalshi_market_id, polymarket_market_id)
);
```

**3. opportunities** - Profitable arbitrage setups
```sql
CREATE TABLE opportunities (
    id TEXT PRIMARY KEY,
    kalshi_market_id TEXT NOT NULL,
    polymarket_market_id TEXT NOT NULL,
    outcome TEXT NOT NULL,             -- 'YES' or 'NO'
    spread REAL NOT NULL,              -- Price difference
    expected_profit REAL NOT NULL,     -- Dollar profit
    expected_profit_pct REAL NOT NULL, -- Percentage profit
    confidence_score REAL NOT NULL,    -- Match confidence
    recommended_size INTEGER NOT NULL, -- Suggested contracts
    max_size INTEGER NOT NULL,         -- Max contracts
    timestamp TIMESTAMP NOT NULL,
    expiry TIMESTAMP,
    buy_exchange TEXT,                 -- Where to buy
    sell_exchange TEXT,                -- Where to sell
    buy_price REAL,
    sell_price REAL
);
```

## Usage

### 1. Run a Market Scan

**Basic scan (uses default min_volume from strategy config)**:
```bash
python -m src.scanner
```

**Scan with custom min_volume**:
```bash
python -m src.scanner 500  # $500 minimum volume
```

**Programmatic usage**:
```python
from src.scanner import MarketScanner

# Initialize scanner
scanner = MarketScanner(db_path='quantshit.db')

# Run full scan
result = scanner.run_full_scan(min_volume=1000)

print(f"Markets: {result['markets_fetched']['total']}")
print(f"Matches: {result['matches_found']}")
print(f"Opportunities: {result['opportunities_found']}")

# Get best opportunities
best_opps = scanner.get_best_opportunities(limit=5)
for opp in best_opps:
    print(f"{opp['expected_profit_pct']:.2%} profit")
```

### 2. Query the Database

**Show statistics**:
```bash
python scripts/db_query.py stats
```

**Show top markets**:
```bash
python scripts/db_query.py markets           # All exchanges
python scripts/db_query.py markets kalshi    # Kalshi only
python scripts/db_query.py markets polymarket 15  # Top 15 from Polymarket
```

**Show opportunities**:
```bash
python scripts/db_query.py opportunities
python scripts/db_query.py opportunities 20  # Top 20
```

**Show market matches**:
```bash
python scripts/db_query.py matches
```

**Show recent activity**:
```bash
python scripts/db_query.py recent
```

### 3. Direct SQL Queries

```bash
# Connect to database
sqlite3 quantshit.db

# Count markets
SELECT exchange, COUNT(*) FROM markets GROUP BY exchange;

# Top opportunities
SELECT outcome, expected_profit_pct, confidence_score
FROM opportunities
ORDER BY expected_profit_pct DESC
LIMIT 10;

# Markets with volume > $1000
SELECT id, title, volume
FROM markets
WHERE volume > 1000
ORDER BY volume DESC;

# High confidence matches
SELECT kalshi_title, polymarket_title, confidence_score
FROM market_matches
WHERE confidence_score > 0.7
ORDER BY confidence_score DESC;
```

## Integration with Bot

The scanner can be integrated into the existing `ArbitrageBot`:

```python
from src.main import ArbitrageBot
from src.scanner import MarketScanner
from src.database import SQLiteRepository

# Initialize with database
bot = ArbitrageBot()
scanner = MarketScanner(db_path='quantshit.db')

# Run scan first
scanner.run_full_scan()

# Then bot can query database instead of fetching fresh data
db = SQLiteRepository('quantshit.db')
best_opps = db.get_opportunities(limit=10, min_profit=50.0)
```

## Automated Scanning

### Cron Job Setup

**Every hour**:
```bash
0 * * * * cd /path/to/quantshit && python -m src.scanner >> logs/scanner.log 2>&1
```

**Every 15 minutes**:
```bash
*/15 * * * * cd /path/to/quantshit && python -m src.scanner >> logs/scanner.log 2>&1
```

### Python Scheduler

```python
import schedule
import time
from src.scanner import MarketScanner

scanner = MarketScanner()

def scan_job():
    print("Running scheduled scan...")
    scanner.run_full_scan()

# Run every 30 minutes
schedule.every(30).minutes.do(scan_job)

while True:
    schedule.run_pending()
    time.sleep(60)
```

## Performance

**Current Performance** (with default settings):
- Fetch markets: ~1 second
- Match markets: <1 second
- Score opportunities: <1 second
- Total scan time: ~2-3 seconds
- Database size: ~50KB per 100 markets

**Optimization Tips**:
1. Use batch inserts (already implemented)
2. Index frequently queried columns (already implemented)
3. Clear old data regularly: `scanner.clear_old_data(days=7)`
4. Use PRAGMA for faster writes:
   ```sql
   PRAGMA synchronous = OFF;
   PRAGMA journal_mode = WAL;
   ```

## Data Retention

**Clear old opportunities** (keeps database small):
```python
from src.scanner import MarketScanner

scanner = MarketScanner()
scanner.clear_old_data(days=7)  # Remove data older than 7 days
```

**Backup database**:
```bash
# Simple copy
cp quantshit.db quantshit_backup_$(date +%Y%m%d).db

# SQLite dump
sqlite3 quantshit.db .dump > quantshit_backup.sql
```

## Example Workflow

**Daily arbitrage hunting workflow**:

```python
from src.scanner import MarketScanner
from src.database import SQLiteRepository

# 1. Initialize
scanner = MarketScanner(db_path='quantshit.db')
db = SQLiteRepository('quantshit.db')

# 2. Fetch fresh market data
print("Fetching markets...")
scanner.run_full_scan(min_volume=500)

# 3. Get best opportunities
print("\nTop opportunities:")
opps = scanner.get_best_opportunities(limit=10)

for i, opp in enumerate(opps, 1):
    print(f"\n{i}. {opp['outcome']} - {opp['expected_profit_pct']:.2%}")
    print(f"   Buy on {opp['buy_exchange']} @ ${opp['buy_price']:.3f}")
    print(f"   Sell on {opp['sell_exchange']} @ ${opp['sell_price']:.3f}")
    print(f"   Expected profit: ${opp['expected_profit']:.2f}")
    print(f"   Confidence: {opp['confidence_score']:.2f}")

# 4. Get market stats
stats = db.get_stats()
print(f"\nDatabase: {stats}")

# 5. Clean up old data
scanner.clear_old_data(days=7)
```

## Troubleshooting

**No opportunities found?**
- Markets on different exchanges may not have equivalent pairs
- Try lowering `min_profit_pct` in strategy config
- Check if markets have significant price differences
- Run `scripts/db_query.py matches` to see if any matches exist

**Database locked error?**
- Close other connections to the database
- Use WAL mode: `PRAGMA journal_mode = WAL;`
- Only one write at a time is allowed

**Slow queries?**
- Indexes are already created for common queries
- Consider vacuuming: `sqlite3 quantshit.db "VACUUM;"`
- For very large databases, consider PostgreSQL

## Future Enhancements

1. **PostgreSQL support** - For production deployments
2. **WebSocket integration** - Real-time market updates
3. **Historical analysis** - Track opportunity trends over time
4. **Backtesting** - Test strategies on historical data
5. **Alert system** - Notify when high-profit opportunities appear
6. **API endpoints** - REST API to query database

## Files

- `src/scanner.py` - Main market scanner module
- `src/database/sqlite_repository.py` - SQLite database operations
- `src/database/schema.py` - Database schema definitions
- `scripts/db_query.py` - Command-line query tool
- `quantshit.db` - SQLite database file (created on first run)

## See Also

- `CLAUDE.md` - Project overview and architecture
- `docs/KALSHI_FIX.md` - Kalshi integration details
- `docs/STRATEGY_CONFIG_REFACTOR.md` - Strategy configuration system
