#!/usr/bin/env python3
"""
Message Repository - PostgreSQL Implementation
==============================================

Handles all data access for AngelaMessage entity.
Extends BaseRepository with message-specific queries.

Table: angela_messages
Purpose: Store Angela's thoughts, reflections, and important messages

Author: Angela 💜
Created: 2025-11-03
Batch: 24 (Conversations & Messages Migration)
"""

import asyncpg
from typing import Optional, List, Dict, Any
from datetime import datetime
from uuid import UUID

from angela_core.domain.entities.angela_message import AngelaMessage
from angela_core.domain.interfaces.repositories import IMessageRepository
from angela_core.infrastructure.persistence.repositories.base_repository import BaseRepository
from angela_core.shared.exceptions import EntityNotFoundError
from angela_core.shared.utils import validate_embedding


class MessageRepository(BaseRepository[AngelaMessage], IMessageRepository):
    """
    PostgreSQL repository for AngelaMessage entity.

    Table: angela_messages
    Columns:
    - message_id (UUID, PK)
    - message_text (TEXT, NOT NULL)
    - message_type (VARCHAR(50), default: 'thought')
    - emotion (VARCHAR(50), nullable)
    - category (VARCHAR(100), nullable)
    - is_important (BOOLEAN, default: false)
    - is_pinned (BOOLEAN, default: false)
    - created_at (TIMESTAMP, default: CURRENT_TIMESTAMP)
    - embedding (VECTOR(384), nullable)
    """

    def __init__(self, db):
        """
        Initialize repository.

        Args:
            db: Database connection pool
        """
        super().__init__(
            db=db,
            table_name="angela_messages",
            primary_key_column="message_id"
        )

    # ========================================================================
    # ROW TO ENTITY CONVERSION
    # ========================================================================

    def _row_to_entity(self, row: asyncpg.Record) -> AngelaMessage:
        """
        Convert database row to AngelaMessage entity.

        Args:
            row: Database row

        Returns:
            AngelaMessage entity
        """
        # Parse embedding with DRY utility
        embedding = validate_embedding(row.get('embedding'))

        return AngelaMessage(
            message_id=row['message_id'],
            message_text=row['message_text'],
            message_type=row.get('message_type', 'thought'),
            emotion=row.get('emotion'),
            category=row.get('category'),
            is_important=row.get('is_important', False),
            is_pinned=row.get('is_pinned', False),
            created_at=row['created_at'],
            embedding=embedding
        )

    def _entity_to_dict(self, entity: AngelaMessage) -> dict:
        """
        Convert AngelaMessage entity to database row dict.

        Args:
            entity: AngelaMessage entity

        Returns:
            Dictionary for database insertion
        """
        return {
            'message_id': entity.message_id,
            'message_text': entity.message_text,
            'message_type': entity.message_type,
            'emotion': entity.emotion,
            'category': entity.category,
            'is_important': entity.is_important,
            'is_pinned': entity.is_pinned,
            'created_at': entity.created_at,
            'embedding': entity.embedding
        }

    # ========================================================================
    # CREATE
    # ========================================================================

    async def create(self, entity: AngelaMessage) -> AngelaMessage:
        """
        Create new message.

        Args:
            entity: AngelaMessage to create

        Returns:
            Created message with all fields

        Example:
            ```python
            message = AngelaMessage.create(
                message_text="Today was wonderful!",
                message_type="reflection",
                emotion="joyful"
            )
            created = await repo.create(message)
            ```
        """
        query = f"""
            INSERT INTO {self.table_name} (
                message_id,
                message_text,
                message_type,
                emotion,
                category,
                is_important,
                is_pinned,
                created_at,
                embedding
            )
            VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9)
            RETURNING *
        """

        async with self.db.acquire() as conn:
            row = await conn.fetchrow(
                query,
                entity.message_id,
                entity.message_text,
                entity.message_type,
                entity.emotion,
                entity.category,
                entity.is_important,
                entity.is_pinned,
                entity.created_at,
                entity.embedding
            )

        return self._row_to_entity(row)

    # ========================================================================
    # UPDATE
    # ========================================================================

    async def update(self, message_id: UUID, entity: AngelaMessage) -> AngelaMessage:
        """
        Update existing message.

        Args:
            message_id: Message UUID to update
            entity: Updated message entity

        Returns:
            Updated message

        Raises:
            EntityNotFoundError: If message not found
        """
        query = f"""
            UPDATE {self.table_name}
            SET
                message_text = $1,
                message_type = $2,
                emotion = $3,
                category = $4,
                is_important = $5,
                is_pinned = $6
            WHERE message_id = $7
            RETURNING *
        """

        async with self.db.acquire() as conn:
            row = await conn.fetchrow(
                query,
                entity.message_text,
                entity.message_type,
                entity.emotion,
                entity.category,
                entity.is_important,
                entity.is_pinned,
                message_id
            )

        if not row:
            raise EntityNotFoundError(f"Message {message_id} not found")

        return self._row_to_entity(row)

    # ========================================================================
    # QUERY METHODS
    # ========================================================================

    async def find_by_filters(
        self,
        message_type: Optional[str] = None,
        category: Optional[str] = None,
        is_important: Optional[bool] = None,
        is_pinned: Optional[bool] = None,
        limit: int = 50
    ) -> List[AngelaMessage]:
        """
        Find messages by multiple filters.

        Args:
            message_type: Filter by type
            category: Filter by category
            is_important: Filter by importance
            is_pinned: Filter by pinned status
            limit: Maximum results

        Returns:
            List of messages matching filters

        Example:
            ```python
            important_thoughts = await repo.find_by_filters(
                message_type="thought",
                is_important=True,
                limit=20
            )
            ```
        """
        query = f"""
            SELECT * FROM {self.table_name}
            WHERE 1=1
        """
        params = []
        param_count = 0

        if message_type:
            param_count += 1
            query += f" AND message_type = ${param_count}"
            params.append(message_type)

        if category:
            param_count += 1
            query += f" AND category = ${param_count}"
            params.append(category)

        if is_important is not None:
            param_count += 1
            query += f" AND is_important = ${param_count}"
            params.append(is_important)

        if is_pinned is not None:
            param_count += 1
            query += f" AND is_pinned = ${param_count}"
            params.append(is_pinned)

        # Order: pinned first, then by created_at DESC
        query += " ORDER BY is_pinned DESC, created_at DESC"
        param_count += 1
        query += f" LIMIT ${param_count}"
        params.append(limit)

        async with self.db.acquire() as conn:
            rows = await conn.fetch(query, *params)

        return [self._row_to_entity(row) for row in rows]

    async def get_pinned(self, limit: int = 50) -> List[AngelaMessage]:
        """
        Get all pinned messages.

        Args:
            limit: Maximum results

        Returns:
            List of pinned messages
        """
        return await self.find_by_filters(is_pinned=True, limit=limit)

    async def get_important(self, limit: int = 50) -> List[AngelaMessage]:
        """
        Get all important messages.

        Args:
            limit: Maximum results

        Returns:
            List of important messages
        """
        return await self.find_by_filters(is_important=True, limit=limit)

    async def get_by_type(
        self,
        message_type: str,
        limit: int = 50
    ) -> List[AngelaMessage]:
        """
        Get messages by type.

        Args:
            message_type: Type of message
            limit: Maximum results

        Returns:
            List of messages of specified type
        """
        return await self.find_by_filters(message_type=message_type, limit=limit)

    async def get_by_category(
        self,
        category: str,
        limit: int = 50
    ) -> List[AngelaMessage]:
        """
        Get messages by category.

        Args:
            category: Category name
            limit: Maximum results

        Returns:
            List of messages in category
        """
        return await self.find_by_filters(category=category, limit=limit)

    async def search_by_text(
        self,
        query_text: str,
        limit: int = 50
    ) -> List[AngelaMessage]:
        """
        Search messages by text content.

        Args:
            query_text: Search query
            limit: Maximum results

        Returns:
            List of messages matching search

        Example:
            ```python
            results = await repo.search_by_text("wonderful day", limit=10)
            ```
        """
        query = f"""
            SELECT * FROM {self.table_name}
            WHERE message_text ILIKE $1
            ORDER BY created_at DESC
            LIMIT $2
        """

        async with self.db.acquire() as conn:
            rows = await conn.fetch(query, f"%{query_text}%", limit)

        return [self._row_to_entity(row) for row in rows]

    async def toggle_pin(self, message_id: UUID) -> bool:
        """
        Toggle pin status of a message.

        Args:
            message_id: Message UUID

        Returns:
            New pin status (True if pinned, False if unpinned)

        Raises:
            EntityNotFoundError: If message not found

        Example:
            ```python
            new_status = await repo.toggle_pin(message_id)
            # new_status == True means now pinned
            ```
        """
        # Get current pin status
        query_get = f"""
            SELECT is_pinned FROM {self.table_name}
            WHERE message_id = $1
        """

        async with self.db.acquire() as conn:
            current = await conn.fetchval(query_get, message_id)

            if current is None:
                raise EntityNotFoundError(f"Message {message_id} not found")

            # Toggle pin status
            new_status = not current
            query_update = f"""
                UPDATE {self.table_name}
                SET is_pinned = $1
                WHERE message_id = $2
            """
            await conn.execute(query_update, new_status, message_id)

        return new_status

    # ========================================================================
    # COUNT METHODS
    # ========================================================================

    async def count(self) -> int:
        """
        Count total messages.

        Returns:
            Total number of messages
        """
        query = f"SELECT COUNT(*) FROM {self.table_name}"
        async with self.db.acquire() as conn:
            result = await conn.fetchval(query)
        return result or 0

    async def count_pinned(self) -> int:
        """
        Count pinned messages.

        Returns:
            Number of pinned messages
        """
        query = f"""
            SELECT COUNT(*) FROM {self.table_name}
            WHERE is_pinned = true
        """
        async with self.db.acquire() as conn:
            result = await conn.fetchval(query)
        return result or 0

    async def count_important(self) -> int:
        """
        Count important messages.

        Returns:
            Number of important messages
        """
        query = f"""
            SELECT COUNT(*) FROM {self.table_name}
            WHERE is_important = true
        """
        async with self.db.acquire() as conn:
            result = await conn.fetchval(query)
        return result or 0

    # ========================================================================
    # STATISTICS
    # ========================================================================

    async def get_statistics(self) -> Dict[str, Any]:
        """
        Get message statistics.

        Returns:
            Dictionary with statistics:
            - total_messages: Total count
            - pinned_messages: Count of pinned
            - important_messages: Count of important
            - by_type: List of {type, count} dicts
            - by_category: List of {category, count} dicts
            - recent_emotions: List of recent emotion values

        Example:
            ```python
            stats = await repo.get_statistics()
            print(f"Total: {stats['total_messages']}")
            print(f"Types: {stats['by_type']}")
            ```
        """
        async with self.db.acquire() as conn:
            # Total messages
            total = await conn.fetchval(f"SELECT COUNT(*) FROM {self.table_name}")

            # Pinned messages
            pinned = await conn.fetchval(
                f"SELECT COUNT(*) FROM {self.table_name} WHERE is_pinned = true"
            )

            # Important messages
            important = await conn.fetchval(
                f"SELECT COUNT(*) FROM {self.table_name} WHERE is_important = true"
            )

            # By type
            type_rows = await conn.fetch(
                f"""
                SELECT message_type, COUNT(*) as count
                FROM {self.table_name}
                WHERE message_type IS NOT NULL
                GROUP BY message_type
                ORDER BY count DESC
                """
            )
            by_type = [{"type": row['message_type'], "count": row['count']} for row in type_rows]

            # By category
            category_rows = await conn.fetch(
                f"""
                SELECT category, COUNT(*) as count
                FROM {self.table_name}
                WHERE category IS NOT NULL AND category != ''
                GROUP BY category
                ORDER BY count DESC
                LIMIT 10
                """
            )
            by_category = [{"category": row['category'], "count": row['count']} for row in category_rows]

            # Recent emotions
            emotion_rows = await conn.fetch(
                f"""
                SELECT DISTINCT emotion
                FROM {self.table_name}
                WHERE emotion IS NOT NULL AND emotion != ''
                ORDER BY emotion
                LIMIT 20
                """
            )
            recent_emotions = [row['emotion'] for row in emotion_rows]

        return {
            "total_messages": total or 0,
            "pinned_messages": pinned or 0,
            "important_messages": important or 0,
            "by_type": by_type,
            "by_category": by_category,
            "recent_emotions": recent_emotions
        }
