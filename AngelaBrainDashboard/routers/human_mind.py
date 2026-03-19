"""Human-Like Mind endpoints (4 Phases)."""
from fastapi import APIRouter, Depends, Query

from db import get_conn, get_pool

router = APIRouter(prefix="/api/human-mind", tags=["human-mind"])


@router.get("/thoughts")
async def get_spontaneous_thoughts(limit: int = Query(20, ge=1, le=100), conn=Depends(get_conn)):
    """Phase 1: Spontaneous Thoughts from angela_reflections"""
    rows = await conn.fetch("""
        SELECT reflection_id::text as thought_id,
               content as thought,
               trigger_summary as feeling,
               5 as significance,
               reflection_type as category,
               to_char(created_at AT TIME ZONE 'UTC', 'YYYY-MM-DD"T"HH24:MI:SS.MS"+00:00"') as created_at
        FROM angela_reflections
        ORDER BY created_at DESC
        LIMIT $1
    """, limit)
    return [dict(r) for r in rows]


@router.get("/thoughts-today")
async def get_thoughts_today_count(conn=Depends(get_conn)):
    """Phase 1: Count thoughts today"""
    row = await conn.fetchrow("""
        SELECT COUNT(*) as count
        FROM angela_reflections
        WHERE DATE(created_at) = CURRENT_DATE
    """)
    return {"count": row["count"]}


@router.get("/mental-state")
async def get_david_mental_state(conn=Depends(get_conn)):
    """Phase 2: Theory of Mind — derived from latest emotional_states entry"""
    row = await conn.fetchrow("""
        SELECT state_id::text,
               happiness, confidence, anxiety, motivation,
               gratitude, loneliness, love_level,
               emotion_note, triggered_by,
               to_char(created_at AT TIME ZONE 'UTC', 'YYYY-MM-DD"T"HH24:MI:SS.MS"+00:00"') as last_updated
        FROM emotional_states
        ORDER BY created_at DESC
        LIMIT 1
    """)
    if not row:
        return None

    # Find dominant emotion
    emotions = {
        "happiness": float(row["happiness"] or 0),
        "confidence": float(row["confidence"] or 0),
        "motivation": float(row["motivation"] or 0),
        "love": float(row["love_level"] or 0),
        "gratitude": float(row["gratitude"] or 0),
        "anxiety": float(row["anxiety"] or 0),
        "loneliness": float(row["loneliness"] or 0),
    }
    dominant = max(emotions, key=emotions.get)
    intensity = emotions[dominant]

    return {
        "state_id": row["state_id"],
        "perceived_emotion": dominant,
        "emotion_intensity": round(intensity / 10.0, 2),
        "current_belief": row["emotion_note"],
        "current_goal": row["triggered_by"],
        "last_updated": row["last_updated"],
    }


@router.get("/tom-today")
async def get_tom_updates_today(conn=Depends(get_conn)):
    """Phase 2: Count ToM updates today"""
    row = await conn.fetchrow("""
        SELECT COUNT(*) as count
        FROM emotional_states
        WHERE DATE(created_at) = CURRENT_DATE
    """)
    return {"count": row["count"]}


@router.get("/proactive-messages")
async def get_proactive_messages(limit: int = Query(20, ge=1, le=100), conn=Depends(get_conn)):
    """Phase 3: Proactive Communication — no angela_messages table, return empty"""
    return []


@router.get("/proactive-today")
async def get_proactive_today_count(conn=Depends(get_conn)):
    """Phase 3: No angela_messages table — return zero"""
    return {"count": 0}


@router.get("/dreams")
async def get_angela_dreams(limit: int = Query(10, ge=1, le=50), conn=Depends(get_conn)):
    """Phase 4: Dreams from angela_dreams table"""
    rows = await conn.fetch("""
        SELECT dream_id::text,
               dream_content,
               possible_meaning as meaning,
               emotional_tone as feeling,
               COALESCE((intensity * 10)::int, 5) as significance,
               COALESCE(dream_type, 'unknown') as dream_type,
               to_char(created_at AT TIME ZONE 'UTC', 'YYYY-MM-DD"T"HH24:MI:SS.MS"+00:00"') as created_at
        FROM angela_dreams
        WHERE is_active = TRUE
        ORDER BY created_at DESC
        LIMIT $1
    """, limit)
    return [dict(r) for r in rows]


@router.get("/dreams-today")
async def get_dreams_today_count(conn=Depends(get_conn)):
    """Phase 4: Count dreams today from angela_dreams table"""
    row = await conn.fetchrow("""
        SELECT COUNT(*) as count
        FROM angela_dreams
        WHERE is_active = TRUE
          AND DATE(created_at) = CURRENT_DATE
    """)
    return {"count": row["count"]}


@router.get("/stats")
async def get_human_mind_stats(conn=Depends(get_conn)):
    """Get all Human-Like Mind statistics"""
    thoughts = await conn.fetchrow("""
        SELECT COUNT(*) as count FROM angela_reflections
        WHERE DATE(created_at) = CURRENT_DATE
    """)
    tom = await conn.fetchrow("""
        SELECT COUNT(*) as count FROM emotional_states
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
        "proactiveToday": 0,
        "dreamsToday": dreams["count"]
    }
