# Demo Mode Summary

## What Was Created

A complete demo environment for testing the arbitrage bot without real API keys or live market data.

### Files Created

```
demo/
├── polymarket_markets.json      # 5 fake Polymarket markets
├── kalshi_markets.json          # 6 fake Kalshi markets
├── .env.demo                    # Demo configuration
├── demo_runner.py               # Python script to run demo
├── run_demo.sh                  # Shell script (Linux/Mac)
├── run_demo.bat                 # Batch script (Windows)
├── README.md                    # Documentation
└── DEMO_SUMMARY.md              # This file
```

## How to Run

### Quick Start Commands

**Linux/Mac:**
```bash
./demo/run_demo.sh
```

**Windows:**
```bash
demo\run_demo.bat
```

**Direct Python:**
```bash
python demo/demo_runner.py
```

## What the Demo Shows

The demo successfully:

1. **Loads Fake Data** - Reads market data from JSON files for Polymarket and Kalshi
2. **Displays Markets** - Shows all 11 markets with prices and volumes
3. **Finds Arbitrage** - Discovers 2 arbitrage opportunities in the demo data
4. **Calculates Profit** - Shows expected profit per share and total profit

### Example Output

```
ARBITRAGE OPPORTUNITIES FOUND
================================================================================

Opportunity #1:
  ID: 66ccf322-e98e-4da8-91ef-7c3e568519e6
  Outcome: NO
  Buy Market: Donald Trump to win 2024 Presidential Election (kalshi)
  Sell Market: Will Donald Trump win the 2024 US Presidential Election? (polymarket)
  Buy Price: $0.4200
  Sell Price: $0.4800
  Spread: 6.00%
  Expected Profit/Share: $0.0600
  Max Quantity: 100
  Confidence Score: 1.00
  Risk Level: medium

Total opportunities found: 2
Total expected profit: $12.00
```

## Demo Data Design

The fake markets are intentionally designed with price discrepancies:

### Trump Election Market
- **Polymarket**: YES $0.52 / NO $0.48
- **Kalshi**: YES $0.58 / NO $0.42
- **Spread**: 6% (above the 5% MIN_SPREAD threshold)
- **Creates**: 2 arbitrage opportunities (YES and NO sides)

### Bitcoin $100k Market
- **Polymarket**: YES $0.35 / NO $0.65
- **Kalshi**: YES $0.29 / NO $0.71
- **Spread**: 6% on YES side only

### Fed Rate Cuts
- **Polymarket**: YES $0.72 / NO $0.28
- **Kalshi**: YES $0.75 / NO $0.25
- **Spread**: 3% (below threshold)

### Tesla $300
- **Polymarket**: YES $0.41 / NO $0.59
- **Kalshi**: YES $0.38 / NO $0.62
- **Spread**: 3% (below threshold)

### Unemployment < 4%
- **Polymarket**: YES $0.68 / NO $0.32
- **Kalshi**: YES $0.64 / NO $0.36
- **Spread**: 4% (below threshold)

## Key Features Demonstrated

1. **Market Matching** - Shows how the bot matches similar markets across platforms using title similarity
2. **Spread Calculation** - Demonstrates profit calculation from price differences
3. **Filtering** - Shows MIN_SPREAD and MIN_VOLUME filtering in action
4. **Type Safety** - Uses the new typed architecture (ArbitrageOpportunity dataclass)
5. **Risk Assessment** - Displays confidence scores and risk levels

## Customization

Edit `demo/.env.demo` to experiment:

```bash
MIN_VOLUME=500000      # Lower to find more opportunities
MIN_SPREAD=0.03        # Lower to 3% to see more matches
```

## Next Steps

After testing with demo data:

1. Get real API keys for Polymarket and Kalshi
2. Configure them in `.env` file (not `.env.demo`)
3. Run with real data: `python main.py --once`
4. Deploy to Vercel for continuous operation

## Technical Notes

- Demo uses the same `ArbitrageStrategy` class as production
- Market data structure matches the `Market` type in `src/types.py`
- No API calls are made in demo mode
- Results are deterministic and reproducible
