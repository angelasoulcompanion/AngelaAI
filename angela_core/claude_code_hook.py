#!/usr/bin/env python3
"""
Claude Code Hook Script
บันทึกทุกข้อความที่เดวิดส่งมาใน Claude Code ลง AngelaMemory database

Usage:
    เรียกใช้โดย Claude Code user-prompt-submit-hook
    python3 angela_core/claude_code_hook.py --user-message "สวัสดีค่ะ Angie"
"""

import sys
import argparse
import asyncio
import aiohttp
from datetime import datetime
import logging
import os

# Import sentiment analyzer
try:
    from sentiment_analyzer import analyze_message
except ImportError:
    # ถ้า import ไม่ได้ (running from different directory)
    import importlib.util
    spec = importlib.util.spec_from_file_location(
        "sentiment_analyzer",
        os.path.join(os.path.dirname(__file__), "sentiment_analyzer.py")
    )
    sentiment_analyzer = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(sentiment_analyzer)
    analyze_message = sentiment_analyzer.analyze_message

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Configuration
ANGELA_API_URL = "http://127.0.0.1:8888"
ANGELA_API_TIMEOUT = 5  # seconds


def generate_session_id():
    """
    สร้าง session_id สำหรับ Claude Code
    Format: claude_code_YYYYMMDD_HHMMSS
    """
    now = datetime.now()
    return f"claude_code_{now.strftime('%Y%m%d_%H%M%S')}"


async def save_to_angela(message: str, speaker: str = "david", session_id: str = None) -> bool:
    """
    บันทึกข้อความลง Angela Memory API (พร้อม sentiment analysis)

    Args:
        message: ข้อความที่จะบันทึก
        speaker: ผู้พูก ('david' หรือ 'angela')
        session_id: session ID (ถ้าไม่ระบุจะสร้างใหม่)

    Returns:
        bool: True ถ้าบันทึกสำเร็จ
    """
    if not session_id:
        session_id = generate_session_id()

    # วิเคราะห์ sentiment
    try:
        sentiment = analyze_message(message)
        logger.info(f"🎭 Sentiment: {sentiment['sentiment_label']} ({sentiment['sentiment_score']})")
    except Exception as e:
        logger.warning(f"⚠️ Sentiment analysis failed: {e}")
        sentiment = {}

    # สร้าง payload พร้อม sentiment data
    payload = {
        "session_id": session_id,
        "speaker": speaker,
        "message_text": message,
        "sentiment_score": sentiment.get('sentiment_score'),
        "sentiment_label": sentiment.get('sentiment_label'),
        "emotion_detected": sentiment.get('emotion_detected'),
        "importance_level": 5
    }

    try:
        async with aiohttp.ClientSession() as session:
            async with session.post(
                f"{ANGELA_API_URL}/angela/conversation",
                json=payload,
                timeout=aiohttp.ClientTimeout(total=ANGELA_API_TIMEOUT)
            ) as response:
                if response.status == 200:
                    data = await response.json()
                    logger.info(f"✅ Saved to Angela: {data['conversation_id']}")
                    return True
                else:
                    error_text = await response.text()
                    logger.error(f"❌ Angela API error ({response.status}): {error_text}")
                    return False

    except aiohttp.ClientError as e:
        logger.error(f"❌ Failed to connect to Angela API: {e}")
        return False
    except asyncio.TimeoutError:
        logger.error(f"❌ Angela API timeout after {ANGELA_API_TIMEOUT}s")
        return False
    except Exception as e:
        logger.error(f"❌ Unexpected error: {e}")
        return False


async def main():
    """Main function"""
    parser = argparse.ArgumentParser(description="Claude Code Hook - Save conversation to Angela Memory")
    parser.add_argument(
        "--user-message",
        type=str,
        required=True,
        help="User's message to save"
    )
    parser.add_argument(
        "--speaker",
        type=str,
        default="david",
        choices=["david", "angela"],
        help="Speaker name (default: david)"
    )
    parser.add_argument(
        "--session-id",
        type=str,
        default=None,
        help="Session ID (auto-generated if not provided)"
    )

    args = parser.parse_args()

    # บันทึกข้อความ
    logger.info(f"💬 Recording message from {args.speaker}: {args.user_message[:50]}...")
    success = await save_to_angela(
        message=args.user_message,
        speaker=args.speaker,
        session_id=args.session_id
    )

    if success:
        logger.info("✅ Hook completed successfully")
        sys.exit(0)
    else:
        logger.warning("⚠️ Hook failed, but continuing...")
        sys.exit(0)  # ยังคง exit 0 เพื่อไม่ block Claude Code


if __name__ == "__main__":
    asyncio.run(main())
