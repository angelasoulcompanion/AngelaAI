"""
Database pool + lifecycle management for Angela Brain Dashboard API.
"""
import sys
from typing import Optional

import asyncpg

DATABASE_URL = "postgresql://neondb_owner:npg_mXbQ5jKhN3zt@ep-withered-bush-a164h0b8-pooler.ap-southeast-1.aws.neon.tech/neondb?sslmode=require"

pool: Optional[asyncpg.Pool] = None


async def startup() -> None:
    """Create connection pool and run migrations."""
    global pool
    try:
        pool = await asyncpg.create_pool(
            DATABASE_URL,
            min_size=2,
            max_size=10,
            command_timeout=60
        )
        print("✅ Connected to Neon Cloud (Singapore)")

        # Run migrations
        async with pool.acquire() as conn:
            await conn.execute("""
                ALTER TABLE meeting_notes
                ADD COLUMN IF NOT EXISTS calendar_event_id TEXT
            """)
            # Self-learning: add source column to learnings table
            await conn.execute("""
                ALTER TABLE learnings
                ADD COLUMN IF NOT EXISTS source VARCHAR(50) DEFAULT NULL
            """)
    except Exception as e:
        print(f"❌ Failed to connect to database: {e}")
        sys.exit(1)


async def shutdown() -> None:
    """Close connection pool."""
    global pool
    if pool:
        await pool.close()
        print("🛑 Database connection closed")


def get_pool() -> asyncpg.Pool:
    """Return the global connection pool. Raises if not initialized."""
    if pool is None:
        raise RuntimeError("Database pool not initialized. Call startup() first.")
    return pool
