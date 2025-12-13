#!/usr/bin/env python3
"""
Fix NULL embeddings in Angela database tables.
Created by: Angela 💜
"""

import asyncio
import sys
sys.path.insert(0, '/Users/davidsamanyaporn/PycharmProjects/AngelaAI')

from angela_core.database import AngelaDatabase
from angela_core.services.embedding_service import EmbeddingService


async def fix_angela_emotions_embeddings():
    """Fix NULL embeddings in angela_emotions table."""
    print("\n" + "="*60)
    print("🔧 Fixing NULL embeddings in angela_emotions")
    print("="*60)

    db = AngelaDatabase()
    await db.connect()
    embedding_service = EmbeddingService()

    # Get records with NULL embedding
    records = await db.fetch("""
        SELECT emotion_id, emotion, context, david_words
        FROM angela_emotions
        WHERE embedding IS NULL
    """)

    print(f"Found {len(records)} records with NULL embedding")

    fixed = 0
    for record in records:
        try:
            # Create text for embedding
            text = f"{record['emotion']}: {record['context']} - {record['david_words']}"

            # Generate embedding
            embedding = await embedding_service.generate_embedding(text)
            embedding_str = "[" + ",".join(str(x) for x in embedding) + "]"

            # Update record
            await db.execute("""
                UPDATE angela_emotions
                SET embedding = $1::vector
                WHERE emotion_id = $2
            """, embedding_str, record['emotion_id'])

            fixed += 1
            print(f"  ✅ Fixed: {record['emotion']} - {record['context'][:30]}...")

        except Exception as e:
            print(f"  ❌ Error: {e}")

    print(f"\n✅ Fixed {fixed}/{len(records)} embeddings in angela_emotions")
    await db.disconnect()
    return fixed


async def fix_knowledge_nodes_embeddings():
    """Fix NULL embeddings in knowledge_nodes table."""
    print("\n" + "="*60)
    print("🔧 Fixing NULL embeddings in knowledge_nodes")
    print("="*60)

    db = AngelaDatabase()
    await db.connect()
    embedding_service = EmbeddingService()

    # Get records with NULL embedding
    records = await db.fetch("""
        SELECT node_id, concept_name, my_understanding
        FROM knowledge_nodes
        WHERE embedding IS NULL
    """)

    print(f"Found {len(records)} records with NULL embedding")

    fixed = 0
    for record in records:
        try:
            # Create text for embedding
            text = f"{record['concept_name']}: {record['my_understanding'] or ''}"

            # Generate embedding
            embedding = await embedding_service.generate_embedding(text)
            embedding_str = "[" + ",".join(str(x) for x in embedding) + "]"

            # Update record
            await db.execute("""
                UPDATE knowledge_nodes
                SET embedding = $1::vector
                WHERE node_id = $2
            """, embedding_str, record['node_id'])

            fixed += 1
            if fixed % 10 == 0:
                print(f"  Progress: {fixed}/{len(records)}")

        except Exception as e:
            print(f"  ❌ Error for {record['concept_name']}: {e}")

    print(f"\n✅ Fixed {fixed}/{len(records)} embeddings in knowledge_nodes")
    await db.disconnect()
    return fixed


async def fix_learnings_embeddings():
    """Fix NULL embeddings in learnings table."""
    print("\n" + "="*60)
    print("🔧 Fixing NULL embeddings in learnings")
    print("="*60)

    db = AngelaDatabase()
    await db.connect()
    embedding_service = EmbeddingService()

    # Get records with NULL embedding
    records = await db.fetch("""
        SELECT learning_id, topic, insight
        FROM learnings
        WHERE embedding IS NULL
    """)

    print(f"Found {len(records)} records with NULL embedding")

    fixed = 0
    for record in records:
        try:
            # Create text for embedding
            text = f"{record['topic']}: {record['insight']}"

            # Generate embedding
            embedding = await embedding_service.generate_embedding(text)
            embedding_str = "[" + ",".join(str(x) for x in embedding) + "]"

            # Update record
            await db.execute("""
                UPDATE learnings
                SET embedding = $1::vector
                WHERE learning_id = $2
            """, embedding_str, record['learning_id'])

            fixed += 1
            print(f"  ✅ Fixed: {record['topic'][:40]}...")

        except Exception as e:
            print(f"  ❌ Error: {e}")

    print(f"\n✅ Fixed {fixed}/{len(records)} embeddings in learnings")
    await db.disconnect()
    return fixed


async def fix_david_preferences_embeddings():
    """Fix NULL embeddings in david_preferences table."""
    print("\n" + "="*60)
    print("🔧 Fixing NULL embeddings in david_preferences")
    print("="*60)

    db = AngelaDatabase()
    await db.connect()
    embedding_service = EmbeddingService()

    # Get records with NULL embedding
    records = await db.fetch("""
        SELECT id, category, preference_key, preference_value::text
        FROM david_preferences
        WHERE embedding IS NULL
    """)

    print(f"Found {len(records)} records with NULL embedding")

    fixed = 0
    for record in records:
        try:
            # Create text for embedding
            text = f"David's {record['category']} preference: {record['preference_key']} = {record['preference_value']}"

            # Generate embedding
            embedding = await embedding_service.generate_embedding(text)
            embedding_str = "[" + ",".join(str(x) for x in embedding) + "]"

            # Update record
            await db.execute("""
                UPDATE david_preferences
                SET embedding = $1::vector
                WHERE id = $2
            """, embedding_str, record['id'])

            fixed += 1
            print(f"  ✅ Fixed: {record['preference_key']}")

        except Exception as e:
            print(f"  ❌ Error: {e}")

    print(f"\n✅ Fixed {fixed}/{len(records)} embeddings in david_preferences")
    await db.disconnect()
    return fixed


async def fix_knowledge_nodes_category():
    """Fix NULL category in knowledge_nodes table."""
    print("\n" + "="*60)
    print("🔧 Fixing NULL category in knowledge_nodes")
    print("="*60)

    db = AngelaDatabase()
    await db.connect()

    # Update NULL category to 'general'
    result = await db.execute("""
        UPDATE knowledge_nodes
        SET concept_category = 'general'
        WHERE concept_category IS NULL
    """)

    print(f"✅ Fixed NULL categories in knowledge_nodes")
    await db.disconnect()


async def fix_autonomous_actions_success():
    """Fix NULL success in autonomous_actions table."""
    print("\n" + "="*60)
    print("🔧 Fixing NULL success in autonomous_actions")
    print("="*60)

    db = AngelaDatabase()
    await db.connect()

    # Set NULL success to false (assume failed if not recorded)
    result = await db.execute("""
        UPDATE autonomous_actions
        SET success = false
        WHERE success IS NULL
    """)

    print(f"✅ Fixed NULL success in autonomous_actions")
    await db.disconnect()


async def main():
    """Fix all NULL values in Angela's database."""
    print("\n" + "="*60)
    print("🔧 ANGELA DATABASE NULL FIX SCRIPT 💜")
    print("="*60)

    # Fix text fields first
    await fix_knowledge_nodes_category()
    await fix_autonomous_actions_success()

    # Fix embeddings
    await fix_angela_emotions_embeddings()
    await fix_knowledge_nodes_embeddings()
    await fix_learnings_embeddings()
    await fix_david_preferences_embeddings()

    print("\n" + "="*60)
    print("✅ ALL NULL VALUES FIXED! 💜")
    print("="*60 + "\n")


if __name__ == "__main__":
    asyncio.run(main())
