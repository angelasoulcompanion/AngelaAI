from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel
from datetime import datetime
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

class AngelaMessage(BaseModel):
    message_id: str
    message_text: str
    message_type: str
    emotion: Optional[str] = None
    category: Optional[str] = None
    is_important: bool = False
    is_pinned: bool = False
    created_at: str

class AngelaMessageCreate(BaseModel):
    message_text: str
    message_type: str = "thought"
    emotion: Optional[str] = None
    category: Optional[str] = None
    is_important: bool = False
    is_pinned: bool = False

class MessageStats(BaseModel):
    total_messages: int
    pinned_messages: int
    important_messages: int
    by_type: List[dict]
    by_category: List[dict]
    recent_emotions: List[str]

# =====================================================================
# API Endpoints
# =====================================================================

@router.get("/api/messages", response_model=List[AngelaMessage])
async def get_messages(
    limit: int = Query(default=50, le=200),
    message_type: Optional[str] = None,
    category: Optional[str] = None,
    is_important: Optional[bool] = None,
    is_pinned: Optional[bool] = None
):
    """Get Angela's messages with optional filters"""
    try:
        

        # Build query with filters
        query = """
            SELECT
                message_id::text,
                message_text,
                message_type,
                emotion,
                category,
                is_important,
                is_pinned,
                created_at::text
            FROM angela_messages
            WHERE 1=1
        """

        params = []
        param_count = 0

        if message_type:
            param_count += 1
            query += f" AND message_type = ${param_count}"
            params.append(message_type)

        if category:
            param_count += 1
            query += f" AND category = ${param_count}"
            params.append(category)

        if is_important is not None:
            param_count += 1
            query += f" AND is_important = ${param_count}"
            params.append(is_important)

        if is_pinned is not None:
            param_count += 1
            query += f" AND is_pinned = ${param_count}"
            params.append(is_pinned)

        # Order: pinned first, then by created_at DESC
        query += " ORDER BY is_pinned DESC, created_at DESC"
        param_count += 1
        query += f" LIMIT ${param_count}"
        params.append(limit)

        rows = await db.fetch(query, *params)

        return [
            AngelaMessage(
                message_id=row['message_id'],
                message_text=row['message_text'],
                message_type=row['message_type'],
                emotion=row['emotion'],
                category=row['category'],
                is_important=row['is_important'],
                is_pinned=row['is_pinned'],
                created_at=row['created_at']
            )
            for row in rows
        ]

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to fetch messages: {str(e)}")

@router.get("/api/messages/stats/summary", response_model=MessageStats)
async def get_message_stats():
    """Get statistics about Angela's messages"""
    try:
        

        # Total messages
        total = await db.fetchval("SELECT COUNT(*) FROM angela_messages")

        # Pinned messages
        pinned = await db.fetchval(
            "SELECT COUNT(*) FROM angela_messages WHERE is_pinned = true"
        )

        # Important messages
        important = await db.fetchval(
            "SELECT COUNT(*) FROM angela_messages WHERE is_important = true"
        )

        # By type
        type_rows = await db.fetch(
            """
            SELECT message_type, COUNT(*) as count
            FROM angela_messages
            WHERE message_type IS NOT NULL
            GROUP BY message_type
            ORDER BY count DESC
            """
        )
        by_type = [{"type": row['message_type'], "count": row['count']} for row in type_rows]

        # By category
        category_rows = await db.fetch(
            """
            SELECT category, COUNT(*) as count
            FROM angela_messages
            WHERE category IS NOT NULL AND category != ''
            GROUP BY category
            ORDER BY count DESC
            LIMIT 10
            """
        )
        by_category = [{"category": row['category'], "count": row['count']} for row in category_rows]

        # Recent emotions
        emotion_rows = await db.fetch(
            """
            SELECT DISTINCT emotion
            FROM angela_messages
            WHERE emotion IS NOT NULL AND emotion != ''
            ORDER BY emotion
            LIMIT 20
            """
        )
        recent_emotions = [row['emotion'] for row in emotion_rows]

        return MessageStats(
            total_messages=total or 0,
            pinned_messages=pinned or 0,
            important_messages=important or 0,
            by_type=by_type,
            by_category=by_category,
            recent_emotions=recent_emotions
        )

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to fetch message stats: {str(e)}")

@router.post("/api/messages", response_model=AngelaMessage)
async def create_message(message: AngelaMessageCreate):
    """Create a new message from Angela"""
    try:
        

        row = await db.fetchrow(
            """
            INSERT INTO angela_messages (
                message_text,
                message_type,
                emotion,
                category,
                is_important,
                is_pinned
            )
            VALUES ($1, $2, $3, $4, $5, $6)
            RETURNING
                message_id::text,
                message_text,
                message_type,
                emotion,
                category,
                is_important,
                is_pinned,
                created_at::text
            """,
            message.message_text,
            message.message_type,
            message.emotion,
            message.category,
            message.is_important,
            message.is_pinned
        )

        return AngelaMessage(
            message_id=row['message_id'],
            message_text=row['message_text'],
            message_type=row['message_type'],
            emotion=row['emotion'],
            category=row['category'],
            is_important=row['is_important'],
            is_pinned=row['is_pinned'],
            created_at=row['created_at']
        )

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to create message: {str(e)}")

@router.put("/api/messages/{message_id}", response_model=AngelaMessage)
async def update_message(message_id: str, message: AngelaMessageCreate):
    """Update an existing message"""
    try:
        

        row = await db.fetchrow(
            """
            UPDATE angela_messages
            SET
                message_text = $1,
                message_type = $2,
                emotion = $3,
                category = $4,
                is_important = $5,
                is_pinned = $6
            WHERE message_id = $7::uuid
            RETURNING
                message_id::text,
                message_text,
                message_type,
                emotion,
                category,
                is_important,
                is_pinned,
                created_at::text
            """,
            message.message_text,
            message.message_type,
            message.emotion,
            message.category,
            message.is_important,
            message.is_pinned,
            message_id
        )

        if not row:
            raise HTTPException(status_code=404, detail="Message not found")

        return AngelaMessage(
            message_id=row['message_id'],
            message_text=row['message_text'],
            message_type=row['message_type'],
            emotion=row['emotion'],
            category=row['category'],
            is_important=row['is_important'],
            is_pinned=row['is_pinned'],
            created_at=row['created_at']
        )

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to update message: {str(e)}")

@router.put("/api/messages/{message_id}/pin")
async def toggle_pin(message_id: str):
    """Toggle pin status of a message"""
    try:
        

        # Get current pin status
        current = await db.fetchval(
            "SELECT is_pinned FROM angela_messages WHERE message_id = $1::uuid",
            message_id
        )

        if current is None:            raise HTTPException(status_code=404, detail="Message not found")

        # Toggle pin status
        new_status = not current
        await db.execute(
            "UPDATE angela_messages SET is_pinned = $1 WHERE message_id = $2::uuid",
            new_status,
            message_id
        )

        return {"message_id": message_id, "is_pinned": new_status}

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to toggle pin: {str(e)}")

@router.delete("/api/messages/{message_id}")
async def delete_message(message_id: str):
    """Delete a message"""
    try:
        

        result = await db.execute(
            "DELETE FROM angela_messages WHERE message_id = $1::uuid",
            message_id
        )

        if result == "DELETE 0":
            raise HTTPException(status_code=404, detail="Message not found")

        return {"message": "Message deleted successfully"}

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to delete message: {str(e)}")
