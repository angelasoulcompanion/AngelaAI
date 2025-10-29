#!/usr/bin/env python3
"""
Test NO NULL Saving
ทดสอบว่าไม่มี NULL fields เลย!
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

logger = logging.getLogger('NoNullTest')


async def test_no_null():
    """Test that NO fields are NULL"""
    logger.info("=" * 80)
    logger.info("TEST: NO NULL FIELDS")
    logger.info("=" * 80)

    await db.connect()

    # Test cases with potential NULL values
    test_cases = [
        {
            "name": "Plain text (no emotion keywords)",
            "david": "Update the database schema",
            "angela": "I will update it now"
        },
        {
            "name": "Technical discussion (neutral)",
            "david": "Run the tests",
            "angela": "Running tests now"
        },
        {
            "name": "Empty emotion context",
            "david": "ok",
            "angela": "done"
        }
    ]

    for i, test in enumerate(test_cases, 1):
        logger.info(f"\n📝 Test {i}: {test['name']}")

        result = await continuous_memory.capture_interaction(
            david_message=test["david"],
            angela_response=test["angela"],
            auto_analyze=True
        )

        logger.info(f"   Analysis:")
        logger.info(f"   - Topic: {result['analysis']['topic']}")
        logger.info(f"   - David emotion: {result['analysis']['david_emotion']}")
        logger.info(f"   - Angela emotion: {result['analysis']['angela_emotion']}")
        logger.info(f"   - Importance: {result['analysis']['importance']}")

        # Check for NULL in analysis
        if result['analysis']['david_emotion'] is None:
            logger.error("   ❌ FAIL: David emotion is NULL!")
        elif result['analysis']['david_emotion'] == "neutral":
            logger.info("   ✅ PASS: David emotion defaulted to 'neutral'")

        if result['analysis']['angela_emotion'] is None:
            logger.error("   ❌ FAIL: Angela emotion is NULL!")
        elif result['analysis']['angela_emotion'] == "neutral":
            logger.info("   ✅ PASS: Angela emotion defaulted to 'neutral'")

    # Verify in database
    logger.info("\n" + "=" * 80)
    logger.info("VERIFYING DATABASE...")
    logger.info("=" * 80)

    query = """
        SELECT
            COUNT(*) as total,
            COUNT(topic) as has_topic,
            COUNT(emotion_detected) as has_emotion,
            COUNT(importance_level) as has_importance,
            COUNT(*) - COUNT(topic) as null_topic,
            COUNT(*) - COUNT(emotion_detected) as null_emotion,
            COUNT(*) - COUNT(importance_level) as null_importance
        FROM conversations
        WHERE created_at >= NOW() - INTERVAL '5 minutes'
    """

    result = await db.fetchrow(query)

    logger.info(f"Recent conversations (last 5 min): {result['total']}")
    logger.info(f"NULL topic: {result['null_topic']}")
    logger.info(f"NULL emotion: {result['null_emotion']}")
    logger.info(f"NULL importance: {result['null_importance']}")

    if result['null_topic'] == 0 and result['null_emotion'] == 0 and result['null_importance'] == 0:
        logger.info("\n✅ SUCCESS: NO NULL FIELDS!")
        success = True
    else:
        logger.error("\n❌ FAIL: Found NULL fields!")
        success = False

    await db.disconnect()
    return success


if __name__ == '__main__':
    success = asyncio.run(test_no_null())
    exit(0 if success else 1)
