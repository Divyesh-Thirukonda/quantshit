# Prediction Market Arbitrage System

A systematic approach to identifying and executing arbitrage opportunities across prediction markets (Kalshi, Polymarket).

## Architecture

- **Backend**: Python FastAPI (deployable to Vercel)
- **Database**: Supabase PostgreSQL
- **Frontend**: Next.js (React + TypeScript)
- **Deployment**: Vercel
- **Data Sources**: Kalshi API, Polymarket API

## Project Structure

```
/
├── api/                    # FastAPI backend
│   ├── main.py            # FastAPI app entry point
│   ├── routes/            # API route handlers
│   ├── services/          # Business logic
│   ├── models/            # Data models
│   └── utils/             # Utilities
├── frontend/              # Next.js frontend
├── shared/                # Shared types and utilities
├── tests/                 # Test suite
└── requirements.txt       # Python dependencies
```

## Development Phases

1. **Phase 1**: Basic API structure + database connection
2. **Phase 2**: Data acquisition from Kalshi/Polymarket
3. **Phase 3**: Arbitrage detection logic
4. **Phase 4**: Basic dashboard
5. **Phase 5**: Trading execution (paper trading first)
6. **Phase 6**: Portfolio management

## Quick Start

```bash
# Install dependencies
pip install -r requirements.txt

# Run development server
uvicorn api.main:app --reload

# Frontend (separate terminal)
cd frontend && npm run dev
```