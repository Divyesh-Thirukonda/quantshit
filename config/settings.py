"""Configuration management for the arbitrage system."""

import os
from typing import Dict, List, Optional
from dataclasses import dataclass, field
from dotenv import load_dotenv

from src.core import Platform, RiskLevel

# Load environment variables
load_dotenv()


@dataclass
class TradingConfig:
    """Trading-related configuration."""
    max_position_size: float = 1000.0  # Max USD per position
    max_total_exposure: float = 10000.0  # Max total USD exposure
    min_profit_threshold: float = 0.02  # Minimum 2% profit
    max_spread_threshold: float = 0.10  # Maximum 10% spread to consider
    default_risk_level: RiskLevel = RiskLevel.MEDIUM
    paper_trading: bool = True  # Start with paper trading


@dataclass
class PlatformCredentials:
    """Credentials for a trading platform."""
    api_key: str
    api_secret: Optional[str] = None
    base_url: str = ""
    is_testnet: bool = True


@dataclass
class Config:
    """Main configuration class."""
    # Environment
    environment: str = field(default_factory=lambda: os.getenv("ENVIRONMENT", "development"))
    debug: bool = field(default_factory=lambda: os.getenv("DEBUG", "true").lower() == "true")
    
    # Trading
    trading: TradingConfig = field(default_factory=TradingConfig)
    
    # Platform credentials
    platforms: Dict[Platform, PlatformCredentials] = field(default_factory=dict)
    
    # Database
    database_url: str = field(default_factory=lambda: os.getenv("DATABASE_URL", "sqlite:///./quantshit.db"))
    
    # Redis (for caching and message queue)
    redis_url: str = field(default_factory=lambda: os.getenv("REDIS_URL", "redis://localhost:6379"))
    
    # API settings
    api_host: str = field(default_factory=lambda: os.getenv("API_HOST", "127.0.0.1"))
    api_port: int = field(default_factory=lambda: int(os.getenv("API_PORT", "8000")))
    
    def __post_init__(self):
        """Initialize platform credentials from environment variables."""
        # Kalshi credentials
        kalshi_key = os.getenv("KALSHI_API_KEY")
        if kalshi_key:
            self.platforms[Platform.KALSHI] = PlatformCredentials(
                api_key=kalshi_key,
                api_secret=os.getenv("KALSHI_API_SECRET"),
                base_url=os.getenv("KALSHI_BASE_URL", "https://trading-api.kalshi.com/trade-api/v2"),
                is_testnet=os.getenv("KALSHI_TESTNET", "true").lower() == "true"
            )
        
        # Polymarket credentials  
        polymarket_key = os.getenv("POLYMARKET_API_KEY")
        if polymarket_key:
            self.platforms[Platform.POLYMARKET] = PlatformCredentials(
                api_key=polymarket_key,
                api_secret=os.getenv("POLYMARKET_API_SECRET"),
                base_url=os.getenv("POLYMARKET_BASE_URL", "https://clob.polymarket.com"),
                is_testnet=os.getenv("POLYMARKET_TESTNET", "true").lower() == "true"
            )
    
    def get_platform_config(self, platform: Platform) -> Optional[PlatformCredentials]:
        """Get configuration for a specific platform."""
        return self.platforms.get(platform)


# Global config instance
config = Config()