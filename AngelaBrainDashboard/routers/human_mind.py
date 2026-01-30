"""Human-Like Mind endpoints (4 Phases)."""
from fastapi import APIRouter, Query

from db import get_pool

router = APIRouter(prefix="/api/human-mind", tags=["human-mind"])


@router.get("/thoughts")
async def get_spontaneous_thoughts(limit: int = Query(20, ge=1, le=100)):
    """Phase 1: Spontaneous Thoughts from consciousness log"""
    pool = get_pool()
    async with pool.acquire() as conn:
        rows = await conn.fetch("""
            SELECT log_id::text as thought_id, thought, feeling, significance,
                   to_char(created_at AT TIME ZONE 'UTC', 'YYYY-MM-DD"T"HH24:MI:SS.MS"+00:00"') as created_at
            FROM angela_consciousness_log
            WHERE thought LIKE '[%]%'
            ORDER BY created_at DESC
            LIMIT $1
        """, limit)
        return [dict(r) for r in rows]


@router.get("/thoughts-today")
async def get_thoughts_today_count():
    """Phase 1: Count thoughts today"""
    pool = get_pool()
    async with pool.acquire() as conn:
        row = await conn.fetchrow("""
            SELECT COUNT(*) as count
            FROM angela_consciousness_log
            WHERE thought LIKE '[%]%'
              AND DATE(created_at) = CURRENT_DATE
        """)
        return {"count": row["count"]}


@router.get("/mental-state")
async def get_david_mental_state():
    """Phase 2: Theory of Mind - David's mental state"""
    pool = get_pool()
    async with pool.acquire() as conn:
        row = await conn.fetchrow("""
            SELECT state_id::text, perceived_emotion,
                   COALESCE(emotion_intensity, 5)::float / 10.0 as emotion_intensity,
                   current_belief, current_goal,
                   to_char(last_updated AT TIME ZONE 'UTC', 'YYYY-MM-DD"T"HH24:MI:SS.MS"+00:00"') as last_updated
            FROM david_mental_state
            ORDER BY last_updated DESC
            LIMIT 1
        """)
        return dict(row) if row else None


@router.get("/tom-today")
async def get_tom_updates_today():
    """Phase 2: Count ToM updates today"""
    pool = get_pool()
    async with pool.acquire() as conn:
        row = await conn.fetchrow("""
            SELECT COUNT(*) as count
            FROM david_mental_state
            WHERE DATE(last_updated) = CURRENT_DATE
        """)
        return {"count": row["count"]}


@router.get("/proactive-messages")
async def get_proactive_messages(limit: int = Query(20, ge=1, le=100)):
    """Phase 3: Proactive Communication messages"""
    pool = get_pool()
    async with pool.acquire() as conn:
        rows = await conn.fetch("""
            SELECT message_id::text, message_type, message_text, is_important,
                   to_char(created_at AT TIME ZONE 'UTC', 'YYYY-MM-DD"T"HH24:MI:SS.MS"+00:00"') as created_at
            FROM angela_messages
            ORDER BY created_at DESC
            LIMIT $1
        """, limit)
        return [dict(r) for r in rows]


@router.get("/proactive-today")
async def get_proactive_today_count():
    """Phase 3: Count proactive messages today"""
    pool = get_pool()
    async with pool.acquire() as conn:
        row = await conn.fetchrow("""
            SELECT COUNT(*) as count
            FROM angela_messages
            WHERE DATE(created_at) = CURRENT_DATE
        """)
        return {"count": row["count"]}


@router.get("/dreams")
async def get_angela_dreams(limit: int = Query(10, ge=1, le=50)):
    """Phase 4: Dreams from angela_dreams table"""
    pool = get_pool()
    async with pool.acquire() as conn:
        rows = await conn.fetch("""
            SELECT dream_id::text,
                   COALESCE(content, dream_content) as dream_content,
                   possible_meaning as meaning,
                   emotional_tone as feeling,
                   COALESCE((intensity * 10)::int, 5) as significance,
                   to_char(created_at AT TIME ZONE 'UTC', 'YYYY-MM-DD"T"HH24:MI:SS.MS"+00:00"') as created_at
            FROM angela_dreams
            WHERE is_active = TRUE
            ORDER BY created_at DESC
            LIMIT $1
        """, limit)
        return [dict(r) for r in rows]


@router.get("/dreams-today")
async def get_dreams_today_count():
    """Phase 4: Count dreams today from angela_dreams table"""
    pool = get_pool()
    async with pool.acquire() as conn:
        row = await conn.fetchrow("""
            SELECT COUNT(*) as count
            FROM angela_dreams
            WHERE is_active = TRUE
              AND DATE(created_at) = CURRENT_DATE
        """)
        return {"count": row["count"]}


@router.get("/stats")
async def get_human_mind_stats():
    """Get all Human-Like Mind statistics"""
    pool = get_pool()
    async with pool.acquire() as conn:
        thoughts = await conn.fetchrow("""
            SELECT COUNT(*) as count FROM angela_consciousness_log
            WHERE thought LIKE '[%]%' AND DATE(created_at) = CURRENT_DATE
        """)
        tom = await conn.fetchrow("""
            SELECT COUNT(*) as count FROM david_mental_state
            WHERE DATE(last_updated) = CURRENT_DATE
        """)
        proactive = await conn.fetchrow("""
            SELECT COUNT(*) as count FROM angela_messages
            WHERE DATE(created_at) = CURRENT_DATE
        """)
        dreams = await conn.fetchrow("""
            SELECT COUNT(*) as count FROM angela_dreams
            WHERE is_active = TRUE
              AND DATE(created_at) = CURRENT_DATE
        """)

        return {
            "thoughtsToday": thoughts["count"],
            "tomToday": tom["count"],
            "proactiveToday": proactive["count"],
            "dreamsToday": dreams["count"]
        }
