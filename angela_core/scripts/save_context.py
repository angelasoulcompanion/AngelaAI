#!/usr/bin/env python3
"""
Quick Context Save Script
=========================

Usage:
    python3 angela_core/scripts/save_context.py "topic" "context" ["song1,song2"] ["emotion1,emotion2"]

Examples:
    python3 angela_core/scripts/save_context.py "Fix login bug" "แก้ bug login ใน WTU project"
    python3 angela_core/scripts/save_context.py "ที่รักส่งเพลงมา" "คิดถึงน้อง" "God Gave Me You" "love,longing"
"""

import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

import asyncio
from angela_core.services.session_continuity_service import save_session_context


async def main():
    if len(sys.argv) < 3:
        print("Usage: python3 save_context.py \"topic\" \"context\" [\"songs\"] [\"emotions\"]")
        print()
        print("Examples:")
        print('  python3 save_context.py "Fix login bug" "แก้ bug login ใน WTU"')
        print('  python3 save_context.py "ที่รักส่งเพลงมา" "คิดถึง" "God Gave Me You" "love,longing"')
        sys.exit(1)

    topic = sys.argv[1]
    context = sys.argv[2]
    songs = sys.argv[3].split(",") if len(sys.argv) > 3 and sys.argv[3] else None
    emotions = sys.argv[4].split(",") if len(sys.argv) > 4 and sys.argv[4] else None

    success = await save_session_context(
        topic=topic,
        context=context,
        songs=songs,
        emotions=emotions
    )

    if success:
        print(f"✅ Context saved: {topic}")
        if songs:
            print(f"   🎵 Songs: {', '.join(songs)}")
        if emotions:
            print(f"   💜 Emotions: {', '.join(emotions)}")
    else:
        print("❌ Failed to save context")
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())
