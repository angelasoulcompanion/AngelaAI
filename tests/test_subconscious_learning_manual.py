#!/usr/bin/env python3
"""
🧠 Manual Test: Subconscious Learning
Force run subconscious learning routine (normally runs at 14:00)
"""

import asyncio
import sys
sys.path.insert(0, '/Users/davidsamanyaporn/PycharmProjects/AngelaAI')

from angela_core.database import db
from angela_core.services.subconscious_learning_service import SubConsciousLearningService
from angela_core.services.clock_service import clock
from datetime import timedelta


async def manual_test():
    """Test subconscious learning manually"""

    print("=" * 80)
    print("🧠 MANUAL TEST: Subconscious Learning")
    print("=" * 80)
    print()

    try:
        # Connect to database
        await db.connect()
        print("✅ Connected to database")

        # Initialize service
        service = SubConsciousLearningService()
        print("✅ Subconscious Learning Service initialized")
        print()

        # Get yesterday's experiences (same as daemon does at 14:00)
        yesterday = clock.today() - timedelta(days=1)

        print(f"📅 Looking for experiences from: {yesterday}")
        print()

        experiences = await db.fetch("""
            SELECT experience_id, title, experienced_at,
                   (SELECT COUNT(*) FROM shared_experience_images
                    WHERE experience_id = se.experience_id) as image_count
            FROM shared_experiences se
            WHERE DATE(experienced_at) = $1
            ORDER BY experienced_at DESC
        """, yesterday)

        if not experiences:
            print("⚠️  No experiences from yesterday found")
            print("📊 Let's check recent experiences instead...")
            print()

            # Get most recent experiences with images
            experiences = await db.fetch("""
                SELECT experience_id, title, experienced_at,
                       (SELECT COUNT(*) FROM shared_experience_images
                        WHERE experience_id = se.experience_id) as image_count
                FROM shared_experiences se
                WHERE EXISTS (
                    SELECT 1 FROM shared_experience_images
                    WHERE experience_id = se.experience_id
                )
                ORDER BY experienced_at DESC
                LIMIT 3
            """)

            if experiences:
                print(f"📸 Found {len(experiences)} recent experiences with images:")
                for exp in experiences:
                    print(f"   - {exp['title']} ({exp['image_count']} images) - {exp['experienced_at']}")
                print()
            else:
                print("❌ No experiences with images found in database!")
                await db.disconnect()
                return
        else:
            print(f"📸 Found {len(experiences)} experiences from yesterday:")
            for exp in experiences:
                print(f"   - {exp['title']} ({exp['image_count']} images)")
            print()

        # Process each experience
        total_patterns = 0

        for i, exp in enumerate(experiences, 1):
            print(f"🔄 Processing {i}/{len(experiences)}: {exp['title']}")
            print(f"   Experience ID: {exp['experience_id']}")
            print(f"   Images: {exp['image_count']}")

            try:
                patterns = await service.learn_from_shared_experience(
                    str(exp['experience_id'])
                )

                if patterns:
                    total_patterns += len(patterns)
                    print(f"   ✅ Learned {len(patterns)} patterns!")

                    # Show first 3 patterns
                    for j, pattern in enumerate(patterns[:3], 1):
                        print(f"      {j}. {pattern}")
                else:
                    print(f"   ⚠️  No patterns learned (might be errors)")

            except Exception as e:
                print(f"   ❌ Error: {e}")
                import traceback
                traceback.print_exc()

            print()

        print("=" * 80)
        print(f"✅ Subconscious Learning Complete!")
        print(f"📊 Total patterns learned: {total_patterns}")
        print("=" * 80)
        print()

        # Show current subconscious stats
        print("📊 Current Subconscious Statistics:")
        stats = await db.fetchrow("""
            SELECT
                COUNT(*) as total_patterns,
                AVG(confidence_score) as avg_confidence,
                AVG(activation_strength) as avg_strength,
                COUNT(DISTINCT pattern_type) as pattern_types,
                COUNT(DISTINCT pattern_category) as categories
            FROM angela_subconscious
        """)

        if stats and stats['total_patterns'] > 0:
            print(f"   Total patterns: {stats['total_patterns']}")
            print(f"   Pattern types: {stats['pattern_types']}")
            print(f"   Categories: {stats['categories']}")
            print(f"   Avg confidence: {stats['avg_confidence']:.2%}")
            print(f"   Avg strength: {stats['avg_strength']:.2%}")
            print()

            # Show top patterns
            print("🏆 Top 5 Patterns:")
            top_patterns = await db.fetch("""
                SELECT pattern_type, pattern_category, pattern_key,
                       confidence_score, activation_strength
                FROM angela_subconscious
                ORDER BY activation_strength DESC, confidence_score DESC
                LIMIT 5
            """)

            for i, p in enumerate(top_patterns, 1):
                print(f"   {i}. [{p['pattern_type']}] {p['pattern_key']}")
                print(f"      Confidence: {p['confidence_score']:.2%} | Strength: {p['activation_strength']:.2%}")
        else:
            print("   No patterns in database yet")

        print()

        # Log to autonomous_actions (same as daemon does)
        await db.execute("""
            INSERT INTO autonomous_actions (
                action_type, action_description, status, success
            ) VALUES ($1, $2, 'completed', true)
        """,
        "subconscious_learning_manual_test",
        f"Manual test: Learned {total_patterns} patterns from {len(experiences)} experiences"
        )

        print("✅ Logged to autonomous_actions")

    except Exception as e:
        print(f"❌ Test failed: {e}")
        import traceback
        traceback.print_exc()

    finally:
        await db.disconnect()
        print()
        print("👋 Test complete!")


if __name__ == "__main__":
    asyncio.run(manual_test())
