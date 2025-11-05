#!/usr/bin/env python3
"""
Autonomous Action Repository - PostgreSQL Implementation

Handles all data access for autonomous_actions table.
Lightweight repository for dashboard queries.

Created for Batch-22 Repository Enhancement.
"""

import asyncpg
from typing import Optional, List, Dict, Any
from datetime import datetime
from uuid import UUID


class AutonomousActionRepository:
    """
    PostgreSQL repository for autonomous_actions table.

    Table: autonomous_actions
    Columns:
    - action_id (UUID, PK)
    - action_type (VARCHAR)
    - action_description (TEXT)
    - status (VARCHAR) - 'pending', 'completed', 'failed'
    - started_at (TIMESTAMP, nullable)
    - completed_at (TIMESTAMP, nullable)
    - result_summary (TEXT, nullable)
    - success (BOOLEAN, nullable)
    - david_feedback (TEXT, nullable)
    - should_repeat (BOOLEAN, default true)
    - created_at (TIMESTAMP)
    """

    def __init__(self, db):
        """
        Initialize repository.

        Args:
            db: Database connection pool
        """
        self.db = db
        self.table_name = "autonomous_actions"

    # =========================================================================
    # Dashboard-Specific Methods
    # =========================================================================

    async def find_recent(self, limit: int = 10) -> List[Dict[str, Any]]:
        """
        Find recent autonomous actions.

        Args:
            limit: Maximum number of results (default: 10)

        Returns:
            List of action dictionaries

        Example:
            >>> actions = await repo.find_recent(limit=3)
            >>> for action in actions:
            ...     print(f"{action['action_type']}: {action['status']}")
            morning_greeting: completed
            emotion_capture: completed
        """
        query = f"""
            SELECT
                action_id,
                action_type,
                action_description,
                status,
                started_at,
                completed_at,
                result_summary,
                success,
                created_at
            FROM {self.table_name}
            ORDER BY created_at DESC
            LIMIT $1
        """

        async with self.db.acquire() as conn:
            rows = await conn.fetch(query, limit)

        return [dict(row) for row in rows]

    async def count(self) -> int:
        """
        Count total autonomous actions.

        Returns:
            Total number of actions

        Example:
            >>> total = await repo.count()
            >>> print(f"Total actions: {total}")
        """
        query = f"SELECT COUNT(*) FROM {self.table_name}"

        async with self.db.acquire() as conn:
            result = await conn.fetchval(query)

        return result or 0

    async def count_successful(self) -> int:
        """
        Count successful autonomous actions.

        Returns:
            Number of successful actions

        Example:
            >>> successful = await repo.count_successful()
            >>> print(f"Successful actions: {successful}")
        """
        query = f"""
            SELECT COUNT(*) FROM {self.table_name}
            WHERE success = true
        """

        async with self.db.acquire() as conn:
            result = await conn.fetchval(query)

        return result or 0

    async def find_by_type(
        self,
        action_type: str,
        limit: int = 10
    ) -> List[Dict[str, Any]]:
        """
        Find actions by type.

        Args:
            action_type: Type of action to find
            limit: Maximum number of results

        Returns:
            List of matching actions

        Example:
            >>> greetings = await repo.find_by_type("morning_greeting", limit=5)
        """
        query = f"""
            SELECT
                action_id,
                action_type,
                action_description,
                status,
                success,
                created_at
            FROM {self.table_name}
            WHERE action_type = $1
            ORDER BY created_at DESC
            LIMIT $2
        """

        async with self.db.acquire() as conn:
            rows = await conn.fetch(query, action_type, limit)

        return [dict(row) for row in rows]
