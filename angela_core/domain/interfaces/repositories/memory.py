"""Memory repository interface for Angela AI."""

from typing import Optional, List, Any
from abc import abstractmethod

from .base import IRepository


class IMemoryRepository(IRepository):
    """
    Extended interface for memory-specific queries.
    Handles long-term memory storage and retrieval.
    """

    @abstractmethod
    async def search_by_vector(
        self,
        embedding: List[float],
        top_k: int = 5,
        memory_type: Optional[str] = None
    ) -> List[tuple[Any, float]]:
        """Vector similarity search for memories."""
        ...

    @abstractmethod
    async def get_by_phase(
        self,
        phase: str,
        limit: int = 100
    ) -> List[Any]:
        """Get memories by phase (episodic, compressed_1, compressed_2, semantic, pattern, intuitive, forgotten)."""
        ...

    @abstractmethod
    async def get_by_type(
        self,
        memory_type: str,
        limit: int = 50
    ) -> List[Any]:
        """Get memories by type (e.g., 'episodic', 'semantic')."""
        ...

    @abstractmethod
    async def get_recent(
        self,
        days: int = 7,
        limit: int = 100
    ) -> List[Any]:
        """Get recent memories (last N days)."""
        ...

    @abstractmethod
    async def get_important(
        self,
        threshold: float = 0.7,
        limit: int = 100
    ) -> List[Any]:
        """Get important memories (importance >= threshold)."""
        ...

    @abstractmethod
    async def get_strong(
        self,
        threshold: float = 0.5,
        limit: int = 100
    ) -> List[Any]:
        """Get strong memories (strength >= threshold)."""
        ...

    @abstractmethod
    async def get_forgotten(
        self,
        limit: int = 100
    ) -> List[Any]:
        """Get forgotten memories (strength < 0.1 or phase=forgotten)."""
        ...

    @abstractmethod
    async def get_episodic(
        self,
        limit: int = 100
    ) -> List[Any]:
        """Get episodic (fresh) memories."""
        ...

    @abstractmethod
    async def get_semantic(
        self,
        limit: int = 100
    ) -> List[Any]:
        """Get semantic (factual) memories."""
        ...

    @abstractmethod
    async def get_ready_for_consolidation(
        self,
        limit: int = 100
    ) -> List[Any]:
        """Get memories ready for consolidation to next phase."""
        ...

    @abstractmethod
    async def search_by_content(
        self,
        query: str,
        limit: int = 100
    ) -> List[Any]:
        """Search memories by content text."""
        ...

    @abstractmethod
    async def count_by_phase(self, phase: str) -> int:
        """Count memories by phase."""
        ...

    @abstractmethod
    async def get_by_importance(
        self,
        min_importance: float,
        max_importance: float = 1.0,
        limit: int = 50
    ) -> List[Any]:
        """Get memories by importance range."""
        ...
