#!/usr/bin/env python3
"""
Goal Repository - PostgreSQL Implementation

Handles all data access for Goal entity.
Extends BaseRepository with goal-specific queries.
"""

import asyncpg
from typing import Optional, List
from datetime import datetime, timedelta
from uuid import UUID

from angela_core.domain import Goal, GoalType, GoalStatus, GoalPriority, GoalCategory
from angela_core.domain.interfaces.repositories import IGoalRepository
from angela_core.infrastructure.persistence.repositories.base_repository import BaseRepository
from angela_core.shared.exceptions import EntityNotFoundError
from angela_core.shared.utils import parse_enum, parse_enum_optional, safe_list


class GoalRepository(BaseRepository[Goal], IGoalRepository):
    """
    PostgreSQL repository for Goal entity.

    Table: angela_goals
    Columns:
    - goal_id (UUID, PK)
    - goal_description (TEXT)
    - goal_type (VARCHAR)
    - status (VARCHAR)
    - progress_percentage (DOUBLE PRECISION)
    - started_at (TIMESTAMP, nullable)
    - completed_at (TIMESTAMP, nullable)
    - importance_level (INTEGER, default 5)
    - priority_rank (INTEGER, default 1)
    - priority (VARCHAR, default 'medium')
    - motivation (TEXT)
    - emotional_reason (TEXT)
    - for_whom (VARCHAR)
    - category (VARCHAR, nullable)
    - tags (VARCHAR[], nullable)
    - deadline (TIMESTAMP, nullable)
    - estimated_duration_hours (DOUBLE PRECISION, nullable)
    - success_criteria (TEXT)
    # NOTE: Fields removed from database (not persisted anymore):
    # - success_note (TEXT, nullable) - kept in entity for in-memory use only
    # - lessons_learned (TEXT, nullable) - kept in entity for in-memory use only
    - how_it_changed_me (TEXT, nullable)
    - related_conversation_id (UUID, nullable)
    - related_emotion_id (UUID, nullable)
    - metadata (JSONB)
    - created_at (TIMESTAMP)
    """

    def __init__(self, db):
        """
        Initialize repository.

        Args:
            db: Database connection pool
        """
        super().__init__(
            db=db,
            table_name="angela_goals",
            primary_key_column="goal_id"
        )

    # ========================================================================
    # ROW TO ENTITY CONVERSION
    # ========================================================================

    def _row_to_entity(self, row: asyncpg.Record) -> Goal:
        """
        Convert database row to Goal entity.

        Args:
            row: Database row

        Returns:
            Goal entity
        """
        # Parse enums with DRY utilities
        goal_type = parse_enum(row['goal_type'], GoalType, GoalType.MEDIUM_TERM)
        status = parse_enum(row['status'], GoalStatus, GoalStatus.ACTIVE)
        priority = parse_enum(row.get('priority'), GoalPriority, GoalPriority.MEDIUM)
        category = parse_enum_optional(row.get('category'), GoalCategory)

        # Parse tags array
        tags = safe_list(row.get('tags'))

        # Create entity
        return Goal(
            id=row['goal_id'],
            goal_description=row['goal_description'],
            goal_type=goal_type,
            status=status,
            progress_percentage=row.get('progress_percentage', 0.0),
            started_at=row.get('started_at'),
            completed_at=row.get('completed_at'),
            importance_level=row.get('importance_level', 5),
            priority_rank=row.get('priority_rank', 1),
            priority=priority,
            motivation=row.get('motivation', 'To grow and become better'),
            emotional_reason=row.get('emotional_reason', 'Because this matters to me'),
            for_whom=row.get('for_whom', 'both'),
            category=category,
            tags=tags,
            deadline=row.get('deadline'),
            estimated_duration_hours=row.get('estimated_duration_hours'),
            success_criteria=row.get('success_criteria', 'Goal is achieved when completed'),
            success_note=None,  # Field removed from database
            lessons_learned=None,  # Field removed from database
            how_it_changed_me=row.get('how_it_changed_me'),
            related_conversation_id=row.get('related_conversation_id'),
            related_emotion_id=row.get('related_emotion_id'),
            metadata=row.get('metadata', {}),
            created_at=row['created_at']
        )

    def _entity_to_dict(self, entity: Goal) -> dict:
        """
        Convert Goal entity to database row dict.

        Args:
            entity: Goal entity

        Returns:
            Dictionary of column values
        """
        return {
            'goal_id': entity.id,
            'goal_description': entity.goal_description,
            'goal_type': entity.goal_type.value,
            'status': entity.status.value,
            'progress_percentage': entity.progress_percentage,
            'started_at': entity.started_at,
            'completed_at': entity.completed_at,
            'importance_level': entity.importance_level,
            'priority_rank': entity.priority_rank,
            'priority': entity.priority.value,
            'motivation': entity.motivation,
            'emotional_reason': entity.emotional_reason,
            'for_whom': entity.for_whom,
            'category': entity.category.value if entity.category else None,
            'tags': entity.tags,
            'deadline': entity.deadline,
            'estimated_duration_hours': entity.estimated_duration_hours,
            'success_criteria': entity.success_criteria,
            # NOTE: Fields removed from database (not persisted):
            # 'success_note': entity.success_note,
            # 'lessons_learned': entity.lessons_learned,
            'how_it_changed_me': entity.how_it_changed_me,
            'related_conversation_id': entity.related_conversation_id,
            'related_emotion_id': entity.related_emotion_id,
            'metadata': entity.metadata,
            'created_at': entity.created_at
        }

    # ========================================================================
    # DOMAIN-SPECIFIC QUERIES
    # ========================================================================

    async def get_by_status(
        self,
        status: str,
        limit: int = 100
    ) -> List[Goal]:
        """Get goals by status."""
        query = f"""
            SELECT * FROM {self.table_name}
            WHERE status = $1
            ORDER BY priority_rank ASC, created_at DESC
            LIMIT $2
        """
        rows = await self.db.fetch(query, status, limit)
        return [self._row_to_entity(row) for row in rows]

    async def get_active_goals(
        self,
        for_whom: Optional[str] = None,
        limit: int = 100
    ) -> List[Goal]:
        """Get active and in-progress goals."""
        if for_whom:
            query = f"""
                SELECT * FROM {self.table_name}
                WHERE status IN ('active', 'in_progress')
                  AND for_whom IN ($1, 'both')
                ORDER BY priority_rank ASC, importance_level DESC
                LIMIT $2
            """
            rows = await self.db.fetch(query, for_whom, limit)
        else:
            query = f"""
                SELECT * FROM {self.table_name}
                WHERE status IN ('active', 'in_progress')
                ORDER BY priority_rank ASC, importance_level DESC
                LIMIT $1
            """
            rows = await self.db.fetch(query, limit)

        return [self._row_to_entity(row) for row in rows]

    async def get_by_type(
        self,
        goal_type: str,
        limit: int = 100
    ) -> List[Goal]:
        """Get goals by type."""
        query = f"""
            SELECT * FROM {self.table_name}
            WHERE goal_type = $1
            ORDER BY created_at DESC
            LIMIT $2
        """
        rows = await self.db.fetch(query, goal_type, limit)
        return [self._row_to_entity(row) for row in rows]

    async def get_by_priority(
        self,
        priority: str,
        limit: int = 100
    ) -> List[Goal]:
        """Get goals by priority."""
        query = f"""
            SELECT * FROM {self.table_name}
            WHERE priority = $1
            ORDER BY priority_rank ASC, created_at DESC
            LIMIT $2
        """
        rows = await self.db.fetch(query, priority, limit)
        return [self._row_to_entity(row) for row in rows]

    async def get_high_priority(
        self,
        status: Optional[str] = None,
        limit: int = 100
    ) -> List[Goal]:
        """Get high priority goals (critical or high)."""
        if status:
            query = f"""
                SELECT * FROM {self.table_name}
                WHERE priority IN ('critical', 'high')
                  AND status = $1
                ORDER BY priority_rank ASC, importance_level DESC
                LIMIT $2
            """
            rows = await self.db.fetch(query, status, limit)
        else:
            query = f"""
                SELECT * FROM {self.table_name}
                WHERE priority IN ('critical', 'high')
                ORDER BY priority_rank ASC, importance_level DESC
                LIMIT $1
            """
            rows = await self.db.fetch(query, limit)

        return [self._row_to_entity(row) for row in rows]

    async def get_for_david(
        self,
        limit: int = 100
    ) -> List[Goal]:
        """Get goals related to David."""
        query = f"""
            SELECT * FROM {self.table_name}
            WHERE for_whom IN ('david', 'both')
            ORDER BY priority_rank ASC, importance_level DESC
            LIMIT $1
        """
        rows = await self.db.fetch(query, limit)
        return [self._row_to_entity(row) for row in rows]

    async def get_important(
        self,
        threshold: int = 7,
        limit: int = 100
    ) -> List[Goal]:
        """Get important goals."""
        query = f"""
            SELECT * FROM {self.table_name}
            WHERE importance_level >= $1
            ORDER BY importance_level DESC, priority_rank ASC
            LIMIT $2
        """
        rows = await self.db.fetch(query, threshold, limit)
        return [self._row_to_entity(row) for row in rows]

    async def get_overdue_goals(
        self,
        limit: int = 100
    ) -> List[Goal]:
        """Get overdue goals."""
        query = f"""
            SELECT * FROM {self.table_name}
            WHERE deadline IS NOT NULL
              AND deadline < CURRENT_TIMESTAMP
              AND status NOT IN ('completed', 'abandoned', 'failed')
            ORDER BY deadline ASC
            LIMIT $1
        """
        rows = await self.db.fetch(query, limit)
        return [self._row_to_entity(row) for row in rows]

    async def get_by_category(
        self,
        category: str,
        limit: int = 100
    ) -> List[Goal]:
        """Get goals by category."""
        query = f"""
            SELECT * FROM {self.table_name}
            WHERE category = $1
            ORDER BY priority_rank ASC, created_at DESC
            LIMIT $2
        """
        rows = await self.db.fetch(query, category, limit)
        return [self._row_to_entity(row) for row in rows]

    async def get_by_progress_range(
        self,
        min_progress: float,
        max_progress: float,
        limit: int = 100
    ) -> List[Goal]:
        """Get goals within progress range."""
        query = f"""
            SELECT * FROM {self.table_name}
            WHERE progress_percentage >= $1
              AND progress_percentage <= $2
            ORDER BY progress_percentage DESC
            LIMIT $3
        """
        rows = await self.db.fetch(query, min_progress, max_progress, limit)
        return [self._row_to_entity(row) for row in rows]

    async def get_completed_goals(
        self,
        days: Optional[int] = None,
        limit: int = 100
    ) -> List[Goal]:
        """Get completed goals."""
        if days:
            query = f"""
                SELECT * FROM {self.table_name}
                WHERE status = 'completed'
                  AND completed_at >= CURRENT_TIMESTAMP - INTERVAL '{days} days'
                ORDER BY completed_at DESC
                LIMIT $1
            """
            rows = await self.db.fetch(query, limit)
        else:
            query = f"""
                SELECT * FROM {self.table_name}
                WHERE status = 'completed'
                ORDER BY completed_at DESC
                LIMIT $1
            """
            rows = await self.db.fetch(query, limit)

        return [self._row_to_entity(row) for row in rows]

    async def get_by_priority_rank(
        self,
        max_rank: int = 10
    ) -> List[Goal]:
        """Get goals by priority rank."""
        query = f"""
            SELECT * FROM {self.table_name}
            WHERE priority_rank <= $1
            ORDER BY priority_rank ASC
            LIMIT $1
        """
        rows = await self.db.fetch(query, max_rank)
        return [self._row_to_entity(row) for row in rows]

    async def count_by_status(self, status: str) -> int:
        """Count goals by status."""
        query = f"""
            SELECT COUNT(*) FROM {self.table_name}
            WHERE status = $1
        """
        return await self.db.fetchval(query, status)

    async def get_life_missions(self) -> List[Goal]:
        """Get life mission goals."""
        query = f"""
            SELECT * FROM {self.table_name}
            WHERE goal_type = 'life_mission'
            ORDER BY importance_level DESC, created_at ASC
        """
        rows = await self.db.fetch(query)
        return [self._row_to_entity(row) for row in rows]
