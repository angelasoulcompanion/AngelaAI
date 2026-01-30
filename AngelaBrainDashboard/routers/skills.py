"""Skills endpoints."""
from fastapi import APIRouter, Query

from db import get_pool

router = APIRouter(prefix="/api/skills", tags=["skills"])


@router.get("/all")
async def get_all_skills():
    """Fetch all skills"""
    pool = get_pool()
    async with pool.acquire() as conn:
        rows = await conn.fetch("""
            SELECT skill_id::text, skill_name, category, proficiency_level,
                   proficiency_score, description,
                   first_demonstrated_at, last_used_at,
                   usage_count, evidence_count, created_at, updated_at
            FROM angela_skills
            ORDER BY proficiency_score DESC
        """)
        return [dict(r) for r in rows]


@router.get("/by-category")
async def get_skills_by_category():
    """Fetch skills grouped by category"""
    pool = get_pool()
    async with pool.acquire() as conn:
        rows = await conn.fetch("""
            SELECT skill_id::text, skill_name, category, proficiency_level,
                   proficiency_score, description,
                   first_demonstrated_at, last_used_at,
                   usage_count, evidence_count, created_at, updated_at
            FROM angela_skills
            ORDER BY category, proficiency_score DESC
        """)

        grouped = {}
        for r in rows:
            category = r['category'] or 'uncategorized'
            if category not in grouped:
                grouped[category] = []
            grouped[category].append(dict(r))

        return grouped


@router.get("/statistics")
async def get_skill_statistics():
    """Fetch skill statistics"""
    pool = get_pool()
    async with pool.acquire() as conn:
        row = await conn.fetchrow("""
            SELECT
                COUNT(*) as total_skills,
                COUNT(CASE WHEN proficiency_level = 'expert' THEN 1 END) as expert_count,
                COUNT(CASE WHEN proficiency_level = 'advanced' THEN 1 END) as advanced_count,
                COUNT(CASE WHEN proficiency_level = 'intermediate' THEN 1 END) as intermediate_count,
                COUNT(CASE WHEN proficiency_level = 'beginner' THEN 1 END) as beginner_count,
                COALESCE(AVG(proficiency_score), 0) as avg_score,
                COALESCE(SUM(evidence_count), 0) as total_evidence,
                COALESCE(SUM(usage_count), 0) as total_usage
            FROM angela_skills
        """)
        return {
            "total_skills": row['total_skills'] or 0,
            "expert_count": row['expert_count'] or 0,
            "advanced_count": row['advanced_count'] or 0,
            "intermediate_count": row['intermediate_count'] or 0,
            "beginner_count": row['beginner_count'] or 0,
            "avg_score": float(row['avg_score'] or 0),
            "total_evidence": row['total_evidence'] or 0,
            "total_usage": row['total_usage'] or 0
        }


@router.get("/growth")
async def get_recent_skill_growth(days: int = Query(7, ge=1, le=30)):
    """Fetch recent skill growth logs"""
    pool = get_pool()
    async with pool.acquire() as conn:
        rows = await conn.fetch("""
            SELECT
                g.log_id::text, g.skill_id::text,
                g.old_proficiency_level, g.new_proficiency_level,
                g.old_score, g.new_score, g.growth_reason,
                g.evidence_count_at_change, g.changed_at
            FROM skill_growth_log g
            WHERE g.changed_at >= CURRENT_TIMESTAMP - make_interval(days => $1)
            ORDER BY g.changed_at DESC
        """, days)
        return [dict(r) for r in rows]
