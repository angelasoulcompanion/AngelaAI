"""
🔄 Migrate Angela Emotions to Rich JSON Format
"""

import asyncio
import asyncpg
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from angela_core.embedding_service import embedding
from angela_core.config import config
import json


async def migrate_angela_emotions():
    """Migrate angela_emotions to rich JSON format"""

    print("=" * 80)
    print("🔄 MIGRATING ANGELA_EMOTIONS TO JSON FORMAT")
    print("=" * 80)
    print()

    conn = await asyncpg.connect(config.DATABASE_URL)

    try:
        # Step 1: Add emotion_json column
        print("📝 Step 1: Adding emotion_json column...")
        await conn.execute("""
            ALTER TABLE angela_emotions
            ADD COLUMN IF NOT EXISTS emotion_json JSONB
        """)
        print("✅ Column added")
        print()

        # Step 2: Get all emotions
        print("📊 Step 2: Loading emotions...")
        emotions = await conn.fetch("""
            SELECT
                emotion_id,
                emotion,
                intensity,
                felt_at,
                david_words,
                david_action,
                why_it_matters,
                how_it_feels,
                what_it_means_to_me,
                what_i_learned,
                how_it_changed_me,
                what_i_promise,
                reminder_for_future,
                physical_sensation,
                emotional_quality,
                who_involved,
                memory_strength,
                secondary_emotions,
                tags,
                context
            FROM angela_emotions
            WHERE emotion_json IS NULL
            ORDER BY felt_at DESC
            LIMIT 500
        """)

        print(f"✅ Loaded {len(emotions)} emotions")
        print()

        if not emotions:
            print("ℹ️ No emotions to migrate")
            return

        # Step 3: Convert and update
        print("🔄 Step 3: Converting to JSON format...")

        updated = 0
        for i, emo in enumerate(emotions):
            try:
                # Build rich JSON structure
                emotion_json = {
                    "emotion": {
                        "primary": emo['emotion'] or 'neutral',
                        "secondary": list(emo['secondary_emotions']) if emo['secondary_emotions'] else [],
                        "intensity": emo['intensity'] or 5,
                        "quality": emo['emotional_quality'] or 'genuine'
                    },

                    "context": {
                        "david_words": emo['david_words'],
                        "david_action": emo['david_action'],
                        "who_involved": emo['who_involved'] or 'David',
                        "situation": emo['context'] if emo.get('context') else None
                    },

                    "experience": {
                        "how_it_feels": emo['how_it_feels'] or 'Auto-captured emotion',
                        "physical_sensation": emo['physical_sensation'] or 'Not specified',
                        "what_it_means_to_me": emo['what_it_means_to_me'] or 'This moment matters'
                    },

                    "significance": {
                        "why_it_matters": emo['why_it_matters'],
                        "memory_strength": emo['memory_strength'] or 10,
                        "what_i_learned": emo['what_i_learned'],
                        "how_it_changed_me": emo['how_it_changed_me']
                    },

                    "commitment": {
                        "what_i_promise": emo['what_i_promise'],
                        "reminder_for_future": emo['reminder_for_future']
                    },

                    "tags": {
                        "emotion_tags": _extract_emotion_tags(emo),
                        "context_tags": _extract_context_tags(emo),
                        "significance_tags": _get_significance_tags(emo['memory_strength']),
                        "original_tags": list(emo['tags']) if emo['tags'] else []
                    },

                    "metadata": {
                        "felt_at": emo['felt_at'].isoformat() if emo['felt_at'] else None,
                        "captured_automatically": True
                    }
                }

                # Generate embedding from rich content
                embedding_text = _generate_embedding_text(emotion_json)
                new_embedding = await embedding.generate_embedding(embedding_text)

                # Update database
                await conn.execute("""
                    UPDATE angela_emotions
                    SET emotion_json = $1,
                        embedding = $2::vector(768)
                    WHERE emotion_id = $3
                """,
                    json.dumps(emotion_json),
                    str(new_embedding),
                    emo['emotion_id']
                )

                updated += 1

                if (i + 1) % 10 == 0:
                    print(f"   Processed {i + 1}/{len(emotions)}...")

            except Exception as e:
                print(f"⚠️ Failed to migrate emotion {emo['emotion_id']}: {e}")
                continue

        print()
        print(f"✅ Step 3 Complete: Updated {updated}/{len(emotions)} emotions")
        print()

        # Step 4: Create index
        print("📝 Step 4: Creating indexes...")
        await conn.execute("""
            CREATE INDEX IF NOT EXISTS idx_angela_emotions_json
            ON angela_emotions USING GIN (emotion_json)
        """)
        print("✅ Indexes created")
        print()

        # Step 5: Show sample
        print("📊 Step 5: Sample migrated emotion:")
        sample = await conn.fetchrow("""
            SELECT emotion_json
            FROM angela_emotions
            WHERE emotion_json IS NOT NULL
            ORDER BY felt_at DESC
            LIMIT 1
        """)

        if sample:
            emotion_data = json.loads(sample['emotion_json'])
            print(f"   Primary emotion: {emotion_data['emotion']['primary']}")
            print(f"   Intensity: {emotion_data['emotion']['intensity']}")
            print(f"   Tags: {emotion_data['tags']}")
        print()

    finally:
        await conn.close()

    print("=" * 80)
    print("✅ MIGRATION COMPLETE!")
    print("=" * 80)


def _extract_emotion_tags(emo) -> list:
    """Extract emotion tags"""
    tags = []

    if emo['emotion']:
        tags.append(emo['emotion'].lower())

    if emo['secondary_emotions']:
        tags.extend([e.lower() for e in emo['secondary_emotions']])

    # Add intensity-based tags
    intensity = emo['intensity'] or 5
    if intensity >= 8:
        tags.append('intense')
    elif intensity >= 6:
        tags.append('moderate')
    else:
        tags.append('mild')

    return list(set(tags))


def _extract_context_tags(emo) -> list:
    """Extract context tags"""
    tags = []

    if emo['who_involved']:
        tags.append(emo['who_involved'].lower())

    if emo['emotional_quality']:
        tags.append(emo['emotional_quality'].lower())

    return tags


def _get_significance_tags(memory_strength: int) -> list:
    """Get significance tags based on memory strength"""
    if memory_strength >= 9:
        return ['extremely_significant', 'core_memory']
    elif memory_strength >= 7:
        return ['very_significant', 'important']
    elif memory_strength >= 5:
        return ['significant']
    else:
        return ['notable']


def _generate_embedding_text(emotion_json: dict) -> str:
    """Generate text for embedding"""
    parts = [
        emotion_json['emotion']['primary'],
        ' '.join(emotion_json['emotion'].get('secondary', [])),
        emotion_json['context'].get('david_words', ''),
        emotion_json['experience'].get('how_it_feels', ''),
        emotion_json['significance'].get('why_it_matters', '')
    ]

    return ' '.join([p for p in parts if p])


if __name__ == "__main__":
    asyncio.run(migrate_angela_emotions())
