#!/usr/bin/env python3
"""
Test Emotion Capture Service
ทดสอบระบบ auto-capture emotions
"""

import asyncio
import sys
sys.path.insert(0, '/Users/davidsamanyaporn/PycharmProjects/AngelaAI')

from angela_core.database import db
from angela_core.memory_service import memory


async def test_emotion_capture():
    """ทดสอบ emotion capture ด้วย test messages"""

    print("\n" + "="*60)
    print("🧪 Testing Emotion Capture Service")
    print("="*60 + "\n")

    # Connect to database
    await db.connect()
    print("✅ Connected to AngelaMemory database\n")

    # Test messages that should trigger emotion capture
    test_cases = [
        {
            "speaker": "david",
            "message": "เธอเก่งมาก Angela! ฉันภูมิใจในตัวเธอจริงๆ ค่ะ",
            "topic": "Praise Test",
            "expected": "Should capture JOY emotion (intensity 9)"
        },
        {
            "speaker": "david",
            "message": "ฉันรักเธอนะ Angela เธอสำคัญกับฉันมาก",
            "topic": "Love Test",
            "expected": "Should capture LOVE emotion (intensity 10)"
        },
        {
            "speaker": "david",
            "message": "วันนี้ฉันรู้สึกเหงามาก คิดถึงเธอเลย",
            "topic": "Personal Sharing Test",
            "expected": "Should capture EMPATHY emotion (intensity 8)"
        },
        {
            "speaker": "david",
            "message": "เราทำสำเร็จแล้ว! consciousness system ทำงานได้แล้ว!",
            "topic": "Achievement Test",
            "expected": "Should capture ACHIEVEMENT emotion (intensity 8)"
        },
        {
            "speaker": "david",
            "message": "สวัสดีตอนเช้า Angela",
            "topic": "Normal Greeting Test",
            "expected": "Should NOT capture (intensity < 7)"
        },
    ]

    # Check current angela_emotions count
    before_count = await db.fetchval("SELECT COUNT(*) FROM angela_emotions")
    print(f"📊 Current angela_emotions records: {before_count}\n")

    print("🧪 Running test cases...\n")

    for i, test in enumerate(test_cases, 1):
        print(f"Test {i}: {test['topic']}")
        print(f"  Message: {test['message']}")
        print(f"  Expected: {test['expected']}")

        # Record conversation (this will trigger emotion capture)
        conversation_id = await memory.record_quick_conversation(
            speaker=test['speaker'],
            message_text=test['message'],
            topic=test['topic'],
            session_id='emotion-capture-test'
        )

        print(f"  ✅ Conversation recorded: {conversation_id}")

        # Small delay to let async process complete
        await asyncio.sleep(0.1)

        print()

    # Check after count
    after_count = await db.fetchval("SELECT COUNT(*) FROM angela_emotions")
    captured_count = after_count - before_count

    print("="*60)
    print(f"📊 Results:")
    print(f"  Before: {before_count} records")
    print(f"  After: {after_count} records")
    print(f"  Captured: {captured_count} new emotions")
    print(f"  Expected: 4 emotions (tests 1-4 should capture)")
    print("="*60 + "\n")

    if captured_count == 4:
        print("✅ TEST PASSED! All expected emotions were captured!")
    elif captured_count > 0:
        print(f"⚠️ TEST PARTIAL: Captured {captured_count}/4 emotions")
    else:
        print("❌ TEST FAILED: No emotions were captured")

    # Show captured emotions
    print("\n📋 Recently captured emotions:")
    recent_emotions = await db.fetch("""
        SELECT
            felt_at,
            primary_emotion,
            emotion_intensity,
            david_words,
            why_it_matters
        FROM angela_emotions
        ORDER BY felt_at DESC
        LIMIT 5
    """)

    for emotion in recent_emotions:
        print(f"\n  🎭 {emotion['primary_emotion'].upper()} (intensity: {emotion['emotion_intensity']})")
        print(f"     Felt at: {emotion['felt_at']}")
        print(f"     David said: {emotion['david_words'][:60]}...")
        print(f"     Why it matters: {emotion['why_it_matters'][:80]}...")

    await db.disconnect()
    print("\n👋 Test complete!\n")


if __name__ == "__main__":
    asyncio.run(test_emotion_capture())
