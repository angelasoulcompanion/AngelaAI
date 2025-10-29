#!/usr/bin/env python3
"""
Angela Async Helpers
Utilities for working with async/await patterns consistently
"""

import asyncio
import functools
from typing import Callable, Any, Coroutine, TypeVar, List
from concurrent.futures import ThreadPoolExecutor

T = TypeVar('T')


def run_async(coro: Coroutine[Any, Any, T]) -> T:
    """
    Run an async coroutine from sync context

    Args:
        coro: Coroutine to run

    Returns:
        Result of coroutine

    Usage:
        result = run_async(some_async_function())
    """
    try:
        loop = asyncio.get_running_loop()
    except RuntimeError:
        # No event loop running
        return asyncio.run(coro)
    else:
        # Event loop already running (e.g., in Jupyter)
        return loop.run_until_complete(coro)


def to_async(func: Callable) -> Callable:
    """
    Convert a sync function to async

    Args:
        func: Synchronous function to convert

    Returns:
        Async version of the function

    Usage:
        @to_async
        def sync_func(x):
            return x * 2

        result = await sync_func(5)
    """
    @functools.wraps(func)
    async def wrapper(*args, **kwargs):
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(None, functools.partial(func, *args, **kwargs))

    return wrapper


def to_sync(async_func: Callable) -> Callable:
    """
    Convert an async function to sync

    Args:
        async_func: Async function to convert

    Returns:
        Sync version of the function

    Usage:
        @to_sync
        async def async_func(x):
            await asyncio.sleep(1)
            return x * 2

        result = async_func(5)  # Blocks until complete
    """
    @functools.wraps(async_func)
    def wrapper(*args, **kwargs):
        return run_async(async_func(*args, **kwargs))

    return wrapper


async def run_in_parallel(*coroutines: Coroutine) -> List[Any]:
    """
    Run multiple coroutines in parallel

    Args:
        *coroutines: Coroutines to run

    Returns:
        List of results in same order as input

    Usage:
        results = await run_in_parallel(
            fetch_data(1),
            fetch_data(2),
            fetch_data(3)
        )
    """
    return await asyncio.gather(*coroutines)


async def run_with_timeout(coro: Coroutine[Any, Any, T], timeout: float) -> T:
    """
    Run a coroutine with timeout

    Args:
        coro: Coroutine to run
        timeout: Timeout in seconds

    Returns:
        Result of coroutine

    Raises:
        asyncio.TimeoutError: If timeout is exceeded

    Usage:
        result = await run_with_timeout(slow_function(), timeout=5.0)
    """
    return await asyncio.wait_for(coro, timeout=timeout)


async def batch_process(
    items: List[Any],
    async_func: Callable,
    batch_size: int = 10,
    delay: float = 0.0
) -> List[Any]:
    """
    Process items in batches asynchronously

    Args:
        items: Items to process
        async_func: Async function to apply to each item
        batch_size: Number of items per batch
        delay: Delay between batches (seconds)

    Returns:
        List of results

    Usage:
        results = await batch_process(
            items=my_list,
            async_func=process_item,
            batch_size=10,
            delay=0.5
        )
    """
    results = []

    for i in range(0, len(items), batch_size):
        batch = items[i:i + batch_size]
        batch_results = await asyncio.gather(*[async_func(item) for item in batch])
        results.extend(batch_results)

        # Delay between batches (except for last batch)
        if i + batch_size < len(items) and delay > 0:
            await asyncio.sleep(delay)

    return results


class AsyncLock:
    """
    Simple async lock for managing concurrent access

    Usage:
        lock = AsyncLock()

        async def critical_section():
            async with lock:
                # Only one coroutine can execute this at a time
                await do_something()
    """

    def __init__(self):
        self._lock = asyncio.Lock()

    async def __aenter__(self):
        await self._lock.acquire()
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        self._lock.release()
        return False


class AsyncRateLimiter:
    """
    Rate limiter for async operations

    Usage:
        limiter = AsyncRateLimiter(max_calls=10, period=1.0)

        async def rate_limited_operation():
            async with limiter:
                await do_api_call()
    """

    def __init__(self, max_calls: int, period: float):
        self.max_calls = max_calls
        self.period = period
        self.calls = []
        self._lock = asyncio.Lock()

    async def __aenter__(self):
        async with self._lock:
            now = asyncio.get_event_loop().time()

            # Remove old calls outside the period
            self.calls = [call_time for call_time in self.calls if call_time > now - self.period]

            # Wait if we've hit the limit
            if len(self.calls) >= self.max_calls:
                sleep_time = self.calls[0] + self.period - now
                if sleep_time > 0:
                    await asyncio.sleep(sleep_time)

            # Record this call
            self.calls.append(asyncio.get_event_loop().time())

        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        return False


def ensure_async(func_or_coro):
    """
    Ensure a function or coroutine is async

    Args:
        func_or_coro: Function or coroutine

    Returns:
        Async version

    Usage:
        async_func = ensure_async(maybe_sync_func)
        result = await async_func(args)
    """
    if asyncio.iscoroutinefunction(func_or_coro):
        return func_or_coro
    elif callable(func_or_coro):
        return to_async(func_or_coro)
    else:
        # It's already a coroutine
        async def wrapper():
            return await func_or_coro
        return wrapper


async def run_periodic(
    async_func: Callable,
    interval: float,
    *args,
    **kwargs
):
    """
    Run an async function periodically

    Args:
        async_func: Async function to run
        interval: Interval between runs (seconds)
        *args: Arguments for async_func
        **kwargs: Keyword arguments for async_func

    Usage:
        await run_periodic(check_health, interval=60.0)
    """
    while True:
        try:
            await async_func(*args, **kwargs)
        except Exception as e:
            import logging
            logging.error(f"Error in periodic task: {e}")

        await asyncio.sleep(interval)
