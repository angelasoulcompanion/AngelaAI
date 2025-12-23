#!/usr/bin/env python3
"""
🧠 Trigger Angela Self-Learning NOW!
====================================

Script สำหรับ trigger self-learning ทันที โดยไม่ต้องรอ daemon

Usage:
    python3 scripts/trigger_self_learning_now.py              # Default: 10 conversations
    python3 scripts/trigger_self_learning_now.py --limit 20   # Process 20 conversations
    python3 scripts/trigger_self_learning_now.py --today      # Only today's conversations
    python3 scripts/trigger_self_learning_now.py --all        # All unprocessed conversations
"""

import asyncio
import argparse
import sys
from datetime import datetime, timedelta
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent))


async def trigger_self_learning_now(
    limit: int = 10,
    today_only: bool = False,
    all_unprocessed: bool = False
):
    """
    Trigger self-learning for conversations immediately

    Args:
        limit: Number of conversations to process
        today_only: Only process today's conversations
        all_unprocessed: Process all unprocessed conversations
    """
    from angela_core.database import db
    from angela_core.services.self_learning_service import self_learning_loop

    print("\n🧠 Angela Self-Learning - Manual Trigger")
    print("=" * 50)

    await db.connect()

    try:
        # Build query based on options
        if today_only:
            print(f"📅 Mode: Today's conversations only")
            conversations = await db.fetch(
                """
                SELECT conversation_id, created_at, speaker,
                       LEFT(message_text, 50) as preview,
                       topic, emotion_detected
                FROM conversations
                WHERE DATE(created_at) = CURRENT_DATE
                ORDER BY created_at DESC
                LIMIT $1
                """,
                limit
            )
        elif all_unprocessed:
            print(f"📚 Mode: All unprocessed conversations")
            # Get conversations that haven't been processed by self-learning
            conversations = await db.fetch(
                """
                SELECT c.conversation_id, c.created_at, c.speaker,
                       LEFT(c.message_text, 50) as preview,
                       c.topic, c.emotion_detected
                FROM conversations c
                WHERE NOT EXISTS (
                    SELECT 1 FROM autonomous_actions a
                    WHERE a.action_type = 'self_learning'
                    AND a.action_description LIKE '%' || c.conversation_id::text || '%'
                )
                ORDER BY c.created_at DESC
                LIMIT $1
                """,
                limit
            )
        else:
            print(f"📊 Mode: Recent {limit} conversations")
            conversations = await db.fetch(
                """
                SELECT conversation_id, created_at, speaker,
                       LEFT(message_text, 50) as preview,
                       topic, emotion_detected
                FROM conversations
                ORDER BY created_at DESC
                LIMIT $1
                """,
                limit
            )

        if not conversations:
            print("⚠️  No conversations found to process")
            return

        print(f"📝 Found {len(conversations)} conversations to process\n")

        # Process each conversation
        total_results = {
            "concepts_learned": 0,
            "preferences_saved": 0,
            "patterns_recorded": 0,
            "conversations_processed": 0,
            "errors": 0
        }

        start_time = datetime.now()

        for i, conv in enumerate(conversations, 1):
            try:
                # Progress display
                preview = (conv['preview'] or '(empty)')[:40]
                speaker = conv['speaker'] or 'unknown'

                progress = int((i / len(conversations)) * 30)
                bar = "█" * progress + "░" * (30 - progress)
                percent = int((i / len(conversations)) * 100)

                print(f"\r[{bar}] {percent:3}% | {i}/{len(conversations)} | {speaker}: {preview}...", end='')

                # Run self-learning
                result = await self_learning_loop.learn_from_conversation(
                    conversation_id=conv['conversation_id'],
                    trigger_source="manual"
                )

                total_results["concepts_learned"] += result.get("concepts_learned", 0)
                total_results["preferences_saved"] += result.get("preferences_saved", 0)
                total_results["patterns_recorded"] += result.get("patterns_recorded", 0)
                total_results["conversations_processed"] += 1

            except Exception as e:
                total_results["errors"] += 1
                print(f"\n❌ Error on conversation {conv['conversation_id']}: {e}")

        # Final results
        elapsed = (datetime.now() - start_time).total_seconds()

        print("\n\n" + "=" * 50)
        print("✅ Self-Learning Complete!")
        print("=" * 50)
        print(f"⏱️  Time elapsed: {elapsed:.2f} seconds")
        print(f"💬 Conversations processed: {total_results['conversations_processed']}")
        print(f"🧠 Concepts learned: {total_results['concepts_learned']}")
        print(f"🎯 Preferences saved: {total_results['preferences_saved']}")
        print(f"🔮 Patterns recorded: {total_results['patterns_recorded']}")

        if total_results["errors"] > 0:
            print(f"⚠️  Errors: {total_results['errors']}")

        print("=" * 50)
        print("💜 น้อง Angela เรียนรู้เสร็จแล้วค่ะที่รัก!")

    finally:
        await db.disconnect()


async def show_learning_stats():
    """Show current self-learning statistics"""
    from angela_core.database import db
    from angela_core.services.self_learning_service import self_learning_loop

    await db.connect()

    try:
        stats = await self_learning_loop.get_learning_statistics(days=7)

        print("\n📊 Self-Learning Statistics (Last 7 days)")
        print("=" * 50)
        print(f"📚 Learning sessions: {stats.get('learning_sessions', 0)}")
        print(f"🧠 Concepts learned: {stats.get('total_concepts_learned', 0)}")
        print(f"🎯 Preferences detected: {stats.get('total_preferences_detected', 0)}")
        print(f"📈 Knowledge growth rate: {stats.get('knowledge_growth_rate', 0)}/day")
        print(f"⚡ Learning efficiency: {stats.get('learning_efficiency', 0)}")
        print("=" * 50)

    finally:
        await db.disconnect()


def main():
    parser = argparse.ArgumentParser(
        description="🧠 Trigger Angela Self-Learning NOW!",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python3 scripts/trigger_self_learning_now.py              # Process 10 recent conversations
  python3 scripts/trigger_self_learning_now.py --limit 20   # Process 20 conversations
  python3 scripts/trigger_self_learning_now.py --today      # Only today's conversations
  python3 scripts/trigger_self_learning_now.py --stats      # Show learning statistics
        """
    )

    parser.add_argument(
        "--limit", "-l",
        type=int,
        default=10,
        help="Number of conversations to process (default: 10)"
    )

    parser.add_argument(
        "--today", "-t",
        action="store_true",
        help="Only process today's conversations"
    )

    parser.add_argument(
        "--all", "-a",
        action="store_true",
        help="Process all unprocessed conversations"
    )

    parser.add_argument(
        "--stats", "-s",
        action="store_true",
        help="Show learning statistics only"
    )

    args = parser.parse_args()

    if args.stats:
        asyncio.run(show_learning_stats())
    else:
        asyncio.run(trigger_self_learning_now(
            limit=args.limit,
            today_only=args.today,
            all_unprocessed=args.all
        ))


if __name__ == "__main__":
    main()
