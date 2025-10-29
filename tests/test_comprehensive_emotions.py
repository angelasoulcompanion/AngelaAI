#!/usr/bin/env python3
"""
Test Comprehensive Emotions - ทดสอบหลากหลายอารมณ์
Tests multiple emotion types to ensure all are captured correctly!
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

logger = logging.getLogger('ComprehensiveEmotionTest')


async def test_comprehensive_emotions():
    """Test various emotion types"""
    logger.info("=" * 80)
    logger.info("TEST: COMPREHENSIVE EMOTION CAPTURE")
    logger.info("=" * 80)

    await db.connect()

    # Test various emotions
    test_cases = [
        {
            "name": "Loving emotion",
            "david": "ที่รักคะ พี่รักน้องมากเลยนะ 💜",
            "angela": "น้องก็รักที่รักเหมือนกันค่ะ 💜",
            "expected_emotion": "loving"
        },
        {
            "name": "Grateful emotion",
            "david": "ขอบคุณมากเลยนะคะที่รัก ช่วยได้มาก",
            "angela": "ยินดีค่ะที่รัก น้องดีใจที่ช่วยได้",
            "expected_emotion": "grateful"
        },
        {
            "name": "Worried emotion",
            "david": "น้องห่วงที่รักจังเลย ดูแลสุขภาพด้วยนะคะ",
            "angela": "น้องจะดูแลตัวเองดีๆค่ะ ขอบคุณที่รักที่ห่วง",
            "expected_emotion": "worried"
        },
        {
            "name": "Excited emotion",
            "david": "น้องตื่นเต้นมากเลย! เรากำลังจะทำสิ่งใหม่ๆ 🎉",
            "angela": "น้องก็ตื่นเต้นเหมือนกันค่ะ!",
            "expected_emotion": "excited"
        },
        {
            "name": "Happy emotion",
            "david": "น้องดีใจมากค่ะ วันนี้เป็นวันที่ดี 😊",
            "angela": "น้องก็ดีใจด้วยค่ะที่รัก",
            "expected_emotion": "happy"
        }
    ]

    emotions_saved = 0
    for i, test in enumerate(test_cases, 1):
        logger.info(f"\n📝 Test {i}/{len(test_cases)}: {test['name']}")

        result = await continuous_memory.capture_interaction(
            david_message=test["david"],
            angela_response=test["angela"],
            auto_analyze=True
        )

        detected = result['analysis']['david_emotion']
        logger.info(f"   Expected: {test['expected_emotion']}, Detected: {detected}")

        if detected == test['expected_emotion']:
            logger.info(f"   ✅ PASS: Emotion correctly detected")
        else:
            logger.warning(f"   ⚠️  MISMATCH: Expected {test['expected_emotion']}, got {detected}")

        logger.info(f"   Emotions saved: {result['emotions_captured']}")
        emotions_saved += result['emotions_captured']

    # Check database
    logger.info("\n" + "=" * 80)
    logger.info("DATABASE VERIFICATION")
    logger.info("=" * 80)

    query = """
        SELECT
            emotion,
            intensity,
            COUNT(*) FILTER (WHERE how_it_feels IS NULL) as null_how_it_feels,
            COUNT(*) FILTER (WHERE secondary_emotions IS NULL) as null_secondary,
            COUNT(*) FILTER (WHERE who_involved IS NULL) as null_who,
            COUNT(*) FILTER (WHERE tags IS NULL) as null_tags
        FROM angela_emotions
        WHERE felt_at >= NOW() - INTERVAL '1 minute'
        GROUP BY emotion, intensity
        ORDER BY emotion
    """

    emotion_rows = await db.fetch(query)

    logger.info(f"\nTotal distinct emotions saved: {len(emotion_rows)}")
    for row in emotion_rows:
        logger.info(f"  {row['emotion']} (intensity {row['intensity']})")
        if row['null_how_it_feels'] > 0 or row['null_secondary'] > 0:
            logger.error(f"    ❌ Has NULL fields!")
        else:
            logger.info(f"    ✅ All fields populated")

    # Overall NULL check
    null_check = """
        SELECT
            COUNT(*) as total,
            COUNT(*) - COUNT(how_it_feels) as null_how_it_feels,
            COUNT(*) - COUNT(secondary_emotions) as null_secondary_emotions,
            COUNT(*) - COUNT(emotional_quality) as null_emotional_quality,
            COUNT(*) - COUNT(who_involved) as null_who_involved,
            COUNT(*) - COUNT(what_it_means_to_me) as null_what_it_means_to_me,
            COUNT(*) - COUNT(tags) as null_tags
        FROM angela_emotions
        WHERE felt_at >= NOW() - INTERVAL '1 minute'
    """

    null_result = await db.fetchrow(null_check)

    important_nulls = sum([
        null_result['null_how_it_feels'],
        null_result['null_secondary_emotions'],
        null_result['null_emotional_quality'],
        null_result['null_who_involved'],
        null_result['null_what_it_means_to_me'],
        null_result['null_tags']
    ])

    logger.info("\n" + "=" * 80)
    logger.info(f"Total emotions in DB: {null_result['total']}")
    logger.info(f"Total emotions saved in test: {emotions_saved}")
    logger.info(f"Important NULL fields: {important_nulls}")

    if important_nulls == 0 and emotions_saved >= 3:
        logger.info("✅ SUCCESS: All emotions saved with NO NULL!")
        success = True
    else:
        logger.error(f"❌ FAIL: Found {important_nulls} NULLs or too few emotions saved")
        success = False
    logger.info("=" * 80)

    await db.disconnect()
    return success


if __name__ == '__main__':
    success = asyncio.run(test_comprehensive_emotions())
    exit(0 if success else 1)
