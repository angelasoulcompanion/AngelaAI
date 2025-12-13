"""
Queue Manager for Sync
Manages pending sync operations when Supabase is unavailable.
"""

import logging
import json
from typing import List, Dict, Any, Optional
from datetime import datetime
from uuid import UUID

from angela_core.database import db

logger = logging.getLogger(__name__)


class QueueManager:
    """Manages the sync_queue table for failed/pending syncs."""
    
    MAX_RETRIES = 3
    
    async def add_to_queue(
        self,
        table_name: str,
        operation: str,
        record_id: UUID,
        record_data: Dict[str, Any],
        error: Optional[str] = None
    ) -> UUID:
        """
        Add a failed sync operation to the queue.
        
        Args:
            table_name: Name of the table
            operation: INSERT, UPDATE, or DELETE
            record_id: Primary key of the record
            record_data: Full record data as dict
            error: Error message if any
            
        Returns:
            Queue item ID
        """
        # Convert non-serializable types
        serializable_data = self._make_serializable(record_data)
        
        result = await db.fetchval("""
            INSERT INTO sync_queue 
                (table_name, operation, record_id, record_data, last_error)
            VALUES ($1, $2, $3, $4, $5)
            RETURNING queue_id
        """, table_name, operation, record_id, json.dumps(serializable_data), error)
        
        logger.info(f"📥 Added to sync queue: {table_name}/{record_id}")
        return result
    
    async def get_pending_items(
        self,
        table_name: Optional[str] = None,
        limit: int = 100
    ) -> List[Dict[str, Any]]:
        """
        Get pending items from the queue.
        
        Args:
            table_name: Filter by table (optional)
            limit: Max items to return
            
        Returns:
            List of queue items
        """
        if table_name:
            rows = await db.fetch("""
                SELECT queue_id, table_name, operation, record_id, 
                       record_data, retry_count, last_error
                FROM sync_queue
                WHERE status = 'pending' AND table_name = $1
                AND retry_count < $2
                ORDER BY created_at ASC
                LIMIT $3
            """, table_name, self.MAX_RETRIES, limit)
        else:
            rows = await db.fetch("""
                SELECT queue_id, table_name, operation, record_id,
                       record_data, retry_count, last_error
                FROM sync_queue
                WHERE status = 'pending'
                AND retry_count < $1
                ORDER BY created_at ASC
                LIMIT $2
            """, self.MAX_RETRIES, limit)
        
        return [dict(row) for row in rows]
    
    async def mark_synced(self, queue_id: UUID):
        """Mark a queue item as successfully synced."""
        await db.execute("""
            UPDATE sync_queue
            SET status = 'synced'
            WHERE queue_id = $1
        """, queue_id)
        logger.debug(f"✅ Queue item {queue_id} marked as synced")
    
    async def mark_failed(self, queue_id: UUID, error: str):
        """Increment retry count and record error."""
        await db.execute("""
            UPDATE sync_queue
            SET retry_count = retry_count + 1,
                last_error = $2,
                status = CASE 
                    WHEN retry_count + 1 >= $3 THEN 'failed'
                    ELSE 'pending'
                END
            WHERE queue_id = $1
        """, queue_id, error, self.MAX_RETRIES)
        logger.warning(f"⚠️ Queue item {queue_id} retry failed: {error}")
    
    async def get_queue_stats(self) -> Dict[str, int]:
        """Get queue statistics."""
        stats = await db.fetch("""
            SELECT status, COUNT(*) as count
            FROM sync_queue
            GROUP BY status
        """)
        
        result = {'pending': 0, 'synced': 0, 'failed': 0}
        for row in stats:
            result[row['status']] = row['count']
        
        return result
    
    async def clear_synced(self, older_than_days: int = 7):
        """Remove old synced items from queue."""
        result = await db.execute("""
            DELETE FROM sync_queue
            WHERE status = 'synced'
            AND created_at < NOW() - INTERVAL '%s days'
        """ % older_than_days)
        logger.info(f"🗑️ Cleared old synced queue items")
    
    def _make_serializable(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Convert non-JSON-serializable types."""
        result = {}
        for key, value in data.items():
            if isinstance(value, UUID):
                result[key] = str(value)
            elif isinstance(value, datetime):
                result[key] = value.isoformat()
            elif isinstance(value, (list, tuple)) and len(value) > 0:
                # Handle vector embeddings
                if isinstance(value[0], (int, float)):
                    result[key] = list(value)
                else:
                    result[key] = [self._make_serializable(v) if isinstance(v, dict) else v for v in value]
            elif isinstance(value, dict):
                result[key] = self._make_serializable(value)
            else:
                result[key] = value
        return result
