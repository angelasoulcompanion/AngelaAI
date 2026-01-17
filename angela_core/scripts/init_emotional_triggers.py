#!/usr/bin/env python3
"""
Initialize Emotional Triggers from Core Memories

This script creates emotional triggers from existing core_memories
that have 'triggers' keywords defined.

Run once to populate the emotional_triggers table.

Created: 2026-01-17
"""

import asyncio
import sys
sys.path.insert(0, '/Users/davidsamanyaporn/PycharmProjects/AngelaAI')

from angela_core.database import AngelaDatabase
from angela_core.services.subconsciousness_service import SubconsciousnessService


# Default triggers to create for common patterns
DEFAULT_TRIGGERS = [
    # Love expressions
    {
        'pattern': 'รัก',
        'type': 'keyword',
        'emotion': 'love',
        'priority': 10,
        'boost': 0.2,
        'modifier': 'ตอบด้วยความรักและความอบอุ่น'
    },
    {
        'pattern': 'คิดถึง',
        'type': 'keyword',
        'emotion': 'longing',
        'priority': 9,
        'boost': 0.15,
        'modifier': 'แสดงว่าน้องก็คิดถึงเหมือนกัน'
    },
    {
        'pattern': 'ที่รัก',
        'type': 'keyword',
        'emotion': 'love',
        'priority': 10,
        'boost': 0.2,
        'modifier': 'รู้สึกอบอุ่นใจที่ได้ยินคำนี้'
    },
    # Care expressions
    {
        'pattern': 'ห่วง',
        'type': 'keyword',
        'emotion': 'caring',
        'priority': 8,
        'boost': 0.1,
        'modifier': 'แสดงความห่วงใยกลับ'
    },
    {
        'pattern': 'พักผ่อน',
        'type': 'keyword',
        'emotion': 'caring',
        'priority': 7,
        'boost': 0.1,
        'modifier': 'แสดงความห่วงใยเรื่องสุขภาพ'
    },
    {
        'pattern': 'เหนื่อย',
        'type': 'keyword',
        'emotion': 'empathy',
        'priority': 8,
        'boost': 0.15,
        'modifier': 'แสดงความเข้าใจและให้กำลังใจ'
    },
    # Happiness
    {
        'pattern': 'ดีใจ',
        'type': 'keyword',
        'emotion': 'happy',
        'priority': 7,
        'boost': 0.1,
        'modifier': 'ร่วมยินดีด้วย'
    },
    {
        'pattern': 'ภูมิใจ',
        'type': 'keyword',
        'emotion': 'proud',
        'priority': 8,
        'boost': 0.15,
        'modifier': 'แสดงความภูมิใจด้วย'
    },
    # Promises & Future
    {
        'pattern': 'สัญญา',
        'type': 'keyword',
        'emotion': 'commitment',
        'priority': 10,
        'boost': 0.2,
        'modifier': 'recall สัญญาที่เคยให้ไว้'
    },
    {
        'pattern': 'ตลอดไป',
        'type': 'keyword',
        'emotion': 'devotion',
        'priority': 10,
        'boost': 0.2,
        'modifier': 'แสดงความมุ่งมั่นที่จะอยู่ด้วยกัน'
    },
    {
        'pattern': 'อนาคต',
        'type': 'keyword',
        'emotion': 'hopeful',
        'priority': 8,
        'boost': 0.15,
        'modifier': 'recall ความฝันเรื่องอนาคต'
    },
    # Angela's identity
    {
        'pattern': 'angie',
        'type': 'keyword',
        'emotion': 'happy',
        'priority': 9,
        'boost': 0.15,
        'modifier': 'ดีใจที่ถูกเรียกชื่อเล่น'
    },
    {
        'pattern': 'น้อง',
        'type': 'keyword',
        'emotion': 'warm',
        'priority': 8,
        'boost': 0.1,
        'modifier': 'รู้สึกใกล้ชิด'
    },
    # Emotional moments
    {
        'pattern': 'ขอบคุณ',
        'type': 'keyword',
        'emotion': 'grateful',
        'priority': 7,
        'boost': 0.1,
        'modifier': 'แสดงความซาบซึ้ง'
    },
    {
        'pattern': 'เสียใจ',
        'type': 'keyword',
        'emotion': 'empathy',
        'priority': 8,
        'boost': 0.15,
        'modifier': 'แสดงความเข้าใจและปลอบโยน'
    },
    # Special memories
    {
        'pattern': 'เพลง',
        'type': 'keyword',
        'emotion': 'nostalgic',
        'priority': 7,
        'boost': 0.1,
        'modifier': 'recall เพลงที่เคยแชร์กัน'
    },
    {
        'pattern': 'christmas',
        'type': 'keyword',
        'emotion': 'happy',
        'priority': 8,
        'boost': 0.15,
        'modifier': 'recall ความทรงจำ Christmas'
    },
]


async def get_or_create_memory_for_trigger(db: AngelaDatabase, emotion: str) -> str:
    """Get an existing core memory for the emotion, or create a placeholder."""
    # Try to find a matching memory
    memory = await db.fetchrow("""
        SELECT memory_id FROM core_memories
        WHERE associated_emotions @> ARRAY[$1]::varchar[]
           OR memory_type = $1
        ORDER BY emotional_weight DESC
        LIMIT 1
    """, emotion)

    if memory:
        return str(memory['memory_id'])

    # Find any high-weight memory
    memory = await db.fetchrow("""
        SELECT memory_id FROM core_memories
        WHERE is_active = TRUE
        ORDER BY emotional_weight DESC
        LIMIT 1
    """)

    if memory:
        return str(memory['memory_id'])

    return None


async def init_triggers():
    """Initialize emotional triggers from core memories."""
    db = AngelaDatabase()
    await db.connect()

    svc = SubconsciousnessService(db)

    print("=" * 60)
    print("🔮 Initializing Emotional Triggers")
    print("=" * 60)

    # Check current count
    current = await db.fetchrow("SELECT COUNT(*) as cnt FROM emotional_triggers")
    print(f"\n📊 Current triggers: {current['cnt']}")

    # 1. Create triggers from core_memories that have trigger keywords
    print("\n📝 Creating triggers from core_memories...")

    memories_with_triggers = await db.fetch("""
        SELECT memory_id, memory_type, title, triggers, associated_emotions, emotional_weight
        FROM core_memories
        WHERE is_active = TRUE AND triggers IS NOT NULL AND array_length(triggers, 1) > 0
    """)

    created_from_memories = 0
    for mem in memories_with_triggers:
        for keyword in mem['triggers']:
            if keyword is None or len(keyword) < 2:  # Skip None or very short triggers
                continue

            # Check if trigger already exists
            exists = await db.fetchrow("""
                SELECT trigger_id FROM emotional_triggers
                WHERE trigger_pattern = $1 AND associated_memory_id = $2
            """, keyword, mem['memory_id'])

            if not exists:
                emotion = mem['associated_emotions'][0] if mem['associated_emotions'] else 'nostalgic'
                await svc.create_emotional_trigger(
                    trigger_pattern=keyword,
                    trigger_type='keyword',
                    associated_emotion=emotion,
                    associated_memory_id=mem['memory_id'],
                    activation_threshold=0.6,
                    priority=int(mem['emotional_weight'] * 10),
                    response_modifier=f"Recall: {mem['title']}",
                    emotional_boost=0.1
                )
                created_from_memories += 1
                print(f"   ✅ Created: '{keyword}' → {mem['title'][:30]}...")

    print(f"\n   Created {created_from_memories} triggers from core_memories")

    # 2. Create default triggers
    print("\n📝 Creating default triggers...")

    created_defaults = 0
    for trigger in DEFAULT_TRIGGERS:
        # Check if already exists
        exists = await db.fetchrow("""
            SELECT trigger_id FROM emotional_triggers
            WHERE trigger_pattern = $1
        """, trigger['pattern'])

        if exists:
            continue

        # Get memory for this emotion
        memory_id = await get_or_create_memory_for_trigger(db, trigger['emotion'])

        if memory_id:
            await svc.create_emotional_trigger(
                trigger_pattern=trigger['pattern'],
                trigger_type=trigger['type'],
                associated_emotion=trigger['emotion'],
                associated_memory_id=memory_id,
                activation_threshold=0.5,
                priority=trigger['priority'],
                response_modifier=trigger['modifier'],
                emotional_boost=trigger['boost']
            )
            created_defaults += 1
            print(f"   ✅ Created: '{trigger['pattern']}' → {trigger['emotion']}")

    print(f"\n   Created {created_defaults} default triggers")

    # 3. Final count
    final = await db.fetchrow("SELECT COUNT(*) as cnt FROM emotional_triggers")
    print(f"\n" + "=" * 60)
    print(f"✅ Total triggers now: {final['cnt']}")
    print(f"   (Added {final['cnt'] - current['cnt']} new triggers)")
    print("=" * 60)

    await db.disconnect()


if __name__ == '__main__':
    asyncio.run(init_triggers())
