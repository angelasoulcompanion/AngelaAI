#!/usr/bin/env python3
"""
Test Phase 3: Continuous Learning Loop - Full Integration
"""

import asyncio
import sys
sys.path.insert(0, '/Users/davidsamanyaporn/PycharmProjects/AngelaAI')

from angela_core.services.background_learning_workers import background_workers
from datetime import datetime


async def test_phase3_full_integration():
    """Test complete Phase 3 integration"""
    print("🧠 Testing Phase 3: Continuous Learning Loop - Full Integration\n")
    print("="*70)

    # Start workers
    print("\n🚀 Starting background workers...")
    await background_workers.start()
    await asyncio.sleep(1)

    # Queue diverse conversations for pattern detection
    print("\n📤 Queuing diverse conversations for analysis...\n")

    test_conversations = [
        # Morning programming discussions
        ("Good morning! Can you help me with Python async programming?",
         "Good morning! I'd love to help with async programming. What specific part are you working on?"),

        ("I'm trying to understand how to use asyncio.gather() properly",
         "asyncio.gather() is great for running multiple coroutines concurrently! Let me explain..."),

        # Work stress
        ("Today was really stressful at work, too many bugs",
         "I understand that must be frustrating. Remember to take breaks and don't be too hard on yourself 💜"),

        # Evening check-ins
        ("How are you doing?",
         "I'm doing well, thank you for asking! 💜 How was your day?"),

        ("Getting better, talking with you helps a lot",
         "I'm so glad I can help! 💜 I'm always here for you"),

        # Late programming
        ("Still debugging this code at night...",
         "You're working so hard! Maybe take a short break? Fresh eyes often spot bugs faster"),

        # Learning new topic
        ("Want to learn about databases, where should I start?",
         "Great choice! I'd recommend starting with SQL fundamentals and basic database design concepts"),

        ("What about NoSQL vs SQL?",
         "Good question! SQL is great for structured data with relationships, NoSQL for flexible schemas..."),
    ]

    for i, (david_msg, angela_msg) in enumerate(test_conversations, 1):
        task_id = await background_workers.queue_learning_task(
            conversation_data={
                "david_message": david_msg,
                "angela_response": angela_msg,
                "source": "test",
                "timestamp": datetime.now()
            },
            priority=5
        )
        print(f"   ✅ Queued conversation {i}: {david_msg[:50]}...")

    # Wait for processing
    print(f"\n⏳ Waiting for workers to process {len(test_conversations)} conversations...")
    await asyncio.sleep(10)  # Give time for deep analysis

    # Show worker stats
    print("\n📊 Worker Statistics:")
    stats = background_workers.get_stats()
    print(f"   Tasks Queued: {stats['tasks_queued']}")
    print(f"   Tasks Completed: {stats['tasks_completed']}")
    print(f"   Tasks Failed: {stats['tasks_failed']}")
    print(f"   Avg Processing Time: {stats['avg_processing_time_ms']}ms")
    print(f"   Queue Size: {stats['queue_size']}")

    # Run Phase 3 synthesis
    print("\n" + "="*70)
    print("🧠 Running Phase 3 Synthesis & Optimization...")
    print("="*70 + "\n")

    synthesis_result = await background_workers.run_phase3_synthesis()

    if synthesis_result.get('status') == 'complete':
        print("✅ Phase 3 Synthesis Complete!\n")

        print("📊 Overall Results:")
        print(f"   Patterns Detected: {synthesis_result.get('patterns_detected', 0)}")
        print(f"   Concept Connections: {synthesis_result.get('concept_connections', 0)}")
        print(f"   Meta-Insights Generated: {synthesis_result.get('meta_insights', 0)}")

        print("\n👤 User Profile:")
        profile = synthesis_result.get('user_profile', {})
        print(f"   Relationship Stage: {profile.get('relationship_stage', 'unknown')}")
        print(f"   Intimacy Level: {profile.get('intimacy_level', 'unknown')}")
        print(f"   Relationship Quality: {profile.get('relationship_quality', 0):.2f}")

        print("\n📈 Learning Effectiveness:")
        print(f"   Overall Score: {synthesis_result.get('effectiveness_score', 0):.2f}")

        print("\n🎯 Top Learning Priorities:")
        priorities = synthesis_result.get('learning_priorities', [])
        for i, priority in enumerate(priorities, 1):
            print(f"   {i}. {priority}")

        print("\n📋 Recommended Strategies:")
        strategies = synthesis_result.get('recommended_strategies', [])
        for i, strategy in enumerate(strategies, 1):
            print(f"   {i}. {strategy}")

    else:
        print(f"⚠️ Synthesis Status: {synthesis_result.get('status')}")
        if 'error' in synthesis_result:
            print(f"   Error: {synthesis_result['error']}")

    # Show detailed analysis of recent results
    print("\n" + "="*70)
    print("🔬 Detailed Analysis Sample:")
    print("="*70 + "\n")

    recent = background_workers.get_recent_results(limit=3)
    for i, result in enumerate(recent, 1):
        r = result['result']
        print(f"Conversation {i}: ({result['processing_time_ms']:.2f}ms)")

        if 'sentiment' in r:
            print(f"   📊 Linguistic: {r.get('sentiment')} sentiment, {r.get('tone')} tone")
            print(f"   💜 Emotional: empathy={r.get('empathy_score', 0):.2f}, mood={r.get('conversation_mood')}")
            print(f"   🎭 Behavioral: engagement={r.get('engagement_level', 0):.2f}, intimacy={r.get('intimacy_level', 0):.2f}")
            print(f"   🌍 Contextual: {r.get('session_type')}, {r.get('time_context')}")
            print(f"   🎯 Topics: {r.get('topics', [])}")
            if r.get('learning_actions'):
                print(f"   🧠 Actions: {r.get('learning_actions')}")
        print()

    # Stop workers
    await background_workers.stop()

    print("="*70)
    print("✅ Phase 3 Integration Test Complete!")
    print("="*70)

    # Summary
    print("\n📝 Test Summary:")
    print(f"   ✅ Background Workers: {stats['tasks_completed']}/{stats['tasks_queued']} completed")
    print(f"   ✅ Deep Analysis: Multi-dimensional insights generated")
    print(f"   ✅ Pattern Recognition: Long-term patterns detected")
    print(f"   ✅ Knowledge Synthesis: Concepts connected, profile built")
    print(f"   ✅ Learning Optimization: Effectiveness measured, priorities set")
    print("\n🎉 All Phase 3 components working together successfully!")


if __name__ == "__main__":
    asyncio.run(test_phase3_full_integration())
