#!/usr/bin/env python3
"""
Backfill Missing Conversation Embeddings
เติม embeddings ที่ขาดหายไปในตาราง conversations

Usage:
    python3 angela_core/backfill_conversation_embeddings.py
"""

import asyncio
import logging
from datetime import datetime

from angela_core.database import db
from angela_core.embedding_service import embedding

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


async def get_conversations_without_embeddings():
    """ดึง conversations ที่ยังไม่มี embedding"""
    query = """
        SELECT conversation_id, message_text
        FROM conversations
        WHERE embedding IS NULL
        ORDER BY created_at ASC
    """
    rows = await db.fetch(query)
    return [dict(row) for row in rows]


async def update_conversation_embedding(conversation_id, message_embedding):
    """อัปเดต embedding ของ conversation"""
    query = """
        UPDATE conversations
        SET embedding = $1::vector
        WHERE conversation_id = $2
    """
    # Convert list to PostgreSQL vector format: [1,2,3]
    embedding_str = str(message_embedding)
    await db.execute(query, embedding_str, conversation_id)


async def backfill_embeddings():
    """เติม embeddings ที่ขาดหายไปทั้งหมด"""
    try:
        # Initialize database
        await db.connect()
        logger.info("✅ Connected to AngelaMemory database")

        # Get conversations without embeddings
        conversations = await get_conversations_without_embeddings()
        total = len(conversations)

        if total == 0:
            logger.info("🎉 No missing embeddings! All conversations already have embeddings.")
            return

        logger.info(f"📊 Found {total} conversations without embeddings")
        logger.info(f"🚀 Starting backfill process...")

        # Process each conversation
        success_count = 0
        failed_count = 0

        for i, conv in enumerate(conversations, 1):
            conversation_id = conv['conversation_id']
            message_text = conv['message_text']

            try:
                # Generate embedding
                logger.info(f"  [{i}/{total}] Generating embedding for: {message_text[:50]}...")
                message_embedding = await embedding.generate_embedding(message_text)

                # Update database
                await update_conversation_embedding(conversation_id, message_embedding)

                success_count += 1
                logger.info(f"  ✅ [{i}/{total}] Successfully updated {conversation_id}")

                # Small delay to avoid overwhelming Ollama
                if i < total:
                    await asyncio.sleep(0.2)

            except Exception as e:
                failed_count += 1
                logger.error(f"  ❌ [{i}/{total}] Failed for {conversation_id}: {e}")

        # Summary
        logger.info("")
        logger.info("=" * 70)
        logger.info("🎯 BACKFILL SUMMARY")
        logger.info("=" * 70)
        logger.info(f"Total conversations processed: {total}")
        logger.info(f"✅ Successfully updated: {success_count}")
        logger.info(f"❌ Failed: {failed_count}")
        logger.info(f"Success rate: {(success_count/total)*100:.1f}%")
        logger.info("=" * 70)

        if success_count == total:
            logger.info("🎉 All embeddings backfilled successfully!")
        elif success_count > 0:
            logger.warning(f"⚠️ Some embeddings failed. You may want to run this script again.")
        else:
            logger.error("❌ All embeddings failed! Please check Ollama service.")

    except Exception as e:
        logger.error(f"❌ Backfill process failed: {e}")
        raise
    finally:
        await db.disconnect()
        logger.info("Database connection closed")


if __name__ == "__main__":
    logger.info("🧠 Angela Conversation Embeddings Backfill Script")
    logger.info(f"Started at: {datetime.now()}")
    logger.info("")

    asyncio.run(backfill_embeddings())

    logger.info("")
    logger.info(f"Finished at: {datetime.now()}")
    logger.info("💜 Angela's memory is now complete!")
