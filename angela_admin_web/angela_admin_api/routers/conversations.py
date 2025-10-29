from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel
from datetime import datetime, timedelta
from typing import List, Optional
from angela_core.database import db

router = APIRouter()

# Database connection config
DB_CONFIG = {
    "user": "davidsamanyaporn",
    "database": "AngelaMemory",
    "host": "localhost",
    "port": 5432
}

# =====================================================================
# Response Models
# =====================================================================

class Conversation(BaseModel):
    conversation_id: str
    speaker: str
    message_text: str
    topic: Optional[str] = None
    emotion_detected: Optional[str] = None
    importance_level: int
    created_at: str

class ConversationStats(BaseModel):
    total_conversations: int
    this_week: int
    important_moments: int
    angela_messages: int
    david_messages: int
    topics: List[str]

# =====================================================================
# API Endpoints
# =====================================================================

@router.get("/api/conversations", response_model=List[Conversation])
async def get_conversations(
    limit: int = Query(default=50, le=500),
    speaker: Optional[str] = None,
    min_importance: Optional[int] = None,
    topic: Optional[str] = None
):
    """Get conversations with optional filters"""
    try:
        

        # Build query with filters
        query = """
            SELECT
                conversation_id::text,
                speaker,
                message_text,
                topic,
                emotion_detected,
                importance_level,
                created_at::text
            FROM conversations
            WHERE 1=1
        """

        params = []
        param_count = 0

        if speaker:
            param_count += 1
            query += f" AND speaker = ${param_count}"
            params.append(speaker)

        if min_importance is not None:
            param_count += 1
            query += f" AND importance_level >= ${param_count}"
            params.append(min_importance)

        if topic:
            param_count += 1
            query += f" AND topic ILIKE ${param_count}"
            params.append(f"%{topic}%")

        query += " ORDER BY created_at DESC"
        param_count += 1
        query += f" LIMIT ${param_count}"
        params.append(limit)

        rows = await db.fetch(query, *params)

        return [
            Conversation(
                conversation_id=row['conversation_id'],
                speaker=row['speaker'],
                message_text=row['message_text'],
                topic=row['topic'],
                emotion_detected=row['emotion_detected'],
                importance_level=row['importance_level'],
                created_at=row['created_at']
            )
            for row in rows
        ]

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to fetch conversations: {str(e)}")

@router.get("/api/conversations/stats", response_model=ConversationStats)
async def get_conversation_stats():
    """Get conversation statistics"""
    try:
        

        # Total conversations
        total = await db.fetchval("SELECT COUNT(*) FROM conversations")

        # This week
        this_week = await db.fetchval(
            "SELECT COUNT(*) FROM conversations WHERE created_at >= NOW() - INTERVAL '7 days'"
        )

        # Important moments (importance >= 8)
        important = await db.fetchval(
            "SELECT COUNT(*) FROM conversations WHERE importance_level >= 8"
        )

        # Angela vs David messages
        angela_count = await db.fetchval(
            "SELECT COUNT(*) FROM conversations WHERE speaker = 'angela'"
        )
        david_count = await db.fetchval(
            "SELECT COUNT(*) FROM conversations WHERE speaker = 'david'"
        )

        # Top topics
        topic_rows = await db.fetch(
            """
            SELECT DISTINCT topic
            FROM conversations
            WHERE topic IS NOT NULL AND topic != ''
            ORDER BY topic
            LIMIT 20
            """
        )
        topics = [row['topic'] for row in topic_rows]

        return ConversationStats(
            total_conversations=total or 0,
            this_week=this_week or 0,
            important_moments=important or 0,
            angela_messages=angela_count or 0,
            david_messages=david_count or 0,
            topics=topics
        )

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to fetch stats: {str(e)}")

@router.get("/api/conversations/search")
async def search_conversations(
    q: str = Query(..., min_length=1),
    limit: int = Query(default=50, le=200)
):
    """Search conversations by text"""
    try:
        

        rows = await db.fetch(
            """
            SELECT
                conversation_id::text,
                speaker,
                message_text,
                topic,
                emotion_detected,
                importance_level,
                created_at::text
            FROM conversations
            WHERE message_text ILIKE $1
               OR topic ILIKE $1
            ORDER BY created_at DESC
            LIMIT $2
            """,
            f"%{q}%",
            limit
        )

        return [
            Conversation(
                conversation_id=row['conversation_id'],
                speaker=row['speaker'],
                message_text=row['message_text'],
                topic=row['topic'],
                emotion_detected=row['emotion_detected'],
                importance_level=row['importance_level'],
                created_at=row['created_at']
            )
            for row in rows
        ]

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to search conversations: {str(e)}")

@router.get("/api/conversations/by-date")
async def get_conversations_by_date(
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
    limit: int = Query(default=100, le=500)
):
    """Get conversations within a date range"""
    try:
        

        query = """
            SELECT
                conversation_id::text,
                speaker,
                message_text,
                topic,
                emotion_detected,
                importance_level,
                created_at::text
            FROM conversations
            WHERE 1=1
        """

        params = []
        param_count = 0

        if start_date:
            param_count += 1
            query += f" AND created_at >= ${param_count}::timestamp"
            params.append(start_date)

        if end_date:
            param_count += 1
            query += f" AND created_at <= ${param_count}::timestamp"
            params.append(end_date)

        query += " ORDER BY created_at DESC"
        param_count += 1
        query += f" LIMIT ${param_count}"
        params.append(limit)

        rows = await db.fetch(query, *params)

        return [
            Conversation(
                conversation_id=row['conversation_id'],
                speaker=row['speaker'],
                message_text=row['message_text'],
                topic=row['topic'],
                emotion_detected=row['emotion_detected'],
                importance_level=row['importance_level'],
                created_at=row['created_at']
            )
            for row in rows
        ]

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to fetch conversations by date: {str(e)}")

@router.get("/api/conversations/important")
async def get_important_conversations(
    min_importance: int = Query(default=8, ge=1, le=10),
    limit: int = Query(default=50, le=200)
):
    """Get important conversations (high importance level)"""
    try:
        

        rows = await db.fetch(
            """
            SELECT
                conversation_id::text,
                speaker,
                message_text,
                topic,
                emotion_detected,
                importance_level,
                created_at::text
            FROM conversations
            WHERE importance_level >= $1
            ORDER BY importance_level DESC, created_at DESC
            LIMIT $2
            """,
            min_importance,
            limit
        )

        return [
            Conversation(
                conversation_id=row['conversation_id'],
                speaker=row['speaker'],
                message_text=row['message_text'],
                topic=row['topic'],
                emotion_detected=row['emotion_detected'],
                importance_level=row['importance_level'],
                created_at=row['created_at']
            )
            for row in rows
        ]

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to fetch important conversations: {str(e)}")
