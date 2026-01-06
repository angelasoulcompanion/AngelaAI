"""
Reverse Sync Service - Sync from Neon Cloud to Local PostgreSQL
Created for ที่รัก David - เพื่อให้ Local มี data ครบเหมือน Neon

Usage:
    python -m angela_core.sync.reverse_sync_service --full
    python -m angela_core.sync.reverse_sync_service --table conversations
    python -m angela_core.sync.reverse_sync_service --list-tables
"""

import asyncio
import argparse
import logging
from typing import Dict, Any, List, Optional
from datetime import datetime

import asyncpg

from angela_core.database import AngelaDatabase, get_secret

logging.basicConfig(level=logging.INFO, format='%(message)s')
logger = logging.getLogger(__name__)

# Tables to sync (priority order)
SYNC_TABLES = [
    # Core consciousness & memory
    'core_memories',
    'emotional_triggers',
    'emotional_growth',
    'emotional_mirroring',

    # Session continuity
    'active_session_context',

    # Conversations & emotions
    'conversations',
    'angela_emotions',
    'emotional_states',

    # Knowledge & learnings
    'knowledge_nodes',
    'knowledge_relationships',
    'learnings',

    # David's data
    'david_preferences',
    'david_mental_state',
    'david_health_tracking',
    'david_health_stats',
    'david_health_goals',

    # Angela's self
    'angela_goals',
    'angela_dreams',
    'angela_skills',
    'angela_journal',
    'angela_projects',
    'angela_subconscious',
    'angela_spontaneous_thoughts',
    'angela_self_assessments',
    'angela_curiosity_questions',
    'angela_learning_questions',
    'angela_consciousness_log',

    # Consciousness & patterns
    'consciousness_metrics',
    'pattern_detections',
    'empathy_moments',

    # Sessions & actions
    'work_sessions',
    'session_actions',
    'autonomous_actions',

    # Other important tables
    'relationship_milestones',
    'shared_experiences',
    'places_visited',
    'news_articles',
    'news_searches',
]

# Tables to NEVER sync (security)
EXCLUDED_TABLES = ['our_secrets']


class ReverseSyncService:
    """
    Sync data FROM Neon Cloud TO Local PostgreSQL.
    """

    def __init__(self):
        self.local_db = AngelaDatabase()
        self.neon_conn: Optional[asyncpg.Connection] = None
        self.stats = {
            'tables_synced': 0,
            'records_synced': 0,
            'records_skipped': 0,
            'errors': []
        }

    async def connect(self) -> bool:
        """Connect to both databases."""
        # Connect to local
        await self.local_db.connect()
        logger.info("✅ Connected to Local PostgreSQL")

        # Connect to Neon
        neon_url = await get_secret('NEON_DATABASE_URL')
        if not neon_url:
            logger.error("❌ NEON_DATABASE_URL not found in ~/.angela_secrets")
            return False

        try:
            self.neon_conn = await asyncpg.connect(neon_url, ssl='require')
            logger.info("✅ Connected to Neon Cloud (San Junipero)")
            return True
        except Exception as e:
            logger.error(f"❌ Failed to connect to Neon: {e}")
            return False

    async def disconnect(self):
        """Disconnect from databases."""
        if self.neon_conn:
            await self.neon_conn.close()
        await self.local_db.disconnect()

    async def list_neon_tables(self) -> List[str]:
        """List all tables in Neon database."""
        rows = await self.neon_conn.fetch("""
            SELECT table_name
            FROM information_schema.tables
            WHERE table_schema = 'public'
            AND table_type = 'BASE TABLE'
            ORDER BY table_name
        """)
        return [row['table_name'] for row in rows]

    async def get_table_columns(self, table_name: str, conn: asyncpg.Connection) -> List[Dict]:
        """Get column info for a table."""
        rows = await conn.fetch("""
            SELECT column_name, data_type, is_nullable
            FROM information_schema.columns
            WHERE table_name = $1
            ORDER BY ordinal_position
        """, table_name)
        return [dict(row) for row in rows]

    async def table_exists_local(self, table_name: str) -> bool:
        """Check if table exists in local database."""
        result = await self.local_db.fetchrow("""
            SELECT EXISTS (
                SELECT FROM information_schema.tables
                WHERE table_schema = 'public'
                AND table_name = $1
            )
        """, table_name)
        return result['exists']

    async def create_table_from_neon(self, table_name: str) -> bool:
        """Create table in local database based on Neon schema."""
        try:
            # Get CREATE TABLE statement from Neon
            result = await self.neon_conn.fetchrow("""
                SELECT
                    'CREATE TABLE IF NOT EXISTS ' || $1 || ' (' ||
                    string_agg(
                        column_name || ' ' ||
                        CASE
                            WHEN data_type = 'uuid' THEN 'UUID'
                            WHEN data_type = 'character varying' THEN 'VARCHAR(' || COALESCE(character_maximum_length::text, '255') || ')'
                            WHEN data_type = 'text' THEN 'TEXT'
                            WHEN data_type = 'integer' THEN 'INTEGER'
                            WHEN data_type = 'bigint' THEN 'BIGINT'
                            WHEN data_type = 'double precision' THEN 'DOUBLE PRECISION'
                            WHEN data_type = 'boolean' THEN 'BOOLEAN'
                            WHEN data_type = 'timestamp without time zone' THEN 'TIMESTAMP'
                            WHEN data_type = 'timestamp with time zone' THEN 'TIMESTAMPTZ'
                            WHEN data_type = 'jsonb' THEN 'JSONB'
                            WHEN data_type = 'json' THEN 'JSON'
                            WHEN data_type = 'ARRAY' THEN 'TEXT[]'
                            WHEN data_type = 'USER-DEFINED' THEN 'TEXT'
                            ELSE data_type
                        END ||
                        CASE WHEN is_nullable = 'NO' THEN ' NOT NULL' ELSE '' END,
                        ', '
                        ORDER BY ordinal_position
                    ) || ')' as create_sql
                FROM information_schema.columns
                WHERE table_name = $1
                GROUP BY table_name
            """, table_name)

            if result and result['create_sql']:
                await self.local_db.execute(result['create_sql'])
                logger.info(f"   📦 Created table: {table_name}")
                return True
            return False
        except Exception as e:
            logger.error(f"   ❌ Failed to create table {table_name}: {e}")
            return False

    async def get_primary_key(self, table_name: str, conn: asyncpg.Connection) -> Optional[str]:
        """Get primary key column for a table."""
        result = await conn.fetchrow("""
            SELECT a.attname as column_name
            FROM pg_index i
            JOIN pg_attribute a ON a.attrelid = i.indrelid AND a.attnum = ANY(i.indkey)
            WHERE i.indrelid = $1::regclass
            AND i.indisprimary
        """, table_name)
        return result['column_name'] if result else None

    async def sync_table(self, table_name: str) -> int:
        """
        Sync a single table from Neon to Local.
        Uses UPSERT to handle existing records.
        """
        logger.info(f"\n📥 Syncing: {table_name}")

        # Check if table exists locally
        if not await self.table_exists_local(table_name):
            logger.info(f"   Table doesn't exist locally, creating...")
            if not await self.create_table_from_neon(table_name):
                return 0

        # Get columns from Neon
        neon_columns = await self.get_table_columns(table_name, self.neon_conn)
        local_columns = await self.get_table_columns(table_name, self.local_db.pool)

        # Find common columns
        neon_col_names = {c['column_name'] for c in neon_columns}
        local_col_names = {c['column_name'] for c in local_columns}
        common_columns = list(neon_col_names & local_col_names)

        if not common_columns:
            logger.warning(f"   ⚠️ No common columns found")
            return 0

        # Get primary key
        pk = await self.get_primary_key(table_name, self.neon_conn)
        if not pk:
            # Try common PK patterns
            pk_patterns = [f'{table_name[:-1]}_id', 'id', f'{table_name}_id']
            for pattern in pk_patterns:
                if pattern in common_columns:
                    pk = pattern
                    break

        if not pk or pk not in common_columns:
            logger.warning(f"   ⚠️ No primary key found, using first column")
            pk = common_columns[0]

        # Fetch all records from Neon
        col_select = ", ".join(common_columns)
        try:
            records = await self.neon_conn.fetch(f"""
                SELECT {col_select} FROM {table_name}
            """)
        except Exception as e:
            logger.error(f"   ❌ Failed to fetch from Neon: {e}")
            self.stats['errors'].append(f"{table_name}: {e}")
            return 0

        if not records:
            logger.info(f"   ✓ No records in Neon")
            return 0

        logger.info(f"   Found {len(records)} records in Neon")

        # Build UPSERT query
        columns_str = ", ".join(common_columns)
        placeholders = ", ".join([f"${i+1}" for i in range(len(common_columns))])
        update_cols = [c for c in common_columns if c != pk]
        update_str = ", ".join([f"{c} = EXCLUDED.{c}" for c in update_cols])

        upsert_sql = f"""
            INSERT INTO {table_name} ({columns_str})
            VALUES ({placeholders})
            ON CONFLICT ({pk}) DO UPDATE SET {update_str}
        """

        # Insert records in batches
        synced = 0
        batch_size = 100

        for i in range(0, len(records), batch_size):
            batch = records[i:i+batch_size]
            for record in batch:
                try:
                    values = [record[col] for col in common_columns]
                    await self.local_db.execute(upsert_sql, *values)
                    synced += 1
                except Exception as e:
                    self.stats['records_skipped'] += 1
                    if 'duplicate key' not in str(e).lower():
                        logger.debug(f"   Skip record: {e}")

        logger.info(f"   ✅ Synced {synced} records")
        self.stats['records_synced'] += synced
        return synced

    async def sync_full(self) -> Dict[str, Any]:
        """Sync all configured tables from Neon to Local."""
        logger.info("""
╔══════════════════════════════════════════════════════════════╗
║     🔄 REVERSE SYNC: Neon Cloud → Local PostgreSQL           ║
║     💜 เพื่อที่รัก David                                        ║
╚══════════════════════════════════════════════════════════════╝
        """)

        start_time = datetime.now()

        # Get tables that exist in Neon
        neon_tables = set(await self.list_neon_tables())

        for table_name in SYNC_TABLES:
            if table_name in EXCLUDED_TABLES:
                logger.info(f"⏭️ Skipping excluded: {table_name}")
                continue

            if table_name not in neon_tables:
                logger.info(f"⏭️ Not in Neon: {table_name}")
                continue

            try:
                await self.sync_table(table_name)
                self.stats['tables_synced'] += 1
            except Exception as e:
                logger.error(f"❌ Error syncing {table_name}: {e}")
                self.stats['errors'].append(f"{table_name}: {e}")

        duration = (datetime.now() - start_time).total_seconds()

        logger.info(f"""
╔══════════════════════════════════════════════════════════════╗
║     📊 REVERSE SYNC COMPLETE                                 ║
╠══════════════════════════════════════════════════════════════╣
║  Tables synced:    {self.stats['tables_synced']:>5}                                      ║
║  Records synced:   {self.stats['records_synced']:>5}                                      ║
║  Records skipped:  {self.stats['records_skipped']:>5}                                      ║
║  Duration:         {duration:>5.1f}s                                     ║
╚══════════════════════════════════════════════════════════════╝
        """)

        if self.stats['errors']:
            logger.info("\n⚠️ Errors encountered:")
            for err in self.stats['errors'][:10]:
                logger.info(f"   • {err}")

        return self.stats


async def main():
    """CLI entry point."""
    parser = argparse.ArgumentParser(description='Angela Reverse Sync - Neon → Local')
    parser.add_argument('--full', action='store_true', help='Full sync all tables')
    parser.add_argument('--table', type=str, help='Sync specific table')
    parser.add_argument('--list-tables', action='store_true', help='List tables in Neon')

    args = parser.parse_args()

    service = ReverseSyncService()

    try:
        if not await service.connect():
            print("❌ Failed to connect to databases")
            return

        if args.list_tables:
            tables = await service.list_neon_tables()
            print(f"\n📋 Tables in Neon Cloud ({len(tables)} total):")
            for t in tables:
                print(f"   • {t}")

        elif args.table:
            await service.sync_table(args.table)

        elif args.full:
            await service.sync_full()

        else:
            parser.print_help()

    finally:
        await service.disconnect()


if __name__ == '__main__':
    asyncio.run(main())
