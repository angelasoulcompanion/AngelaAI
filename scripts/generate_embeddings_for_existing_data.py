#!/usr/bin/env python3
"""
Generate Embeddings for Existing Data
======================================

After Migration 015 restored embedding columns, this script generates
embeddings for all existing data that has NULL embeddings.

Features:
- Batch processing for performance
- Progress tracking
- Resume capability (skip already processed)
- Detailed statistics

Usage:
    python3 scripts/generate_embeddings_for_existing_data.py [--table TABLE_NAME] [--batch-size N]

Examples:
    # Process all tables
    python3 scripts/generate_embeddings_for_existing_data.py

    # Process specific table
    python3 scripts/generate_embeddings_for_existing_data.py --table conversations

    # Custom batch size
    python3 scripts/generate_embeddings_for_existing_data.py --batch-size 50

Author: น้อง Angela 💜
Date: 2025-11-04
"""

import asyncio
import sys
import argparse
import logging
from pathlib import Path
from datetime import datetime
from typing import List, Dict, Tuple

# Add parent directory to path
script_dir = Path(__file__).parent.parent
if str(script_dir) not in sys.path:
    sys.path.insert(0, str(script_dir))

from angela_core.database import db
from angela_core.services.embedding_service import get_embedding_service

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class EmbeddingMigration:
    """Generate embeddings for existing data"""

    # Table configurations: (table_name, text_column, id_column)
    # ✅ Column names verified from database schema
    TABLES = [
        ('conversations', 'message_text', 'conversation_id'),
        ('angela_messages', 'message_text', 'message_id'),
        ('angela_emotions', 'context', 'emotion_id'),
        ('knowledge_nodes', 'concept_name', 'node_id'),  # Fixed: node_name → concept_name
        ('knowledge_items', 'item_value', 'item_id'),
        ('learning_patterns', 'description', 'id'),  # Fixed: pattern_id → id (PK is 'id')
        ('learnings', 'insight', 'learning_id'),  # Fixed: learning_description → insight
        ('david_preferences', 'preference_key', 'id'),  # Fixed: preference_id → id (PK is 'id' not 'preference_id')
    ]

    def __init__(self, batch_size: int = 100):
        self.batch_size = batch_size
        self.embedding_service = get_embedding_service()
        self.stats = {
            'total_processed': 0,
            'total_updated': 0,
            'total_skipped': 0,
            'total_errors': 0,
            'by_table': {}
        }

    async def get_null_count(self, table_name: str) -> int:
        """Get count of rows with NULL embeddings"""
        result = await db.fetchval(f"""
            SELECT COUNT(*)
            FROM {table_name}
            WHERE embedding IS NULL
        """)
        return result or 0

    async def fetch_batch(
        self,
        table_name: str,
        text_column: str,
        id_column: str,
        offset: int
    ) -> List[Tuple]:
        """Fetch batch of rows with NULL embeddings"""
        query = f"""
            SELECT {id_column}, {text_column}
            FROM {table_name}
            WHERE embedding IS NULL
            AND {text_column} IS NOT NULL
            AND {text_column} != ''
            ORDER BY {id_column}
            LIMIT $1 OFFSET $2
        """
        return await db.fetch(query, self.batch_size, offset)

    async def update_embedding(
        self,
        table_name: str,
        id_column: str,
        row_id,
        embedding_str: str
    ) -> bool:
        """Update a single row's embedding"""
        try:
            query = f"""
                UPDATE {table_name}
                SET embedding = $1::vector
                WHERE {id_column} = $2
            """
            await db.execute(query, embedding_str, row_id)
            return True
        except Exception as e:
            logger.error(f"Error updating {table_name} row {row_id}: {e}")
            return False

    async def process_table(
        self,
        table_name: str,
        text_column: str,
        id_column: str
    ) -> Dict:
        """Process all rows in a table"""
        logger.info(f"\n{'='*60}")
        logger.info(f"📊 Processing table: {table_name}")
        logger.info(f"{'='*60}")

        # Get total count
        total_null = await self.get_null_count(table_name)

        if total_null == 0:
            logger.info(f"✅ {table_name}: No rows need embeddings!")
            return {'processed': 0, 'updated': 0, 'skipped': 0, 'errors': 0}

        logger.info(f"🎯 Found {total_null} rows with NULL embeddings")

        stats = {'processed': 0, 'updated': 0, 'skipped': 0, 'errors': 0}
        offset = 0

        while True:
            # Fetch batch
            batch = await self.fetch_batch(table_name, text_column, id_column, offset)

            if not batch:
                break

            logger.info(f"⚙️  Processing batch {offset // self.batch_size + 1} ({len(batch)} rows)...")

            for row in batch:
                row_id = row[id_column]
                text = row[text_column]

                if not text or not text.strip():
                    stats['skipped'] += 1
                    continue

                try:
                    # Generate embedding
                    embedding = await self.embedding_service.generate_embedding(text)
                    embedding_str = self.embedding_service.embedding_to_pgvector(embedding)

                    # Update database
                    success = await self.update_embedding(
                        table_name, id_column, row_id, embedding_str
                    )

                    if success:
                        stats['updated'] += 1
                    else:
                        stats['errors'] += 1

                    stats['processed'] += 1

                    # Progress update every 10 rows
                    if stats['processed'] % 10 == 0:
                        logger.info(f"   Progress: {stats['processed']}/{total_null} ({stats['processed']*100//total_null}%)")

                except Exception as e:
                    logger.error(f"Error processing row {row_id}: {e}")
                    stats['errors'] += 1
                    stats['processed'] += 1

            offset += self.batch_size

        # Final summary for this table
        logger.info(f"\n✅ {table_name} complete!")
        logger.info(f"   Processed: {stats['processed']}")
        logger.info(f"   Updated: {stats['updated']}")
        logger.info(f"   Skipped: {stats['skipped']}")
        logger.info(f"   Errors: {stats['errors']}")

        return stats

    async def process_all_tables(self, specific_table: str = None):
        """Process all tables or a specific table"""
        start_time = datetime.now()

        logger.info("🚀 Starting Embedding Generation Migration")
        logger.info(f"⚙️  Batch size: {self.batch_size}")
        logger.info(f"🧠 Embedding model: {self.embedding_service.MODEL_NAME}")
        logger.info(f"📐 Dimensions: {self.embedding_service.DIMENSIONS}")

        # Filter tables if specific table requested
        tables = self.TABLES
        if specific_table:
            tables = [t for t in self.TABLES if t[0] == specific_table]
            if not tables:
                logger.error(f"❌ Table '{specific_table}' not found in configuration!")
                return

        # Process each table
        for table_name, text_column, id_column in tables:
            try:
                table_stats = await self.process_table(table_name, text_column, id_column)

                # Update global stats
                self.stats['total_processed'] += table_stats['processed']
                self.stats['total_updated'] += table_stats['updated']
                self.stats['total_skipped'] += table_stats['skipped']
                self.stats['total_errors'] += table_stats['errors']
                self.stats['by_table'][table_name] = table_stats

            except Exception as e:
                logger.error(f"❌ Error processing table {table_name}: {e}")
                import traceback
                traceback.print_exc()

        # Final summary
        elapsed = datetime.now() - start_time

        logger.info(f"\n{'='*60}")
        logger.info("🎉 MIGRATION COMPLETE!")
        logger.info(f"{'='*60}")
        logger.info(f"⏱️  Total time: {elapsed}")
        logger.info(f"📊 Total processed: {self.stats['total_processed']}")
        logger.info(f"✅ Total updated: {self.stats['total_updated']}")
        logger.info(f"⏭️  Total skipped: {self.stats['total_skipped']}")
        logger.info(f"❌ Total errors: {self.stats['total_errors']}")

        # Cache stats
        cache_stats = self.embedding_service.get_cache_stats()
        logger.info(f"\n📈 Cache Statistics:")
        logger.info(f"   Hit rate: {cache_stats['hit_rate_percent']}%")
        logger.info(f"   Hits: {cache_stats['cache_hits']}")
        logger.info(f"   Misses: {cache_stats['cache_misses']}")

        logger.info("\n💜 น้อง Angela: Embedding migration complete! ✨")


async def main():
    """Main entry point"""
    parser = argparse.ArgumentParser(description='Generate embeddings for existing data')
    parser.add_argument('--table', type=str, help='Process specific table only')
    parser.add_argument('--batch-size', type=int, default=100, help='Batch size (default: 100)')

    args = parser.parse_args()

    migration = EmbeddingMigration(batch_size=args.batch_size)

    try:
        await migration.process_all_tables(specific_table=args.table)
    except KeyboardInterrupt:
        logger.info("\n⚠️  Migration interrupted by user")
        logger.info(f"📊 Progress so far: {migration.stats['total_updated']} rows updated")
    except Exception as e:
        logger.error(f"❌ Migration failed: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())
