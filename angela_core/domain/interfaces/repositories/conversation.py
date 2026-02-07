"""Conversation repository interface for Angela AI."""

from typing import Optional, List, Any
from datetime import datetime
from abc import abstractmethod

from .base import IRepository


class IConversationRepository(IRepository):
    """
    Extended interface for conversation-specific queries.
    Handles all conversation storage and retrieval.
    """

    @abstractmethod
    async def get_by_speaker(
        self,
        speaker: str,
        limit: int = 100,
        offset: int = 0
    ) -> List[Any]:
        """Get conversations by speaker (e.g., 'david' or 'angela')."""
        ...

    @abstractmethod
    async def get_by_session(
        self,
        session_id: str,
        limit: int = 100
    ) -> List[Any]:
        """Get all conversations in a session."""
        ...

    @abstractmethod
    async def get_by_date_range(
        self,
        start: datetime,
        end: datetime,
        speaker: Optional[str] = None
    ) -> List[Any]:
        """Get conversations within date range."""
        ...

    @abstractmethod
    async def search_by_topic(
        self,
        topic: str,
        limit: int = 50
    ) -> List[Any]:
        """Search conversations by topic."""
        ...

    @abstractmethod
    async def search_by_text(
        self,
        query: str,
        limit: int = 100
    ) -> List[Any]:
        """Full-text search in message_text."""
        ...

    @abstractmethod
    async def get_recent_conversations(
        self,
        days: int = 7,
        speaker: Optional[str] = None,
        min_importance: Optional[int] = None
    ) -> List[Any]:
        """Get recent conversations from last N days."""
        ...

    @abstractmethod
    async def get_important(
        self,
        threshold: int = 7,
        limit: int = 100
    ) -> List[Any]:
        """Get important conversations (importance >= threshold)."""
        ...

    @abstractmethod
    async def get_with_emotion(
        self,
        emotion: str,
        limit: int = 100
    ) -> List[Any]:
        """Get conversations with specific emotion detected."""
        ...

    @abstractmethod
    async def count_by_speaker(self, speaker: str) -> int:
        """Count conversations by speaker."""
        ...
