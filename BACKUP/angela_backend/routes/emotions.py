"""
Emotions Routes - Handle emotional state queries
"""

import logging
from datetime import datetime
from fastapi import APIRouter, HTTPException
from angela_backend.models.responses import EmotionalState
from angela_core.database import db

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/emotions", tags=["emotions"])


@router.get("/current", response_model=EmotionalState)
async def get_current_emotion():
    """
    Get Angela's current emotional state

    Returns the most recent emotional state from the database.
    If no emotions exist, returns a default neutral state.

    Returns:
        EmotionalState with current emotion values
    """
    try:
        emotion = await db.fetchrow(
            """
            SELECT happiness, confidence, anxiety, motivation, gratitude, loneliness,
                   triggered_by, emotion_note, created_at
            FROM emotional_states
            ORDER BY created_at DESC
            LIMIT 1
            """
        )

        if not emotion:
            # Return default neutral state
            logger.info("📊 No emotions found, returning default neutral state")
            return EmotionalState(
                happiness=0.7,
                confidence=0.7,
                anxiety=0.3,
                motivation=0.8,
                gratitude=0.8,
                loneliness=0.2,
                triggered_by="system_default",
                emotion_note="Angela is ready to chat!",
                created_at=datetime.now()
            )

        logger.info(f"📊 Retrieved current emotion: happiness={emotion['happiness']:.2f}")
        return EmotionalState(**dict(emotion))

    except Exception as e:
        logger.error(f"❌ Error fetching emotion: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/history")
async def get_emotion_history(limit: int = 10):
    """
    Get Angela's emotion history

    Args:
        limit: Number of recent emotions to retrieve (default: 10)

    Returns:
        List of recent emotional states
    """
    try:
        emotions = await db.fetch(
            """
            SELECT happiness, confidence, anxiety, motivation, gratitude, loneliness,
                   triggered_by, emotion_note, created_at
            FROM emotional_states
            ORDER BY created_at DESC
            LIMIT $1
            """,
            limit
        )

        return {
            "emotions": [dict(e) for e in emotions],
            "total": len(emotions)
        }

    except Exception as e:
        logger.error(f"❌ Error fetching emotion history: {e}")
        raise HTTPException(status_code=500, detail=str(e))
