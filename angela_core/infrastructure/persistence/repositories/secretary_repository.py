#!/usr/bin/env python3
"""
Secretary Repository - PostgreSQL Implementation

Handles all data access for Task and Note entities.
Manages Angela's secretary functions: tasks, reminders, and notes.
"""

import asyncpg
from typing import Optional, List, Dict, Any
from datetime import datetime, timedelta
from uuid import UUID

from angela_core.domain import Task, Note, TaskType, TaskPriority, NoteCategory, SyncStatus
from angela_core.domain.interfaces.repositories import ISecretaryRepository
from angela_core.infrastructure.persistence.repositories.base_repository import BaseRepository


class SecretaryRepository(BaseRepository[Task], ISecretaryRepository):
    """
    PostgreSQL repository for Task and Note entities.

    Uses secretary_reminders table for tasks/reminders.
    Note: This implementation focuses on Tasks.
    Notes could use a separate table or share the same table.
    """

    def __init__(self, db):
        super().__init__(
            db=db,
            table_name="secretary_reminders",
            primary_key_column="reminder_id"
        )

    # ========================================================================
    # ROW TO ENTITY CONVERSION
    # ========================================================================

    def _row_to_entity(self, row: asyncpg.Record) -> Task:
        """Convert database row to Task entity."""
        task_type = None
        if row.get('task_type'):
            try:
                task_type = TaskType(row['task_type'])
            except ValueError:
                task_type = None

        sync_status = SyncStatus.NOT_SYNCED
        if row.get('sync_status'):
            try:
                sync_status = SyncStatus(row['sync_status'])
            except ValueError:
                sync_status = SyncStatus.NOT_SYNCED

        return Task(
            id=row['reminder_id'],
            title=row['title'],
            notes=row.get('notes'),
            priority=row.get('priority', 0),
            importance_level=row.get('importance_level', 5),
            due_date=row.get('due_date'),
            completion_date=row.get('completion_date'),
            is_completed=row.get('is_completed', False),
            task_type=task_type,
            context_tags=list(row['context_tags']) if row.get('context_tags') else [],
            is_recurring=row.get('is_recurring', False),
            recurrence_rule=row.get('recurrence_rule'),
            conversation_id=row.get('conversation_id'),
            david_words=row.get('david_words'),
            angela_interpretation=row.get('angela_interpretation'),
            confidence_score=row.get('confidence_score', 0.5),
            auto_created=row.get('auto_created', False),
            eventkit_identifier=row.get('eventkit_identifier'),
            eventkit_calendar_identifier=row.get('eventkit_calendar_identifier'),
            sync_status=sync_status,
            sync_error=row.get('sync_error'),
            last_synced_at=row.get('last_synced_at'),
            created_at=row['created_at'],
            updated_at=row.get('updated_at', row['created_at'])
        )

    def _entity_to_dict(self, entity: Task) -> dict:
        """Convert Task entity to database row dict."""
        return {
            'reminder_id': entity.id,
            'title': entity.title,
            'notes': entity.notes,
            'priority': entity.priority,
            'importance_level': entity.importance_level,
            'due_date': entity.due_date,
            'completion_date': entity.completion_date,
            'is_completed': entity.is_completed,
            'task_type': entity.task_type.value if entity.task_type else None,
            'context_tags': entity.context_tags,
            'is_recurring': entity.is_recurring,
            'recurrence_rule': entity.recurrence_rule,
            'conversation_id': entity.conversation_id,
            'david_words': entity.david_words,
            'angela_interpretation': entity.angela_interpretation,
            'confidence_score': entity.confidence_score,
            'auto_created': entity.auto_created,
            'eventkit_identifier': entity.eventkit_identifier,
            'eventkit_calendar_identifier': entity.eventkit_calendar_identifier,
            'sync_status': entity.sync_status.value,
            'sync_error': entity.sync_error,
            'last_synced_at': entity.last_synced_at,
            'created_at': entity.created_at,
            'updated_at': entity.updated_at
        }

    # ========================================================================
    # TASK METHODS
    # ========================================================================

    async def get_pending_tasks(self, limit: int = 100) -> List[Task]:
        """Get tasks that are not completed."""
        query = f"""
            SELECT * FROM {self.table_name}
            WHERE is_completed = false
            ORDER BY priority DESC, due_date ASC NULLS LAST
            LIMIT $1
        """
        async with self.db.acquire() as conn:
            rows = await conn.fetch(query, limit)
        return [self._row_to_entity(row) for row in rows]

    async def get_completed_tasks(self, limit: int = 100) -> List[Task]:
        """Get tasks that are completed."""
        query = f"""
            SELECT * FROM {self.table_name}
            WHERE is_completed = true
            ORDER BY completion_date DESC
            LIMIT $1
        """
        async with self.db.acquire() as conn:
            rows = await conn.fetch(query, limit)
        return [self._row_to_entity(row) for row in rows]

    async def get_overdue_tasks(self, limit: int = 100) -> List[Task]:
        """Get tasks that are overdue."""
        query = f"""
            SELECT * FROM {self.table_name}
            WHERE is_completed = false
              AND due_date IS NOT NULL
              AND due_date < $1
            ORDER BY due_date ASC
            LIMIT $2
        """
        async with self.db.acquire() as conn:
            rows = await conn.fetch(query, datetime.now(), limit)
        return [self._row_to_entity(row) for row in rows]

    async def get_tasks_due_soon(self, hours: int = 24, limit: int = 100) -> List[Task]:
        """Get tasks due within N hours."""
        threshold = datetime.now() + timedelta(hours=hours)
        query = f"""
            SELECT * FROM {self.table_name}
            WHERE is_completed = false
              AND due_date IS NOT NULL
              AND due_date <= $1
              AND due_date >= $2
            ORDER BY due_date ASC
            LIMIT $3
        """
        async with self.db.acquire() as conn:
            rows = await conn.fetch(query, threshold, datetime.now(), limit)
        return [self._row_to_entity(row) for row in rows]

    async def get_tasks_by_priority(self, min_priority: int, limit: int = 100) -> List[Task]:
        """Get tasks with priority >= min_priority."""
        query = f"""
            SELECT * FROM {self.table_name}
            WHERE priority >= $1
              AND is_completed = false
            ORDER BY priority DESC, due_date ASC NULLS LAST
            LIMIT $2
        """
        async with self.db.acquire() as conn:
            rows = await conn.fetch(query, min_priority, limit)
        return [self._row_to_entity(row) for row in rows]

    async def get_recurring_tasks(self, limit: int = 100) -> List[Task]:
        """Get recurring tasks."""
        query = f"""
            SELECT * FROM {self.table_name}
            WHERE is_recurring = true
            ORDER BY created_at DESC
            LIMIT $1
        """
        async with self.db.acquire() as conn:
            rows = await conn.fetch(query, limit)
        return [self._row_to_entity(row) for row in rows]

    async def get_tasks_by_type(self, task_type: str, limit: int = 100) -> List[Task]:
        """Get tasks by type."""
        query = f"""
            SELECT * FROM {self.table_name}
            WHERE task_type = $1
            ORDER BY created_at DESC
            LIMIT $2
        """
        async with self.db.acquire() as conn:
            rows = await conn.fetch(query, task_type, limit)
        return [self._row_to_entity(row) for row in rows]

    # ========================================================================
    # NOTE METHODS (Placeholder - would need separate table or different approach)
    # ========================================================================

    async def get_pinned_notes(self, limit: int = 100) -> List[Note]:
        """Get pinned notes. Note: This needs separate implementation."""
        # Placeholder: Notes would need separate table or different logic
        return []

    async def get_notes_by_category(self, category: str, limit: int = 100) -> List[Note]:
        """Get notes by category. Note: This needs separate implementation."""
        return []

    async def search_notes(self, query: str, limit: int = 20) -> List[Note]:
        """Search notes by content. Note: This needs separate implementation."""
        return []

    async def get_recent_notes(self, days: int = 7, limit: int = 100) -> List[Note]:
        """Get notes from the last N days. Note: This needs separate implementation."""
        return []

    # ========================================================================
    # COMBINED/UTILITY METHODS
    # ========================================================================

    async def get_from_conversation(self, conversation_id: UUID) -> Dict[str, List[Any]]:
        """Get all tasks from a specific conversation."""
        query = f"""
            SELECT * FROM {self.table_name}
            WHERE conversation_id = $1
            ORDER BY created_at DESC
        """
        async with self.db.acquire() as conn:
            rows = await conn.fetch(query, conversation_id)

        tasks = [self._row_to_entity(row) for row in rows]
        notes = []  # Notes would need separate implementation

        return {"tasks": tasks, "notes": notes}

    async def count_pending_tasks(self) -> int:
        """Count pending tasks."""
        query = f"""
            SELECT COUNT(*) FROM {self.table_name}
            WHERE is_completed = false
        """
        async with self.db.acquire() as conn:
            count = await conn.fetchval(query)
        return count

    async def count_overdue_tasks(self) -> int:
        """Count overdue tasks."""
        query = f"""
            SELECT COUNT(*) FROM {self.table_name}
            WHERE is_completed = false
              AND due_date IS NOT NULL
              AND due_date < $1
        """
        async with self.db.acquire() as conn:
            count = await conn.fetchval(query, datetime.now())
        return count
