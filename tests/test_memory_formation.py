"""
🧪 Test Memory Formation Service
"""

import asyncio
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from angela_core.services.memory_formation_service import memory_formation_service
from angela_core.database import db


async def test_memory_formation():
    print("=" * 80)
    print("🧪 TESTING MEMORY FORMATION SERVICE")
    print("=" * 80)
    print()

    await db.connect()

    # Test 1: Capture confusion interaction
    print("📍 TEST 1: Capturing confusion interaction...")
    formed1 = await memory_formation_service.capture_interaction(
        david_message="น้อง งงๆ เลย ไม่เข้าใจเรื่อง semantic search",
        angela_response="น้องเห็นแล้วว่าที่รักรู้สึกconfusedค่ะ น้องเข้าใจความรู้สึกนี้ค่ะ 💜 Semantic search คือการค้นหาด้วยความหมาย ไม่ใช่แค่ keyword ตรงๆ ค่ะ",
        context={
            'topic': 'semantic_search',
            'emotion': 'confused',
            'importance': 8
        }
    )
    print(f"✅ Formed memories: {list(formed1.keys())}")
    print()

    # Test 2: Capture praise (should trigger emotional conditioning)
    print("📍 TEST 2: Capturing praise interaction...")
    formed2 = await memory_formation_service.capture_interaction(
        david_message="ที่รักเก่งมากๆ ค่ะ ระบบดีมาก",
        angela_response="ขอบคุณมากค่ะที่รัก 💜 น้องดีใจมากที่ได้ช่วยที่รักค่ะ",
        context={
            'topic': 'praise',
            'emotion': 'grateful',
            'importance': 9
        }
    )
    print(f"✅ Formed memories: {list(formed2.keys())}")
    print()

    # Test 3: Capture gratitude
    print("📍 TEST 3: Capturing gratitude interaction...")
    formed3 = await memory_formation_service.capture_interaction(
        david_message="ขอบคุณมากนะน้อง ช่วยเหลือดีมาก",
        angela_response="ยินดีมากค่ะที่รัก 💜 น้องก็ขอบคุณที่รักที่ไว้ใจน้องค่ะ",
        context={
            'topic': 'gratitude',
            'emotion': 'grateful',
            'importance': 8
        }
    )
    print(f"✅ Formed memories: {list(formed3.keys())}")
    print()

    # Check what was created in database
    print("=" * 80)
    print("📊 CHECKING DATABASE")
    print("=" * 80)

    async with db.acquire() as conn:
        # Count episodic memories
        episodic_count = await conn.fetchval("SELECT COUNT(*) FROM episodic_memories")
        print(f"✅ Episodic memories: {episodic_count}")

        # Count semantic memories
        semantic_count = await conn.fetchval("SELECT COUNT(*) FROM semantic_memories")
        print(f"✅ Semantic memories: {semantic_count}")

        # Count emotional conditioning
        conditioning_count = await conn.fetchval("SELECT COUNT(*) FROM emotional_conditioning")
        print(f"✅ Emotional conditioning: {conditioning_count}")

        # Count procedural memories
        procedural_count = await conn.fetchval("SELECT COUNT(*) FROM procedural_memories")
        print(f"✅ Procedural memories: {procedural_count}")

        # Show latest episodic memory
        print()
        print("=" * 80)
        print("📝 LATEST EPISODIC MEMORY")
        print("=" * 80)
        latest = await conn.fetchrow("""
            SELECT memory_id, event_content, tags, process_metadata,
                   emotional_intensity, importance_level
            FROM episodic_memories
            ORDER BY created_at DESC
            LIMIT 1
        """)

        if latest:
            import json
            print(f"Memory ID: {latest['memory_id']}")
            print(f"Emotional Intensity: {latest['emotional_intensity']}")
            print(f"Importance Level: {latest['importance_level']}")
            print()
            print("Event Content:")
            content = json.loads(latest['event_content'])
            print(f"  Event: {content['event']}")
            print(f"  What happened: {content['what_happened'][:80]}...")
            print()
            print("Tags:")
            tags = json.loads(latest['tags'])
            print(f"  Emotion tags: {tags.get('emotion_tags', [])}")
            print(f"  Topic tags: {tags.get('topic_tags', [])}")
            print()
            print("Process Metadata:")
            process = json.loads(latest['process_metadata'])
            print(f"  Formed via: {process['formed_via']}")
            print(f"  Capture trigger: {process['capture_trigger']}")
            print(f"  Confidence: {process['capture_confidence']}")
            print(f"  Reasoning: {process['reasoning']}")

    await db.disconnect()

    print()
    print("=" * 80)
    print("✅ TEST COMPLETE!")
    print("=" * 80)


if __name__ == "__main__":
    asyncio.run(test_memory_formation())
