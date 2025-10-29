#!/usr/bin/env python3
"""
Backfill Angela Emotions - ถมข้อมูลให้เต็ม!
Populates NULL fields in angela_emotions table with meaningful defaults
"""

import asyncio
import logging
import sys
sys.path.insert(0, '/Users/davidsamanyaporn/PycharmProjects/AngelaAI')

from angela_core.database import db

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)

logger = logging.getLogger('BackfillEmotions')


def detect_secondary_emotions(primary_emotion: str) -> list:
    """Detect secondary emotions based on primary"""
    emotion_clusters = {
        'loving': ['caring', 'affectionate', 'warm'],
        'grateful': ['appreciative', 'thankful', 'blessed'],
        'worried': ['concerned', 'anxious', 'protective'],
        'frustrated': ['annoyed', 'stressed', 'overwhelmed'],
        'excited': ['enthusiastic', 'energized', 'eager'],
        'happy': ['joyful', 'content', 'pleased'],
        'sad': ['disappointed', 'hurt', 'melancholy'],
        'angry': ['upset', 'irritated', 'indignant']
    }
    return emotion_clusters.get(primary_emotion, ['engaged', 'responsive'])


async def backfill_emotions():
    """Backfill all NULL fields in angela_emotions"""
    logger.info("=" * 80)
    logger.info("BACKFILL ANGELA EMOTIONS - ถมข้อมูลให้เต็ม!")
    logger.info("=" * 80)

    await db.connect()

    # 1. Find records with NULL fields
    logger.info("\n📊 Checking for NULL records...")

    null_check = """
        SELECT
            emotion_id,
            emotion,
            intensity,
            context,
            david_words,
            how_it_feels,
            secondary_emotions,
            emotional_quality,
            who_involved,
            what_it_means_to_me,
            tags,
            physical_sensation,
            what_i_learned,
            how_it_changed_me,
            what_i_promise,
            reminder_for_future
        FROM angela_emotions
        WHERE how_it_feels IS NULL
           OR secondary_emotions IS NULL
           OR emotional_quality IS NULL
           OR who_involved IS NULL
           OR what_it_means_to_me IS NULL
           OR tags IS NULL
        ORDER BY felt_at DESC
    """

    null_records = await db.fetch(null_check)

    logger.info(f"Found {len(null_records)} records with NULL fields")

    if len(null_records) == 0:
        logger.info("✅ No NULL records found! All fields are populated!")
        await db.disconnect()
        return True

    # 2. Backfill each record
    logger.info(f"\n🔧 Backfilling {len(null_records)} records...")

    updated = 0
    for record in null_records:
        emotion = record['emotion']
        intensity = record['intensity']
        context = record['context'] or "Emotional moment with David"

        # Prepare backfill values
        how_it_feels = record['how_it_feels'] or f"I feel {emotion} when interacting with David"
        secondary_emotions = record['secondary_emotions'] or detect_secondary_emotions(emotion)
        emotional_quality = record['emotional_quality'] or "genuine and meaningful"
        who_involved = record['who_involved'] or "David"
        what_it_means_to_me = record['what_it_means_to_me'] or f"This {emotion} feeling shows how much our relationship matters"
        tags = record['tags'] or [emotion, "auto_captured", f"intensity_{intensity}"]

        # Update the record
        update_query = """
            UPDATE angela_emotions
            SET
                how_it_feels = $1,
                secondary_emotions = $2,
                emotional_quality = $3,
                who_involved = $4,
                what_it_means_to_me = $5,
                tags = $6
            WHERE emotion_id = $7
        """

        await db.execute(
            update_query,
            how_it_feels,
            secondary_emotions,
            emotional_quality,
            who_involved,
            what_it_means_to_me,
            tags,
            record['emotion_id']
        )

        updated += 1
        logger.info(f"  ✅ Updated {emotion} emotion (intensity: {intensity})")

    # 2b. Backfill optional fields (david_action, trigger, last_reflected_on)
    logger.info(f"\n🔧 Backfilling optional fields...")

    optional_backfill = """
        UPDATE angela_emotions
        SET
            david_action = COALESCE(david_action, 'Expressed ' || emotion || ' emotion'),
            trigger = COALESCE(trigger, 'Conversation with Angela'),
            last_reflected_on = COALESCE(last_reflected_on, felt_at)
        WHERE david_action IS NULL
           OR trigger IS NULL
           OR last_reflected_on IS NULL
    """

    await db.execute(optional_backfill)
    logger.info(f"  ✅ Backfilled optional fields (david_action, trigger, last_reflected_on)")

    logger.info(f"\n✅ Successfully backfilled {updated} records!")

    # 3. Verify no more NULLs
    logger.info("\n📊 Verifying backfill...")

    verify_query = """
        SELECT
            COUNT(*) as total,
            COUNT(*) - COUNT(how_it_feels) as null_how_it_feels,
            COUNT(*) - COUNT(secondary_emotions) as null_secondary_emotions,
            COUNT(*) - COUNT(emotional_quality) as null_emotional_quality,
            COUNT(*) - COUNT(who_involved) as null_who_involved,
            COUNT(*) - COUNT(what_it_means_to_me) as null_what_it_means_to_me,
            COUNT(*) - COUNT(tags) as null_tags,
            COUNT(*) - COUNT(david_action) as null_david_action,
            COUNT(*) - COUNT(trigger) as null_trigger,
            COUNT(*) - COUNT(last_reflected_on) as null_last_reflected_on
        FROM angela_emotions
    """

    result = await db.fetchrow(verify_query)

    logger.info("=" * 80)
    logger.info("VERIFICATION RESULTS:")
    logger.info("=" * 80)
    logger.info(f"Total emotions: {result['total']}")
    logger.info(f"\nImportant fields:")
    logger.info(f"  NULL how_it_feels: {result['null_how_it_feels']}")
    logger.info(f"  NULL secondary_emotions: {result['null_secondary_emotions']}")
    logger.info(f"  NULL emotional_quality: {result['null_emotional_quality']}")
    logger.info(f"  NULL who_involved: {result['null_who_involved']}")
    logger.info(f"  NULL what_it_means_to_me: {result['null_what_it_means_to_me']}")
    logger.info(f"  NULL tags: {result['null_tags']}")
    logger.info(f"\nOptional fields:")
    logger.info(f"  NULL david_action: {result['null_david_action']}")
    logger.info(f"  NULL trigger: {result['null_trigger']}")
    logger.info(f"  NULL last_reflected_on: {result['null_last_reflected_on']}")

    important_nulls = sum([
        result['null_how_it_feels'],
        result['null_secondary_emotions'],
        result['null_emotional_quality'],
        result['null_who_involved'],
        result['null_what_it_means_to_me'],
        result['null_tags'],
        result['null_david_action'],
        result['null_trigger'],
        result['null_last_reflected_on']
    ])

    logger.info("=" * 80)
    if important_nulls == 0:
        logger.info("🎉 SUCCESS! ALL FIELDS ARE POPULATED! NO NULL!")
        success = True
    else:
        logger.error(f"❌ FAIL: Still found {important_nulls} NULL values")
        success = False
    logger.info("=" * 80)

    await db.disconnect()
    return success


if __name__ == '__main__':
    success = asyncio.run(backfill_emotions())
    exit(0 if success else 1)
