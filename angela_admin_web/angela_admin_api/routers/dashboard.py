from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from datetime import datetime, timedelta
from typing import List, Optional, Dict, Any
import uuid
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
async def get_dashboard_stats():
    """Get dashboard statistics"""
    try:
        

        # Get total conversations
        total_conversations = await db.fetchval(
            "SELECT COUNT(*) FROM conversations"
        )

        # Get conversations today
        conversations_today = await db.fetchval(
            "SELECT COUNT(*) FROM conversations WHERE DATE(created_at) = CURRENT_DATE"
        )

        # Get important messages (importance >= 7)
        important_messages = await db.fetchval(
            "SELECT COUNT(*) FROM conversations WHERE importance_level >= 7"
        )

        # Get knowledge nodes
        knowledge_nodes = await db.fetchval(
            "SELECT COUNT(*) FROM knowledge_nodes"
        )

        # Get knowledge connections
        knowledge_connections = await db.fetchval(
            "SELECT COUNT(*) FROM knowledge_relationships"
        )

        # Get knowledge categories
        knowledge_categories = await db.fetchval(
            "SELECT COUNT(DISTINCT concept_category) FROM knowledge_nodes WHERE concept_category IS NOT NULL"
        )

        # Get latest emotional state
        emotional_state = await db.fetchrow(
            """
            SELECT happiness, confidence, gratitude
            FROM emotional_states
            ORDER BY created_at DESC
            LIMIT 1
            """
        )

        # Default emotional values if no state exists
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
async def get_recent_conversations(limit: int = 20):
    """Get recent conversations"""
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
                created_at
            FROM conversations
            ORDER BY created_at DESC
            LIMIT $1
            """,
            limit
        )

        return [
            ConversationItem(
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

@router.get("/conversations/today", response_model=List[ConversationItem])
async def get_today_conversations():
    """Get today's conversations"""
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
                created_at
            FROM conversations
            WHERE DATE(created_at) = CURRENT_DATE
            ORDER BY created_at DESC
            """
        )

        return [
            ConversationItem(
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
        raise HTTPException(status_code=500, detail=f"Failed to fetch today's conversations: {str(e)}")

@router.get("/activities/recent", response_model=List[ActivityItem])
async def get_recent_activities(limit: int = 10):
    """Get recent activities from multiple sources"""
    try:
        

        # Combine multiple activity sources
        activities = []

        # 1. Recent conversations (important ones)
        conversations = await db.fetch(
            """
            SELECT
                conversation_id::text as id,
                'conversation' as type,
                LEFT(message_text, 100) as description,
                created_at as timestamp,
                topic as category,
                CASE
                    WHEN importance_level >= 8 THEN 'important'
                    WHEN importance_level >= 5 THEN 'normal'
                    ELSE 'low'
                END as importance
            FROM conversations
            WHERE importance_level >= 5
            ORDER BY created_at DESC
            LIMIT 5
            """
        )

        for row in conversations:
            activities.append(ActivityItem(
                activity_id=row['id'],
                activity_type=row['type'],
                description=row['description'],
                timestamp=row['timestamp'],
                category=row['category'] or 'chat',
                importance=row['importance']
            ))

        # 2. Autonomous actions
        actions = await db.fetch(
            """
            SELECT
                action_id::text as id,
                action_type as type,
                action_description as description,
                created_at as timestamp,
                action_type as category,
                CASE
                    WHEN success = true THEN 'normal'
                    ELSE 'low'
                END as importance
            FROM autonomous_actions
            ORDER BY created_at DESC
            LIMIT 3
            """
        )

        for row in actions:
            activities.append(ActivityItem(
                activity_id=row['id'],
                activity_type=row['type'],
                description=row['description'],
                timestamp=row['timestamp'],
                category=row['category'],
                importance=row['importance']
            ))

        # 3. Significant emotional moments
        emotions = await db.fetch(
            """
            SELECT
                emotion_id::text as id,
                'emotion' as type,
                context as description,
                felt_at as timestamp,
                emotion as category,
                CASE
                    WHEN intensity >= 8 THEN 'important'
                    WHEN intensity >= 5 THEN 'normal'
                    ELSE 'low'
                END as importance
            FROM angela_emotions
            WHERE intensity >= 7
            ORDER BY felt_at DESC
            LIMIT 3
            """
        )

        for row in emotions:
            activities.append(ActivityItem(
                activity_id=row['id'],
                activity_type=row['type'],
                description=row['description'],
                timestamp=row['timestamp'],
                category=row['category'],
                importance=row['importance']
            ))        # Sort all activities by timestamp and limit
        activities.sort(key=lambda x: x.timestamp, reverse=True)
        return activities[:limit]

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to fetch activities: {str(e)}")

@router.get("/emotional-state", response_model=EmotionalState)
async def get_emotional_state():
    """Get current emotional state"""
    try:
        

        row = await db.fetchrow(
            """
            SELECT
                happiness,
                confidence,
                anxiety,
                motivation,
                gratitude,
                loneliness
            FROM emotional_states
            ORDER BY created_at DESC
            LIMIT 1
            """
        )

        if row:
            return EmotionalState(
                happiness=float(row['happiness']),
                confidence=float(row['confidence']),
                anxiety=float(row['anxiety']),
                motivation=float(row['motivation']),
                gratitude=float(row['gratitude']),
                loneliness=float(row['loneliness'])
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
            "timestamp": datetime.now()
        }

    except Exception as e:
        return {
            "status": "unhealthy",
            "database": "disconnected",
            "error": str(e),
            "timestamp": datetime.now()
        }
