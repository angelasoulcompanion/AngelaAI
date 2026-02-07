"""Learning pattern repository interface for Angela AI."""

from typing import Optional, List, Dict, Any
from uuid import UUID
from abc import abstractmethod

from .base import IRepository


class ILearningPatternRepository(IRepository):
    """
    Extended interface for learning pattern queries.

    Handles Angela's learned behavioral patterns - recurring behaviors,
    communication styles, and preferences discovered through observation.

    Part of: Self-Learning System (Phase 5+)
    """

    @abstractmethod
    async def find_by_type(
        self,
        pattern_type: str,
        min_confidence: float = 0.0,
        limit: int = 50
    ) -> List[Any]:
        """
        Find patterns by type with optional confidence filter.

        Args:
            pattern_type: Pattern type (conversation_flow, emotional_response, etc.)
            min_confidence: Minimum confidence score (0.0-1.0)
            limit: Maximum number of results

        Returns:
            List of LearningPattern entities matching criteria
        """
        ...

    @abstractmethod
    async def find_similar(
        self,
        embedding: List[float],
        top_k: int = 10,
        pattern_type: Optional[str] = None,
        min_confidence: float = 0.5
    ) -> List[tuple[Any, float]]:
        """
        Find similar patterns using vector similarity search.

        Args:
            embedding: Query embedding (768 dimensions)
            top_k: Number of results
            pattern_type: Optional pattern type filter
            min_confidence: Minimum confidence score

        Returns:
            List of (LearningPattern, similarity_score) tuples
        """
        ...

    @abstractmethod
    async def get_high_confidence(
        self,
        threshold: float = 0.8,
        pattern_type: Optional[str] = None,
        limit: int = 50
    ) -> List[Any]:
        """
        Get high-confidence patterns.

        Args:
            threshold: Minimum confidence threshold (0.0-1.0)
            pattern_type: Optional pattern type filter
            limit: Maximum number of results

        Returns:
            List of high-confidence LearningPattern entities
        """
        ...

    @abstractmethod
    async def get_frequently_observed(
        self,
        min_occurrences: int = 5,
        pattern_type: Optional[str] = None,
        limit: int = 50
    ) -> List[Any]:
        """
        Get frequently observed patterns.

        Args:
            min_occurrences: Minimum occurrence count
            pattern_type: Optional pattern type filter
            limit: Maximum number of results

        Returns:
            List of frequently observed LearningPattern entities
        """
        ...

    @abstractmethod
    async def get_recent_patterns(
        self,
        days: int = 30,
        pattern_type: Optional[str] = None,
        limit: int = 50
    ) -> List[Any]:
        """
        Get recently observed patterns.

        Args:
            days: Number of days to look back
            pattern_type: Optional pattern type filter
            limit: Maximum number of results

        Returns:
            List of recently observed LearningPattern entities
        """
        ...

    @abstractmethod
    async def search_by_description(
        self,
        query: str,
        limit: int = 20
    ) -> List[Any]:
        """
        Search patterns by description text.

        Args:
            query: Search query
            limit: Maximum number of results

        Returns:
            List of matching LearningPattern entities
        """
        ...

    @abstractmethod
    async def update_observation(
        self,
        pattern_id: UUID
    ) -> None:
        """
        Update pattern to record another observation.

        Increments occurrence_count, updates last_observed timestamp,
        and increases confidence score using diminishing returns algorithm.

        Args:
            pattern_id: Pattern UUID

        Raises:
            EntityNotFoundError: If pattern not found
        """
        ...

    @abstractmethod
    async def count_by_type(self, pattern_type: str) -> int:
        """
        Count patterns by type.

        Args:
            pattern_type: Pattern type

        Returns:
            Number of patterns of this type
        """
        ...

    @abstractmethod
    async def get_quality_distribution(self) -> Dict[str, int]:
        """
        Get distribution of patterns by quality level.

        Returns:
            Dictionary mapping quality level to count:
            {"excellent": 5, "good": 12, "acceptable": 8, "poor": 2}
        """
        ...
