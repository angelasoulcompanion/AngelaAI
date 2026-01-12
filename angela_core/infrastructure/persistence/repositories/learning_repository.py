#!/usr/bin/env python3
"""
Learning Repository - PostgreSQL Implementation

Handles all data access for Learning entity.
Extends BaseRepository with learning-specific queries.
"""

import asyncpg
from typing import Optional, List
from datetime import datetime, timedelta
from uuid import UUID

from angela_core.domain import Learning, LearningCategory
from angela_core.domain.interfaces.repositories import ILearningRepository
from angela_core.infrastructure.persistence.repositories.base_repository import BaseRepository
from angela_core.shared.exceptions import EntityNotFoundError
from angela_core.shared.utils import parse_enum_optional, validate_embedding


class LearningRepository(BaseRepository[Learning], ILearningRepository):
    """
    PostgreSQL repository for Learning entity.

    Table: learnings
    Columns:
    - learning_id (UUID, PK)
    - topic (VARCHAR 200)
    - category (VARCHAR 50, nullable)
    - insight (TEXT)
    - learned_from (UUID, nullable, FK to conversations)
    - evidence (TEXT, nullable)
    - confidence_level (DOUBLE PRECISION, 0.0-1.0)
    - times_reinforced (INTEGER, default 1)
    - has_applied (BOOLEAN, default false)
    - application_note (TEXT, nullable)
    - created_at (TIMESTAMP)
    - last_reinforced_at (TIMESTAMP, nullable)
    - embedding (VECTOR 768, nullable)
    - learning_json (JSONB, nullable)
    - # content_json (JSONB, nullable)  # REMOVED: Migration 010
    """

    def __init__(self, db):
        """
        Initialize repository.

        Args:
            db: Database connection pool
        """
        super().__init__(
            db=db,
            table_name="learnings",
            primary_key_column="learning_id"
        )

    # ========================================================================
    # ROW TO ENTITY CONVERSION
    # ========================================================================

    def _row_to_entity(self, row: asyncpg.Record) -> Learning:
        """
        Convert database row to Learning entity.

        Args:
            row: Database row

        Returns:
            Learning entity
        """
        # Parse category enum with DRY utility
        category = parse_enum_optional(row.get('category'), LearningCategory)

        # Parse embedding with DRY utility (handles string/list/None)
        embedding = validate_embedding(row.get('embedding'))

        # Create entity
        return Learning(
            id=row['learning_id'],
            topic=row['topic'],
            insight=row['insight'],
            category=category,
            learned_from=row.get('learned_from'),
            evidence=row.get('evidence'),
            confidence_level=row.get('confidence_level', 0.7),
            times_reinforced=row.get('times_reinforced', 1),
            has_applied=row.get('has_applied', False),
            application_note=row.get('application_note'),
            created_at=row['created_at'],
            last_reinforced_at=row.get('last_reinforced_at'),
            embedding=embedding,
            learning_json=row.get('learning_json', {}),
            content_json=row.get('# content_json', {})  # REMOVED: Migration 010
        )

    def _entity_to_dict(self, entity: Learning) -> dict:
        """
        Convert Learning entity to database row dict.

        Args:
            entity: Learning entity

        Returns:
            Dictionary of column values
        """
        return {
            'learning_id': entity.id,
            'topic': entity.topic,
            'category': entity.category.value if entity.category else None,
            'insight': entity.insight,
            'learned_from': entity.learned_from,
            'evidence': entity.evidence,
            'confidence_level': entity.confidence_level,
            'times_reinforced': entity.times_reinforced,
            'has_applied': entity.has_applied,
            'application_note': entity.application_note,
            'created_at': entity.created_at,
            'last_reinforced_at': entity.last_reinforced_at,
            'embedding': entity.embedding,  # asyncpg handles vector conversion
            'learning_json': entity.learning_json
            # 'content_json': entity.content_json  # REMOVED: Migration 010
        }

    # ========================================================================
    # QUERY METHODS
    # ========================================================================

    async def get_by_category(
        self,
        category: str,
        limit: int = 100
    ) -> List[Learning]:
        """
        Get learnings by category.

        Args:
            category: Learning category
            limit: Maximum number of results

        Returns:
            List of Learning entities
        """
        query = f"""
            SELECT * FROM {self.table_name}
            WHERE category = $1
            ORDER BY confidence_level DESC, created_at DESC
            LIMIT $2
        """

        async with self.db.acquire() as conn:
            rows = await conn.fetch(query, category, limit)

        return [self._row_to_entity(row) for row in rows]

    async def get_by_confidence(
        self,
        min_confidence: float,
        limit: int = 100
    ) -> List[Learning]:
        """
        Get learnings with confidence >= min_confidence.

        Args:
            min_confidence: Minimum confidence level (0.0-1.0)
            limit: Maximum number of results

        Returns:
            List of Learning entities ordered by confidence desc
        """
        query = f"""
            SELECT * FROM {self.table_name}
            WHERE confidence_level >= $1
            ORDER BY confidence_level DESC, created_at DESC
            LIMIT $2
        """

        async with self.db.acquire() as conn:
            rows = await conn.fetch(query, min_confidence, limit)

        return [self._row_to_entity(row) for row in rows]

    async def get_confident_learnings(
        self,
        category: Optional[str] = None,
        limit: int = 100
    ) -> List[Learning]:
        """
        Get high-confidence learnings (confidence >= 0.7).

        Args:
            category: Optional category filter
            limit: Maximum number of results

        Returns:
            List of confident Learning entities
        """
        if category:
            query = f"""
                SELECT * FROM {self.table_name}
                WHERE confidence_level >= 0.7
                  AND category = $1
                ORDER BY confidence_level DESC, created_at DESC
                LIMIT $2
            """
            async with self.db.acquire() as conn:
                rows = await conn.fetch(query, category, limit)
        else:
            query = f"""
                SELECT * FROM {self.table_name}
                WHERE confidence_level >= 0.7
                ORDER BY confidence_level DESC, created_at DESC
                LIMIT $1
            """
            async with self.db.acquire() as conn:
                rows = await conn.fetch(query, limit)

        return [self._row_to_entity(row) for row in rows]

    async def get_uncertain_learnings(
        self,
        category: Optional[str] = None,
        limit: int = 100
    ) -> List[Learning]:
        """
        Get uncertain learnings (confidence < 0.5).

        Args:
            category: Optional category filter
            limit: Maximum number of results

        Returns:
            List of uncertain Learning entities
        """
        if category:
            query = f"""
                SELECT * FROM {self.table_name}
                WHERE confidence_level < 0.5
                  AND category = $1
                ORDER BY confidence_level ASC, created_at DESC
                LIMIT $2
            """
            async with self.db.acquire() as conn:
                rows = await conn.fetch(query, category, limit)
        else:
            query = f"""
                SELECT * FROM {self.table_name}
                WHERE confidence_level < 0.5
                ORDER BY confidence_level ASC, created_at DESC
                LIMIT $1
            """
            async with self.db.acquire() as conn:
                rows = await conn.fetch(query, limit)

        return [self._row_to_entity(row) for row in rows]

    async def get_applied_learnings(
        self,
        category: Optional[str] = None,
        limit: int = 100
    ) -> List[Learning]:
        """
        Get learnings that have been applied in practice.

        Args:
            category: Optional category filter
            limit: Maximum number of results

        Returns:
            List of applied Learning entities
        """
        if category:
            query = f"""
                SELECT * FROM {self.table_name}
                WHERE has_applied = true
                  AND category = $1
                ORDER BY confidence_level DESC, created_at DESC
                LIMIT $2
            """
            async with self.db.acquire() as conn:
                rows = await conn.fetch(query, category, limit)
        else:
            query = f"""
                SELECT * FROM {self.table_name}
                WHERE has_applied = true
                ORDER BY confidence_level DESC, created_at DESC
                LIMIT $1
            """
            async with self.db.acquire() as conn:
                rows = await conn.fetch(query, limit)

        return [self._row_to_entity(row) for row in rows]

    async def get_unapplied_learnings(
        self,
        min_confidence: float = 0.7,
        limit: int = 100
    ) -> List[Learning]:
        """
        Get learnings that have NOT been applied yet.

        Args:
            min_confidence: Minimum confidence level (default 0.7)
            limit: Maximum number of results

        Returns:
            List of unapplied Learning entities
        """
        query = f"""
            SELECT * FROM {self.table_name}
            WHERE has_applied = false
              AND confidence_level >= $1
            ORDER BY confidence_level DESC, created_at DESC
            LIMIT $2
        """

        async with self.db.acquire() as conn:
            rows = await conn.fetch(query, min_confidence, limit)

        return [self._row_to_entity(row) for row in rows]

    async def get_recent_learnings(
        self,
        days: int = 7,
        category: Optional[str] = None,
        limit: int = 100
    ) -> List[Learning]:
        """
        Get learnings from the last N days.

        Args:
            days: Number of days to look back
            category: Optional category filter
            limit: Maximum number of results

        Returns:
            List of recent Learning entities
        """
        cutoff_date = datetime.now() - timedelta(days=days)

        if category:
            query = f"""
                SELECT * FROM {self.table_name}
                WHERE created_at >= $1
                  AND category = $2
                ORDER BY created_at DESC
                LIMIT $3
            """
            async with self.db.acquire() as conn:
                rows = await conn.fetch(query, cutoff_date, category, limit)
        else:
            query = f"""
                SELECT * FROM {self.table_name}
                WHERE created_at >= $1
                ORDER BY created_at DESC
                LIMIT $2
            """
            async with self.db.acquire() as conn:
                rows = await conn.fetch(query, cutoff_date, limit)

        return [self._row_to_entity(row) for row in rows]

    async def get_reinforced_learnings(
        self,
        min_times: int = 3,
        category: Optional[str] = None,
        limit: int = 100
    ) -> List[Learning]:
        """
        Get learnings that have been reinforced at least N times.

        Args:
            min_times: Minimum reinforcement count
            category: Optional category filter
            limit: Maximum number of results

        Returns:
            List of well-reinforced Learning entities
        """
        if category:
            query = f"""
                SELECT * FROM {self.table_name}
                WHERE times_reinforced >= $1
                  AND category = $2
                ORDER BY times_reinforced DESC, confidence_level DESC
                LIMIT $3
            """
            async with self.db.acquire() as conn:
                rows = await conn.fetch(query, min_times, category, limit)
        else:
            query = f"""
                SELECT * FROM {self.table_name}
                WHERE times_reinforced >= $1
                ORDER BY times_reinforced DESC, confidence_level DESC
                LIMIT $2
            """
            async with self.db.acquire() as conn:
                rows = await conn.fetch(query, min_times, limit)

        return [self._row_to_entity(row) for row in rows]

    async def get_from_conversation(
        self,
        conversation_id: UUID
    ) -> List[Learning]:
        """
        Get all learnings derived from a specific conversation.

        Args:
            conversation_id: ID of the conversation

        Returns:
            List of Learning entities from that conversation
        """
        query = f"""
            SELECT * FROM {self.table_name}
            WHERE learned_from = $1
            ORDER BY created_at DESC
        """

        async with self.db.acquire() as conn:
            rows = await conn.fetch(query, conversation_id)

        return [self._row_to_entity(row) for row in rows]

    async def search_by_topic(
        self,
        query: str,
        limit: int = 20
    ) -> List[Learning]:
        """
        Search learnings by topic text (case-insensitive).

        Args:
            query: Search query
            limit: Maximum number of results

        Returns:
            List of matching Learning entities
        """
        sql_query = f"""
            SELECT * FROM {self.table_name}
            WHERE topic ILIKE $1
               OR insight ILIKE $1
            ORDER BY confidence_level DESC, created_at DESC
            LIMIT $2
        """

        search_pattern = f"%{query}%"

        async with self.db.acquire() as conn:
            rows = await conn.fetch(sql_query, search_pattern, limit)

        return [self._row_to_entity(row) for row in rows]

    async def get_by_confidence_range(
        self,
        min_confidence: float,
        max_confidence: float,
        category: Optional[str] = None,
        limit: int = 100
    ) -> List[Learning]:
        """
        Get learnings within a confidence range.

        Args:
            min_confidence: Minimum confidence (inclusive)
            max_confidence: Maximum confidence (inclusive)
            category: Optional category filter
            limit: Maximum number of results

        Returns:
            List of Learning entities in confidence range
        """
        if category:
            query = f"""
                SELECT * FROM {self.table_name}
                WHERE confidence_level >= $1
                  AND confidence_level <= $2
                  AND category = $3
                ORDER BY confidence_level DESC, created_at DESC
                LIMIT $4
            """
            async with self.db.acquire() as conn:
                rows = await conn.fetch(query, min_confidence, max_confidence, category, limit)
        else:
            query = f"""
                SELECT * FROM {self.table_name}
                WHERE confidence_level >= $1
                  AND confidence_level <= $2
                ORDER BY confidence_level DESC, created_at DESC
                LIMIT $3
            """
            async with self.db.acquire() as conn:
                rows = await conn.fetch(query, min_confidence, max_confidence, limit)

        return [self._row_to_entity(row) for row in rows]

    async def get_needs_reinforcement(
        self,
        max_confidence: float = 0.7,
        limit: int = 100
    ) -> List[Learning]:
        """
        Get learnings that need more reinforcement.

        Identifies learnings with low confidence OR few reinforcements.

        Args:
            max_confidence: Maximum confidence (default 0.7)
            limit: Maximum number of results

        Returns:
            List of Learning entities that could use reinforcement
        """
        query = f"""
            SELECT * FROM {self.table_name}
            WHERE confidence_level < $1
               OR times_reinforced < 3
            ORDER BY confidence_level ASC, times_reinforced ASC, created_at DESC
            LIMIT $2
        """

        async with self.db.acquire() as conn:
            rows = await conn.fetch(query, max_confidence, limit)

        return [self._row_to_entity(row) for row in rows]
