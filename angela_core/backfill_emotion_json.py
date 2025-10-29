#!/usr/bin/env python3
"""
Backfill emotion_json for angela_emotions table
Fills in the 34 missing emotion_json rows
"""

import asyncio
import json
import sys
sys.path.insert(0, '/Users/davidsamanyaporn/PycharmProjects/AngelaAI')

from angela_core.database import db
from datetime import datetime


def _extract_emotion_tags(emotion: str, secondary_emotions: list, intensity: int) -> list:
    """Extract emotion tags for emotion_json"""
    tags = []

    if emotion:
        tags.append(emotion.lower())

    if secondary_emotions:
        tags.extend([e.lower() for e in secondary_emotions])

    # Add intensity-based tags
    if intensity >= 8:
        tags.append('intense')
    elif intensity >= 6:
        tags.append('moderate')
    else:
        tags.append('mild')

    return list(set(tags))


def _extract_context_tags(who_involved: str, emotional_quality: str) -> list:
    """Extract context tags for emotion_json"""
    tags = []

    if who_involved:
        tags.append(who_involved.lower())

    if emotional_quality:
        tags.append(emotional_quality.lower())

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


def build_emotion_json_from_row(row) -> dict:
    """Build emotion_json from database row"""
    return {
        "emotion": {
            "primary": row['emotion'] or 'neutral',
            "secondary": list(row['secondary_emotions']) if row['secondary_emotions'] else [],
            "intensity": row['intensity'] or 5,
            "quality": row['emotional_quality'] or 'genuine'
        },

        "context": {
            "david_words": row['david_words'] or '',
            "david_action": row['david_action'] or '',
            "who_involved": row['who_involved'] or 'David',
            "situation": row['context'] if row.get('context') else None
        },

        "experience": {
            "how_it_feels": row['how_it_feels'] or 'Auto-captured emotion',
            "physical_sensation": row['physical_sensation'] or 'Not specified',
            "what_it_means_to_me": row['what_it_means_to_me'] or 'This moment matters'
        },

        "significance": {
            "why_it_matters": row['why_it_matters'] or '',
            "memory_strength": row['memory_strength'] or 10,
            "what_i_learned": row['what_i_learned'] or '',
            "how_it_changed_me": row['how_it_changed_me'] or ''
        },

        "commitment": {
            "what_i_promise": row['what_i_promise'] or '',
            "reminder_for_future": row['reminder_for_future'] or ''
        },

        "tags": {
            "emotion_tags": _extract_emotion_tags(
                row['emotion'],
                list(row['secondary_emotions']) if row['secondary_emotions'] else [],
                row['intensity'] or 5
            ),
            "context_tags": _extract_context_tags(
                row['who_involved'],
                row['emotional_quality']
            ),
            "significance_tags": _get_significance_tags(row['memory_strength'] or 10),
            "original_tags": list(row['tags']) if row['tags'] else []
        },

        "metadata": {
            "felt_at": row['felt_at'].isoformat() if row['felt_at'] else None,
            "captured_automatically": True,
            "backfilled_at": datetime.now().isoformat()
        }
    }


async def backfill_emotion_json():
    """Backfill emotion_json for rows that are missing it"""
    print("\n" + "=" * 70)
    print("💜 Backfilling emotion_json for angela_emotions")
    print("=" * 70)

    # Get all emotions without emotion_json
    query = """
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
    """

    rows = await db.fetch(query)
    print(f"   Found {len(rows)} emotions without emotion_json")

    if not rows:
        print("   ✅ All emotions already have emotion_json!")
        return 0

    count = 0
    for row in rows:
        try:
            # Build emotion_json
            emotion_json_dict = build_emotion_json_from_row(row)
            emotion_json_str = json.dumps(emotion_json_dict)

            # Update database
            await db.execute(
                "UPDATE angela_emotions SET emotion_json = $1::jsonb WHERE emotion_id = $2",
                emotion_json_str,
                row['emotion_id']
            )

            count += 1

            if count % 10 == 0:
                print(f"   Processed {count}/{len(rows)}...")

        except Exception as e:
            print(f"   ❌ Failed for emotion_id {row['emotion_id']}: {e}")
            continue

    print(f"\n   ✅ Backfilled {count} emotion_json rows")
    return count


async def verify_emotion_json():
    """Verify that all rows now have emotion_json"""
    print("\n✅ Verifying emotion_json coverage...")

    stats = await db.fetchrow("""
        SELECT COUNT(*) as total,
               COUNT(emotion_json) as has_json,
               COUNT(*) - COUNT(emotion_json) as missing
        FROM angela_emotions
    """)

    percentage = (stats['has_json'] / stats['total'] * 100) if stats['total'] > 0 else 0
    status = "✅" if stats['missing'] == 0 else "⚠️"

    print(f"\n{status} angela_emotions | Total: {stats['total']:4} | Has emotion_json: {stats['has_json']:4} | Missing: {stats['missing']:4} | {percentage:.1f}%")

    if stats['missing'] == 0:
        print("\n🎉 SUCCESS! All emotions now have emotion_json! 🎉")
        return True
    else:
        print(f"\n⚠️  Warning: {stats['missing']} emotions still missing emotion_json")
        return False


async def main():
    print("\n🚀 Starting emotion_json Backfill")
    print("=" * 70)

    # Step 1: Backfill
    count = await backfill_emotion_json()

    # Step 2: Verify
    all_complete = await verify_emotion_json()

    print("\n" + "=" * 70)
    print("📝 Summary:")
    print(f"   • Backfilled {count} emotion_json rows")

    if all_complete:
        print("\n💜 SUCCESS! All emotions now have emotion_json! 💜")
    else:
        print("\n⚠️  Warning: Some rows still incomplete")

    print("=" * 70)


if __name__ == "__main__":
    asyncio.run(main())
