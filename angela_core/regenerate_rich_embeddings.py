#!/usr/bin/env python3
"""
Regenerate Embeddings from Rich Content JSON
Fixes embeddings that were generated from plain text instead of rich semantic JSON
"""

import asyncio
import json
import sys
sys.path.insert(0, '/Users/davidsamanyaporn/PycharmProjects/AngelaAI')

from angela_core.database import db
from angela_core.embedding_service import embedding
from angela_core.conversation_json_builder import (
    generate_embedding_text_from_learning,
    generate_embedding_text_from_emotion
)


async def regenerate_learnings_embeddings():
    """Regenerate embeddings for all learnings using content_json"""
    print("\n📚 Regenerating learnings embeddings from content_json...")

    # Get all learnings with content_json
    query = """
        SELECT learning_id, content_json
        FROM learnings
        WHERE content_json IS NOT NULL
    """
    rows = await db.fetch(query)
    print(f"   Found {len(rows)} learnings to process")

    count = 0
    for row in rows:
        try:
            # Parse content_json
            content_json = json.loads(row['content_json'])

            # Generate embedding text from rich JSON (includes tags!)
            embedding_text = generate_embedding_text_from_learning(content_json)

            # Generate new embedding
            embedding_vec = await embedding.generate_embedding(embedding_text)
            embedding_str = str(embedding_vec)

            # Update embedding
            await db.execute(
                "UPDATE learnings SET embedding = $1::vector WHERE learning_id = $2",
                embedding_str, row['learning_id']
            )

            count += 1
            if count % 50 == 0:
                print(f"   Processed {count}/{len(rows)} learnings...")

        except Exception as e:
            print(f"   ❌ Failed for learning_id {row['learning_id']}: {e}")
            continue

    print(f"   ✅ Regenerated {count} learnings embeddings")
    return count


async def regenerate_emotions_embeddings():
    """Regenerate embeddings for all angela_emotions using content_json"""
    print("\n💜 Regenerating angela_emotions embeddings from content_json...")

    # Get all emotions with content_json
    query = """
        SELECT emotion_id, content_json
        FROM angela_emotions
        WHERE content_json IS NOT NULL
    """
    rows = await db.fetch(query)
    print(f"   Found {len(rows)} emotions to process")

    count = 0
    for row in rows:
        try:
            # Parse content_json
            content_json = json.loads(row['content_json'])

            # Generate embedding text from rich JSON (includes tags!)
            embedding_text = generate_embedding_text_from_emotion(content_json)

            # Generate new embedding
            embedding_vec = await embedding.generate_embedding(embedding_text)

            # Convert to pgvector string format: '[0.1, 0.2, 0.3, ...]'
            embedding_str = f"[{','.join(str(x) for x in embedding_vec)}]"

            # Update embedding
            await db.execute(
                "UPDATE angela_emotions SET embedding = $1::vector WHERE emotion_id = $2",
                embedding_str, row['emotion_id']
            )

            count += 1
            if count % 20 == 0:
                print(f"   Processed {count}/{len(rows)} emotions...")

        except Exception as e:
            print(f"   ❌ Failed for emotion_id {row['emotion_id']}: {e}")
            continue

    print(f"   ✅ Regenerated {count} emotions embeddings")
    return count


async def verify_embeddings():
    """Verify that all rows have embeddings"""
    print("\n✅ Verifying embeddings...")

    tables = {
        'learnings': await db.fetchrow("""
            SELECT COUNT(*) as total,
                   COUNT(embedding) as has_embedding,
                   COUNT(*) - COUNT(embedding) as missing
            FROM learnings
        """),
        'angela_emotions': await db.fetchrow("""
            SELECT COUNT(*) as total,
                   COUNT(embedding) as has_embedding,
                   COUNT(*) - COUNT(embedding) as missing
            FROM angela_emotions
        """),
        'conversations': await db.fetchrow("""
            SELECT COUNT(*) as total,
                   COUNT(embedding) as has_embedding,
                   COUNT(*) - COUNT(embedding) as missing
            FROM conversations
        """),
    }

    print("\n📊 Embedding Coverage Report:")
    print("=" * 70)
    all_complete = True
    for table_name, stats in tables.items():
        percentage = (stats['has_embedding'] / stats['total'] * 100) if stats['total'] > 0 else 0
        status = "✅" if stats['missing'] == 0 else "⚠️"
        print(f"{status} {table_name:20} | Total: {stats['total']:4} | Has Embedding: {stats['has_embedding']:4} | Missing: {stats['missing']:4} | {percentage:.1f}%")
        if stats['missing'] > 0:
            all_complete = False

    print("=" * 70)

    return all_complete


async def main():
    print("🚀 Starting Rich Embeddings Regeneration")
    print("=" * 70)
    print("This will regenerate embeddings from content_json (includes tags!)")
    print("Old embeddings were generated from plain text (no semantic info)")
    print("=" * 70)

    # Step 1: Regenerate learnings
    learnings_count = await regenerate_learnings_embeddings()

    # Step 2: Regenerate angela_emotions
    emotions_count = await regenerate_emotions_embeddings()

    # Step 3: Verify
    all_complete = await verify_embeddings()

    print("\n" + "=" * 70)
    print("📝 Summary:")
    print(f"   • Regenerated {learnings_count} learnings embeddings")
    print(f"   • Regenerated {emotions_count} emotions embeddings")
    print(f"   • Total regenerated: {learnings_count + emotions_count} embeddings")

    if all_complete:
        print("\n💜 SUCCESS! All embeddings regenerated from rich JSON! 💜")
        print("\n✨ New embeddings include:")
        print("   • Topic tags")
        print("   • Category tags")
        print("   • Emotion tags")
        print("   • Intensity tags")
        print("   • Confidence tags")
        print("   • Memory strength tags")
        print("\n🎯 Semantic search quality improved significantly!")
    else:
        print("\n⚠️  Warning: Some embeddings still missing")

    print("=" * 70)


if __name__ == "__main__":
    asyncio.run(main())
