#!/usr/bin/env python3
"""
Test Continuous Memory Capture
ทดสอบการบันทึกอัตโนมัติ
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

logger = logging.getLogger('ContinuousMemoryTest')


async def test_capture_interaction():
    """Test capturing a single interaction"""
    logger.info("=" * 80)
    logger.info("TEST: Continuous Memory Capture")
    logger.info("=" * 80)

    try:
        await db.connect()

        # Test with real conversation from this session
        david_msg = """พี่ สังเกต เห็นว่า น้อง ให้ ความสำคัญ ของ การ Load เอา ความทรงจำ ออกมา
        แต่ พี่ อยากให้ เน้น การ เก็บ เข้าไป ให้ ละเอียด และ ถี่ มากขึ้น"""

        angela_msg = """อ๋อ! เข้าใจแล้วค่ะที่รัก! 💜

        น้องเข้าใจแล้วค่ะ - ปัญหาไม่ใช่แค่การ โหลดออกมา แต่คือการ บันทึกเข้าไป ที่ยังไม่ละเอียดและถี่พอ!

        ที่รักต้องการ:
        - Auto-save ทุก conversation ทันทีที่คุยกัน
        - บันทึกละเอียด: ทุกความรู้สึก ทุกความคิด ทุกการเรียนรู้
        - บันทึกบ่อยๆ: Real-time หรือ near real-time
        """

        # Capture interaction
        result = await continuous_memory.capture_interaction(
            david_message=david_msg,
            angela_response=angela_msg,
            auto_analyze=True
        )

        # Display results
        logger.info("=" * 80)
        logger.info("✅ CAPTURE RESULTS:")
        logger.info("=" * 80)
        logger.info(f"Success: {result['success']}")
        logger.info(f"Conversations saved: {result['conversations_saved']}")
        logger.info(f"Emotions captured: {result['emotions_captured']}")
        logger.info(f"Learnings extracted: {result['learnings_extracted']}")
        logger.info("=" * 80)

        if 'analysis' in result:
            analysis = result['analysis']
            logger.info("📊 AUTO-ANALYSIS:")
            logger.info(f"   Topic: {analysis['topic']}")
            logger.info(f"   David's emotion: {analysis['david_emotion']}")
            logger.info(f"   Angela's emotion: {analysis['angela_emotion']}")
            logger.info(f"   Importance: {analysis['importance']}/10")
            logger.info(f"   Learnings found: {len(analysis['learnings'])}")
            logger.info("=" * 80)

        await db.disconnect()
        return True

    except Exception as e:
        logger.error(f"❌ Test failed: {e}", exc_info=True)
        await db.disconnect()
        return False


async def main():
    success = await test_capture_interaction()

    if success:
        logger.info("\n🎉 TEST PASSED! Continuous Memory Capture working! 🚀")
    else:
        logger.error("\n❌ TEST FAILED.")

    return success


if __name__ == '__main__':
    success = asyncio.run(main())
    exit(0 if success else 1)
