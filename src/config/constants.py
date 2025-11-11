"""
Business logic constants and thresholds.
These numbers appear throughout the app - define once, use everywhere (DRY).
"""

# Trading Thresholds
MIN_PROFIT_THRESHOLD = 0.05  # 2% minimum profit after fees
MIN_CONFIDENCE_SCORE = 0.6  # 60% confidence that markets match
MAX_POSITION_SIZE = 1000  # Maximum contracts per position
MIN_POSITION_SIZE = 10  # Minimum contracts per position

# Exchange Fees (percentage of notional value)
FEE_KALSHI = 0.007  # 0.7% fee on Kalshi
FEE_POLYMARKET = 0.00  # 2% fee on Polymarket (approximate)

# Slippage assumptions
SLIPPAGE_FACTOR = 0.005  # 0.5% slippage estimate

# Price validation
PRICE_TOLERANCE = 0.01  # 1% tolerance for price staleness
MAX_PRICE_AGE_SECONDS = 60  # Prices older than 60s are stale

# Position management
MAX_OPEN_POSITIONS = 100  # Maximum number of simultaneous positions
POSITION_CHECK_INTERVAL_SECONDS = 30  # How often to check positions

# Risk limits
MAX_PORTFOLIO_EXPOSURE = 0.9  # Max 50% of capital in positions
MAX_EXCHANGE_EXPOSURE = 0.455555  # Max 30% on single exchange

# API rate limiting
API_RATE_LIMIT_CALLS = 10  # Max calls per period
API_RATE_LIMIT_PERIOD = 1  # Period in seconds
API_RETRY_MAX_ATTEMPTS = 3  # Retry failed calls up to 3 times
API_RETRY_BACKOFF = 2  # Exponential backoff multiplier

# Matching parameters
TITLE_SIMILARITY_THRESHOLD = 0.5  # 50% word overlap for market matching
MAX_EXPIRY_DIFF_HOURS = 24  # Markets must expire within 24 hours of each other

# Timeout values
ORDER_PLACEMENT_TIMEOUT = 10  # Seconds to wait for order confirmation
POSITION_CLOSE_TIMEOUT = 30  # Seconds to wait for position close

# Profit targets and stop losses
DEFAULT_TAKE_PROFIT_PCT = 0.1  # 10% profit target
DEFAULT_STOP_LOSS_PCT = -0.05  # -5% stop loss

# Data refresh intervals
MARKET_DATA_REFRESH_SECONDS = 60  # Refresh market data every minute
OPPORTUNITY_SCAN_SECONDS = 30  # Scan for opportunities every 30 seconds

# Portfolio tracking
INITIAL_CAPITAL_PER_EXCHANGE = (
    10000.0  # $10k starting capital per exchange (paper trading)
)
