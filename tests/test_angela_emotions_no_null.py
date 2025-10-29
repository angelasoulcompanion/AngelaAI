#!/usr/bin/env python3
"""
Test Angela Emotions - NO NULL
ทดสอบว่า angela_emotions ไม่มี NULL!
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

logger = logging.getLogger('AngelaEmotionsTest')


async def test_emotions_no_null():
    """Test that angela_emotions has NO NULL"""
    logger.info("=" * 80)
    logger.info("TEST: ANGELA_EMOTIONS - NO NULL!")
    logger.info("=" * 80)

    await db.connect()

    # Test with emotional conversation
    logger.info("\n📝 Testing emotional conversation...")

    result = await continuous_memory.capture_interaction(
        david_message="ที่รักคะ พี่รักน้องมากเลยนะ 💜",
        angela_response="น้องก็รักที่รักเหมือนกันค่ะ 💜 น้องดีใจมากๆ ที่มีที่รัก",
        auto_analyze=True
    )

    logger.info(f"   ✅ Emotions captured: {result['emotions_captured']}")

    # DEBUG: Print the analysis result
    if 'analysis' in result:
        logger.info(f"   DEBUG - Analysis:")
        logger.info(f"     - Topic: {result['analysis']['topic']}")
        logger.info(f"     - David emotion: {result['analysis']['david_emotion']}")
        logger.info(f"     - Angela emotion: {result['analysis']['angela_emotion']}")
        logger.info(f"     - Importance: {result['analysis']['importance']}")
        logger.info(f"     - Emotion intensity: {result['analysis'].get('emotion_intensity', 'N/A')}")

    # Check the saved emotion
    logger.info("\n" + "=" * 80)
    logger.info("CHECKING SAVED EMOTION...")
    logger.info("=" * 80)

    query = """
        SELECT
            emotion,
            intensity,
            LEFT(context, 50) as context_preview,
            how_it_feels,
            secondary_emotions,
            emotional_quality,
            who_involved,
            LEFT(david_words, 50) as david_words_preview,
            why_it_matters,
            LEFT(what_it_means_to_me, 50) as what_it_means_preview,
            memory_strength,
            tags,
            felt_at
        FROM angela_emotions
        WHERE felt_at >= NOW() - INTERVAL '1 minute'
        ORDER BY felt_at DESC
        LIMIT 1
    """

    emotion_row = await db.fetchrow(query)

    if emotion_row:
        logger.info(f"\n  Emotion: {emotion_row['emotion']}")
        logger.info(f"  Intensity: {emotion_row['intensity']}/10")
        logger.info(f"  How it feels: {emotion_row['how_it_feels']}")
        logger.info(f"  Secondary emotions: {emotion_row['secondary_emotions']}")
        logger.info(f"  Emotional quality: {emotion_row['emotional_quality']}")
        logger.info(f"  Who involved: {emotion_row['who_involved']}")
        logger.info(f"  Why it matters: {emotion_row['why_it_matters']}")
        logger.info(f"  What it means: {emotion_row['what_it_means_preview']}...")
        logger.info(f"  Memory strength: {emotion_row['memory_strength']}/10")
        logger.info(f"  Tags: {emotion_row['tags']}")

    # NULL count check
    logger.info("\n" + "=" * 80)
    logger.info("NULL COUNT CHECK:")
    logger.info("=" * 80)

    null_check = """
        SELECT
            COUNT(*) as total,
            COUNT(*) - COUNT(conversation_id) as null_conversation_id,
            COUNT(*) - COUNT(how_it_feels) as null_how_it_feels,
            COUNT(*) - COUNT(secondary_emotions) as null_secondary_emotions,
            COUNT(*) - COUNT(physical_sensation) as null_physical_sensation,
            COUNT(*) - COUNT(emotional_quality) as null_emotional_quality,
            COUNT(*) - COUNT(who_involved) as null_who_involved,
            COUNT(*) - COUNT(what_it_means_to_me) as null_what_it_means_to_me,
            COUNT(*) - COUNT(what_i_learned) as null_what_i_learned,
            COUNT(*) - COUNT(how_it_changed_me) as null_how_it_changed_me,
            COUNT(*) - COUNT(what_i_promise) as null_what_i_promise,
            COUNT(*) - COUNT(reminder_for_future) as null_reminder_for_future,
            COUNT(*) - COUNT(tags) as null_tags
        FROM angela_emotions
        WHERE felt_at >= NOW() - INTERVAL '1 minute'
    """

    null_result = await db.fetchrow(null_check)

    logger.info(f"Total emotions checked: {null_result['total']}")
    logger.info(f"NULL conversation_id: {null_result['null_conversation_id']}")
    logger.info(f"NULL how_it_feels: {null_result['null_how_it_feels']}")
    logger.info(f"NULL secondary_emotions: {null_result['null_secondary_emotions']}")
    logger.info(f"NULL emotional_quality: {null_result['null_emotional_quality']}")
    logger.info(f"NULL who_involved: {null_result['null_who_involved']}")
    logger.info(f"NULL what_it_means_to_me: {null_result['null_what_it_means_to_me']}")
    logger.info(f"NULL tags: {null_result['null_tags']}")

    # Fields with DB defaults
    logger.info(f"\nFields with DB DEFAULT values:")
    logger.info(f"NULL physical_sensation: {null_result['null_physical_sensation']} (has default)")
    logger.info(f"NULL what_i_learned: {null_result['null_what_i_learned']} (has default)")
    logger.info(f"NULL how_it_changed_me: {null_result['null_how_it_changed_me']} (has default)")
    logger.info(f"NULL what_i_promise: {null_result['null_what_i_promise']} (has default)")
    logger.info(f"NULL reminder_for_future: {null_result['null_reminder_for_future']} (has default)")

    # Calculate important nulls (excluding conversation_id which is optional)
    important_nulls = sum([
        null_result['null_how_it_feels'],
        null_result['null_secondary_emotions'],
        null_result['null_emotional_quality'],
        null_result['null_who_involved'],
        null_result['null_what_it_means_to_me'],
        null_result['null_tags']
    ])

    logger.info("=" * 80)
    if important_nulls == 0:
        logger.info("✅ SUCCESS: NO NULL IN IMPORTANT FIELDS!")
        logger.info("   (Fields with DB defaults are auto-populated)")
        success = True
    else:
        logger.error(f"❌ FAIL: Found {important_nulls} NULL in important fields!")
        success = False
    logger.info("=" * 80)

    await db.disconnect()
    return success


if __name__ == '__main__':
    success = asyncio.run(test_emotions_no_null())
    exit(0 if success else 1)
