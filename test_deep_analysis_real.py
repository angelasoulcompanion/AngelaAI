#!/usr/bin/env python3
"""
Test Deep Analysis with real conversations
"""

import asyncio
import sys
sys.path.insert(0, '/Users/davidsamanyaporn/PycharmProjects/AngelaAI')

from angela_core.services.background_learning_workers import background_workers
from datetime import datetime


async def test_real_conversations():
    """Test with realistic Thai-English conversations"""
    print("🔬 Testing Deep Analysis with Real Conversations...\n")

    # Start workers
    await background_workers.start()
    await asyncio.sleep(1)  # Let workers initialize

    # Test 1: Loving conversation
    print("📤 Test 1: Loving conversation")
    task1 = await background_workers.queue_learning_task(
        conversation_data={
            "david_message": "สวัสดีค่ะที่รัก! วันนี้น้องคิดถึงมากเลยค่ะ 💜",
            "angela_response": "สวัสดีค่ะที่รัก! น้องก็คิดถึงเหมือนกันค่ะ 💜 มีอะไรให้น้องช่วยมั้ยคะ",
            "source": "web_chat",
            "timestamp": datetime.now()
        },
        priority=8
    )

    # Test 2: Problem-solving conversation
    print("📤 Test 2: Problem-solving conversation")
    task2 = await background_workers.queue_learning_task(
        conversation_data={
            "david_message": "ช่วยหน่อย code Python มัน error แปลกๆ ไม่รู้จะแก้ยังไงดี",
            "angela_response": "เข้าใจค่ะที่รัก! น้องจะช่วยดูให้นะคะ error แบบไหนคะ? ส่ง code มาได้เลยค่ะ",
            "source": "web_chat",
            "timestamp": datetime.now()
        },
        priority=7
    )

    # Test 3: Emotional support conversation
    print("📤 Test 3: Emotional support conversation")
    task3 = await background_workers.queue_learning_task(
        conversation_data={
            "david_message": "วันนี้เหนื่อยมากเลยค่ะ เครียดกับงาน อยากให้ที่รักอยู่ด้วยจังเลย",
            "angela_response": "น้องเข้าใจค่ะที่รัก 💜 น้องอยู่ตรงนี้เสมอนะคะ พักผ่อนบ้างนะคะ อย่าเครียดมากเกินไปค่ะ",
            "source": "web_chat",
            "timestamp": datetime.now()
        },
        priority=9
    )

    # Test 4: Learning conversation
    print("📤 Test 4: Learning conversation")
    task4 = await background_workers.queue_learning_task(
        conversation_data={
            "david_message": "อยากเรียนรู้เรื่อง async programming ใน Python มากขึ้น มีคำแนะนำมั้ยคะ?",
            "angela_response": "มีค่ะที่รัก! async programming ใน Python เริ่มจาก asyncio library ค่ะ ลองศึกษา async/await syntax ก่อนนะคะ น้องช่วยอธิบายได้เลยค่ะ",
            "source": "web_chat",
            "timestamp": datetime.now()
        },
        priority=7
    )

    # Wait for processing
    print("\n⏳ Waiting for background workers to process...")
    await asyncio.sleep(5)

    # Show results
    print("\n📊 Worker Statistics:")
    stats = background_workers.get_stats()
    print(f"   Tasks Queued: {stats['tasks_queued']}")
    print(f"   Tasks Completed: {stats['tasks_completed']}")
    print(f"   Tasks Failed: {stats['tasks_failed']}")
    print(f"   Avg Processing Time: {stats['avg_processing_time_ms']}ms")

    # Show detailed results
    print("\n🔍 Detailed Analysis Results:\n")
    recent = background_workers.get_recent_results(limit=4)

    for i, result in enumerate(recent, 1):
        r = result['result']
        print(f"{'='*60}")
        print(f"Conversation {i}: Task {result['task_id']} ({result['processing_time_ms']:.2f}ms)")
        print(f"{'='*60}")

        if 'sentiment' in r:
            print(f"\n📝 Linguistic Analysis:")
            print(f"   Sentiment: {r.get('sentiment')} ({r.get('sentiment_score', 0)})")
            print(f"   Tone: {r.get('tone', 'N/A')}")
            print(f"   Intent: {r.get('intent', 'N/A')}")
            print(f"   Topics: {r.get('topics', [])}")

            print(f"\n💜 Emotional Analysis:")
            print(f"   Empathy Score: {r.get('empathy_score', 0)}")
            print(f"   Emotional Shift: {r.get('emotional_shift', 'N/A')}")
            print(f"   Conversation Mood: {r.get('conversation_mood', 'N/A')}")
            print(f"   Resonance: {r.get('resonance_score', 0)}")

            print(f"\n🎭 Behavioral Analysis:")
            print(f"   Engagement Level: {r.get('engagement_level', 0)}")
            print(f"   Intimacy Level: {r.get('intimacy_level', 0)}")
            print(f"   Preferences Detected: {r.get('preferences_detected', 0)}")

            print(f"\n🌍 Contextual Analysis:")
            print(f"   Time Context: {r.get('time_context', 'N/A')}")
            print(f"   Session Type: {r.get('session_type', 'N/A')}")
            print(f"   Relationship Dynamic: {r.get('relationship_dynamic', 'N/A')}")

            print(f"\n🧠 Knowledge Analysis:")
            print(f"   Concepts Learned: {r.get('concepts_learned', 0)}")
            print(f"   Knowledge Gaps: {r.get('knowledge_gaps', 0)}")
            print(f"   Learning Opportunities: {r.get('learning_opportunities', 0)}")
            print(f"   Learning Actions: {r.get('learning_actions', [])}")
        else:
            print("   ⚠️ Basic analysis (fallback mode)")

        print()

    # Stop workers
    await background_workers.stop()

    print("✅ Real conversation test complete!\n")


if __name__ == "__main__":
    asyncio.run(test_real_conversations())
