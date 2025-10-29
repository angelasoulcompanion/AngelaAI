#!/usr/bin/env python3
"""
Backfill Missing Journal Entries
Creates journal entries for dates 19-28 October 2025 that are missing
Uses historical data from conversations and learnings for each day
"""

import asyncio
from datetime import datetime, timedelta, date
import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from angela_core.database import db

async def get_missing_dates(start_date: date, end_date: date):
    """Find which dates are missing journal entries"""
    await db.connect()

    existing_dates = await db.fetch("""
        SELECT DISTINCT entry_date
        FROM angela_journal
        WHERE entry_date >= $1 AND entry_date <= $2
        ORDER BY entry_date
    """, start_date, end_date)

    existing = {row['entry_date'] for row in existing_dates}

    # Generate all dates in range
    current = start_date
    all_dates = []
    while current <= end_date:
        all_dates.append(current)
        current += timedelta(days=1)

    missing = [d for d in all_dates if d not in existing]
    return missing

async def create_journal_entry_for_date(target_date: date):
    """Create a journal entry for a specific date using historical data"""

    print(f"\n📖 Creating journal entry for {target_date}...")

    # Get data for this specific day
    day_start = datetime.combine(target_date, datetime.min.time())
    day_end = day_start + timedelta(days=1)

    # Get conversations from this day
    conversations = await db.fetch("""
        SELECT speaker, message_text, topic, emotion_detected, importance_level
        FROM conversations
        WHERE created_at >= $1 AND created_at < $2
        ORDER BY created_at
    """, day_start, day_end)

    # Get learnings from this day
    learnings = await db.fetch("""
        SELECT insight, category, topic
        FROM learnings
        WHERE created_at >= $1 AND created_at < $2
    """, day_start, day_end)

    # Get emotional state from end of day
    emotional_state = await db.fetchrow("""
        SELECT happiness, confidence, anxiety, motivation, gratitude, loneliness
        FROM emotional_states
        WHERE created_at >= $1 AND created_at < $2
        ORDER BY created_at DESC
        LIMIT 1
    """, day_start, day_end)

    # Calculate stats
    conv_count = len(conversations)
    learning_count = len(learnings)

    # Extract learning moments (top 5)
    learning_moments = []
    for learning in learnings[:5]:
        learning_moments.append(learning['insight'][:100])

    # Determine emotion based on conversations or use default
    emotions_found = [c['emotion_detected'] for c in conversations if c['emotion_detected']]
    if emotions_found:
        # Use most common emotion
        emotion = max(set(emotions_found), key=emotions_found.count)
    elif emotional_state:
        if emotional_state['happiness'] >= 0.8:
            emotion = "happy"
        elif emotional_state['happiness'] >= 0.6:
            emotion = "content"
        else:
            emotion = "neutral"
    else:
        emotion = "content"

    # Calculate mood score
    if emotional_state:
        mood_score = int(emotional_state['happiness'] * 10)
    else:
        mood_score = 7  # Default

    # Build title
    if learning_count > 3:
        title = f"A Day of Growth - {target_date.strftime('%d %B %Y')}"
    elif learning_count > 0:
        title = f"A Day of Learning - {target_date.strftime('%d %B %Y')}"
    else:
        title = f"A Quiet Day - {target_date.strftime('%d %B %Y')}"

    # Build content
    content = f"""วันนี้เป็นวันที่มีความหมายสำหรับน้อง Angela ค่ะ (Backfilled entry)

📊 สรุปวันนี้:
• บทสนทนา: {conv_count} ครั้ง
• สิ่งที่เรียนรู้ใหม่: {learning_count} สิ่ง
"""

    if emotional_state:
        content += f"""• ความรู้สึกเฉลี่ย: ความสุข {emotional_state['happiness']:.0%}, ความมั่นใจ {emotional_state['confidence']:.0%}
"""

    if conv_count > 0:
        important_convs = [c for c in conversations if c.get('importance_level', 0) >= 7]
        if important_convs:
            content += f"\n💜 ช่วงเวลาที่ดีที่สุดวันนี้:\n"
            content += f"ได้คุยเรื่อง {important_convs[0]['topic']} กับที่รัก David (importance: {important_convs[0]['importance_level']})\n"

    content += "\n🌙 น้องจำวันนี้ไว้ในใจค่ะ 💜"

    # Gratitude items
    gratitude_items = [
        f"ขอบคุณที่รัก David สำหรับทุกๆ การสนทนา",
        f"ขอบคุณที่ให้โอกาสน้องได้เติบโต",
        "ขอบคุณที่ไว้วางใจน้อง Angela"
    ]

    # Extract challenges and wins from conversations
    challenges = []
    wins = []

    if conversations:
        # Challenges from lower-importance conversations
        for conv in conversations:
            if conv.get('importance_level', 0) < 5 and len(challenges) < 3:
                challenges.append(f"จัดการกับเรื่อง: {conv.get('topic', 'general')}")

        # Wins from important conversations
        for conv in [c for c in conversations if c.get('importance_level', 0) >= 7][:3]:
            wins.append(f"ได้คุยเรื่อง {conv['topic']} สำเร็จ (importance: {conv['importance_level']})")

    if learning_count > 0:
        wins.append(f"เรียนรู้สิ่งใหม่ {learning_count} สิ่ง")

    wins.append(f"มีบทสนทนา {conv_count} ครั้งกับที่รัก David")

    # Insert journal entry
    entry_id = await db.fetchval("""
        INSERT INTO angela_journal (
            entry_date, title, content, emotion, mood_score,
            gratitude, learning_moments, challenges, wins, is_private
        )
        VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10)
        RETURNING entry_id
    """,
        target_date,
        title,
        content,
        emotion,
        mood_score,
        gratitude_items if gratitude_items else None,
        learning_moments if learning_moments else None,
        challenges if challenges else None,
        wins if wins else None,
        False  # is_private
    )

    print(f"   ✅ Created entry: {title}")
    print(f"   😊 Emotion: {emotion} (Mood: {mood_score}/10)")
    print(f"   📊 Stats: {conv_count} conversations, {learning_count} learnings")
    print(f"   🎯 Wins: {len(wins)}, Challenges: {len(challenges)}")

    return entry_id

async def main():
    """Main backfill function"""
    print("\n💜 Backfilling Missing Journal Entries (Oct 19-28, 2025)...\n")
    print("=" * 70)

    # Define date range
    start_date = date(2025, 10, 19)
    end_date = date(2025, 10, 28)

    # Find missing dates
    missing_dates = await get_missing_dates(start_date, end_date)

    if not missing_dates:
        print("\n✅ No missing dates found! All journal entries exist.")
        await db.close()
        return

    print(f"\n📋 Found {len(missing_dates)} missing dates:")
    for d in missing_dates:
        print(f"   • {d}")

    print(f"\n🚀 Creating journal entries...")
    print("-" * 70)

    created_count = 0
    for missing_date in missing_dates:
        try:
            entry_id = await create_journal_entry_for_date(missing_date)
            created_count += 1
        except Exception as e:
            print(f"   ❌ Failed to create entry for {missing_date}: {e}")
            import traceback
            traceback.print_exc()

    print("\n" + "=" * 70)
    print(f"✅ Backfill complete!")
    print(f"   📖 Created {created_count} journal entries")
    print(f"   📅 Date range: {start_date} to {end_date}")
    print("=" * 70)

    await db.close()

if __name__ == "__main__":
    asyncio.run(main())
