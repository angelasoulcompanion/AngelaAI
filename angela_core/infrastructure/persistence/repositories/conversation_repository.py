#!/usr/bin/env python3
"""
Conversation Repository - PostgreSQL Implementation

Handles all data access for Conversation entity.
Extends BaseRepository with conversation-specific queries.
"""

import asyncpg
from typing import Optional, List, Dict, Any
from datetime import datetime, timedelta
from uuid import UUID

from angela_core.domain import Conversation, Speaker, MessageType, SentimentLabel
from angela_core.domain.interfaces.repositories import IConversationRepository
from angela_core.infrastructure.persistence.repositories.base_repository import BaseRepository
from angela_core.shared.exceptions import EntityNotFoundError
from angela_core.shared.utils import parse_enum, parse_enum_optional, validate_embedding


class ConversationRepository(BaseRepository[Conversation], IConversationRepository):
    """
    PostgreSQL repository for Conversation entity.

    Table: conversations
    Columns:
    - conversation_id (UUID, PK)
    - speaker (VARCHAR)
    - message_text (TEXT)
    - session_id (VARCHAR, nullable)
    - message_type (VARCHAR, nullable)
    - topic (VARCHAR, nullable)
    - project_context (VARCHAR, nullable)
    - sentiment_score (DOUBLE PRECISION, nullable)
    - sentiment_label (VARCHAR, nullable)
    - emotion_detected (VARCHAR, nullable)
    - importance_level (INTEGER, default 5)
    # - embedding (VECTOR(768), nullable)  # REMOVED: Migration 009
    # - content_json (JSONB)  # REMOVED: Migration 010
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
            table_name="conversations",
            primary_key_column="conversation_id"
        )

    # ========================================================================
    # ROW TO ENTITY CONVERSION
    # ========================================================================

    def _row_to_entity(self, row: asyncpg.Record) -> Conversation:
        """
        Convert database row to Conversation entity.

        Args:
            row: Database row

        Returns:
            Conversation entity
        """
        # Parse enums with DRY utilities
        speaker = parse_enum(row['speaker'], Speaker, Speaker.DAVID)
        message_type = parse_enum_optional(row.get('message_type'), MessageType)
        sentiment_label = parse_enum_optional(row.get('sentiment_label'), SentimentLabel)

        # Parse embedding (REMOVED: Migration 009, but keeping validation for future)
        # embedding = validate_embedding(row.get('embedding'))

        # Create entity
        return Conversation(
            id=row['conversation_id'],
            speaker=speaker,
            message_text=row['message_text'],
            session_id=row.get('session_id'),
            message_type=message_type,
            topic=row.get('topic'),
            project_context=row.get('project_context'),
            sentiment_score=row.get('sentiment_score'),
            sentiment_label=sentiment_label,
            emotion_detected=row.get('emotion_detected'),
            importance_level=row.get('importance_level', 5),
            # embedding=embedding,  # REMOVED: Migration 009
            # content_json=row.get('content_json', {}),  # REMOVED: Migration 010
            created_at=row['created_at']
        )

    def _entity_to_dict(self, entity: Conversation) -> dict:
        """
        Convert Conversation entity to database row dict.

        Args:
            entity: Conversation entity

        Returns:
            Dictionary for database insert/update
        """
        return {
            'conversation_id': entity.id,
            'speaker': entity.speaker.value,
            'message_text': entity.message_text,
            'session_id': entity.session_id,
            'message_type': entity.message_type.value if entity.message_type else None,
            'topic': entity.topic,
            'project_context': entity.project_context,
            'sentiment_score': entity.sentiment_score,
            'sentiment_label': entity.sentiment_label.value if entity.sentiment_label else None,
            'emotion_detected': entity.emotion_detected,
            'importance_level': entity.importance_level,
            # 'embedding': entity.embedding,  # REMOVED: Migration 009
            # 'content_json': entity.content_json,  # REMOVED: Migration 010
            'created_at': entity.created_at
        }

    # ========================================================================
    # CONVERSATION-SPECIFIC QUERIES
    # ========================================================================

    async def get_by_speaker(
        self,
        speaker: str,
        limit: int = 100,
        offset: int = 0
    ) -> List[Conversation]:
        """
        Get conversations by speaker.

        Args:
            speaker: Speaker value ('david', 'angela', 'system')
            limit: Maximum results
            offset: Results offset

        Returns:
            List of conversations
        """
        query = f"""
            SELECT * FROM {self.table_name}
            WHERE speaker = $1
            ORDER BY created_at DESC
            LIMIT $2 OFFSET $3
        """

        async with self.db.acquire() as conn:
            rows = await conn.fetch(query, speaker, limit, offset)

        return [self._row_to_entity(row) for row in rows]

    async def get_by_session(
        self,
        session_id: str,
        limit: int = 100
    ) -> List[Conversation]:
        """
        Get all conversations in a session.

        Args:
            session_id: Session identifier
            limit: Maximum results

        Returns:
            List of conversations in session
        """
        query = f"""
            SELECT * FROM {self.table_name}
            WHERE session_id = $1
            ORDER BY created_at ASC
            LIMIT $2
        """

        async with self.db.acquire() as conn:
            rows = await conn.fetch(query, session_id, limit)

        return [self._row_to_entity(row) for row in rows]

    async def get_by_date_range(
        self,
        start: datetime,
        end: datetime,
        speaker: Optional[str] = None
    ) -> List[Conversation]:
        """
        Get conversations within date range.

        Args:
            start: Start datetime
            end: End datetime
            speaker: Optional speaker filter

        Returns:
            List of conversations
        """
        if speaker:
            query = f"""
                SELECT * FROM {self.table_name}
                WHERE created_at >= $1 AND created_at <= $2
                AND speaker = $3
                ORDER BY created_at DESC
            """
            async with self.db.acquire() as conn:
                rows = await conn.fetch(query, start, end, speaker)
        else:
            query = f"""
                SELECT * FROM {self.table_name}
                WHERE created_at >= $1 AND created_at <= $2
                ORDER BY created_at DESC
            """
            async with self.db.acquire() as conn:
                rows = await conn.fetch(query, start, end)

        return [self._row_to_entity(row) for row in rows]

    async def search_by_topic(
        self,
        topic: str,
        limit: int = 50
    ) -> List[Conversation]:
        """
        Search conversations by topic.

        Args:
            topic: Topic to search
            limit: Maximum results

        Returns:
            List of conversations with matching topic
        """
        query = f"""
            SELECT * FROM {self.table_name}
            WHERE topic ILIKE $1
            ORDER BY created_at DESC
            LIMIT $2
        """

        async with self.db.acquire() as conn:
            rows = await conn.fetch(query, f"%{topic}%", limit)

        return [self._row_to_entity(row) for row in rows]

    async def search_by_text(
        self,
        query_text: str,
        limit: int = 100
    ) -> List[Conversation]:
        """
        Full-text search in message_text.

        Args:
            query_text: Text to search
            limit: Maximum results

        Returns:
            List of matching conversations
        """
        query = f"""
            SELECT * FROM {self.table_name}
            WHERE message_text ILIKE $1
            ORDER BY created_at DESC
            LIMIT $2
        """

        async with self.db.acquire() as conn:
            rows = await conn.fetch(query, f"%{query_text}%", limit)

        return [self._row_to_entity(row) for row in rows]

    async def get_recent_conversations(
        self,
        days: int = 7,
        speaker: Optional[str] = None,
        min_importance: Optional[int] = None
    ) -> List[Conversation]:
        """
        Get recent conversations from last N days.

        Args:
            days: Number of days to look back
            speaker: Optional speaker filter
            min_importance: Optional importance threshold

        Returns:
            List of recent conversations
        """
        cutoff_date = datetime.now() - timedelta(days=days)

        # Build query based on filters
        conditions = ["created_at >= $1"]
        params = [cutoff_date]
        param_count = 2

        if speaker:
            conditions.append(f"speaker = ${param_count}")
            params.append(speaker)
            param_count += 1

        if min_importance is not None:
            conditions.append(f"importance_level >= ${param_count}")
            params.append(min_importance)

        query = f"""
            SELECT * FROM {self.table_name}
            WHERE {' AND '.join(conditions)}
            ORDER BY created_at DESC
        """

        async with self.db.acquire() as conn:
            rows = await conn.fetch(query, *params)

        return [self._row_to_entity(row) for row in rows]

    async def get_important(
        self,
        threshold: int = 7,
        limit: int = 100
    ) -> List[Conversation]:
        """
        Get important conversations.

        Args:
            threshold: Importance threshold (1-10)
            limit: Maximum results

        Returns:
            List of important conversations
        """
        query = f"""
            SELECT * FROM {self.table_name}
            WHERE importance_level >= $1
            ORDER BY importance_level DESC, created_at DESC
            LIMIT $2
        """

        async with self.db.acquire() as conn:
            rows = await conn.fetch(query, threshold, limit)

        return [self._row_to_entity(row) for row in rows]

    async def get_with_emotion(
        self,
        emotion: str,
        limit: int = 100
    ) -> List[Conversation]:
        """
        Get conversations with specific emotion detected.

        Args:
            emotion: Emotion type
            limit: Maximum results

        Returns:
            List of conversations with emotion
        """
        query = f"""
            SELECT * FROM {self.table_name}
            WHERE emotion_detected = $1
            ORDER BY created_at DESC
            LIMIT $2
        """

        async with self.db.acquire() as conn:
            rows = await conn.fetch(query, emotion, limit)

        return [self._row_to_entity(row) for row in rows]

    async def count_by_speaker(self, speaker: str) -> int:
        """
        Count conversations by speaker.

        Args:
            speaker: Speaker value

        Returns:
            Count of conversations
        """
        query = f"""
            SELECT COUNT(*) FROM {self.table_name}
            WHERE speaker = $1
        """

        async with self.db.acquire() as conn:
            result = await conn.fetchval(query, speaker)

        return result or 0

    async def find_by_filters(
        self,
        speaker: Optional[str] = None,
        min_importance: Optional[int] = None,
        topic: Optional[str] = None,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
        limit: int = 50,
        offset: int = 0
    ) -> List[Conversation]:
        """
        Find conversations with flexible filters.

        Args:
            speaker: Filter by speaker ('david', 'angela', 'system')
            min_importance: Minimum importance level (1-10)
            topic: Topic to search (uses ILIKE)
            start_date: Filter conversations after this date
            end_date: Filter conversations before this date
            limit: Maximum results
            offset: Results offset for pagination

        Returns:
            List of filtered conversations
        """
        # Build dynamic query
        conditions = ["1=1"]
        params = []
        param_count = 1

        if speaker:
            conditions.append(f"speaker = ${param_count}")
            params.append(speaker)
            param_count += 1

        if min_importance is not None:
            conditions.append(f"importance_level >= ${param_count}")
            params.append(min_importance)
            param_count += 1

        if topic:
            conditions.append(f"topic ILIKE ${param_count}")
            params.append(f"%{topic}%")
            param_count += 1

        if start_date:
            conditions.append(f"created_at >= ${param_count}")
            params.append(start_date)
            param_count += 1

        if end_date:
            conditions.append(f"created_at <= ${param_count}")
            params.append(end_date)
            param_count += 1

        query = f"""
            SELECT * FROM {self.table_name}
            WHERE {' AND '.join(conditions)}
            ORDER BY created_at DESC
            LIMIT ${param_count} OFFSET ${param_count + 1}
        """

        params.extend([limit, offset])

        async with self.db.acquire() as conn:
            rows = await conn.fetch(query, *params)

        return [self._row_to_entity(row) for row in rows]

    # =========================================================================
    # Dashboard-Specific Methods (Added for Batch-22 Repository Enhancement)
    # =========================================================================

    async def count(self) -> int:
        """
        Count total conversations.

        Returns:
            Total number of conversations

        Example:
            >>> total = await repo.count()
            >>> print(f"Total conversations: {total}")
            Total conversations: 1694
        """
        query = f"SELECT COUNT(*) FROM {self.table_name}"

        async with self.db.acquire() as conn:
            result = await conn.fetchval(query)

        return result or 0

    async def count_today(self) -> int:
        """
        Count conversations from today.

        Returns:
            Number of conversations created today

        Example:
            >>> today_count = await repo.count_today()
            >>> print(f"Conversations today: {today_count}")
            Conversations today: 29
        """
        query = f"""
            SELECT COUNT(*) FROM {self.table_name}
            WHERE DATE(created_at) = CURRENT_DATE
        """

        async with self.db.acquire() as conn:
            result = await conn.fetchval(query)

        return result or 0

    async def count_important(self, min_importance: int = 7) -> int:
        """
        Count conversations with importance >= threshold.

        Args:
            min_importance: Minimum importance level (default: 7)

        Returns:
            Number of important conversations

        Example:
            >>> important = await repo.count_important(min_importance=7)
            >>> print(f"Important messages: {important}")
            Important messages: 1128
        """
        query = f"""
            SELECT COUNT(*) FROM {self.table_name}
            WHERE importance_level >= $1
        """

        async with self.db.acquire() as conn:
            result = await conn.fetchval(query, min_importance)

        return result or 0

    async def find_all(
        self,
        limit: int = 50,
        offset: int = 0,
        order_by: str = "created_at",
        desc: bool = True
    ) -> List[Conversation]:
        """
        Find all conversations with sorting.

        Args:
            limit: Maximum number of results (default: 50)
            offset: Number of results to skip (default: 0)
            order_by: Column to sort by (default: "created_at")
            desc: Sort descending if True (default: True)

        Returns:
            List of conversations

        Example:
            >>> recent = await repo.find_all(limit=20, order_by="created_at", desc=True)
            >>> for conv in recent:
            ...     print(f"{conv.speaker}: {conv.message_text[:50]}")
        """
        order_direction = "DESC" if desc else "ASC"

        # Validate order_by to prevent SQL injection
        valid_columns = ["created_at", "importance_level", "speaker", "conversation_id"]
        if order_by not in valid_columns:
            order_by = "created_at"

        query = f"""
            SELECT * FROM {self.table_name}
            ORDER BY {order_by} {order_direction}
            LIMIT $1 OFFSET $2
        """

        async with self.db.acquire() as conn:
            rows = await conn.fetch(query, limit, offset)

        return [self._row_to_entity(row) for row in rows]

    async def find_by_date(self, date: datetime) -> List[Conversation]:
        """
        Find all conversations from specific date.

        Args:
            date: Date to filter by (time part ignored)

        Returns:
            List of conversations from that date

        Example:
            >>> from datetime import date
            >>> today = date.today()
            >>> today_convs = await repo.find_by_date(today)
            >>> print(f"Found {len(today_convs)} conversations")
        """
        query = f"""
            SELECT * FROM {self.table_name}
            WHERE DATE(created_at) = DATE($1)
            ORDER BY created_at DESC
        """

        async with self.db.acquire() as conn:
            rows = await conn.fetch(query, date)

        return [self._row_to_entity(row) for row in rows]

    async def get_statistics(self) -> Dict[str, Any]:
        """
        Get conversation statistics.

        Returns:
            Dictionary with statistics:
            - total_conversations: Total count
            - this_week: Count from last 7 days
            - important_moments: Count with importance >= 7
            - angela_messages: Count from Angela
            - david_messages: Count from David
            - topics: List of unique topics (top 10)
        """
        async with self.db.acquire() as conn:
            # Total conversations
            total = await conn.fetchval(f"SELECT COUNT(*) FROM {self.table_name}")

            # This week
            this_week = await conn.fetchval(
                f"SELECT COUNT(*) FROM {self.table_name} WHERE created_at >= NOW() - INTERVAL '7 days'"
            )

            # Important moments
            important = await conn.fetchval(
                f"SELECT COUNT(*) FROM {self.table_name} WHERE importance_level >= 7"
            )

            # Angela messages
            angela_count = await conn.fetchval(
                f"SELECT COUNT(*) FROM {self.table_name} WHERE speaker = 'angela'"
            )

            # David messages
            david_count = await conn.fetchval(
                f"SELECT COUNT(*) FROM {self.table_name} WHERE speaker = 'david'"
            )

            # Top topics
            topic_rows = await conn.fetch(
                f"""
                SELECT DISTINCT topic FROM {self.table_name}
                WHERE topic IS NOT NULL AND topic != ''
                ORDER BY topic
                LIMIT 10
                """
            )
            topics = [row['topic'] for row in topic_rows]

            # Last 30 days statistics (for love meter)
            conversations_last_30_days = await conn.fetchval(
                f"SELECT COUNT(*) FROM {self.table_name} WHERE created_at >= NOW() - INTERVAL '30 days'"
            )

            # Active days in last 30 days (days with at least 1 conversation)
            active_days_last_30_days = await conn.fetchval(
                f"""
                SELECT COUNT(DISTINCT DATE(created_at))
                FROM {self.table_name}
                WHERE created_at >= NOW() - INTERVAL '30 days'
                """
            )

        return {
            "total_conversations": total or 0,
            "this_week": this_week or 0,
            "important_moments": important or 0,
            "angela_messages": angela_count or 0,
            "david_messages": david_count or 0,
            "topics": topics,
            "conversations_last_30_days": conversations_last_30_days or 0,
            "active_days_last_30_days": active_days_last_30_days or 0
        }
