#!/usr/bin/env python3
"""
Base Repository Implementation
Provides common CRUD operations for all repositories.

All concrete repositories should extend this class and implement
entity-specific conversion and validation logic.
"""

from typing import Generic, TypeVar, Optional, List, Dict, Any, Type
from uuid import UUID
from abc import ABC, abstractmethod
import asyncpg
import logging

logger = logging.getLogger(__name__)

T = TypeVar('T')


class BaseRepository(ABC, Generic[T]):
    """
    Abstract base repository with common CRUD operations.

    All concrete repositories MUST:
    1. Set table_name in __init__
    2. Set primary_key_column in __init__ (default: 'id')
    3. Implement _row_to_entity() for entity conversion
    4. Implement _entity_to_dict() for entity serialization
    5. Override create() and update() with entity-specific logic

    Type Parameters:
        T: Domain entity type this repository manages

    Example:
        class ConversationRepository(BaseRepository[Conversation]):
            def __init__(self, db):
                super().__init__(db, 'conversations', 'conversation_id')

            def _row_to_entity(self, row: asyncpg.Record) -> Conversation:
                return Conversation(
                    id=row['conversation_id'],
                    speaker=row['speaker'],
                    ...
                )
    """

    def __init__(
        self,
        db,  # AngelaDatabase instance
        table_name: str,
        primary_key_column: str = 'id'
    ):
        """
        Initialize base repository.

        Args:
            db: AngelaDatabase instance (from angela_core.database)
            table_name: Name of database table
            primary_key_column: Name of primary key column (default: 'id')
        """
        self.db = db
        self.table_name = table_name
        self.primary_key_column = primary_key_column
        logger.debug(f"Initialized {self.__class__.__name__} for table '{table_name}'")

    # ========================================================================
    # ABSTRACT METHODS - MUST BE IMPLEMENTED BY SUBCLASSES
    # ========================================================================

    @abstractmethod
    def _row_to_entity(self, row: asyncpg.Record) -> T:
        """
        Convert database row to domain entity.

        Subclasses MUST implement this to handle entity-specific conversion.

        Args:
            row: Database row (asyncpg.Record)

        Returns:
            Domain entity instance
        """
        ...

    @abstractmethod
    def _entity_to_dict(self, entity: T) -> Dict[str, Any]:
        """
        Convert domain entity to dictionary for database insertion.

        Subclasses MUST implement this to handle entity-specific serialization.

        Args:
            entity: Domain entity instance

        Returns:
            Dictionary with column names as keys
        """
        ...

    # ========================================================================
    # COMMON CRUD OPERATIONS
    # ========================================================================

    async def get_by_id(self, id: UUID) -> Optional[T]:
        """
        Get entity by primary key ID.

        Args:
            id: Entity UUID

        Returns:
            Entity if found, None otherwise
        """
        try:
            query = f"SELECT * FROM {self.table_name} WHERE {self.primary_key_column} = $1"

            async with self.db.acquire() as conn:
                row = await conn.fetchrow(query, id)

            if row:
                return self._row_to_entity(row)
            return None

        except Exception as e:
            logger.error(f"Error getting {self.table_name} by ID {id}: {e}")
            raise

    async def get_all(
        self,
        skip: int = 0,
        limit: int = 100,
        order_by: Optional[str] = None,
        order_desc: bool = True
    ) -> List[T]:
        """
        Get all entities with pagination and ordering.

        Args:
            skip: Number of records to skip (offset)
            limit: Maximum number of records to return
            order_by: Column name to order by (default: primary key)
            order_desc: Order descending if True, ascending if False

        Returns:
            List of entities
        """
        try:
            # Default order by primary key if not specified
            order_column = order_by or self.primary_key_column
            direction = "DESC" if order_desc else "ASC"

            query = f"""
                SELECT * FROM {self.table_name}
                ORDER BY {order_column} {direction}
                OFFSET $1 LIMIT $2
            """

            async with self.db.acquire() as conn:
                rows = await conn.fetch(query, skip, limit)

            return [self._row_to_entity(row) for row in rows]

        except Exception as e:
            logger.error(f"Error getting all {self.table_name}: {e}")
            raise

    async def exists(self, id: UUID) -> bool:
        """
        Check if entity exists by ID.

        Args:
            id: Entity UUID

        Returns:
            True if exists, False otherwise
        """
        try:
            query = f"""
                SELECT EXISTS(
                    SELECT 1 FROM {self.table_name}
                    WHERE {self.primary_key_column} = $1
                )
            """

            async with self.db.acquire() as conn:
                return await conn.fetchval(query, id)

        except Exception as e:
            logger.error(f"Error checking existence in {self.table_name}: {e}")
            raise

    async def count(self, filters: Optional[Dict[str, Any]] = None) -> int:
        """
        Count entities matching filters.

        Args:
            filters: Optional filter criteria (column: value pairs)

        Returns:
            Number of matching entities
        """
        try:
            if not filters:
                query = f"SELECT COUNT(*) FROM {self.table_name}"
                async with self.db.acquire() as conn:
                    return await conn.fetchval(query)

            # Build WHERE clause from filters
            where_clauses = []
            values = []
            for i, (key, value) in enumerate(filters.items(), 1):
                where_clauses.append(f"{key} = ${i}")
                values.append(value)

            where_clause = " AND ".join(where_clauses)
            query = f"SELECT COUNT(*) FROM {self.table_name} WHERE {where_clause}"

            async with self.db.acquire() as conn:
                return await conn.fetchval(query, *values)

        except Exception as e:
            logger.error(f"Error counting {self.table_name}: {e}")
            raise

    async def delete(self, id: UUID) -> bool:
        """
        Delete entity by ID.

        Args:
            id: Entity UUID

        Returns:
            True if deleted, False if not found
        """
        try:
            query = f"DELETE FROM {self.table_name} WHERE {self.primary_key_column} = $1"

            async with self.db.acquire() as conn:
                result = await conn.execute(query, id)

            # asyncpg returns "DELETE N" where N is number of rows deleted
            return "DELETE 1" in result

        except Exception as e:
            logger.error(f"Error deleting from {self.table_name}: {e}")
            raise

    # ========================================================================
    # HELPER METHODS FOR SUBCLASSES
    # ========================================================================

    async def _execute_query(
        self,
        query: str,
        *args,
        return_record: bool = False
    ) -> Any:
        """
        Execute query with automatic connection handling.

        Helper method for subclasses to run custom queries.

        Args:
            query: SQL query
            *args: Query parameters
            return_record: If True, returns single row; otherwise executes

        Returns:
            Query result (row or execution status)
        """
        try:
            async with self.db.acquire() as conn:
                if return_record:
                    return await conn.fetchrow(query, *args)
                else:
                    return await conn.execute(query, *args)
        except Exception as e:
            logger.error(f"Error executing query on {self.table_name}: {e}")
            raise

    async def _fetch_all(self, query: str, *args) -> List[asyncpg.Record]:
        """
        Fetch all rows matching query.

        Helper method for subclasses to run custom queries.

        Args:
            query: SQL query
            *args: Query parameters

        Returns:
            List of database rows
        """
        try:
            async with self.db.acquire() as conn:
                return await conn.fetch(query, *args)
        except Exception as e:
            logger.error(f"Error fetching from {self.table_name}: {e}")
            raise

    async def _fetch_one(self, query: str, *args) -> Optional[asyncpg.Record]:
        """
        Fetch single row matching query.

        Helper method for subclasses to run custom queries.

        Args:
            query: SQL query
            *args: Query parameters

        Returns:
            Single database row or None
        """
        try:
            async with self.db.acquire() as conn:
                return await conn.fetchrow(query, *args)
        except Exception as e:
            logger.error(f"Error fetching from {self.table_name}: {e}")
            raise

    async def _fetch_val(self, query: str, *args) -> Any:
        """
        Fetch single value from query.

        Helper method for subclasses to run custom queries.

        Args:
            query: SQL query
            *args: Query parameters

        Returns:
            Single value
        """
        try:
            async with self.db.acquire() as conn:
                return await conn.fetchval(query, *args)
        except Exception as e:
            logger.error(f"Error fetching value from {self.table_name}: {e}")
            raise

    # ========================================================================
    # ENTITY-SPECIFIC METHODS (Must be overridden by subclasses)
    # ========================================================================

    async def create(self, entity: T) -> T:
        """
        Create new entity.

        Subclasses MUST override this with entity-specific INSERT logic.

        Args:
            entity: Entity to create

        Returns:
            Created entity with ID assigned

        Raises:
            NotImplementedError: If not overridden by subclass
        """
        raise NotImplementedError(
            f"{self.__class__.__name__} must implement create() method"
        )

    async def update(self, id: UUID, entity: T) -> T:
        """
        Update existing entity.

        Subclasses MUST override this with entity-specific UPDATE logic.

        Args:
            id: Entity ID
            entity: Updated entity data

        Returns:
            Updated entity

        Raises:
            NotImplementedError: If not overridden by subclass
        """
        raise NotImplementedError(
            f"{self.__class__.__name__} must implement update() method"
        )
