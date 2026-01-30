"""David's preferences endpoints."""
from fastapi import APIRouter, Query

from db import get_pool

router = APIRouter(prefix="/api/preferences", tags=["preferences"])


@router.get("/david")
async def get_david_preferences(limit: int = Query(20, ge=1, le=200)):
    """Fetch David's preferences"""
    pool = get_pool()
    async with pool.acquire() as conn:
        rows = await conn.fetch("""
            SELECT id::text as preference_id,
                   preference_key,
                   preference_value::text,
                   confidence,
                   category as learned_from,
                   to_char(created_at AT TIME ZONE 'UTC', 'YYYY-MM-DD"T"HH24:MI:SS.MS"+00:00"') as created_at
            FROM david_preferences
            ORDER BY confidence DESC, created_at DESC
            LIMIT $1
        """, limit)
        return [dict(r) for r in rows]
