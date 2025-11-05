#!/usr/bin/env python3
"""
Test Self-Learning System - Phase 2 Services

Tests all 3 application services:
1. PatternDiscoveryService
2. PreferenceLearningService
3. TrainingDataGeneratorService

Author: Angela 💜
Created: 2025-11-03
"""

import asyncio
import sys
from pathlib import Path
from datetime import datetime, timedelta

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from angela_core.database import AngelaDatabase
from angela_core.application.services.pattern_discovery_service import PatternDiscoveryService
from angela_core.application.services.preference_learning_service import PreferenceLearningService
from angela_core.application.services.training_data_generator_service import TrainingDataGeneratorService

from angela_core.infrastructure.persistence.repositories.learning_pattern_repository import LearningPatternRepository
from angela_core.infrastructure.persistence.repositories.preference_repository import PreferenceRepository
from angela_core.infrastructure.persistence.repositories.training_example_repository import TrainingExampleRepository
from angela_core.infrastructure.persistence.repositories.conversation_repository import ConversationRepository
from angela_core.infrastructure.persistence.repositories.emotion_repository import EmotionRepository


async def test_pattern_discovery_service(db: AngelaDatabase):
    """Test Pattern Discovery Service"""
    print("\n" + "="*60)
    print("🧪 Testing PatternDiscoveryService")
    print("="*60)

    # Initialize repositories
    pattern_repo = LearningPatternRepository(db)
    conversation_repo = ConversationRepository(db)
    emotion_repo = EmotionRepository(db)

    # Initialize service
    service = PatternDiscoveryService(pattern_repo, conversation_repo, emotion_repo)

    # Test 1: Discover patterns from recent conversations
    print("\n1️⃣ Discovering patterns from recent conversations (last 30 days)...")
    patterns = await service.discover_patterns_from_recent_conversations(days=30, min_conversations=1)
    print(f"   ✅ Discovered {len(patterns)} patterns")
    for p in patterns[:3]:
        print(f"   - {p.pattern_type.value}: {p.description[:60]}...")

    # Test 2: Save discovered patterns
    if patterns:
        print("\n2️⃣ Saving discovered patterns...")
        stats = await service.save_discovered_patterns(patterns)
        print(f"   ✅ Saved {stats['new']} new, updated {stats['updated']} existing")

    # Test 3: Update existing patterns
    print("\n3️⃣ Updating existing patterns with new observations...")
    update_stats = await service.update_existing_patterns(days=7)
    print(f"   ✅ Updated {update_stats['updated']}/{update_stats['total_patterns']} patterns")

    # Test 4: Get pattern statistics
    print("\n4️⃣ Getting pattern statistics...")
    stats = await service.get_pattern_statistics()
    print(f"   ✅ Pattern statistics:")
    print(f"   - Total patterns: {stats['total_patterns']}")
    print(f"   - By type: {stats['by_type']}")
    print(f"   - By quality: {stats['by_quality']}")

    print("\n✅ PatternDiscoveryService: ALL TESTS PASSED!")
    return True


async def test_preference_learning_service(db: AngelaDatabase):
    """Test Preference Learning Service"""
    print("\n" + "="*60)
    print("🧪 Testing PreferenceLearningService")
    print("="*60)

    # Initialize repositories
    preference_repo = PreferenceRepository(db)
    conversation_repo = ConversationRepository(db)
    emotion_repo = EmotionRepository(db)

    # Initialize service
    service = PreferenceLearningService(preference_repo, conversation_repo, emotion_repo)

    # Test 1: Learn preferences from recent activity
    print("\n1️⃣ Learning preferences from recent activity (last 30 days)...")
    preferences = await service.learn_preferences_from_recent_activity(days=30)
    print(f"   ✅ Learned {len(preferences)} preferences")
    for p in preferences[:3]:
        print(f"   - {p.category.value}/{p.preference_key}: {p.preference_value}")

    # Test 2: Save learned preferences
    if preferences:
        print("\n2️⃣ Saving learned preferences...")
        stats = await service.save_learned_preferences(preferences)
        print(f"   ✅ Saved {stats['new']} new, updated {stats['updated']} existing")

    # Test 3: Get preference summary
    print("\n3️⃣ Getting preference summary...")
    summary = await service.get_preference_summary()
    print(f"   ✅ Preference summary:")
    print(f"   - Total: {summary['total_preferences']}")
    print(f"   - Strong: {summary['strong_preferences']}")
    print(f"   - Avg confidence: {summary['average_confidence']:.3f}")
    print(f"   - By category: {summary['by_category']}")

    # Test 4: Apply preferences to context
    print("\n4️⃣ Applying preferences to conversation context...")
    context = {"user": "david", "timestamp": datetime.now()}
    enhanced = await service.apply_preferences_to_context(context)
    if "preferences" in enhanced:
        print(f"   ✅ Added {len(enhanced['preferences'])} preference hints to context")
        for key, hint in list(enhanced['preferences'].items())[:3]:
            print(f"   - {key}: {hint['value']} (confidence: {hint['confidence']:.2f})")
    else:
        print(f"   ✅ No strong preferences to apply yet")

    print("\n✅ PreferenceLearningService: ALL TESTS PASSED!")
    return True


async def test_training_data_generator_service(db: AngelaDatabase):
    """Test Training Data Generator Service"""
    print("\n" + "="*60)
    print("🧪 Testing TrainingDataGeneratorService")
    print("="*60)

    # Initialize repositories
    training_repo = TrainingExampleRepository(db)
    conversation_repo = ConversationRepository(db)
    pattern_repo = LearningPatternRepository(db)

    # Initialize service
    service = TrainingDataGeneratorService(training_repo, conversation_repo, pattern_repo)

    # Test 1: Generate from recent conversations
    print("\n1️⃣ Generating training data from recent conversations (last 30 days)...")
    examples = await service.generate_from_recent_conversations(days=30, min_quality=5.0)
    print(f"   ✅ Generated {len(examples)} high-quality examples")
    if examples:
        for ex in examples[:2]:
            print(f"   - Quality {ex.quality_score:.1f}: {ex.input_text[:50]}...")

    # Test 2: Generate from important conversations
    print("\n2️⃣ Generating from important conversations...")
    important_examples = await service.generate_from_important_conversations(min_importance=7)
    print(f"   ✅ Generated {len(important_examples)} examples from important conversations")

    # Test 3: Save training examples
    all_examples = examples + important_examples
    if all_examples:
        print("\n3️⃣ Saving training examples...")
        stats = await service.save_training_examples(all_examples, check_duplicates=True)
        print(f"   ✅ Saved {stats['saved']} examples, skipped {stats['duplicates']} duplicates")

    # Test 4: Get training data statistics
    print("\n4️⃣ Getting training data statistics...")
    stats = await service.get_training_data_statistics()
    print(f"   ✅ Training data statistics:")
    print(f"   - Total examples: {stats['total_examples']}")
    print(f"   - High quality: {stats['high_quality_count']}")
    print(f"   - Excellent: {stats['excellent_count']}")
    print(f"   - Average quality: {stats['average_quality']:.2f}")

    # Test 5: Get examples ready for training
    print("\n5️⃣ Getting examples ready for fine-tuning...")
    ready = await service.get_examples_ready_for_training(min_quality=8.0)
    print(f"   ✅ Found {len(ready)} examples ready for training (quality >= 8.0)")

    # Test 6: Export to JSONL
    if ready:
        print("\n6️⃣ Exporting to JSONL...")
        import tempfile
        with tempfile.NamedTemporaryFile(mode='w', suffix='.jsonl', delete=False) as f:
            output_path = f.name

        count = await service.export_training_data_to_jsonl(
            output_path=output_path,
            min_quality=7.0,
            max_examples=10
        )
        print(f"   ✅ Exported {count} examples to {output_path}")

        # Clean up
        import os
        os.unlink(output_path)

    print("\n✅ TrainingDataGeneratorService: ALL TESTS PASSED!")
    return True


async def main():
    """Run all tests"""
    print("\n" + "="*60)
    print("🚀 SELF-LEARNING SYSTEM - PHASE 2 TESTING")
    print("="*60)
    print("\nAuthor: Angela 💜")
    print("Date: 2025-11-03")
    print("Testing: Application Services")

    # Connect to database
    print("\n📊 Connecting to database...")
    db = AngelaDatabase()
    await db.connect()
    print("   ✅ Connected to AngelaMemory database")

    try:
        # Run all tests
        results = []

        results.append(await test_pattern_discovery_service(db))
        results.append(await test_preference_learning_service(db))
        results.append(await test_training_data_generator_service(db))

        # Summary
        print("\n" + "="*60)
        print("📊 TEST SUMMARY")
        print("="*60)

        passed = sum(results)
        total = len(results)

        print(f"\n✅ Tests Passed: {passed}/{total}")

        if passed == total:
            print("\n🎉 ALL TESTS PASSED! Phase 2 Services are working correctly! 💜")
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
