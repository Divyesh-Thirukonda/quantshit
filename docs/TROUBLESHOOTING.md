# Troubleshooting Guide

## Common Issues and Solutions

### Installation Issues

#### Python Version
**Issue**: "Python version not supported"
```
Solution: Ensure you're using Python 3.8 or higher
python --version
pip install --upgrade python
```

#### Dependencies
**Issue**: "Package not found" or import errors
```
Solution: Install all dependencies
pip install -r requirements.txt

# For development dependencies
pip install -r requirements-dev.txt
```

#### Virtual Environment
**Issue**: Conflicts with system packages
```
Solution: Use virtual environment
python -m venv venv
venv\Scripts\activate  # Windows
pip install -r requirements.txt
```

### Configuration Issues

#### Environment Variables
**Issue**: "Configuration not found" errors
```
Solution: Create .env file with required variables
cp .env.example .env
# Edit .env with your API keys and settings
```

#### Database Connection
**Issue**: "Database connection failed"
```
Solution: Check database settings
# For SQLite (default)
DATABASE_URL=sqlite:///arbitrage.db

# For PostgreSQL
DATABASE_URL=postgresql://user:pass@localhost/arbitrage
```

#### API Keys
**Issue**: "Authentication failed" for trading platforms
```
Solution: Verify API credentials
# Check .env file
KALSHI_API_KEY=your_api_key
KALSHI_API_SECRET=your_secret

# Test connection
python -c "from src.platforms.kalshi import KalshiDataProvider; print('OK')"
```

### Runtime Issues

#### Memory Usage
**Issue**: High memory consumption
```
Solution: Adjust batch sizes and caching
# In config.py
BATCH_SIZE = 100  # Reduce if needed
CACHE_TTL = 300   # Reduce cache time
```

#### Performance Issues
**Issue**: Slow data fetching
```
Solution: Enable concurrent requests
# In config.py
MAX_CONCURRENT_REQUESTS = 10  # Adjust based on API limits
ENABLE_CACHING = True
```

#### Rate Limiting
**Issue**: "Rate limit exceeded" errors
```
Solution: Adjust request frequency
# In config.py
REQUEST_DELAY = 1.0  # Seconds between requests
MAX_REQUESTS_PER_MINUTE = 60
```

### Strategy Issues

#### No Trading Signals
**Issue**: Strategy not generating signals
```
Solution: Check strategy parameters and data
# Debug mode
python main.py run --debug

# Check logs
tail -f logs/arbitrage.log

# Verify market data
python -c "
from src.data.aggregator import DataAggregator
aggregator = DataAggregator()
markets = await aggregator.get_all_markets()
print(len(markets))
"
```

#### Backtest Failures
**Issue**: Backtesting crashes or wrong results
```
Solution: Validate historical data
# Check data format
python scripts/validate_data.py

# Run simple backtest
python scripts/quick_backtest.py
```

#### Execution Errors
**Issue**: Orders not being placed
```
Solution: Check execution engine
# Test mode
TRADING_MODE = "paper"  # In .env

# Check order status
python -c "
from src.execution.engine import OrderManager
manager = OrderManager()
print(manager.get_order_status('order_id'))
"
```

### Data Issues

#### Missing Market Data
**Issue**: "No data available" for certain markets
```
Solution: Check data providers
# Test data connection
python -c "
from src.platforms.kalshi import KalshiDataProvider
provider = KalshiDataProvider()
await provider.connect()
markets = await provider.get_markets()
print(len(markets))
"
```

#### Stale Data
**Issue**: Old or incorrect market prices
```
Solution: Clear cache and refresh
# Clear Redis cache
redis-cli FLUSHDB

# Restart data feeds
python main.py restart-data
```

#### Data Validation Errors
**Issue**: "Invalid market data" errors
```
Solution: Check data format
# Validate data schema
python -c "
from src.core.database import MarketData
# Check if data matches schema
"
```

### Dashboard Issues

#### Streamlit Errors
**Issue**: Dashboard won't start
```
Solution: Check Streamlit installation
pip install streamlit --upgrade

# Run dashboard separately
streamlit run src/frontend/dashboard.py
```

#### Charts Not Loading
**Issue**: Empty or broken charts
```
Solution: Check data and Plotly
pip install plotly --upgrade

# Test with sample data
python -c "
import plotly.graph_objects as go
fig = go.Figure()
print('Plotly OK')
"
```

#### Authentication Issues
**Issue**: Can't access protected endpoints
```
Solution: Check API authentication
# Test API endpoint
curl -X GET http://localhost:8000/api/v1/markets \
  -H "Authorization: Bearer your_token"
```

### System Issues

#### High CPU Usage
**Issue**: System consuming too much CPU
```
Solution: Optimize strategy frequency
# In strategy config
UPDATE_INTERVAL = 60  # Seconds between updates
ENABLE_THREADING = False  # If causing issues
```

#### Memory Leaks
**Issue**: Memory usage keeps growing
```
Solution: Check for unclosed connections
# Monitor memory
python -c "
import psutil
import time
process = psutil.Process()
while True:
    print(f'Memory: {process.memory_info().rss / 1024 / 1024:.1f} MB')
    time.sleep(5)
"
```

#### Log File Size
**Issue**: Log files growing too large
```
Solution: Configure log rotation
# In config.py
LOG_ROTATION = "100 MB"
LOG_RETENTION = "7 days"
```

### Development Issues

#### Import Errors
**Issue**: "Module not found" errors
```
Solution: Check PYTHONPATH
# Add to .env
PYTHONPATH=.

# Or use relative imports
python -m src.main
```

#### Test Failures
**Issue**: Tests failing unexpectedly
```
Solution: Check test environment
# Run tests in isolation
python -m pytest tests/ -v

# Check test data
python -c "
import tests.test_data as td
print(td.sample_markets)
"
```

#### Code Formatting
**Issue**: Linting errors
```
Solution: Run code formatters
# Format code
black src/ tests/
isort src/ tests/

# Check style
flake8 src/ tests/
```

## Debugging Techniques

### Enable Debug Logging
```python
# In .env
LOG_LEVEL = "DEBUG"

# Or programmatically
from src.core.logger import setup_logging
setup_logging(level="DEBUG")
```

### Profile Performance
```python
import cProfile
import pstats

# Profile a function
cProfile.run('your_function()', 'profile_stats')
stats = pstats.Stats('profile_stats')
stats.sort_stats('cumulative').print_stats(10)
```

### Monitor System Resources
```python
import psutil

# Check system resources
print(f"CPU: {psutil.cpu_percent()}%")
print(f"Memory: {psutil.virtual_memory().percent}%")
print(f"Disk: {psutil.disk_usage('/').percent}%")
```

### Test API Endpoints
```bash
# Test health endpoint
curl http://localhost:8000/health

# Test markets endpoint
curl http://localhost:8000/api/v1/markets

# Test with authentication
curl -H "Authorization: Bearer token" http://localhost:8000/api/v1/positions
```

## Log Analysis

### Important Log Patterns
```
# Connection issues
grep "Connection failed" logs/arbitrage.log

# Trading signals
grep "Trading signal generated" logs/arbitrage.log

# Risk alerts
grep "Risk alert" logs/arbitrage.log

# Order execution
grep "Order executed" logs/arbitrage.log
```

### Log Levels
- **DEBUG**: Detailed information for debugging
- **INFO**: General information about system operation
- **WARNING**: Warning messages about potential issues
- **ERROR**: Error messages for failed operations
- **CRITICAL**: Critical errors that may stop the system

## Performance Monitoring

### Key Metrics to Watch
- **Memory Usage**: Should remain stable
- **CPU Usage**: Should be reasonable for your hardware
- **Request Latency**: API calls should complete quickly
- **Order Fill Rate**: Percentage of successful order executions
- **Strategy Performance**: PnL and risk metrics

### Monitoring Tools
```python
# Built-in metrics
from src.risk.manager import RiskManager
risk_manager = RiskManager()
metrics = risk_manager.get_performance_metrics()

# System metrics
import psutil
print(f"System load: {psutil.getloadavg()}")
```

## Getting Support

### Before Asking for Help
1. Check this troubleshooting guide
2. Search the logs for error messages
3. Verify your configuration
4. Test with minimal examples
5. Check if it's a known issue

### Information to Include
- Error messages (full stack trace)
- Configuration details (without secrets)
- System information (OS, Python version)
- Steps to reproduce the issue
- What you expected vs. what happened

### Useful Debug Commands
```bash
# System info
python --version
pip list
uname -a  # Linux/Mac
systeminfo  # Windows

# Test basic functionality
python -c "import src.core.config; print('Config OK')"
python -c "from src.data.aggregator import DataAggregator; print('Data OK')"
python -c "from src.strategies.base import BaseStrategy; print('Strategies OK')"

# Check database
python -c "from src.core.database import create_database_engine; print('DB OK')"
```