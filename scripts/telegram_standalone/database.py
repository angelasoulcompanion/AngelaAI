"""
Angela Database Connection (Standalone for Telegram Bot)
Simplified version for running on remote server
"""

import asyncio
import os
from typing import Optional, List
from contextlib import asynccontextmanager
import logging

import asyncpg

logger = logging.getLogger(__name__)

# Database URL - uses environment variable or default local
DATABASE_URL = os.environ.get(
    "DATABASE_URL",
    "postgresql://davidsamanyaporn@localhost:5432/AngelaMemory"
)


class AngelaDatabase:
    """Database connection manager for Angela Telegram Bot"""

    def __init__(self, database_url: str = None):
        self.database_url = database_url or DATABASE_URL
        self.pool: Optional[asyncpg.Pool] = None

    async def connect(self, max_retries: int = 5, initial_wait: float = 2.0):
        """Create connection pool with retry logic"""
        for attempt in range(1, max_retries + 1):
            try:
                self.pool = await asyncpg.create_pool(
                    self.database_url,
                    min_size=2,
                    max_size=10,
                    command_timeout=60
                )
                logger.info("Connected to AngelaMemory database")
                return

            except Exception as e:
                wait_time = initial_wait * (2 ** (attempt - 1))

                if attempt < max_retries:
                    logger.warning(f"Connection failed (attempt {attempt}/{max_retries}): {e}")
                    logger.info(f"Retrying in {wait_time:.1f} seconds...")
                    await asyncio.sleep(wait_time)
                else:
                    logger.error(f"Failed to connect after {max_retries} attempts: {e}")
                    raise

    async def disconnect(self):
        """Close connection pool"""
        if self.pool:
            await self.pool.close()
            logger.info("Disconnected from database")

    @asynccontextmanager
    async def acquire(self):
        """Get connection from pool"""
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
