#!/usr/bin/env python3
"""
Memory Repository - PostgreSQL Implementation

Handles all data access for Memory entity.
Manages Angela's long-term memories with decay and consolidation.
"""

import asyncpg
from typing import Optional, List, Dict, Any
from datetime import datetime, timedelta
from uuid import UUID

from angela_core.domain import Memory, MemoryPhase
from angela_core.domain.interfaces.repositories import IMemoryRepository
from angela_core.infrastructure.persistence.repositories.base_repository import BaseRepository
from angela_core.shared.utils import parse_enum, parse_enum_optional, safe_dict, validate_embedding


class MemoryRepository(BaseRepository[Memory], IMemoryRepository):
    """
    PostgreSQL repository for Memory entity.

    Table: long_term_memory
    Columns:
    - id (UUID, PK)
    - content (TEXT)
    - metadata (JSONB)
    - importance (DOUBLE PRECISION, 0.0-1.0)
    - memory_phase (VARCHAR)
    - memory_strength (DOUBLE PRECISION)
    - half_life_days (DOUBLE PRECISION)
    - last_decayed (TIMESTAMP, nullable)
    - access_count (INTEGER)
    - last_accessed (TIMESTAMP, nullable)
    - token_count (INTEGER)
    - promoted_from (VARCHAR, nullable)
    - source_event_id (UUID, nullable)
    - embedding (VECTOR(384), nullable)
    - created_at (TIMESTAMP)
    """

    def __init__(self, db):
        """Initialize repository."""
        super().__init__(
            db=db,
            table_name="long_term_memory",
            primary_key_column="id"
        )

    # ========================================================================
    # ROW TO ENTITY CONVERSION
    # ========================================================================

    def _row_to_entity(self, row: asyncpg.Record) -> Memory:
        """Convert database row to Memory entity."""
        # Parse enums with DRY utilities
        memory_phase = parse_enum(row['memory_phase'], MemoryPhase)
        promoted_from = parse_enum_optional(row.get('promoted_from'), MemoryPhase)

        # Parse embedding with DRY utility
        embedding = validate_embedding(row.get('embedding'))

        return Memory(
            content=row['content'],
            id=row['id'],
            metadata=safe_dict(row.get('metadata')),
            importance=row.get('importance', 0.5),
            memory_phase=memory_phase,
            memory_strength=row.get('memory_strength', 1.0),
            half_life_days=row.get('half_life_days', 30.0),
            last_decayed=row.get('last_decayed'),
            access_count=row.get('access_count', 0),
            last_accessed=row.get('last_accessed'),
            token_count=row.get('token_count', 500),
            promoted_from=promoted_from,
            source_event_id=row.get('source_event_id'),
            embedding=embedding,
            created_at=row['created_at']
        )

    def _entity_to_dict(self, entity: Memory) -> Dict[str, Any]:
        """
        Convert Memory entity to database row dict.

        Args:
            entity: Memory entity

        Returns:
            Dictionary for database insert/update
        """
        return {
            'id': entity.id,
            'content': entity.content,
            'metadata': entity.metadata,
            'importance': entity.importance,
            'memory_phase': entity.memory_phase.value,
            'memory_strength': entity.memory_strength,
            'half_life_days': entity.half_life_days,
            'last_decayed': entity.last_decayed,
            'access_count': entity.access_count,
            'last_accessed': entity.last_accessed,
            'token_count': entity.token_count,
            'promoted_from': entity.promoted_from.value if entity.promoted_from else None,
            'source_event_id': entity.source_event_id,
            'embedding': entity.embedding,
            'created_at': entity.created_at
        }

    # ========================================================================
    # MEMORY-SPECIFIC QUERIES
    # ========================================================================

    async def search_by_vector(
        self,
        embedding: List[float],
        top_k: int = 5,
        memory_type: Optional[str] = None
    ) -> List[tuple[Memory, float]]:
        """
        Vector similarity search for memories.

        Args:
            embedding: Query embedding vector (384 dimensions)
            top_k: Number of top results to return
            memory_type: Optional memory phase filter

        Returns:
            List of (Memory, similarity_score) tuples
        """
        if memory_type:
            query = f"""
                SELECT *, (embedding <=> $1::vector) as distance
                FROM {self.table_name}
                WHERE memory_phase = $2 AND embedding IS NOT NULL
                ORDER BY distance ASC
                LIMIT $3
            """
            async with self.db.acquire() as conn:
                rows = await conn.fetch(query, embedding, memory_type, top_k)
        else:
            query = f"""
                SELECT *, (embedding <=> $1::vector) as distance
                FROM {self.table_name}
                WHERE embedding IS NOT NULL
                ORDER BY distance ASC
                LIMIT $2
            """
            async with self.db.acquire() as conn:
                rows = await conn.fetch(query, embedding, top_k)

        # Convert distance to similarity score (1 - distance for cosine)
        results = []
        for row in rows:
            memory = self._row_to_entity(row)
            similarity = 1.0 - float(row['distance'])
            results.append((memory, similarity))

        return results

    async def get_by_phase(
        self,
        phase: str,
        limit: int = 100
    ) -> List[Memory]:
        """
        Get memories by phase.

        Args:
            phase: Memory phase (episodic, compressed_1, compressed_2, semantic, pattern, intuitive, forgotten)
            limit: Maximum results

        Returns:
            List of memories in phase
        """
        query = f"""
            SELECT * FROM {self.table_name}
            WHERE memory_phase = $1
            ORDER BY created_at DESC
            LIMIT $2
        """

        async with self.db.acquire() as conn:
            rows = await conn.fetch(query, phase, limit)

        return [self._row_to_entity(row) for row in rows]

    async def get_by_type(
        self,
        memory_type: str,
        limit: int = 50
    ) -> List[Memory]:
        """
        Get memories by type (same as phase for now).

        Args:
            memory_type: Memory type (episodic, semantic, etc.)
            limit: Maximum results

        Returns:
            List of memories of type
        """
        return await self.get_by_phase(memory_type, limit)

    async def get_recent(
        self,
        days: int = 7,
        limit: int = 100
    ) -> List[Memory]:
        """
        Get recent memories (last N days).

        Args:
            days: Number of days to look back
            limit: Maximum results

        Returns:
            List of recent memories
        """
        cutoff_date = datetime.now() - timedelta(days=days)

        query = f"""
            SELECT * FROM {self.table_name}
            WHERE created_at >= $1
            ORDER BY created_at DESC
            LIMIT $2
        """

        async with self.db.acquire() as conn:
            rows = await conn.fetch(query, cutoff_date, limit)

        return [self._row_to_entity(row) for row in rows]

    async def get_important(
        self,
        threshold: float = 0.7,
        limit: int = 100
    ) -> List[Memory]:
        """
        Get important memories (importance >= threshold).

        Args:
            threshold: Importance threshold (0.0-1.0)
            limit: Maximum results

        Returns:
            List of important memories
        """
        query = f"""
            SELECT * FROM {self.table_name}
            WHERE importance >= $1
            ORDER BY importance DESC, created_at DESC
            LIMIT $2
        """

        async with self.db.acquire() as conn:
            rows = await conn.fetch(query, threshold, limit)

        return [self._row_to_entity(row) for row in rows]

    async def get_strong(
        self,
        threshold: float = 0.5,
        limit: int = 100
    ) -> List[Memory]:
        """
        Get strong memories (strength >= threshold).

        Args:
            threshold: Strength threshold (0.0-1.0)
            limit: Maximum results

        Returns:
            List of strong memories
        """
        query = f"""
            SELECT * FROM {self.table_name}
            WHERE memory_strength >= $1
            ORDER BY memory_strength DESC, created_at DESC
            LIMIT $2
        """

        async with self.db.acquire() as conn:
            rows = await conn.fetch(query, threshold, limit)

        return [self._row_to_entity(row) for row in rows]

    async def get_forgotten(
        self,
        limit: int = 100
    ) -> List[Memory]:
        """
        Get forgotten memories (strength < 0.1 or phase=forgotten).

        Args:
            limit: Maximum results

        Returns:
            List of forgotten memories
        """
        query = f"""
            SELECT * FROM {self.table_name}
            WHERE memory_strength < 0.1 OR memory_phase = 'forgotten'
            ORDER BY memory_strength ASC, created_at DESC
            LIMIT $1
        """

        async with self.db.acquire() as conn:
            rows = await conn.fetch(query, limit)

        return [self._row_to_entity(row) for row in rows]

    async def get_episodic(
        self,
        limit: int = 100
    ) -> List[Memory]:
        """
        Get episodic (fresh) memories.

        Args:
            limit: Maximum results

        Returns:
            List of episodic memories
        """
        return await self.get_by_phase('episodic', limit)

    async def get_semantic(
        self,
        limit: int = 100
    ) -> List[Memory]:
        """
        Get semantic (factual) memories.

        Args:
            limit: Maximum results

        Returns:
            List of semantic memories
        """
        return await self.get_by_phase('semantic', limit)

    async def get_ready_for_consolidation(
        self,
        limit: int = 100
    ) -> List[Memory]:
        """
        Get memories ready for consolidation to next phase.

        Consolidation criteria by phase:
        - EPISODIC: >= 7 days old
        - COMPRESSED_1: >= 30 days old
        - COMPRESSED_2: >= 90 days old
        - SEMANTIC: >= 180 days old
        - PATTERN: >= 365 days old
        - INTUITIVE: Already at final phase (none returned)
        - FORGOTTEN: Cannot consolidate (none returned)

        Args:
            limit: Maximum results

        Returns:
            List of memories ready for consolidation
        """
        # Calculate cutoff dates for each phase
        now = datetime.now()
        cutoffs = {
            'episodic': now - timedelta(days=7),
            'compressed_1': now - timedelta(days=30),
            'compressed_2': now - timedelta(days=90),
            'semantic': now - timedelta(days=180),
            'pattern': now - timedelta(days=365)
        }

        query = f"""
            SELECT * FROM {self.table_name}
            WHERE
                (memory_phase = 'episodic' AND created_at <= $1) OR
                (memory_phase = 'compressed_1' AND created_at <= $2) OR
                (memory_phase = 'compressed_2' AND created_at <= $3) OR
                (memory_phase = 'semantic' AND created_at <= $4) OR
                (memory_phase = 'pattern' AND created_at <= $5)
            ORDER BY created_at ASC
            LIMIT $6
        """

        async with self.db.acquire() as conn:
            rows = await conn.fetch(
                query,
                cutoffs['episodic'],
                cutoffs['compressed_1'],
                cutoffs['compressed_2'],
                cutoffs['semantic'],
                cutoffs['pattern'],
                limit
            )

        return [self._row_to_entity(row) for row in rows]

    async def search_by_content(
        self,
        query: str,
        limit: int = 100
    ) -> List[Memory]:
        """
        Search memories by content text.

        Args:
            query: Search query
            limit: Maximum results

        Returns:
            List of matching memories
        """
        search_query = f"""
            SELECT * FROM {self.table_name}
            WHERE content ILIKE $1
            ORDER BY created_at DESC
            LIMIT $2
        """

        async with self.db.acquire() as conn:
            rows = await conn.fetch(search_query, f"%{query}%", limit)

        return [self._row_to_entity(row) for row in rows]

    async def count_by_phase(self, phase: str) -> int:
        """
        Count memories by phase.

        Args:
            phase: Memory phase

        Returns:
            Count of memories in phase
        """
        query = f"""
            SELECT COUNT(*) FROM {self.table_name}
            WHERE memory_phase = $1
        """

        async with self.db.acquire() as conn:
            result = await conn.fetchval(query, phase)

        return result or 0

    async def get_by_importance(
        self,
        min_importance: float,
        max_importance: float = 1.0,
        limit: int = 50
    ) -> List[Memory]:
        """
        Get memories by importance range.

        Args:
            min_importance: Minimum importance threshold
            max_importance: Maximum importance threshold (default: 1.0)
            limit: Maximum results

        Returns:
            List of memories within importance range
        """
        query = f"""
            SELECT * FROM {self.table_name}
            WHERE importance >= $1 AND importance <= $2
            ORDER BY importance DESC, created_at DESC
            LIMIT $3
        """

        async with self.db.acquire() as conn:
            rows = await conn.fetch(query, min_importance, max_importance, limit)

        return [self._row_to_entity(row) for row in rows]
