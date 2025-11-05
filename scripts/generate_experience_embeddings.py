"""
Generate embeddings for existing shared_experiences
Uses Angela's existing EmbeddingService (Ollama multilingual-e5-small, 384 dims)
"""

import asyncio
import asyncpg
from typing import List
import sys
import os

# Add project root to path
sys.path.insert(0, '/Users/davidsamanyaporn/PycharmProjects/AngelaAI')

from angela_core.services.embedding_service import EmbeddingService

async def generate_embeddings_for_experiences():
    """Generate embeddings for all shared experiences"""
    print("🧠 Generating embeddings for shared experiences using Ollama...\n")

    # Initialize embedding service
    embedding_service = EmbeddingService()
    print("✅ Initialized EmbeddingService (multilingual-e5-small, 384 dims)\n")

    # Connect to database
    conn = await asyncpg.connect(
        host='localhost',
        port=5432,
        user='davidsamanyaporn',
        database='AngelaMemory'
    )

    # Get all experiences without embeddings
    experiences = await conn.fetch("""
        SELECT
            experience_id,
            title,
            description,
            memorable_moments,
            what_angela_learned
        FROM shared_experiences
        WHERE embedding IS NULL
    """)

    print(f"📊 Found {len(experiences)} experiences without embeddings\n")

    updated_count = 0

    for exp in experiences:
        # Create combined text for embedding
        parts = [
            f"Title: {exp['title']}",
        ]

        if exp['description']:
            parts.append(f"Description: {exp['description']}")

        if exp['memorable_moments']:
            parts.append(f"Memorable: {exp['memorable_moments']}")

        if exp['what_angela_learned']:
            parts.append(f"Learned: {exp['what_angela_learned']}")

        combined_text = " | ".join(parts)

        print(f"📝 Processing: {exp['title'][:50]}...")

        # Generate embedding using Angela's EmbeddingService
        embedding = await embedding_service.generate_embedding(combined_text)

        # Convert embedding list to PostgreSQL vector format string
        embedding_str = '[' + ','.join(map(str, embedding)) + ']'

        # Update database
        await conn.execute("""
            UPDATE shared_experiences
            SET embedding = $1::vector
            WHERE experience_id = $2
        """, embedding_str, exp['experience_id'])

        updated_count += 1
        print(f"   ✅ Generated embedding (dimension: {len(embedding)})\n")

    await conn.close()

    print(f"🎉 Complete! Generated embeddings for {updated_count} experiences")

if __name__ == '__main__':
    asyncio.run(generate_embeddings_for_experiences())
