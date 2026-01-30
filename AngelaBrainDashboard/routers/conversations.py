"""Conversations endpoints."""
from fastapi import APIRouter, Query

from db import get_pool

router = APIRouter(prefix="/api/conversations", tags=["conversations"])


@router.get("/recent")
async def get_recent_conversations(limit: int = Query(50, ge=1, le=200)):
    """Fetch recent conversations"""
    pool = get_pool()
    async with pool.acquire() as conn:
        rows = await conn.fetch("""
            SELECT conversation_id::text, speaker, message_text, topic,
                   emotion_detected, importance_level, created_at
            FROM conversations
            ORDER BY created_at DESC
            LIMIT $1
        """, limit)
        return [dict(r) for r in rows]


@router.get("/stats")
async def get_conversation_stats():
    """Fetch conversation statistics"""
    pool = get_pool()
    async with pool.acquire() as conn:
        row = await conn.fetchrow("""
            SELECT
                COUNT(*) as total,
                COUNT(*) FILTER (WHERE created_at >= NOW() - INTERVAL '24 hours') as last_24h,
                COALESCE(AVG(importance_level) FILTER (WHERE created_at >= NOW() - INTERVAL '24 hours'), 0) as avg_importance
            FROM conversations
        """)
        return {
            "total": row['total'] or 0,
            "last_24h": row['last_24h'] or 0,
            "avg_importance": float(row['avg_importance'] or 0)
        }
