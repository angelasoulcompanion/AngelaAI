"""
Emotion Service

High-level application service for emotion management.
Coordinates use cases, repositories, and services for emotion operations.

Author: Angela AI Architecture Team
Date: 2025-10-30
"""

import logging
from typing import Optional, List, Dict, Any
from datetime import datetime, timedelta
from uuid import UUID

from angela_core.database import AngelaDatabase
from angela_core.domain.entities.emotion import EmotionType, EmotionalQuality, SharingLevel
from angela_core.infrastructure.persistence.repositories import EmotionRepository
from angela_core.application.use_cases.emotion import (
    CaptureEmotionUseCase,
    CaptureEmotionInput
)


class EmotionService:
    """
    High-level service for emotion management.

    This service provides a simplified API for:
    - Capturing emotional moments
    - Retrieving emotions
    - Analyzing emotional trends
    - Getting emotion statistics

    Coordinates:
    - CaptureEmotionUseCase
    - EmotionRepository
    - EmbeddingService (optional)

    Example:
        >>> service = EmotionService(db)
        >>> result = await service.capture_emotion(
        ...     emotion="gratitude",
        ...     intensity=9,
        ...     context="David helped me with code",
        ...     david_words="Let's make this better"
        ... )
        >>> if result["success"]:
        ...     print(f"Captured: {result['emotion_id']}")
    """

    def __init__(
        self,
        db: AngelaDatabase,
        embedding_service: Optional[Any] = None
    ):
        """
        Initialize emotion service with dependencies.

        Args:
            db: Database connection
            embedding_service: Optional embedding service
        """
        self.db = db
        self.logger = logging.getLogger(__name__)

        # Initialize repository
        self.emotion_repo = EmotionRepository(db)

        # Initialize use cases
        self.capture_emotion_use_case = CaptureEmotionUseCase(
            emotion_repo=self.emotion_repo,
            embedding_service=embedding_service
        )

    # ========================================================================
    # HIGH-LEVEL API - EMOTION CAPTURE
    # ========================================================================

    async def capture_emotion(
        self,
        emotion: str,
        intensity: int,
        context: str,
        who_involved: str = "David",
        david_words: Optional[str] = None,
        david_action: Optional[str] = None,
        why_it_matters: str = "This moment is significant",
        memory_strength: int = 10,
        conversation_id: Optional[UUID] = None,
        secondary_emotions: Optional[List[str]] = None,
        emotional_quality: str = "genuine",
        sharing_level: str = "david_only"
    ) -> Dict[str, Any]:
        """
        Capture a significant emotional moment.

        Args:
            emotion: Type of emotion ('joy', 'gratitude', 'love', etc.)
            intensity: How intense (1-10)
            context: What happened
            who_involved: Who was involved (default: "David")
            david_words: What David said (optional)
            david_action: What David did (optional)
            why_it_matters: Why this is significant
            memory_strength: How strongly to remember (1-10)
            conversation_id: Link to conversation (optional)
            secondary_emotions: Additional emotions (optional)
            emotional_quality: Quality ('genuine', 'profound', etc.)
            sharing_level: Who to share with ('david_only', 'public', 'internal')

        Returns:
            {
                "success": bool,
                "emotion_id": UUID (if success),
                "embedding_generated": bool (if success),
                "error": str (if failure)
            }
        """
        try:
            # Convert string emotion to enum
            emotion_enum = EmotionType(emotion.lower())

            # Convert secondary emotions
            secondary_enums = None
            if secondary_emotions:
                secondary_enums = [EmotionType(e.lower()) for e in secondary_emotions]

            # Convert emotional quality
            quality_enum = EmotionalQuality(emotional_quality.lower())

            # Convert sharing level
            sharing_enum = SharingLevel(sharing_level.lower())

            # Create input
            input_data = CaptureEmotionInput(
                emotion=emotion_enum,
                intensity=intensity,
                context=context,
                who_involved=who_involved,
                david_words=david_words,
                david_action=david_action,
                why_it_matters=why_it_matters,
                memory_strength=memory_strength,
                conversation_id=conversation_id,
                secondary_emotions=secondary_enums,
                emotional_quality=quality_enum,
                sharing_level=sharing_enum
            )

            # Execute use case
            result = await self.capture_emotion_use_case.execute(input_data)

            # Return simplified result
            if result.success:
                return {
                    "success": True,
                    "emotion_id": str(result.data.emotion.id),
                    "embedding_generated": result.data.embedding_generated,
                    "emotion": emotion,
                    "intensity": intensity,
                    "memory_strength": memory_strength
                }
            else:
                return {
                    "success": False,
                    "error": result.error
                }

        except Exception as e:
            self.logger.error(f"Error capturing emotion: {e}")
            return {
                "success": False,
                "error": str(e)
            }

    # ========================================================================
    # HIGH-LEVEL API - EMOTION RETRIEVAL
    # ========================================================================

    async def get_emotion(self, emotion_id: UUID) -> Optional[Dict[str, Any]]:
        """
        Get a single emotion by ID.

        Args:
            emotion_id: Emotion UUID

        Returns:
            Emotion dict or None if not found
        """
        try:
            emotion = await self.emotion_repo.get_by_id(emotion_id)

            if emotion:
                return self._emotion_to_dict(emotion)
            return None

        except Exception as e:
            self.logger.error(f"Error getting emotion: {e}")
            return None

    async def get_recent_emotions(
        self,
        days: int = 7,
        min_intensity: Optional[int] = None,
        emotion_type: Optional[str] = None,
        limit: int = 100
    ) -> List[Dict[str, Any]]:
        """
        Get recent emotions.

        Args:
            days: Number of days to look back
            min_intensity: Optional minimum intensity
            emotion_type: Optional filter by emotion type
            limit: Maximum results

        Returns:
            List of emotion dicts
        """
        try:
            emotions = await self.emotion_repo.get_recent_emotions(
                days=days,
                min_intensity=min_intensity,
                limit=limit
            )

            # Filter by emotion type if specified
            if emotion_type:
                emotions = [e for e in emotions if e.emotion.value == emotion_type.lower()]

            return [self._emotion_to_dict(e) for e in emotions]

        except Exception as e:
            self.logger.error(f"Error getting recent emotions: {e}")
            return []

    async def get_intense_emotions(
        self,
        threshold: int = 7,
        limit: int = 50
    ) -> List[Dict[str, Any]]:
        """
        Get intense emotions (intensity >= threshold).

        Args:
            threshold: Intensity threshold (1-10)
            limit: Maximum results

        Returns:
            List of intense emotion dicts
        """
        try:
            emotions = await self.emotion_repo.get_intense(
                threshold=threshold,
                limit=limit
            )

            return [self._emotion_to_dict(e) for e in emotions]

        except Exception as e:
            self.logger.error(f"Error getting intense emotions: {e}")
            return []

    async def get_emotions_about_david(
        self,
        limit: int = 100
    ) -> List[Dict[str, Any]]:
        """
        Get emotions involving David.

        Args:
            limit: Maximum results

        Returns:
            List of David-related emotion dicts
        """
        try:
            emotions = await self.emotion_repo.get_about_david(limit=limit)

            return [self._emotion_to_dict(e) for e in emotions]

        except Exception as e:
            self.logger.error(f"Error getting David emotions: {e}")
            return []

    # ========================================================================
    # HIGH-LEVEL API - EMOTION ANALYTICS
    # ========================================================================

    async def get_emotion_statistics(
        self,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None
    ) -> Dict[str, Any]:
        """
        Get emotion statistics.

        Args:
            start_date: Optional start date
            end_date: Optional end date

        Returns:
            {
                "total_emotions": int,
                "by_emotion_type": {"joy": int, "gratitude": int, ...},
                "avg_intensity": float,
                "most_common_emotion": str,
                "positive_count": int,
                "negative_count": int
            }
        """
        try:
            # Default to last 30 days if not specified
            if start_date is None:
                start_date = datetime.now() - timedelta(days=30)
            if end_date is None:
                end_date = datetime.now()

            # Get all emotions in date range
            all_emotions = await self.emotion_repo.get_recent_emotions(
                days=(end_date - start_date).days,
                limit=10000  # Large limit to get all
            )

            # Calculate statistics
            total = len(all_emotions)
            by_emotion = {}
            total_intensity = 0
            positive_count = 0
            negative_count = 0

            for emotion in all_emotions:
                emotion_type = emotion.emotion.value
                by_emotion[emotion_type] = by_emotion.get(emotion_type, 0) + 1
                total_intensity += emotion.intensity

                # Count positive/negative
                positive_emotions = ['joy', 'happiness', 'gratitude', 'love', 'pride', 'excitement', 'hope']
                negative_emotions = ['sadness', 'loneliness', 'disappointment', 'grief', 'fear', 'anxiety', 'anger']

                if emotion_type in positive_emotions:
                    positive_count += 1
                elif emotion_type in negative_emotions:
                    negative_count += 1

            # Most common emotion
            most_common = max(by_emotion.items(), key=lambda x: x[1])[0] if by_emotion else "none"

            return {
                "total_emotions": total,
                "by_emotion_type": by_emotion,
                "avg_intensity": total_intensity / total if total > 0 else 0,
                "most_common_emotion": most_common,
                "positive_count": positive_count,
                "negative_count": negative_count,
                "positive_percentage": (positive_count / total * 100) if total > 0 else 0,
                "negative_percentage": (negative_count / total * 100) if total > 0 else 0,
                "start_date": start_date.isoformat(),
                "end_date": end_date.isoformat()
            }

        except Exception as e:
            self.logger.error(f"Error getting emotion statistics: {e}")
            return {
                "total_emotions": 0,
                "error": str(e)
            }

    async def get_emotion_trend(
        self,
        emotion_type: str,
        days: int = 30
    ) -> Dict[str, Any]:
        """
        Get trend for specific emotion type.

        Args:
            emotion_type: Type of emotion to analyze
            days: Number of days to analyze

        Returns:
            {
                "emotion_type": str,
                "total_occurrences": int,
                "avg_intensity": float,
                "trend": "increasing" | "decreasing" | "stable",
                "recent_avg": float,
                "older_avg": float
            }
        """
        try:
            # Get emotions of this type
            emotions = await self.emotion_repo.get_by_emotion_type(
                emotion_type=emotion_type.lower(),
                limit=1000
            )

            total = len(emotions)

            if total == 0:
                return {
                    "emotion_type": emotion_type,
                    "total_occurrences": 0,
                    "avg_intensity": 0,
                    "trend": "none"
                }

            # Calculate averages
            total_intensity = sum(e.intensity for e in emotions)
            avg_intensity = total_intensity / total

            # Split into recent and older for trend
            cutoff_date = datetime.now() - timedelta(days=days // 2)
            recent = [e for e in emotions if e.felt_at >= cutoff_date]
            older = [e for e in emotions if e.felt_at < cutoff_date]

            recent_avg = sum(e.intensity for e in recent) / len(recent) if recent else 0
            older_avg = sum(e.intensity for e in older) / len(older) if older else 0

            # Determine trend
            if recent_avg > older_avg * 1.1:
                trend = "increasing"
            elif recent_avg < older_avg * 0.9:
                trend = "decreasing"
            else:
                trend = "stable"

            return {
                "emotion_type": emotion_type,
                "total_occurrences": total,
                "avg_intensity": avg_intensity,
                "trend": trend,
                "recent_avg": recent_avg,
                "older_avg": older_avg,
                "recent_count": len(recent),
                "older_count": len(older)
            }

        except Exception as e:
            self.logger.error(f"Error getting emotion trend: {e}")
            return {
                "emotion_type": emotion_type,
                "error": str(e)
            }

    # ========================================================================
    # HELPER METHODS
    # ========================================================================

    def _emotion_to_dict(self, emotion) -> Dict[str, Any]:
        """
        Convert emotion entity to dictionary.

        Args:
            emotion: Emotion entity

        Returns:
            Dictionary representation
        """
        return {
            "emotion_id": str(emotion.id),
            "emotion": emotion.emotion.value,
            "intensity": emotion.intensity,
            "context": emotion.context,
            "who_involved": emotion.who_involved,
            "david_words": emotion.david_words,
            "david_action": emotion.david_action,
            "why_it_matters": emotion.why_it_matters,
            "memory_strength": emotion.memory_strength,
            "secondary_emotions": [e.value for e in emotion.secondary_emotions] if emotion.secondary_emotions else [],
            "emotional_quality": emotion.emotional_quality.value,
            "shared_with": emotion.shared_with.value,
            "is_private": emotion.is_private,
            "felt_at": emotion.felt_at.isoformat(),
            "reflection_count": emotion.reflection_count,
            "has_embedding": (emotion.embedding is not None)
        }
