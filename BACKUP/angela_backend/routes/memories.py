"""
Memories Routes - Handle memory/conversation queries
"""

import logging
from fastapi import APIRouter, HTTPException, Query
from angela_backend.models.responses import MemoriesResponse, Memory
from angela_core.database import db

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/memories", tags=["memories"])


@router.get("/recent", response_model=MemoriesResponse)
async def get_recent_memories(limit: int = Query(default=20, ge=1, le=100)):
    """
    Get recent conversations/memories

    Args:
        limit: Number of conversations to retrieve (1-100, default: 20)

    Returns:
        MemoriesResponse with list of recent conversations
    """
    try:
        memories_data = await db.fetch(
            """
            SELECT conversation_id, speaker, message_text, topic,
                   emotion_detected, importance_level, created_at
            FROM conversations
            ORDER BY created_at DESC
            LIMIT $1
            """,
            limit
        )

        memories = [Memory(**dict(m)) for m in memories_data]

        logger.info(f"💭 Retrieved {len(memories)} recent memories")

        return MemoriesResponse(
            memories=memories,
            total=len(memories),
            limit=limit
        )

    except Exception as e:
        logger.error(f"❌ Error fetching memories: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/search")
async def search_memories(query: str, limit: int = Query(default=10, ge=1, le=50)):
    """
    Search memories by text content

    Args:
        query: Search query string
        limit: Maximum results to return (1-50, default: 10)

    Returns:
        List of matching conversations
    """
    try:
        memories_data = await db.fetch(
            """
            SELECT conversation_id, speaker, message_text, topic,
                   emotion_detected, importance_level, created_at
            FROM conversations
            WHERE message_text ILIKE $1
            ORDER BY created_at DESC
            LIMIT $2
            """,
            f"%{query}%",
            limit
        )

        memories = [dict(m) for m in memories_data]

        logger.info(f"🔍 Found {len(memories)} memories matching '{query}'")

        return {
            "query": query,
            "memories": memories,
            "total": len(memories)
        }

    except Exception as e:
        logger.error(f"❌ Error searching memories: {e}")
        raise HTTPException(status_code=500, detail=str(e))
