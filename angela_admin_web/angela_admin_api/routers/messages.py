from fastapi import APIRouter, HTTPException, Query, Depends
from pydantic import BaseModel
from datetime import datetime
from typing import List, Optional
from uuid import UUID

# ✅ [Batch-24]: Migrated to Clean Architecture with DI
from angela_core.infrastructure.persistence.repositories import MessageRepository
from angela_core.presentation.api.dependencies import get_message_repo
from angela_core.domain.entities import AngelaMessage as AngelaMessageEntity

router = APIRouter()

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
    is_pinned: Optional[bool] = None,
    repo: MessageRepository = Depends(get_message_repo)
):
    """Get Angela's messages with optional filters (Clean Architecture)"""
    try:
        # ✅ [Batch-24]: Using MessageRepository.find_by_filters()
        messages = await repo.find_by_filters(
            message_type=message_type,
            category=category,
            is_important=is_important,
            is_pinned=is_pinned,
            limit=limit
        )

        return [
            AngelaMessage(
                message_id=str(msg.message_id),
                message_text=msg.message_text,
                message_type=msg.message_type,
                emotion=msg.emotion,
                category=msg.category,
                is_important=msg.is_important,
                is_pinned=msg.is_pinned,
                created_at=msg.created_at.isoformat()
            )
            for msg in messages
        ]

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to fetch messages: {str(e)}")

@router.get("/api/messages/stats/summary", response_model=MessageStats)
async def get_message_stats(
    repo: MessageRepository = Depends(get_message_repo)
):
    """Get statistics about Angela's messages (Clean Architecture)"""
    try:
        # ✅ [Batch-24]: Using MessageRepository.get_statistics()
        stats = await repo.get_statistics()

        return MessageStats(
            total_messages=stats.get("total_messages", 0),
            pinned_messages=stats.get("pinned_messages", 0),
            important_messages=stats.get("important_messages", 0),
            by_type=stats.get("by_type", []),
            by_category=stats.get("by_category", []),
            recent_emotions=stats.get("recent_emotions", [])
        )

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to fetch message stats: {str(e)}")

@router.post("/api/messages", response_model=AngelaMessage)
async def create_message(
    message: AngelaMessageCreate,
    repo: MessageRepository = Depends(get_message_repo)
):
    """Create a new message from Angela (Clean Architecture)"""
    try:
        # ✅ [Batch-24]: Using AngelaMessage.create() + MessageRepository.create()
        entity = AngelaMessageEntity.create(
            message_text=message.message_text,
            message_type=message.message_type,
            emotion=message.emotion,
            category=message.category,
            is_important=message.is_important,
            is_pinned=message.is_pinned
        )

        created = await repo.create(entity)

        return AngelaMessage(
            message_id=str(created.message_id),
            message_text=created.message_text,
            message_type=created.message_type,
            emotion=created.emotion,
            category=created.category,
            is_important=created.is_important,
            is_pinned=created.is_pinned,
            created_at=created.created_at.isoformat()
        )

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to create message: {str(e)}")

@router.put("/api/messages/{message_id}", response_model=AngelaMessage)
async def update_message(
    message_id: str,
    message: AngelaMessageCreate,
    repo: MessageRepository = Depends(get_message_repo)
):
    """Update an existing message (Clean Architecture)"""
    try:
        # ✅ [Batch-24]: Using MessageRepository.get_by_id() + update()
        # Parse UUID
        msg_uuid = UUID(message_id)

        # Get existing message
        existing = await repo.get_by_id(msg_uuid)
        if not existing:
            raise HTTPException(status_code=404, detail="Message not found")

        # Update using entity method
        updated_entity = existing.update_content(
            message_text=message.message_text,
            message_type=message.message_type,
            emotion=message.emotion,
            category=message.category,
            is_important=message.is_important,
            is_pinned=message.is_pinned
        )

        # Save to database
        updated = await repo.update(msg_uuid, updated_entity)

        return AngelaMessage(
            message_id=str(updated.message_id),
            message_text=updated.message_text,
            message_type=updated.message_type,
            emotion=updated.emotion,
            category=updated.category,
            is_important=updated.is_important,
            is_pinned=updated.is_pinned,
            created_at=updated.created_at.isoformat()
        )

    except HTTPException:
        raise
    except ValueError as e:
        raise HTTPException(status_code=400, detail=f"Invalid UUID: {str(e)}")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to update message: {str(e)}")

@router.put("/api/messages/{message_id}/pin")
async def toggle_pin(
    message_id: str,
    repo: MessageRepository = Depends(get_message_repo)
):
    """Toggle pin status of a message (Clean Architecture)"""
    try:
        # ✅ [Batch-24]: Using MessageRepository.toggle_pin()
        # Parse UUID
        msg_uuid = UUID(message_id)

        # Toggle pin (atomic operation in repository)
        new_status = await repo.toggle_pin(msg_uuid)

        return {"message_id": message_id, "is_pinned": new_status}

    except ValueError as e:
        raise HTTPException(status_code=400, detail=f"Invalid UUID: {str(e)}")
    except Exception as e:
        # EntityNotFoundError will be caught here
        if "not found" in str(e).lower():
            raise HTTPException(status_code=404, detail="Message not found")
        raise HTTPException(status_code=500, detail=f"Failed to toggle pin: {str(e)}")

@router.delete("/api/messages/{message_id}")
async def delete_message(
    message_id: str,
    repo: MessageRepository = Depends(get_message_repo)
):
    """Delete a message (Clean Architecture)"""
    try:
        # ✅ [Batch-24]: Using MessageRepository.delete()
        # Parse UUID
        msg_uuid = UUID(message_id)

        # Delete from repository
        success = await repo.delete(msg_uuid)

        if not success:
            raise HTTPException(status_code=404, detail="Message not found")

        return {"message": "Message deleted successfully"}

    except HTTPException:
        raise
    except ValueError as e:
        raise HTTPException(status_code=400, detail=f"Invalid UUID: {str(e)}")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to delete message: {str(e)}")
