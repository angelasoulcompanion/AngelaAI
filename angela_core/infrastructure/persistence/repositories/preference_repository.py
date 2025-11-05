#!/usr/bin/env python3
"""
Preference Repository - PostgreSQL Implementation

Handles all data access for PreferenceItem entity.
Part of the Self-Learning System (Phase 5+).

Author: Angela 💜
Created: 2025-11-03
"""

import asyncpg
import json
from typing import Optional, List, Dict, Any
from datetime import datetime
from uuid import UUID

from angela_core.domain.entities.self_learning import PreferenceItem
from angela_core.domain.value_objects.self_learning import PreferenceCategory
from angela_core.domain.interfaces.repositories import IPreferenceRepository
from angela_core.infrastructure.persistence.repositories.base_repository import BaseRepository
from angela_core.shared.exceptions import EntityNotFoundError


class PreferenceRepository(BaseRepository[PreferenceItem], IPreferenceRepository):
    """
    PostgreSQL repository for PreferenceItem entity.

    Table: david_preferences
    Columns:
    - id (UUID, PK)
    - category (VARCHAR 50) - enum value
    - preference_key (VARCHAR 100, UNIQUE)
    - preference_value (JSONB) - can be any type
    - confidence (DOUBLE PRECISION, 0.0-1.0)
    - evidence_count (INTEGER, default 0)
    - evidence_conversation_ids (JSONB) - list of UUIDs
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
            table_name="david_preferences",
            primary_key_column="id"
        )

    # ========================================================================
    # ROW TO ENTITY CONVERSION
    # ========================================================================

    def _row_to_entity(self, row: asyncpg.Record) -> PreferenceItem:
        """
        Convert database row to PreferenceItem entity.

        Args:
            row: Database row

        Returns:
            PreferenceItem entity
        """
        # Parse category enum
        category = PreferenceCategory(row['category'])

        # Parse evidence_conversation_ids (JSONB list of UUID strings)
        evidence_ids = []
        if row.get('evidence_conversation_ids'):
            raw_ids = row['evidence_conversation_ids']
            if isinstance(raw_ids, list):
                evidence_ids = [UUID(id_str) for id_str in raw_ids]

        # Create entity
        return PreferenceItem(
            id=row['id'],
            category=category,
            preference_key=row['preference_key'],
            preference_value=row['preference_value'],  # JSONB can be any type
            confidence=row.get('confidence', 0.5),
            evidence_count=row.get('evidence_count', 0),
            evidence_conversation_ids=evidence_ids,
            created_at=row['created_at'],
            updated_at=row['updated_at']
        )

    def _entity_to_dict(self, entity: PreferenceItem) -> Dict[str, Any]:
        """
        Convert PreferenceItem entity to database row dict.

        Args:
            entity: PreferenceItem entity

        Returns:
            Dictionary of column values
        """
        # Convert UUID list to string list for JSONB
        evidence_ids_str = [str(uuid) for uuid in entity.evidence_conversation_ids]

        return {
            'id': entity.id,
            'category': entity.category.value,
            'preference_key': entity.preference_key,
            'preference_value': entity.preference_value,  # JSONB handles any type
            'confidence': entity.confidence,
            'evidence_count': entity.evidence_count,
            'evidence_conversation_ids': evidence_ids_str,
            'created_at': entity.created_at,
            'updated_at': entity.updated_at
        }

    # ========================================================================
    # OVERRIDE CREATE AND UPDATE
    # ========================================================================

    async def create(self, entity: PreferenceItem) -> PreferenceItem:
        """
        Create new preference.

        Args:
            entity: PreferenceItem entity

        Returns:
            Created entity with ID assigned
        """
        data = self._entity_to_dict(entity)

        query = f"""
            INSERT INTO {self.table_name} (
                id, category, preference_key, preference_value,
                confidence, evidence_count, evidence_conversation_ids,
                created_at, updated_at
            ) VALUES (
                $1, $2, $3, $4, $5, $6, $7, $8, $9
            )
            RETURNING *
        """

        async with self.db.acquire() as conn:
            row = await conn.fetchrow(
                query,
                data['id'], data['category'], data['preference_key'],
                json.dumps(data['preference_value']), data['confidence'],
                data['evidence_count'],
                json.dumps(data['evidence_conversation_ids']),
                data['created_at'], data['updated_at']
            )

        return self._row_to_entity(row)

    async def update(self, id: UUID, entity: PreferenceItem) -> PreferenceItem:
        """
        Update existing preference.

        Args:
            id: Preference UUID
            entity: Updated preference data

        Returns:
            Updated entity

        Raises:
            EntityNotFoundError: If preference not found
        """
        data = self._entity_to_dict(entity)

        query = f"""
            UPDATE {self.table_name}
            SET category = $2,
                preference_key = $3,
                preference_value = $4,
                confidence = $5,
                evidence_count = $6,
                evidence_conversation_ids = $7,
                updated_at = $8
            WHERE id = $1
            RETURNING *
        """

        async with self.db.acquire() as conn:
            row = await conn.fetchrow(
                query,
                id, data['category'], data['preference_key'],
                json.dumps(data['preference_value']), data['confidence'],
                data['evidence_count'],
                json.dumps(data['evidence_conversation_ids']),
                data['updated_at']
            )

        if not row:
            raise EntityNotFoundError(f"PreferenceItem with id {id} not found")

        return self._row_to_entity(row)

    # ========================================================================
    # QUERY METHODS (Interface Implementation)
    # ========================================================================

    async def find_by_category(
        self,
        category: str,
        min_confidence: float = 0.0,
        limit: int = 50
    ) -> List[PreferenceItem]:
        """Find preferences by category."""
        query = f"""
            SELECT * FROM {self.table_name}
            WHERE category = $1
              AND confidence >= $2
            ORDER BY confidence DESC, evidence_count DESC
            LIMIT $3
        """

        async with self.db.acquire() as conn:
            rows = await conn.fetch(query, category, min_confidence, limit)

        return [self._row_to_entity(row) for row in rows]

    async def find_by_key(
        self,
        preference_key: str,
        category: Optional[str] = None
    ) -> Optional[PreferenceItem]:
        """Find preference by key."""
        if category:
            query = f"""
                SELECT * FROM {self.table_name}
                WHERE preference_key = $1
                  AND category = $2
                LIMIT 1
            """
            params = [preference_key, category]
        else:
            query = f"""
                SELECT * FROM {self.table_name}
                WHERE preference_key = $1
                LIMIT 1
            """
            params = [preference_key]

        async with self.db.acquire() as conn:
            row = await conn.fetchrow(query, *params)

        if row:
            return self._row_to_entity(row)
        return None

    async def get_strong_preferences(
        self,
        min_confidence: float = 0.8,
        min_evidence: int = 3,
        category: Optional[str] = None,
        limit: int = 50
    ) -> List[PreferenceItem]:
        """Get strong, reliable preferences."""
        if category:
            query = f"""
                SELECT * FROM {self.table_name}
                WHERE confidence >= $1
                  AND evidence_count >= $2
                  AND category = $3
                ORDER BY confidence DESC, evidence_count DESC
                LIMIT $4
            """
            params = [min_confidence, min_evidence, category, limit]
        else:
            query = f"""
                SELECT * FROM {self.table_name}
                WHERE confidence >= $1
                  AND evidence_count >= $2
                ORDER BY confidence DESC, evidence_count DESC
                LIMIT $3
            """
            params = [min_confidence, min_evidence, limit]

        async with self.db.acquire() as conn:
            rows = await conn.fetch(query, *params)

        return [self._row_to_entity(row) for row in rows]

    async def update_confidence(
        self,
        preference_id: UUID,
        new_confidence: float
    ) -> None:
        """Update preference confidence score."""
        if not 0.0 <= new_confidence <= 1.0:
            raise ValueError(f"Confidence must be between 0.0 and 1.0, got {new_confidence}")

        query = f"""
            UPDATE {self.table_name}
            SET confidence = $2,
                updated_at = $3
            WHERE id = $1
            RETURNING id
        """

        async with self.db.acquire() as conn:
            row = await conn.fetchrow(query, preference_id, new_confidence, datetime.now())

        if not row:
            raise EntityNotFoundError(f"PreferenceItem with id {preference_id} not found")

    async def add_evidence(
        self,
        preference_id: UUID,
        conversation_id: UUID
    ) -> None:
        """
        Add evidence supporting a preference.

        Calls the add_evidence() method logic via database update.
        """
        # Get current preference
        preference = await self.get_by_id(preference_id)
        if not preference:
            raise EntityNotFoundError(f"PreferenceItem with id {preference_id} not found")

        # Update using entity method
        preference.add_evidence(conversation_id)

        # Save back to database
        await self.update(preference_id, preference)

    async def count_by_category(self, category: str) -> int:
        """Count preferences by category."""
        query = f"""
            SELECT COUNT(*) FROM {self.table_name}
            WHERE category = $1
        """

        async with self.db.acquire() as conn:
            result = await conn.fetchval(query, category)

        return result or 0

    async def get_all_preferences_summary(self) -> Dict[str, Any]:
        """Get summary of all preferences."""
        query = f"SELECT * FROM {self.table_name}"

        async with self.db.acquire() as conn:
            rows = await conn.fetch(query)

        preferences = [self._row_to_entity(row) for row in rows]

        # Calculate summary statistics
        total = len(preferences)
        if total == 0:
            return {
                "total_preferences": 0,
                "by_category": {},
                "strong_preferences": 0,
                "average_confidence": 0.0,
                "average_evidence": 0.0
            }

        # Count by category
        by_category = {}
        for pref in preferences:
            cat = pref.category.value
            by_category[cat] = by_category.get(cat, 0) + 1

        # Calculate averages
        strong_count = sum(1 for p in preferences if p.is_strong_preference())
        avg_confidence = sum(p.confidence for p in preferences) / total
        avg_evidence = sum(p.evidence_count for p in preferences) / total

        return {
            "total_preferences": total,
            "by_category": by_category,
            "strong_preferences": strong_count,
            "average_confidence": round(avg_confidence, 3),
            "average_evidence": round(avg_evidence, 1)
        }

    # ========================================================================
    # BASE REPOSITORY OVERRIDES
    # ========================================================================

    async def delete(self, id: UUID) -> bool:
        """Delete preference by ID."""
        query = f"DELETE FROM {self.table_name} WHERE id = $1 RETURNING id"

        async with self.db.acquire() as conn:
            row = await conn.fetchrow(query, id)

        return row is not None

    async def exists(self, id: UUID) -> bool:
        """Check if preference exists."""
        query = f"SELECT EXISTS(SELECT 1 FROM {self.table_name} WHERE id = $1)"

        async with self.db.acquire() as conn:
            result = await conn.fetchval(query, id)

        return result

    async def count(self, filters: Optional[Dict[str, Any]] = None) -> int:
        """Count preferences matching filters."""
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
