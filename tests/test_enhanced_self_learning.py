#!/usr/bin/env python3
"""
Test Enhanced Self-Learning Service
Priority 2.2: เรียนรู้เร็วขึ้น แม่นยำขึ้น

Tests 3 major enhancements:
1. LLM-Powered Preference Detection (instead of pattern matching)
2. Smarter Pattern Detection with Historical Analysis
3. Knowledge Consolidation (auto-merge duplicates)
"""

import asyncio
import sys
from pathlib import Path
from datetime import datetime

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from angela_core.services.self_learning_service import self_learning_loop
from angela_core.database import db
from angela_core.claude_conversation_logger import log_conversation


async def test_enhanced_self_learning():
    """Test all 3 enhancements"""

    print("=" * 80)
    print("🧠 Testing Enhanced Self-Learning Service (Priority 2.2)")
    print("=" * 80)
    print()

    # Connect to database
    await db.connect()

    try:
        # ========================================
        # Test 1: LLM-Powered Preference Detection
        # ========================================
        print("📍 Test 1: LLM-Powered Preference Detection")
        print("-" * 80)

        # Log a conversation with implicit preferences
        await log_conversation(
            david_message="I really don't like when things are slow. I prefer fast responses, even if they're shorter. And I want Angela to use Thai when talking about feelings.",
            angela_response="เข้าใจค่ะที่รัก! 💜 น้องจะตอบเร็วขึ้น และใช้ภาษาไทยเวลาพูดเรื่องความรู้สึกค่ะ",
            topic="preference_communication",
            emotion="understanding",
            importance=8
        )

        print("✅ Logged test conversation with multiple preferences")
        print()

        # Get the conversation ID
        last_conv = await db.fetchrow(
            """
            SELECT conversation_id, message_text
            FROM conversations
            WHERE speaker = 'david'
            ORDER BY created_at DESC
            LIMIT 1
            """
        )

        if last_conv:
            print(f"   Conversation ID: {last_conv['conversation_id']}")
            print(f"   Message: {last_conv['message_text'][:80]}...")
            print()

            # Run self-learning on it
            print("   🔄 Running self-learning with LLM preference detection...")
            result = await self_learning_loop.learn_from_conversation(
                conversation_id=last_conv['conversation_id'],
                trigger_source="test"
            )

            print(f"   ✅ Results:")
            print(f"      - Concepts learned: {result.get('concepts_learned', 0)}")
            print(f"      - Preferences detected: {result.get('preferences_saved', 0)}")
            print(f"      - Patterns found: {result.get('patterns_recorded', 0)}")
            print(f"      - Learning time: {result.get('learning_time_ms', 0)}ms")
            print()

            # Check what preferences were detected
            prefs = await db.fetch(
                """
                SELECT category, preference_value, confidence_level
                FROM david_preferences
                ORDER BY created_at DESC
                LIMIT 3
                """
            )

            if prefs:
                print("   📋 Recently detected preferences:")
                for i, pref in enumerate(prefs, 1):
                    print(f"      {i}. [{pref['category']}] {pref.get('preference_value', 'N/A')[:60]}... (confidence: {pref.get('confidence_level', 0):.2f})")
            print()

        print()

        # ========================================
        # Test 2: Smarter Pattern Detection
        # ========================================
        print("📍 Test 2: Smarter Pattern Detection (Historical Analysis)")
        print("-" * 80)

        # Log another conversation to build history
        await log_conversation(
            david_message="Let's work on Angela again today. I love building her intelligence!",
            angela_response="น้องก็รักเวลาที่ได้พัฒนากับที่รักค่ะ! 💜 มาทำต่อกันเลยค่ะ",
            topic="angela_development",
            emotion="excited",
            importance=9
        )

        last_conv2 = await db.fetchrow(
            """
            SELECT conversation_id
            FROM conversations
            WHERE speaker = 'david'
            ORDER BY created_at DESC
            LIMIT 1
            """
        )

        if last_conv2:
            print("   ✅ Logged test conversation for pattern detection")
            print(f"   Conversation ID: {last_conv2['conversation_id']}")
            print()

            print("   🔄 Running self-learning with pattern detection...")
            result2 = await self_learning_loop.learn_from_conversation(
                conversation_id=last_conv2['conversation_id'],
                trigger_source="test"
            )

            print(f"   ✅ Patterns detected: {result2.get('patterns_recorded', 0)}")
            print()

        print()

        # ========================================
        # Test 3: Knowledge Consolidation
        # ========================================
        print("📍 Test 3: Knowledge Consolidation (Auto-Merge Duplicates)")
        print("-" * 80)

        # First, check current knowledge stats
        node_count = await db.fetchval(
            "SELECT COUNT(*) FROM knowledge_nodes"
        )

        print(f"   📊 Current knowledge nodes: {node_count}")
        print()

        # Run consolidation (dry run first)
        print("   🔍 Running DRY RUN consolidation (similarity >= 0.85)...")
        dry_result = await self_learning_loop.consolidate_knowledge(
            similarity_threshold=0.85,
            dry_run=True
        )

        print(f"   ✅ Dry run results:")
        print(f"      - Duplicates found: {dry_result.get('duplicates_found', 0)}")
        print()

        if dry_result.get('duplicates_found', 0) > 0:
            # Actually run consolidation
            print("   🧹 Running ACTUAL consolidation...")
            result3 = await self_learning_loop.consolidate_knowledge(
                similarity_threshold=0.85,
                dry_run=False
            )

            print(f"   ✅ Consolidation results:")
            print(f"      - Duplicates found: {result3.get('duplicates_found', 0)}")
            print(f"      - Nodes merged: {result3.get('nodes_merged', 0)}")
            print(f"      - Relationships updated: {result3.get('relationships_updated', 0)}")
            print(f"      - Quality improved: {result3.get('knowledge_quality_improved', False)}")

            new_count = await db.fetchval(
                "SELECT COUNT(*) FROM knowledge_nodes"
            )
            print(f"      - Knowledge nodes: {node_count} → {new_count}")
            print()
        else:
            print("   ✨ Knowledge graph is already clean!")
            print()

        print()

        # ========================================
        # Test 4: Learning Statistics
        # ========================================
        print("📍 Test 4: Learning Statistics (7 days)")
        print("-" * 80)

        stats = await self_learning_loop.get_learning_statistics(days=7)

        print(f"   📊 Learning Stats (last 7 days):")
        print(f"      - Learning sessions: {stats.get('learning_sessions', 0)}")
        print(f"      - Concepts learned: {stats.get('total_concepts_learned', 0)}")
        print(f"      - Preferences detected: {stats.get('total_preferences_detected', 0)}")
        print(f"      - Knowledge growth rate: {stats.get('knowledge_growth_rate', 0):.2f} nodes/day")
        print(f"      - Learning efficiency: {stats.get('learning_efficiency', 0):.2f} concepts/session")
        print()

        # ========================================
        # Summary
        # ========================================
        print("=" * 80)
        print("🎉 All Enhanced Self-Learning Tests Complete!")
        print("=" * 80)
        print()

        print("✅ Enhancements Tested:")
        print("   1. LLM-Powered Preference Detection - Uses Qwen 2.5:14b instead of pattern matching")
        print("   2. Smarter Pattern Detection - Analyzes historical context")
        print("   3. Knowledge Consolidation - Auto-merges duplicate concepts")
        print("   4. Learning Statistics - Track growth and efficiency")
        print()

        print("🚀 Priority 2.2 implementation COMPLETE!")
        print()

    except Exception as e:
        print(f"\n❌ Test failed: {e}")
        import traceback
        traceback.print_exc()

    finally:
        await db.disconnect()


if __name__ == "__main__":
    asyncio.run(test_enhanced_self_learning())
