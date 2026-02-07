"""Emotion repository interface for Angela AI."""

from typing import Optional, List, Dict, Any
from uuid import UUID
from datetime import datetime
from abc import abstractmethod

from .base import IRepository


class IEmotionRepository(IRepository):
    """
    Extended interface for emotion-specific queries.
    Handles significant emotional moments storage.
    """

    @abstractmethod
    async def get_by_emotion_type(
        self,
        emotion_type: str,
        min_intensity: Optional[int] = None,
        limit: int = 50
    ) -> List[Any]:
        """Get emotions by type with optional intensity filter."""
        ...

    @abstractmethod
    async def get_recent_emotions(
        self,
        days: int = 7,
        min_intensity: Optional[int] = None
    ) -> List[Any]:
        """Get recent emotions from last N days."""
        ...

    @abstractmethod
    async def get_intense(
        self,
        threshold: int = 7,
        limit: int = 100
    ) -> List[Any]:
        """Get intense emotions (intensity >= threshold)."""
        ...

    @abstractmethod
    async def get_strongly_remembered(
        self,
        threshold: int = 8,
        limit: int = 100
    ) -> List[Any]:
        """Get strongly remembered emotions (memory_strength >= threshold)."""
        ...

    @abstractmethod
    async def get_about_david(
        self,
        limit: int = 100
    ) -> List[Any]:
        """Get emotions involving David."""
        ...

    @abstractmethod
    async def get_by_conversation(
        self,
        conversation_id: UUID,
        limit: int = 100
    ) -> List[Any]:
        """Get emotions linked to a conversation."""
        ...

    @abstractmethod
    async def get_positive(
        self,
        limit: int = 100
    ) -> List[Any]:
        """Get positive emotions."""
        ...

    @abstractmethod
    async def get_negative(
        self,
        limit: int = 100
    ) -> List[Any]:
        """Get negative emotions."""
        ...

    @abstractmethod
    async def get_reflected(
        self,
        limit: int = 100
    ) -> List[Any]:
        """Get emotions that have been reflected upon (reflection_count > 0)."""
        ...

    @abstractmethod
    async def count_by_emotion_type(self, emotion_type: str) -> int:
        """Count emotions by type."""
        ...

    @abstractmethod
    async def get_emotion_statistics(
        self,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None
    ) -> Dict[str, Any]:
        """
        Get emotion statistics.

        Returns:
            {
                'total_count': int,
                'by_emotion': Dict[str, int],
                'avg_intensity': float,
                'most_common_emotion': str
            }
        """
        ...
