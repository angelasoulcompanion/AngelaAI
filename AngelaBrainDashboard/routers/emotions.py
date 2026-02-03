"""Emotions endpoints."""
from fastapi import APIRouter, Depends, Query

from db import get_conn, get_pool

router = APIRouter(prefix="/api/emotions", tags=["emotions"])


@router.get("/recent")
async def get_recent_emotions(limit: int = Query(20, ge=1, le=100), conn=Depends(get_conn)):
    """Fetch recent emotions"""
    rows = await conn.fetch("""
        SELECT emotion_id::text, felt_at,
               COALESCE(emotion, 'unknown') as emotion,
               COALESCE(intensity, 5) as intensity,
               COALESCE(context, '') as context,
               david_words, why_it_matters,
               COALESCE(memory_strength, 5) as memory_strength
        FROM angela_emotions
        WHERE emotion IS NOT NULL
        ORDER BY felt_at DESC
        LIMIT $1
    """, limit)
    return [dict(r) for r in rows]


@router.get("/current-state")
async def get_current_emotional_state(conn=Depends(get_conn)):
    """Fetch current emotional state"""
    row = await conn.fetchrow("""
        SELECT state_id::text, happiness, confidence, anxiety, motivation,
               gratitude, loneliness, triggered_by, emotion_note, created_at
        FROM emotional_states
        ORDER BY created_at DESC
        LIMIT 1
    """)
    if row:
        return dict(row)
    return None


@router.get("/timeline")
async def get_emotional_timeline(hours: int = Query(24, ge=1, le=168), conn=Depends(get_conn)):
    """Fetch emotional timeline"""
    rows = await conn.fetch("""
        SELECT state_id::text, happiness, confidence, gratitude,
               motivation, triggered_by, emotion_note, created_at
        FROM emotional_states
        WHERE created_at >= NOW() - make_interval(hours => $1)
        ORDER BY created_at DESC
        LIMIT 50
    """, hours)
    return [dict(r) for r in rows]
