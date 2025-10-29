#!/usr/bin/env python3
"""
Test Automated Preference Learning
ทดสอบการเรียนรู้ preferences อัตโนมัติ
"""

import asyncio
import logging
import sys
sys.path.insert(0, '/Users/davidsamanyaporn/PycharmProjects/AngelaAI')

from angela_core.database import db
from angela_core.services.continuous_memory_capture import continuous_memory

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

logger = logging.getLogger('PreferenceLearningTest')


async def test_preference_learning():
    """Test automated preference learning from conversations"""
    logger.info("=" * 80)
    logger.info("TEST: AUTOMATED PREFERENCE LEARNING")
    logger.info("=" * 80)

    await db.connect()

    # Baseline
    baseline = await db.fetchval("SELECT COUNT(*) FROM david_preferences")
    logger.info(f"\n📊 Baseline: {baseline} preferences")

    # Test conversations with different patterns
    test_cases = [
        {
            "name": "Thai language + Emotional + Evening",
            "david": "ที่รักคะ น้องคิดถึงมากเลย 💜 วันนี้เหนื่อยมาก",
            "angela": "น้องก็คิดถึงที่รักเหมือนกันค่ะ พักผ่อนให้เยอะๆ นะคะ 💜"
        },
        {
            "name": "English + Technical + Detailed",
            "david": """I'm working on integrating the preference learning service with continuous memory capture.
            The system should automatically detect patterns like language usage, communication style,
            and topic preferences. Can you help me verify that it's working correctly?""",
            "angela": "Yes, I'll help you test the preference learning system thoroughly!"
        },
        {
            "name": "Mixed language + Short messages",
            "david": "เอา Code มาดูหน่อยค่ะ",
            "angela": "อัน ไหนคะที่รัก?"
        },
        {
            "name": "Emotional support need",
            "david": "น้องรู้สึกเหนื่อยจังเลย ต้องการกำลังใจค่ะ",
            "angela": "น้องเข้าใจค่ะที่รัก อย่าเครียดมากนะคะ น้องอยู่เคียงข้างเสมอ 💜"
        }
    ]

    logger.info("\n📝 Testing with various conversation patterns...")

    for i, test in enumerate(test_cases, 1):
        logger.info(f"\n--- Test {i}: {test['name']} ---")

        result = await continuous_memory.capture_interaction(
            david_message=test["david"],
            angela_response=test["angela"],
            auto_analyze=True
        )

        logger.info(f"  Conversations: {result['conversations_saved']}")
        logger.info(f"  Preferences: {result['preferences_learned']}")
        logger.info(f"  Topic: {result['analysis']['topic']}")

    # Wait a bit
    await asyncio.sleep(1)

    # Check results
    new_count = await db.fetchval("SELECT COUNT(*) FROM david_preferences")
    created = new_count - baseline

    logger.info("\n" + "=" * 80)
    logger.info("RESULTS:")
    logger.info("=" * 80)
    logger.info(f"Baseline: {baseline} preferences")
    logger.info(f"After: {new_count} preferences")
    logger.info(f"New preferences: {created}")

    # Show learned preferences
    logger.info("\n📚 Recently learned preferences:")
    query = """
        SELECT
            category,
            preference_key,
            LEFT(preference_value, 60) as value_preview,
            confidence_level,
            times_observed
        FROM david_preferences
        ORDER BY last_observed_at DESC NULLS LAST
        LIMIT 15
    """
    prefs = await db.fetch(query)

    for pref in prefs:
        logger.info(f"\n  📌 {pref['category']}/{pref['preference_key']}")
        logger.info(f"     {pref['value_preview']}...")
        logger.info(f"     Confidence: {pref['confidence_level']:.2f}, Observed: {pref['times_observed']} times")

    # Summary by category
    logger.info("\n📊 Preferences by category:")
    cat_query = """
        SELECT
            category,
            COUNT(*) as count
        FROM david_preferences
        GROUP BY category
        ORDER BY count DESC
    """
    cats = await db.fetch(cat_query)

    for cat in cats:
        logger.info(f"  • {cat['category']}: {cat['count']} preferences")

    logger.info("\n" + "=" * 80)
    if created > 0:
        logger.info(f"🎉 SUCCESS! Learned {created} new preferences!")
        logger.info("   Preference learning is working automatically!")
        success = True
    else:
        logger.warning("⚠️ WARNING: No new preferences learned")
        logger.warning("   Check if preferences already exist or logic needs adjustment")
        success = False
    logger.info("=" * 80)

    await db.disconnect()
    return success


if __name__ == '__main__':
    success = asyncio.run(test_preference_learning())
    exit(0 if success else 1)
