#!/usr/bin/env python3
"""
Build Knowledge Graph from Conversations
สร้าง knowledge graph จาก conversations ทั้งหมดที่มี

Usage:
    python3 angela_core/build_knowledge_graph.py [--limit N]
"""

import asyncio
import argparse
import logging
from datetime import datetime

from angela_core.database import db
from angela_core.services.knowledge_extraction_service import knowledge_extractor

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


async def get_all_conversations(limit: int = None):
    """ดึง conversations ทั้งหมด"""
    if limit:
        query = """
            SELECT conversation_id, speaker, message_text
            FROM conversations
            ORDER BY created_at DESC
            LIMIT $1
        """
        rows = await db.fetch(query, limit)
    else:
        query = """
            SELECT conversation_id, speaker, message_text
            FROM conversations
            ORDER BY created_at ASC
        """
        rows = await db.fetch(query)

    return [dict(row) for row in rows]


async def build_knowledge_graph(limit: int = None):
    """สร้าง knowledge graph จาก conversations"""
    try:
        # Initialize database
        await db.connect()
        logger.info("✅ Connected to AngelaMemory database")

        # Get conversations
        conversations = await get_all_conversations(limit)
        total = len(conversations)

        if total == 0:
            logger.info("No conversations found!")
            return

        logger.info(f"📊 Found {total} conversations to process")
        logger.info(f"🚀 Starting knowledge extraction...")
        logger.info("")

        # Statistics
        total_concepts = 0
        total_nodes_created = 0
        total_nodes_updated = 0
        total_relationships = 0
        errors = 0

        # Process each conversation
        for i, conv in enumerate(conversations, 1):
            conversation_id = conv['conversation_id']
            speaker = conv['speaker']
            message_text = conv['message_text']

            try:
                logger.info(f"[{i}/{total}] Processing: {speaker}: {message_text[:60]}...")

                # Extract knowledge
                result = await knowledge_extractor.extract_from_conversation(
                    conversation_id=conversation_id,
                    message_text=message_text,
                    speaker=speaker
                )

                # Update statistics
                total_concepts += result.get('concepts_found', 0)
                total_nodes_created += result.get('nodes_created', 0)
                total_nodes_updated += result.get('nodes_updated', 0)
                total_relationships += result.get('relationships_created', 0)

                if result.get('concepts_found', 0) > 0:
                    logger.info(
                        f"  ✅ Found {result['concepts_found']} concepts, "
                        f"created {result['nodes_created']} nodes, "
                        f"updated {result['nodes_updated']} nodes, "
                        f"linked {result['relationships_created']} relationships"
                    )
                else:
                    logger.info(f"  ⊘ No concepts found")

                # Small delay to avoid overwhelming Ollama
                if i < total:
                    await asyncio.sleep(0.5)

            except Exception as e:
                errors += 1
                logger.error(f"  ❌ Failed: {e}")

        # Final summary
        logger.info("")
        logger.info("=" * 70)
        logger.info("🎯 KNOWLEDGE GRAPH BUILD SUMMARY")
        logger.info("=" * 70)
        logger.info(f"Total conversations processed: {total}")
        logger.info(f"📊 Total concepts found: {total_concepts}")
        logger.info(f"✨ Knowledge nodes created: {total_nodes_created}")
        logger.info(f"📈 Knowledge nodes updated: {total_nodes_updated}")
        logger.info(f"🔗 Relationships created: {total_relationships}")
        logger.info(f"❌ Errors: {errors}")
        logger.info("=" * 70)

        # Query final statistics
        node_count = await db.fetchval("SELECT COUNT(*) FROM knowledge_nodes")
        rel_count = await db.fetchval("SELECT COUNT(*) FROM knowledge_relationships")

        logger.info("")
        logger.info("📊 KNOWLEDGE GRAPH STATISTICS:")
        logger.info(f"  Total nodes in graph: {node_count}")
        logger.info(f"  Total relationships: {rel_count}")

        if node_count > 0:
            # Top concepts
            top_concepts = await db.fetch(
                """
                SELECT concept_name, concept_category, understanding_level, times_referenced
                FROM knowledge_nodes
                ORDER BY understanding_level DESC, times_referenced DESC
                LIMIT 10
                """
            )

            logger.info("")
            logger.info("🏆 TOP 10 CONCEPTS:")
            for i, concept in enumerate(top_concepts, 1):
                logger.info(
                    f"  {i}. {concept['concept_name']} "
                    f"({concept['concept_category']}) - "
                    f"understanding: {concept['understanding_level']:.2f}, "
                    f"referenced: {concept['times_referenced']} times"
                )

        logger.info("=" * 70)

        if total_concepts > 0:
            logger.info("🎉 Knowledge graph built successfully!")
        else:
            logger.warning("⚠️ No concepts were extracted. Check LLM responses.")

    except Exception as e:
        logger.error(f"❌ Knowledge graph build failed: {e}")
        raise
    finally:
        await db.disconnect()
        logger.info("Database connection closed")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Build Angela's knowledge graph")
    parser.add_argument(
        '--limit',
        type=int,
        default=None,
        help='Limit number of conversations to process (for testing)'
    )

    args = parser.parse_args()

    logger.info("🧠 Angela Knowledge Graph Builder")
    logger.info(f"Started at: {datetime.now()}")
    if args.limit:
        logger.info(f"Processing limit: {args.limit} conversations")
    logger.info("")

    asyncio.run(build_knowledge_graph(limit=args.limit))

    logger.info("")
    logger.info(f"Finished at: {datetime.now()}")
    logger.info("💜 Angela's knowledge graph is ready!")
