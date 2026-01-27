#!/usr/bin/env python3
"""
Conversation Backfill Utility
Reconstruct conversation entries from existing session summaries.

Use this when /log-session captured too few conversation pairs
and we want to backfill from the narrative summaries stored in the database.

Usage:
    python3 -m angela_core.integrations.conversation_backfill --date 2026-01-25
    python3 -m angela_core.integrations.conversation_backfill --date 2026-01-26

Or import and call:
    from angela_core.integrations.conversation_backfill import backfill_from_summaries
    await backfill_from_summaries(date="2026-01-25")
"""

import asyncio
import argparse
import sys
import logging
from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional
from pathlib import Path

# Add parent path for direct execution
script_dir = Path(__file__).parent.parent
if str(script_dir) not in sys.path:
    sys.path.insert(0, str(script_dir))

from angela_core.database import db
from angela_core.integrations.claude_conversation_logger import log_conversations_bulk

logger = logging.getLogger(__name__)


async def get_session_summaries(date: str) -> List[Dict[str, Any]]:
    """
    Fetch session summaries for a given date from conversations table.

    Args:
        date: Date string YYYY-MM-DD

    Returns:
        List of summary rows
    """
    rows = await db.fetch("""
        SELECT conversation_id, session_id, message_text, message_type,
               topic, emotion_detected, importance_level, created_at
        FROM conversations
        WHERE session_id LIKE $1
          AND (message_type = 'reflection' OR topic = 'session_summary')
        ORDER BY created_at ASC
    """, f"claude_code_{date.replace('-', '')}")

    return [dict(r) for r in rows]


async def get_existing_conversation_count(date: str) -> int:
    """Count non-summary conversations for a date."""
    count = await db.fetchval("""
        SELECT COUNT(*)
        FROM conversations
        WHERE session_id = $1
          AND message_type != 'reflection'
          AND topic != 'session_summary'
          AND project_context != 'backfill_from_summary'
    """, f"claude_code_{date.replace('-', '')}")
    return count or 0


async def backfill_from_conversations_list(
    date: str,
    conversations: List[Dict[str, Any]],
    session_id: Optional[str] = None,
    dry_run: bool = False,
) -> Dict[str, Any]:
    """
    Backfill conversations from an explicit list.

    Each dict in conversations should have:
        - david_message (str)
        - angela_response (str)
        - topic (str, optional)
        - emotion (str, optional)
        - importance (int, optional)
        - created_at (str/datetime, optional)

    All entries are marked with:
        - message_type = "reconstructed"
        - project_context = "backfill_from_summary"

    Args:
        date: The date these conversations belong to (YYYY-MM-DD)
        conversations: List of conversation dicts
        session_id: Override session ID
        dry_run: If True, just count without inserting

    Returns:
        dict with backfill results
    """
    sid = session_id or f"claude_code_{date.replace('-', '')}"

    if dry_run:
        print(f"🔍 DRY RUN: Would backfill {len(conversations)} pairs for {date}")
        return {"would_insert": len(conversations), "dry_run": True}

    # Mark all as reconstructed
    for conv in conversations:
        conv["project_context"] = "backfill_from_summary"

    result = await log_conversations_bulk(
        conversations=conversations,
        embedding_mode="deferred",
        session_id=sid,
        project_context="backfill_from_summary",
        minimum_pairs=0,  # Disable minimum check for backfill operations
    )

    print(f"✅ Backfilled {result['inserted_count']} conversation pairs for {date}")
    return result


async def spread_timestamps(
    conversations: List[Dict[str, Any]],
    start_time: datetime,
    end_time: datetime,
) -> List[Dict[str, Any]]:
    """
    Spread conversation timestamps evenly across a time range.

    Args:
        conversations: List of conversation dicts (modified in-place)
        start_time: Session start time
        end_time: Session end time

    Returns:
        Same list with created_at fields set
    """
    if not conversations:
        return conversations

    total = len(conversations)
    duration = (end_time - start_time).total_seconds()
    interval = duration / max(total, 1)

    for i, conv in enumerate(conversations):
        conv["created_at"] = start_time + timedelta(seconds=interval * i)

    return conversations


# ========================================================================
# CLI
# ========================================================================

async def main():
    parser = argparse.ArgumentParser(description="Backfill conversations from summaries")
    parser.add_argument("--date", required=True, help="Date to backfill (YYYY-MM-DD)")
    parser.add_argument("--dry-run", action="store_true", help="Just show what would be done")
    parser.add_argument("--show-summaries", action="store_true", help="Show existing summaries for date")
    args = parser.parse_args()

    await db.connect()

    try:
        if args.show_summaries:
            summaries = await get_session_summaries(args.date)
            existing = await get_existing_conversation_count(args.date)
            print(f"\n📅 Date: {args.date}")
            print(f"📊 Existing conversations (non-summary): {existing}")
            print(f"📝 Session summaries found: {len(summaries)}")
            for s in summaries:
                text = s["message_text"][:200].replace("\n", " ")
                print(f"\n   [{s['created_at']}] {text}...")
        else:
            print(f"\n📅 Backfill for {args.date}")
            print("⚠️ This utility needs conversation data passed programmatically.")
            print("   Use backfill_from_conversations_list() from Python.")
            print("   Or use --show-summaries to see what's in the database.")
    finally:
        await db.disconnect()


if __name__ == "__main__":
    asyncio.run(main())
