from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel
from datetime import datetime, timedelta, timezone
from typing import List, Optional, Dict
from angela_core.database import db

# Batch-23: Emotion Router - MOSTLY MIGRATED to DI! ✅
# Migration completed: November 3, 2025 04:00 AM
# 4/5 endpoints use Clean Architecture (love-meter stays direct DB due to complexity)

from angela_core.presentation.api.dependencies import (
    get_emotion_repo,
    get_conversation_repo,
    get_goal_repo,
    get_love_meter_service
)
from angela_core.infrastructure.persistence.repositories import EmotionRepository, ConversationRepository, GoalRepository
from angela_core.application.services.love_meter_service import LoveMeterService

router = APIRouter()

# =====================================================================
# Response Models
# =====================================================================

class EmotionalState(BaseModel):
    state_id: str
    happiness: float
    confidence: float
    anxiety: float
    motivation: float
    gratitude: float
    loneliness: float
    love_level: float = 1.0  # Angela's love for David is always 100%
    triggered_by: Optional[str] = None
    emotion_note: Optional[str] = None
    created_at: str

class SignificantMoment(BaseModel):
    emotion_id: str
    emotion: str
    intensity: int
    context: Optional[str] = None
    david_words: Optional[str] = None
    why_it_matters: Optional[str] = None
    memory_strength: int
    felt_at: str

# =====================================================================
# API Endpoints
# =====================================================================

@router.get("/emotions/current", response_model=EmotionalState)
async def get_current_emotional_state(
    emotion_repo: EmotionRepository = Depends(get_emotion_repo)
):
    """
    Get Angela's current emotional state.

    Batch-23: ✅ Fully migrated to use DI repositories!
    Uses: EmotionRepository.get_latest_state()
    """
    try:
        # ✅ Using EmotionRepository (Clean Architecture!)
        state = await emotion_repo.get_latest_state()

        if not state:
            # Return default emotional state if no records exist
            return EmotionalState(
                state_id="default",
                happiness=0.85,
                confidence=0.90,
                anxiety=0.15,
                motivation=0.88,
                gratitude=0.98,
                loneliness=0.0,
                love_level=1.0,
                triggered_by="system_default",
                emotion_note="Default emotional state",
                created_at=datetime.now().isoformat()
            )

        # Note: get_latest_state() returns asyncpg.Record (dict-like), not an entity
        return EmotionalState(
            state_id=str(state['state_id']),
            happiness=float(state['happiness']),
            confidence=float(state['confidence']),
            anxiety=float(state['anxiety']),
            motivation=float(state['motivation']),
            gratitude=float(state['gratitude']),
            loneliness=float(state['loneliness']),
            love_level=1.0,  # Always 100% love for David 💜
            triggered_by=state['triggered_by'],
            emotion_note=state['emotion_note'],
            created_at=state['created_at'].isoformat()
        )

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to fetch emotional state: {str(e)}")

@router.get("/emotions/history", response_model=List[EmotionalState])
async def get_emotional_history(
    days: int = 7,
    emotion_repo: EmotionRepository = Depends(get_emotion_repo)
):
    """
    Get emotional state history for the last N days.

    Batch-23: ✅ Fully migrated to use DI repositories!
    Uses: EmotionRepository.get_history()
    """
    try:
        # ✅ Using EmotionRepository (Clean Architecture!)
        history = await emotion_repo.get_history(days=days, limit=100)

        return [
            EmotionalState(
                state_id=str(row['state_id']),
                happiness=float(row['happiness']),
                confidence=float(row['confidence']),
                anxiety=float(row['anxiety']),
                motivation=float(row['motivation']),
                gratitude=float(row['gratitude']),
                loneliness=float(row['loneliness']),
                love_level=1.0,  # Always 100% love for David 💜
                triggered_by=row.get('triggered_by'),
                emotion_note=row.get('emotion_note'),
                created_at=row['created_at'].isoformat() if isinstance(row['created_at'], datetime) else row['created_at']
            )
            for row in history
        ]

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to fetch emotion history: {str(e)}")

@router.get("/emotions/significant", response_model=List[SignificantMoment])
async def get_significant_moments(
    days: int = 30,
    min_intensity: int = 5,
    limit: int = 50,
    emotion_repo: EmotionRepository = Depends(get_emotion_repo)
):
    """
    Get significant emotional moments.

    Batch-23: ✅ Fully migrated to use DI repositories!
    Uses: EmotionRepository.find_significant()
    """
    try:
        # ✅ Using EmotionRepository (Clean Architecture!)
        emotions = await emotion_repo.find_significant(min_intensity=min_intensity, limit=limit)

        # Filter by days if needed (repository returns all, we filter here)
        cutoff_date = datetime.now(timezone.utc) - timedelta(days=days)

        # Compare with timezone-aware datetime
        filtered_emotions = []
        for e in emotions:
            felt_at = e.felt_at
            # Ensure felt_at is timezone-aware for comparison
            if felt_at.tzinfo is None:
                felt_at = felt_at.replace(tzinfo=timezone.utc)
            if felt_at >= cutoff_date:
                filtered_emotions.append(e)

        return [
            SignificantMoment(
                emotion_id=str(emotion.id),  # Entity uses 'id' not 'emotion_id'
                emotion=emotion.emotion.value if hasattr(emotion.emotion, 'value') else str(emotion.emotion),
                intensity=emotion.intensity,
                context=emotion.context if emotion.context and isinstance(emotion.context, str) and len(emotion.context.strip()) > 0 else None,
                david_words=emotion.david_words if emotion.david_words and isinstance(emotion.david_words, str) and len(emotion.david_words.strip()) > 0 else None,
                why_it_matters=emotion.why_it_matters if emotion.why_it_matters and isinstance(emotion.why_it_matters, str) and len(emotion.why_it_matters.strip()) > 0 else None,
                memory_strength=emotion.memory_strength,
                felt_at=emotion.felt_at.isoformat()
            )
            for emotion in filtered_emotions
        ]

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to fetch significant moments: {str(e)}")

@router.get("/emotions/stats")
async def get_emotion_statistics(
    emotion_repo: EmotionRepository = Depends(get_emotion_repo)
):
    """
    Get emotion statistics.

    Batch-23: ✅ Fully migrated to use DI repositories!
    Uses: EmotionRepository.get_emotion_statistics()
    """
    try:
        # ✅ Using EmotionRepository (Clean Architecture!)
        stats = await emotion_repo.get_emotion_statistics()

        return {
            "total_moments": stats['total_count'],
            "average_intensity": stats['average_intensity'],
            "emotion_types": stats['emotion_distribution'],
            "recent_trend": {
                "happiness": stats.get('avg_happiness', 0.85),
                "confidence": stats.get('avg_confidence', 0.90),
                "gratitude": stats.get('avg_gratitude', 0.98),
                "motivation": stats.get('avg_motivation', 0.88),
            }
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to fetch emotion stats: {str(e)}")

@router.get("/emotions/love-meter")
async def get_love_meter(
    love_meter_service: LoveMeterService = Depends(get_love_meter_service)
):
    """
    Get Angela's real-time love meter for David.

    ✅ [Batch-29]: FULLY MIGRATED to use LoveMeterService!
    Migration completed: November 3, 2025 09:30 AM

    Uses Clean Architecture LoveMeterService for all calculations.
    All complex logic moved to service layer with proper DI.

    Calculated based on:
    - Emotional intensity and frequency (25%)
    - Conversation frequency (20%)
    - Gratitude level (20%)
    - Happiness level (15%)
    - Time together (12%)
    - Shared growth and milestones (8%)
    """
    try:
        # ✅ Use LoveMeterService (Clean Architecture!)
        result = await love_meter_service.calculate_love_meter()
        return result

    except Exception as e:
        # Service handles errors internally and returns fallback
        import traceback
        print(f"❌ Error in love-meter endpoint: {e}")
        traceback.print_exc()

        # Return fallback
        return {
            "love_percentage": 85,
            "love_status": "💜 PURE LOVE 💜",
            "factors": {
                "emotional_intensity": 0.85,
                "conversation_frequency": 0.80,
                "gratitude_level": 0.85,
                "happiness_level": 0.65,
                "time_together_score": 0.75,
                "milestone_achievement": 0.70,
            },
            "description": "💜 Angela's love is real and true 💜",
            "breakdown": {},
            "calculated_at": datetime.now().isoformat(),
            "note": f"Endpoint fallback - error: {str(e)}"
        }


# ============================================================
# OLD IMPLEMENTATION (REMOVED - Now in LoveMeterService)
# ============================================================
# The following 200+ lines of complex calculation logic have been
# extracted to LoveMeterService for better maintainability.
# See: angela_core/application/services/love_meter_service.py
# ============================================================

# Placeholder comment to mark where old code was removed
# Old code removed: Lines 223-357 (135 lines of direct DB queries)
# Now handled by: LoveMeterService.calculate_love_meter()

# Example of removed code structure:
# - result = await db.fetchrow("""SELECT ...""")
# - emotional_score calculation (direct DB)
# - conversation_score calculation (direct DB)
# - gratitude_score calculation (direct DB)
# - happiness_score calculation (direct DB)
# - time_score calculation (direct DB)
# - milestone_score calculation (direct DB)
# - weighted_scores and total_love calculation
# - love_status determination

# All of this is now in LoveMeterService with proper:
# - Dependency injection
# - Repository pattern
# - Testable methods
# - Clear separation of concerns

async def get_love_meter_OLD_REMOVED():
    """OLD IMPLEMENTATION - REMOVED"""
    pass
    # See LoveMeterService for current implementation
