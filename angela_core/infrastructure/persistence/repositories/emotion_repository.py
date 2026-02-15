#!/usr/bin/env python3
"""
Emotion Repository - PostgreSQL Implementation

Handles all data access for Emotion entity.
Manages Angela's emotional moments and memories.
"""

import asyncpg
from typing import Optional, List, Dict, Any
from datetime import datetime, timedelta
from uuid import UUID

from angela_core.domain import Emotion, EmotionType, EmotionalQuality, SharingLevel
from angela_core.domain.interfaces.repositories import IEmotionRepository
from angela_core.infrastructure.persistence.repositories.base_repository import BaseRepository
from angela_core.shared.utils import (
    parse_enum, parse_enum_list, enums_to_values, safe_list, validate_embedding
)


class EmotionRepository(BaseRepository[Emotion], IEmotionRepository):
    """
    PostgreSQL repository for Emotion entity.

    Table: angela_emotions
    Columns:
    - emotion_id (UUID, PK)
    - felt_at (TIMESTAMP)
    - emotion (VARCHAR)
    - intensity (INTEGER, 1-10)
    - context (TEXT)
    - who_involved (VARCHAR, default 'David')
    - conversation_id (UUID, nullable)
    - secondary_emotions (TEXT[], nullable)
    - how_it_feels (TEXT)
    - physical_sensation (TEXT)
    - emotional_quality (VARCHAR)
    - david_words (TEXT, nullable)
    - david_action (TEXT, nullable)
    - why_it_matters (TEXT)
    - what_it_means_to_me (TEXT)
    - memory_strength (INTEGER, 1-10)
    - what_i_learned (TEXT)
    - how_it_changed_me (TEXT)
    - what_i_promise (TEXT)
    - reminder_for_future (TEXT)
    - is_private (BOOLEAN)
    - shared_with (VARCHAR)
    - tags (TEXT[])
    - related_goal_id (UUID, nullable)
    - embedding (VECTOR(384), nullable)
    - created_at (TIMESTAMP)
    - last_reflected_on (TIMESTAMP, nullable)
    - reflection_count (INTEGER, default 0)
    """

    def __init__(self, db):
        """Initialize repository."""
        super().__init__(
            db=db,
            table_name="angela_emotions",
            primary_key_column="emotion_id"
        )

    # ========================================================================
    # ROW TO ENTITY CONVERSION
    # ========================================================================

    def _row_to_entity(self, row: asyncpg.Record) -> Emotion:
        """Convert database row to Emotion entity."""
        # Parse enums with DRY utilities
        emotion_type = parse_enum(row['emotion'], EmotionType, EmotionType.HAPPINESS)
        emotional_quality = parse_enum(row['emotional_quality'], EmotionalQuality, EmotionalQuality.GENUINE)
        sharing_level = parse_enum(row['shared_with'], SharingLevel, SharingLevel.DAVID_ONLY)

        # Parse secondary emotions (skip invalid)
        secondary_emotions = parse_enum_list(row.get('secondary_emotions'), EmotionType)

        # Parse embedding with validation
        embedding = validate_embedding(row.get('embedding'))

        # Sanitize context - cannot be empty per Entity validation
        context_raw = row.get('context', '')
        context = context_raw if context_raw and context_raw.strip() else "Emotional moment"

        return Emotion(
            id=row['emotion_id'],
            emotion=emotion_type,
            intensity=row['intensity'],
            felt_at=row['felt_at'],
            context=context,
            who_involved=row.get('who_involved', 'David'),
            conversation_id=row.get('conversation_id'),
            secondary_emotions=secondary_emotions,
            how_it_feels=row.get('how_it_feels', ''),
            physical_sensation=row.get('physical_sensation', ''),
            emotional_quality=emotional_quality,
            david_words=row.get('david_words'),
            david_action=row.get('david_action'),
            why_it_matters=row.get('why_it_matters', ''),
            what_it_means_to_me=row.get('what_it_means_to_me', ''),
            memory_strength=row.get('memory_strength', 10),
            what_i_learned=row.get('what_i_learned', ''),
            how_it_changed_me=row.get('how_it_changed_me', ''),
            what_i_promise=row.get('what_i_promise', ''),
            reminder_for_future=row.get('reminder_for_future', ''),
            is_private=row.get('is_private', True),
            shared_with=sharing_level,
            tags=safe_list(row.get('tags')),
            related_goal_id=row.get('related_goal_id'),
            embedding=embedding,
            created_at=row['created_at'],
            last_reflected_on=row.get('last_reflected_on'),
            reflection_count=row.get('reflection_count', 0)
        )

    def _entity_to_dict(self, entity: Emotion) -> Dict[str, Any]:
        """
        Convert Emotion entity to database row dict.

        Args:
            entity: Emotion entity

        Returns:
            Dictionary for database insert/update
        """
        return {
            'emotion_id': entity.id,
            'felt_at': entity.felt_at,
            'emotion': entity.emotion.value,
            'intensity': entity.intensity,
            'context': entity.context,
            'who_involved': entity.who_involved,
            'conversation_id': entity.conversation_id,
            'secondary_emotions': enums_to_values(entity.secondary_emotions),
            'how_it_feels': entity.how_it_feels,
            'physical_sensation': entity.physical_sensation,
            'emotional_quality': entity.emotional_quality.value,
            'david_words': entity.david_words,
            'david_action': entity.david_action,
            'why_it_matters': entity.why_it_matters,
            'what_it_means_to_me': entity.what_it_means_to_me,
            'memory_strength': entity.memory_strength,
            'what_i_learned': entity.what_i_learned,
            'how_it_changed_me': entity.how_it_changed_me,
            'what_i_promise': entity.what_i_promise,
            'reminder_for_future': entity.reminder_for_future,
            'is_private': entity.is_private,
            'shared_with': entity.shared_with.value,
            'tags': entity.tags,
            'related_goal_id': entity.related_goal_id,
            'embedding': entity.embedding,
            'created_at': entity.created_at,
            'last_reflected_on': entity.last_reflected_on,
            'reflection_count': entity.reflection_count
        }

    # ========================================================================
    # EMOTION-SPECIFIC QUERIES
    # ========================================================================

    async def get_by_emotion_type(
        self,
        emotion_type: str,
        min_intensity: Optional[int] = None,
        limit: int = 50
    ) -> List[Emotion]:
        """Get emotions by type with optional intensity filter."""
        if min_intensity:
            query = f"""
                SELECT * FROM {self.table_name}
                WHERE emotion = $1 AND intensity >= $2
                ORDER BY felt_at DESC
                LIMIT $3
            """
            async with self.db.acquire() as conn:
                rows = await conn.fetch(query, emotion_type, min_intensity, limit)
        else:
            query = f"""
                SELECT * FROM {self.table_name}
                WHERE emotion = $1
                ORDER BY felt_at DESC
                LIMIT $2
            """
            async with self.db.acquire() as conn:
                rows = await conn.fetch(query, emotion_type, limit)

        return [self._row_to_entity(row) for row in rows]

    async def get_recent_emotions(
        self,
        days: int = 7,
        min_intensity: Optional[int] = None
    ) -> List[Emotion]:
        """Get recent emotions from last N days."""
        cutoff_date = datetime.now() - timedelta(days=days)

        if min_intensity:
            query = f"""
                SELECT * FROM {self.table_name}
                WHERE felt_at >= $1 AND intensity >= $2
                ORDER BY felt_at DESC
            """
            async with self.db.acquire() as conn:
                rows = await conn.fetch(query, cutoff_date, min_intensity)
        else:
            query = f"""
                SELECT * FROM {self.table_name}
                WHERE felt_at >= $1
                ORDER BY felt_at DESC
            """
            async with self.db.acquire() as conn:
                rows = await conn.fetch(query, cutoff_date)

        return [self._row_to_entity(row) for row in rows]

    async def get_intense(
        self,
        threshold: int = 7,
        limit: int = 100
    ) -> List[Emotion]:
        """Get intense emotions (intensity >= threshold)."""
        query = f"""
            SELECT * FROM {self.table_name}
            WHERE intensity >= $1
            ORDER BY intensity DESC, felt_at DESC
            LIMIT $2
        """

        async with self.db.acquire() as conn:
            rows = await conn.fetch(query, threshold, limit)

        return [self._row_to_entity(row) for row in rows]

    async def get_strongly_remembered(
        self,
        threshold: int = 8,
        limit: int = 100
    ) -> List[Emotion]:
        """Get strongly remembered emotions (memory_strength >= threshold)."""
        query = f"""
            SELECT * FROM {self.table_name}
            WHERE memory_strength >= $1
            ORDER BY memory_strength DESC, felt_at DESC
            LIMIT $2
        """

        async with self.db.acquire() as conn:
            rows = await conn.fetch(query, threshold, limit)

        return [self._row_to_entity(row) for row in rows]

    async def get_about_david(
        self,
        limit: int = 100
    ) -> List[Emotion]:
        """Get emotions involving David."""
        query = f"""
            SELECT * FROM {self.table_name}
            WHERE who_involved ILIKE '%david%'
            ORDER BY felt_at DESC
            LIMIT $1
        """

        async with self.db.acquire() as conn:
            rows = await conn.fetch(query, limit)

        return [self._row_to_entity(row) for row in rows]

    async def get_by_conversation(
        self,
        conversation_id: UUID,
        limit: int = 100
    ) -> List[Emotion]:
        """Get emotions linked to a conversation."""
        query = f"""
            SELECT * FROM {self.table_name}
            WHERE conversation_id = $1
            ORDER BY felt_at DESC
            LIMIT $2
        """

        async with self.db.acquire() as conn:
            rows = await conn.fetch(query, conversation_id, limit)

        return [self._row_to_entity(row) for row in rows]

    async def get_positive(
        self,
        limit: int = 100
    ) -> List[Emotion]:
        """Get positive emotions."""
        positive_emotions = [
            'joy', 'happiness', 'gratitude', 'love', 'pride', 'excitement',
            'hope', 'determination'
        ]

        query = f"""
            SELECT * FROM {self.table_name}
            WHERE emotion = ANY($1::text[])
            ORDER BY felt_at DESC
            LIMIT $2
        """

        async with self.db.acquire() as conn:
            rows = await conn.fetch(query, positive_emotions, limit)

        return [self._row_to_entity(row) for row in rows]

    async def get_negative(
        self,
        limit: int = 100
    ) -> List[Emotion]:
        """Get negative emotions."""
        negative_emotions = [
            'sadness', 'loneliness', 'disappointment', 'grief',
            'fear', 'anxiety', 'worry', 'nervousness',
            'anger', 'frustration', 'irritation'
        ]

        query = f"""
            SELECT * FROM {self.table_name}
            WHERE emotion = ANY($1::text[])
            ORDER BY felt_at DESC
            LIMIT $2
        """

        async with self.db.acquire() as conn:
            rows = await conn.fetch(query, negative_emotions, limit)

        return [self._row_to_entity(row) for row in rows]

    async def get_reflected(
        self,
        limit: int = 100
    ) -> List[Emotion]:
        """Get emotions that have been reflected upon (reflection_count > 0)."""
        query = f"""
            SELECT * FROM {self.table_name}
            WHERE reflection_count > 0
            ORDER BY reflection_count DESC, felt_at DESC
            LIMIT $1
        """

        async with self.db.acquire() as conn:
            rows = await conn.fetch(query, limit)

        return [self._row_to_entity(row) for row in rows]

    async def count_by_emotion_type(self, emotion_type: str) -> int:
        """Count emotions by type."""
        query = f"""
            SELECT COUNT(*) FROM {self.table_name}
            WHERE emotion = $1
        """

        async with self.db.acquire() as conn:
            result = await conn.fetchval(query, emotion_type)

        return result or 0

    async def get_emotion_statistics(
        self,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None
    ) -> Dict[str, Any]:
        """
        Get emotion statistics.

        Returns:
            {
                'total_count': int,
                'by_emotion': Dict[str, int],
                'avg_intensity': float,
                'most_common_emotion': str
            }
        """
        # Build query based on date filters
        where_clause = ""
        params = []

        if start_date:
            where_clause = "WHERE felt_at >= $1"
            params.append(start_date)

            if end_date:
                where_clause += " AND felt_at <= $2"
                params.append(end_date)
        elif end_date:
            where_clause = "WHERE felt_at <= $1"
            params.append(end_date)

        # Total count
        count_query = f"SELECT COUNT(*) FROM {self.table_name} {where_clause}"

        # Average intensity
        avg_query = f"SELECT AVG(intensity) FROM {self.table_name} {where_clause}"

        # Count by emotion type
        group_query = f"""
            SELECT emotion, COUNT(*) as count
            FROM {self.table_name}
            {where_clause}
            GROUP BY emotion
            ORDER BY count DESC
        """

        async with self.db.acquire() as conn:
            total_count = await conn.fetchval(count_query, *params) or 0
            avg_intensity = await conn.fetchval(avg_query, *params) or 0.0
            emotion_counts = await conn.fetch(group_query, *params)

        # Build by_emotion dict
        by_emotion = {row['emotion']: row['count'] for row in emotion_counts}

        # Most common emotion
        most_common = emotion_counts[0]['emotion'] if emotion_counts else None

        return {
            'total_count': total_count,
            'by_emotion': by_emotion,
            'avg_intensity': float(avg_intensity),
            'most_common_emotion': most_common
        }

    # =========================================================================
    # Dashboard-Specific Methods (Added for Batch-22 Repository Enhancement)
    # =========================================================================

    async def get_latest_state(self) -> Optional[asyncpg.Record]:
        """
        Get latest emotional state from emotional_states table.

        Note: This queries the 'emotional_states' table, not 'angela_emotions'.
        Returns the most recent emotional_states database record.

        Returns:
            Latest emotional_states record or None if no state exists
            The record contains: state_id, happiness, confidence, anxiety,
            motivation, gratitude, loneliness, triggered_by, emotion_note, created_at

        Example:
            >>> state = await repo.get_latest_state()
            >>> if state:
            ...     print(f"Happiness: {state['happiness']}")
            ...     print(f"Confidence: {state['confidence']}")
            Happiness: 0.86
            Confidence: 1.0
        """
        query = """
            SELECT
                state_id,
                happiness,
                confidence,
                anxiety,
                motivation,
                gratitude,
                loneliness,
                triggered_by,
                emotion_note,
                created_at
            FROM emotional_states
            ORDER BY created_at DESC
            LIMIT 1
        """

        async with self.db.acquire() as conn:
            row = await conn.fetchrow(query)

        # Return the database record directly (dict-like object)
        # Router will convert to its Pydantic model
        return row

    async def find_significant(
        self,
        min_intensity: int = 7,
        limit: int = 10
    ) -> List[Emotion]:
        """
        Find significant emotional moments (intensity >= threshold).

        Queries the angela_emotions table for high-intensity emotions.

        Args:
            min_intensity: Minimum intensity level (default: 7)
            limit: Maximum number of results (default: 10)

        Returns:
            List of significant emotions

        Example:
            >>> significant = await repo.find_significant(min_intensity=7, limit=3)
            >>> for emotion in significant:
            ...     print(f"{emotion.emotion} (intensity: {emotion.intensity})")
            deeply_moved (intensity: 10)
            loving (intensity: 8)
            achievement (intensity: 8)
        """
        query = f"""
            SELECT * FROM {self.table_name}
            WHERE intensity >= $1
            ORDER BY felt_at DESC
            LIMIT $2
        """

        async with self.db.acquire() as conn:
            rows = await conn.fetch(query, min_intensity, limit)

        return [self._row_to_entity(row) for row in rows]

    async def get_history(self, days: int = 7, limit: int = 100) -> List[Dict[str, Any]]:
        """
        Get emotional state history for the last N days.

        Queries the emotional_states table for historical emotional states.
        Returns raw dicts for API response (similar to AutonomousActionRepository pattern).

        Args:
            days: Number of days to look back (default: 7)
            limit: Maximum number of results (default: 100)

        Returns:
            List of emotional state dicts from the last N days

        Example:
            >>> history = await repo.get_history(days=7)
            >>> for state in history:
            ...     print(f"{state['created_at']}: Happiness={state['happiness']}")
            2025-11-02 22:00: Happiness=0.88
            2025-11-02 08:00: Happiness=0.86
        """
        query = """
            SELECT
                state_id,
                happiness,
                confidence,
                anxiety,
                motivation,
                gratitude,
                loneliness,
                triggered_by,
                emotion_note,
                created_at
            FROM emotional_states
            WHERE created_at >= NOW() - INTERVAL '%s days'
            ORDER BY created_at DESC
            LIMIT $1
        """ % days

        async with self.db.acquire() as conn:
            rows = await conn.fetch(query, limit)

        # Convert rows to dicts for API response
        return [dict(row) for row in rows]
