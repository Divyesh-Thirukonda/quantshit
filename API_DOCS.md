# Trading Bot REST API Documentation

## Base URL
- **Local Development**: `http://localhost:8000`
- **Vercel Deployment**: `https://your-deployment.vercel.app`

## Interactive Documentation
- **Swagger UI**: `/docs`
- **ReDoc**: `/redoc`

---

## Core Endpoints

### 🏠 General

#### `GET /`
Basic API information
```json
{
  "message": "Prediction Market Trading Bot API",
  "version": "2.0.0",
  "docs": "/docs"
}
```

#### `GET /health`
Health check with system status
```json
{
  "status": "healthy",
  "timestamp": "2025-10-13T19:52:12",
  "strategies": ["arbitrage", "expiry"],
  "platforms": ["polymarket", "manifold"]
}
```

---

### 🎯 Strategy Management

#### `POST /strategy/run`
Manually trigger a strategy cycle
```json
{
  "success": true,
  "message": "Strategy cycle completed"
}
```

#### `GET /strategy/opportunities`
Get current trading opportunities without executing
```json
{
  "success": true,
  "opportunities": [
    {
      "type": "arbitrage",
      "outcome": "YES",
      "buy_market": {...},
      "sell_market": {...},
      "expected_profit": 0.04,
      "strategy": "arbitrage"
    }
  ],
  "total_count": 5
}
```

---

### 📊 Market Data

#### `GET /markets`
Get current market data from all platforms
```json
{
  "success": true,
  "data": {
    "polymarket": [...],
    "manifold": [...]
  },
  "summary": {
    "total_markets": 45,
    "by_platform": {
      "polymarket": 25,
      "manifold": 20
    }
  }
}
```

---

### 💼 Position Tracking

#### `GET /positions`
Get all open trading positions
```json
{
  "success": true,
  "positions": [
    {
      "id": "polymarket_trump_2024_YES",
      "market_id": "trump_2024",
      "market_title": "Will Trump win 2024 election?",
      "platform": "polymarket",
      "outcome": "YES",
      "shares": 100,
      "entry_price": 0.52,
      "current_price": 0.54,
      "entry_time": "2025-10-13T15:30:00",
      "strategy": "arbitrage",
      "unrealized_pnl": 2.0
    }
  ],
  "count": 3
}
```

#### `GET /positions/summary`
Portfolio summary with P&L statistics
```json
{
  "success": true,
  "summary": {
    "total_positions": 3,
    "total_trades": 12,
    "total_unrealized_pnl": 15.50,
    "total_realized_pnl": 8.25,
    "total_pnl": 23.75,
    "strategy_breakdown": {
      "arbitrage": {
        "trades": 8,
        "total_pnl": 12.50
      },
      "expiry": {
        "trades": 4,
        "total_pnl": -4.25
      }
    },
    "platform_breakdown": {
      "polymarket": {
        "positions": 2,
        "total_unrealized_pnl": 10.25
      },
      "manifold": {
        "positions": 1,
        "total_unrealized_pnl": 5.25
      }
    },
    "last_updated": "2025-10-13T19:52:12"
  }
}
```

---

### 📈 Trade History

#### `GET /trades`
Get trade history with optional filters

**Query Parameters:**
- `limit` (optional): Maximum trades to return
- `strategy` (optional): Filter by strategy name
- `platform` (optional): Filter by platform

```json
{
  "success": true,
  "trades": [
    {
      "id": "abc123",
      "market_id": "trump_2024",
      "market_title": "Will Trump win 2024 election?",
      "platform": "polymarket",
      "action": "BUY",
      "outcome": "YES",
      "shares": 100,
      "price": 0.52,
      "timestamp": "2025-10-13T15:30:00",
      "strategy": "arbitrage",
      "order_id": "poly_buy_12345",
      "realized_pnl": 0.0,
      "fees": 0.0
    }
  ],
  "count": 15,
  "filters": {
    "limit": 50,
    "strategy": null,
    "platform": null
  }
}
```

---

### 🔄 Price Updates

#### `POST /positions/update-prices`
Update current market prices for all positions
```json
{
  "success": true,
  "message": "Updated prices for 25 markets"
}
```

---

## Usage Examples

### Python Client Example
```python
import requests

# Get API status
response = requests.get("http://localhost:8000/health")
print(response.json())

# Trigger strategy run
response = requests.post("http://localhost:8000/strategy/run")
print(response.json())

# Get current positions
response = requests.get("http://localhost:8000/positions")
positions = response.json()['positions']

for pos in positions:
    print(f"{pos['platform']}: {pos['shares']} {pos['outcome']} @ ${pos['current_price']:.3f}")

# Get trade history for arbitrage strategy
response = requests.get("http://localhost:8000/trades?strategy=arbitrage&limit=10")
trades = response.json()['trades']

for trade in trades:
    print(f"{trade['action']} {trade['shares']} {trade['outcome']} @ ${trade['price']:.3f}")
```

### JavaScript/Node.js Example
```javascript
// Get portfolio summary
const response = await fetch('http://localhost:8000/positions/summary');
const data = await response.json();

console.log(`Total P&L: $${data.summary.total_pnl}`);
console.log(`Open Positions: ${data.summary.total_positions}`);

// Get current opportunities
const oppResponse = await fetch('http://localhost:8000/strategy/opportunities');
const opportunities = await oppResponse.json();

opportunities.opportunities.forEach(opp => {
    console.log(`${opp.strategy}: $${opp.expected_profit} profit`);
});
```

### cURL Examples
```bash
# Check API health
curl http://localhost:8000/health

# Get all positions
curl http://localhost:8000/positions

# Get recent trades
curl "http://localhost:8000/trades?limit=5"

# Trigger strategy run
curl -X POST http://localhost:8000/strategy/run

# Update position prices
curl -X POST http://localhost:8000/positions/update-prices
```

---

## Error Responses

All endpoints return errors in this format:
```json
{
  "success": false,
  "error": "Error description here"
}
```

Common HTTP status codes:
- `200`: Success
- `500`: Internal server error
- `400`: Bad request (invalid parameters)

---

## Data Persistence

- Position and trade data is stored in `positions_data.json`
- Data persists across bot restarts
- Automatic backups recommended for production use

## Rate Limiting

- No rate limiting currently implemented
- Consider adding rate limiting for production deployments

## Authentication

- Currently no authentication required
- Consider adding API keys for production use