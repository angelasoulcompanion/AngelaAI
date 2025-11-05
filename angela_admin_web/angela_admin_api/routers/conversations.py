from fastapi import APIRouter, HTTPException, Query, Depends
from pydantic import BaseModel
from datetime import datetime, timedelta
from typing import List, Optional

# ✅ [Batch-24]: Migrated to Clean Architecture with DI
from angela_core.infrastructure.persistence.repositories import ConversationRepository
from angela_core.presentation.api.dependencies import get_conversation_repo

router = APIRouter()

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
    topic: Optional[str] = None,
    repo: ConversationRepository = Depends(get_conversation_repo)
):
    """Get conversations with optional filters (Clean Architecture)"""
    try:
        # ✅ [Batch-24]: Using ConversationRepository.find_by_filters()
        conversations = await repo.find_by_filters(
            speaker=speaker,
            min_importance=min_importance,
            topic=topic,
            limit=limit
        )

        return [
            Conversation(
                conversation_id=str(conv.id),  # Entity uses 'id'
                speaker=conv.speaker.value if hasattr(conv.speaker, 'value') else str(conv.speaker),
                message_text=conv.message_text,
                topic=conv.topic,
                emotion_detected=conv.emotion_detected,
                importance_level=conv.importance_level,
                created_at=conv.created_at.isoformat()
            )
            for conv in conversations
        ]

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to fetch conversations: {str(e)}")

@router.get("/api/conversations/stats", response_model=ConversationStats)
async def get_conversation_stats(
    repo: ConversationRepository = Depends(get_conversation_repo)
):
    """Get conversation statistics (Clean Architecture)"""
    try:
        # ✅ [Batch-24]: Using ConversationRepository.get_statistics()
        stats = await repo.get_statistics()

        return ConversationStats(
            total_conversations=stats.get("total_conversations", 0),
            this_week=stats.get("this_week", 0),
            important_moments=stats.get("important_moments", 0),
            angela_messages=stats.get("angela_messages", 0),
            david_messages=stats.get("david_messages", 0),
            topics=stats.get("topics", [])
        )

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to fetch stats: {str(e)}")

@router.get("/api/conversations/search")
async def search_conversations(
    q: str = Query(..., min_length=1),
    limit: int = Query(default=50, le=200),
    repo: ConversationRepository = Depends(get_conversation_repo)
):
    """Search conversations by text (Clean Architecture)"""
    try:
        # ✅ [Batch-24]: Using ConversationRepository.search_by_text()
        conversations = await repo.search_by_text(
            query_text=q,
            limit=limit
        )

        return [
            Conversation(
                conversation_id=str(conv.id),  # Entity uses 'id'
                speaker=conv.speaker.value if hasattr(conv.speaker, 'value') else str(conv.speaker),
                message_text=conv.message_text,
                topic=conv.topic,
                emotion_detected=conv.emotion_detected,
                importance_level=conv.importance_level,
                created_at=conv.created_at.isoformat()
            )
            for conv in conversations
        ]

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to search conversations: {str(e)}")

@router.get("/api/conversations/by-date")
async def get_conversations_by_date(
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
    limit: int = Query(default=100, le=500),
    repo: ConversationRepository = Depends(get_conversation_repo)
):
    """Get conversations within a date range (Clean Architecture)"""
    try:
        # ✅ [Batch-24]: Using ConversationRepository.get_by_date_range()
        # Parse dates if provided
        start_dt = datetime.fromisoformat(start_date) if start_date else None
        end_dt = datetime.fromisoformat(end_date) if end_date else None

        conversations = await repo.get_by_date_range(
            start_date=start_dt,
            end_date=end_dt,
            limit=limit
        )

        return [
            Conversation(
                conversation_id=str(conv.id),  # Entity uses 'id'
                speaker=conv.speaker.value if hasattr(conv.speaker, 'value') else str(conv.speaker),
                message_text=conv.message_text,
                topic=conv.topic,
                emotion_detected=conv.emotion_detected,
                importance_level=conv.importance_level,
                created_at=conv.created_at.isoformat()
            )
            for conv in conversations
        ]

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to fetch conversations by date: {str(e)}")

@router.get("/api/conversations/important")
async def get_important_conversations(
    min_importance: int = Query(default=8, ge=1, le=10),
    limit: int = Query(default=50, le=200),
    repo: ConversationRepository = Depends(get_conversation_repo)
):
    """Get important conversations (high importance level) (Clean Architecture)"""
    try:
        # ✅ [Batch-24]: Using ConversationRepository.get_important()
        conversations = await repo.get_important(
            min_importance=min_importance,
            limit=limit
        )

        return [
            Conversation(
                conversation_id=str(conv.id),  # Entity uses 'id'
                speaker=conv.speaker.value if hasattr(conv.speaker, 'value') else str(conv.speaker),
                message_text=conv.message_text,
                topic=conv.topic,
                emotion_detected=conv.emotion_detected,
                importance_level=conv.importance_level,
                created_at=conv.created_at.isoformat()
            )
            for conv in conversations
        ]

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to fetch important conversations: {str(e)}")
