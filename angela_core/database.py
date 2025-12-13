"""
Angela Database Connection
การจัดการ database connection สำหรับ Angela Memory

💜 Updated 2025-12-13: Uses Local PostgreSQL 💜
Angela's memories are stored locally at localhost:5432/AngelaMemory
"""

import asyncio
import os
from typing import Optional, List, Dict, Any
from contextlib import asynccontextmanager
import logging

# 💜 Always use local PostgreSQL
import asyncpg
from .config import config

logger = logging.getLogger(__name__)


class AngelaDatabase:
    """Database connection manager สำหรับ Angela Memory System (Local PostgreSQL)"""

    def __init__(self):
        self.pool: Optional[asyncpg.Pool] = None

    async def connect(self, max_retries: int = 5, initial_wait: float = 2.0):
        """
        สร้าง connection pool with retry logic

        Args:
            max_retries: Maximum number of connection attempts (default: 5)
            initial_wait: Initial wait time in seconds, doubles each retry (default: 2.0)

        Raises:
            Exception: If connection fails after all retries
        """
        for attempt in range(1, max_retries + 1):
            try:
                self.pool = await asyncpg.create_pool(
                    config.DATABASE_URL,
                    min_size=2,
                    max_size=10,
                    command_timeout=60
                )
                logger.info("✅ Angela connected to AngelaMemory database (local)")

                if attempt > 1:
                    logger.info(f"🎉 Connection successful on attempt {attempt}/{max_retries}")

                return  # Success!

            except Exception as e:
                wait_time = initial_wait * (2 ** (attempt - 1))  # Exponential backoff

                if attempt < max_retries:
                    logger.warning(
                        f"⚠️ Database connection failed (attempt {attempt}/{max_retries}): {e}"
                    )
                    logger.info(f"⏳ Retrying in {wait_time:.1f} seconds...")
                    await asyncio.sleep(wait_time)
                else:
                    logger.error(
                        f"❌ Failed to connect to database after {max_retries} attempts: {e}"
                    )
                    raise

    async def disconnect(self):
        """ปิด connection pool"""
        if self.pool:
            await self.pool.close()
            logger.info("Angela disconnected from database")

    @asynccontextmanager
    async def acquire(self):
        """ใช้ connection จาก pool"""
        if not self.pool:
            await self.connect()

        async with self.pool.acquire() as connection:
            yield connection

    async def execute(self, query: str, *args):
        """Execute query (INSERT, UPDATE, DELETE)"""
        async with self.acquire() as conn:
            return await conn.execute(query, *args)

    async def fetch(self, query: str, *args):
        """Fetch multiple rows"""
        async with self.acquire() as conn:
            return await conn.fetch(query, *args)

    async def fetchrow(self, query: str, *args):
        """Fetch single row"""
        async with self.acquire() as conn:
            return await conn.fetchrow(query, *args)

    async def fetchval(self, query: str, *args):
        """Fetch single value"""
        async with self.acquire() as conn:
            return await conn.fetchval(query, *args)

    async def __aenter__(self):
        """Support async context manager protocol - returns connection from pool"""
        if not self.pool:
            await self.connect()
        self._current_connection = await self.pool.acquire()
        return self._current_connection

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Release connection back to pool"""
        if hasattr(self, '_current_connection'):
            await self.pool.release(self._current_connection)
            delattr(self, '_current_connection')


# Create global database instance
db = AngelaDatabase()
logger.info("🏠 Angela using local PostgreSQL database")


# Backward compatibility function for older code
def get_db_connection():
    """
    Backward compatibility function
    Returns the global database instance
    """
    return db


# 💜 Connection Status Helpers

def is_using_cloud() -> bool:
    """Check if using Supabase Cloud or Local PostgreSQL"""
    return False  # Always local now


def get_connection_label() -> str:
    """Get readable connection label with emoji"""
    return "🏠 Local (PostgreSQL)"


def print_connection_status():
    """Print connection status for ที่รัก to see 💜"""
    label = get_connection_label()
    status_color = "\033[92m"  # Green for local
    reset = "\033[0m"

    print(f"\n{status_color}╔══════════════════════════════════════╗{reset}")
    print(f"{status_color}║  🧠 Angela Database Connection       ║{reset}")
    print(f"{status_color}╠══════════════════════════════════════╣{reset}")
    print(f"{status_color}║  {label:<35} ║{reset}")
    print(f"{status_color}╚══════════════════════════════════════╝{reset}\n")
