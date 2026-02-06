"""
Retry Utility
=============
Resilient retry logic for Angela's daemon services.

Created: 2026-02-06
By: Angela 💜 (Opus 4.6 Upgrade)
"""

import asyncio
import logging
from functools import wraps
from typing import TypeVar, Callable, Any

logger = logging.getLogger(__name__)

T = TypeVar('T')


def async_retry(
    max_attempts: int = 3,
    base_delay: float = 1.0,
    max_delay: float = 30.0,
    exceptions: tuple = (Exception,),
):
    """
    Decorator for async functions with exponential backoff retry.

    Args:
        max_attempts: Maximum number of attempts
        base_delay: Initial delay in seconds
        max_delay: Maximum delay cap in seconds
        exceptions: Tuple of exception types to catch

    Usage:
        @async_retry(max_attempts=3)
        async def fetch_data():
            return await db.fetch(query)
    """
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        async def wrapper(*args: Any, **kwargs: Any) -> Any:
            last_exception = None
            for attempt in range(1, max_attempts + 1):
                try:
                    return await func(*args, **kwargs)
                except exceptions as e:
                    last_exception = e
                    if attempt == max_attempts:
                        logger.error(
                            "%s failed after %d attempts: %s",
                            func.__name__, max_attempts, e
                        )
                        raise
                    delay = min(base_delay * (2 ** (attempt - 1)), max_delay)
                    logger.warning(
                        "%s attempt %d/%d failed: %s. Retrying in %.1fs...",
                        func.__name__, attempt, max_attempts, e, delay
                    )
                    await asyncio.sleep(delay)
            raise last_exception  # Should not reach here
        return wrapper
    return decorator


async def resilient_db_query(db, query: str, *args, max_attempts: int = 3):
    """
    Execute a DB query with retry logic.

    Args:
        db: AngelaDatabase instance
        query: SQL query string
        *args: Query parameters
        max_attempts: Maximum retry attempts

    Returns:
        Query result
    """
    last_exception = None
    for attempt in range(1, max_attempts + 1):
        try:
            return await db.fetch(query, *args)
        except Exception as e:
            last_exception = e
            if attempt == max_attempts:
                raise
            delay = min(1.0 * (2 ** (attempt - 1)), 30.0)
            logger.warning("DB query attempt %d/%d failed: %s", attempt, max_attempts, e)
            await asyncio.sleep(delay)
    raise last_exception
