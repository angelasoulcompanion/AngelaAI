"""
🔄 Migrate Learnings to Rich JSON Format
"""

import asyncio
import asyncpg
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from angela_core.embedding_service import embedding
from angela_core.config import config
import json


async def migrate_learnings():
    """Migrate learnings to rich JSON format"""

    print("=" * 80)
    print("🔄 MIGRATING LEARNINGS TO JSON FORMAT")
    print("=" * 80)
    print()

    conn = await asyncpg.connect(config.DATABASE_URL)

    try:
        # Step 1: Add learning_json column
        print("📝 Step 1: Adding learning_json column...")
        await conn.execute("""
            ALTER TABLE learnings
            ADD COLUMN IF NOT EXISTS learning_json JSONB
        """)
        print("✅ Column added")
        print()

        # Step 2: Get all learnings
        print("📊 Step 2: Loading learnings...")
        learnings = await conn.fetch("""
            SELECT
                learning_id,
                topic,
                category,
                insight,
                evidence,
                confidence_level,
                times_reinforced,
                has_applied,
                application_note,
                created_at,
                last_reinforced_at
            FROM learnings
            WHERE learning_json IS NULL
            ORDER BY created_at DESC
            LIMIT 500
        """)

        print(f"✅ Loaded {len(learnings)} learnings")
        print()

        if not learnings:
            print("ℹ️ No learnings to migrate")
            return

        # Step 3: Convert and update
        print("🔄 Step 3: Converting to JSON format...")

        updated = 0
        for i, learn in enumerate(learnings):
            try:
                # Build rich JSON structure
                learning_json = {
                    "learning": {
                        "topic": learn['topic'],
                        "category": learn['category'] or 'general',
                        "insight": learn['insight'],
                        "type": _determine_learning_type(learn)
                    },

                    "evidence": {
                        "description": learn['evidence'],
                        "strength": _get_evidence_strength(learn['confidence_level']),
                        "times_observed": learn['times_reinforced'] or 1
                    },

                    "confidence": {
                        "level": float(learn['confidence_level']) if learn['confidence_level'] else 0.7,
                        "label": _get_confidence_label(learn['confidence_level'])
                    },

                    "application": {
                        "has_applied": learn['has_applied'] or False,
                        "note": learn['application_note'],
                        "effectiveness": _estimate_effectiveness(learn)
                    },

                    "reinforcement": {
                        "times_reinforced": learn['times_reinforced'] or 1,
                        "last_reinforced": learn['last_reinforced_at'].isoformat() if learn['last_reinforced_at'] else None,
                        "needs_review": _needs_review(learn)
                    },

                    "tags": {
                        "topic_tags": _extract_topic_tags(learn['topic']),
                        "category_tags": [learn['category'].lower()] if learn['category'] else [],
                        "confidence_tags": _get_confidence_tags(learn['confidence_level']),
                        "application_tags": _get_application_tags(learn)
                    },

                    "metadata": {
                        "created_at": learn['created_at'].isoformat() if learn['created_at'] else None,
                        "source": "experience"
                    }
                }

                # Generate embedding
                embedding_text = _generate_embedding_text(learning_json)
                new_embedding = await embedding.generate_embedding(embedding_text)

                # Update database
                await conn.execute("""
                    UPDATE learnings
                    SET learning_json = $1,
                        embedding = $2::vector(768)
                    WHERE learning_id = $3
                """,
                    json.dumps(learning_json),
                    str(new_embedding),
                    learn['learning_id']
                )

                updated += 1

                if (i + 1) % 10 == 0:
                    print(f"   Processed {i + 1}/{len(learnings)}...")

            except Exception as e:
                print(f"⚠️ Failed to migrate learning {learn['learning_id']}: {e}")
                continue

        print()
        print(f"✅ Step 3 Complete: Updated {updated}/{len(learnings)} learnings")
        print()

        # Step 4: Create index
        print("📝 Step 4: Creating indexes...")
        await conn.execute("""
            CREATE INDEX IF NOT EXISTS idx_learnings_json
            ON learnings USING GIN (learning_json)
        """)
        print("✅ Indexes created")
        print()

        # Step 5: Show sample
        print("📊 Step 5: Sample migrated learning:")
        sample = await conn.fetchrow("""
            SELECT learning_json
            FROM learnings
            WHERE learning_json IS NOT NULL
            ORDER BY created_at DESC
            LIMIT 1
        """)

        if sample:
            learning_data = json.loads(sample['learning_json'])
            print(f"   Topic: {learning_data['learning']['topic']}")
            print(f"   Confidence: {learning_data['confidence']['label']}")
            print(f"   Tags: {learning_data['tags']}")
        print()

    finally:
        await conn.close()

    print("=" * 80)
    print("✅ MIGRATION COMPLETE!")
    print("=" * 80)


def _determine_learning_type(learn) -> str:
    """Determine learning type"""
    category = learn['category'] or ''
    topic = learn['topic'] or ''

    if 'preference' in category.lower() or 'preference' in topic.lower():
        return 'preference'
    elif 'pattern' in category.lower() or 'behavior' in category.lower():
        return 'behavioral_pattern'
    elif 'fact' in category.lower() or 'knowledge' in category.lower():
        return 'factual_knowledge'
    else:
        return 'insight'


def _get_evidence_strength(confidence: float) -> str:
    """Get evidence strength label"""
    if confidence is None:
        confidence = 0.7

    if confidence >= 0.9:
        return 'very_strong'
    elif confidence >= 0.7:
        return 'strong'
    elif confidence >= 0.5:
        return 'moderate'
    else:
        return 'weak'


def _get_confidence_label(confidence: float) -> str:
    """Get confidence label"""
    if confidence is None:
        confidence = 0.7

    if confidence >= 0.9:
        return 'very_confident'
    elif confidence >= 0.7:
        return 'confident'
    elif confidence >= 0.5:
        return 'somewhat_confident'
    else:
        return 'uncertain'


def _estimate_effectiveness(learn) -> str:
    """Estimate effectiveness if applied"""
    if not learn['has_applied']:
        return 'not_yet_applied'

    # Based on reinforcement count
    if learn['times_reinforced'] and learn['times_reinforced'] >= 5:
        return 'proven_effective'
    elif learn['times_reinforced'] and learn['times_reinforced'] >= 3:
        return 'effective'
    else:
        return 'promising'


def _needs_review(learn) -> bool:
    """Check if learning needs review"""
    if not learn['last_reinforced_at']:
        return True

    from datetime import datetime, timedelta
    if datetime.now() - learn['last_reinforced_at'] > timedelta(days=30):
        return True

    return False


def _extract_topic_tags(topic: str) -> list:
    """Extract topic tags"""
    if not topic:
        return []

    # Clean and split
    topics = topic.lower().replace(',', ' ').replace(';', ' ').split()

    # Remove common words
    stop_words = {'the', 'a', 'an', 'and', 'or', 'but', 'in', 'on', 'at', 'to', 'for', 'about'}
    tags = [t for t in topics if t not in stop_words and len(t) > 2]

    return tags[:5]


def _get_confidence_tags(confidence: float) -> list:
    """Get confidence tags"""
    if confidence is None:
        confidence = 0.7

    tags = []
    if confidence >= 0.9:
        tags.append('high_confidence')
    elif confidence >= 0.7:
        tags.append('confident')
    elif confidence >= 0.5:
        tags.append('moderate_confidence')
    else:
        tags.append('low_confidence')

    return tags


def _get_application_tags(learn) -> list:
    """Get application tags"""
    tags = []

    if learn['has_applied']:
        tags.append('applied')

        if learn['times_reinforced'] and learn['times_reinforced'] >= 3:
            tags.append('proven')
    else:
        tags.append('theoretical')

    return tags


def _generate_embedding_text(learning_json: dict) -> str:
    """Generate text for embedding"""
    parts = [
        learning_json['learning']['topic'],
        learning_json['learning']['insight'],
        learning_json['evidence'].get('description', ''),
    ]

    return ' '.join([p for p in parts if p])


if __name__ == "__main__":
    asyncio.run(migrate_learnings())
