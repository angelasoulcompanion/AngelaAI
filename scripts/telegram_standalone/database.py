"""
Angela Database Connection (Standalone for Telegram Bot)
Simplified version for running on remote server

Updated: 2026-01-05 - Uses Neon Cloud as primary
"""

import asyncio
import os
import sys
from typing import Optional, List
from contextlib import asynccontextmanager
import logging

import asyncpg

logger = logging.getLogger(__name__)

# Try to import from main angela_core config
try:
    sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
    from config import NEON_DATABASE_URL, ANGELA_MACHINE
    USE_MAIN_CONFIG = True
except ImportError:
    NEON_DATABASE_URL = ""
    ANGELA_MACHINE = "unknown"
    USE_MAIN_CONFIG = False

# Database URL priority:
# 1. NEON_DATABASE_URL from config/local_settings.py
# 2. DATABASE_URL environment variable
# 3. Local fallback
DATABASE_URL = (
    NEON_DATABASE_URL or
    os.environ.get("DATABASE_URL") or
    os.environ.get("NEON_DATABASE_URL") or
    "postgresql://davidsamanyaporn@localhost:5432/AngelaMemory"
)

# Local database URL (for secrets only)
LOCAL_DATABASE_URL = "postgresql://davidsamanyaporn@localhost:5432/AngelaMemory"

# Determine if using Neon
USE_NEON = "neon.tech" in DATABASE_URL


class AngelaDatabase:
    """Database connection manager for Angela Telegram Bot"""

    def __init__(self, database_url: str = None):
        self.database_url = database_url or DATABASE_URL
        self.pool: Optional[asyncpg.Pool] = None
        self.is_neon = "neon.tech" in self.database_url

    async def connect(self, max_retries: int = 5, initial_wait: float = 2.0):
        """Create connection pool with retry logic"""
        db_label = "☁️ Neon Cloud" if self.is_neon else "🏠 Local PostgreSQL"

        for attempt in range(1, max_retries + 1):
            try:
                self.pool = await asyncpg.create_pool(
                    self.database_url,
                    min_size=2,
                    max_size=10,
                    command_timeout=60,
                    ssl='require' if self.is_neon else None
                )
                logger.info(f"Connected to {db_label}")
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


# Global database instance (connects to Neon by default)
db = AngelaDatabase()


# Local database for secrets
class LocalDatabase:
    """Local PostgreSQL for secrets only"""

    def __init__(self):
        self.pool: Optional[asyncpg.Pool] = None

    async def connect(self):
        if not self.pool:
            self.pool = await asyncpg.create_pool(
                LOCAL_DATABASE_URL,
                min_size=1,
                max_size=3,
                command_timeout=30
            )

    async def fetchrow(self, query: str, *args):
        await self.connect()
        async with self.pool.acquire() as conn:
            return await conn.fetchrow(query, *args)


local_db = LocalDatabase()


async def get_secret(secret_name: str) -> Optional[str]:
    """Get secret from local our_secrets table"""
    try:
        result = await local_db.fetchrow(
            'SELECT secret_value FROM our_secrets WHERE secret_name = $1',
            secret_name
        )
        return result['secret_value'] if result else None
    except Exception as e:
        logger.error(f"Error getting secret: {e}")
        return None
