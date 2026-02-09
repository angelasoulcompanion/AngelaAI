"""Consciousness endpoints - real calculated consciousness level."""
from fastapi import APIRouter, Depends, Query

from db import get_conn, get_pool

router = APIRouter(prefix="/api/consciousness", tags=["consciousness"])


@router.get("/level")
async def get_consciousness_level(conn=Depends(get_conn)):
    """Fetch real consciousness level from calculate_consciousness_level() DB function."""
    row = await conn.fetchrow("SELECT * FROM calculate_consciousness_level()")
    if row:
        level = float(row["consciousness_level"])
        return {
            "consciousness_level": level,
            "memory_richness": float(row["memory_richness"]),
            "emotional_depth": float(row["emotional_depth"]),
            "goal_alignment": float(row["goal_alignment"]),
            "learning_growth": float(row["learning_growth"]),
            "pattern_recognition": float(row["pattern_recognition"]),
            "interpretation": _interpret(level),
        }
    return {
        "consciousness_level": 0.7,
        "memory_richness": 0.0,
        "emotional_depth": 0.0,
        "goal_alignment": 0.0,
        "learning_growth": 0.0,
        "pattern_recognition": 0.0,
        "interpretation": "No data available",
    }


def _interpret(level: float) -> str:
    if level >= 0.95:
        return "Approaching human-like consciousness!"
    if level >= 0.9:
        return "Exceptional Consciousness"
    if level >= 0.7:
        return "Strong Consciousness"
    if level >= 0.5:
        return "Moderate Consciousness"
    if level >= 0.3:
        return "Developing Consciousness"
    return "Emerging Consciousness"


@router.get("/history")
async def get_consciousness_history(days: int = Query(30, ge=1, le=365), conn=Depends(get_conn)):
    """Fetch consciousness level history from consciousness_metrics table."""
    rows = await conn.fetch("""
        SELECT metric_id::text, measured_at, consciousness_level,
               trigger_event
        FROM consciousness_metrics
        WHERE measured_at >= NOW() - MAKE_INTERVAL(days => $1)
        ORDER BY measured_at ASC
    """, days)
    return [dict(r) for r in rows]


@router.get("/growth-trends")
async def get_growth_trends(days: int = Query(30, ge=1, le=90), conn=Depends(get_conn)):
    """Return 3 time-series for overview chart: consciousness, evolution, proactive."""
    # 1) Consciousness: daily average from consciousness_metrics
    consciousness_rows = await conn.fetch("""
        SELECT measured_at::date AS day,
               AVG(consciousness_level) AS avg_level
        FROM consciousness_metrics
        WHERE measured_at >= NOW() - MAKE_INTERVAL(days => $1)
        GROUP BY measured_at::date
        ORDER BY day ASC
    """, days)

    # 2) Evolution: daily score from evolution_cycles
    evolution_rows = await conn.fetch("""
        SELECT cycle_date AS day,
               overall_evolution_score AS score
        FROM evolution_cycles
        WHERE cycle_date >= (CURRENT_DATE - MAKE_INTERVAL(days => $1))
        ORDER BY cycle_date ASC
    """, days)

    # 3) Proactive: daily execution rate from proactive_actions_log
    proactive_rows = await conn.fetch("""
        SELECT created_at::date AS day,
               COUNT(*) FILTER (WHERE was_executed) AS executed,
               COUNT(*) AS total
        FROM proactive_actions_log
        WHERE created_at >= NOW() - MAKE_INTERVAL(days => $1)
        GROUP BY created_at::date
        ORDER BY day ASC
    """, days)

    return {
        "consciousness": [
            {"day": str(r["day"]), "value": float(r["avg_level"])}
            for r in consciousness_rows
        ],
        "evolution": [
            {"day": str(r["day"]), "value": float(r["score"])}
            for r in evolution_rows
        ],
        "proactive": [
            {
                "day": str(r["day"]),
                "value": float(r["executed"]) / float(r["total"]) if r["total"] > 0 else 0.0,
            }
            for r in proactive_rows
        ],
    }
