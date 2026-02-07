"""Goal repository interface for Angela AI."""

from typing import Optional, List, Any
from abc import abstractmethod

from .base import IRepository


class IGoalRepository(IRepository):
    """
    Extended interface for goal-specific queries.
    Handles Angela's goals, progress tracking, and achievement.
    """

    @abstractmethod
    async def get_by_status(
        self,
        status: str,
        limit: int = 100
    ) -> List[Any]:
        """Get goals by status (active, in_progress, completed, etc.)."""
        ...

    @abstractmethod
    async def get_active_goals(
        self,
        for_whom: Optional[str] = None,
        limit: int = 100
    ) -> List[Any]:
        """Get active and in-progress goals."""
        ...

    @abstractmethod
    async def get_by_type(
        self,
        goal_type: str,
        limit: int = 100
    ) -> List[Any]:
        """Get goals by type (immediate, short_term, long_term, etc.)."""
        ...

    @abstractmethod
    async def get_by_priority(
        self,
        priority: str,
        limit: int = 100
    ) -> List[Any]:
        """Get goals by priority (critical, high, medium, low)."""
        ...

    @abstractmethod
    async def get_high_priority(
        self,
        status: Optional[str] = None,
        limit: int = 100
    ) -> List[Any]:
        """Get high priority goals (critical or high)."""
        ...

    @abstractmethod
    async def get_for_david(
        self,
        limit: int = 100
    ) -> List[Any]:
        """Get goals related to David."""
        ...

    @abstractmethod
    async def get_important(
        self,
        threshold: int = 7,
        limit: int = 100
    ) -> List[Any]:
        """Get important goals (importance_level >= threshold)."""
        ...

    @abstractmethod
    async def get_overdue_goals(
        self,
        limit: int = 100
    ) -> List[Any]:
        """Get overdue goals (deadline passed, not completed)."""
        ...

    @abstractmethod
    async def get_by_category(
        self,
        category: str,
        limit: int = 100
    ) -> List[Any]:
        """Get goals by category."""
        ...

    @abstractmethod
    async def get_by_progress_range(
        self,
        min_progress: float,
        max_progress: float,
        limit: int = 100
    ) -> List[Any]:
        """Get goals within progress range (0.0-100.0)."""
        ...

    @abstractmethod
    async def get_completed_goals(
        self,
        days: Optional[int] = None,
        limit: int = 100
    ) -> List[Any]:
        """Get completed goals, optionally filtered by completion date."""
        ...

    @abstractmethod
    async def get_by_priority_rank(
        self,
        max_rank: int = 10
    ) -> List[Any]:
        """Get goals by priority rank (1 = highest)."""
        ...

    @abstractmethod
    async def count_by_status(self, status: str) -> int:
        """Count goals by status."""
        ...

    @abstractmethod
    async def get_life_missions(self) -> List[Any]:
        """Get life mission goals."""
        ...
