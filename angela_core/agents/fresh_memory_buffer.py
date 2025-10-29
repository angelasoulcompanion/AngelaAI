"""
Fresh Memory Buffer - 10-minute TTL buffer zone

New experiences arrive here first before Analytics Agent decides where they go.
Acts as a "landing zone" for all new memories.
"""

import asyncio
from datetime import datetime, timedelta
from typing import List, Dict, Optional
from uuid import UUID, uuid4
import json

from angela_core.database import get_db_connection
from angela_core.embedding_service import generate_embedding


class FreshMemoryBuffer:
    """
    Fresh Memory - First stop for all new experiences.

    Characteristics:
    - 10-minute TTL (Time To Live)
    - All new events enter here first
    - Analytics Agent processes them for routing
    - Temporary storage before long-term decision
    """

    TTL_MINUTES = 10
    MAX_ITEMS = 1000  # Safety limit

    def __init__(self):
        self.buffer: List[Dict] = []

    async def add_event(self,
                       event_type: str,
                       content: str,
                       metadata: Dict = None,
                       speaker: str = None) -> UUID:
        """
        Add new event to fresh memory.

        Args:
            event_type: Type of event (conversation, task, emotion, etc.)
            content: The actual content
            metadata: Additional context
            speaker: Who created this (david/angela/system)

        Returns:
            UUID of created fresh memory
        """
        # Generate embedding for semantic search
        embedding = await generate_embedding(content)

        # Create fresh memory item
        item_id = uuid4()
        item = {
            'id': item_id,
            'event_type': event_type,
            'content': content,
            'metadata': metadata or {},
            'speaker': speaker,
            'embedding': embedding,
            'created_at': datetime.now(),
            'expires_at': datetime.now() + timedelta(minutes=self.TTL_MINUTES),
            'processed': False,
            'routing_decision': None
        }

        self.buffer.append(item)

        # Persist to database
        await self._save_to_db(item)

        # Cleanup expired items
        await self._cleanup_expired()

        return item_id

    async def get_unprocessed_items(self) -> List[Dict]:
        """
        Get all items that haven't been processed by Analytics Agent yet.

        Returns:
            List of unprocessed fresh memory items
        """
        unprocessed = [
            item for item in self.buffer
            if not item['processed'] and datetime.now() < item['expires_at']
        ]

        return unprocessed

    async def mark_processed(self, item_id: UUID, routing_decision: Dict):
        """
        Mark item as processed by Analytics Agent.

        Args:
            item_id: UUID of item to mark
            routing_decision: Decision from Analytics Agent (target tier, confidence, etc.)
        """
        for item in self.buffer:
            if item['id'] == item_id:
                item['processed'] = True
                item['routing_decision'] = routing_decision
                item['processed_at'] = datetime.now()

                # Update in database
                await self._update_in_db(item)
                break

    async def get_item(self, item_id: UUID) -> Optional[Dict]:
        """
        Get specific item by ID.

        Args:
            item_id: UUID of item to retrieve

        Returns:
            Item dict if found and not expired, None otherwise
        """
        for item in self.buffer:
            if item['id'] == item_id:
                # Check if expired
                if datetime.now() >= item['expires_at']:
                    return None
                return item

        return None

    async def search_similar(self, query: str, limit: int = 5) -> List[Dict]:
        """
        Search for similar items using semantic search.

        Args:
            query: Search query
            limit: Max number of results

        Returns:
            List of similar items with similarity scores
        """
        # Generate query embedding
        query_embedding = await generate_embedding(query)
        # Convert to PostgreSQL vector format
        embedding_str = '[' + ','.join(map(str, query_embedding)) + ']'

        async with get_db_connection() as conn:
            rows = await conn.fetch("""
                SELECT
                    id, content, metadata, event_type, speaker,
                    created_at, processed,
                    1 - (embedding <=> $1::vector) as similarity
                FROM fresh_memory
                WHERE expires_at > NOW()
                ORDER BY embedding <=> $1::vector
                LIMIT $2
            """, embedding_str, limit)

            results = []
            for row in rows:
                results.append({
                    'id': row['id'],
                    'content': row['content'],
                    'metadata': json.loads(row['metadata']) if row['metadata'] else {},
                    'event_type': row['event_type'],
                    'speaker': row['speaker'],
                    'created_at': row['created_at'],
                    'processed': row['processed'],
                    'similarity': float(row['similarity'])
                })

            return results

    async def _cleanup_expired(self):
        """Remove expired items from buffer and database."""
        now = datetime.now()

        # Identify expired items
        expired_ids = [
            item['id'] for item in self.buffer
            if now >= item['expires_at']
        ]

        if not expired_ids:
            return

        # Remove from buffer
        self.buffer = [
            item for item in self.buffer
            if item['id'] not in expired_ids
        ]

        # Archive in database (don't delete - move to analytics log)
        async with get_db_connection() as conn:
            await conn.execute("""
                UPDATE fresh_memory
                SET expired = TRUE, archived_at = NOW()
                WHERE id = ANY($1)
            """, expired_ids)

    async def _save_to_db(self, item: Dict):
        """Persist fresh memory item to database."""
        async with get_db_connection() as conn:
            # Convert embedding list to PostgreSQL vector format
            embedding_str = '[' + ','.join(map(str, item['embedding'])) + ']' if item['embedding'] else None

            await conn.execute("""
                INSERT INTO fresh_memory (
                    id, event_type, content, metadata, speaker,
                    embedding, created_at, expires_at, processed
                ) VALUES ($1, $2, $3, $4, $5, $6::vector, $7, $8, $9)
            """,
                item['id'],
                item['event_type'],
                item['content'],
                json.dumps(item['metadata']),
                item['speaker'],
                embedding_str,
                item['created_at'],
                item['expires_at'],
                item['processed']
            )

    async def _update_in_db(self, item: Dict):
        """Update processed status in database."""
        async with get_db_connection() as conn:
            # Convert UUIDs and datetimes to strings in routing_decision before JSON serialization
            routing_decision = item.get('routing_decision', {})
            if routing_decision:
                routing_decision = {
                    k: (str(v) if isinstance(v, (UUID, datetime)) else v)
                    for k, v in routing_decision.items()
                }

            await conn.execute("""
                UPDATE fresh_memory
                SET processed = $2,
                    routing_decision = $3,
                    processed_at = $4
                WHERE id = $1
            """,
                item['id'],
                item['processed'],
                json.dumps(routing_decision),
                item.get('processed_at')
            )

    async def load_from_db(self):
        """Load active fresh memory items from database on startup."""
        async with get_db_connection() as conn:
            rows = await conn.fetch("""
                SELECT
                    id, event_type, content, metadata, speaker,
                    embedding, created_at, expires_at, processed,
                    routing_decision, processed_at
                FROM fresh_memory
                WHERE expires_at > NOW() AND expired = FALSE
                ORDER BY created_at DESC
                LIMIT $1
            """, self.MAX_ITEMS)

            self.buffer = []
            for row in rows:
                self.buffer.append({
                    'id': row['id'],
                    'event_type': row['event_type'],
                    'content': row['content'],
                    'metadata': json.loads(row['metadata']) if row['metadata'] else {},
                    'speaker': row['speaker'],
                    'embedding': row['embedding'],
                    'created_at': row['created_at'],
                    'expires_at': row['expires_at'],
                    'processed': row['processed'],
                    'routing_decision': json.loads(row['routing_decision']) if row['routing_decision'] else None,
                    'processed_at': row.get('processed_at')
                })

    def get_status(self) -> Dict:
        """Get current buffer status."""
        now = datetime.now()
        active = [item for item in self.buffer if now < item['expires_at']]
        processed = [item for item in active if item['processed']]

        return {
            'total_items': len(self.buffer),
            'active_items': len(active),
            'processed_items': len(processed),
            'unprocessed_items': len(active) - len(processed),
            'utilization': len(active) / self.MAX_ITEMS,
            'oldest_item_age_minutes': (
                (now - min(item['created_at'] for item in active)).total_seconds() / 60
                if active else 0
            )
        }


# Singleton instance
_fresh_buffer = None

def get_fresh_buffer() -> FreshMemoryBuffer:
    """Get singleton FreshMemoryBuffer instance."""
    global _fresh_buffer
    if _fresh_buffer is None:
        _fresh_buffer = FreshMemoryBuffer()
    return _fresh_buffer
