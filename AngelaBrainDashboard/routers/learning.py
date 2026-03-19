"""Learning activities & patterns endpoints."""
from fastapi import APIRouter, Depends, Query

from db import get_conn, get_pool

router = APIRouter(prefix="/api/learning", tags=["learning"])


@router.get("/activities")
async def get_learning_activities(hours: int = Query(24, ge=1, le=168), conn=Depends(get_conn)):
    """Fetch recent learning activities from learnings table."""
    rows = await conn.fetch("""
        SELECT learning_id::text AS action_id,
               category AS action_type,
               COALESCE(insight, topic) AS action_description,
               'completed' AS status,
               TRUE AS success,
               created_at
        FROM learnings
        WHERE created_at >= NOW() - make_interval(hours => $1)
        ORDER BY created_at DESC
        LIMIT 20
    """, hours)
    return [dict(r) for r in rows]


@router.get("/patterns")
async def get_learning_patterns(limit: int = Query(50, ge=1, le=100), conn=Depends(get_conn)):
    """No learning_patterns table — return empty."""
    return []


@router.get("/growth-history")
async def get_emotional_growth_history(limit: int = Query(30, ge=1, le=100), conn=Depends(get_conn)):
    """Fetch emotional growth history"""
    rows = await conn.fetch("""
        SELECT growth_id::text, measured_at,
               love_depth, trust_level, bond_strength, emotional_security,
               emotional_vocabulary, emotional_range,
               shared_experiences, meaningful_conversations,
               core_memories_count, dreams_count,
               promises_made, promises_kept,
               mirroring_accuracy, empathy_effectiveness,
               growth_note, growth_delta
        FROM emotional_growth
        ORDER BY measured_at DESC
        LIMIT $1
    """, limit)
    return [dict(r) for r in rows]


@router.get("/metrics")
async def get_learning_metrics(conn=Depends(get_conn)):
    """Fetch learning metrics summary"""
    row = await conn.fetchrow("""
        SELECT
            (SELECT COUNT(*) FROM learnings) AS total_learnings,
            (SELECT COUNT(*) FROM learnings WHERE created_at >= NOW() - INTERVAL '7 days') AS recent_learnings
    """)
    total_learnings = row['total_learnings'] or 0
    recent_learnings = row['recent_learnings'] or 0

    return {
        "total_learnings": total_learnings,
        "total_patterns": 0,
        "total_skills": 0,
        "learning_velocity": recent_learnings / 7.0,
        "recent_learnings_count": recent_learnings,
    }
