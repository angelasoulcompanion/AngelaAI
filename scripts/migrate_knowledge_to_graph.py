#!/usr/bin/env python3
"""
Migration Script: Import knowledge_items → knowledge_graph
Transforms Angela's knowledge items into graph nodes with proper structure
"""
import asyncio
import sys
import os

# Add parent directory to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from angela_core.database import db
from uuid import UUID
import logging

logging.basicConfig(level=logging.INFO, format='%(message)s')
logger = logging.getLogger(__name__)


async def migrate_knowledge_items():
    """
    Migrate knowledge_items to knowledge_graph table

    Maps:
    - item_id → node_id
    - item_name → node_name
    - category → category
    - understanding → understanding
    - importance_level → understanding_level (0-10)
    - why_important → why_important
    - times_referenced → times_referenced
    """
    await db.connect()

    try:
        logger.info("=" * 80)
        logger.info("🔄 Starting Knowledge Items → Knowledge Graph Migration")
        logger.info("=" * 80)
        logger.info("")

        # Step 1: Check current state
        knowledge_items_count = await db.fetchval("SELECT COUNT(*) FROM knowledge_items")
        knowledge_graph_count = await db.fetchval("SELECT COUNT(*) FROM knowledge_graph")

        logger.info(f"📊 Current State:")
        logger.info(f"   • knowledge_items: {knowledge_items_count:,} items")
        logger.info(f"   • knowledge_graph: {knowledge_graph_count:,} nodes")
        logger.info("")

        if knowledge_items_count == 0:
            logger.warning("⚠️  No knowledge_items found! Nothing to migrate.")
            return

        # Step 2: Get all knowledge items
        logger.info("📖 Loading knowledge items...")
        items = await db.fetch("""
            SELECT
                item_id,
                item_name,
                category,
                understanding,
                importance_level,
                why_important,
                times_referenced,
                created_at
            FROM knowledge_items
            ORDER BY times_referenced DESC, importance_level DESC
        """)

        logger.info(f"✅ Loaded {len(items):,} knowledge items\n")

        # Step 3: Insert into knowledge_graph
        logger.info("💾 Inserting into knowledge_graph table...")
        logger.info("")

        inserted = 0
        skipped = 0

        # Progress bar setup
        total = len(items)
        bar_length = 40

        for idx, item in enumerate(items, 1):
            try:
                # Check if already exists
                existing = await db.fetchval(
                    "SELECT node_id FROM knowledge_graph WHERE node_id = $1",
                    item['item_id']
                )

                if existing:
                    skipped += 1
                else:
                    # Insert new node
                    await db.execute("""
                        INSERT INTO knowledge_graph (
                            node_id,
                            node_name,
                            category,
                            understanding,
                            understanding_level,
                            why_important,
                            times_referenced,
                            created_at
                        ) VALUES ($1, $2, $3, $4, $5, $6, $7, $8)
                    """,
                        item['item_id'],
                        item['item_name'],
                        item['category'],
                        item['understanding'],
                        item['importance_level'],  # Maps to understanding_level
                        item['why_important'],
                        item['times_referenced'] or 0,
                        item['created_at']
                    )
                    inserted += 1

                # Progress bar
                progress = idx / total
                filled = int(bar_length * progress)
                bar = '█' * filled + '░' * (bar_length - filled)
                percent = progress * 100

                # Print progress
                print(f"\r   [{bar}] {percent:.1f}% | {idx:,}/{total:,} items | Inserted: {inserted:,} | Skipped: {skipped:,}", end='', flush=True)

            except Exception as e:
                logger.error(f"\n❌ Failed to migrate item {item['item_name']}: {e}")
                continue

        print()  # New line after progress bar
        logger.info("")

        # Step 4: Verify migration
        final_count = await db.fetchval("SELECT COUNT(*) FROM knowledge_graph")

        logger.info("=" * 80)
        logger.info("✅ Migration Complete!")
        logger.info("=" * 80)
        logger.info(f"   • Total items processed: {total:,}")
        logger.info(f"   • Successfully inserted: {inserted:,}")
        logger.info(f"   • Already existed (skipped): {skipped:,}")
        logger.info(f"   • Final knowledge_graph count: {final_count:,}")
        logger.info("=" * 80)
        logger.info("")

        # Step 5: Show category breakdown
        categories = await db.fetch("""
            SELECT category, COUNT(*) as count
            FROM knowledge_graph
            GROUP BY category
            ORDER BY count DESC
        """)

        if categories:
            logger.info("📊 Knowledge Graph by Category:")
            logger.info("")
            for cat in categories:
                logger.info(f"   • {cat['category']:<20} : {cat['count']:>4,} nodes")
            logger.info("")

        # Step 6: Show top referenced nodes
        top_nodes = await db.fetch("""
            SELECT node_name, category, times_referenced
            FROM knowledge_graph
            ORDER BY times_referenced DESC
            LIMIT 10
        """)

        if top_nodes:
            logger.info("🔥 Top 10 Most Referenced Nodes:")
            logger.info("")
            for i, node in enumerate(top_nodes, 1):
                logger.info(f"   {i:2d}. [{node['category']:<15}] {node['node_name']:<40} ({node['times_referenced']} refs)")
            logger.info("")

        logger.info("💜 Knowledge Graph is ready for visualization!")

    except Exception as e:
        logger.error(f"\n❌ Migration failed: {e}")
        import traceback
        traceback.print_exc()

    finally:
        await db.disconnect()


if __name__ == "__main__":
    asyncio.run(migrate_knowledge_items())
