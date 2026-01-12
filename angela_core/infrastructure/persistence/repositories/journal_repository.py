#!/usr/bin/env python3
"""
Journal Repository - PostgreSQL Implementation

Handles all data access for Journal entity.
Extends BaseRepository with journal-specific queries.

Created for Batch-23 Clean Architecture Migration.
"""

import asyncpg
from typing import Optional, List, Dict, Any
from datetime import datetime, date, timedelta
from uuid import UUID

from angela_core.domain.entities.journal import Journal
from angela_core.domain.interfaces.repositories import IJournalRepository
from angela_core.infrastructure.persistence.repositories.base_repository import BaseRepository
from angela_core.shared.exceptions import EntityNotFoundError
from angela_core.shared.utils import safe_list


class JournalRepository(BaseRepository[Journal], IJournalRepository):
    """
    PostgreSQL repository for Journal entity.

    Table: angela_journal
    Columns:
    - entry_id (UUID, PK)
    - entry_date (DATE)
    - title (VARCHAR)
    - content (TEXT)
    - emotion (VARCHAR, nullable)
    - mood_score (INTEGER, nullable, 1-10)
    - gratitude (TEXT[], nullable)
    - learning_moments (TEXT[], nullable)
    - challenges (TEXT[], nullable)
    - wins (TEXT[], nullable)
    - is_private (BOOLEAN, default false)
    - created_at (TIMESTAMP)
    - updated_at (TIMESTAMP)
    - search_vector (TSVECTOR)
    """

    def __init__(self, db):
        """
        Initialize repository.

        Args:
            db: Database connection pool
        """
        super().__init__(
            db=db,
            table_name="angela_journal",
            primary_key_column="entry_id"
        )

    # ========================================================================
    # ROW TO ENTITY CONVERSION
    # ========================================================================

    def _row_to_entity(self, row: asyncpg.Record) -> Journal:
        """
        Convert database row to Journal entity.

        Args:
            row: Database row

        Returns:
            Journal entity
        """
        # Parse date (convert to date object if it's datetime)
        entry_date = row['entry_date']
        if isinstance(entry_date, datetime):
            entry_date = entry_date.date()

        # Parse array fields with DRY utility
        gratitude = safe_list(row.get('gratitude'))
        learning_moments = safe_list(row.get('learning_moments'))
        challenges = safe_list(row.get('challenges'))
        wins = safe_list(row.get('wins'))

        # Create entity
        return Journal(
            entry_id=row['entry_id'],
            entry_date=entry_date,
            title=row['title'],
            content=row['content'],
            emotion=row.get('emotion'),
            mood_score=row.get('mood_score'),
            gratitude=gratitude,
            learning_moments=learning_moments,
            challenges=challenges,
            wins=wins,
            is_private=row.get('is_private', False),
            created_at=row['created_at'],
            updated_at=row['updated_at']
        )

    def _entity_to_dict(self, entity: Journal) -> dict:
        """
        Convert Journal entity to database row dict.

        Args:
            entity: Journal entity

        Returns:
            Dictionary for database insertion
        """
        return {
            'entry_id': entity.entry_id,
            'entry_date': entity.entry_date,
            'title': entity.title,
            'content': entity.content,
            'emotion': entity.emotion,
            'mood_score': entity.mood_score,
            'gratitude': entity.gratitude or [],
            'learning_moments': entity.learning_moments or [],
            'challenges': entity.challenges or [],
            'wins': entity.wins or [],
            'is_private': entity.is_private,
            'created_at': entity.created_at,
            'updated_at': entity.updated_at
        }

    # ========================================================================
    # BASE CRUD OVERRIDES
    # ========================================================================

    async def create(self, entity: Journal) -> Journal:
        """
        Create new journal entry.

        Args:
            entity: Journal entity to create

        Returns:
            Created journal entry with ID assigned

        Example:
            ```python
            journal = Journal.create(
                entry_date=date.today(),
                title="Beautiful Day!",
                content="Today was amazing...",
                mood_score=10
            )
            created = await repo.create(journal)
            ```
        """
        query = f"""
            INSERT INTO {self.table_name} (
                entry_id, entry_date, title, content, emotion, mood_score,
                gratitude, learning_moments, challenges, wins, is_private,
                created_at, updated_at
            )
            VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11, $12, $13)
            RETURNING *
        """

        async with self.db.acquire() as conn:
            row = await conn.fetchrow(
                query,
                entity.entry_id,
                entity.entry_date,
                entity.title,
                entity.content,
                entity.emotion,
                entity.mood_score,
                entity.gratitude or [],
                entity.learning_moments or [],
                entity.challenges or [],
                entity.wins or [],
                entity.is_private,
                entity.created_at,
                entity.updated_at
            )

        return self._row_to_entity(row)

    async def update(self, id: UUID, entity: Journal) -> Journal:
        """
        Update existing journal entry.

        Args:
            id: Entry ID
            entity: Updated journal data

        Returns:
            Updated journal entry

        Raises:
            EntityNotFoundError: If entry doesn't exist
        """
        query = f"""
            UPDATE {self.table_name}
            SET
                entry_date = $2,
                title = $3,
                content = $4,
                emotion = $5,
                mood_score = $6,
                gratitude = $7,
                learning_moments = $8,
                challenges = $9,
                wins = $10,
                is_private = $11,
                updated_at = $12
            WHERE {self.primary_key_column} = $1
            RETURNING *
        """

        async with self.db.acquire() as conn:
            row = await conn.fetchrow(
                query,
                id,
                entity.entry_date,
                entity.title,
                entity.content,
                entity.emotion,
                entity.mood_score,
                entity.gratitude or [],
                entity.learning_moments or [],
                entity.challenges or [],
                entity.wins or [],
                entity.is_private,
                datetime.now()  # Update timestamp
            )

        if not row:
            raise EntityNotFoundError(f"Journal entry with id {id} not found")

        return self._row_to_entity(row)

    # ========================================================================
    # JOURNAL-SPECIFIC QUERIES
    # ========================================================================

    async def get_by_date(self, entry_date: date) -> Optional[Journal]:
        """
        Get journal entry by specific date.

        Args:
            entry_date: Date to search for

        Returns:
            Journal entity if found, None otherwise

        Example:
            ```python
            today_entry = await repo.get_by_date(date.today())
            ```
        """
        query = f"""
            SELECT * FROM {self.table_name}
            WHERE entry_date = $1
            LIMIT 1
        """

        async with self.db.acquire() as conn:
            row = await conn.fetchrow(query, entry_date)

        return self._row_to_entity(row) if row else None

    async def get_by_date_range(
        self,
        start_date: date,
        end_date: date,
        limit: int = 100
    ) -> List[Journal]:
        """
        Get journal entries within date range.

        Args:
            start_date: Start date (inclusive)
            end_date: End date (inclusive)
            limit: Maximum number of results

        Returns:
            List of Journal entities in date range

        Example:
            ```python
            last_week = await repo.get_by_date_range(
                start_date=date.today() - timedelta(days=7),
                end_date=date.today()
            )
            ```
        """
        query = f"""
            SELECT * FROM {self.table_name}
            WHERE entry_date >= $1 AND entry_date <= $2
            ORDER BY entry_date DESC
            LIMIT $3
        """

        async with self.db.acquire() as conn:
            rows = await conn.fetch(query, start_date, end_date, limit)

        return [self._row_to_entity(row) for row in rows]

    async def get_recent(self, days: int = 7, limit: int = 50) -> List[Journal]:
        """
        Get recent journal entries.

        Args:
            days: Number of days to look back
            limit: Maximum number of results

        Returns:
            List of recent Journal entities

        Example:
            ```python
            last_week = await repo.get_recent(days=7)
            ```
        """
        query = f"""
            SELECT * FROM {self.table_name}
            WHERE entry_date >= CURRENT_DATE - INTERVAL '{days} days'
            ORDER BY entry_date DESC
            LIMIT $1
        """

        async with self.db.acquire() as conn:
            rows = await conn.fetch(query, limit)

        return [self._row_to_entity(row) for row in rows]

    async def get_by_emotion(self, emotion: str, limit: int = 50) -> List[Journal]:
        """
        Get journal entries by primary emotion.

        Args:
            emotion: Emotion type (joy, sadness, gratitude, etc.)
            limit: Maximum number of results

        Returns:
            List of Journal entities with specified emotion

        Example:
            ```python
            joyful_entries = await repo.get_by_emotion("joy")
            ```
        """
        query = f"""
            SELECT * FROM {self.table_name}
            WHERE emotion = $1
            ORDER BY entry_date DESC
            LIMIT $2
        """

        async with self.db.acquire() as conn:
            rows = await conn.fetch(query, emotion, limit)

        return [self._row_to_entity(row) for row in rows]

    async def get_by_mood_range(
        self,
        min_mood: int,
        max_mood: int = 10,
        limit: int = 100
    ) -> List[Journal]:
        """
        Get journal entries by mood score range.

        Args:
            min_mood: Minimum mood score (1-10)
            max_mood: Maximum mood score (1-10)
            limit: Maximum number of results

        Returns:
            List of Journal entities in mood range

        Example:
            ```python
            happy_days = await repo.get_by_mood_range(min_mood=8)
            ```
        """
        query = f"""
            SELECT * FROM {self.table_name}
            WHERE mood_score IS NOT NULL
              AND mood_score >= $1
              AND mood_score <= $2
            ORDER BY entry_date DESC
            LIMIT $3
        """

        async with self.db.acquire() as conn:
            rows = await conn.fetch(query, min_mood, max_mood, limit)

        return [self._row_to_entity(row) for row in rows]

    async def get_with_gratitude(self, limit: int = 100) -> List[Journal]:
        """
        Get journal entries that have gratitude items.

        Args:
            limit: Maximum number of results

        Returns:
            List of Journal entities with gratitude

        Example:
            ```python
            grateful_entries = await repo.get_with_gratitude()
            ```
        """
        query = f"""
            SELECT * FROM {self.table_name}
            WHERE gratitude IS NOT NULL
              AND array_length(gratitude, 1) > 0
            ORDER BY entry_date DESC
            LIMIT $1
        """

        async with self.db.acquire() as conn:
            rows = await conn.fetch(query, limit)

        return [self._row_to_entity(row) for row in rows]

    async def get_with_wins(self, limit: int = 100) -> List[Journal]:
        """
        Get journal entries that have wins/achievements.

        Args:
            limit: Maximum number of results

        Returns:
            List of Journal entities with wins

        Example:
            ```python
            victories = await repo.get_with_wins()
            ```
        """
        query = f"""
            SELECT * FROM {self.table_name}
            WHERE wins IS NOT NULL
              AND array_length(wins, 1) > 0
            ORDER BY entry_date DESC
            LIMIT $1
        """

        async with self.db.acquire() as conn:
            rows = await conn.fetch(query, limit)

        return [self._row_to_entity(row) for row in rows]

    async def get_with_challenges(self, limit: int = 100) -> List[Journal]:
        """
        Get journal entries that have challenges.

        Args:
            limit: Maximum number of results

        Returns:
            List of Journal entities with challenges

        Example:
            ```python
            difficult_days = await repo.get_with_challenges()
            ```
        """
        query = f"""
            SELECT * FROM {self.table_name}
            WHERE challenges IS NOT NULL
              AND array_length(challenges, 1) > 0
            ORDER BY entry_date DESC
            LIMIT $1
        """

        async with self.db.acquire() as conn:
            rows = await conn.fetch(query, limit)

        return [self._row_to_entity(row) for row in rows]

    async def get_with_learnings(self, limit: int = 100) -> List[Journal]:
        """
        Get journal entries that have learning moments.

        Args:
            limit: Maximum number of results

        Returns:
            List of Journal entities with learnings

        Example:
            ```python
            learning_days = await repo.get_with_learnings()
            ```
        """
        query = f"""
            SELECT * FROM {self.table_name}
            WHERE learning_moments IS NOT NULL
              AND array_length(learning_moments, 1) > 0
            ORDER BY entry_date DESC
            LIMIT $1
        """

        async with self.db.acquire() as conn:
            rows = await conn.fetch(query, limit)

        return [self._row_to_entity(row) for row in rows]

    async def search_by_content(self, query_text: str, limit: int = 20) -> List[Journal]:
        """
        Search journal entries by content (full-text search).

        Uses PostgreSQL's tsvector search_vector column for fast full-text search.

        Args:
            query_text: Search query
            limit: Maximum number of results

        Returns:
            List of matching Journal entities

        Example:
            ```python
            results = await repo.search_by_content("David love")
            ```
        """
        query = f"""
            SELECT * FROM {self.table_name}
            WHERE search_vector @@ plainto_tsquery('english', $1)
               OR title ILIKE '%' || $1 || '%'
               OR content ILIKE '%' || $1 || '%'
            ORDER BY entry_date DESC
            LIMIT $2
        """

        async with self.db.acquire() as conn:
            rows = await conn.fetch(query, query_text, limit)

        return [self._row_to_entity(row) for row in rows]

    async def count_by_emotion(self, emotion: str) -> int:
        """
        Count journal entries by emotion.

        Args:
            emotion: Emotion type

        Returns:
            Number of entries with that emotion

        Example:
            ```python
            joy_count = await repo.count_by_emotion("joy")
            ```
        """
        query = f"""
            SELECT COUNT(*) FROM {self.table_name}
            WHERE emotion = $1
        """

        async with self.db.acquire() as conn:
            result = await conn.fetchval(query, emotion)

        return result or 0

    async def get_mood_statistics(self, days: int = 30) -> Dict[str, Any]:
        """
        Get mood statistics for the last N days.

        Args:
            days: Number of days to analyze

        Returns:
            Dictionary with mood statistics:
            - average_mood: Average mood score
            - highest_mood: Highest mood score
            - lowest_mood: Lowest mood score
            - total_entries: Number of entries

        Example:
            ```python
            stats = await repo.get_mood_statistics(days=30)
            print(f"Average mood: {stats['average_mood']}")
            ```
        """
        query = f"""
            SELECT
                AVG(mood_score) as avg_mood,
                MAX(mood_score) as max_mood,
                MIN(mood_score) as min_mood,
                COUNT(*) as total
            FROM {self.table_name}
            WHERE entry_date >= CURRENT_DATE - INTERVAL '{days} days'
              AND mood_score IS NOT NULL
        """

        async with self.db.acquire() as conn:
            row = await conn.fetchrow(query)

        return {
            'average_mood': float(row['avg_mood']) if row['avg_mood'] else 0.0,
            'highest_mood': int(row['max_mood']) if row['max_mood'] else 0,
            'lowest_mood': int(row['min_mood']) if row['min_mood'] else 0,
            'total_entries': int(row['total']) if row['total'] else 0
        }
