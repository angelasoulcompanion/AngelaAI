#!/usr/bin/env python3
"""
Test vector search for conversations
"""

import asyncio
import sys
sys.path.insert(0, '/Users/davidsamanyaporn/PycharmProjects/AngelaAI')

from angela_core.database import db
from angela_core.services.embedding_service import get_embedding_service


async def main():
    await db.connect()

    # Generate embedding for query
    query = "breakfast together"
    print(f"🔍 Searching for: '{query}'")
    print("=" * 60)

    embedding_service = get_embedding_service()
    query_embedding = await embedding_service.generate_embedding(query)

    print(f"✅ Generated embedding: {len(query_embedding)} dimensions")

    # Convert to PostgreSQL format
    embedding_str = f"[{','.join(map(str, query_embedding))}]"

    # Search with vector similarity
    sql = """
        SELECT
            conversation_id,
            speaker,
            LEFT(message_text, 100) as message,
            topic,
            importance_level,
            created_at,
            (embedding <=> $1::vector) as distance
        FROM conversations
        WHERE embedding IS NOT NULL
        ORDER BY embedding <=> $1::vector
        LIMIT 10
    """

    rows = await db.fetch(sql, embedding_str)

    print(f"\n📊 Found {len(rows)} results:\n")

    for i, row in enumerate(rows, 1):
        distance = float(row['distance'])
        similarity = round((1.0 - distance / 2.0) * 100, 1)

        print(f"{i}. [{row['speaker']}] {row['topic']}")
        print(f"   🎯 Similarity: {similarity}% (distance: {distance:.4f})")
        print(f"   💜 Importance: {row['importance_level']}/10")
        print(f"   📅 {row['created_at']}")
        print(f"   📝 {row['message']}...")
        print()

    await db.disconnect()


if __name__ == "__main__":
    asyncio.run(main())
