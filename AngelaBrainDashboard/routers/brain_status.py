"""Brain Status metrics endpoint — comprehensive brain-based architecture dashboard.

Most tables (angela_stimuli, angela_thoughts, thought_expression_log,
brain_vs_rule_comparison, companion_patterns, memory_consolidation_log)
have been removed. Only angela_reflections remains.
"""
import asyncio

from fastapi import APIRouter

from db import get_pool

router = APIRouter(prefix="/api/brain-status", tags=["brain-status"])


async def _fetch_stimuli_summary(pool) -> dict:
    """No angela_stimuli table — return zeroed."""
    return {
        "total_24h": 0,
        "total_7d": 0,
        "avg_salience": 0.0,
        "high_salience": 0,
        "by_type": [],
        "top_salient": [],
        "salience_dims": {
            "novelty": 0.0,
            "emotional": 0.0,
            "goal_relevance": 0.0,
            "temporal_urgency": 0.0,
            "social_relevance": 0.0,
        },
    }


async def _fetch_thoughts_summary(pool) -> dict:
    """No angela_thoughts table — use angela_reflections as proxy."""
    async with pool.acquire() as conn:
        counts = await conn.fetchrow("""
            SELECT
                COUNT(*) FILTER (WHERE created_at >= NOW() - INTERVAL '24 hours') AS total_24h,
                COUNT(*) FILTER (WHERE created_at >= NOW() - INTERVAL '7 days') AS total_7d
            FROM angela_reflections
        """)

        top_rows = await conn.fetch("""
            SELECT reflection_id::text AS thought_id, reflection_type AS thought_type,
                   content, COALESCE(importance_sum, 0) AS motivation_score,
                   status AS expressed_via, created_at
            FROM angela_reflections
            WHERE created_at >= NOW() - INTERVAL '7 days'
            ORDER BY importance_sum DESC NULLS LAST
            LIMIT 5
        """)

    return {
        "total_24h": counts["total_24h"] or 0,
        "total_7d": counts["total_7d"] or 0,
        "system1": 0,
        "system2": counts["total_7d"] or 0,
        "avg_motivation": 0.0,
        "high_motivation": 0,
        "top_thoughts": [
            {
                "id": r["thought_id"],
                "type": r["thought_type"],
                "template": None,
                "content": (r["content"] or "")[:150],
                "motivation": round(float(r["motivation_score"] or 0), 3),
                "expressed_via": r["expressed_via"],
                "created_at": r["created_at"].isoformat() if r["created_at"] else None,
            }
            for r in top_rows
        ],
    }


async def _fetch_expression_summary(pool) -> dict:
    """No thought_expression_log — return zeroed."""
    return {
        "generated": 0,
        "total_expressed": 0,
        "telegram_count": 0,
        "chat_count": 0,
        "suppressed_count": 0,
        "suppress_reasons": {},
        "effectiveness_avg": 0.0,
        "david_responses": {"positive": 0, "neutral": 0, "negative": 0},
    }


async def _fetch_reflections_summary(pool) -> dict:
    """Reflections: 7d counts, by type, recent 5 reflections."""
    async with pool.acquire() as conn:
        counts = await conn.fetchrow("""
            SELECT
                COUNT(*) AS total_7d,
                COUNT(*) FILTER (WHERE status = 'integrated') AS integrated
            FROM angela_reflections
            WHERE created_at >= NOW() - INTERVAL '7 days'
        """)

        by_type_rows = await conn.fetch("""
            SELECT reflection_type, COUNT(*) AS cnt
            FROM angela_reflections
            WHERE created_at >= NOW() - INTERVAL '7 days'
            GROUP BY reflection_type
            ORDER BY cnt DESC
        """)

        recent_rows = await conn.fetch("""
            SELECT reflection_id::text, reflection_type, depth_level,
                   content, status, importance_sum, created_at
            FROM angela_reflections
            WHERE created_at >= NOW() - INTERVAL '7 days'
            ORDER BY created_at DESC
            LIMIT 5
        """)

    return {
        "total_7d": counts["total_7d"] or 0,
        "integrated_count": counts["integrated"] or 0,
        "by_type": {r["reflection_type"]: r["cnt"] for r in by_type_rows},
        "recent": [
            {
                "id": r["reflection_id"],
                "type": r["reflection_type"],
                "depth": r["depth_level"],
                "content": (r["content"] or "")[:200],
                "status": r["status"],
                "importance_sum": round(float(r["importance_sum"] or 0), 1),
                "created_at": r["created_at"].isoformat() if r["created_at"] else None,
            }
            for r in recent_rows
        ],
    }


async def _fetch_migration_summary(pool) -> dict:
    """No brain_vs_rule_comparison — return zeroed."""
    return {
        "brain_wins": 0,
        "rule_wins": 0,
        "ties": 0,
        "total_comparisons": 0,
        "readiness_pct": 0.0,
        "routing": [],
    }


async def _fetch_consolidation_summary(pool) -> dict:
    """No memory_consolidation_log — return zeroed."""
    return {
        "clusters_7d": 0,
        "episodes_processed": 0,
        "knowledge_created": 0,
        "avg_confidence": 0.0,
        "top_topics": [],
    }


@router.get("/metrics")
async def get_brain_status_metrics():
    """Unified endpoint — returns ALL brain status dashboard data in one call."""
    pool = get_pool()

    (
        stimuli,
        thoughts,
        expression,
        reflections,
        migration,
        consolidation,
    ) = await asyncio.gather(
        _fetch_stimuli_summary(pool),
        _fetch_thoughts_summary(pool),
        _fetch_expression_summary(pool),
        _fetch_reflections_summary(pool),
        _fetch_migration_summary(pool),
        _fetch_consolidation_summary(pool),
    )

    return {
        "stimuli": stimuli,
        "thoughts": thoughts,
        "expression": expression,
        "reflections": reflections,
        "migration": migration,
        "consolidation": consolidation,
    }
