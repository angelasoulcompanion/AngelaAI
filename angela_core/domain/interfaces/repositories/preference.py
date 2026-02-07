"""Preference repository interface for Angela AI."""

from typing import Optional, List, Dict, Any
from uuid import UUID
from abc import abstractmethod

from .base import IRepository


class IPreferenceRepository(IRepository):
    """
    Extended interface for preference queries.

    Handles David's learned preferences - specific likes, dislikes,
    and style choices observed through interactions.

    Part of: Self-Learning System (Phase 5+)
    """

    @abstractmethod
    async def find_by_category(
        self,
        category: str,
        min_confidence: float = 0.0,
        limit: int = 50
    ) -> List[Any]:
        """
        Find preferences by category.

        Args:
            category: Preference category (communication, technical, emotional, etc.)
            min_confidence: Minimum confidence level
            limit: Maximum number of results

        Returns:
            List of PreferenceItem entities in category
        """
        ...

    @abstractmethod
    async def find_by_key(
        self,
        preference_key: str,
        category: Optional[str] = None
    ) -> Optional[Any]:
        """
        Find preference by key.

        Args:
            preference_key: Unique preference key
            category: Optional category filter

        Returns:
            PreferenceItem if found, None otherwise
        """
        ...

    @abstractmethod
    async def get_strong_preferences(
        self,
        min_confidence: float = 0.8,
        min_evidence: int = 3,
        category: Optional[str] = None,
        limit: int = 50
    ) -> List[Any]:
        """
        Get strong, reliable preferences.

        Args:
            min_confidence: Minimum confidence threshold
            min_evidence: Minimum evidence count
            category: Optional category filter
            limit: Maximum number of results

        Returns:
            List of strong PreferenceItem entities
        """
        ...

    @abstractmethod
    async def update_confidence(
        self,
        preference_id: UUID,
        new_confidence: float
    ) -> None:
        """
        Update preference confidence score.

        Args:
            preference_id: Preference UUID
            new_confidence: New confidence value (0.0-1.0)

        Raises:
            EntityNotFoundError: If preference not found
            ValueError: If confidence out of range
        """
        ...

    @abstractmethod
    async def add_evidence(
        self,
        preference_id: UUID,
        conversation_id: UUID
    ) -> None:
        """
        Add evidence supporting a preference.

        Adds conversation to evidence list, increments count,
        and boosts confidence using diminishing returns.

        Args:
            preference_id: Preference UUID
            conversation_id: Supporting conversation UUID

        Raises:
            EntityNotFoundError: If preference not found
        """
        ...

    @abstractmethod
    async def count_by_category(self, category: str) -> int:
        """
        Count preferences by category.

        Args:
            category: Preference category

        Returns:
            Number of preferences in category
        """
        ...

    @abstractmethod
    async def get_all_preferences_summary(self) -> Dict[str, Any]:
        """
        Get summary of all preferences.

        Returns:
            Dictionary with:
            - total_preferences: Total count
            - by_category: Dict mapping category to count
            - strong_preferences: Count with confidence >= 0.8
            - average_confidence: Average confidence score
            - average_evidence: Average evidence count
        """
        ...
