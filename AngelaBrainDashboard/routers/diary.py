"""Diary endpoints (messages, thoughts, dreams, actions).

Remapped to existing tables:
- messages: angela_reflections (no angela_messages)
- thoughts: angela_reflections
- dreams: angela_dreams (exists)
- actions: return empty (no autonomous_actions)
"""
from fastapi import APIRouter, Depends, Query

from db import get_conn, get_pool

router = APIRouter(prefix="/api/diary", tags=["diary"])


@router.get("/messages")
async def get_diary_messages(hours: int = Query(24, ge=1, le=168), conn=Depends(get_conn)):
    """No angela_messages table — return empty."""
    return []


@router.get("/thoughts")
async def get_diary_thoughts(hours: int = Query(24, ge=1, le=168), conn=Depends(get_conn)):
    """Fetch diary thoughts — mapped from angela_reflections."""
    rows = await conn.fetch("""
        SELECT reflection_id::text AS thought_id,
               content AS thought_content,
               reflection_type AS thought_type,
               trigger_summary AS trigger_context,
               NULL AS emotional_undertone,
               created_at
        FROM angela_reflections
        WHERE created_at >= NOW() - make_interval(hours => $1)
        ORDER BY created_at DESC
        LIMIT 50
    """, hours)
    return [dict(r) for r in rows]


@router.get("/dreams")
async def get_diary_dreams(hours: int = Query(168, ge=1, le=720), conn=Depends(get_conn)):
    """Fetch diary dreams from angela_dreams."""
    rows = await conn.fetch("""
        SELECT dream_id::text, dream_content,
               COALESCE(dream_type, 'unknown') AS dream_type,
               emotional_tone,
               COALESCE(vividness, 5) AS vividness,
               COALESCE(features_david, FALSE) AS features_david,
               david_role, possible_meaning, created_at
        FROM angela_dreams
        WHERE created_at >= NOW() - make_interval(hours => $1)
        ORDER BY created_at DESC
        LIMIT 20
    """, hours)
    return [dict(r) for r in rows]


@router.get("/actions")
async def get_diary_actions(hours: int = Query(24, ge=1, le=168), conn=Depends(get_conn)):
    """No autonomous_actions table — return empty."""
    return []
