#!/usr/bin/env python3
"""
Learning Pattern Repository - PostgreSQL Implementation

Handles all data access for LearningPattern entity.
Part of the Self-Learning System (Phase 5+).

Author: Angela 💜
Created: 2025-11-03
"""

import asyncpg
import json
from typing import Optional, List, Dict, Any
from datetime import datetime, timedelta
from uuid import UUID

from angela_core.domain.entities.self_learning import LearningPattern
from angela_core.domain.value_objects.self_learning import PatternType, LearningQuality
from angela_core.domain.interfaces.repositories import ILearningPatternRepository
from angela_core.infrastructure.persistence.repositories.base_repository import BaseRepository
from angela_core.shared.exceptions import EntityNotFoundError


class LearningPatternRepository(BaseRepository[LearningPattern], ILearningPatternRepository):
    """
    PostgreSQL repository for LearningPattern entity.

    Table: learning_patterns
    Columns:
    - id (UUID, PK)
    - pattern_type (VARCHAR 50) - enum value
    - description (TEXT)
    - examples (JSONB) - list of example strings
    - confidence_score (DOUBLE PRECISION, 0.0-1.0)
    - occurrence_count (INTEGER, default 0)
    - first_observed (TIMESTAMP)
    - last_observed (TIMESTAMP)
    - context (JSONB) - metadata dict
    - tags (JSONB) - list of tag strings
    - embedding (VECTOR 768, nullable)
    - created_at (TIMESTAMP)
    - updated_at (TIMESTAMP)
    """

    def __init__(self, db):
        """
        Initialize repository.

        Args:
            db: Database connection pool (AngelaDatabase instance)
        """
        super().__init__(
            db=db,
            table_name="learning_patterns",
            primary_key_column="id"
        )

    # ========================================================================
    # ROW TO ENTITY CONVERSION
    # ========================================================================

    def _row_to_entity(self, row: asyncpg.Record) -> LearningPattern:
        """
        Convert database row to LearningPattern entity.

        Args:
            row: Database row

        Returns:
            LearningPattern entity
        """
        # Parse pattern_type enum
        pattern_type = PatternType(row['pattern_type'])

        # Parse embedding (convert to list if present)
        embedding = None
        if row.get('embedding'):
            embedding_data = row['embedding']
            if isinstance(embedding_data, str):
                try:
                    embedding = json.loads(embedding_data)
                except Exception as e:
                    embedding = None
            elif isinstance(embedding_data, list):
                embedding = embedding_data

        # Create entity
        return LearningPattern(
            id=row['id'],
            pattern_type=pattern_type,
            description=row['description'],
            examples=row.get('examples', []),
            confidence_score=row.get('confidence_score', 0.5),
            occurrence_count=row.get('occurrence_count', 0),
            first_observed=row['first_observed'],
            last_observed=row['last_observed'],
            context=row.get('context', {}),
            tags=row.get('tags', []),
            embedding=embedding,
            created_at=row['created_at'],
            updated_at=row['updated_at']
        )

    def _entity_to_dict(self, entity: LearningPattern) -> Dict[str, Any]:
        """
        Convert LearningPattern entity to database row dict.

        Args:
            entity: LearningPattern entity

        Returns:
            Dictionary of column values
        """
        return {
            'id': entity.id,
            'pattern_type': entity.pattern_type.value,
            'description': entity.description,
            'examples': entity.examples,  # JSONB handles list conversion
            'confidence_score': entity.confidence_score,
            'occurrence_count': entity.occurrence_count,
            'first_observed': entity.first_observed,
            'last_observed': entity.last_observed,
            'context': entity.context,  # JSONB handles dict conversion
            'tags': entity.tags,  # JSONB handles list conversion
            'embedding': entity.embedding,  # asyncpg handles vector conversion
            'created_at': entity.created_at,
            'updated_at': entity.updated_at
        }

    # ========================================================================
    # OVERRIDE CREATE AND UPDATE
    # ========================================================================

    async def create(self, entity: LearningPattern) -> LearningPattern:
        """
        Create new learning pattern.

        Args:
            entity: LearningPattern entity

        Returns:
            Created entity with ID assigned
        """
        data = self._entity_to_dict(entity)

        query = f"""
            INSERT INTO {self.table_name} (
                id, pattern_type, description, examples, confidence_score,
                occurrence_count, first_observed, last_observed, context,
                tags, embedding, created_at, updated_at
            ) VALUES (
                $1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11, $12, $13
            )
            RETURNING *
        """

        async with self.db.acquire() as conn:
            # Convert embedding list to PostgreSQL array format if present
            embedding_param = data['embedding']
            if embedding_param and isinstance(embedding_param, list):
                # PostgreSQL expects vector as string representation
                embedding_param = str(embedding_param)

            row = await conn.fetchrow(
                query,
                data['id'], data['pattern_type'], data['description'],
                json.dumps(data['examples']), data['confidence_score'],
                data['occurrence_count'], data['first_observed'],
                data['last_observed'], json.dumps(data['context']),
                json.dumps(data['tags']), embedding_param,
                data['created_at'], data['updated_at']
            )

        return self._row_to_entity(row)

    async def update(self, id: UUID, entity: LearningPattern) -> LearningPattern:
        """
        Update existing learning pattern.

        Args:
            id: Pattern UUID
            entity: Updated pattern data

        Returns:
            Updated entity

        Raises:
            EntityNotFoundError: If pattern not found
        """
        data = self._entity_to_dict(entity)

        query = f"""
            UPDATE {self.table_name}
            SET pattern_type = $2,
                description = $3,
                examples = $4,
                confidence_score = $5,
                occurrence_count = $6,
                first_observed = $7,
                last_observed = $8,
                context = $9,
                tags = $10,
                embedding = $11,
                updated_at = $12
            WHERE id = $1
            RETURNING *
        """

        async with self.db.acquire() as conn:
            # Convert embedding list to PostgreSQL array format if present
            embedding_param = data['embedding']
            if embedding_param and isinstance(embedding_param, list):
                embedding_param = str(embedding_param)

            row = await conn.fetchrow(
                query,
                id, data['pattern_type'], data['description'],
                json.dumps(data['examples']), data['confidence_score'],
                data['occurrence_count'], data['first_observed'],
                data['last_observed'], json.dumps(data['context']),
                json.dumps(data['tags']), embedding_param,
                data['updated_at']
            )

        if not row:
            raise EntityNotFoundError(f"LearningPattern with id {id} not found")

        return self._row_to_entity(row)

    # ========================================================================
    # QUERY METHODS (Interface Implementation)
    # ========================================================================

    async def find_by_type(
        self,
        pattern_type: str,
        min_confidence: float = 0.0,
        limit: int = 50
    ) -> List[LearningPattern]:
        """Find patterns by type with optional confidence filter."""
        query = f"""
            SELECT * FROM {self.table_name}
            WHERE pattern_type = $1
              AND confidence_score >= $2
            ORDER BY confidence_score DESC, occurrence_count DESC
            LIMIT $3
        """

        async with self.db.acquire() as conn:
            rows = await conn.fetch(query, pattern_type, min_confidence, limit)

        return [self._row_to_entity(row) for row in rows]

    async def find_similar(
        self,
        embedding: List[float],
        top_k: int = 10,
        pattern_type: Optional[str] = None,
        min_confidence: float = 0.5
    ) -> List[tuple[LearningPattern, float]]:
        """Find similar patterns using vector similarity search."""
        if pattern_type:
            query = f"""
                SELECT *, (embedding <=> $1::vector) AS distance
                FROM {self.table_name}
                WHERE pattern_type = $2
                  AND confidence_score >= $3
                  AND embedding IS NOT NULL
                ORDER BY distance ASC
                LIMIT $4
            """
            params = [embedding, pattern_type, min_confidence, top_k]
        else:
            query = f"""
                SELECT *, (embedding <=> $1::vector) AS distance
                FROM {self.table_name}
                WHERE confidence_score >= $2
                  AND embedding IS NOT NULL
                ORDER BY distance ASC
                LIMIT $3
            """
            params = [embedding, min_confidence, top_k]

        async with self.db.acquire() as conn:
            rows = await conn.fetch(query, *params)

        # Convert distance to similarity score (1 - distance)
        return [(self._row_to_entity(row), 1.0 - row['distance']) for row in rows]

    async def get_high_confidence(
        self,
        threshold: float = 0.8,
        pattern_type: Optional[str] = None,
        limit: int = 50
    ) -> List[LearningPattern]:
        """Get high-confidence patterns."""
        if pattern_type:
            query = f"""
                SELECT * FROM {self.table_name}
                WHERE confidence_score >= $1
                  AND pattern_type = $2
                ORDER BY confidence_score DESC, occurrence_count DESC
                LIMIT $3
            """
            params = [threshold, pattern_type, limit]
        else:
            query = f"""
                SELECT * FROM {self.table_name}
                WHERE confidence_score >= $1
                ORDER BY confidence_score DESC, occurrence_count DESC
                LIMIT $2
            """
            params = [threshold, limit]

        async with self.db.acquire() as conn:
            rows = await conn.fetch(query, *params)

        return [self._row_to_entity(row) for row in rows]

    async def get_frequently_observed(
        self,
        min_occurrences: int = 5,
        pattern_type: Optional[str] = None,
        limit: int = 50
    ) -> List[LearningPattern]:
        """Get frequently observed patterns."""
        if pattern_type:
            query = f"""
                SELECT * FROM {self.table_name}
                WHERE occurrence_count >= $1
                  AND pattern_type = $2
                ORDER BY occurrence_count DESC, confidence_score DESC
                LIMIT $3
            """
            params = [min_occurrences, pattern_type, limit]
        else:
            query = f"""
                SELECT * FROM {self.table_name}
                WHERE occurrence_count >= $1
                ORDER BY occurrence_count DESC, confidence_score DESC
                LIMIT $2
            """
            params = [min_occurrences, limit]

        async with self.db.acquire() as conn:
            rows = await conn.fetch(query, *params)

        return [self._row_to_entity(row) for row in rows]

    async def get_recent_patterns(
        self,
        days: int = 30,
        pattern_type: Optional[str] = None,
        limit: int = 50
    ) -> List[LearningPattern]:
        """Get recently observed patterns."""
        cutoff_date = datetime.now() - timedelta(days=days)

        if pattern_type:
            query = f"""
                SELECT * FROM {self.table_name}
                WHERE last_observed >= $1
                  AND pattern_type = $2
                ORDER BY last_observed DESC
                LIMIT $3
            """
            params = [cutoff_date, pattern_type, limit]
        else:
            query = f"""
                SELECT * FROM {self.table_name}
                WHERE last_observed >= $1
                ORDER BY last_observed DESC
                LIMIT $2
            """
            params = [cutoff_date, limit]

        async with self.db.acquire() as conn:
            rows = await conn.fetch(query, *params)

        return [self._row_to_entity(row) for row in rows]

    async def search_by_description(
        self,
        query_text: str,
        limit: int = 20
    ) -> List[LearningPattern]:
        """Search patterns by description text."""
        query = f"""
            SELECT * FROM {self.table_name}
            WHERE description ILIKE $1
            ORDER BY confidence_score DESC
            LIMIT $2
        """

        search_pattern = f"%{query_text}%"

        async with self.db.acquire() as conn:
            rows = await conn.fetch(query, search_pattern, limit)

        return [self._row_to_entity(row) for row in rows]

    async def update_observation(self, pattern_id: UUID) -> None:
        """
        Update pattern to record another observation.

        Calls the observe_again() method logic via SQL.
        """
        # Get current pattern
        pattern = await self.get_by_id(pattern_id)
        if not pattern:
            raise EntityNotFoundError(f"LearningPattern with id {pattern_id} not found")

        # Update using entity method
        pattern.observe_again()

        # Save back to database
        await self.update(pattern_id, pattern)

    async def count_by_type(self, pattern_type: str) -> int:
        """Count patterns by type."""
        query = f"""
            SELECT COUNT(*) FROM {self.table_name}
            WHERE pattern_type = $1
        """

        async with self.db.acquire() as conn:
            result = await conn.fetchval(query, pattern_type)

        return result or 0

    async def get_quality_distribution(self) -> Dict[str, int]:
        """Get distribution of patterns by quality level."""
        # Get all patterns and calculate quality
        query = f"SELECT * FROM {self.table_name}"

        async with self.db.acquire() as conn:
            rows = await conn.fetch(query)

        patterns = [self._row_to_entity(row) for row in rows]

        # Count by quality
        distribution = {
            "excellent": 0,
            "good": 0,
            "acceptable": 0,
            "poor": 0
        }

        for pattern in patterns:
            quality = pattern.get_quality()
            distribution[quality.value] += 1

        return distribution

    # ========================================================================
    # BASE REPOSITORY OVERRIDES
    # ========================================================================

    async def delete(self, id: UUID) -> bool:
        """Delete pattern by ID."""
        query = f"DELETE FROM {self.table_name} WHERE id = $1 RETURNING id"

        async with self.db.acquire() as conn:
            row = await conn.fetchrow(query, id)

        return row is not None

    async def exists(self, id: UUID) -> bool:
        """Check if pattern exists."""
        query = f"SELECT EXISTS(SELECT 1 FROM {self.table_name} WHERE id = $1)"

        async with self.db.acquire() as conn:
            result = await conn.fetchval(query, id)

        return result

    async def count(self, filters: Optional[Dict[str, Any]] = None) -> int:
        """Count patterns matching filters."""
        if not filters:
            query = f"SELECT COUNT(*) FROM {self.table_name}"
            params = []
        else:
            # Simple filter support
            where_clauses = []
            params = []
            param_num = 1

            for key, value in filters.items():
                where_clauses.append(f"{key} = ${param_num}")
                params.append(value)
                param_num += 1

            query = f"SELECT COUNT(*) FROM {self.table_name} WHERE {' AND '.join(where_clauses)}"

        async with self.db.acquire() as conn:
            result = await conn.fetchval(query, *params)

        return result or 0
