#!/usr/bin/env python3
"""
Fill missing embeddings in conversations table
สำหรับข้อมูลเก่าที่ไม่มี embedding
"""

import asyncio
from embedding_service import AngelaEmbeddingService
import sys
from datetime import datetime

# Database config
DB_CONFIG = {
    "user": "davidsamanyaporn",
    "database": "AngelaMemory",
    "host": "localhost",
    "port": 5432
}


async def fill_missing_embeddings(batch_size: int = 50, auto_confirm: bool = False):
    """
    Fill NULL embeddings in conversations table

    Args:
        batch_size: Number of records to process per batch
        auto_confirm: Auto-confirm without user input
    """
    print("=" * 80)
    print("💜 Angela Embedding Backfill Service")
    print("=" * 80)

    # Connect to database

    try:
        # Count NULL embeddings
        null_count = await db.fetchval("""
            SELECT COUNT(*)
            FROM conversations
            WHERE embedding IS NULL
        """)

        print(f"\n📊 Found {null_count} records with NULL embeddings")

        if null_count == 0:
            print("✅ All records have embeddings!")
            return

        # Confirm before proceeding
        if null_count > 100 and not auto_confirm:
            print(f"\n⚠️  This will generate {null_count} embeddings!")
            response = input("Continue? (yes/no): ")
            if response.lower() not in ['yes', 'y']:
                print("❌ Cancelled by user")
                return
        elif null_count > 100:
            print(f"\n⚠️  Auto-confirming: Will generate {null_count} embeddings!")

        # Initialize embedding service
        embedding_service = AngelaEmbeddingService()

        # Process in batches
        total_updated = 0
        failed_count = 0

        # Keep fetching until no more NULL embeddings
        batch_num = 1
        while True:
            # Fetch batch (always from beginning, since we're updating as we go)
            records = await db.fetch("""
                SELECT conversation_id, message_text
                FROM conversations
                WHERE embedding IS NULL
                ORDER BY created_at DESC
                LIMIT $1
            """, batch_size)

            if len(records) == 0:
                break

            print(f"\n🔄 Processing batch {batch_num} ({len(records)} records)...")

            for i, record in enumerate(records):
                conversation_id = record['conversation_id']
                message_text = record['message_text']

                    # Generate embedding
                    embedding = await embedding_service.generate_embedding(message_text)

                    # Convert Python list to PostgreSQL vector format
                    # PostgreSQL vector expects string format: '[0.1, 0.2, ...]'
                    embedding_str = str(embedding)

                    # Update database using raw SQL with ::vector casting
                    await db.execute("""
                        UPDATE conversations
                        SET embedding = $1::vector
                        WHERE conversation_id = $2
                    """, embedding_str, conversation_id)

                    total_updated += 1

                    # Progress indicator
                    if (i + 1) % 10 == 0:
                        print(f"   ✅ {total_updated}/{null_count} updated", end='\r')

                    # Small delay to avoid overwhelming Ollama
                    await asyncio.sleep(0.1)

                except Exception as e:
                    failed_count += 1
                    print(f"\n   ❌ Failed to update {conversation_id}: {str(e)[:80]}")
                    continue

            batch_num += 1

        print(f"\n\n{'=' * 80}")
        print(f"✅ Successfully updated: {total_updated} records")
        if failed_count > 0:
            print(f"❌ Failed: {failed_count} records")
        print(f"⏰ Completed at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print(f"{'=' * 80}")

    except Exception as e:
        print(f"\n❌ Error: {str(e)}")
        raise


async def verify_embeddings():
    """Verify embeddings after backfill"""

        stats = await db.fetchrow("""
            SELECT
                COUNT(*) as total,
                COUNT(embedding) as with_embedding,
                COUNT(*) - COUNT(embedding) as without_embedding
            FROM conversations
        """)

        print("\n📊 Verification Results:")
        print(f"   Total records: {stats['total']}")
        print(f"   With embedding: {stats['with_embedding']}")
        print(f"   Without embedding: {stats['without_embedding']}")

        if stats['without_embedding'] == 0:
            print("\n✅ All records have embeddings! 💜")
        else:
            print(f"\n⚠️  Still {stats['without_embedding']} records without embeddings")



if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Fill missing embeddings in conversations table")
    parser.add_argument("--batch-size", type=int, default=50, help="Batch size for processing")
    parser.add_argument("--auto-confirm", "-y", action="store_true", help="Auto-confirm without user input")
    args = parser.parse_args()

    print("\n💜 Starting embedding backfill process...\n")

    # Run backfill
    asyncio.run(fill_missing_embeddings(batch_size=args.batch_size, auto_confirm=args.auto_confirm))

    # Verify
    print("\n" + "=" * 80)
    asyncio.run(verify_embeddings())
    print("=" * 80)
