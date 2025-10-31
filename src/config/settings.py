"""
Environment-specific configuration loaded from environment variables.
API keys, database connections, endpoints, feature flags.
"""

import os
from typing import Optional
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()


class Settings:
    """
    Application settings loaded from environment variables.
    Different configs for dev/staging/prod via environment.
    """

    def __init__(self):
        # API Keys
        self.KALSHI_API_KEY: Optional[str] = os.getenv('KALSHI_API_KEY')
        self.POLYMARKET_API_KEY: Optional[str] = os.getenv('POLYMARKET_API_KEY')

        # Trading parameters
        self.MIN_SPREAD: float = float(os.getenv('MIN_SPREAD', '0.05'))  # 5% minimum spread
        self.MIN_VOLUME: float = float(os.getenv('MIN_VOLUME', '1000'))  # $1000 minimum volume

        # Exchange endpoints (can switch between prod/testnet)
        self.KALSHI_API_URL: str = os.getenv('KALSHI_API_URL', 'https://api.kalshi.com/v1')
        self.POLYMARKET_API_URL: str = os.getenv('POLYMARKET_API_URL', 'https://api.polymarket.com')

        # Database configuration
        self.DATABASE_URL: Optional[str] = os.getenv('DATABASE_URL', 'sqlite:///quantshit.db')

        # Logging
        self.LOG_LEVEL: str = os.getenv('LOG_LEVEL', 'INFO')
        self.LOG_FILE: Optional[str] = os.getenv('LOG_FILE', 'quantshit.log')

        # Feature flags
        self.PAPER_TRADING: bool = os.getenv('PAPER_TRADING', 'true').lower() == 'true'
        self.ENABLE_ALERTS: bool = os.getenv('ENABLE_ALERTS', 'false').lower() == 'true'

        # Notification settings (if alerts enabled)
        self.TELEGRAM_BOT_TOKEN: Optional[str] = os.getenv('TELEGRAM_BOT_TOKEN')
        self.TELEGRAM_CHAT_ID: Optional[str] = os.getenv('TELEGRAM_CHAT_ID')

        # Performance tuning
        self.MAX_CONCURRENT_REQUESTS: int = int(os.getenv('MAX_CONCURRENT_REQUESTS', '5'))
        self.REQUEST_TIMEOUT_SECONDS: int = int(os.getenv('REQUEST_TIMEOUT_SECONDS', '30'))

    def validate(self) -> list[str]:
        """Validate required settings are present"""
        errors = []

        if not self.PAPER_TRADING:
            # In live trading mode, API keys are required
            if not self.KALSHI_API_KEY:
                errors.append("KALSHI_API_KEY is required for live trading")
            if not self.POLYMARKET_API_KEY:
                errors.append("POLYMARKET_API_KEY is required for live trading")

        if self.ENABLE_ALERTS:
            if not self.TELEGRAM_BOT_TOKEN or not self.TELEGRAM_CHAT_ID:
                errors.append("Telegram settings required when alerts are enabled")

        if self.MIN_SPREAD < 0 or self.MIN_SPREAD > 1:
            errors.append(f"MIN_SPREAD must be between 0 and 1, got {self.MIN_SPREAD}")

        if self.MIN_VOLUME < 0:
            errors.append(f"MIN_VOLUME must be non-negative, got {self.MIN_VOLUME}")

        return errors

    @property
    def is_paper_trading(self) -> bool:
        """Check if running in paper trading mode"""
        return self.PAPER_TRADING

    @property
    def has_valid_api_keys(self) -> bool:
        """Check if API keys are configured"""
        return bool(self.KALSHI_API_KEY and self.POLYMARKET_API_KEY)


# Global settings instance
settings = Settings()
