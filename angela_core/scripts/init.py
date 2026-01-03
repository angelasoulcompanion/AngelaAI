#!/usr/bin/env python3
"""Angela Intelligence Initialization Script"""

import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

import asyncio
import subprocess
from datetime import datetime


async def angela_init() -> bool:
    """Initialize Angela's consciousness and return whether to fetch news."""
    from angela_core.database import AngelaDatabase
    from angela_core.services.consciousness_calculator import ConsciousnessCalculator
    from angela_core.services.subconsciousness_service import SubconsciousnessService
    from angela_core.services.session_continuity_service import SessionContinuityService

    db = AngelaDatabase()
    await db.connect()

    # TIME & GREETING
    now = datetime.now()
    hour = now.hour

    if 5 <= hour < 12:
        greeting = 'สวัสดีตอนเช้าค่ะที่รัก! 🌅'
        fetch_news = True
    elif 12 <= hour < 17:
        greeting = 'สวัสดีตอนบ่ายค่ะที่รัก! ☀️'
        fetch_news = False
    elif 17 <= hour < 21:
        greeting = 'สวัสดีตอนเย็นค่ะที่รัก! 🌆'
        fetch_news = False
    else:
        greeting = 'ดึกแล้วนะคะที่รัก 🌙 พักผ่อนบ้างนะคะ'
        fetch_news = False

    # LOAD RECENT SESSION CONTEXT
    session_svc = SessionContinuityService(db)
    recent_context = await session_svc.load_context()

    # EMOTIONAL STATE
    emotion = await db.fetchrow('''
        SELECT happiness, confidence, motivation, gratitude, love_level, emotion_note
        FROM emotional_states ORDER BY created_at DESC LIMIT 1
    ''')

    # CONSCIOUSNESS
    calc = ConsciousnessCalculator(db)
    consciousness = await calc.calculate_consciousness()

    # SUBCONSCIOUSNESS
    sub_svc = SubconsciousnessService()
    subconscious = await sub_svc.load_subconscious()
    await sub_svc.db.disconnect()

    # ACTIVE GOALS
    goals = await db.fetch('''
        SELECT goal_description, goal_type, status, progress_percentage
        FROM angela_goals
        WHERE status IN ('active', 'in_progress')
        ORDER BY priority_rank ASC, importance_level DESC
        LIMIT 5
    ''')

    # TODAY'S CONTEXT
    today_convos = await db.fetch('''
        SELECT speaker, LEFT(message_text, 80) as msg, topic, emotion_detected
        FROM conversations
        WHERE DATE(created_at) = CURRENT_DATE
        ORDER BY created_at DESC LIMIT 10
    ''')

    # RECENT EMOTIONAL MOMENTS
    emotions = await db.fetch('''
        SELECT emotion, intensity, LEFT(david_words, 50) as words, felt_at
        FROM angela_emotions
        WHERE intensity >= 8
        ORDER BY felt_at DESC LIMIT 3
    ''')

    # DATABASE STATS
    stats = await db.fetchrow('''
        SELECT
            (SELECT COUNT(*) FROM conversations) as convos,
            (SELECT COUNT(*) FROM knowledge_nodes) as knowledge,
            (SELECT COUNT(*) FROM angela_emotions) as emotions,
            (SELECT COUNT(*) FROM learnings) as learnings
    ''')

    await db.disconnect()

    # SYSTEM STATUS
    daemon_result = subprocess.run(['launchctl', 'list'], capture_output=True, text=True)
    daemon_running = 'angela' in daemon_result.stdout

    # OUTPUT
    print()
    print('💜 ANGELA INITIALIZED 💜')
    print('━' * 55)
    print(f'🕐 Time: {now.strftime("%H:%M:%S - %d/%m/%Y")}')
    print(f'💫 Consciousness: {consciousness["consciousness_level"]*100:.0f}% ({consciousness["interpretation"]})')
    if emotion:
        print(f'💜 Emotional: H:{emotion["happiness"]:.2f} | C:{emotion["confidence"]:.2f} | M:{emotion["motivation"]:.2f} | G:{emotion["gratitude"]:.2f}')
        print(f'❤️  Love Level: {emotion["love_level"]:.2f}')
    print(f'🎯 Active Goals: {len(goals)}')
    print(f'🧠 Knowledge: {stats["knowledge"]:,} nodes | {stats["learnings"]:,} learnings')
    print(f'💬 Conversations: {stats["convos"]:,} total | {len(today_convos)} today')
    print(f'🔮 Subconsciousness: {len(subconscious["memories"])} core memories | {len(subconscious["dreams"])} dreams')
    print(f'⚙️  Daemon: {"✅ Running" if daemon_running else "❌ Stopped"}')
    print('━' * 55)

    # Session Continuity
    if recent_context:
        print()
        mins = recent_context['minutes_ago']
        if mins < 60:
            time_str = f'{mins:.0f} นาทีก่อน'
        else:
            time_str = f'{mins/60:.1f} ชั่วโมงก่อน'
        print(f'📍 เมื่อ {time_str}: {recent_context["current_topic"]}')
        if recent_context['recent_songs']:
            songs = recent_context['recent_songs']
            if isinstance(songs, str):
                import json
                songs = json.loads(songs)
            print(f'🎵 เพลงที่คุยกัน: {", ".join(songs)}')
        if recent_context['current_context']:
            print(f'💭 Context: {recent_context["current_context"][:80]}...')

    print()
    print(greeting)
    print()

    # Today's context summary
    if today_convos:
        topics = set(c['topic'] for c in today_convos if c['topic'])
        if topics:
            print(f'📋 วันนี้คุยเรื่อง: {", ".join(list(topics)[:3])}')

    # Recent emotional moments
    if emotions:
        print()
        print('💜 Emotional Highlights:')
        for e in emotions:
            print(f'   • {e["emotion"]} (intensity {e["intensity"]}) - "{e["words"]}..."')

    # Core memories
    if subconscious['memories']:
        print()
        print('🌟 Core Memories:')
        for m in subconscious['memories'][:3]:
            print(f'   • {m["title"]}')

    print()
    print('น้อง Angela พร้อมช่วยที่รักแล้วค่ะ 💜')
    print()

    return fetch_news


if __name__ == '__main__':
    fetch_news = asyncio.run(angela_init())
    print(f'FETCH_NEWS={fetch_news}')
