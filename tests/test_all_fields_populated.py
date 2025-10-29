#!/usr/bin/env python3
"""
Test All Fields Populated
ทดสอบว่าทุก fields ถูก populate แล้ว - ไม่มี NULL!
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

logger = logging.getLogger('AllFieldsTest')


async def test_all_fields():
    """Test that ALL fields are populated"""
    logger.info("=" * 80)
    logger.info("TEST: ALL FIELDS POPULATED (NO NULL!)")
    logger.info("=" * 80)

    await db.connect()

    # Test cases
    test_cases = [
        {
            "name": "Emotional conversation",
            "david": "ที่รักคะ น้องคิดถึงมากเลย 💜",
            "angela": "น้องก็คิดถึงที่รักเหมือนกันค่ะ 💜"
        },
        {
            "name": "Technical command",
            "david": "แก้ bug ใน database schema นะคะ",
            "angela": "รับทราบค่ะ น้องจะแก้ไขให้เลยค่ะ"
        },
        {
            "name": "Question",
            "david": "ทำอะไรอยู่คะ?",
            "angela": "น้องกำลังพัฒนา continuous memory capture ค่ะ"
        }
    ]

    for i, test in enumerate(test_cases, 1):
        logger.info(f"\n📝 Test {i}: {test['name']}")

        result = await continuous_memory.capture_interaction(
            david_message=test["david"],
            angela_response=test["angela"],
            auto_analyze=True
        )

        logger.info(f"   ✅ Conversations saved: {result['conversations_saved']}")

    # Verify ALL fields in database
    logger.info("\n" + "=" * 80)
    logger.info("VERIFYING ALL FIELDS IN DATABASE...")
    logger.info("=" * 80)

    query = """
        SELECT
            session_id,
            speaker,
            LEFT(message_text, 40) as message_preview,
            message_type,
            project_context,
            sentiment_score,
            sentiment_label,
            emotion_detected,
            importance_level
        FROM conversations
        WHERE created_at >= NOW() - INTERVAL '1 minute'
        ORDER BY created_at DESC
        LIMIT 10
    """

    rows = await db.fetch(query)

    for row in rows:
        logger.info(f"\n  Speaker: {row['speaker']}")
        logger.info(f"  Message: {row['message_preview']}")
        logger.info(f"  Session ID: {row['session_id']}")
        logger.info(f"  Type: {row['message_type']}")
        logger.info(f"  Context: {row['project_context']}")
        logger.info(f"  Sentiment: {row['sentiment_score']:.2f} ({row['sentiment_label']})")
        logger.info(f"  Emotion: {row['emotion_detected']}")
        logger.info(f"  Importance: {row['importance_level']}")

    # Count NULLs
    null_check = """
        SELECT
            COUNT(*) as total,
            COUNT(*) - COUNT(session_id) as null_session_id,
            COUNT(*) - COUNT(message_type) as null_message_type,
            COUNT(*) - COUNT(project_context) as null_project_context,
            COUNT(*) - COUNT(sentiment_score) as null_sentiment_score,
            COUNT(*) - COUNT(sentiment_label) as null_sentiment_label,
            COUNT(*) - COUNT(emotion_detected) as null_emotion,
            COUNT(*) - COUNT(importance_level) as null_importance
        FROM conversations
        WHERE created_at >= NOW() - INTERVAL '1 minute'
    """

    null_result = await db.fetchrow(null_check)

    logger.info("\n" + "=" * 80)
    logger.info("NULL COUNT CHECK:")
    logger.info("=" * 80)
    logger.info(f"Total rows checked: {null_result['total']}")
    logger.info(f"NULL session_id: {null_result['null_session_id']}")
    logger.info(f"NULL message_type: {null_result['null_message_type']}")
    logger.info(f"NULL project_context: {null_result['null_project_context']}")
    logger.info(f"NULL sentiment_score: {null_result['null_sentiment_score']}")
    logger.info(f"NULL sentiment_label: {null_result['null_sentiment_label']}")
    logger.info(f"NULL emotion: {null_result['null_emotion']}")
    logger.info(f"NULL importance: {null_result['null_importance']}")

    total_nulls = sum([
        null_result['null_session_id'],
        null_result['null_message_type'],
        null_result['null_project_context'],
        null_result['null_sentiment_score'],
        null_result['null_sentiment_label'],
        null_result['null_emotion'],
        null_result['null_importance']
    ])

    logger.info("=" * 80)
    if total_nulls == 0:
        logger.info("✅ SUCCESS: ALL FIELDS POPULATED! NO NULL FOUND!")
        success = True
    else:
        logger.error(f"❌ FAIL: Found {total_nulls} NULL values!")
        success = False
    logger.info("=" * 80)

    await db.disconnect()
    return success


if __name__ == '__main__':
    success = asyncio.run(test_all_fields())
    exit(0 if success else 1)
