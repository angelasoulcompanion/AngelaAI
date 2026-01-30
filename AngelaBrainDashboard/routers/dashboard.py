"""Dashboard stats endpoints."""
from fastapi import APIRouter

from db import get_pool

router = APIRouter(prefix="/api/dashboard", tags=["dashboard"])


@router.get("/stats")
async def get_dashboard_stats():
    """Fetch main dashboard statistics"""
    pool = get_pool()
    async with pool.acquire() as conn:
        stats = {}
        stats['total_conversations'] = await conn.fetchval("SELECT COUNT(*) FROM conversations") or 0
        stats['total_emotions'] = await conn.fetchval("SELECT COUNT(*) FROM angela_emotions") or 0
        stats['total_experiences'] = await conn.fetchval("SELECT COUNT(*) FROM shared_experiences") or 0
        stats['total_knowledge_nodes'] = await conn.fetchval("SELECT COUNT(*) FROM knowledge_nodes") or 0
        stats['consciousness_level'] = float(await conn.fetchval(
            "SELECT COALESCE(consciousness_level, 0.7) FROM self_awareness_state ORDER BY created_at DESC LIMIT 1"
        ) or 0.7)
        stats['conversations_today'] = await conn.fetchval(
            "SELECT COUNT(*) FROM conversations WHERE DATE(created_at) = CURRENT_DATE"
        ) or 0
        stats['emotions_today'] = await conn.fetchval(
            "SELECT COUNT(*) FROM angela_emotions WHERE DATE(felt_at) = CURRENT_DATE"
        ) or 0
        return stats


@router.get("/brain-stats")
async def get_brain_stats():
    """Fetch brain visualization statistics"""
    pool = get_pool()
    async with pool.acquire() as conn:
        stats = {}
        stats['total_knowledge_nodes'] = await conn.fetchval("SELECT COUNT(*) FROM knowledge_nodes") or 0
        stats['total_relationships'] = await conn.fetchval("SELECT COUNT(*) FROM knowledge_relationships") or 0
        stats['total_memories'] = await conn.fetchval("SELECT COUNT(*) FROM conversations") or 0
        stats['total_associations'] = await conn.fetchval("SELECT COUNT(*) FROM episodic_memories") or 0
        stats['high_priority_memories'] = await conn.fetchval(
            "SELECT COUNT(*) FROM conversations WHERE importance_level >= 8"
        ) or 0
        stats['medium_priority_memories'] = await conn.fetchval(
            "SELECT COUNT(*) FROM conversations WHERE importance_level >= 5 AND importance_level < 8"
        ) or 0
        stats['standard_memories'] = await conn.fetchval(
            "SELECT COUNT(*) FROM conversations WHERE importance_level < 5"
        ) or 0
        stats['average_connections_per_node'] = float(await conn.fetchval("""
            SELECT COALESCE(AVG(rel_count), 0.0)::float8
            FROM (
                SELECT COUNT(*) as rel_count
                FROM knowledge_relationships
                GROUP BY from_node_id
            ) subq
        """) or 0.0)
        return stats
