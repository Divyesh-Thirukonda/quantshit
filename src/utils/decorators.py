"""
Reusable function decorators.
Add @retry, @rate_limit, etc. to any function without reimplementing the logic.
"""

import time
import functools
from typing import Callable, Any, Optional, Dict
from datetime import datetime, timedelta
from .logger import get_logger

logger = get_logger(__name__)


def retry(
    max_attempts: int = 3,
    backoff: float = 2.0,
    exceptions: tuple = (Exception,)
):
    """
    Retry decorator for handling transient failures (e.g., API calls).

    Args:
        max_attempts: Maximum number of attempts
        backoff: Exponential backoff multiplier (e.g., 2.0 means 1s, 2s, 4s delays)
        exceptions: Tuple of exception types to catch and retry

    Usage:
        @retry(max_attempts=3, backoff=2)
        def fetch_markets():
            return api.get_markets()
    """
    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        def wrapper(*args, **kwargs) -> Any:
            attempt = 1
            delay = 1.0

            while attempt <= max_attempts:
                try:
                    return func(*args, **kwargs)
                except exceptions as e:
                    if attempt == max_attempts:
                        logger.error(f"{func.__name__} failed after {max_attempts} attempts: {e}")
                        raise

                    logger.warning(
                        f"{func.__name__} failed (attempt {attempt}/{max_attempts}): {e}. "
                        f"Retrying in {delay}s..."
                    )
                    time.sleep(delay)
                    attempt += 1
                    delay *= backoff

        return wrapper
    return decorator


def rate_limit(calls: int = 10, period: float = 1.0):
    """
    Rate limiting decorator to prevent hitting API rate limits.

    Args:
        calls: Maximum number of calls allowed
        period: Time period in seconds

    Usage:
        @rate_limit(calls=10, period=1)
        def api_call():
            return requests.get(...)
    """
    def decorator(func: Callable) -> Callable:
        # Store call timestamps
        call_times: list = []

        @functools.wraps(func)
        def wrapper(*args, **kwargs) -> Any:
            nonlocal call_times

            now = time.time()

            # Remove timestamps older than the period
            call_times = [t for t in call_times if now - t < period]

            # Check if we've hit the limit
            if len(call_times) >= calls:
                # Calculate how long to wait
                oldest_call = min(call_times)
                wait_time = period - (now - oldest_call)

                if wait_time > 0:
                    logger.debug(f"Rate limit reached for {func.__name__}, waiting {wait_time:.2f}s")
                    time.sleep(wait_time)

            # Record this call
            call_times.append(time.time())

            return func(*args, **kwargs)

        return wrapper
    return decorator


def log_execution_time(func: Callable) -> Callable:
    """
    Decorator to log function execution time.

    Usage:
        @log_execution_time
        def expensive_operation():
            # do work
            pass
    """
    @functools.wraps(func)
    def wrapper(*args, **kwargs) -> Any:
        start_time = time.time()
        try:
            result = func(*args, **kwargs)
            return result
        finally:
            execution_time = time.time() - start_time
            logger.debug(f"{func.__name__} executed in {execution_time:.3f}s")

    return wrapper


def cache(ttl: int = 60):
    """
    Simple cache decorator with time-to-live.

    Args:
        ttl: Time to live in seconds

    Usage:
        @cache(ttl=60)
        def get_markets():
            return expensive_api_call()
    """
    def decorator(func: Callable) -> Callable:
        cached_result: Dict[str, Any] = {}

        @functools.wraps(func)
        def wrapper(*args, **kwargs) -> Any:
            # Create cache key from function name and args
            cache_key = f"{func.__name__}:{str(args)}:{str(kwargs)}"

            now = datetime.now()

            # Check if we have a valid cached result
            if cache_key in cached_result:
                cached_time, result = cached_result[cache_key]
                if now - cached_time < timedelta(seconds=ttl):
                    logger.debug(f"Cache hit for {func.__name__}")
                    return result

            # Cache miss or expired - call function
            logger.debug(f"Cache miss for {func.__name__}")
            result = func(*args, **kwargs)
            cached_result[cache_key] = (now, result)

            return result

        # Add method to clear cache
        def clear_cache():
            cached_result.clear()

        wrapper.clear_cache = clear_cache  # type: ignore

        return wrapper
    return decorator
