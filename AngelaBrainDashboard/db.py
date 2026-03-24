"""
Database pool + lifecycle management for Angela Brain Dashboard API.
"""
import sys
from pathlib import Path
from typing import AsyncGenerator, Optional

import asyncpg

# Add AngelaAI root to sys.path for config imports
_angela_root = str(Path(__file__).resolve().parents[1])
if _angela_root not in sys.path:
    sys.path.insert(0, _angela_root)

from config.db_url import get_supabase_url

DATABASE_URL = get_supabase_url()

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
        print("✅ Connected to Supabase (Tokyo)")

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
            # DJ Angela: source column for angela_songs
            await conn.execute("ALTER TABLE angela_songs ADD COLUMN IF NOT EXISTS source VARCHAR(50) DEFAULT 'dj_angela'")

            # DJ Angela: Music listening history (play tracking + learning)
            await conn.execute("""
                CREATE TABLE IF NOT EXISTS music_listening_history (
                    listen_id        UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
                    title            VARCHAR(255) NOT NULL,
                    artist           VARCHAR(255),
                    album            VARCHAR(255),
                    apple_music_id   VARCHAR(100),
                    source_tab       VARCHAR(30),
                    started_at       TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
                    ended_at         TIMESTAMP,
                    duration_seconds NUMERIC,
                    listened_seconds NUMERIC,
                    play_status      VARCHAR(20) DEFAULT 'started',
                    mood_at_play     VARCHAR(50),
                    emotion_scores   JSONB,
                    occasion         VARCHAR(50),
                    generated_insight BOOLEAN DEFAULT FALSE
                )
            """)
            await conn.execute("""
                CREATE INDEX IF NOT EXISTS idx_mlh_started
                ON music_listening_history(started_at DESC)
            """)
            await conn.execute("""
                CREATE INDEX IF NOT EXISTS idx_mlh_title_artist
                ON music_listening_history(title, artist)
            """)
            await conn.execute("""
                CREATE INDEX IF NOT EXISTS idx_mlh_mood
                ON music_listening_history(mood_at_play)
            """)
            # DJ Angela: Wine-to-Music pairing
            await conn.execute("ALTER TABLE music_listening_history ADD COLUMN IF NOT EXISTS wine_type VARCHAR(50)")

            # DJ Angela: Wine reaction feedback (thumbs up/down/love)
            await conn.execute("""
                CREATE TABLE IF NOT EXISTS wine_reactions (
                    reaction_id  UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
                    wine_type    VARCHAR(50) NOT NULL,
                    reaction     VARCHAR(10) NOT NULL,
                    target_type  VARCHAR(20) NOT NULL,
                    song_title   VARCHAR(255),
                    song_artist  VARCHAR(255),
                    created_at   TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
                )
            """)
            await conn.execute("""
                CREATE INDEX IF NOT EXISTS idx_wr_wine
                ON wine_reactions(wine_type)
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


async def get_conn() -> AsyncGenerator[asyncpg.Connection, None]:
    """FastAPI dependency that yields a connection from the pool."""
    p = get_pool()
    async with p.acquire() as conn:
        yield conn
