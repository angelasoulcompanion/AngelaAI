"""Pattern repository interface for Angela AI."""

from typing import List, Dict, Any
from abc import abstractmethod

from .base import IRepository


class IPatternRepository(IRepository):
    """
    Extended interface for pattern-specific queries.
    Handles Angela's learned behavioral patterns for situation recognition
    and response generation.
    """

    # ========================================================================
    # PATTERN RETRIEVAL METHODS
    # ========================================================================

    @abstractmethod
    async def get_by_situation_type(
        self,
        situation_type: str,
        limit: int = 20
    ) -> List[Any]:
        """
        Get patterns by situation type.

        Args:
            situation_type: Type of situation (e.g., "greeting", "question")
            limit: Maximum number of results

        Returns:
            List of Pattern entities matching the situation type
        """
        ...

    @abstractmethod
    async def get_by_emotion_category(
        self,
        emotion_category: str,
        limit: int = 20
    ) -> List[Any]:
        """
        Get patterns by emotion category.

        Args:
            emotion_category: Emotion category (e.g., "happy", "sad")
            limit: Maximum number of results

        Returns:
            List of Pattern entities for this emotion
        """
        ...

    @abstractmethod
    async def get_by_response_type(
        self,
        response_type: str,
        limit: int = 20
    ) -> List[Any]:
        """
        Get patterns by response type.

        Args:
            response_type: Type of response (e.g., "emotional_support")
            limit: Maximum number of results

        Returns:
            List of Pattern entities of this response type
        """
        ...

    @abstractmethod
    async def search_by_keywords(
        self,
        keywords: List[str],
        limit: int = 20
    ) -> List[Any]:
        """
        Search patterns by context keywords.

        Args:
            keywords: List of keywords to match
            limit: Maximum number of results

        Returns:
            List of Pattern entities matching any of the keywords
        """
        ...

    @abstractmethod
    async def search_by_embedding(
        self,
        embedding: List[float],
        limit: int = 10,
        similarity_threshold: float = 0.7
    ) -> List[Any]:
        """
        Search patterns by situation embedding (semantic similarity).

        Args:
            embedding: Query embedding vector
            limit: Maximum number of results
            similarity_threshold: Minimum cosine similarity (0.0-1.0)

        Returns:
            List of similar Pattern entities
        """
        ...

    # ========================================================================
    # PATTERN EFFECTIVENESS QUERIES
    # ========================================================================

    @abstractmethod
    async def get_effective_patterns(
        self,
        min_success_rate: float = 0.7,
        min_usage_count: int = 5,
        limit: int = 50
    ) -> List[Any]:
        """
        Get patterns that are effective (high success rate).

        Args:
            min_success_rate: Minimum success rate (0.0-1.0)
            min_usage_count: Minimum usage count for statistical significance
            limit: Maximum number of results

        Returns:
            List of effective Pattern entities
        """
        ...

    @abstractmethod
    async def get_popular_patterns(
        self,
        min_usage_count: int = 10,
        limit: int = 50
    ) -> List[Any]:
        """
        Get frequently used patterns.

        Args:
            min_usage_count: Minimum usage count
            limit: Maximum number of results

        Returns:
            List of popular Pattern entities, ordered by usage
        """
        ...

    @abstractmethod
    async def get_recent_patterns(
        self,
        days: int = 30,
        limit: int = 50
    ) -> List[Any]:
        """
        Get recently used patterns.

        Args:
            days: Number of days to look back
            limit: Maximum number of results

        Returns:
            List of Pattern entities used in last N days
        """
        ...

    @abstractmethod
    async def get_high_satisfaction_patterns(
        self,
        min_satisfaction: float = 0.8,
        min_usage_count: int = 5,
        limit: int = 50
    ) -> List[Any]:
        """
        Get patterns with high user satisfaction.

        Args:
            min_satisfaction: Minimum average satisfaction (0.0-1.0)
            min_usage_count: Minimum usage for statistical significance
            limit: Maximum number of results

        Returns:
            List of Pattern entities with high satisfaction
        """
        ...

    # ========================================================================
    # UTILITY METHODS
    # ========================================================================

    @abstractmethod
    async def count_by_situation_type(self, situation_type: str) -> int:
        """
        Count patterns by situation type.

        Args:
            situation_type: Type of situation

        Returns:
            Number of patterns for this situation type
        """
        ...

    @abstractmethod
    async def count_effective_patterns(
        self,
        min_success_rate: float = 0.7,
        min_usage_count: int = 5
    ) -> int:
        """
        Count effective patterns.

        Args:
            min_success_rate: Minimum success rate
            min_usage_count: Minimum usage count

        Returns:
            Number of effective patterns
        """
        ...

    @abstractmethod
    async def get_pattern_statistics(self) -> Dict[str, Any]:
        """
        Get overall pattern statistics.

        Returns:
            Dictionary with:
            - total_patterns: Total number of patterns
            - avg_success_rate: Average success rate
            - avg_usage_count: Average usage count
            - avg_satisfaction: Average satisfaction score
            - total_usages: Total pattern usages across all patterns
        """
        ...
