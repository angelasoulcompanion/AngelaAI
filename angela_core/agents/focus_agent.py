"""
Focus Agent - Working Memory (7±2 items)
Based on George Miller's "Magic Number Seven, Plus or Minus Two"

Manages Angela's immediate attention and working memory.
Only holds the most important current items.
"""

import asyncio
from datetime import datetime, timedelta
from typing import List, Dict, Optional
from uuid import UUID, uuid4
import json

from angela_core.database import get_db_connection


class FocusAgent:
    """
    Angela's working memory - holds 7±2 most important current items.

    Based on cognitive science research:
    - George Miller (1956): Magic number 7±2
    - Items compete for attention based on importance and recency
    - Automatic pruning when capacity exceeded
    """

    MIN_ITEMS = 5
    MAX_ITEMS = 9
    OPTIMAL_ITEMS = 7

    def __init__(self):
        self.items: List[Dict] = []
        self.capacity = self.OPTIMAL_ITEMS

    async def add_item(self, content: str, metadata: Dict = None, importance: float = 1.0) -> UUID:
        """
        Add item to working memory. If full, removes lowest attention item.

        Args:
            content: The actual content to remember
            metadata: Additional context (speaker, topic, etc.)
            importance: Initial importance (0.0-10.0)

        Returns:
            UUID of created focus item
        """
        # Check capacity
        if len(self.items) >= self.capacity:
            await self._remove_lowest_attention()

        # Create focus item
        item_id = uuid4()
        item = {
            'id': item_id,
            'content': content,
            'metadata': metadata or {},
            'attention_weight': importance,
            'created_at': datetime.now(),
            'last_accessed': datetime.now(),
            'access_count': 0
        }

        self.items.append(item)

        # Persist to database
        await self._save_to_db(item)

        return item_id

    async def get_items(self) -> List[Dict]:
        """Get all current focus items, sorted by attention weight."""
        # Update attention weights based on recency
        await self._update_attention_weights()

        # Sort by attention (highest first)
        self.items.sort(key=lambda x: x['attention_weight'], reverse=True)

        return self.items.copy()

    async def access_item(self, item_id: UUID) -> Optional[Dict]:
        """
        Access an item, increasing its attention weight.

        Args:
            item_id: UUID of item to access

        Returns:
            Item dict if found, None otherwise
        """
        for item in self.items:
            if item['id'] == item_id:
                # Boost attention
                item['attention_weight'] += 0.5
                item['last_accessed'] = datetime.now()
                item['access_count'] += 1

                # Update in database
                await self._update_in_db(item)

                return item

        return None

    async def remove_item(self, item_id: UUID) -> bool:
        """
        Explicitly remove item from focus (e.g., when resolved/completed).

        Args:
            item_id: UUID of item to remove

        Returns:
            True if removed, False if not found
        """
        for i, item in enumerate(self.items):
            if item['id'] == item_id:
                self.items.pop(i)
                await self._archive_in_db(item_id)
                return True

        return False

    async def _remove_lowest_attention(self):
        """Remove item with lowest attention weight to make room."""
        if not self.items:
            return

        # Find lowest attention item
        lowest = min(self.items, key=lambda x: x['attention_weight'])

        # Move to Fresh Memory instead of deleting
        await self._promote_to_fresh(lowest)

        # Remove from focus
        self.items = [item for item in self.items if item['id'] != lowest['id']]

    async def _update_attention_weights(self):
        """
        Update attention weights based on time decay.

        Attention decays over time:
        - Items accessed recently maintain high attention
        - Older items gradually lose attention
        """
        now = datetime.now()

        for item in self.items:
            # Time since last access (in minutes)
            minutes_elapsed = (now - item['last_accessed']).total_seconds() / 60

            # Decay: lose 10% attention per hour
            decay_factor = 0.9 ** (minutes_elapsed / 60)

            # Apply decay
            item['attention_weight'] *= decay_factor

            # Boost from access count
            access_boost = min(item['access_count'] * 0.1, 2.0)
            item['attention_weight'] += access_boost

            # Clamp to [0.1, 10.0]
            item['attention_weight'] = max(0.1, min(10.0, item['attention_weight']))

    async def _save_to_db(self, item: Dict):
        """Persist focus item to database."""
        async with get_db_connection() as conn:
            await conn.execute("""
                INSERT INTO focus_memory (
                    id, content, metadata, attention_weight,
                    created_at, last_accessed, access_count
                ) VALUES ($1, $2, $3, $4, $5, $6, $7)
                ON CONFLICT (id) DO UPDATE SET
                    attention_weight = EXCLUDED.attention_weight,
                    last_accessed = EXCLUDED.last_accessed,
                    access_count = EXCLUDED.access_count
            """,
                item['id'],
                item['content'],
                json.dumps(item['metadata']),
                item['attention_weight'],
                item['created_at'],
                item['last_accessed'],
                item['access_count']
            )

    async def _update_in_db(self, item: Dict):
        """Update existing focus item in database."""
        async with get_db_connection() as conn:
            await conn.execute("""
                UPDATE focus_memory
                SET attention_weight = $2,
                    last_accessed = $3,
                    access_count = $4
                WHERE id = $1
            """,
                item['id'],
                item['attention_weight'],
                item['last_accessed'],
                item['access_count']
            )

    async def _archive_in_db(self, item_id: UUID):
        """Archive focus item (mark as no longer in focus)."""
        async with get_db_connection() as conn:
            await conn.execute("""
                UPDATE focus_memory
                SET archived = TRUE, archived_at = NOW()
                WHERE id = $1
            """, item_id)

    async def _promote_to_fresh(self, item: Dict):
        """
        Move item from Focus to Fresh Memory.

        Items evicted from focus aren't deleted - they go to Fresh Memory
        where they can be promoted back if they become relevant again.
        """
        # Generate embedding for the evicted item
        from angela_core.embedding_service import generate_embedding
        embedding_vec = await generate_embedding(item['content'])
        embedding_str = '[' + ','.join(map(str, embedding_vec)) + ']'

        # Add importance to metadata
        metadata = item['metadata'].copy()
        metadata['importance'] = item['attention_weight'] / 10.0  # Convert to 0-1 scale

        async with get_db_connection() as conn:
            now = datetime.now()
            expires = now + timedelta(minutes=10)

            await conn.execute("""
                INSERT INTO fresh_memory (
                    id, event_type, content, metadata, speaker,
                    embedding, created_at, expires_at, source_tier
                ) VALUES ($1, $2, $3, $4, $5, $6::vector, $7, $8, $9)
            """,
                uuid4(),
                'focus_eviction',
                item['content'],
                json.dumps(metadata),
                'system',
                embedding_str,
                now,
                expires,
                'focus'
            )

    async def load_from_db(self):
        """Load current focus items from database on startup."""
        async with get_db_connection() as conn:
            rows = await conn.fetch("""
                SELECT id, content, metadata, attention_weight,
                       created_at, last_accessed, access_count
                FROM focus_memory
                WHERE archived = FALSE
                ORDER BY attention_weight DESC
                LIMIT $1
            """, self.capacity)

            self.items = []
            for row in rows:
                self.items.append({
                    'id': row['id'],
                    'content': row['content'],
                    'metadata': json.loads(row['metadata']) if row['metadata'] else {},
                    'attention_weight': row['attention_weight'],
                    'created_at': row['created_at'],
                    'last_accessed': row['last_accessed'],
                    'access_count': row['access_count']
                })

    def get_status(self) -> Dict:
        """Get current status summary."""
        return {
            'current_items': len(self.items),
            'capacity': self.capacity,
            'utilization': len(self.items) / self.capacity,
            'top_3_topics': [
                item['metadata'].get('topic', 'unknown')
                for item in sorted(self.items, key=lambda x: x['attention_weight'], reverse=True)[:3]
            ]
        }


# Singleton instance
_focus_agent = None

def get_focus_agent() -> FocusAgent:
    """Get singleton FocusAgent instance."""
    global _focus_agent
    if _focus_agent is None:
        _focus_agent = FocusAgent()
    return _focus_agent
