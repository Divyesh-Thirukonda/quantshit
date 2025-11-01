# Quantshit - Prediction Market Arbitrage System

🚀 **Deploy to Vercel + Supabase in 3 minutes** ⚡

## Quick Deploy (Free & Easy)

**Prerequisites:**
- [Node.js](https://nodejs.org/) (for Vercel CLI)
- GitHub account (free)

**Deploy Now:**
```powershell
# 1. Run the deploy helper
.\vercel-deploy.ps1

# 2. Deploy to Vercel
vercel
```

**Or follow the full guide:** `VERCEL_DEPLOY.md`

---

## What This Builds

A **production-ready prediction market arbitrage system** that:

## Development Phases

### Phase 1: Foundation & Types ✅ (Current)
- Core data types and enums
- Basic project structure
- Configuration management
- Simple test suite

### Phase 2: Data Acquisition (Next)
- Kalshi API integration
- Polymarket API integration
- Data models and storage
- Basic market data fetching

### Phase 3: Arbitrage Detection
- Market matching algorithms
- Spread calculation
- Opportunity detection
- Paper trading simulation

### Phase 4: Execution Engine
- Order placement system
- Position management
- Risk management basics

### Phase 5: Dashboard & Monitoring
- Web interface
- Real-time monitoring
- Authentication

## Project Structure

```
quantshit/
├── src/
│   ├── core/           # Core types and enums
│   ├── data/           # Data acquisition modules
│   ├── strategies/     # Trading strategies
│   ├── execution/      # Order execution
│   └── dashboard/      # Web interface
├── tests/              # Test suite
├── config/             # Configuration files
└── docs/               # Documentation
```

## Installation

```bash
pip install -r requirements.txt
```

## Testing

```bash
pytest tests/
```

## Deployment

Each phase is designed to be deployable and testable independently.