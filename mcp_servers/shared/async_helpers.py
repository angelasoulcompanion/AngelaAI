"""
Async helpers for MCP servers.

Provides:
- run_in_thread(): Decorator to run blocking functions in asyncio.to_thread()
- with_retry(): Retry wrapper with exponential backoff for transient failures
- google_api_call(): Combines to_thread + retry for Google API .execute() calls
"""

import asyncio
import functools
import logging
from typing import TypeVar, Callable, Any

try:
    from googleapiclient.errors import HttpError
    _GOOGLE_TRANSIENT = (ConnectionError, TimeoutError, HttpError)
except ImportError:
    _GOOGLE_TRANSIENT = (ConnectionError, TimeoutError)

T = TypeVar("T")

logger = logging.getLogger("angela.shared")


def run_in_thread(func: Callable[..., T]) -> Callable[..., T]:
    """
    Decorator that wraps a sync function to run in asyncio.to_thread().

    Usage:
        @run_in_thread
        def blocking_operation():
            return service.events().list(...).execute()

        result = await blocking_operation()
    """
    @functools.wraps(func)
    async def wrapper(*args: Any, **kwargs: Any) -> T:
        return await asyncio.to_thread(func, *args, **kwargs)
    return wrapper


async def with_retry(
    func: Callable,
    *args: Any,
    max_attempts: int = 3,
    retry_on: tuple[type[Exception], ...] = (ConnectionError, TimeoutError),
    base_delay: float = 1.0,
    **kwargs: Any,
) -> Any:
    """
    Retry an async or sync callable with exponential backoff.

    Args:
        func: The function to call (async or sync)
        *args: Positional arguments for func
        max_attempts: Maximum number of attempts (default: 3)
        retry_on: Tuple of exception types to retry on
        base_delay: Base delay in seconds between retries (doubles each attempt)
        **kwargs: Keyword arguments for func

    Returns:
        The result of func(*args, **kwargs)

    Raises:
        The last exception if all attempts fail
    """
    last_exception = None

    for attempt in range(1, max_attempts + 1):
        try:
            result = func(*args, **kwargs)
            if asyncio.iscoroutine(result):
                return await result
            return result
        except retry_on as e:
            last_exception = e
            if attempt < max_attempts:
                delay = base_delay * (2 ** (attempt - 1))
                logger.warning(
                    "Attempt %d/%d failed (%s: %s), retrying in %.1fs...",
                    attempt, max_attempts, type(e).__name__, e, delay,
                )
                await asyncio.sleep(delay)
            else:
                logger.error(
                    "All %d attempts failed. Last error: %s: %s",
                    max_attempts, type(e).__name__, e,
                )

    raise last_exception


async def google_api_call(blocking_func: Callable[..., Any], *args: Any, **kwargs: Any) -> Any:
    """
    Execute a blocking Google API call in a thread with retry for transient errors.

    Retries on HttpError (5xx), ConnectionError, and TimeoutError.

    Usage:
        result = await google_api_call(
            lambda: service.events().list(calendarId='primary').execute()
        )

    Args:
        blocking_func: A zero-arg callable that performs the blocking API call
        *args, **kwargs: Passed to blocking_func if it accepts them

    Returns:
        The result of the API call
    """

    def _is_transient_http_error(exc: Exception) -> bool:
        """Check if HttpError is transient (5xx or 429)."""
        try:
            from googleapiclient.errors import HttpError as GHttpError
            if isinstance(exc, GHttpError):
                return exc.resp.status >= 500 or exc.resp.status == 429
        except ImportError:
            pass
        return False

    last_exception = None

    for attempt in range(1, 4):  # max 3 attempts
        try:
            return await asyncio.to_thread(blocking_func, *args, **kwargs)
        except _GOOGLE_TRANSIENT as e:
            # Only retry HttpErrors that are transient (5xx, 429)
            try:
                from googleapiclient.errors import HttpError as GHttpError
                if isinstance(e, GHttpError) and not _is_transient_http_error(e):
                    raise  # Don't retry 4xx errors (except 429)
            except ImportError:
                pass

            last_exception = e
            if attempt < 3:
                delay = 1.0 * (2 ** (attempt - 1))
                logger.warning(
                    "Google API attempt %d/3 failed (%s), retrying in %.1fs...",
                    attempt, e, delay,
                )
                await asyncio.sleep(delay)
            else:
                logger.error("Google API all 3 attempts failed: %s", e)

    raise last_exception
