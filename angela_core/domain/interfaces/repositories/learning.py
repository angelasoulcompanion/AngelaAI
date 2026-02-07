"""Learning repository interface for Angela AI."""

from typing import Optional, List, Any
from uuid import UUID
from abc import abstractmethod

from .base import IRepository


class ILearningRepository(IRepository):
    """
    Extended interface for learning-specific queries.

    Handles Angela's learnings, knowledge acquisition, and skill development.
    Supports querying by confidence, category, application status, and reinforcement.
    """

    @abstractmethod
    async def get_by_category(
        self,
        category: str,
        limit: int = 100
    ) -> List[Any]:
        """
        Get learnings by category.

        Args:
            category: Learning category (technical, emotional, personal, etc.)
            limit: Maximum number of results

        Returns:
            List of Learning entities
        """
        ...

    @abstractmethod
    async def get_by_confidence(
        self,
        min_confidence: float,
        limit: int = 100
    ) -> List[Any]:
        """
        Get learnings with confidence >= min_confidence.

        Args:
            min_confidence: Minimum confidence level (0.0-1.0)
            limit: Maximum number of results

        Returns:
            List of Learning entities ordered by confidence desc
        """
        ...

    @abstractmethod
    async def get_confident_learnings(
        self,
        category: Optional[str] = None,
        limit: int = 100
    ) -> List[Any]:
        """
        Get high-confidence learnings (confidence >= 0.7).

        Args:
            category: Optional category filter
            limit: Maximum number of results

        Returns:
            List of confident Learning entities
        """
        ...

    @abstractmethod
    async def get_uncertain_learnings(
        self,
        category: Optional[str] = None,
        limit: int = 100
    ) -> List[Any]:
        """
        Get uncertain learnings (confidence < 0.5).

        These learnings need more reinforcement or evidence.

        Args:
            category: Optional category filter
            limit: Maximum number of results

        Returns:
            List of uncertain Learning entities
        """
        ...

    @abstractmethod
    async def get_applied_learnings(
        self,
        category: Optional[str] = None,
        limit: int = 100
    ) -> List[Any]:
        """
        Get learnings that have been applied in practice.

        Args:
            category: Optional category filter
            limit: Maximum number of results

        Returns:
            List of applied Learning entities
        """
        ...

    @abstractmethod
    async def get_unapplied_learnings(
        self,
        min_confidence: float = 0.7,
        limit: int = 100
    ) -> List[Any]:
        """
        Get learnings that have NOT been applied yet.

        Useful for identifying knowledge that should be put into practice.

        Args:
            min_confidence: Minimum confidence level (default 0.7)
            limit: Maximum number of results

        Returns:
            List of unapplied Learning entities
        """
        ...

    @abstractmethod
    async def get_recent_learnings(
        self,
        days: int = 7,
        category: Optional[str] = None,
        limit: int = 100
    ) -> List[Any]:
        """
        Get learnings from the last N days.

        Args:
            days: Number of days to look back
            category: Optional category filter
            limit: Maximum number of results

        Returns:
            List of recent Learning entities
        """
        ...

    @abstractmethod
    async def get_reinforced_learnings(
        self,
        min_times: int = 3,
        category: Optional[str] = None,
        limit: int = 100
    ) -> List[Any]:
        """
        Get learnings that have been reinforced at least N times.

        Args:
            min_times: Minimum reinforcement count
            category: Optional category filter
            limit: Maximum number of results

        Returns:
            List of well-reinforced Learning entities
        """
        ...

    @abstractmethod
    async def get_from_conversation(
        self,
        conversation_id: UUID
    ) -> List[Any]:
        """
        Get all learnings derived from a specific conversation.

        Args:
            conversation_id: ID of the conversation

        Returns:
            List of Learning entities from that conversation
        """
        ...

    @abstractmethod
    async def search_by_topic(
        self,
        query: str,
        limit: int = 20
    ) -> List[Any]:
        """
        Search learnings by topic text (case-insensitive).

        Args:
            query: Search query
            limit: Maximum number of results

        Returns:
            List of matching Learning entities
        """
        ...

    @abstractmethod
    async def get_by_confidence_range(
        self,
        min_confidence: float,
        max_confidence: float,
        category: Optional[str] = None,
        limit: int = 100
    ) -> List[Any]:
        """
        Get learnings within a confidence range.

        Args:
            min_confidence: Minimum confidence (inclusive)
            max_confidence: Maximum confidence (inclusive)
            category: Optional category filter
            limit: Maximum number of results

        Returns:
            List of Learning entities in confidence range
        """
        ...

    @abstractmethod
    async def get_needs_reinforcement(
        self,
        max_confidence: float = 0.7,
        limit: int = 100
    ) -> List[Any]:
        """
        Get learnings that need more reinforcement.

        Identifies learnings with low confidence or few reinforcements.

        Args:
            max_confidence: Maximum confidence (default 0.7)
            limit: Maximum number of results

        Returns:
            List of Learning entities that could use reinforcement
        """
        ...
