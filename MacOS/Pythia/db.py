"""
Database pool + lifecycle management for Pythia API.
Connects to Neon Cloud — Pythia database (Singapore).
"""
import os
import sys
from typing import AsyncGenerator, Optional

import asyncpg

# Pythia Neon database URL (set via env or fallback)
DATABASE_URL = os.environ.get(
    "PYTHIA_DATABASE_URL",
    "postgresql://neondb_owner:npg_mXbQ5jKhN3zt@ep-withered-bush-a164h0b8-pooler.ap-southeast-1.aws.neon.tech/pythia?sslmode=require"
)

pool: Optional[asyncpg.Pool] = None


async def startup() -> None:
    """Create connection pool on app startup."""
    global pool
    try:
        pool = await asyncpg.create_pool(
            DATABASE_URL,
            min_size=2,
            max_size=10,
            command_timeout=60
        )
        print("✅ Connected to Neon Cloud — Pythia (Singapore)")

        # Run lightweight migrations
        async with pool.acquire() as conn:
            # Ensure watchlist table exists (convenience migration)
            await conn.execute("""
                CREATE TABLE IF NOT EXISTS watchlists (
                    watchlist_id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
                    name VARCHAR(100) NOT NULL,
                    description TEXT,
                    is_active BOOLEAN DEFAULT true,
                    created_at TIMESTAMPTZ DEFAULT NOW(),
                    updated_at TIMESTAMPTZ DEFAULT NOW()
                )
            """)
            await conn.execute("""
                CREATE TABLE IF NOT EXISTS watchlist_items (
                    item_id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
                    watchlist_id UUID NOT NULL REFERENCES watchlists(watchlist_id) ON DELETE CASCADE,
                    asset_id UUID NOT NULL REFERENCES assets(asset_id) ON DELETE CASCADE,
                    added_at TIMESTAMPTZ DEFAULT NOW(),
                    notes TEXT,
                    CONSTRAINT unique_watchlist_asset UNIQUE (watchlist_id, asset_id)
                )
            """)
    except Exception as e:
        print(f"❌ Failed to connect to Pythia database: {e}")
        sys.exit(1)


async def shutdown() -> None:
    """Close connection pool on app shutdown."""
    global pool
    if pool:
        await pool.close()
        print("🛑 Pythia database connection closed")


def get_pool() -> asyncpg.Pool:
    """Return the global connection pool. Raises if not initialized."""
    if pool is None:
        raise RuntimeError("Database pool not initialized. Call startup() first.")
    return pool


async def get_conn() -> AsyncGenerator[asyncpg.Connection, None]:
    """FastAPI dependency that yields a connection from the pool."""
    p = get_pool()
    async with p.acquire() as conn:
        yield conn
