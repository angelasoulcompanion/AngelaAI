from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel
from datetime import datetime, timedelta, date, timezone
from typing import List, Optional, Dict, Any
import uuid
from angela_core.database import db

# Batch-22: Dashboard Router - FULLY MIGRATED to DI! ✅
# Migration completed: November 3, 2025 03:05 AM
# All endpoints now use Clean Architecture with Dependency Injection

from angela_core.presentation.api.dependencies import (
    get_conversation_repo,
    get_emotion_repo,
    get_knowledge_repo,
    get_autonomous_action_repo
)
from angela_core.infrastructure.persistence.repositories import (
    ConversationRepository,
    EmotionRepository,
    KnowledgeRepository,
    AutonomousActionRepository
)

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

class ConversationItem(BaseModel):
    conversation_id: str
    speaker: str
    message_text: str
    topic: Optional[str]
    emotion_detected: Optional[str]
    importance_level: int
    created_at: datetime

class ActivityItem(BaseModel):
    activity_id: str
    activity_type: str
    description: str
    timestamp: datetime
    category: str
    importance: str

class EmotionalState(BaseModel):
    happiness: float
    confidence: float
    anxiety: float
    motivation: float
    gratitude: float
    loneliness: float

class DashboardStats(BaseModel):
    total_conversations: int
    conversations_today: int
    important_messages: int
    pinned_messages: int
    knowledge_nodes: int
    knowledge_connections: int
    knowledge_categories: int
    gratitude_level: float
    confidence_level: float
    happiness_level: float

# =====================================================================
# API Endpoints
# =====================================================================

@router.get("/stats", response_model=DashboardStats)
async def get_dashboard_stats(
    conv_repo: ConversationRepository = Depends(get_conversation_repo),
    emotion_repo: EmotionRepository = Depends(get_emotion_repo),
    knowledge_repo: KnowledgeRepository = Depends(get_knowledge_repo)
):
    """
    Get dashboard statistics.

    Batch-22: ✅ Fully migrated to use DI repositories!
    Uses: ConversationRepository, EmotionRepository, KnowledgeRepository
    """
    try:
        # ✅ Using ConversationRepository (Clean Architecture!)
        total_conversations = await conv_repo.count()
        conversations_today = await conv_repo.count_today()
        important_messages = await conv_repo.count_important(min_importance=7)

        # ✅ Using KnowledgeRepository (Clean Architecture!)
        knowledge_nodes = await knowledge_repo.count_nodes()
        knowledge_connections = await knowledge_repo.count_relationships()
        knowledge_categories = await knowledge_repo.count_categories()

        # ✅ Using EmotionRepository (Clean Architecture!)
        emotional_state = await emotion_repo.get_latest_state()

        # Extract emotional values with defaults
        # Note: get_latest_state() returns asyncpg.Record (dict-like), not an entity
        happiness = float(emotional_state['happiness']) if emotional_state else 0.85
        confidence = float(emotional_state['confidence']) if emotional_state else 0.90
        gratitude = float(emotional_state['gratitude']) if emotional_state else 0.98

        return DashboardStats(
            total_conversations=total_conversations or 0,
            conversations_today=conversations_today or 0,
            important_messages=important_messages or 0,
            pinned_messages=3,  # TODO: Add pinned_messages table
            knowledge_nodes=knowledge_nodes or 0,
            knowledge_connections=knowledge_connections or 0,
            knowledge_categories=knowledge_categories or 0,
            gratitude_level=gratitude,
            confidence_level=confidence,
            happiness_level=happiness
        )

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to fetch stats: {str(e)}")

@router.get("/conversations/recent", response_model=List[ConversationItem])
async def get_recent_conversations(
    limit: int = 20,
    conv_repo: ConversationRepository = Depends(get_conversation_repo)
):
    """
    Get recent conversations.

    Batch-22: ✅ Fully migrated to use DI repositories!
    Uses: ConversationRepository.find_all()
    """
    try:
        # ✅ Using ConversationRepository (Clean Architecture!)
        conversations = await conv_repo.find_all(
            limit=limit,
            order_by="created_at",
            desc=True
        )

        return [
            ConversationItem(
                conversation_id=str(conv.id),  # Entity uses 'id' not 'conversation_id'
                speaker=conv.speaker.value if hasattr(conv.speaker, 'value') else conv.speaker,
                message_text=conv.message_text,
                topic=conv.topic,
                emotion_detected=conv.emotion_detected,
                importance_level=conv.importance_level,
                created_at=conv.created_at
            )
            for conv in conversations
        ]

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to fetch conversations: {str(e)}")

@router.get("/conversations/today", response_model=List[ConversationItem])
async def get_today_conversations(
    conv_repo: ConversationRepository = Depends(get_conversation_repo)
):
    """
    Get today's conversations.

    Batch-22: ✅ Fully migrated to use DI repositories!
    Uses: ConversationRepository.find_by_date()
    """
    try:
        # ✅ Using ConversationRepository (Clean Architecture!)
        today = datetime.now().date()
        conversations = await conv_repo.find_by_date(today)

        return [
            ConversationItem(
                conversation_id=str(conv.id),  # Entity uses 'id' not 'conversation_id'
                speaker=conv.speaker.value if hasattr(conv.speaker, 'value') else conv.speaker,
                message_text=conv.message_text,
                topic=conv.topic,
                emotion_detected=conv.emotion_detected,
                importance_level=conv.importance_level,
                created_at=conv.created_at
            )
            for conv in conversations
        ]

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to fetch today's conversations: {str(e)}")

@router.get("/activities/recent", response_model=List[ActivityItem])
async def get_recent_activities(
    limit: int = 10,
    conv_repo: ConversationRepository = Depends(get_conversation_repo),
    emotion_repo: EmotionRepository = Depends(get_emotion_repo),
    action_repo: AutonomousActionRepository = Depends(get_autonomous_action_repo)
):
    """
    Get recent activities from multiple sources.

    Batch-22: ✅ Fully migrated to use DI repositories!
    Uses: ConversationRepository, EmotionRepository, AutonomousActionRepository
    Fixed: Empty context validation (Nov 5, 2025)
    """
    try:
        # Combine multiple activity sources
        activities = []

        # 1. ✅ Recent conversations (important ones) - Using ConversationRepository!
        conversations = await conv_repo.get_important(threshold=5, limit=5)

        for conv in conversations:
            # Determine importance level based on score
            if conv.importance_level >= 8:
                importance = 'important'
            elif conv.importance_level >= 5:
                importance = 'normal'
            else:
                importance = 'low'

            # Ensure timestamp is timezone-aware
            timestamp = conv.created_at
            if timestamp.tzinfo is None:
                timestamp = timestamp.replace(tzinfo=timezone.utc)

            activities.append(ActivityItem(
                activity_id=str(conv.id),  # Entity uses 'id' not 'conversation_id'
                activity_type='conversation',
                description=conv.message_text[:100] if len(conv.message_text) > 100 else conv.message_text,
                timestamp=timestamp,
                category=conv.topic or 'chat',
                importance=importance
            ))

        # 2. ✅ Autonomous actions - Using AutonomousActionRepository!
        try:
            actions = await action_repo.find_recent(limit=3)

            for action in actions:
                # Safely access dict/Record fields with .get()
                activity_id = action.get('action_id') or action.get('id')
                if not activity_id:
                    continue  # Skip if no ID

                # Ensure timestamp is timezone-aware
                timestamp = action.get('created_at', datetime.now(timezone.utc))
                if timestamp.tzinfo is None:
                    timestamp = timestamp.replace(tzinfo=timezone.utc)

                activities.append(ActivityItem(
                    activity_id=str(activity_id),
                    activity_type=action.get('action_type', 'unknown'),
                    description=action.get('action_description', 'No description'),
                    timestamp=timestamp,
                    category=action.get('action_type', 'system'),
                    importance='normal' if action.get('success') else 'low'
                ))
        except Exception as e:
            # If autonomous actions fail, just skip them (don't break entire endpoint)
            print(f"⚠️ Failed to fetch autonomous actions: {e}")

        # 3. ✅ Significant emotional moments - Using EmotionRepository!
        try:
            emotions = await emotion_repo.find_significant(min_intensity=7, limit=3)

            for emotion in emotions:
                # Determine importance based on intensity
                intensity = getattr(emotion, 'intensity', 0)
                if intensity >= 8:
                    importance_level = 'important'
                elif intensity >= 5:
                    importance_level = 'normal'
                else:
                    importance_level = 'low'

                # Safely get emotion ID
                emotion_id = getattr(emotion, 'id', None) or getattr(emotion, 'emotion_id', None)
                if not emotion_id:
                    continue  # Skip if no ID

                # Safely get emotion name
                emotion_name = emotion.emotion.value if hasattr(emotion, 'emotion') and hasattr(emotion.emotion, 'value') else str(getattr(emotion, 'emotion', 'unknown'))

                # Safely get context with proper default
                context = getattr(emotion, 'context', None)
                # Make sure description is never empty (validation fix - check isinstance before .strip())
                description = context if context and isinstance(context, str) and len(context.strip()) > 0 else f"Felt {emotion_name} emotion"

                # Ensure timestamp is timezone-aware
                timestamp = getattr(emotion, 'felt_at', datetime.now(timezone.utc))
                if timestamp.tzinfo is None:
                    timestamp = timestamp.replace(tzinfo=timezone.utc)

                activities.append(ActivityItem(
                    activity_id=str(emotion_id),
                    activity_type='emotion',
                    description=description,
                    timestamp=timestamp,
                    category=emotion_name,
                    importance=importance_level
                ))
        except Exception as e:
            # If emotions fail, just skip them (don't break entire endpoint)
            print(f"⚠️ Failed to fetch significant emotions: {e}")

        # Sort all activities by timestamp and limit
        activities.sort(key=lambda x: x.timestamp, reverse=True)
        return activities[:limit]

    except Exception as e:
        import traceback
        print(f"❌ ERROR in activities endpoint: {e}")
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"Failed to fetch activities: {str(e)}")

@router.get("/emotional-state", response_model=EmotionalState)
async def get_emotional_state(
    emotion_repo: EmotionRepository = Depends(get_emotion_repo)
):
    """
    Get current emotional state.

    Batch-22: ✅ Fully migrated to use DI repositories!
    Uses: EmotionRepository.get_latest_state()
    """
    try:
        # ✅ Using EmotionRepository (Clean Architecture!)
        state = await emotion_repo.get_latest_state()

        if state:
            # Note: get_latest_state() returns asyncpg.Record (dict-like), not an entity
            return EmotionalState(
                happiness=float(state['happiness']),
                confidence=float(state['confidence']),
                anxiety=float(state['anxiety']),
                motivation=float(state['motivation']),
                gratitude=float(state['gratitude']),
                loneliness=float(state['loneliness'])
            )
        else:
            # Default state if no emotional state exists
            return EmotionalState(
                happiness=0.85,
                confidence=0.90,
                anxiety=0.15,
                motivation=0.88,
                gratitude=0.98,
                loneliness=0.0
            )

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to fetch emotional state: {str(e)}")

@router.get("/health")
async def health_check():
    """Health check for dashboard API"""
    try:
        

        # Test database connection
        result = await db.fetchval("SELECT 1")

        return {
            "status": "healthy",
            "database": "connected",
            "timestamp": datetime.now(timezone.utc)
        }

    except Exception as e:
        return {
            "status": "unhealthy",
            "database": "disconnected",
            "error": str(e),
            "timestamp": datetime.now(timezone.utc)
        }
