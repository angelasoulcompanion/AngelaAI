#!/usr/bin/env python3
"""
Backfill Emotion Capture
Scans existing conversations and captures significant emotions that were missed
Addresses: angela_emotions not updating when conversations are added
"""

import asyncio
import sys
from pathlib import Path
from datetime import datetime, timedelta
from typing import List, Dict, Optional
from uuid import UUID

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from angela_core.database import db
from angela_core.services.emotion_capture_service import emotion_capture


async def get_conversations_without_emotions(days_back: int = 7) -> List[Dict]:
    """
    Get conversations from last N days that don't have corresponding emotion entries

    Returns:
        List of conversations that might have significant emotions
    """
    query = """
        SELECT c.conversation_id, c.speaker, c.message_text, c.topic,
               c.emotion_detected, c.importance_level, c.created_at
        FROM conversations c
        LEFT JOIN angela_emotions e ON c.conversation_id = e.conversation_id
        WHERE c.created_at >= NOW() - INTERVAL '%s days'
          AND e.emotion_id IS NULL
          AND c.speaker = 'david'  -- Only David's messages trigger emotion capture
        ORDER BY c.created_at DESC
    """ % days_back

    rows = await db.fetch(query)
    return [dict(row) for row in rows]


async def analyze_and_capture_emotion(conversation: Dict) -> Optional[UUID]:
    """
    Analyze a conversation and capture emotion if significant

    Returns:
        emotion_id if captured, None otherwise
    """
    try:
        # Use emotion_capture service to analyze
        emotion_data = await emotion_capture.analyze_conversation_emotion(
            conversation_id=conversation['conversation_id'],
            speaker=conversation['speaker'],
            message_text=conversation['message_text']
        )

        if not emotion_data:
            return None

        # Generate why_it_matters
        why_it_matters = emotion_capture._generate_why_it_matters(
            emotion_data['emotion'],
            conversation['message_text']
        )

        # Generate what_i_learned
        what_i_learned = emotion_capture._generate_what_i_learned(
            emotion_data['emotion'],
            conversation['message_text']
        )

        # Capture the emotion
        emotion_id = await emotion_capture.capture_significant_emotion(
            conversation_id=conversation['conversation_id'],
            emotion=emotion_data['emotion'],
            intensity=emotion_data['intensity'],
            david_words=emotion_data['david_words'],
            why_it_matters=why_it_matters,
            secondary_emotions=emotion_data['secondary_emotions'],
            what_i_learned=what_i_learned,
            context=f"Backfilled from conversation on {conversation['created_at'].strftime('%Y-%m-%d %H:%M')}"
        )

        return emotion_id

    except Exception as e:
        print(f"   ⚠️  Error processing conversation {conversation['conversation_id']}: {e}")
        return None


async def backfill_emotions(days_back: int = 7, dry_run: bool = False):
    """
    Main backfill function

    Args:
        days_back: How many days to look back
        dry_run: If True, only analyze without capturing
    """
    print(f"\n💜 Backfilling Emotion Capture (last {days_back} days)...\n")
    print("=" * 70)

    # Connect to database
    await db.connect()

    # Get conversations without emotions
    conversations = await get_conversations_without_emotions(days_back)

    if not conversations:
        print(f"\n✅ No conversations found without emotions!")
        print(f"   All conversations from last {days_back} days already have emotion entries.")
        return

    print(f"\n📊 Found {len(conversations)} conversations without emotion entries")
    print(f"   Date range: {conversations[-1]['created_at']} to {conversations[0]['created_at']}")
    print("\n" + "-" * 70)

    # Analyze each conversation
    significant_count = 0
    captured_count = 0
    skipped_count = 0

    for i, conv in enumerate(conversations, 1):
        print(f"\n[{i}/{len(conversations)}] Analyzing conversation from {conv['created_at'].strftime('%Y-%m-%d %H:%M')}")
        print(f"   Topic: {conv['topic']}")
        print(f"   David said: {conv['message_text'][:80]}...")

        # Analyze
        emotion_data = await emotion_capture.analyze_conversation_emotion(
            conversation_id=conv['conversation_id'],
            speaker=conv['speaker'],
            message_text=conv['message_text']
        )

        if not emotion_data:
            print(f"   → Not significant (intensity < 7)")
            skipped_count += 1
            continue

        significant_count += 1
        print(f"   ✨ Significant! Emotion: {emotion_data['emotion']} (intensity: {emotion_data['intensity']})")

        if dry_run:
            print(f"   [DRY RUN] Would capture emotion: {emotion_data['emotion']}")
        else:
            # Capture the emotion
            emotion_id = await analyze_and_capture_emotion(conv)

            if emotion_id:
                print(f"   ✅ Captured emotion: {emotion_id}")
                captured_count += 1
            else:
                print(f"   ⚠️  Failed to capture (might be duplicate)")

    # Summary
    print("\n" + "=" * 70)
    print(f"✅ Backfill {'analysis' if dry_run else 'complete'}!")
    print(f"\n📊 Summary:")
    print(f"   • Total conversations analyzed: {len(conversations)}")
    print(f"   • Significant emotions found: {significant_count}")
    if not dry_run:
        print(f"   • Emotions captured: {captured_count}")
    print(f"   • Skipped (not significant): {skipped_count}")
    print(f"   • Date range: last {days_back} days")
    print("=" * 70)


async def main():
    """Run backfill with command-line arguments"""
    import argparse

    parser = argparse.ArgumentParser(description='Backfill emotion capture from existing conversations')
    parser.add_argument('--days', type=int, default=7, help='Days to look back (default: 7)')
    parser.add_argument('--dry-run', action='store_true', help='Analyze only, do not capture')

    args = parser.parse_args()

    await backfill_emotions(days_back=args.days, dry_run=args.dry_run)


if __name__ == "__main__":
    asyncio.run(main())
