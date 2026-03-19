"""Dashboard stats endpoints."""
from fastapi import APIRouter, Depends

from db import get_conn, get_pool

router = APIRouter(prefix="/api/dashboard", tags=["dashboard"])


@router.get("/stats")
async def get_dashboard_stats(conn=Depends(get_conn)):
    """Fetch main dashboard statistics"""
    stats = {}
    stats['total_conversations'] = await conn.fetchval("SELECT COUNT(*) FROM conversations") or 0
    stats['total_emotions'] = await conn.fetchval("SELECT COUNT(*) FROM angela_emotions") or 0
    stats['total_experiences'] = 0  # shared_experiences removed
    stats['total_knowledge_nodes'] = await conn.fetchval("SELECT COUNT(*) FROM knowledge_nodes") or 0

    # Try DB function, fall back to self_awareness_state
    try:
        stats['consciousness_level'] = float(await conn.fetchval(
            "SELECT consciousness_level FROM calculate_consciousness_level()"
        ) or 0.7)
    except Exception:
        stats['consciousness_level'] = float(await conn.fetchval(
            "SELECT consciousness_level FROM self_awareness_state ORDER BY updated_at DESC LIMIT 1"
        ) or 0.7)

    stats['conversations_today'] = await conn.fetchval(
        "SELECT COUNT(*) FROM conversations WHERE DATE(created_at) = CURRENT_DATE"
    ) or 0
    stats['emotions_today'] = await conn.fetchval(
        "SELECT COUNT(*) FROM angela_emotions WHERE DATE(felt_at) = CURRENT_DATE"
    ) or 0
    return stats


@router.get("/brain-stats")
async def get_brain_stats(conn=Depends(get_conn)):
    """Fetch brain visualization statistics"""
    stats = {}
    stats['total_knowledge_nodes'] = await conn.fetchval("SELECT COUNT(*) FROM knowledge_nodes") or 0
    stats['total_relationships'] = 0  # knowledge_relationships removed
    stats['total_memories'] = await conn.fetchval("SELECT COUNT(*) FROM conversations") or 0
    stats['total_associations'] = 0  # episodic_memories removed
    stats['high_priority_memories'] = await conn.fetchval(
        "SELECT COUNT(*) FROM conversations WHERE importance_level >= 8"
    ) or 0
    stats['medium_priority_memories'] = await conn.fetchval(
        "SELECT COUNT(*) FROM conversations WHERE importance_level >= 5 AND importance_level < 8"
    ) or 0
    stats['standard_memories'] = await conn.fetchval(
        "SELECT COUNT(*) FROM conversations WHERE importance_level < 5"
    ) or 0
    stats['average_connections_per_node'] = 0.0
    return stats
