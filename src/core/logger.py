"""
Logging configuration for the arbitrage system.
"""
import os
import sys
from loguru import logger
from typing import Optional
from src.core.config import get_settings


def setup_logging(
    log_level: Optional[str] = None,
    log_file: Optional[str] = None,
    rotation: str = "10 MB",
    retention: str = "30 days"
) -> None:
    """
    Setup logging configuration.
    
    Args:
        log_level: Logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
        log_file: Path to log file
        rotation: Log rotation policy
        retention: Log retention policy
    """
    settings = get_settings()
    
    # Remove default handler
    logger.remove()
    
    # Set log level
    level = log_level or settings.log_level
    
    # Console handler with colors
    logger.add(
        sys.stdout,
        level=level,
        format="<green>{time:YYYY-MM-DD HH:mm:ss}</green> | "
               "<level>{level: <8}</level> | "
               "<cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> - "
               "<level>{message}</level>",
        colorize=True
    )
    
    # File handler
    log_path = log_file or settings.log_file
    if log_path:
        # Create logs directory if it doesn't exist
        os.makedirs(os.path.dirname(log_path), exist_ok=True)
        
        logger.add(
            log_path,
            level=level,
            format="{time:YYYY-MM-DD HH:mm:ss} | {level: <8} | {name}:{function}:{line} - {message}",
            rotation=rotation,
            retention=retention,
            compression="zip"
        )
    
    # Add custom context for trading operations
    logger.configure(
        extra={
            "strategy": "N/A",
            "platform": "N/A",
            "market": "N/A"
        }
    )


def get_logger(name: str) -> logger:
    """
    Get a logger instance for a module.
    
    Args:
        name: Logger name (usually __name__)
        
    Returns:
        Logger instance
    """
    return logger.bind(module=name)


# Initialize logging on import
setup_logging()