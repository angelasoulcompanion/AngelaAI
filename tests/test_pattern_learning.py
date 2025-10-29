"""
🧪 Test Pattern Learning Service
"""

import asyncio
import sys
from pathlib import Path
from datetime import datetime, timedelta

sys.path.insert(0, str(Path(__file__).parent.parent))

from angela_core.services.pattern_learning_service import pattern_learning_service
from angela_core.services.memory_formation_service import memory_formation_service
from angela_core.database import db


async def test_pattern_learning():
    print("=" * 80)
    print("🧪 TESTING PATTERN LEARNING SERVICE")
    print("=" * 80)
    print()

    await db.connect()

    # First, create some similar memories to learn patterns from
    print("📍 SETUP: Creating similar memories for pattern learning...")

    # Similar pattern 1: David asking about technical topics (confusion → explanation)
    similar_interactions = [
        {
            "david": "น้อง งงๆ เลย ไม่เข้าใจเรื่อง vector embeddings",
            "angela": "น้องเห็นแล้วว่าที่รักรู้สึก confused ค่ะ ให้น้องอธิบายนะคะ...",
            "context": {"topic": "vector_embeddings", "emotion": "confused", "importance": 8}
        },
        {
            "david": "พี่ไม่ค่อยเข้าใจเรื่อง semantic search เลยค่ะ",
            "angela": "เข้าใจค่ะที่รัก น้องอธิบายให้ฟังนะคะ เรื่อง semantic search...",
            "context": {"topic": "semantic_search", "emotion": "confused", "importance": 8}
        },
        {
            "david": "อธิบายเรื่อง PostgreSQL pgvector หน่อยค่ะ พี่งง",
            "angela": "น้องเห็นว่าที่รักงงค่ะ มาอธิบายกันนะคะ pgvector คือ...",
            "context": {"topic": "pgvector", "emotion": "confused", "importance": 8}
        },
    ]

    for interaction in similar_interactions:
        await memory_formation_service.capture_interaction(
            david_message=interaction["david"],
            angela_response=interaction["angela"],
            context=interaction["context"]
        )
        print(f"  ✅ Created memory: {interaction['context']['topic']}")

    print(f"✅ Created {len(similar_interactions)} similar memories")
    print()

    # Test 1: Discover patterns
    print("📍 TEST 1: Discovering patterns from episodic memories...")
    patterns = await pattern_learning_service.discover_patterns(
        min_similarity=0.70,
        min_instances=2,  # Lower threshold for testing
        lookback_days=1
    )
    print(f"✅ Discovered {len(patterns)} patterns")
    for pattern in patterns:
        print(f"   Pattern: {pattern['name']}")
        print(f"     Instances: {pattern['instances']}")
        print(f"     Features: {pattern.get('features', {})}")
    print()

    if patterns:
        # Test 2: Recognize pattern from new input
        print("📍 TEST 2: Recognizing pattern from new input...")
        test_inputs = [
            "พี่ไม่เข้าใจเรื่อง database indexing เลย",
            "มีอะไรให้น้องช่วยมั้ยคะวันนี้",  # Should not match
        ]

        for test_input in test_inputs:
            matched = await pattern_learning_service.recognize_pattern(
                user_input=test_input,
                context={"source": "test"}
            )

            if matched:
                print(f"   Input: '{test_input[:50]}...'")
                print(f"   ✅ Matched pattern: {matched['pattern_name']}")
                print(f"   Confidence: {matched['confidence']:.2f}")
                response = str(matched.get('typical_response', 'N/A'))
                if len(response) > 80:
                    print(f"   Suggested response: {response[:80]}...")
                else:
                    print(f"   Suggested response: {response}")
            else:
                print(f"   Input: '{test_input[:50]}...'")
                print(f"   ❌ No pattern matched")
            print()

    # Test 3: Get statistics
    print("📍 TEST 3: Getting pattern learning statistics...")
    stats = await pattern_learning_service.get_pattern_stats()
    print("✅ Pattern Statistics:")
    for key, value in stats.items():
        if isinstance(value, float):
            print(f"   {key}: {value:.2f}")
        else:
            print(f"   {key}: {value}")
    print()

    await db.disconnect()

    print("=" * 80)
    print("✅ PATTERN LEARNING TEST COMPLETE!")
    print("=" * 80)


if __name__ == "__main__":
    asyncio.run(test_pattern_learning())
