#!/usr/bin/env python3
"""
Update Missing Embeddings in Conversations Table

This script finds all conversations with NULL embeddings and generates them.
IMPORTANT: Must be run whenever there are NULL embeddings in the database!

Usage:
    python3 angela_core/scripts/update_missing_embeddings.py
    python3 angela_core/scripts/update_missing_embeddings.py --limit 100  # Process first 100
    python3 angela_core/scripts/update_missing_embeddings.py --dry-run    # See what would be updated
"""

import asyncio
import sys
from pathlib import Path
from typing import Optional
import argparse

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from angela_core.database import db
from angela_core.services.embedding_service import get_embedding_service
from datetime import datetime


async def count_null_embeddings() -> int:
    """Count how many conversations have NULL embeddings"""
    count = await db.fetchval("""
        SELECT COUNT(*) FROM conversations WHERE embedding IS NULL
    """)
    return count


async def get_conversations_without_embeddings(limit: Optional[int] = None) -> list:
    """Get conversations that don't have embeddings"""
    query = """
        SELECT conversation_id, speaker, message_text, created_at
        FROM conversations
        WHERE embedding IS NULL
        ORDER BY created_at DESC
    """

    if limit:
        query += f" LIMIT {limit}"

    rows = await db.fetch(query)
    return rows


async def update_conversation_embedding(
    conversation_id: str,
    message_text: str,
    embedding_service
) -> bool:
    """Update a single conversation with its embedding"""
    try:
        # Generate embedding
        embedding = await embedding_service.generate_embedding(message_text)
        emb_str = embedding_service.embedding_to_pgvector(embedding)

        # Update database
        await db.execute("""
            UPDATE conversations
            SET embedding = $1::vector
            WHERE conversation_id = $2
        """, emb_str, conversation_id)

        return True
    except Exception as e:
        print(f"   ❌ Error updating {conversation_id}: {e}")
        return False


async def main():
    parser = argparse.ArgumentParser(description="Update missing embeddings in conversations table")
    parser.add_argument("--limit", type=int, help="Process only first N conversations")
    parser.add_argument("--dry-run", action="store_true", help="Show what would be updated without actually updating")
    args = parser.parse_args()

    print("🔍 Checking for conversations with NULL embeddings...")

    # Count NULL embeddings
    null_count = await count_null_embeddings()
    print(f"   Found {null_count} conversations with NULL embeddings")

    if null_count == 0:
        print("✅ All conversations have embeddings! Nothing to do.")
        return

    if args.dry_run:
        print("\n📋 DRY RUN MODE - No changes will be made")

    # Get conversations without embeddings
    limit = args.limit if args.limit else null_count
    conversations = await get_conversations_without_embeddings(limit)

    print(f"\n🔄 Processing {len(conversations)} conversations...")

    if args.dry_run:
        print("\nWould update the following conversations:")
        for conv in conversations[:10]:  # Show first 10
            conv_id_str = str(conv['conversation_id'])
            print(f"   • {conv_id_str[:8]}... ({conv['speaker']}): {conv['message_text'][:60]}...")
        if len(conversations) > 10:
            print(f"   ... and {len(conversations) - 10} more")
        return

    # Initialize embedding service
    embedding_service = get_embedding_service()

    # Update embeddings
    success_count = 0
    fail_count = 0

    for i, conv in enumerate(conversations, 1):
        conv_id = conv['conversation_id']
        conv_id_str = str(conv_id)
        speaker = conv['speaker']
        message = conv['message_text']

        print(f"   [{i}/{len(conversations)}] Updating {conv_id_str[:8]}... ({speaker})")

        success = await update_conversation_embedding(
            conv_id,
            message,
            embedding_service
        )

        if success:
            success_count += 1
        else:
            fail_count += 1

        # Progress update every 10
        if i % 10 == 0:
            print(f"      Progress: {success_count} success, {fail_count} failed")

    # Final summary
    print(f"\n✅ Update Complete!")
    print(f"   ✅ Successfully updated: {success_count}")
    if fail_count > 0:
        print(f"   ❌ Failed: {fail_count}")

    # Verify
    remaining_null = await count_null_embeddings()
    print(f"\n📊 Remaining NULL embeddings: {remaining_null}")


if __name__ == "__main__":
    asyncio.run(main())
