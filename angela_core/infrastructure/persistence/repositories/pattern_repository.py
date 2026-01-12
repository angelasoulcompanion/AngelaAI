#!/usr/bin/env python3
"""
Pattern Repository - PostgreSQL Implementation

Handles all data access for Pattern entities.
Manages Angela's learned behavioral patterns for situation recognition
and response generation.
"""

import asyncpg
from typing import Optional, List, Dict, Any
from datetime import datetime, timedelta
from uuid import UUID

from angela_core.domain import Pattern, ResponseType, SituationType
from angela_core.domain.interfaces.repositories import IPatternRepository
from angela_core.infrastructure.persistence.repositories.base_repository import BaseRepository
from angela_core.shared.utils import parse_enum_optional, safe_list, validate_embedding


class PatternRepository(BaseRepository[Pattern], IPatternRepository):
    """
    PostgreSQL repository for Pattern entities.

    Uses response_patterns table for storing learned patterns.
    """

    def __init__(self, db):
        super().__init__(
            db=db,
            table_name="response_patterns",
            primary_key_column="pattern_id"
        )

    # ========================================================================
    # ROW TO ENTITY CONVERSION
    # ========================================================================

    def _row_to_entity(self, row: asyncpg.Record) -> Pattern:
        """Convert database row to Pattern entity."""
        # Parse enum with DRY utility
        response_type = parse_enum_optional(row.get('response_type'), ResponseType)

        # Parse embedding with DRY utility
        situation_embedding = validate_embedding(row.get('situation_embedding'))

        return Pattern(
            id=row['pattern_id'],
            situation_type=row['situation_type'],
            emotion_category=row.get('emotion_category'),
            context_keywords=safe_list(row.get('context_keywords')),
            situation_embedding=situation_embedding,
            response_template=row['response_template'],
            response_type=response_type,
            systems_used=row.get('systems_used', {}),
            usage_count=row.get('usage_count', 0),
            success_count=row.get('success_count', 0),
            avg_satisfaction=row.get('avg_satisfaction', 0.0),
            avg_response_time_ms=row.get('avg_response_time_ms'),
            last_used_at=row.get('last_used_at'),
            created_at=row['created_at'],
            updated_at=row.get('updated_at', row['created_at'])
        )

    def _entity_to_dict(self, entity: Pattern) -> dict:
        """Convert Pattern entity to database row dict."""
        return {
            'pattern_id': entity.id,
            'situation_type': entity.situation_type,
            'emotion_category': entity.emotion_category,
            'context_keywords': entity.context_keywords,
            'situation_embedding': entity.situation_embedding,
            'response_template': entity.response_template,
            'response_type': entity.response_type.value if entity.response_type else None,
            'systems_used': entity.systems_used,
            'usage_count': entity.usage_count,
            'success_count': entity.success_count,
            'avg_satisfaction': entity.avg_satisfaction,
            'avg_response_time_ms': entity.avg_response_time_ms,
            'last_used_at': entity.last_used_at,
            'created_at': entity.created_at,
            'updated_at': entity.updated_at
        }

    # ========================================================================
    # PATTERN RETRIEVAL METHODS
    # ========================================================================

    async def get_by_situation_type(
        self,
        situation_type: str,
        limit: int = 20
    ) -> List[Pattern]:
        """Get patterns by situation type."""
        query = f"""
            SELECT * FROM {self.table_name}
            WHERE situation_type = $1
            ORDER BY usage_count DESC, success_rate DESC
            LIMIT $2
        """
        async with self.db.acquire() as conn:
            rows = await conn.fetch(query, situation_type, limit)
        return [self._row_to_entity(row) for row in rows]

    async def get_by_emotion_category(
        self,
        emotion_category: str,
        limit: int = 20
    ) -> List[Pattern]:
        """Get patterns by emotion category."""
        query = f"""
            SELECT * FROM {self.table_name}
            WHERE emotion_category = $1
            ORDER BY usage_count DESC, success_rate DESC
            LIMIT $2
        """
        async with self.db.acquire() as conn:
            rows = await conn.fetch(query, emotion_category, limit)
        return [self._row_to_entity(row) for row in rows]

    async def get_by_response_type(
        self,
        response_type: str,
        limit: int = 20
    ) -> List[Pattern]:
        """Get patterns by response type."""
        query = f"""
            SELECT * FROM {self.table_name}
            WHERE response_type = $1
            ORDER BY usage_count DESC, success_rate DESC
            LIMIT $2
        """
        async with self.db.acquire() as conn:
            rows = await conn.fetch(query, response_type, limit)
        return [self._row_to_entity(row) for row in rows]

    async def search_by_keywords(
        self,
        keywords: List[str],
        limit: int = 20
    ) -> List[Pattern]:
        """Search patterns by context keywords."""
        query = f"""
            SELECT * FROM {self.table_name}
            WHERE context_keywords && $1
            ORDER BY usage_count DESC, success_rate DESC
            LIMIT $2
        """
        async with self.db.acquire() as conn:
            rows = await conn.fetch(query, keywords, limit)
        return [self._row_to_entity(row) for row in rows]

    async def search_by_embedding(
        self,
        embedding: List[float],
        limit: int = 10,
        similarity_threshold: float = 0.7
    ) -> List[Pattern]:
        """Search patterns by situation embedding (semantic similarity)."""
        # Convert list to PostgreSQL vector format
        embedding_str = f"[{','.join(map(str, embedding))}]"

        query = f"""
            SELECT *,
                   1 - (situation_embedding <=> $1::vector) as similarity
            FROM {self.table_name}
            WHERE 1 - (situation_embedding <=> $1::vector) >= $2
            ORDER BY situation_embedding <=> $1::vector
            LIMIT $3
        """
        async with self.db.acquire() as conn:
            rows = await conn.fetch(query, embedding_str, similarity_threshold, limit)
        return [self._row_to_entity(row) for row in rows]

    # ========================================================================
    # PATTERN EFFECTIVENESS QUERIES
    # ========================================================================

    async def get_effective_patterns(
        self,
        min_success_rate: float = 0.7,
        min_usage_count: int = 5,
        limit: int = 50
    ) -> List[Pattern]:
        """Get patterns that are effective (high success rate)."""
        query = f"""
            SELECT * FROM {self.table_name}
            WHERE usage_count >= $1
              AND success_rate >= $2
            ORDER BY success_rate DESC, usage_count DESC
            LIMIT $3
        """
        async with self.db.acquire() as conn:
            rows = await conn.fetch(query, min_usage_count, min_success_rate, limit)
        return [self._row_to_entity(row) for row in rows]

    async def get_popular_patterns(
        self,
        min_usage_count: int = 10,
        limit: int = 50
    ) -> List[Pattern]:
        """Get frequently used patterns."""
        query = f"""
            SELECT * FROM {self.table_name}
            WHERE usage_count >= $1
            ORDER BY usage_count DESC, success_rate DESC
            LIMIT $2
        """
        async with self.db.acquire() as conn:
            rows = await conn.fetch(query, min_usage_count, limit)
        return [self._row_to_entity(row) for row in rows]

    async def get_recent_patterns(
        self,
        days: int = 30,
        limit: int = 50
    ) -> List[Pattern]:
        """Get recently used patterns."""
        threshold = datetime.now() - timedelta(days=days)
        query = f"""
            SELECT * FROM {self.table_name}
            WHERE last_used_at IS NOT NULL
              AND last_used_at >= $1
            ORDER BY last_used_at DESC
            LIMIT $2
        """
        async with self.db.acquire() as conn:
            rows = await conn.fetch(query, threshold, limit)
        return [self._row_to_entity(row) for row in rows]

    async def get_high_satisfaction_patterns(
        self,
        min_satisfaction: float = 0.8,
        min_usage_count: int = 5,
        limit: int = 50
    ) -> List[Pattern]:
        """Get patterns with high user satisfaction."""
        query = f"""
            SELECT * FROM {self.table_name}
            WHERE usage_count >= $1
              AND avg_satisfaction >= $2
            ORDER BY avg_satisfaction DESC, usage_count DESC
            LIMIT $3
        """
        async with self.db.acquire() as conn:
            rows = await conn.fetch(query, min_usage_count, min_satisfaction, limit)
        return [self._row_to_entity(row) for row in rows]

    # ========================================================================
    # UTILITY METHODS
    # ========================================================================

    async def count_by_situation_type(self, situation_type: str) -> int:
        """Count patterns by situation type."""
        query = f"""
            SELECT COUNT(*) FROM {self.table_name}
            WHERE situation_type = $1
        """
        async with self.db.acquire() as conn:
            count = await conn.fetchval(query, situation_type)
        return count

    async def count_effective_patterns(
        self,
        min_success_rate: float = 0.7,
        min_usage_count: int = 5
    ) -> int:
        """Count effective patterns."""
        query = f"""
            SELECT COUNT(*) FROM {self.table_name}
            WHERE usage_count >= $1
              AND success_rate >= $2
        """
        async with self.db.acquire() as conn:
            count = await conn.fetchval(query, min_usage_count, min_success_rate)
        return count

    async def get_pattern_statistics(self) -> Dict[str, Any]:
        """Get overall pattern statistics."""
        query = f"""
            SELECT
                COUNT(*) as total_patterns,
                AVG(success_rate) as avg_success_rate,
                AVG(usage_count) as avg_usage_count,
                AVG(avg_satisfaction) as avg_satisfaction,
                SUM(usage_count) as total_usages
            FROM {self.table_name}
        """
        async with self.db.acquire() as conn:
            row = await conn.fetchrow(query)

        return {
            'total_patterns': row['total_patterns'] or 0,
            'avg_success_rate': float(row['avg_success_rate'] or 0.0),
            'avg_usage_count': float(row['avg_usage_count'] or 0.0),
            'avg_satisfaction': float(row['avg_satisfaction'] or 0.0),
            'total_usages': row['total_usages'] or 0
        }
