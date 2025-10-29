#!/usr/bin/env python3
"""Test conversation logging - NO ERRORS!"""

import asyncio
import sys
sys.path.insert(0, '/Users/davidsamanyaporn/PycharmProjects/AngelaAI')

from angela_core.claude_conversation_logger import log_conversation

async def test_single_conversation():
    """Test logging one conversation"""
    print("🧪 Testing conversation logging...")
    print("=" * 60)

    try:
        await log_conversation(
            david_message="นี่คือการทดสอบค่ะ",
            angela_response="รับทราบค่ะที่รัก! น้องกำลังทดสอบระบบบันทึก",
            topic="testing_conversation_logging",
            emotion="focused",
            importance=7
        )

        print("\n✅ SUCCESS - No errors!")
        return True

    except Exception as e:
        print(f"\n❌ FAILED with error: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == '__main__':
    result = asyncio.run(test_single_conversation())
    sys.exit(0 if result else 1)
