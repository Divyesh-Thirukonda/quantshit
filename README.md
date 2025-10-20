# Quantshit Arbitrage Engine

**API-only** cross-venue prediction market arbitrage detection and execution engine.

## Quick Start

```bash
# Install dependencies
pip install -r requirements.txt

# Set up environment
cp .env.example .env
# Add your API keys to .env

# Start the API server
python -m uvicorn api:app --host 0.0.0.0 --port 8000
```

API will be available at `http://localhost:8000`

## API Endpoints

### GET /
- **Description**: API information and usage examples
- **Returns**: Service info and endpoint documentation

### GET /health
- **Description**: Health check
- **Returns**: `{"status": "healthy"}`

### GET /scan
- **Description**: Scan for arbitrage opportunities
- **Parameters**: 
  - `size` (int, optional): Trade size in USD (default: 250)
  - `min_edge` (float, optional): Minimum edge threshold (default: 0.05 = 5%)
- **Returns**: List of arbitrage opportunities
- **Example**: `GET /scan?size=500&min_edge=0.02`

### POST /execute/{opportunity_id}
- **Description**: Execute an arbitrage trade
- **Parameters**: `opportunity_id` from scan results
- **Returns**: Execution result
- **Example**: `POST /execute/arb_123`

### GET /markets
- **Description**: Get current market data from all platforms
- **Returns**: Raw market data by platform

## Response Format

### Scan Response
```json
{
  "success": true,
  "opportunities": [
    {
      "id": "arb_0",
      "question": "Trump Wins 2024 Presidential Election",
      "yes_venue": "polymarket",
      "no_venue": "manifold", 
      "yes_price": "$0.520",
      "no_price": "$0.465",
      "size": "$250",
      "edge_bps": "150",
      "cost": "$246.25",
      "profit": "$3.75"
    }
  ],
  "meta": {
    "scanned_markets": 42,
    "opportunities_found": 3,
    "timestamp": "2024-01-01T12:00:00Z",
    "parameters": {
      "size": 250,
      "min_edge": 0.05
    }
  }
}
```

## Usage Examples

### Python Client
```python
import requests

# Scan for opportunities
response = requests.get("http://localhost:8000/scan?size=1000&min_edge=0.03")
data = response.json()

for opp in data["opportunities"]:
    print(f"Edge: {opp['edge_bps']} bps - {opp['question']}")
    
    # Execute if profitable
    if int(opp['edge_bps']) > 100:
        exec_response = requests.post(f"http://localhost:8000/execute/{opp['id']}")
        print(f"Execution: {exec_response.json()}")
```

### JavaScript/Node.js Client
```javascript
// Scan for opportunities
const response = await fetch('http://localhost:8000/scan?size=500');
const data = await response.json();

for (const opp of data.opportunities) {
    console.log(`${opp.edge_bps} bps edge: ${opp.question}`);
    
    // Execute trade
    if (parseInt(opp.edge_bps) >= 80) {
        const execResponse = await fetch(`http://localhost:8000/execute/${opp.id}`, {
            method: 'POST'
        });
        const result = await execResponse.json();
        console.log('Execution result:', result);
    }
}
```

### cURL
```bash
# Scan for opportunities
curl "http://localhost:8000/scan?size=250&min_edge=0.02"

# Execute a trade
curl -X POST "http://localhost:8000/execute/arb_0"
```

## Environment Variables

```bash
# Required API Keys
POLYMARKET_API_KEY=your_polymarket_key
KALSHI_API_KEY=your_kalshi_key  
MANIFOLD_API_KEY=your_manifold_key

# Optional Configuration
MIN_VOLUME=1000        # Minimum market volume
MIN_SPREAD=0.05        # Minimum spread threshold
```

## Architecture

- **Pure Python API** - FastAPI with real market connections
- **Multi-platform** - Polymarket, Kalshi, Manifold Markets
- **Real execution** - Actual trade placement via platform APIs
- **Extensible** - Easy to add new platforms and strategies

## Adding New Platforms

1. Create new API connector in `platforms/newplatform.py`
2. Add to `platforms/__init__.py` registry
3. Add API key to `.env`

## Deployment

### Local Development
```bash
python -m uvicorn api:app --reload --port 8000
```

### Production
```bash
# Using gunicorn
gunicorn -w 4 -k uvicorn.workers.UvicornWorker api:app --bind 0.0.0.0:8000

# Using Docker
docker build -t quantshit-api .
docker run -p 8000:8000 quantshit-api
```

## License

MIT