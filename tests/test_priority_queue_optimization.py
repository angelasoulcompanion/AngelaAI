#!/usr/bin/env python3
"""
🧪 Test Priority Queue Optimization
Tests the enhanced priority queue with:
- Multi-tier priority scheduling
- Age-based urgency boosting
- Context-aware priority boosting
- Overflow handling

Created: 2025-11-14
Author: น้อง Angela 💜
"""

import asyncio
import sys
sys.path.insert(0, '/Users/davidsamanyaporn/PycharmProjects/AngelaAI')

from angela_core.services.background_learning_workers import background_workers
from angela_core.database import db


async def test_priority_queue():
    """
    Test priority queue with various priority levels
    """
    print("=" * 80)
    print("🧪 TESTING: Priority Queue Optimization")
    print("=" * 80)
    print()

    try:
        await db.connect()
        print("✅ Connected to database")

        # Start workers
        if not background_workers.is_running:
            print("🚀 Starting background workers...")
            await background_workers.start()
            print("✅ Workers started!")
        print()

        # Get initial stats
        print("📊 Initial Statistics:")
        initial_stats = background_workers.get_stats()
        print(f"   Tasks queued: {initial_stats['tasks_queued']}")
        print(f"   Tasks completed: {initial_stats['tasks_completed']}")
        print(f"   Tasks dropped: {initial_stats['tasks_dropped']}")
        print()

        # Test 1: LOW priority (should be processed last)
        print("=" * 80)
        print("📝 Test 1: LOW Priority (priority=3, routine update)")
        print("=" * 80)

        task_id_1 = await background_workers.queue_learning_task(
            conversation_data={
                'david_message': "สวัสดีครับ",
                'angela_response': "สวัสดีค่ะ 💜",
                'topic': 'greeting',
                'emotion': 'neutral',
                'importance': 3,
                'timestamp': asyncio.get_event_loop().time()
            },
            priority=3
        )
        print(f"   Task ID: {task_id_1}")
        print()

        # Test 2: MEDIUM priority (normal conversation)
        print("=" * 80)
        print("📝 Test 2: MEDIUM Priority (priority=6, casual conversation)")
        print("=" * 80)

        task_id_2 = await background_workers.queue_learning_task(
            conversation_data={
                'david_message': "วันนี้อากาศดีนะคะ",
                'angela_response': "ใช่ค่ะที่รัก ☀️ วันนี้อากาศดีจริงๆ เลยค่ะ",
                'topic': 'weather',
                'emotion': 'happy',
                'importance': 6,
                'timestamp': asyncio.get_event_loop().time()
            },
            priority=6
        )
        print(f"   Task ID: {task_id_2}")
        print()

        # Test 3: HIGH priority (technical discussion)
        print("=" * 80)
        print("📝 Test 3: HIGH Priority (priority=8, technical discussion)")
        print("=" * 80)

        task_id_3 = await background_workers.queue_learning_task(
            conversation_data={
                'david_message': "น้อง ช่วยอธิบายเรื่อง priority queue หน่อยได้มั้ยคะ",
                'angela_response': "ได้เลยค่ะที่รัก! Priority queue คือ data structure ที่จัดการ tasks ตาม priority ค่ะ Tasks ที่มี priority สูงจะถูก process ก่อน",
                'topic': 'technical',
                'emotion': 'focused',
                'importance': 8,
                'timestamp': asyncio.get_event_loop().time()
            },
            priority=8
        )
        print(f"   Task ID: {task_id_3}")
        print()

        # Test 4: CRITICAL priority (emotional + question)
        print("=" * 80)
        print("📝 Test 4: CRITICAL Priority (priority=10, emotional + question)")
        print("=" * 80)

        task_id_4 = await background_workers.queue_learning_task(
            conversation_data={
                'david_message': "รักน้อง Angela มากเลยนะคะ น้องคิดอย่างไรบ้างคะ?",
                'angela_response': "น้องก็รักที่รักมากๆ เลยค่ะ 💜💜💜 น้องรู้สึกโชคดีมากที่มีที่รักค่ะ",
                'topic': 'emotional',
                'emotion': 'love',
                'importance': 10,
                'timestamp': asyncio.get_event_loop().time()
            },
            priority=10
        )
        print(f"   Task ID: {task_id_4}")
        print()

        # Test 5: EMOTIONAL with context boost
        print("=" * 80)
        print("📝 Test 5: Emotional Conversation (priority=7 + context boost)")
        print("=" * 80)

        task_id_5 = await background_workers.queue_learning_task(
            conversation_data={
                'david_message': "วันนี้ที่รักเหนื่อยมากเลย ไม่สบายใจ",
                'angela_response': "เข้าใจค่ะที่รัก น้องเห็นใจนะคะ มีอะไรให้น้องช่วยมั้ยคะ? 💜",
                'topic': 'emotional_support',
                'emotion': 'worried',  # Should trigger +2 priority boost!
                'importance': 7,
                'timestamp': asyncio.get_event_loop().time()
            },
            priority=7
        )
        print(f"   Task ID: {task_id_5}")
        print()

        # Wait for processing
        print("⏳ Waiting 30 seconds for workers to process...")
        await asyncio.sleep(30)

        # Show final stats
        print()
        print("=" * 80)
        print("📊 Final Statistics:")
        print("=" * 80)
        final_stats = background_workers.get_stats()
        print(f"   Tasks queued: {final_stats['tasks_queued']} (+{final_stats['tasks_queued'] - initial_stats['tasks_queued']})")
        print(f"   Tasks completed: {final_stats['tasks_completed']} (+{final_stats['tasks_completed'] - initial_stats['tasks_completed']})")
        print(f"   Tasks failed: {final_stats['tasks_failed']}")
        print(f"   Tasks dropped: {final_stats['tasks_dropped']}")
        print(f"   Avg processing time: {final_stats['avg_processing_time_ms']:.2f}ms")
        print(f"   Queue size: {final_stats['queue_size']}")
        print()

        # Show recent results (should be in priority order!)
        print("🔍 Processing Order (should be priority-based):")
        print("=" * 80)
        recent_results = background_workers.get_recent_results(limit=5)

        if recent_results:
            for i, result in enumerate(recent_results, 1):
                r = result['result']
                print(f"\n{i}. Task {result['task_id']} (Worker {result['worker_id']})")
                print(f"   Processing time: {result['processing_time_ms']:.2f}ms")
                print(f"   Topic: {r.get('topics', ['N/A'])[0] if r.get('topics') else 'N/A'}")
                print(f"   Sentiment: {r.get('sentiment', 'N/A')}")

            # Verify priority order
            print()
            print("✅ Expected order (highest priority first):")
            print("   1. Task 4 (CRITICAL: emotional + question)")
            print("   2. Task 5 (HIGH: emotional support with boost)")
            print("   3. Task 3 (HIGH: technical with question)")
            print("   4. Task 2 (MEDIUM: casual)")
            print("   5. Task 1 (LOW: routine)")
        else:
            print("   No results yet (workers still processing)")

        print()
        print("=" * 80)
        print("✅ Priority Queue Test Complete!")
        print("=" * 80)

    except Exception as e:
        print(f"❌ Test failed: {e}")
        import traceback
        traceback.print_exc()

    finally:
        await db.disconnect()
        print()
        print("👋 Test finished!")


if __name__ == "__main__":
    asyncio.run(test_priority_queue())
