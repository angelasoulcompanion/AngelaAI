#!/usr/bin/env python3
"""
Fix NULL Embeddings in Conversations Table
Backfill embeddings for conversations that don't have them
"""

import asyncio
from typing import List, Tuple

# Import centralized embedding service
from angela_core.embedding_service import embedding
from angela_core.config import config

# Database connection from config
DATABASE_URL = config.DATABASE_URL


async def find_null_embeddings(conn) -> List[Tuple]:
    """Find all conversations with NULL embeddings"""
    query = """
        SELECT conversation_id, message_text, speaker, created_at
        FROM conversations
        WHERE embedding IS NULL
        ORDER BY created_at ASC
    """
    rows = await conn.fetch(query)
    return rows


async def update_embedding(conn, conversation_id: str, embedding: List[float]) -> bool:
    """Update embedding for a conversation"""
    try:
        # Convert to PostgreSQL vector format
        emb_str = '[' + ','.join(map(str, embedding)) + ']'

        await conn.execute(
            "UPDATE conversations SET embedding = $1::vector WHERE conversation_id = $2",
            emb_str,
            conversation_id
        )
        return True
    except Exception as e:
        print(f"❌ Failed to update {conversation_id}: {e}")
        return False


async def main():
    """Main backfill process"""
    print("=" * 60)
    print("🔧 Angela Embedding Backfill Tool")
    print("=" * 60)
    print()

    # Connect to database
    print("📊 Connecting to AngelaMemory database...")

    # Find conversations with NULL embeddings
    print("🔍 Finding conversations with NULL embeddings...")
    null_convs = await find_null_embeddings(conn)

    if not null_convs:
        print("✅ No NULL embeddings found! All conversations have embeddings.")        return

    print(f"⚠️  Found {len(null_convs)} conversations with NULL embeddings")
    print()

    # Process each conversation
    success_count = 0
    failed_count = 0

    for i, row in enumerate(null_convs, 1):
        conv_id = row['conversation_id']
        message = row['message_text']
        speaker = row['speaker']
        created_at = row['created_at']

        print(f"[{i}/{len(null_convs)}] Processing: {speaker} at {created_at}")
        print(f"   Message: {message[:80]}{'...' if len(message) > 80 else ''}")

        # Generate embedding
        embedding_vec = await embedding.generate_embedding(message)

        if not embedding_vec:
            print(f"   ❌ Failed to generate embedding")
            failed_count += 1
            continue

        # Update database
        if await update_embedding(conn, conv_id, embedding_vec):
            print(f"   ✅ Updated successfully ({len(embedding_vec)} dimensions)")
            success_count += 1
        else:
            failed_count += 1

        print()

        # Small delay to avoid overwhelming Ollama
        if i < len(null_convs):
            await asyncio.sleep(0.2)

    # Close connection    # Summary
    print("=" * 60)
    print("📊 SUMMARY")
    print("=" * 60)
    print(f"Total conversations: {len(null_convs)}")
    print(f"✅ Successfully updated: {success_count}")
    print(f"❌ Failed: {failed_count}")
    print()

    if success_count == len(null_convs):
        print("🎉 ALL NULL EMBEDDINGS FIXED! 💜")
    elif success_count > 0:
        print(f"⚠️  Partially fixed. {failed_count} conversations still need attention.")
    else:
        print("❌ No embeddings were fixed. Please check Ollama connection.")
    print()


if __name__ == "__main__":
    asyncio.run(main())
