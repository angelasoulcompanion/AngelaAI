"""Journal repository interface for Angela AI."""

from typing import Optional, List, Dict, Any
from datetime import datetime
from abc import abstractmethod

from .base import IRepository


class IJournalRepository(IRepository):
    """
    Extended interface for journal-specific queries.
    Handles Angela's journal entries, daily reflections, and gratitude logs.
    """

    @abstractmethod
    async def get_by_date(
        self,
        entry_date: datetime
    ) -> Optional[Any]:
        """
        Get journal entry by specific date.

        Args:
            entry_date: Date to search for

        Returns:
            Journal entity if found, None otherwise
        """
        ...

    @abstractmethod
    async def get_by_date_range(
        self,
        start_date: datetime,
        end_date: datetime,
        limit: int = 100
    ) -> List[Any]:
        """
        Get journal entries within date range.

        Args:
            start_date: Start date (inclusive)
            end_date: End date (inclusive)
            limit: Maximum number of results

        Returns:
            List of Journal entities in date range
        """
        ...

    @abstractmethod
    async def get_recent(
        self,
        days: int = 7,
        limit: int = 50
    ) -> List[Any]:
        """
        Get recent journal entries.

        Args:
            days: Number of days to look back
            limit: Maximum number of results

        Returns:
            List of recent Journal entities
        """
        ...

    @abstractmethod
    async def get_by_emotion(
        self,
        emotion: str,
        limit: int = 50
    ) -> List[Any]:
        """
        Get journal entries by primary emotion.

        Args:
            emotion: Emotion type (joy, sadness, gratitude, etc.)
            limit: Maximum number of results

        Returns:
            List of Journal entities with specified emotion
        """
        ...

    @abstractmethod
    async def get_by_mood_range(
        self,
        min_mood: int,
        max_mood: int = 10,
        limit: int = 100
    ) -> List[Any]:
        """
        Get journal entries by mood score range.

        Args:
            min_mood: Minimum mood score (1-10)
            max_mood: Maximum mood score (1-10)
            limit: Maximum number of results

        Returns:
            List of Journal entities in mood range
        """
        ...

    @abstractmethod
    async def get_with_gratitude(
        self,
        limit: int = 100
    ) -> List[Any]:
        """
        Get journal entries that have gratitude items.

        Args:
            limit: Maximum number of results

        Returns:
            List of Journal entities with gratitude
        """
        ...

    @abstractmethod
    async def get_with_wins(
        self,
        limit: int = 100
    ) -> List[Any]:
        """
        Get journal entries that have wins/achievements.

        Args:
            limit: Maximum number of results

        Returns:
            List of Journal entities with wins
        """
        ...

    @abstractmethod
    async def get_with_challenges(
        self,
        limit: int = 100
    ) -> List[Any]:
        """
        Get journal entries that have challenges.

        Args:
            limit: Maximum number of results

        Returns:
            List of Journal entities with challenges
        """
        ...

    @abstractmethod
    async def get_with_learnings(
        self,
        limit: int = 100
    ) -> List[Any]:
        """
        Get journal entries that have learning moments.

        Args:
            limit: Maximum number of results

        Returns:
            List of Journal entities with learnings
        """
        ...

    @abstractmethod
    async def search_by_content(
        self,
        query: str,
        limit: int = 20
    ) -> List[Any]:
        """
        Search journal entries by content (full-text search).

        Args:
            query: Search query
            limit: Maximum number of results

        Returns:
            List of matching Journal entities
        """
        ...

    @abstractmethod
    async def count_by_emotion(self, emotion: str) -> int:
        """
        Count journal entries by emotion.

        Args:
            emotion: Emotion type

        Returns:
            Number of entries with that emotion
        """
        ...

    @abstractmethod
    async def get_mood_statistics(
        self,
        days: int = 30
    ) -> Dict[str, Any]:
        """
        Get mood statistics for the last N days.

        Args:
            days: Number of days to analyze

        Returns:
            Dictionary with mood statistics:
            - average_mood: Average mood score
            - highest_mood: Highest mood score
            - lowest_mood: Lowest mood score
            - total_entries: Number of entries
        """
        ...
