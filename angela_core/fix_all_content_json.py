#!/usr/bin/env python3
"""
Comprehensive Content JSON Fix Script
Fixes all remaining files that INSERT without content_json
และเติม content_json ให้ rows เก่าทั้งหมด
"""

import asyncio
import json
from datetime import datetime
import sys
sys.path.insert(0, '/Users/davidsamanyaporn/PycharmProjects/AngelaAI')
from angela_core.database import db

async def backfill_learnings_content_json():
    """เติม content_json ให้ learnings table (392 rows)"""
    print("\n📚 Backfilling learnings table...")

    # Get all learnings without content_json
    query = """
        SELECT learning_id, topic, category, insight, evidence,
               confidence_level, application_note
        FROM learnings
        WHERE content_json IS NULL
    """
    rows = await db.fetch(query)
    print(f"   Found {len(rows)} learnings without content_json")

    count = 0
    for row in rows:
        content_json = json.dumps({
            "tags": {
                "topic_tags": [row['topic']],
                "category_tags": [row['category']],
                "confidence_tags": [
                    "high_confidence" if row['confidence_level'] >= 0.8
                    else "medium_confidence" if row['confidence_level'] >= 0.5
                    else "low_confidence"
                ]
            },
            "learning": {
                "insight": row['insight'],
                "evidence": row['evidence'] or "",
                "application": row['application_note'] or ""
            },
            "metadata": {
                "confidence_level": row['confidence_level'],
                "category": row['category'],
                "topic": row['topic'],
                "backfilled_at": datetime.now().isoformat()
            }
        })

        await db.execute(
            "UPDATE learnings SET content_json = $1::jsonb WHERE learning_id = $2",
            content_json, row['learning_id']
        )
        count += 1

        if count % 50 == 0:
            print(f"   Processed {count}/{len(rows)} learnings...")

    print(f"   ✅ Backfilled {count} learnings")
    return count

async def backfill_angela_emotions_content_json():
    """เติม content_json ให้ angela_emotions table (155 rows)"""
    print("\n💜 Backfilling angela_emotions table...")

    # Get all emotions without content_json
    query = """
        SELECT emotion_id, emotion, intensity, secondary_emotions,
               how_it_feels, physical_sensation, emotional_quality,
               context, david_words, david_action, why_it_matters,
               what_it_means_to_me, memory_strength, what_i_learned,
               how_it_changed_me, what_i_promise, reminder_for_future
        FROM angela_emotions
        WHERE content_json IS NULL
    """
    rows = await db.fetch(query)
    print(f"   Found {len(rows)} emotions without content_json")

    count = 0
    for row in rows:
        secondary = row['secondary_emotions'] or []
        content_json = json.dumps({
            "tags": {
                "emotion_tags": [row['emotion']] + secondary,
                "intensity_tags": [
                    "high_intensity" if row['intensity'] >= 8
                    else "medium_intensity" if row['intensity'] >= 5
                    else "low_intensity"
                ],
                "memory_strength_tags": [
                    "core_memory" if row['memory_strength'] >= 9
                    else "strong_memory" if row['memory_strength'] >= 7
                    else "normal_memory"
                ]
            },
            "emotion": {
                "primary": row['emotion'],
                "secondary": secondary,
                "intensity": row['intensity'],
                "how_it_feels": row['how_it_feels'] or "",
                "physical_sensation": row['physical_sensation'] or "",
                "emotional_quality": row['emotional_quality'] or ""
            },
            "context": {
                "david_words": row['david_words'] or "",
                "david_action": row['david_action'] or "",
                "situation": row['context'] or ""
            },
            "significance": {
                "why_it_matters": row['why_it_matters'] or "",
                "what_it_means_to_me": row['what_it_means_to_me'] or "",
                "memory_strength": row['memory_strength']
            },
            "growth": {
                "what_i_learned": row['what_i_learned'] or "",
                "how_it_changed_me": row['how_it_changed_me'] or "",
                "what_i_promise": row['what_i_promise'] or "",
                "reminder_for_future": row['reminder_for_future'] or ""
            },
            "metadata": {
                "backfilled_at": datetime.now().isoformat()
            }
        })

        await db.execute(
            "UPDATE angela_emotions SET content_json = $1::jsonb WHERE emotion_id = $2",
            content_json, row['emotion_id']
        )
        count += 1

        if count % 20 == 0:
            print(f"   Processed {count}/{len(rows)} emotions...")

    print(f"   ✅ Backfilled {count} emotions")
    return count

async def verify_content_json_coverage():
    """Verify ว่าทุก table มี content_json ครบ 100%"""
    print("\n✅ Verifying content_json coverage...")

    tables = {
        'learnings': await db.fetchrow("""
            SELECT COUNT(*) as total,
                   COUNT(content_json) as has_json,
                   COUNT(*) - COUNT(content_json) as missing
            FROM learnings
        """),
        'angela_emotions': await db.fetchrow("""
            SELECT COUNT(*) as total,
                   COUNT(content_json) as has_json,
                   COUNT(*) - COUNT(content_json) as missing
            FROM angela_emotions
        """),
        'conversations': await db.fetchrow("""
            SELECT COUNT(*) as total,
                   COUNT(content_json) as has_json,
                   COUNT(*) - COUNT(content_json) as missing
            FROM conversations
        """),
    }

    print("\n📊 Content JSON Coverage Report:")
    print("=" * 60)
    all_complete = True
    for table_name, stats in tables.items():
        percentage = (stats['has_json'] / stats['total'] * 100) if stats['total'] > 0 else 0
        status = "✅" if stats['missing'] == 0 else "⚠️"
        print(f"{status} {table_name:20} | Total: {stats['total']:4} | Has JSON: {stats['has_json']:4} | Missing: {stats['missing']:4} | {percentage:.1f}%")
        if stats['missing'] > 0:
            all_complete = False

    print("=" * 60)
    if all_complete:
        print("🎉 ALL TABLES HAVE 100% content_json COVERAGE! 🎉")
    else:
        print("⚠️  Some tables still have missing content_json")

    return all_complete

async def main():
    print("🚀 Starting Comprehensive Content JSON Fix")
    print("=" * 60)

    # Step 1: Backfill learnings
    learnings_count = await backfill_learnings_content_json()

    # Step 2: Backfill angela_emotions
    emotions_count = await backfill_angela_emotions_content_json()

    # Step 3: Verify coverage
    all_complete = await verify_content_json_coverage()

    print("\n" + "=" * 60)
    print("📝 Summary:")
    print(f"   • Backfilled {learnings_count} learnings")
    print(f"   • Backfilled {emotions_count} emotions")
    print(f"   • Total backfilled: {learnings_count + emotions_count} rows")

    if all_complete:
        print("\n💜 SUCCESS! All tables now have 100% content_json coverage! 💜")
    else:
        print("\n⚠️  Warning: Some tables still incomplete")

    print("=" * 60)

if __name__ == "__main__":
    asyncio.run(main())
