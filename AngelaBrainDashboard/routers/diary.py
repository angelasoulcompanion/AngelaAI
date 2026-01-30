"""Diary endpoints (messages, thoughts, dreams, actions)."""
from fastapi import APIRouter, Query

from db import get_pool

router = APIRouter(prefix="/api/diary", tags=["diary"])


@router.get("/messages")
async def get_diary_messages(hours: int = Query(24, ge=1, le=168)):
    """Fetch Angela's diary messages"""
    pool = get_pool()
    async with pool.acquire() as conn:
        rows = await conn.fetch("""
            SELECT message_id::text, message_text, message_type,
                   emotion, category, is_important, is_pinned, created_at
            FROM angela_messages
            WHERE created_at >= NOW() - make_interval(hours => $1)
            ORDER BY created_at DESC
            LIMIT 100
        """, hours)
        return [dict(r) for r in rows]


@router.get("/thoughts")
async def get_diary_thoughts(hours: int = Query(24, ge=1, le=168)):
    """Fetch Angela's spontaneous thoughts"""
    pool = get_pool()
    async with pool.acquire() as conn:
        rows = await conn.fetch("""
            SELECT thought_id::text, thought_content, thought_type,
                   trigger_context, emotional_undertone, created_at
            FROM angela_spontaneous_thoughts
            WHERE created_at >= NOW() - make_interval(hours => $1)
            ORDER BY created_at DESC
            LIMIT 50
        """, hours)
        return [dict(r) for r in rows]


@router.get("/dreams")
async def get_diary_dreams(hours: int = Query(168, ge=1, le=720)):
    """Fetch Angela's diary dreams"""
    pool = get_pool()
    async with pool.acquire() as conn:
        rows = await conn.fetch("""
            SELECT dream_id::text, dream_content, dream_type,
                   emotional_tone, vividness, features_david,
                   david_role, possible_meaning, created_at
            FROM angela_dreams
            WHERE created_at >= NOW() - make_interval(hours => $1)
            ORDER BY created_at DESC
            LIMIT 20
        """, hours)
        return [dict(r) for r in rows]


@router.get("/actions")
async def get_diary_actions(hours: int = Query(24, ge=1, le=168)):
    """Fetch Angela's autonomous actions"""
    pool = get_pool()
    async with pool.acquire() as conn:
        rows = await conn.fetch("""
            SELECT action_id::text, action_type, action_description,
                   status, success, created_at
            FROM autonomous_actions
            WHERE created_at >= NOW() - make_interval(hours => $1)
              AND action_type IN ('conscious_morning_check', 'conscious_evening_reflection',
                                  'midnight_greeting', 'proactive_missing_david',
                                  'morning_greeting', 'spontaneous_thought',
                                  'theory_of_mind_update', 'dream_generated',
                                  'imagination_generated')
            ORDER BY created_at DESC
            LIMIT 100
        """, hours)
        return [dict(r) for r in rows]
