# Kalshi API Integration Fix

**Date**: October 31, 2025
**Status**: ✅ Fixed and tested

## Problem

The Kalshi client was returning 0 markets despite having working code structure. The bot couldn't fetch any market data from Kalshi.

## Root Cause Analysis

After investigating the Kalshi API, I found several issues:

### 1. Wrong API Approach
**Problem**: The client was fetching `/events` endpoint, which only returns basic event information without market data.

```python
# OLD - Wrong approach
url = f"{self.BASE_URL}/events"
# Returns: event metadata only, no market prices/volume
```

**Solution**: Use `/markets` endpoint directly to get full market data.

```python
# NEW - Correct approach
url = f"{self.BASE_URL}/markets"
# Returns: complete market data with prices, volume, etc.
```

### 2. Incorrect Response Structure
**Problem**: Parser expected nested `event_data` and `market_data` objects.

```python
# OLD - Expected nested structure
def parse_market(event_data: Dict, market_data: Dict) -> Market:
    markets = event_data.get('markets', [])  # This field doesn't exist!
```

**Solution**: Markets endpoint returns flat market objects directly.

```python
# NEW - Direct market parsing
def parse_market(market_data: Dict) -> Market:
    # Parse directly from market object
```

### 3. Incorrect Price Field Names
**Problem**: Parser used `yes_bid` and `no_bid` only.

**Reality**: Kalshi returns both bid and ask prices:
- `yes_bid` / `yes_ask`
- `no_bid` / `no_ask`

**Solution**: Use mid-price between bid and ask for more accurate pricing.

```python
# NEW - Use mid-price
yes_price = ((yes_bid + yes_ask) / 2.0) / 100.0
no_price = ((no_bid + no_ask) / 2.0) / 100.0
```

### 4. Incorrect Volume Calculation
**Problem**: Treated volume as dollars directly.

**Reality**: Volume is in contracts, needs conversion:
- `volume` = number of contracts traded
- `notional_value` = value per contract (usually 100 cents = $1)
- Dollar volume = `volume * notional_value / 100`

**Solution**: Convert contracts to dollars.

```python
# NEW - Correct conversion
volume_contracts = market_data.get('volume', 0)
notional_value = market_data.get('notional_value', 100)
volume = (volume_contracts * notional_value) / 100.0
```

## API Response Structure

### Kalshi `/markets` Endpoint

**Request**:
```bash
GET https://api.elections.kalshi.com/trade-api/v2/markets?status=open&limit=200
```

**Response**:
```json
{
  "cursor": "...",
  "markets": [
    {
      "ticker": "KXELONMARS-99",
      "title": "Will Elon Musk visit Mars before Aug 1, 2099?",
      "status": "active",
      "yes_bid": 7,
      "yes_ask": 9,
      "no_bid": 91,
      "no_ask": 93,
      "volume": 14738,
      "liquidity": 3537295,
      "liquidity_dollars": "35372.95",
      "open_interest": 13066,
      "notional_value": 100,
      "close_time": "2099-08-01T04:59:00Z",
      "category": "World",
      ...
    }
  ]
}
```

**Key Fields**:
- Prices are in cents (0-100), convert to 0.0-1.0
- Volume is in contracts, multiply by notional_value/100 for dollars
- Liquidity is available in `liquidity_dollars` field directly
- Status is "active", "closed", or "settled"

## Changes Made

### Modified Files

**1. `src/exchanges/kalshi/client.py`**
```python
# Before
url = f"{self.BASE_URL}/events"
for event_data in events:
    market = self._fetch_market_details(event_data)

# After
url = f"{self.BASE_URL}/markets"
for market_data in market_list:
    market = parse_market(market_data)
```

**2. `src/exchanges/kalshi/parser.py`**
```python
# Before
def parse_market(event_data: Dict, market_data: Dict) -> Market:
    yes_price = market_data.get('yes_bid', 50) / 100.0
    volume = market_data.get('volume', 0.0)

# After
def parse_market(market_data: Dict) -> Market:
    # Use mid-price between bid/ask
    yes_price = ((yes_bid + yes_ask) / 2.0) / 100.0
    # Convert contracts to dollars
    volume = (volume_contracts * notional_value) / 100.0
```

## Testing Results

### Before Fix
```
Kalshi markets: 0
Polymarket markets: 100
```

### After Fix
```
✓ Kalshi markets: 2 (with min_volume=1000)
✓ Kalshi markets: 200 (with min_volume=0)
✓ Polymarket markets: 100

Sample Kalshi market:
  Title: yes New England,yes Cincinnati,yes Denver...
  YES: $0.500 | NO: $0.500
  Volume: $1,162
  ID: KXMVENFLMULTIGAMEEXTENDED-S20251177785052D
```

### End-to-End Test
```python
bot = ArbitrageBot()
kalshi_markets, polymarket_markets = bot._fetch_markets()

# ✓ Successfully fetches from both exchanges
# ✓ Markets are properly parsed
# ✓ Prices are in correct 0.0-1.0 range
# ✓ Volume is in dollars
# ✓ Integration works correctly
```

## Market Types Available

Current Kalshi markets are primarily:
- **NFL multi-game parlays** - Combined outcomes across multiple games
- **Long-term prediction markets** - Events years in the future
- **Political events** - Elections, appointments, etc.

Most have very low volume currently, which is why `min_volume=1000` only returns 2 markets.

## API Endpoint Verified

The correct Kalshi API endpoint is:
```
https://api.elections.kalshi.com/trade-api/v2
```

Note: The general trading API was moved to the elections subdomain. The documentation suggests using this endpoint for all market data.

## Next Steps

### Completed ✅
- [x] Fix API endpoint usage
- [x] Update parser for correct response structure
- [x] Fix price calculations
- [x] Fix volume calculations
- [x] Test end-to-end integration

### Recommended Future Improvements

1. **Pagination Support**
   - API returns max 200 markets per request
   - Use `cursor` field to fetch additional pages
   - Implement if more than 200 markets needed

2. **Market Filtering**
   - Add category filtering (e.g., only sports, only politics)
   - Filter by expiry date (e.g., closing within 30 days)
   - Filter by liquidity (not just volume)

3. **Better Price Handling**
   - Consider using bid price for buys, ask price for sells
   - Calculate actual executable price based on order book depth
   - Factor in spread costs

4. **Rate Limiting**
   - API may have rate limits
   - Implement exponential backoff on errors
   - Add request throttling if needed

5. **Authentication**
   - Test with real API key for authenticated endpoints
   - Some markets may require authentication
   - Order placement definitely requires auth

6. **WebSocket Support**
   - Kalshi offers WebSocket for real-time data
   - Could reduce API calls and get faster updates
   - Implement for live trading

## Documentation

- Kalshi API Docs: https://docs.kalshi.com
- Trading API v2: https://api.elections.kalshi.com/trade-api/v2
- Market data endpoint: `/markets`
- Event data endpoint: `/events`

## Summary

The Kalshi integration is now **fully functional**. The bot can:
- ✅ Fetch markets from Kalshi
- ✅ Parse market data correctly
- ✅ Convert prices to standard format
- ✅ Calculate volume in dollars
- ✅ Integrate with ArbitrageBot
- ✅ Work alongside Polymarket

The fix enables the arbitrage engine to find opportunities across both Kalshi and Polymarket! 🎉
