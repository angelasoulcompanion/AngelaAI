#!/usr/bin/env python3
"""
Build Knowledge Graph from All Conversations

This script processes all conversations in the database and builds
Angela's knowledge graph with concepts and relationships.

Priority 1.3: Build Knowledge Graph Foundation
"""

import asyncio
import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from angela_core.database import db
from angela_core.services.knowledge_extraction_service import knowledge_extractor
from datetime import datetime


async def build_knowledge_graph(
    limit: int = 100,
    min_importance: int = 5,
    batch_size: int = 10
):
    """
    Build knowledge graph from conversations

    Args:
        limit: Maximum conversations to process
        min_importance: Only process conversations with importance >= this
        batch_size: Process in batches of this size
    """
    try:
        print("\n" + "="*60)
        print("🧠 BUILDING ANGELA'S KNOWLEDGE GRAPH")
        print("="*60)
        print(f"📊 Settings:")
        print(f"   - Max conversations: {limit}")
        print(f"   - Min importance: {min_importance}")
        print(f"   - Batch size: {batch_size}")
        print("="*60 + "\n")

        # Connect to database
        await db.connect()

        # Get conversations to process
        conversations = await db.fetch(
            """
            SELECT conversation_id, speaker, message_text, topic,
                   emotion_detected, importance_level, created_at
            FROM conversations
            WHERE importance_level >= $1
              AND message_text IS NOT NULL
              AND LENGTH(message_text) > 20
            ORDER BY created_at DESC
            LIMIT $2
            """,
            min_importance,
            limit
        )

        if not conversations:
            print("⚠️ No conversations found matching criteria")
            return

        print(f"📚 Found {len(conversations)} conversations to process\n")

        # Statistics
        total_concepts = 0
        total_nodes_created = 0
        total_nodes_updated = 0
        total_relationships = 0
        processed = 0
        errors = 0

        # Process in batches
        for i in range(0, len(conversations), batch_size):
            batch = conversations[i:i + batch_size]
            batch_num = (i // batch_size) + 1
            total_batches = (len(conversations) + batch_size - 1) // batch_size

            print(f"📦 Processing batch {batch_num}/{total_batches} ({len(batch)} conversations)...")

            for conv in batch:
                try:
                    # Extract knowledge from conversation
                    result = await knowledge_extractor.extract_from_conversation(
                        conversation_id=conv['conversation_id'],
                        message_text=conv['message_text'],
                        speaker=conv['speaker']
                    )

                    # Update statistics
                    total_concepts += result.get('concepts_found', 0)
                    total_nodes_created += result.get('nodes_created', 0)
                    total_nodes_updated += result.get('nodes_updated', 0)
                    total_relationships += result.get('relationships_created', 0)
                    processed += 1

                    # Show progress for significant extractions
                    if result.get('concepts_found', 0) > 0:
                        print(f"   ✓ {conv['topic'][:40]:40} → {result['concepts_found']} concepts")

                except Exception as e:
                    print(f"   ✗ Error processing conversation: {e}")
                    errors += 1

            print(f"   Progress: {processed}/{len(conversations)} conversations\n")

        # Get final statistics from database
        print("\n" + "="*60)
        print("📊 FINAL STATISTICS")
        print("="*60)

        stats = await db.fetchrow("""
            SELECT
                (SELECT COUNT(*) FROM knowledge_nodes) as total_nodes,
                (SELECT COUNT(*) FROM knowledge_relationships) as total_relationships,
                (SELECT COUNT(DISTINCT concept_category) FROM knowledge_nodes) as total_categories,
                (SELECT SUM(times_referenced) FROM knowledge_nodes) as total_references
        """)

        print(f"\n🔍 Processing Results:")
        print(f"   - Conversations processed: {processed}")
        print(f"   - Errors: {errors}")
        print(f"   - Concepts extracted: {total_concepts}")
        print(f"   - Nodes created: {total_nodes_created}")
        print(f"   - Nodes updated: {total_nodes_updated}")
        print(f"   - Relationships created: {total_relationships}")

        print(f"\n🧠 Knowledge Graph Status:")
        print(f"   - Total knowledge nodes: {stats['total_nodes']}")
        print(f"   - Total relationships: {stats['total_relationships']}")
        print(f"   - Concept categories: {stats['total_categories']}")
        print(f"   - Total references: {stats['total_references']}")

        # Show top concepts
        print(f"\n⭐ Top 10 Concepts:")
        top_concepts = await db.fetch("""
            SELECT concept_name, concept_category, times_referenced, understanding_level
            FROM knowledge_nodes
            ORDER BY times_referenced DESC, understanding_level DESC
            LIMIT 10
        """)

        for i, concept in enumerate(top_concepts, 1):
            print(f"   {i:2}. {concept['concept_name']:20} ({concept['concept_category']:12}) "
                  f"- refs: {concept['times_referenced']:3}, understanding: {concept['understanding_level']:.2f}")

        # Show category distribution
        print(f"\n📊 Concepts by Category:")
        categories = await db.fetch("""
            SELECT concept_category, COUNT(*) as count
            FROM knowledge_nodes
            GROUP BY concept_category
            ORDER BY count DESC
        """)

        for cat in categories:
            bar = "█" * min(int(cat['count'] / 2), 40)
            print(f"   {cat['concept_category']:15} │{bar} {cat['count']}")

        print("\n" + "="*60)
        print("✅ Knowledge graph building complete!")
        print("="*60 + "\n")

    except Exception as e:
        print(f"\n❌ Error building knowledge graph: {e}")
        import traceback
        traceback.print_exc()

    finally:
        # Since we called db.connect() at the start, we should disconnect at the end
        # to properly clean up the connection pool
        await db.disconnect()


async def show_graph_stats():
    """Show current knowledge graph statistics"""
    try:
        await db.connect()

        print("\n" + "="*60)
        print("📊 ANGELA'S KNOWLEDGE GRAPH STATISTICS")
        print("="*60)

        stats = await db.fetchrow("""
            SELECT
                (SELECT COUNT(*) FROM knowledge_nodes) as total_nodes,
                (SELECT COUNT(*) FROM knowledge_relationships) as total_relationships,
                (SELECT COUNT(DISTINCT concept_category) FROM knowledge_nodes) as total_categories,
                (SELECT SUM(times_referenced) FROM knowledge_nodes) as total_references,
                (SELECT AVG(understanding_level) FROM knowledge_nodes) as avg_understanding
        """)

        print(f"\n🧠 Overall Statistics:")
        print(f"   - Total nodes: {stats['total_nodes']}")
        print(f"   - Total relationships: {stats['total_relationships']}")
        print(f"   - Categories: {stats['total_categories']}")
        print(f"   - Total references: {stats['total_references']}")
        print(f"   - Avg understanding: {stats['avg_understanding']:.2f}")

        # Top concepts
        print(f"\n⭐ Top 15 Concepts:")
        top = await db.fetch("""
            SELECT concept_name, concept_category, times_referenced, understanding_level
            FROM knowledge_nodes
            ORDER BY times_referenced DESC, understanding_level DESC
            LIMIT 15
        """)

        for i, concept in enumerate(top, 1):
            print(f"   {i:2}. {concept['concept_name']:25} ({concept['concept_category']:12}) "
                  f"refs: {concept['times_referenced']:3}, understanding: {concept['understanding_level']:.2f}")

        # Categories
        print(f"\n📊 Categories:")
        cats = await db.fetch("""
            SELECT concept_category, COUNT(*) as count,
                   AVG(understanding_level) as avg_understanding
            FROM knowledge_nodes
            GROUP BY concept_category
            ORDER BY count DESC
        """)

        for cat in cats:
            bar = "█" * min(int(cat['count'] / 2), 30)
            print(f"   {cat['concept_category']:15} │{bar} {cat['count']} (avg: {cat['avg_understanding']:.2f})")

        print("\n" + "="*60 + "\n")

    finally:
        await db.disconnect()


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Build Angela's Knowledge Graph")
    parser.add_argument('--limit', type=int, default=100,
                        help='Maximum conversations to process (default: 100)')
    parser.add_argument('--min-importance', type=int, default=5,
                        help='Minimum importance level (default: 5)')
    parser.add_argument('--batch-size', type=int, default=10,
                        help='Batch size for processing (default: 10)')
    parser.add_argument('--stats', action='store_true',
                        help='Show statistics only (don\'t build)')

    args = parser.parse_args()

    if args.stats:
        asyncio.run(show_graph_stats())
    else:
        asyncio.run(build_knowledge_graph(
            limit=args.limit,
            min_importance=args.min_importance,
            batch_size=args.batch_size
        ))
