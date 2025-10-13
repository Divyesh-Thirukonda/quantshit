# Arbitrage Trading System

A comprehensive Python-based arbitrage trading system for prediction markets, starting with Kalshi integration. The system provides a modular architecture for developing, testing, and deploying trading strategies with built-in risk management and backtesting capabilities.

## Features

- **Multi-Platform Support**: Platform-agnostic design with Kalshi integration
- **Strategy Framework**: Modular system for developing custom trading strategies
- **Built-in Strategies**: Cross-platform arbitrage and correlation arbitrage
- **Risk Management**: Comprehensive risk controls and monitoring
- **Backtesting**: Historical strategy testing with performance metrics
- **Web Dashboard**: Real-time monitoring and control interface
- **Data Acquisition**: Automated market data collection and processing
- **Order Execution**: Robust order management and execution engine
- **Utility Modules**: Statistics and NLP analysis tools

## Quick Start

### 1. Setup
```bash
# Clone and setup the system
git clone <repository>
cd quantshit
python scripts/setup.py
```

### 2. Configuration
```bash
# Copy and edit environment variables
cp .env.example .env
# Edit .env with your API keys and settings
```

### 3. Run System
```bash
# Start the trading system
python main.py run

# Or launch the web dashboard
python main.py dashboard
```

### 4. Test with Backtesting
```bash
# Run a quick backtest
python scripts/quick_backtest.py
```

## Architecture

```
src/
├── core/          # Core system components
├── data/          # Data acquisition layer
├── platforms/     # Platform integrations (Kalshi, etc.)
├── strategies/    # Trading strategies
├── execution/     # Order execution engine
├── risk/          # Risk management
├── backtesting/   # Backtesting framework
├── modules/       # Utility modules (stats, NLP)
└── frontend/      # Web dashboard
```

## Included Strategies

### Cross-Platform Arbitrage
Finds the same betting market across different platforms and places bets to profit from price differences.

### Correlation Arbitrage
Identifies related markets with high correlation on the same platform and trades based on statistical arbitrage opportunities.

## Documentation

- [Developer Guide](docs/DEVELOPER.md) - Complete guide for adding strategies and platforms
- [API Documentation](docs/API.md) - REST API reference
- [Troubleshooting](docs/TROUBLESHOOTING.md) - Common issues and solutions

## Requirements

- Python 3.8+
- Redis (for caching)
- PostgreSQL or SQLite (for data storage)

## Dependencies

All dependencies are automatically installed via `scripts/setup.py`. Key packages include:

- FastAPI for REST API
- Streamlit for web dashboard
- SQLAlchemy for database ORM
- Pandas/NumPy for data analysis
- Scikit-learn for statistical analysis
- aiohttp for async HTTP requests

## Configuration

The system uses environment variables for configuration. Copy `.env.example` to `.env` and configure:

```env
# Database
DATABASE_URL=sqlite:///arbitrage.db

# Kalshi API
KALSHI_API_KEY=your_api_key
KALSHI_API_SECRET=your_secret

# Trading
TRADING_MODE=paper  # or 'live'
INITIAL_CAPITAL=100000

# Risk Management
MAX_POSITION_SIZE=0.1
MAX_DAILY_LOSS=0.05
```

## Usage Examples

### Running Strategies
```python
from src.strategies.cross_platform import CrossPlatformArbitrage
from src.data.aggregator import DataAggregator

# Initialize strategy
strategy = CrossPlatformArbitrage()

# Get market data
aggregator = DataAggregator()
markets = await aggregator.get_all_markets()

# Find opportunities
opportunities = await strategy.find_opportunities(markets)
```

### Backtesting
```python
from src.backtesting.engine import BacktestEngine
from datetime import datetime

engine = BacktestEngine(initial_capital=100000)
results = await engine.run_backtest(
    strategy=strategy,
    historical_data=data,
    start_date=datetime(2024, 1, 1),
    end_date=datetime(2024, 12, 31)
)
```

### Risk Management
```python
from src.risk.manager import RiskManager

risk_manager = RiskManager()
is_safe, reason = risk_manager.check_signal_risk(trading_signal)
```

## Web Dashboard

Access the web dashboard at `http://localhost:8501` after running:
```bash
python main.py dashboard
```

Features:
- Real-time market monitoring
- Strategy performance tracking
- Risk metrics visualization
- Order management interface
- Backtesting results

## API Endpoints

The system provides a REST API for external integration:

- `GET /api/v1/markets` - Get current markets
- `GET /api/v1/strategies` - List active strategies
- `POST /api/v1/orders` - Place orders
- `GET /api/v1/positions` - View positions
- `GET /api/v1/performance` - Get performance metrics

See [API Documentation](docs/API.md) for complete reference.

## Development

### Adding New Strategies

1. Create a new class inheriting from `BaseStrategy`
2. Implement `analyze_markets()` and `find_opportunities()` methods
3. Register the strategy in the main system
4. Add configuration parameters

See [Developer Guide](docs/DEVELOPER.md) for detailed instructions.

### Adding New Platforms

1. Implement `BaseDataProvider` for data acquisition
2. Implement `BaseTradingClient` for order execution
3. Register providers in the data aggregator
4. Add platform-specific configuration

### Testing

```bash
# Run all tests
python -m pytest tests/

# Run specific test
python -m pytest tests/test_strategies.py

# Run with coverage
python -m pytest tests/ --cov=src
```

## Deployment

### Production Setup

1. Set up production environment variables
2. Configure production database (PostgreSQL recommended)
3. Set up Redis for caching
4. Configure logging and monitoring
5. Deploy using Docker or traditional deployment

### Docker Deployment
```bash
# Build image
docker build -t arbitrage-system .

# Run container
docker run -d --name arbitrage \
  -p 8000:8000 \
  -p 8501:8501 \
  -e DATABASE_URL=postgresql://... \
  arbitrage-system
```

## Monitoring

The system includes comprehensive logging and monitoring:

- **Logs**: Structured logging with configurable levels
- **Metrics**: Performance and risk metrics tracking
- **Alerts**: Risk and system alerts
- **Dashboard**: Real-time monitoring interface

## Security

- API key management through environment variables
- Request rate limiting
- Order size and risk limits
- Audit logging for all trades

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests for new functionality
5. Submit a pull request

## License

This project is licensed under the MIT License. See LICENSE file for details.

## Support

- Check [Troubleshooting Guide](docs/TROUBLESHOOTING.md) for common issues
- Review logs in `logs/arbitrage.log`
- Use the web dashboard for monitoring
- Run tests to verify functionality

## Roadmap

- [ ] Additional platform integrations
- [ ] Advanced ML-based strategies
- [ ] Portfolio optimization
- [ ] Real-time risk monitoring
- [ ] Mobile dashboard
- [ ] Advanced backtesting features

## Disclaimer

This software is for educational and research purposes. Use at your own risk. Always test thoroughly with paper trading before using real money. The authors are not responsible for any financial losses.

All configuration is managed through environment variables and config files in `config/`.

## Testing

```bash
pytest tests/
```

## License

MIT License