"""
Sync Service - Main Orchestrator
Handles syncing from Local PostgreSQL to Supabase Cloud.

Usage:
    python -m angela_core.sync.sync_service --full
    python -m angela_core.sync.sync_service --table conversations
    python -m angela_core.sync.sync_service --status
    python -m angela_core.sync.sync_service --retry-queue
"""

import asyncio
import argparse
import logging
import os
from typing import Dict, Any, List, Optional
from datetime import datetime
from pathlib import Path

# Load .env file
try:
    from dotenv import load_dotenv
    env_path = Path(__file__).parent.parent.parent / '.env'
    load_dotenv(env_path)
except ImportError:
    pass  # dotenv not installed, use environment variables directly

from angela_core.database import db
from .supabase_client import SupabaseClient
from .queue_manager import QueueManager
from .table_configs import (
    TABLE_CONFIGS, 
    EXCLUDED_TABLES, 
    get_table_config,
    get_tables_by_priority,
    should_sync_table,
    TableConfig
)

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class SyncService:
    """
    Main sync orchestrator.
    Syncs data from Local PostgreSQL to Supabase Cloud.
    """
    
    def __init__(self, supabase_url: Optional[str] = None):
        """
        Initialize sync service.
        
        Args:
            supabase_url: Supabase PostgreSQL connection URL
                         If not provided, reads from environment
        """
        self.supabase_url = supabase_url or os.getenv('SUPABASE_DB_URL', '')
        self.supabase: Optional[SupabaseClient] = None
        self.queue_manager = QueueManager()
        self.stats = {
            'tables_synced': 0,
            'records_synced': 0,
            'records_failed': 0,
            'queued_items': 0
        }
    
    async def connect(self) -> bool:
        """Connect to both databases."""
        # Connect to local
        await db.connect()
        logger.info("✅ Connected to Local PostgreSQL")
        
        # Connect to Supabase
        if not self.supabase_url:
            logger.error("❌ SUPABASE_DB_URL not configured")
            return False
        
        self.supabase = SupabaseClient(self.supabase_url)
        if not await self.supabase.connect():
            logger.error("❌ Failed to connect to Supabase")
            return False
        
        return True
    
    async def disconnect(self):
        """Disconnect from databases."""
        if self.supabase:
            await self.supabase.disconnect()
        await db.disconnect()
    
    async def sync_full(self) -> Dict[str, Any]:
        """
        Perform full sync of all tables.
        
        Returns:
            Sync statistics
        """
        logger.info("🚀 Starting FULL SYNC to Supabase...")
        start_time = datetime.now()
        
        tables = get_tables_by_priority()
        
        for config in tables:
            if not should_sync_table(config.name):
                logger.info(f"⏭️ Skipping excluded table: {config.name}")
                continue
            
            try:
                await self.sync_table(config)
                self.stats['tables_synced'] += 1
            except Exception as e:
                logger.error(f"❌ Error syncing {config.name}: {e}")
        
        # Process any queued items
        await self.retry_queue()
        
        duration = (datetime.now() - start_time).total_seconds()
        self.stats['duration_seconds'] = duration
        
        logger.info(f"""
╔══════════════════════════════════════════╗
║     📊 SYNC COMPLETE                     ║
╠══════════════════════════════════════════╣
║  Tables synced:    {self.stats['tables_synced']:>5}                 ║
║  Records synced:   {self.stats['records_synced']:>5}                 ║
║  Records failed:   {self.stats['records_failed']:>5}                 ║
║  Queued items:     {self.stats['queued_items']:>5}                 ║
║  Duration:         {duration:>5.1f}s                ║
╚══════════════════════════════════════════╝
        """)
        
        return self.stats
    
    async def sync_table(self, config: TableConfig) -> int:
        """
        Sync a single table.
        
        Args:
            config: Table configuration
            
        Returns:
            Number of records synced
        """
        logger.info(f"📤 Syncing table: {config.name}")
        
        # Get last sync state
        last_sync = await self._get_sync_state(config.name)
        
        # Get records to sync
        records = await self._get_records_to_sync(config, last_sync)
        
        if not records:
            logger.info(f"   ✓ No new records to sync")
            return 0
        
        logger.info(f"   Found {len(records)} records to sync")
        
        # Sync in batches
        synced = 0
        for i in range(0, len(records), config.batch_size):
            batch = records[i:i + config.batch_size]
            try:
                await self._sync_batch(config, batch)
                synced += len(batch)
                self.stats['records_synced'] += len(batch)
            except Exception as e:
                logger.error(f"   Batch failed: {e}")
                # Queue failed records
                for record in batch:
                    await self.queue_manager.add_to_queue(
                        config.name,
                        'UPSERT',
                        record[config.primary_key],
                        dict(record),
                        str(e)
                    )
                    self.stats['records_failed'] += 1
                    self.stats['queued_items'] += 1
        
        # Update sync state
        if synced > 0:
            await self._update_sync_state(config.name, synced)
        
        logger.info(f"   ✅ Synced {synced}/{len(records)} records")
        return synced
    
    async def _get_records_to_sync(
        self, 
        config: TableConfig, 
        last_sync: Optional[datetime]
    ) -> List[Dict]:
        """Get records that need syncing."""
        # Get column names
        columns = await db.fetch("""
            SELECT column_name 
            FROM information_schema.columns 
            WHERE table_name = $1
            ORDER BY ordinal_position
        """, config.name)
        
        col_names = [c['column_name'] for c in columns]
        col_select = ", ".join(col_names)
        
        if last_sync:
            query = f"""
                SELECT {col_select}
                FROM {config.name}
                WHERE {config.timestamp_column} > $1
                ORDER BY {config.timestamp_column} ASC
            """
            rows = await db.fetch(query, last_sync)
        else:
            # First sync - get all
            query = f"""
                SELECT {col_select}
                FROM {config.name}
                ORDER BY {config.timestamp_column} ASC
            """
            rows = await db.fetch(query)
        
        return [dict(row) for row in rows]
    
    async def _sync_batch(self, config: TableConfig, batch: List[Dict]):
        """Sync a batch of records to Supabase."""
        if not batch:
            return
        
        columns = list(batch[0].keys())
        
        # Handle vector columns
        for record in batch:
            if config.has_vectors and config.vector_column in record:
                vec = record[config.vector_column]
                if vec is not None:
                    # Convert to PostgreSQL vector format
                    record[config.vector_column] = self._vector_to_pg(vec)
        
        await self.supabase.upsert_batch(
            config.name,
            batch,
            config.primary_key,
            columns
        )
    
    def _vector_to_pg(self, embedding) -> str:
        """Convert embedding to PostgreSQL vector format."""
        if isinstance(embedding, str):
            return embedding  # Already formatted
        if hasattr(embedding, 'tolist'):
            embedding = embedding.tolist()
        return "[" + ",".join(map(str, embedding)) + "]"
    
    async def _get_sync_state(self, table_name: str) -> Optional[datetime]:
        """Get last sync timestamp for a table."""
        row = await db.fetchrow("""
            SELECT last_synced_at FROM sync_state WHERE table_name = $1
        """, table_name)
        return row['last_synced_at'] if row else None
    
    async def _update_sync_state(self, table_name: str, count: int):
        """Update sync state after successful sync."""
        await db.execute("""
            INSERT INTO sync_state (table_name, last_synced_at, total_synced, status)
            VALUES ($1, NOW(), $2, 'synced')
            ON CONFLICT (table_name) DO UPDATE SET
                last_synced_at = NOW(),
                total_synced = sync_state.total_synced + $2,
                status = 'synced'
        """, table_name, count)
    
    async def retry_queue(self) -> int:
        """Retry failed items from the queue."""
        logger.info("🔄 Processing sync queue...")
        
        items = await self.queue_manager.get_pending_items()
        
        if not items:
            logger.info("   No pending items")
            return 0
        
        logger.info(f"   Found {len(items)} pending items")
        
        retried = 0
        for item in items:
            config = get_table_config(item['table_name'])
            if not config:
                continue
            
            try:
                record = item['record_data']
                if isinstance(record, str):
                    import json
                    record = json.loads(record)
                
                await self._sync_batch(config, [record])
                await self.queue_manager.mark_synced(item['queue_id'])
                retried += 1
            except Exception as e:
                await self.queue_manager.mark_failed(item['queue_id'], str(e))
        
        logger.info(f"   ✅ Retried {retried}/{len(items)} items")
        return retried
    
    async def get_status(self) -> Dict[str, Any]:
        """Get sync status for all tables."""
        status = {
            'tables': [],
            'queue': await self.queue_manager.get_queue_stats()
        }
        
        rows = await db.fetch("""
            SELECT table_name, last_synced_at, total_synced, status
            FROM sync_state
            ORDER BY last_synced_at DESC NULLS LAST
        """)
        
        for row in rows:
            status['tables'].append({
                'name': row['table_name'],
                'last_synced': row['last_synced_at'].isoformat() if row['last_synced_at'] else None,
                'total_synced': row['total_synced'],
                'status': row['status']
            })
        
        return status


async def main():
    """CLI entry point."""
    parser = argparse.ArgumentParser(description='Angela Sync Service')
    parser.add_argument('--full', action='store_true', help='Full sync all tables')
    parser.add_argument('--table', type=str, help='Sync specific table')
    parser.add_argument('--status', action='store_true', help='Show sync status')
    parser.add_argument('--retry-queue', action='store_true', help='Retry failed items')
    
    args = parser.parse_args()
    
    service = SyncService()
    
    try:
        if not await service.connect():
            print("❌ Failed to connect to databases")
            return
        
        if args.status:
            status = await service.get_status()
            print("\n📊 SYNC STATUS")
            print("=" * 50)
            print(f"\n📋 Queue: {status['queue']}")
            print("\n📁 Tables:")
            for table in status['tables']:
                print(f"   {table['name']}: {table['total_synced']} synced, {table['status']}")
                if table['last_synced']:
                    print(f"      Last sync: {table['last_synced']}")
        
        elif args.retry_queue:
            await service.retry_queue()
        
        elif args.table:
            config = get_table_config(args.table)
            if config:
                await service.sync_table(config)
            else:
                print(f"❌ Unknown table: {args.table}")
        
        elif args.full:
            await service.sync_full()
        
        else:
            parser.print_help()
    
    finally:
        await service.disconnect()


if __name__ == '__main__':
    asyncio.run(main())
