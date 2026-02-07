"""Knowledge repository interface for Angela AI."""

from typing import Optional, List, Any
from uuid import UUID
from abc import abstractmethod

from .base import IRepository


class IKnowledgeRepository(IRepository):
    """
    Extended interface for knowledge graph queries.
    Handles knowledge items and relationships.
    """

    @abstractmethod
    async def search_by_vector(
        self,
        embedding: List[float],
        top_k: int = 5,
        category: Optional[str] = None
    ) -> List[tuple[Any, float]]:
        """Vector similarity search for knowledge."""
        ...

    @abstractmethod
    async def get_by_concept_name(
        self,
        concept_name: str
    ) -> Optional[Any]:
        """Get knowledge node by concept name."""
        ...

    @abstractmethod
    async def get_by_category(
        self,
        category: str,
        limit: int = 100
    ) -> List[Any]:
        """Get knowledge by category."""
        ...

    @abstractmethod
    async def get_well_understood(
        self,
        threshold: float = 0.7,
        limit: int = 100
    ) -> List[Any]:
        """Get well-understood concepts (understanding_level >= threshold)."""
        ...

    @abstractmethod
    async def get_expert_level(
        self,
        limit: int = 100
    ) -> List[Any]:
        """Get expert-level concepts (understanding_level >= 0.9)."""
        ...

    @abstractmethod
    async def get_about_david(
        self,
        limit: int = 100
    ) -> List[Any]:
        """Get knowledge about David."""
        ...

    @abstractmethod
    async def get_frequently_used(
        self,
        threshold: int = 10,
        limit: int = 100
    ) -> List[Any]:
        """Get frequently referenced concepts (times_referenced >= threshold)."""
        ...

    @abstractmethod
    async def get_recently_used(
        self,
        days: int = 7,
        limit: int = 100
    ) -> List[Any]:
        """Get recently used concepts (last_used_at within last N days)."""
        ...

    @abstractmethod
    async def search_by_concept(
        self,
        query: str,
        limit: int = 100
    ) -> List[Any]:
        """Search knowledge by concept name."""
        ...

    @abstractmethod
    async def count_by_category(self, category: str) -> int:
        """Count knowledge nodes by category."""
        ...

    @abstractmethod
    async def get_related_knowledge(
        self,
        knowledge_id: UUID,
        max_depth: int = 2
    ) -> List[Any]:
        """Get related knowledge via graph traversal."""
        ...
