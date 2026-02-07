"""Base repository interface for Angela AI."""

from typing import Protocol, TypeVar, Generic, Optional, List, Dict, Any
from uuid import UUID
from abc import abstractmethod

T = TypeVar('T')


class IRepository(Protocol, Generic[T]):
    """
    Base repository interface for CRUD operations.
    All repositories MUST implement these methods.

    Type Parameters:
        T: Domain entity type

    Usage:
        class MyRepository(IRepository[MyEntity]):
            async def get_by_id(self, id: UUID) -> Optional[MyEntity]:
                # Implementation
    """

    @abstractmethod
    async def get_by_id(self, id: UUID) -> Optional[T]:
        """
        Get entity by ID.

        Args:
            id: Entity UUID

        Returns:
            Entity if found, None otherwise
        """
        ...

    @abstractmethod
    async def get_all(
        self,
        skip: int = 0,
        limit: int = 100,
        order_by: Optional[str] = None,
        order_desc: bool = True
    ) -> List[T]:
        """
        Get all entities with pagination.

        Args:
            skip: Number of records to skip
            limit: Maximum number of records to return
            order_by: Column name to order by
            order_desc: Order descending if True, ascending if False

        Returns:
            List of entities
        """
        ...

    @abstractmethod
    async def create(self, entity: T) -> T:
        """
        Create new entity.

        Args:
            entity: Entity to create

        Returns:
            Created entity with ID assigned
        """
        ...

    @abstractmethod
    async def update(self, id: UUID, entity: T) -> T:
        """
        Update existing entity.

        Args:
            id: Entity ID
            entity: Updated entity data

        Returns:
            Updated entity

        Raises:
            EntityNotFoundError: If entity doesn't exist
        """
        ...

    @abstractmethod
    async def delete(self, id: UUID) -> bool:
        """
        Delete entity by ID.

        Args:
            id: Entity ID

        Returns:
            True if deleted, False if not found
        """
        ...

    @abstractmethod
    async def exists(self, id: UUID) -> bool:
        """
        Check if entity exists by ID.

        Args:
            id: Entity ID

        Returns:
            True if exists, False otherwise
        """
        ...

    @abstractmethod
    async def count(self, filters: Optional[Dict[str, Any]] = None) -> int:
        """
        Count entities matching filters.

        Args:
            filters: Optional filter criteria

        Returns:
            Number of matching entities
        """
        ...
