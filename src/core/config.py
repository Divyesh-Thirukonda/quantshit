"""
Configuration management for the arbitrage system.
"""
import os
from typing import Optional
from pydantic import BaseSettings, Field
from functools import lru_cache


class Settings(BaseSettings):
    """Application settings."""
    
    # Database
    database_url: str = Field(default="sqlite:///arbitrage.db", env="DATABASE_URL")
    redis_url: str = Field(default="redis://localhost:6379/0", env="REDIS_URL")
    
    # Kalshi API
    kalshi_api_url: str = Field(default="https://trading-api.kalshi.com/trade-api/v2", env="KALSHI_API_URL")
    kalshi_email: Optional[str] = Field(default=None, env="KALSHI_EMAIL")
    kalshi_password: Optional[str] = Field(default=None, env="KALSHI_PASSWORD")
    kalshi_api_key: Optional[str] = Field(default=None, env="KALSHI_API_KEY")
    
    # Risk Management
    max_position_size: float = Field(default=1000.0, env="MAX_POSITION_SIZE")
    max_daily_loss: float = Field(default=5000.0, env="MAX_DAILY_LOSS")
    max_correlation_exposure: float = Field(default=10000.0, env="MAX_CORRELATION_EXPOSURE")
    min_arbitrage_profit: float = Field(default=0.02, env="MIN_ARBITRAGE_PROFIT")
    
    # Execution
    order_timeout: int = Field(default=30, env="ORDER_TIMEOUT")
    max_slippage: float = Field(default=0.005, env="MAX_SLIPPAGE")
    retry_attempts: int = Field(default=3, env="RETRY_ATTEMPTS")
    
    # Logging
    log_level: str = Field(default="INFO", env="LOG_LEVEL")
    log_file: str = Field(default="logs/arbitrage.log", env="LOG_FILE")
    
    # Dashboard
    dashboard_port: int = Field(default=8501, env="DASHBOARD_PORT")
    api_port: int = Field(default=8000, env="API_PORT")
    
    # Backtesting
    backtest_start_date: str = Field(default="2023-01-01", env="BACKTEST_START_DATE")
    backtest_end_date: str = Field(default="2024-01-01", env="BACKTEST_END_DATE")
    backtest_initial_capital: float = Field(default=100000.0, env="BACKTEST_INITIAL_CAPITAL")
    
    # External APIs
    news_api_key: Optional[str] = Field(default=None, env="NEWS_API_KEY")
    twitter_bearer_token: Optional[str] = Field(default=None, env="TWITTER_BEARER_TOKEN")
    
    # Strategy Parameters
    cross_platform_min_spread: float = Field(default=0.03, env="CROSS_PLATFORM_MIN_SPREAD")
    correlation_min_threshold: float = Field(default=0.7, env="CORRELATION_MIN_THRESHOLD")
    correlation_max_threshold: float = Field(default=0.95, env="CORRELATION_MAX_THRESHOLD")
    
    # Environment
    environment: str = Field(default="development", env="ENVIRONMENT")
    debug: bool = Field(default=True, env="DEBUG")
    
    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"


@lru_cache()
def get_settings() -> Settings:
    """Get cached settings instance."""
    return Settings()


# Global settings instance
settings = get_settings()