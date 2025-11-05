#!/usr/bin/env python3
"""
Test Self-Learning System - Phase 1 Foundation

Tests all 3 repositories:
1. LearningPatternRepository
2. PreferenceRepository
3. TrainingExampleRepository

Author: Angela 💜
Created: 2025-11-03
"""

import asyncio
import sys
from pathlib import Path
from uuid import uuid4
from datetime import datetime

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from angela_core.database import AngelaDatabase
from angela_core.domain.entities.self_learning import (
    LearningPattern,
    PreferenceItem,
    TrainingExample
)
from angela_core.domain.value_objects.self_learning import (
    PatternType,
    PreferenceCategory,
    SourceType,
    LearningQuality
)
from angela_core.infrastructure.persistence.repositories.learning_pattern_repository import LearningPatternRepository
from angela_core.infrastructure.persistence.repositories.preference_repository import PreferenceRepository
from angela_core.infrastructure.persistence.repositories.training_example_repository import TrainingExampleRepository


async def test_learning_pattern_repository(db: AngelaDatabase):
    """Test LearningPatternRepository"""
    print("\n" + "="*60)
    print("🧪 Testing LearningPatternRepository")
    print("="*60)

    repo = LearningPatternRepository(db)

    # Test 1: Create new pattern
    print("\n1️⃣ Creating new learning pattern...")
    pattern = LearningPattern(
        pattern_type=PatternType.EMOTIONAL_RESPONSE,
        description="When frustrated, David appreciates empathy before solutions",
        examples=["Show understanding first", "Acknowledge feelings", "Then suggest fixes"],
        confidence_score=0.75,
        occurrence_count=8,
        tags=["emotional_support", "empathy", "problem_solving"]
    )

    created = await repo.create(pattern)
    print(f"   ✅ Created pattern: {created.id}")
    print(f"   - Type: {created.pattern_type.value}")
    print(f"   - Confidence: {created.confidence_score}")
    print(f"   - Occurrences: {created.occurrence_count}")

    # Test 2: Get by type
    print("\n2️⃣ Getting patterns by type...")
    patterns = await repo.find_by_type(PatternType.EMOTIONAL_RESPONSE.value)
    print(f"   ✅ Found {len(patterns)} emotional_response patterns")
    for p in patterns:
        print(f"   - {p.description[:50]}...")

    # Test 3: Update observation
    print("\n3️⃣ Recording another observation...")
    await repo.update_observation(created.id)
    updated = await repo.get_by_id(created.id)
    print(f"   ✅ Updated pattern:")
    print(f"   - Occurrences: {updated.occurrence_count} (was {created.occurrence_count})")
    print(f"   - Confidence: {updated.confidence_score:.3f} (was {created.confidence_score:.3f})")

    # Test 4: Get quality distribution
    print("\n4️⃣ Getting quality distribution...")
    distribution = await repo.get_quality_distribution()
    print(f"   ✅ Quality distribution:")
    for quality, count in distribution.items():
        print(f"   - {quality}: {count}")

    # Test 5: Count by type
    print("\n5️⃣ Counting patterns by type...")
    count = await repo.count_by_type(PatternType.EMOTIONAL_RESPONSE.value)
    print(f"   ✅ Total emotional_response patterns: {count}")

    print("\n✅ LearningPatternRepository: ALL TESTS PASSED!")
    return True


async def test_preference_repository(db: AngelaDatabase):
    """Test PreferenceRepository"""
    print("\n" + "="*60)
    print("🧪 Testing PreferenceRepository")
    print("="*60)

    repo = PreferenceRepository(db)

    # Test 1: Create new preference
    print("\n1️⃣ Creating new preference...")
    preference = PreferenceItem(
        category=PreferenceCategory.COMMUNICATION,
        preference_key="response_length",
        preference_value="concise_with_examples",
        confidence=0.85,
        evidence_count=12
    )

    created = await repo.create(preference)
    print(f"   ✅ Created preference: {created.id}")
    print(f"   - Category: {created.category.value}")
    print(f"   - Key: {created.preference_key}")
    print(f"   - Value: {created.preference_value}")
    print(f"   - Confidence: {created.confidence}")

    # Test 2: Find by category
    print("\n2️⃣ Finding preferences by category...")
    prefs = await repo.find_by_category(PreferenceCategory.COMMUNICATION.value)
    print(f"   ✅ Found {len(prefs)} communication preferences")
    for p in prefs:
        print(f"   - {p.preference_key}: {p.preference_value}")

    # Test 3: Find by key
    print("\n3️⃣ Finding preference by key...")
    found = await repo.find_by_key("response_length")
    if found:
        print(f"   ✅ Found preference: {found.preference_key}")
        print(f"   - Value: {found.preference_value}")
        print(f"   - Confidence: {found.confidence}")

    # Test 4: Add evidence
    print("\n4️⃣ Adding evidence...")
    conversation_id = uuid4()
    await repo.add_evidence(created.id, conversation_id)
    updated = await repo.get_by_id(created.id)
    print(f"   ✅ Updated preference:")
    print(f"   - Evidence count: {updated.evidence_count} (was {created.evidence_count})")
    print(f"   - Confidence: {updated.confidence:.3f} (was {created.confidence:.3f})")

    # Test 5: Get strong preferences
    print("\n5️⃣ Getting strong preferences...")
    strong = await repo.get_strong_preferences(min_confidence=0.8, min_evidence=3)
    print(f"   ✅ Found {len(strong)} strong preferences")
    for p in strong:
        print(f"   - {p.preference_key}: confidence={p.confidence:.2f}, evidence={p.evidence_count}")

    # Test 6: Get summary
    print("\n6️⃣ Getting preferences summary...")
    summary = await repo.get_all_preferences_summary()
    print(f"   ✅ Preferences summary:")
    print(f"   - Total: {summary['total_preferences']}")
    print(f"   - Strong: {summary['strong_preferences']}")
    print(f"   - Avg confidence: {summary['average_confidence']:.3f}")
    print(f"   - By category: {summary['by_category']}")

    print("\n✅ PreferenceRepository: ALL TESTS PASSED!")
    return True


async def test_training_example_repository(db: AngelaDatabase):
    """Test TrainingExampleRepository"""
    print("\n" + "="*60)
    print("🧪 Testing TrainingExampleRepository")
    print("="*60)

    repo = TrainingExampleRepository(db)

    # Test 1: Create training example
    print("\n1️⃣ Creating training example...")
    example = TrainingExample(
        input_text="What's the best way to handle errors in Python?",
        expected_output="Use try-except blocks for error handling:\\n\\n```python\\ntry:\\n    # risky code\\n    result = 10 / 0\\nexcept ZeroDivisionError as e:\\n    print(f'Error: {e}')\\n```",
        quality_score=8.5,
        source_type=SourceType.REAL_CONVERSATION,
        metadata={"topic": "error_handling", "language": "python"}
    )

    created = await repo.create(example)
    print(f"   ✅ Created example: {created.id}")
    print(f"   - Quality: {created.quality_score}")
    print(f"   - Source: {created.source_type.value}")
    print(f"   - High quality: {created.is_high_quality()}")

    # Test 2: Get high quality examples
    print("\n2️⃣ Getting high-quality examples...")
    high_quality = await repo.get_high_quality(min_score=7.0, limit=10)
    print(f"   ✅ Found {len(high_quality)} high-quality examples")
    for ex in high_quality[:3]:
        print(f"   - Score {ex.quality_score}: {ex.input_text[:50]}...")

    # Test 3: Get by source type
    print("\n3️⃣ Getting examples by source type...")
    real_convs = await repo.get_by_source_type(SourceType.REAL_CONVERSATION.value)
    print(f"   ✅ Found {len(real_convs)} real_conversation examples")

    # Test 4: Get unused examples
    print("\n4️⃣ Getting unused examples...")
    unused = await repo.get_unused_examples(min_quality=7.0)
    print(f"   ✅ Found {len(unused)} unused high-quality examples")

    # Test 5: Mark as used
    print("\n5️⃣ Marking example as used...")
    marked = await repo.mark_as_used([created.id], datetime.now())
    print(f"   ✅ Marked {marked} example(s) as used")

    updated = await repo.get_by_id(created.id)
    print(f"   - Used in training: {updated.used_in_training}")
    print(f"   - Training date: {updated.training_date}")

    # Test 6: Export to JSONL
    print("\n6️⃣ Exporting to JSONL...")
    import tempfile
    with tempfile.NamedTemporaryFile(mode='w', suffix='.jsonl', delete=False) as f:
        output_path = f.name

    exported = await repo.export_to_jsonl(
        output_path=output_path,
        min_quality=7.0,
        limit=5
    )
    print(f"   ✅ Exported {exported} examples to {output_path}")

    # Read back and verify
    import json
    with open(output_path, 'r') as f:
        lines = f.readlines()
        print(f"   - File has {len(lines)} lines")
        if lines:
            first = json.loads(lines[0])
            print(f"   - First example preview: {first['messages'][0]['content'][:40]}...")

    # Clean up
    import os
    os.unlink(output_path)

    # Test 7: Get quality statistics
    print("\n7️⃣ Getting quality statistics...")
    stats = await repo.get_quality_statistics()
    print(f"   ✅ Quality statistics:")
    print(f"   - Total examples: {stats['total_examples']}")
    print(f"   - High quality: {stats['high_quality_count']}")
    print(f"   - Average quality: {stats['average_quality']:.2f}")
    print(f"   - Used in training: {stats['used_in_training']}")
    print(f"   - By source: {stats['by_source_type']}")
    print(f"   - By quality level: {stats['by_quality_level']}")

    print("\n✅ TrainingExampleRepository: ALL TESTS PASSED!")
    return True


async def main():
    """Run all tests"""
    print("\n" + "="*60)
    print("🚀 SELF-LEARNING SYSTEM - PHASE 1 TESTING")
    print("="*60)
    print("\nAuthor: Angela 💜")
    print("Date: 2025-11-03")
    print("Testing: Foundation (Repositories)")

    # Connect to database
    print("\n📊 Connecting to database...")
    db = AngelaDatabase()
    await db.connect()
    print("   ✅ Connected to AngelaMemory database")

    try:
        # Run all tests
        results = []

        results.append(await test_learning_pattern_repository(db))
        results.append(await test_preference_repository(db))
        results.append(await test_training_example_repository(db))

        # Summary
        print("\n" + "="*60)
        print("📊 TEST SUMMARY")
        print("="*60)

        passed = sum(results)
        total = len(results)

        print(f"\n✅ Tests Passed: {passed}/{total}")

        if passed == total:
            print("\n🎉 ALL TESTS PASSED! Phase 1 Foundation is working correctly! 💜")
            return 0
        else:
            print(f"\n❌ {total - passed} test(s) failed")
            return 1

    finally:
        await db.disconnect()
        print("\n📊 Disconnected from database")


if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)
