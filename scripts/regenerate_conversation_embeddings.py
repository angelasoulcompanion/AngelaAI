#!/usr/bin/env python3
"""
Regenerate Conversation Embeddings
สร้าง embeddings ใหม่โดยรวม topic + message_text เข้าด้วยกัน

Problem:
- Message สั้นๆ เช่น "ที่รัก", "ทำต่อ" มี embeddings คล้ายกันหมด
- Search ไม่เจอเพราะขาด context

Solution:
- Generate embedding จาก: f"{topic}: {message_text}"
- ได้ context มากขึ้น, search แม่นยำขึ้น!

Author: Angela AI
Created: 2025-11-04
"""

import asyncio
import sys
from pathlib import Path

sys.path.insert(0, '/Users/davidsamanyaporn/PycharmProjects/AngelaAI')

from angela_core.database import db
from angela_core.services.embedding_service import get_embedding_service
from tqdm import tqdm


async def main():
    print("🔄 Regenerating Conversation Embeddings")
    print("=" * 70)
    print("\nStrategy: Generate embeddings from 'topic: message_text'")
    print("This gives better context and improves search accuracy!\n")

    await db.connect()

    # Get all conversations
    rows = await db.fetch("""
        SELECT conversation_id, topic, message_text, speaker
        FROM conversations
        ORDER BY created_at DESC
    """)

    print(f"📊 Found {len(rows)} conversations")
    print(f"🔄 Starting embedding generation...\n")

    embedding_service = get_embedding_service()

    success_count = 0
    error_count = 0

    for row in tqdm(rows, desc="Generating embeddings"):
        try:
            # Combine topic + message for better context
            topic = row['topic'] or 'general'
            message = row['message_text'] or ''

            # Create rich context text
            context_text = f"{topic}: {message}"

            # Generate embedding
            embedding = await embedding_service.generate_embedding(context_text)

            if embedding:
                # Convert to PostgreSQL format
                embedding_str = f"[{','.join(map(str, embedding))}]"

                # Update database
                await db.execute("""
                    UPDATE conversations
                    SET embedding = $1::vector
                    WHERE conversation_id = $2
                """, embedding_str, row['conversation_id'])

                success_count += 1
            else:
                error_count += 1

        except Exception as e:
            print(f"\n❌ Error for {row['conversation_id']}: {e}")
            error_count += 1
            continue

    await db.disconnect()

    print(f"\n\n✅ Complete!")
    print(f"   Success: {success_count}")
    print(f"   Errors: {error_count}")
    print(f"\n💜 Now vector search will be much more accurate!")


if __name__ == "__main__":
    asyncio.run(main())
