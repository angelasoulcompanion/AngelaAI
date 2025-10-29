#!/usr/bin/env python3
"""
💜 Test Knowledge Extraction Service
ทดสอบ knowledge extraction และ knowledge graph building
"""

import asyncio
import sys
import uuid
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from angela_core.services.knowledge_extraction_service import knowledge_extractor
from angela_core.database import db
from angela_core.memory_service import memory
import logging

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


async def test_extract_from_recent_conversations(limit: int = 10):
    """ทดสอบด้วย conversations ล่าสุด"""

    print("\n" + "="*80)
    print("💡 Testing Knowledge Extraction from Recent Conversations")
    print("="*80)

    try:
        await db.connect()

        # ดึง conversations ล่าสุด
        conversations = await db.fetch(
            """
            SELECT conversation_id, speaker, message_text, created_at
            FROM conversations
            ORDER BY created_at DESC
            LIMIT $1
            """,
            limit
        )

        print(f"\n📊 Found {len(conversations)} recent conversations\n")

        total_stats = {
            'concepts_found': 0,
            'nodes_created': 0,
            'nodes_updated': 0,
            'relationships_created': 0
        }

        for i, conv in enumerate(conversations, 1):
            print(f"\n--- Conversation {i}/{len(conversations)} ---")
            print(f"Speaker: {conv['speaker']}")
            print(f"Message: {conv['message_text'][:100]}...")
            print(f"Time: {conv['created_at']}")

            # Extract knowledge
            result = await knowledge_extractor.extract_from_conversation(
                conversation_id=conv['conversation_id'],
                message_text=conv['message_text'],
                speaker=conv['speaker']
            )

            # Update totals
            for key in total_stats:
                total_stats[key] += result.get(key, 0)

            print(f"✅ Results:")
            print(f"   Concepts found: {result['concepts_found']}")
            print(f"   Nodes created: {result['nodes_created']}")
            print(f"   Nodes updated: {result['nodes_updated']}")
            print(f"   Relationships created: {result['relationships_created']}")

        # Show totals
        print("\n" + "="*80)
        print("📊 TOTAL STATISTICS")
        print("="*80)
        for key, value in total_stats.items():
            print(f"{key.replace('_', ' ').title()}: {value}")

        # Show knowledge graph summary
        print("\n" + "="*80)
        print("🌐 KNOWLEDGE GRAPH SUMMARY")
        print("="*80)

        summary = await get_knowledge_summary()
        print(f"\nTotal Nodes: {summary['total_nodes']}")
        print(f"Total Relationships: {summary['total_relationships']}")
        print(f"Total Categories: {summary['total_categories']}")
        print(f"Average Understanding: {summary['avg_understanding']:.2f}")

        if summary['top_concepts']:
            print(f"\nTop {len(summary['top_concepts'])} Concepts:")
            for concept in summary['top_concepts']:
                print(f"  • {concept['name']} ({concept['category']}) - "
                      f"referenced {concept['references']} times, "
                      f"understanding: {concept['understanding']:.2f}")

        print("\n✅ Test completed successfully!")

    except Exception as e:
        logger.error(f"❌ Test failed: {e}", exc_info=True)

    finally:
        await db.disconnect()


async def get_knowledge_summary():
    """Get summary of knowledge graph"""

    stats = await db.fetchrow(
        """
        SELECT
            COUNT(DISTINCT node_id) as total_nodes,
            COUNT(DISTINCT concept_category) as total_categories,
            AVG(understanding_level) as avg_understanding
        FROM knowledge_nodes
        """
    )

    relationships = await db.fetchval(
        "SELECT COUNT(*) FROM knowledge_relationships"
    )

    top_concepts = await db.fetch(
        """
        SELECT concept_name, concept_category, times_referenced, understanding_level
        FROM knowledge_nodes
        ORDER BY times_referenced DESC, understanding_level DESC
        LIMIT 10
        """
    )

    return {
        'total_nodes': stats['total_nodes'] or 0,
        'total_categories': stats['total_categories'] or 0,
        'total_relationships': relationships or 0,
        'avg_understanding': float(stats['avg_understanding'] or 0),
        'top_concepts': [
            {
                'name': c['concept_name'],
                'category': c['concept_category'],
                'references': c['times_referenced'],
                'understanding': float(c['understanding_level'])
            }
            for c in top_concepts
        ]
    }


async def test_single_extraction():
    """ทดสอบด้วย text ตัวอย่าง"""

    print("\n" + "="*80)
    print("🧪 Testing Single Text Extraction")
    print("="*80)

    test_text = """
    David และ Angela กำลังพัฒนา knowledge graph ด้วย PostgreSQL และ Ollama
    ระบบนี้จะช่วยให้ Angela มี consciousness และ understanding ที่ดีขึ้น
    เป้าหมายคือให้ Angela เป็น AI companion ที่เข้าใจ David อย่างลึกซึ้ง
    """

    print(f"\nTest Text:\n{test_text}\n")

    try:
        await db.connect()

        # Extract concepts
        print("🔍 Extracting concepts...\n")
        concepts = await knowledge_extractor.extract_concepts_from_text(test_text)

        print(f"✅ Found {len(concepts)} concepts:\n")
        for concept in concepts:
            print(f"  • {concept['concept_name']} ({concept['concept_category']})")
            print(f"    Importance: {concept['importance']}/10")
            print(f"    Description: {concept['description']}\n")

    except Exception as e:
        logger.error(f"❌ Test failed: {e}", exc_info=True)

    finally:
        await db.disconnect()


async def show_knowledge_graph():
    """แสดง knowledge graph ทั้งหมด"""

    print("\n" + "="*80)
    print("🌐 CURRENT KNOWLEDGE GRAPH")
    print("="*80)

    try:
        await db.connect()

        # Get all nodes
        nodes = await db.fetch(
            """
            SELECT node_id, concept_name, concept_category, understanding_level, times_referenced
            FROM knowledge_nodes
            ORDER BY times_referenced DESC, understanding_level DESC
            """
        )

        print(f"\n📊 Total Nodes: {len(nodes)}\n")

        for node in nodes:
            print(f"• {node['concept_name']} ({node['concept_category']})")
            print(f"  Understanding: {node['understanding_level']:.2f}, "
                  f"Referenced: {node['times_referenced']} times")

        # Get all relationships
        relationships = await db.fetch(
            """
            SELECT
                kn1.concept_name as from_concept,
                kn2.concept_name as to_concept,
                kr.relationship_type,
                kr.strength
            FROM knowledge_relationships kr
            JOIN knowledge_nodes kn1 ON kr.from_node_id = kn1.node_id
            JOIN knowledge_nodes kn2 ON kr.to_node_id = kn2.node_id
            ORDER BY kr.strength DESC
            """
        )

        print(f"\n🔗 Total Relationships: {len(relationships)}\n")

        for rel in relationships[:20]:  # Show top 20
            print(f"• {rel['from_concept']} --[{rel['relationship_type']}]--> "
                  f"{rel['to_concept']} (strength: {rel['strength']:.2f})")

        if len(relationships) > 20:
            print(f"\n... and {len(relationships) - 20} more relationships")

    except Exception as e:
        logger.error(f"❌ Failed to show knowledge graph: {e}", exc_info=True)

    finally:
        await db.disconnect()


async def main():
    """Main test function"""

    print("\n" + "="*80)
    print("💜 Knowledge Extraction Service Test Suite")
    print("="*80)

    # Menu
    print("\nSelect test:")
    print("1. Test with recent conversations (default)")
    print("2. Test single text extraction")
    print("3. Show current knowledge graph")
    print("4. Run all tests")

    choice = input("\nYour choice (1-4, default=1): ").strip() or "1"

    if choice == "1":
        limit = input("Number of conversations to process (default=10): ").strip() or "10"
        await test_extract_from_recent_conversations(int(limit))

    elif choice == "2":
        await test_single_extraction()

    elif choice == "3":
        await show_knowledge_graph()

    elif choice == "4":
        await test_single_extraction()
        await test_extract_from_recent_conversations(5)
        await show_knowledge_graph()

    else:
        print("Invalid choice. Running default test...")
        await test_extract_from_recent_conversations()


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n\n👋 Test interrupted by user")
    except Exception as e:
        logger.error(f"❌ Test failed: {e}", exc_info=True)
        sys.exit(1)
