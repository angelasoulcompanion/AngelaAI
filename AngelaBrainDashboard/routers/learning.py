"""Learning activities & patterns endpoints."""
from fastapi import APIRouter, Depends, Query

from db import get_conn, get_pool

router = APIRouter(prefix="/api/learning", tags=["learning"])


@router.get("/activities")
async def get_learning_activities(hours: int = Query(24, ge=1, le=168), conn=Depends(get_conn)):
    """Fetch recent learning activities"""
    rows = await conn.fetch("""
        SELECT action_id::text, action_type, action_description, status, success, created_at
        FROM autonomous_actions
        WHERE created_at >= NOW() - make_interval(hours => $1)
          AND (action_type LIKE '%learning%'
               OR action_type LIKE '%subconscious%'
               OR action_type LIKE '%consolidation%'
               OR action_type LIKE '%pattern%')
        ORDER BY created_at DESC
        LIMIT 20
    """, hours)
    return [dict(r) for r in rows]


@router.get("/patterns")
async def get_learning_patterns(limit: int = Query(50, ge=1, le=100), conn=Depends(get_conn)):
    """Fetch learning patterns"""
    rows = await conn.fetch("""
        SELECT id::text, pattern_type, description,
               confidence_score, occurrence_count,
               first_observed, last_observed
        FROM learning_patterns
        ORDER BY confidence_score DESC, occurrence_count DESC
        LIMIT $1
    """, limit)
    return [dict(r) for r in rows]


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
            (SELECT COUNT(*) FROM learnings) as total_learnings,
            (SELECT COUNT(*) FROM learning_patterns) as total_patterns,
            (SELECT COUNT(*) FROM angela_skills) as total_skills,
            (SELECT COUNT(*) FROM learnings WHERE created_at >= NOW() - INTERVAL '7 days') as recent_learnings
    """)
    total_learnings = row['total_learnings'] or 0
    total_patterns = row['total_patterns'] or 0
    total_skills = row['total_skills'] or 0
    recent_learnings = row['recent_learnings'] or 0
    velocity = recent_learnings / 7.0

    return {
        "total_learnings": total_learnings,
        "total_patterns": total_patterns,
        "total_skills": total_skills,
        "learning_velocity": velocity,
        "recent_learnings_count": recent_learnings
    }
