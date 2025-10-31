"""
Centralized logging configuration.
Consistent logging everywhere - change log format once, affects everywhere.
"""

import logging
import sys
from pathlib import Path
from typing import Optional


def setup_logger(
    name: str = "quantshit",
    level: str = "INFO",
    log_file: Optional[str] = None,
    format_string: Optional[str] = None
) -> logging.Logger:
    """
    Configure and return a logger with consistent formatting.

    Args:
        name: Logger name
        level: Log level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
        log_file: Optional file to write logs to
        format_string: Custom format string (uses default if None)

    Returns:
        Configured logger instance
    """
    logger = logging.getLogger(name)
    logger.setLevel(getattr(logging, level.upper()))

    # Avoid adding handlers multiple times
    if logger.handlers:
        return logger

    # Default format with timestamp, level, module, and message
    if format_string is None:
        format_string = '%(asctime)s - %(name)s - %(levelname)s - %(module)s - %(message)s'

    formatter = logging.Formatter(format_string)

    # Console handler (stdout)
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setFormatter(formatter)
    logger.addHandler(console_handler)

    # File handler (if log_file specified)
    if log_file:
        # Ensure log directory exists
        log_path = Path(log_file)
        log_path.parent.mkdir(parents=True, exist_ok=True)

        file_handler = logging.FileHandler(log_file)
        file_handler.setFormatter(formatter)
        logger.addHandler(file_handler)

    return logger


def get_logger(name: str) -> logging.Logger:
    """
    Get an existing logger or create a new one with default settings.

    Args:
        name: Logger name (typically __name__ from calling module)

    Returns:
        Logger instance
    """
    logger = logging.getLogger(name)

    # If logger hasn't been configured yet, set it up with defaults
    if not logger.handlers:
        from ..config import settings
        setup_logger(
            name=name,
            level=settings.LOG_LEVEL,
            log_file=settings.LOG_FILE
        )

    return logger
