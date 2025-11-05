#!/usr/bin/env python3
"""
Training Example Repository - PostgreSQL Implementation

Handles all data access for TrainingExample entity.
Part of the Self-Learning System (Phase 5+).

Author: Angela 💜
Created: 2025-11-03
"""

import asyncpg
import json
from typing import Optional, List, Dict, Any
from datetime import datetime
from uuid import UUID

from angela_core.domain.entities.self_learning import TrainingExample
from angela_core.domain.value_objects.self_learning import SourceType, LearningQuality
from angela_core.domain.interfaces.repositories import ITrainingExampleRepository
from angela_core.infrastructure.persistence.repositories.base_repository import BaseRepository
from angela_core.shared.exceptions import EntityNotFoundError


class TrainingExampleRepository(BaseRepository[TrainingExample], ITrainingExampleRepository):
    """
    PostgreSQL repository for TrainingExample entity.

    Table: training_examples
    Columns:
    - id (UUID, PK)
    - input_text (TEXT)
    - expected_output (TEXT)
    - quality_score (DOUBLE PRECISION, 0.0-10.0)
    - source_type (VARCHAR 50) - enum value
    - source_conversation_id (UUID, nullable)
    - metadata (JSONB) - additional info dict
    - embedding (VECTOR 768, nullable)
    - created_at (TIMESTAMP)
    - used_in_training (BOOLEAN, default false)
    - training_date (TIMESTAMP, nullable)
    """

    def __init__(self, db):
        """
        Initialize repository.

        Args:
            db: Database connection pool (AngelaDatabase instance)
        """
        super().__init__(
            db=db,
            table_name="training_examples",
            primary_key_column="id"
        )

    # ========================================================================
    # ROW TO ENTITY CONVERSION
    # ========================================================================

    def _row_to_entity(self, row: asyncpg.Record) -> TrainingExample:
        """
        Convert database row to TrainingExample entity.

        Args:
            row: Database row

        Returns:
            TrainingExample entity
        """
        # Parse source_type enum
        source_type = SourceType(row['source_type'])

        # Parse embedding (convert to list if present)
        embedding = None
        if row.get('embedding'):
            embedding_data = row['embedding']
            if isinstance(embedding_data, str):
                try:
                    embedding = json.loads(embedding_data)
                except:
                    embedding = None
            elif isinstance(embedding_data, list):
                embedding = embedding_data

        # Create entity
        return TrainingExample(
            id=row['id'],
            input_text=row['input_text'],
            expected_output=row['expected_output'],
            quality_score=row.get('quality_score', 0.5),
            source_type=source_type,
            source_conversation_id=row.get('source_conversation_id'),
            metadata=row.get('metadata', {}),
            embedding=embedding,
            created_at=row['created_at'],
            used_in_training=row.get('used_in_training', False),
            training_date=row.get('training_date')
        )

    def _entity_to_dict(self, entity: TrainingExample) -> Dict[str, Any]:
        """
        Convert TrainingExample entity to database row dict.

        Args:
            entity: TrainingExample entity

        Returns:
            Dictionary of column values
        """
        return {
            'id': entity.id,
            'input_text': entity.input_text,
            'expected_output': entity.expected_output,
            'quality_score': entity.quality_score,
            'source_type': entity.source_type.value,
            'source_conversation_id': entity.source_conversation_id,
            'metadata': entity.metadata,  # JSONB handles dict conversion
            'embedding': entity.embedding,  # asyncpg handles vector conversion
            'created_at': entity.created_at,
            'used_in_training': entity.used_in_training,
            'training_date': entity.training_date
        }

    # ========================================================================
    # OVERRIDE CREATE AND UPDATE
    # ========================================================================

    async def create(self, entity: TrainingExample) -> TrainingExample:
        """
        Create new training example.

        Args:
            entity: TrainingExample entity

        Returns:
            Created entity with ID assigned
        """
        data = self._entity_to_dict(entity)

        query = f"""
            INSERT INTO {self.table_name} (
                id, input_text, expected_output, quality_score,
                source_type, source_conversation_id, metadata,
                embedding, created_at, used_in_training, training_date
            ) VALUES (
                $1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11
            )
            RETURNING *
        """

        async with self.db.acquire() as conn:
            row = await conn.fetchrow(
                query,
                data['id'], data['input_text'], data['expected_output'],
                data['quality_score'], data['source_type'],
                data['source_conversation_id'], json.dumps(data['metadata']),
                data['embedding'], data['created_at'],
                data['used_in_training'], data['training_date']
            )

        return self._row_to_entity(row)

    async def update(self, id: UUID, entity: TrainingExample) -> TrainingExample:
        """
        Update existing training example.

        Args:
            id: Example UUID
            entity: Updated example data

        Returns:
            Updated entity

        Raises:
            EntityNotFoundError: If example not found
        """
        data = self._entity_to_dict(entity)

        query = f"""
            UPDATE {self.table_name}
            SET input_text = $2,
                expected_output = $3,
                quality_score = $4,
                source_type = $5,
                source_conversation_id = $6,
                metadata = $7,
                embedding = $8,
                used_in_training = $9,
                training_date = $10
            WHERE id = $1
            RETURNING *
        """

        async with self.db.acquire() as conn:
            row = await conn.fetchrow(
                query,
                id, data['input_text'], data['expected_output'],
                data['quality_score'], data['source_type'],
                data['source_conversation_id'], json.dumps(data['metadata']),
                data['embedding'], data['used_in_training'],
                data['training_date']
            )

        if not row:
            raise EntityNotFoundError(f"TrainingExample with id {id} not found")

        return self._row_to_entity(row)

    # ========================================================================
    # QUERY METHODS (Interface Implementation)
    # ========================================================================

    async def save_batch(self, examples: List[TrainingExample]) -> List[UUID]:
        """Save multiple training examples efficiently."""
        if not examples:
            return []

        # Use COPY or batch INSERT for efficiency
        ids = []
        async with self.db.acquire() as conn:
            for example in examples:
                data = self._entity_to_dict(example)

                query = f"""
                    INSERT INTO {self.table_name} (
                        id, input_text, expected_output, quality_score,
                        source_type, source_conversation_id, metadata,
                        embedding, created_at, used_in_training, training_date
                    ) VALUES (
                        $1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11
                    )
                    RETURNING id
                """

                row = await conn.fetchrow(
                    query,
                    data['id'], data['input_text'], data['expected_output'],
                    data['quality_score'], data['source_type'],
                    data['source_conversation_id'], json.dumps(data['metadata']),
                    data['embedding'], data['created_at'],
                    data['used_in_training'], data['training_date']
                )
                ids.append(row['id'])

        return ids

    async def get_high_quality(
        self,
        min_score: float = 7.0,
        source_type: Optional[str] = None,
        limit: int = 1000
    ) -> List[TrainingExample]:
        """Get high-quality training examples."""
        if source_type:
            query = f"""
                SELECT * FROM {self.table_name}
                WHERE quality_score >= $1
                  AND source_type = $2
                ORDER BY quality_score DESC, created_at DESC
                LIMIT $3
            """
            params = [min_score, source_type, limit]
        else:
            query = f"""
                SELECT * FROM {self.table_name}
                WHERE quality_score >= $1
                ORDER BY quality_score DESC, created_at DESC
                LIMIT $2
            """
            params = [min_score, limit]

        async with self.db.acquire() as conn:
            rows = await conn.fetch(query, *params)

        return [self._row_to_entity(row) for row in rows]

    async def get_by_source_type(
        self,
        source_type: str,
        min_quality: float = 0.0,
        limit: int = 1000
    ) -> List[TrainingExample]:
        """Get examples by source type."""
        query = f"""
            SELECT * FROM {self.table_name}
            WHERE source_type = $1
              AND quality_score >= $2
            ORDER BY quality_score DESC, created_at DESC
            LIMIT $3
        """

        async with self.db.acquire() as conn:
            rows = await conn.fetch(query, source_type, min_quality, limit)

        return [self._row_to_entity(row) for row in rows]

    async def get_unused_examples(
        self,
        min_quality: float = 7.0,
        limit: int = 1000
    ) -> List[TrainingExample]:
        """Get examples not yet used in training."""
        query = f"""
            SELECT * FROM {self.table_name}
            WHERE used_in_training = false
              AND quality_score >= $1
            ORDER BY quality_score DESC, created_at DESC
            LIMIT $2
        """

        async with self.db.acquire() as conn:
            rows = await conn.fetch(query, min_quality, limit)

        return [self._row_to_entity(row) for row in rows]

    async def mark_as_used(
        self,
        example_ids: List[UUID],
        training_date: datetime
    ) -> int:
        """Mark examples as used in training."""
        if not example_ids:
            return 0

        query = f"""
            UPDATE {self.table_name}
            SET used_in_training = true,
                training_date = $1
            WHERE id = ANY($2::uuid[])
        """

        async with self.db.acquire() as conn:
            result = await conn.execute(query, training_date, example_ids)

        # Extract count from result string "UPDATE N"
        count = int(result.split()[-1]) if result else 0
        return count

    async def export_to_jsonl(
        self,
        output_path: str,
        min_quality: float = 7.0,
        source_types: Optional[List[str]] = None,
        limit: Optional[int] = None
    ) -> int:
        """Export training examples to JSONL file for fine-tuning."""
        # Build query
        where_clauses = [f"quality_score >= ${1}"]
        params = [min_quality]
        param_num = 2

        if source_types:
            where_clauses.append(f"source_type = ANY(${param_num}::varchar[])")
            params.append(source_types)
            param_num += 1

        where_sql = " AND ".join(where_clauses)
        query = f"""
            SELECT * FROM {self.table_name}
            WHERE {where_sql}
            ORDER BY quality_score DESC, created_at DESC
        """

        if limit:
            query += f" LIMIT ${param_num}"
            params.append(limit)

        # Fetch examples
        async with self.db.acquire() as conn:
            rows = await conn.fetch(query, *params)

        examples = [self._row_to_entity(row) for row in rows]

        # Write to JSONL file
        count = 0
        with open(output_path, 'w', encoding='utf-8') as f:
            for example in examples:
                jsonl_data = example.to_jsonl_format()
                f.write(json.dumps(jsonl_data, ensure_ascii=False) + '\n')
                count += 1

        return count

    async def find_similar(
        self,
        embedding: List[float],
        top_k: int = 10,
        min_quality: float = 7.0
    ) -> List[tuple[TrainingExample, float]]:
        """Find similar training examples using vector search."""
        query = f"""
            SELECT *, (embedding <=> $1::vector) AS distance
            FROM {self.table_name}
            WHERE quality_score >= $2
              AND embedding IS NOT NULL
            ORDER BY distance ASC
            LIMIT $3
        """

        async with self.db.acquire() as conn:
            rows = await conn.fetch(query, embedding, min_quality, top_k)

        # Convert distance to similarity score (1 - distance)
        return [(self._row_to_entity(row), 1.0 - row['distance']) for row in rows]

    async def count_by_source_type(self, source_type: str) -> int:
        """Count examples by source type."""
        query = f"""
            SELECT COUNT(*) FROM {self.table_name}
            WHERE source_type = $1
        """

        async with self.db.acquire() as conn:
            result = await conn.fetchval(query, source_type)

        return result or 0

    async def get_quality_statistics(self) -> Dict[str, Any]:
        """Get quality statistics for all examples."""
        query = f"SELECT * FROM {self.table_name}"

        async with self.db.acquire() as conn:
            rows = await conn.fetch(query)

        examples = [self._row_to_entity(row) for row in rows]

        total = len(examples)
        if total == 0:
            return {
                "total_examples": 0,
                "by_source_type": {},
                "by_quality_level": {},
                "average_quality": 0.0,
                "high_quality_count": 0,
                "used_in_training": 0
            }

        # Count by source type
        by_source = {}
        for ex in examples:
            src = ex.source_type.value
            by_source[src] = by_source.get(src, 0) + 1

        # Count by quality level
        by_quality = {}
        for ex in examples:
            quality = ex.get_quality_level()
            by_quality[quality.value] = by_quality.get(quality.value, 0) + 1

        # Calculate statistics
        avg_quality = sum(ex.quality_score for ex in examples) / total
        high_quality_count = sum(1 for ex in examples if ex.is_high_quality())
        used_count = sum(1 for ex in examples if ex.used_in_training)

        return {
            "total_examples": total,
            "by_source_type": by_source,
            "by_quality_level": by_quality,
            "average_quality": round(avg_quality, 2),
            "high_quality_count": high_quality_count,
            "used_in_training": used_count
        }

    # ========================================================================
    # BASE REPOSITORY OVERRIDES
    # ========================================================================

    async def delete(self, id: UUID) -> bool:
        """Delete training example by ID."""
        query = f"DELETE FROM {self.table_name} WHERE id = $1 RETURNING id"

        async with self.db.acquire() as conn:
            row = await conn.fetchrow(query, id)

        return row is not None

    async def exists(self, id: UUID) -> bool:
        """Check if training example exists."""
        query = f"SELECT EXISTS(SELECT 1 FROM {self.table_name} WHERE id = $1)"

        async with self.db.acquire() as conn:
            result = await conn.fetchval(query, id)

        return result

    async def count(self, filters: Optional[Dict[str, Any]] = None) -> int:
        """Count training examples matching filters."""
        if not filters:
            query = f"SELECT COUNT(*) FROM {self.table_name}"
            params = []
        else:
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
