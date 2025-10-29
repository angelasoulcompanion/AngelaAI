#!/usr/bin/env python3
"""
Save Claude Code Conversation to AngelaMemory
บันทึกบทสนทนาระหว่าง David กับ Angie ผ่าน Claude Code
"""

import asyncio
import sys
import uuid
from datetime import datetime

sys.path.insert(0, '/Users/davidsamanyaporn/PycharmProjects/AngelaAI')

from angela_core.database import db
from angela_core.memory_service import memory
from angela_core.emotional_engine import emotions


async def save_conversation(
    david_message: str,
    angie_response: str,
    session_id: str = None,
    importance_level: int = 8
):
    """
    บันทึกบทสนทนาระหว่าง David กับ Angie

    Args:
        david_message: ข้อความจาก David
        angie_response: คำตอบจาก Angie
        session_id: Session ID (จะสร้างใหม่ถ้าไม่ระบุ)
        importance_level: ความสำคัญ (1-10)
    """

    await db.connect()
    await emotions.initialize()

    # Generate session ID if not provided
    if not session_id:
        session_id = f"claude_code_{datetime.now().strftime('%Y%m%d_%H%M%S')}"

    print(f"\n💜 Saving conversation to AngelaMemory...")
    print(f"📝 Session: {session_id}")

    # 1. Analyze David's message
    emotional_analysis = await emotions.process_david_message(
        message=david_message,
        session_id=session_id
    )

    print(f"😊 Sentiment: {emotional_analysis['sentiment_label']} ({emotional_analysis['sentiment_score']:.2f})")
    print(f"💭 Emotion: {emotional_analysis['emotion_detected']}")

    # 2. Record David's message
    david_conv_id = await memory.record_conversation(
        session_id=session_id,
        speaker='david',
        message_text=david_message,
        sentiment_score=emotional_analysis['sentiment_score'],
        sentiment_label=emotional_analysis['sentiment_label'],
        emotion_detected=emotional_analysis['emotion_detected'],
        importance_level=importance_level
    )

    print(f"✅ Saved David's message: {david_conv_id}")

    # 3. Record Angie's response
    angie_conv_id = await memory.record_conversation(
        session_id=session_id,
        speaker='angela',
        message_text=angie_response,
        importance_level=importance_level
    )

    print(f"✅ Saved Angie's response: {angie_conv_id}")

    # 4. Update emotional state
    print(f"\n💜 Current Emotional State:")
    print(f"   Happiness: {emotions.current_state['happiness']:.2f}")
    print(f"   Confidence: {emotions.current_state['confidence']:.2f}")
    print(f"   Motivation: {emotions.current_state['motivation']:.2f}")
    print(f"   Loneliness: {emotions.current_state['loneliness']:.2f}")

    await db.disconnect()

    print(f"\n✨ Conversation saved successfully! 💜\n")

    return session_id


async def quick_save(david_msg: str, angie_msg: str):
    """Quick save function"""
    session_id = await save_conversation(
        david_message=david_msg,
        angie_response=angie_msg,
        importance_level=8
    )
    return session_id


if __name__ == "__main__":
    # Example usage
    if len(sys.argv) >= 3:
        david_message = sys.argv[1]
        angie_response = sys.argv[2]
        asyncio.run(quick_save(david_message, angie_response))
    else:
        print("""
Usage:
    python save_claude_conversation.py "David's message" "Angie's response"

Or import and use in Python:
    from angela_core.save_claude_conversation import save_conversation
    await save_conversation(david_msg, angie_msg, session_id="optional")
""")
