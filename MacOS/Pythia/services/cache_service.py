"""
Pythia — In-memory TTL cache for market data.
Lightweight alternative to Redis for single-user macOS app.
Eliminates redundant yfinance API calls.
"""
from __future__ import annotations

import time
import logging
from typing import Any

logger = logging.getLogger("pythia.cache")


class CacheEntry:
    __slots__ = ("value", "expires_at")

    def __init__(self, value: Any, ttl: int):
        self.value = value
        self.expires_at = time.time() + ttl


class MemoryCache:
    """Thread-safe in-memory cache with TTL expiration."""

    # Default TTLs (seconds)
    QUOTE_TTL = 300        # 5 minutes — individual quotes
    BATCH_QUOTE_TTL = 60   # 1 minute — watchlist batch quotes
    HISTORY_TTL = 3600     # 1 hour — historical OHLCV
    OPTIONS_TTL = 1800     # 30 minutes — options chain data
    OUTLOOK_TTL = 3600     # 1 hour — financial outlook
    EARNINGS_TTL = 3600    # 1 hour — earnings calendar

    def __init__(self):
        self._store: dict[str, CacheEntry] = {}
        self._hits = 0
        self._misses = 0

    def get(self, key: str) -> Any | None:
        """Get value if exists and not expired."""
        entry = self._store.get(key)
        if entry is None:
            self._misses += 1
            return None
        if time.time() > entry.expires_at:
            del self._store[key]
            self._misses += 1
            return None
        self._hits += 1
        return entry.value

    def set(self, key: str, value: Any, ttl: int = 300):
        """Set value with TTL in seconds."""
        self._store[key] = CacheEntry(value, ttl)

    def delete(self, key: str):
        self._store.pop(key, None)

    def clear(self):
        """Clear all entries."""
        self._store.clear()
        self._hits = 0
        self._misses = 0

    def clear_prefix(self, prefix: str):
        """Clear all keys starting with prefix."""
        keys = [k for k in self._store if k.startswith(prefix)]
        for k in keys:
            del self._store[k]

    def cleanup(self):
        """Remove expired entries (call periodically)."""
        now = time.time()
        expired = [k for k, v in self._store.items() if now > v.expires_at]
        for k in expired:
            del self._store[k]
        if expired:
            logger.debug("Cache cleanup: %d expired entries removed", len(expired))

    @property
    def stats(self) -> dict:
        total = self._hits + self._misses
        return {
            "entries": len(self._store),
            "hits": self._hits,
            "misses": self._misses,
            "hit_rate": round(self._hits / total * 100, 1) if total > 0 else 0,
        }


# Singleton
cache = MemoryCache()
