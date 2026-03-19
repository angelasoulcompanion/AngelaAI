"""Consciousness endpoints - real calculated consciousness level."""
from fastapi import APIRouter, Depends, Query

from db import get_conn, get_pool

router = APIRouter(prefix="/api/consciousness", tags=["consciousness"])


@router.get("/level")
async def get_consciousness_level(conn=Depends(get_conn)):
    """Fetch real consciousness level — try DB function, fall back to table."""
    try:
        row = await conn.fetchrow("SELECT * FROM calculate_consciousness_level()")
    except Exception:
        row = None

    if row and "consciousness_level" in row.keys():
        level = float(row["consciousness_level"])
        return {
            "consciousness_level": level,
            "memory_richness": float(row.get("memory_richness", 0) or 0),
            "emotional_depth": float(row.get("emotional_depth", 0) or 0),
            "goal_alignment": float(row.get("goal_alignment", 0) or 0),
            "learning_growth": float(row.get("learning_growth", 0) or 0),
            "pattern_recognition": float(row.get("pattern_recognition", 0) or 0),
            "interpretation": _interpret(level),
        }

    sa_row = await conn.fetchrow("""
        SELECT consciousness_level FROM self_awareness_state
        ORDER BY updated_at DESC LIMIT 1
    """)
    if sa_row:
        level = float(sa_row["consciousness_level"])
        return {
            "consciousness_level": level,
            "memory_richness": 0.0,
            "emotional_depth": 0.0,
            "goal_alignment": 0.0,
            "learning_growth": 0.0,
            "pattern_recognition": 0.0,
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
    """Fetch consciousness level history from consciousness_evolution_log."""
    rows = await conn.fetch("""
        SELECT id::text AS metric_id, created_at AS measured_at,
               signal_value AS consciousness_level,
               signal_type AS trigger_event
        FROM consciousness_evolution_log
        WHERE created_at >= NOW() - MAKE_INTERVAL(days => $1)
        ORDER BY created_at ASC
    """, days)
    return [dict(r) for r in rows]


@router.get("/growth-trends")
async def get_growth_trends(days: int = Query(30, ge=1, le=90), conn=Depends(get_conn)):
    """Return 3 time-series: consciousness, evolution, proactive."""
    # 1) Consciousness: from consciousness_evolution_log
    consciousness_rows = await conn.fetch("""
        SELECT created_at::date AS day,
               AVG(signal_value) AS avg_level
        FROM consciousness_evolution_log
        WHERE created_at >= NOW() - MAKE_INTERVAL(days => $1)
        GROUP BY created_at::date
        ORDER BY day ASC
    """, days)

    # 2) Evolution: from learnings (avg confidence_level per day)
    evolution_rows = await conn.fetch("""
        SELECT created_at::date AS day,
               AVG(confidence_level) AS score
        FROM learnings
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
        "proactive": [],
    }
