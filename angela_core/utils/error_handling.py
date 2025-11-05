#!/usr/bin/env python3
"""
Angela Error Handling
Centralized error handling and retry logic for all services
"""

import functools
import asyncio
import logging
from typing import Callable, Any, Optional
from datetime import datetime

logger = logging.getLogger(__name__)


class AngelaError(Exception):
    """Base exception for Angela-specific errors"""
    pass


class DatabaseError(AngelaError):
    """Database-related errors"""
    pass


class EmbeddingError(AngelaError):
    """Embedding generation errors"""
    pass


class ModelError(AngelaError):
    """Model inference errors"""
    pass


class ConfigError(AngelaError):
    """Configuration errors"""
    pass


def with_error_handling(
    error_message: str = "Operation failed",
    log_error: bool = True,
    raise_on_error: bool = True,
    default_return: Any = None
):
    """
    Decorator for consistent error handling across Angela services

    Args:
        error_message: Custom error message prefix
        log_error: Whether to log errors
        raise_on_error: Whether to re-raise exceptions
        default_return: Default value to return on error (if not raising)

    Usage:
        @with_error_handling("Failed to save conversation")
        async def save_conversation(...):
            ...
    """
    def decorator(func: Callable):
        @functools.wraps(func)
        async def async_wrapper(*args, **kwargs):
            try:
                return await func(*args, **kwargs)
            except Exception as e:
                if log_error:
                    logger.error(f"❌ {error_message}: {str(e)}")
                    logger.exception(e)

                if raise_on_error:
                    # Wrap in appropriate Angela exception type
                    if "database" in str(e).lower() or "postgres" in str(e).lower():
                        raise DatabaseError(f"{error_message}: {str(e)}") from e
                    elif "embedding" in str(e).lower():
                        raise EmbeddingError(f"{error_message}: {str(e)}") from e
                    elif "model" in str(e).lower() or "ollama" in str(e).lower():
                        raise ModelError(f"{error_message}: {str(e)}") from e
                    else:
                        raise AngelaError(f"{error_message}: {str(e)}") from e
                else:
                    return default_return

        @functools.wraps(func)
        def sync_wrapper(*args, **kwargs):
            try:
                return func(*args, **kwargs)
            except Exception as e:
                if log_error:
                    logger.error(f"❌ {error_message}: {str(e)}")
                    logger.exception(e)

                if raise_on_error:
                    if "database" in str(e).lower() or "postgres" in str(e).lower():
                        raise DatabaseError(f"{error_message}: {str(e)}") from e
                    elif "embedding" in str(e).lower():
                        raise EmbeddingError(f"{error_message}: {str(e)}") from e
                    elif "model" in str(e).lower() or "ollama" in str(e).lower():
                        raise ModelError(f"{error_message}: {str(e)}") from e
                    else:
                        raise AngelaError(f"{error_message}: {str(e)}") from e
                else:
                    return default_return

        # Return appropriate wrapper based on function type
        if asyncio.iscoroutinefunction(func):
            return async_wrapper
        else:
            return sync_wrapper

    return decorator


def with_retry(
    max_retries: int = 3,
    initial_delay: float = 1.0,
    backoff_factor: float = 2.0,
    error_message: str = "Operation failed after retries"
):
    """
    Decorator for automatic retry with exponential backoff

    Args:
        max_retries: Maximum number of retry attempts
        initial_delay: Initial delay between retries (seconds)
        backoff_factor: Multiplier for delay after each retry
        error_message: Error message if all retries fail

    Usage:
        @with_retry(max_retries=5)
        async def fetch_data(...):
            ...
    """
    def decorator(func: Callable):
        @functools.wraps(func)
        async def async_wrapper(*args, **kwargs):
            last_exception = None
            delay = initial_delay

            for attempt in range(1, max_retries + 1):
                try:
                    return await func(*args, **kwargs)
                except Exception as e:
                    last_exception = e

                    if attempt < max_retries:
                        logger.warning(
                            f"⚠️ Attempt {attempt}/{max_retries} failed: {str(e)}"
                        )
                        logger.info(f"⏳ Retrying in {delay:.1f} seconds...")
                        await asyncio.sleep(delay)
                        delay *= backoff_factor
                    else:
                        logger.error(
                            f"❌ {error_message} after {max_retries} attempts: {str(e)}"
                        )

            # All retries exhausted
            raise AngelaError(f"{error_message}") from last_exception

        @functools.wraps(func)
        def sync_wrapper(*args, **kwargs):
            import time
            last_exception = None
            delay = initial_delay

            for attempt in range(1, max_retries + 1):
                try:
                    return func(*args, **kwargs)
                except Exception as e:
                    last_exception = e

                    if attempt < max_retries:
                        logger.warning(
                            f"⚠️ Attempt {attempt}/{max_retries} failed: {str(e)}"
                        )
                        logger.info(f"⏳ Retrying in {delay:.1f} seconds...")
                        time.sleep(delay)
                        delay *= backoff_factor
                    else:
                        logger.error(
                            f"❌ {error_message} after {max_retries} attempts: {str(e)}"
                        )

            raise AngelaError(f"{error_message}") from last_exception

        if asyncio.iscoroutinefunction(func):
            return async_wrapper
        else:
            return sync_wrapper

    return decorator


async def safe_async_operation(
    operation: Callable,
    *args,
    error_message: str = "Operation failed",
    default_return: Any = None,
    **kwargs
) -> Any:
    """
    Safely execute an async operation with error handling

    Args:
        operation: Async function to execute
        *args: Arguments for the operation
        error_message: Error message if operation fails
        default_return: Value to return on error
        **kwargs: Keyword arguments for the operation

    Returns:
        Result of operation or default_return on error
    """
    try:
        return await operation(*args, **kwargs)
    except Exception as e:
        logger.error(f"❌ {error_message}: {str(e)}")
        return default_return


class ErrorLogger:
    """Context manager for logging errors with timestamps"""

    def __init__(self, operation_name: str, log_success: bool = False):
        self.operation_name = operation_name
        self.log_success = log_success
        self.start_time = None

    async def __aenter__(self):
        self.start_time = datetime.now()
        logger.debug(f"🔄 Starting: {self.operation_name}")
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        duration = (datetime.now() - self.start_time).total_seconds()

        if exc_type is None:
            if self.log_success:
                logger.info(f"✅ {self.operation_name} completed in {duration:.2f}s")
        else:
            logger.error(f"❌ {self.operation_name} failed after {duration:.2f}s: {exc_val}")

        return False  # Don't suppress exceptions
