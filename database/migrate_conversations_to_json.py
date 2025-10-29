"""
🔄 Migrate Conversations to Rich JSON Format

Converts existing conversations table to use rich JSON format with tags.
"""

import asyncio
import asyncpg
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from angela_core.embedding_service import embedding
from angela_core.config import config
import json


async def migrate_conversations():
    """Migrate conversations to rich JSON format"""

    print("=" * 80)
    print("🔄 MIGRATING CONVERSATIONS TO JSON FORMAT")
    print("=" * 80)
    print()

    conn = await asyncpg.connect(config.DATABASE_URL)

    try:
        # Step 1: Add content_json column if it doesn't exist
        print("📝 Step 1: Adding content_json column...")
        await conn.execute("""
            ALTER TABLE conversations
            ADD COLUMN IF NOT EXISTS content_json JSONB
        """)
        print("✅ Column added")
        print()

        # Step 2: Get all conversations
        print("📊 Step 2: Loading conversations...")
        conversations = await conn.fetch("""
            SELECT
                conversation_id,
                speaker,
                message_text,
                topic,
                emotion_detected,
                sentiment_score,
                sentiment_label,
                message_type,
                project_context,
                importance_level,
                created_at
            FROM conversations
            WHERE content_json IS NULL
            ORDER BY created_at DESC
            LIMIT 1000
        """)

        print(f"✅ Loaded {len(conversations)} conversations")
        print()

        if not conversations:
            print("ℹ️ No conversations to migrate")
            return

        # Step 3: Convert and update
        print("🔄 Step 3: Converting to JSON format...")

        updated = 0
        for i, conv in enumerate(conversations):
            try:
                # Build rich JSON structure with tags
                content_json = {
                    "message": conv['message_text'],
                    "speaker": conv['speaker'],

                    # Rich tags structure
                    "tags": {
                        "emotion_tags": _extract_emotion_tags(conv['emotion_detected']),
                        "topic_tags": _extract_topic_tags(conv['topic']),
                        "sentiment_tags": _extract_sentiment_tags(conv['sentiment_score'], conv['sentiment_label']),
                        "context_tags": _extract_context_tags(conv['message_type'], conv['project_context']),
                        "importance_tags": _get_importance_tags(conv['importance_level'])
                    },

                    # Metadata
                    "metadata": {
                        "original_topic": conv['topic'],
                        "original_emotion": conv['emotion_detected'],
                        "sentiment_score": float(conv['sentiment_score']) if conv['sentiment_score'] else None,
                        "sentiment_label": conv['sentiment_label'],
                        "message_type": conv['message_type'],
                        "project_context": conv['project_context'],
                        "importance_level": conv['importance_level'],
                        "created_at": conv['created_at'].isoformat()
                    }
                }

                # Generate new embedding from rich content
                embedding_text = _generate_embedding_text(content_json)
                new_embedding = await embedding.generate_embedding(embedding_text)

                # Update database
                await conn.execute("""
                    UPDATE conversations
                    SET content_json = $1,
                        embedding = $2::vector(768)
                    WHERE conversation_id = $3
                """,
                    json.dumps(content_json),
                    str(new_embedding),
                    conv['conversation_id']
                )

                updated += 1

                if (i + 1) % 10 == 0:
                    print(f"   Processed {i + 1}/{len(conversations)}...")

            except Exception as e:
                print(f"⚠️ Failed to migrate conversation {conv['conversation_id']}: {e}")
                continue

        print()
        print(f"✅ Step 3 Complete: Updated {updated}/{len(conversations)} conversations")
        print()

        # Step 4: Create index on content_json
        print("📝 Step 4: Creating indexes...")
        await conn.execute("""
            CREATE INDEX IF NOT EXISTS idx_conversations_content_json
            ON conversations USING GIN (content_json)
        """)
        print("✅ Indexes created")
        print()

        # Step 5: Show sample
        print("📊 Step 5: Sample migrated conversation:")
        sample = await conn.fetchrow("""
            SELECT content_json
            FROM conversations
            WHERE content_json IS NOT NULL
            ORDER BY created_at DESC
            LIMIT 1
        """)

        if sample:
            content = json.loads(sample['content_json'])
            print(f"   Message: {content['message'][:100]}...")
            print(f"   Tags: {content['tags']}")
        print()

    finally:
        await conn.close()

    print("=" * 80)
    print("✅ MIGRATION COMPLETE!")
    print("=" * 80)


def _extract_emotion_tags(emotion_detected: str) -> list:
    """Extract emotion tags from emotion_detected field"""
    if not emotion_detected:
        return []

    # Split by common delimiters
    emotions = emotion_detected.lower().replace(',', ' ').replace(';', ' ').split()

    # Common emotion keywords
    emotion_map = {
        'happy': 'happy', 'joy': 'happy', 'excited': 'excited',
        'sad': 'sad', 'unhappy': 'sad',
        'angry': 'angry', 'frustrated': 'frustrated',
        'confused': 'confused', 'uncertain': 'confused',
        'grateful': 'grateful', 'thankful': 'grateful',
        'worried': 'worried', 'anxious': 'worried',
        'calm': 'calm', 'peaceful': 'calm',
        'curious': 'curious', 'interested': 'curious'
    }

    tags = []
    for word in emotions:
        if word in emotion_map:
            tag = emotion_map[word]
            if tag not in tags:
                tags.append(tag)

    return tags if tags else ['neutral']


def _extract_topic_tags(topic: str) -> list:
    """Extract topic tags"""
    if not topic:
        return []

    # Clean and split
    topics = topic.lower().replace(',', ' ').replace(';', ' ').split()

    # Remove common words
    stop_words = {'the', 'a', 'an', 'and', 'or', 'but', 'in', 'on', 'at', 'to', 'for'}
    tags = [t for t in topics if t not in stop_words and len(t) > 2]

    return tags[:5]  # Limit to 5 tags


def _extract_sentiment_tags(score: float, label: str) -> list:
    """Extract sentiment tags"""
    tags = []

    if score is not None:
        if score > 0.3:
            tags.append('positive')
        elif score < -0.3:
            tags.append('negative')
        else:
            tags.append('neutral')

    if label:
        label_lower = label.lower()
        if 'pos' in label_lower and 'positive' not in tags:
            tags.append('positive')
        elif 'neg' in label_lower and 'negative' not in tags:
            tags.append('negative')

    return tags if tags else ['neutral']


def _extract_context_tags(message_type: str, project_context: str) -> list:
    """Extract context tags"""
    tags = []

    if message_type:
        tags.append(message_type.lower())

    if project_context:
        tags.append(project_context.lower())

    return tags


def _get_importance_tags(importance_level: int) -> list:
    """Get importance tags based on level"""
    if importance_level >= 8:
        return ['critical', 'high_importance']
    elif importance_level >= 6:
        return ['significant', 'medium_importance']
    elif importance_level >= 4:
        return ['normal']
    else:
        return ['low_importance']


def _generate_embedding_text(content_json: dict) -> str:
    """Generate text for embedding from rich JSON"""
    parts = [
        content_json['message'],
        ' '.join(content_json['tags'].get('emotion_tags', [])),
        ' '.join(content_json['tags'].get('topic_tags', [])),
    ]

    return ' '.join(parts)


if __name__ == "__main__":
    asyncio.run(migrate_conversations())
