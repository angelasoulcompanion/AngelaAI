#!/usr/bin/env python3
"""
Conversation Hooks - Trigger self-learning after conversation save

This module provides hooks that are automatically called after conversations
are saved to the database, triggering the self-learning loop.
"""

import asyncio
import logging
import uuid
from typing import Optional

logger = logging.getLogger(__name__)


# Lazy import to avoid circular dependencies
_self_learning_loop = None


def get_self_learning_loop():
    """Lazy load self-learning loop to avoid circular imports"""
    global _self_learning_loop
    if _self_learning_loop is None:
        try:
            from angela_core.services.self_learning_service import self_learning_loop
            _self_learning_loop = self_learning_loop
            logger.info("🧠 Self-learning loop loaded successfully")
        except ImportError as e:
            logger.error(f"❌ Failed to import self-learning loop: {e}")
            _self_learning_loop = None
    return _self_learning_loop


async def trigger_self_learning(conversation_id: uuid.UUID, background: bool = True):
    """
    Trigger self-learning loop after conversation save

    Args:
        conversation_id: UUID of the saved conversation
        background: If True, run in background (non-blocking)

    Usage:
        # After saving conversation
        conversation_id = await db.fetchval("INSERT INTO conversations ...")
        await trigger_self_learning(conversation_id)  # Non-blocking
    """
    try:
        loop = get_self_learning_loop()
        if not loop:
            logger.warning("⚠️ Self-learning loop not available")
            return

        if background:
            # Run in background (non-blocking)
            asyncio.create_task(_run_self_learning(conversation_id))
            logger.debug(f"🔄 Self-learning triggered (background) for {conversation_id}")
        else:
            # Run immediately (blocking)
            await _run_self_learning(conversation_id)
            logger.debug(f"🔄 Self-learning completed for {conversation_id}")

    except Exception as e:
        logger.error(f"❌ Failed to trigger self-learning: {e}")


async def _run_self_learning(conversation_id: uuid.UUID):
    """Internal function to run self-learning loop"""
    try:
        loop = get_self_learning_loop()
        if not loop:
            return

        result = await loop.learn_from_conversation(conversation_id, trigger_source="auto")

        logger.info(
            f"✅ Self-learning complete: "
            f"{result.get('concepts_learned', 0)} concepts, "
            f"{result.get('preferences_saved', 0)} preferences, "
            f"{result.get('patterns_recorded', 0)} patterns"
        )

    except Exception as e:
        logger.error(f"❌ Self-learning failed for {conversation_id}: {e}")
        import traceback
        traceback.print_exc()


# Convenience function for manual trigger
async def trigger_self_learning_for_recent_conversations(limit: int = 10):
    """
    Manually trigger self-learning for recent conversations

    Useful for:
    - Testing self-learning system
    - Re-processing conversations after improvements
    - Catching up on missed conversations

    Args:
        limit: Number of recent conversations to process
    """
    try:
        from angela_core.database import db

        print(f"   🔄 Processing {limit} conversations...")

        conversations = await db.fetch(
            """
            SELECT conversation_id, created_at, speaker, LEFT(message_text, 40) as preview
            FROM conversations
            ORDER BY created_at DESC
            LIMIT $1
            """,
            limit
        )

        if not conversations:
            print(f"   ⚠️ No conversations found")
            return

        processed = 0
        total = len(conversations)

        for i, conv in enumerate(conversations, 1):
            try:
                # Progress bar
                progress = int((i / total) * 20)  # 20-char bar
                bar = "█" * progress + "░" * (20 - progress)
                percent = int((i / total) * 100)

                # Show progress
                preview = conv['preview'] or '(no text)'
                print(f"   [{bar}] {percent:3}% | {i}/{total} | {conv['speaker']}: {preview}...", end='\r')

                # Trigger self-learning
                await trigger_self_learning(conv['conversation_id'], background=False)
                processed += 1

            except Exception as e:
                print(f"\n   ✗ Failed on {i}/{total}: {e}")

        # Final progress (100%)
        bar = "█" * 20
        print(f"   [{bar}] 100% | {processed}/{total} conversations processed     ")

    except Exception as e:
        print(f"   ❌ Failed: {e}")
