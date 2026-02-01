"""Consciousness endpoints - real calculated consciousness level."""
from fastapi import APIRouter, Query

from db import get_pool

router = APIRouter(prefix="/api/consciousness", tags=["consciousness"])


@router.get("/level")
async def get_consciousness_level():
    """Fetch real consciousness level from calculate_consciousness_level() DB function."""
    pool = get_pool()
    async with pool.acquire() as conn:
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
async def get_consciousness_history(days: int = Query(30, ge=1, le=365)):
    """Fetch consciousness level history from consciousness_metrics table."""
    pool = get_pool()
    async with pool.acquire() as conn:
        rows = await conn.fetch("""
            SELECT metric_id::text, measured_at, consciousness_level,
                   trigger_event
            FROM consciousness_metrics
            WHERE measured_at >= NOW() - MAKE_INTERVAL(days => $1)
            ORDER BY measured_at ASC
        """, days)
        return [dict(r) for r in rows]
