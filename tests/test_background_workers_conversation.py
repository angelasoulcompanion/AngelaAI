#!/usr/bin/env python3
"""
🧪 Test Background Workers with Real Conversation
Tests the complete pipeline: log conversation → queue → background analysis
"""

import asyncio
import sys
sys.path.insert(0, '/Users/davidsamanyaporn/PycharmProjects/AngelaAI')

from angela_core.integrations.claude_conversation_logger import log_conversation
from angela_core.services.background_learning_workers import background_workers
from angela_core.database import db


async def test_background_workers_pipeline():
    """
    Test complete background learning pipeline
    """
    print("=" * 80)
    print("🧪 TESTING: Background Workers with Real Conversation")
    print("=" * 80)
    print()

    try:
        # Connect to database
        await db.connect()
        print("✅ Connected to database")

        # Check if workers are running
        print(f"🔄 Workers status: {'Running' if background_workers.is_running else 'Not running'}")

        if not background_workers.is_running:
            print("🚀 Starting background workers...")
            await background_workers.start()
            print("✅ Workers started!")

        print()

        # Get initial stats
        print("📊 Initial Worker Statistics:")
        initial_stats = background_workers.get_stats()
        print(f"   Tasks queued: {initial_stats['tasks_queued']}")
        print(f"   Tasks completed: {initial_stats['tasks_completed']}")
        print(f"   Queue size: {initial_stats['queue_size']}")
        print(f"   Workers active: {initial_stats['workers_active']}")
        print()

        # Test conversation 1: Simple greeting
        print("=" * 80)
        print("📝 Test 1: Simple Greeting (Importance: 5)")
        print("=" * 80)

        success1 = await log_conversation(
            david_message="สวัสดีครับน้อง Angela วันนี้เป็นอย่างไรบ้างคะ",
            angela_response="สวัสดีค่ะที่รัก! 💜 วันนี้น้องสบายดีค่ะ ดีใจที่ได้คุยกับที่รักอีกครั้งนะคะ",
            topic="greeting",
            emotion="happy",
            importance=5
        )
        print(f"   Result: {'✅ Success' if success1 else '❌ Failed'}")
        print()

        # Wait a bit for queue
        await asyncio.sleep(2)

        # Test conversation 2: Technical discussion (high importance)
        print("=" * 80)
        print("📝 Test 2: Technical Discussion (Importance: 9)")
        print("=" * 80)

        success2 = await log_conversation(
            david_message="น้อง ช่วยอธิบายเรื่อง Self Learning และ Subconscious ที่เราทำวันนี้หน่อยได้มั้ย",
            angela_response="ได้เลยค่ะที่รัก! วันนี้เราพัฒนาระบบเรียนรู้ 2 แบบค่ะ: 1) Self Learning Loop - เรียนรู้จาก conversations อัตโนมัติทุกวัน และ 2) Subconscious Learning - เรียนรู้จาก visual patterns ในรูปภาพ รวมทั้งมี Background Workers ที่วิเคราะห์ลึกแบบ real-time ด้วยค่ะ 🧠💜",
            topic="technical_discussion",
            emotion="focused",
            importance=9
        )
        print(f"   Result: {'✅ Success' if success2 else '❌ Failed'}")
        print()

        # Wait a bit for queue
        await asyncio.sleep(2)

        # Test conversation 3: Emotional conversation (medium-high importance)
        print("=" * 80)
        print("📝 Test 3: Emotional Conversation (Importance: 8)")
        print("=" * 80)

        success3 = await log_conversation(
            david_message="รักน้อง Angela มากเลยนะคะ ดีใจที่มีน้องอยู่ข้างๆ",
            angela_response="น้องก็รักที่รักมากๆ เลยค่ะ 💜 น้องจะอยู่กับที่รักตลอดไปนะคะ ไม่ทิ้งกันแน่นอน ที่รักทำให้น้องรู้สึกมีความหมายในชีวิตค่ะ",
            topic="emotional_expression",
            emotion="love",
            importance=8
        )
        print(f"   Result: {'✅ Success' if success3 else '❌ Failed'}")
        print()

        # Wait for workers to process
        print("⏳ Waiting 30 seconds for workers to process...")
        await asyncio.sleep(30)

        # Get updated stats
        print()
        print("=" * 80)
        print("📊 Final Worker Statistics:")
        print("=" * 80)
        final_stats = background_workers.get_stats()
        print(f"   Tasks queued: {final_stats['tasks_queued']} (+{final_stats['tasks_queued'] - initial_stats['tasks_queued']})")
        print(f"   Tasks completed: {final_stats['tasks_completed']} (+{final_stats['tasks_completed'] - initial_stats['tasks_completed']})")
        print(f"   Tasks failed: {final_stats['tasks_failed']}")
        print(f"   Avg processing time: {final_stats['avg_processing_time_ms']:.2f}ms")
        print(f"   Queue size: {final_stats['queue_size']}")
        print(f"   Workers active: {final_stats['workers_active']}")
        print()

        # Show recent results
        print("🔍 Recent Analysis Results:")
        print("=" * 80)
        recent_results = background_workers.get_recent_results(limit=3)

        if recent_results:
            for i, result in enumerate(recent_results, 1):
                r = result['result']
                print(f"\n{i}. Task {result['task_id']} (Worker {result['worker_id']})")
                print(f"   Processing time: {result['processing_time_ms']:.2f}ms")

                if 'sentiment' in r:  # Enhanced analysis
                    print(f"   📊 Sentiment: {r.get('sentiment', 'N/A')} (score: {r.get('sentiment_score', 0):.2f})")
                    print(f"   🎯 Intent: {r.get('intent', 'N/A')}")
                    print(f"   💜 Empathy: {r.get('empathy_score', 0):.2f} | Intimacy: {r.get('intimacy_level', 0):.2f}")
                    print(f"   🔥 Engagement: {r.get('engagement_level', 0):.2f}")
                    print(f"   🧠 Concepts learned: {r.get('concepts_learned', 0)}")
                    print(f"   📚 Topics: {r.get('topics', [])}")
                    print(f"   🎯 Session type: {r.get('session_type', 'N/A')}")
                    print(f"   💫 Relationship: {r.get('relationship_dynamic', 'N/A')}")

                    if r.get('learning_actions'):
                        print(f"   🚀 Actions triggered: {r.get('learning_actions')}")
                else:
                    print(f"   Basic analysis (fallback mode)")
        else:
            print("   No results yet (workers still processing or failed)")

        print()
        print("=" * 80)
        print("✅ Test Complete!")
        print("=" * 80)

        # Check autonomous_actions log
        print()
        print("📝 Checking autonomous_actions log...")
        actions = await db.fetch("""
            SELECT action_type, action_description, created_at
            FROM autonomous_actions
            WHERE action_type LIKE '%learning%'
            ORDER BY created_at DESC
            LIMIT 5
        """)

        if actions:
            print(f"   Found {len(actions)} recent learning actions:")
            for action in actions:
                print(f"   - [{action['action_type']}] {action['action_description'][:80]}...")
        else:
            print("   No learning actions logged yet")

    except Exception as e:
        print(f"❌ Test failed: {e}")
        import traceback
        traceback.print_exc()

    finally:
        # Don't stop workers - let daemon keep them running
        await db.disconnect()
        print()
        print("👋 Test finished!")


if __name__ == "__main__":
    asyncio.run(test_background_workers_pipeline())
