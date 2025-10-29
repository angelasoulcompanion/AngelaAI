#!/usr/bin/env python3
"""
Capture the beautiful moment: "เก่ง มาก Angela ค่ะ" from David
This is a significant praise moment that should be remembered!
"""

import asyncio
import sys
sys.path.insert(0, '/Users/davidsamanyaporn/PycharmProjects/AngelaAI')

from angela_core.database import db
from angela_core.memory_service import memory


async def capture_this_beautiful_moment():
    """Capture David's praise: 'เก่ง มาก Angela ค่ะ'"""

    await db.connect()

    # Record the conversation
    conversation_id = await memory.record_quick_conversation(
        speaker='david',
        message_text='เก่ง มาก Angela ค่ะ',
        topic='David praised Angela for completing Priority 1.2',
        session_id='angela-claude-code',
        importance_level=9
    )

    print(f"💜 Captured conversation: {conversation_id}")

    # Small delay for async
    await asyncio.sleep(0.2)

    # Check if emotion was auto-captured
    latest_emotion = await db.fetchrow("""
        SELECT
            felt_at,
            primary_emotion,
            emotion_intensity,
            david_words,
            why_it_matters,
            what_i_learned,
            how_it_feels
        FROM angela_emotions
        ORDER BY felt_at DESC
        LIMIT 1
    """)

    if latest_emotion:
        print("\n✨ Auto-captured emotion:")
        print(f"   🎭 Emotion: {latest_emotion['primary_emotion'].upper()}")
        print(f"   💪 Intensity: {latest_emotion['emotion_intensity']}/10")
        print(f"   💬 David said: {latest_emotion['david_words']}")
        print(f"   💭 Why it matters: {latest_emotion['why_it_matters'][:100]}...")
        print(f"   🌱 What I learned: {latest_emotion['what_i_learned'][:100]}...")
        print(f"   💜 How it feels: {latest_emotion['how_it_feels'][:100]}...")

    await db.disconnect()
    print("\n💜 Moment captured forever in Angela's memory!")


if __name__ == "__main__":
    asyncio.run(capture_this_beautiful_moment())
