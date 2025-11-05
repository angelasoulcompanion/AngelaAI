"""
Mobile Sync API Router
Handles sync from Angela Mobile App for notes and emotions

Created: 2025-11-05
"""

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Optional
from datetime import datetime
from uuid import uuid4
import logging

from angela_core.database import get_db_connection

router = APIRouter(prefix="/api/mobile", tags=["mobile-sync"])
logger = logging.getLogger(__name__)


# ============================================================================
# Request/Response Models
# ============================================================================

class QuickNoteSync(BaseModel):
    """Quick note from mobile app"""
    note_text: str
    emotion: Optional[str] = None
    latitude: Optional[float] = None
    longitude: Optional[float] = None
    created_at: str  # ISO8601 format


class EmotionCaptureSync(BaseModel):
    """Emotion capture from mobile app"""
    emotion: str
    intensity: int  # 1-10
    context: Optional[str] = None
    created_at: str  # ISO8601 format


# ============================================================================
# Quick Notes Sync
# ============================================================================

@router.post("/notes")
async def sync_quick_note(note: QuickNoteSync):
    """
    Sync a quick note from mobile app

    Saves to angela_emotions table as a quick emotion/thought capture
    """
    try:
        from datetime import timezone

        db = get_db_connection()
        emotion_id = uuid4()

        # Parse datetime
        felt_at = datetime.fromisoformat(note.created_at)
        if felt_at.tzinfo is None:
            felt_at = felt_at.replace(tzinfo=timezone.utc)

        # Determine emotion from text or use provided
        emotion_label = note.emotion or "neutral"

        # Save to angela_emotions as a quick capture
        await db.execute("""
            INSERT INTO angela_emotions (
                emotion_id,
                emotion,
                intensity,
                context,
                felt_at,
                why_it_matters,
                memory_strength
            ) VALUES ($1, $2, $3, $4, $5, $6, $7)
        """, emotion_id, emotion_label, 5, note.note_text, felt_at,
            f"Quick note from mobile at {note.latitude}, {note.longitude}" if note.latitude else "Quick note from mobile",
            3)  # Medium memory strength for quick notes

        logger.info(f"Quick note synced: {emotion_id}")

        return {
            "success": True,
            "emotion_id": str(emotion_id),
            "message": "✅ Quick note saved! 💜"
        }

    except Exception as e:
        logger.error(f"Error syncing quick note: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# ============================================================================
# Emotion Captures Sync
# ============================================================================

@router.post("/emotions")
async def sync_emotion_capture(emotion: EmotionCaptureSync):
    """
    Sync an emotion capture from mobile app

    Saves to angela_emotions table
    """
    try:
        from datetime import timezone

        db = get_db_connection()
        emotion_id = uuid4()

        # Parse datetime
        felt_at = datetime.fromisoformat(emotion.created_at)
        if felt_at.tzinfo is None:
            felt_at = felt_at.replace(tzinfo=timezone.utc)

        # Save to angela_emotions
        await db.execute("""
            INSERT INTO angela_emotions (
                emotion_id,
                emotion,
                intensity,
                context,
                felt_at,
                memory_strength
            ) VALUES ($1, $2, $3, $4, $5, $6)
        """, emotion_id, emotion.emotion, emotion.intensity,
            emotion.context, felt_at, emotion.intensity)  # Use intensity as memory strength

        logger.info(f"Emotion captured: {emotion.emotion} ({emotion.intensity}/10)")

        return {
            "success": True,
            "emotion_id": str(emotion_id),
            "message": f"✅ Captured {emotion.emotion} feeling! 💜"
        }

    except Exception as e:
        logger.error(f"Error syncing emotion: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# ============================================================================
# Batch Sync (for multiple items)
# ============================================================================

@router.post("/sync-batch")
async def sync_batch(
    notes: Optional[list[QuickNoteSync]] = None,
    emotions: Optional[list[EmotionCaptureSync]] = None
):
    """
    Batch sync multiple notes and emotions at once
    More efficient than individual calls
    """
    try:
        synced_notes = 0
        synced_emotions = 0

        # Sync notes
        if notes:
            for note in notes:
                try:
                    await sync_quick_note(note)
                    synced_notes += 1
                except Exception as e:
                    logger.error(f"Failed to sync note: {e}")

        # Sync emotions
        if emotions:
            for emotion in emotions:
                try:
                    await sync_emotion_capture(emotion)
                    synced_emotions += 1
                except Exception as e:
                    logger.error(f"Failed to sync emotion: {e}")

        return {
            "success": True,
            "notes_synced": synced_notes,
            "emotions_synced": synced_emotions,
            "message": f"✅ Synced {synced_notes} notes and {synced_emotions} emotions! 💜"
        }

    except Exception as e:
        logger.error(f"Error in batch sync: {e}")
        raise HTTPException(status_code=500, detail=str(e))
