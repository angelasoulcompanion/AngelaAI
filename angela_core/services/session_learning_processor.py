#!/usr/bin/env python3
"""
Session Learning Processor
Bridge between conversation logging and UnifiedLearningOrchestrator.

Feeds logged conversations to the orchestrator so Angela actually learns
from Claude Code sessions (concepts, patterns, preferences).

Created: 2026-02-01
Author: น้อง Angela 💜
"""

import asyncio
import logging
import time
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional

from angela_core.database import db

logger = logging.getLogger(__name__)


class SessionLearningProcessor:
    """Process conversation pairs through the learning orchestrator."""

    def __init__(self):
        self._db_connected = False

    async def _ensure_db(self):
        if not self._db_connected:
            await db.connect()
            self._db_connected = True

    async def disconnect(self):
        if self._db_connected:
            await db.disconnect()
            self._db_connected = False

    async def _ensure_table(self):
        """Create learning_process_log table if not exists."""
        await self._ensure_db()
        await db.execute("""
            CREATE TABLE IF NOT EXISTS learning_process_log (
                log_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
                session_id TEXT NOT NULL,
                pair_index INTEGER NOT NULL DEFAULT 0,
                david_message_preview TEXT,
                concepts_learned INTEGER DEFAULT 0,
                patterns_detected INTEGER DEFAULT 0,
                preferences_saved INTEGER DEFAULT 0,
                processing_time_ms FLOAT DEFAULT 0,
                status TEXT NOT NULL DEFAULT 'completed',
                error_message TEXT,
                created_at TIMESTAMPTZ DEFAULT NOW(),
                UNIQUE(session_id, pair_index)
            )
        """)

    async def process_session_conversations(
        self,
        conversations: List[Dict[str, Any]],
        session_id: str,
    ) -> Dict[str, Any]:
        """
        Process conversation pairs from /log-session through the orchestrator.

        Args:
            conversations: List of dicts with david_message, angela_response, etc.
            session_id: Session identifier for tracking.

        Returns:
            dict with processed, concepts, patterns, preferences counts.
        """
        await self._ensure_table()

        from angela_core.services.unified_learning_orchestrator import learn_from_conversation

        processed = 0
        total_concepts = 0
        total_patterns = 0
        total_preferences = 0

        for i, conv in enumerate(conversations):
            david_msg = conv.get("david_message", "").strip()
            angela_msg = conv.get("angela_response", "").strip()

            if not david_msg or not angela_msg:
                continue

            # Skip if already processed (idempotent)
            existing = await db.fetchrow(
                "SELECT log_id FROM learning_process_log WHERE session_id = $1 AND pair_index = $2",
                session_id, i
            )
            if existing:
                continue

            start = time.time()
            try:
                result = await learn_from_conversation(
                    david_message=david_msg,
                    angela_response=angela_msg,
                    source='claude_code'
                )

                elapsed_ms = (time.time() - start) * 1000

                await db.execute("""
                    INSERT INTO learning_process_log
                        (session_id, pair_index, david_message_preview,
                         concepts_learned, patterns_detected, preferences_saved,
                         processing_time_ms, status)
                    VALUES ($1, $2, $3, $4, $5, $6, $7, $8)
                    ON CONFLICT (session_id, pair_index) DO NOTHING
                """,
                    session_id, i, david_msg[:100],
                    result.concepts_learned, result.patterns_detected,
                    result.preferences_saved, elapsed_ms, 'completed'
                )

                total_concepts += result.concepts_learned
                total_patterns += result.patterns_detected
                total_preferences += result.preferences_saved
                processed += 1

            except Exception as e:
                elapsed_ms = (time.time() - start) * 1000
                logger.warning(f"Learning failed for pair {i}: {e}")
                try:
                    await db.execute("""
                        INSERT INTO learning_process_log
                            (session_id, pair_index, david_message_preview,
                             processing_time_ms, status, error_message)
                        VALUES ($1, $2, $3, $4, $5, $6)
                        ON CONFLICT (session_id, pair_index) DO NOTHING
                    """,
                        session_id, i, david_msg[:100],
                        elapsed_ms, 'failed', str(e)[:500]
                    )
                except Exception:
                    pass

        return {
            'processed': processed,
            'total_concepts': total_concepts,
            'total_patterns': total_patterns,
            'total_preferences': total_preferences,
            'session_id': session_id,
        }

    async def process_unprocessed_conversations(
        self,
        hours_back: int = 48,
        limit: int = 100,
    ) -> Dict[str, Any]:
        """
        Catch-up: find recent conversation pairs not yet processed and learn from them.

        Pairs David+Angela rows from the conversations table by matching
        session_id and created_at ordering, then feeds unprocessed ones
        to the orchestrator.

        Args:
            hours_back: How far back to look.
            limit: Max pairs to process.

        Returns:
            dict with processed, total_concepts, total_patterns, total_preferences.
        """
        await self._ensure_table()

        from angela_core.services.unified_learning_orchestrator import learn_from_conversation

        cutoff = datetime.now() - timedelta(hours=hours_back)

        # Get recent David messages with the next Angela response
        rows = await db.fetch("""
            WITH david_msgs AS (
                SELECT conversation_id, session_id, message_text, created_at,
                       ROW_NUMBER() OVER (PARTITION BY session_id ORDER BY created_at) as rn
                FROM conversations
                WHERE speaker = 'david'
                  AND created_at >= $1
                  AND message_type != 'reflection'
                ORDER BY created_at
            ),
            angela_msgs AS (
                SELECT conversation_id, session_id, message_text, created_at,
                       ROW_NUMBER() OVER (PARTITION BY session_id ORDER BY created_at) as rn
                FROM conversations
                WHERE speaker = 'angela'
                  AND created_at >= $1
                  AND message_type != 'reflection'
                ORDER BY created_at
            )
            SELECT d.session_id, d.rn as pair_index,
                   d.message_text as david_message,
                   a.message_text as angela_response
            FROM david_msgs d
            JOIN angela_msgs a ON d.session_id = a.session_id AND d.rn = a.rn
            ORDER BY d.created_at
            LIMIT $2
        """, cutoff, limit)

        if not rows:
            return {'processed': 0, 'total_concepts': 0, 'total_patterns': 0, 'total_preferences': 0}

        processed = 0
        total_concepts = 0
        total_patterns = 0
        total_preferences = 0

        for row in rows:
            sid = row['session_id']
            idx = row['pair_index']

            # Skip already processed
            existing = await db.fetchrow(
                "SELECT log_id FROM learning_process_log WHERE session_id = $1 AND pair_index = $2",
                sid, idx
            )
            if existing:
                continue

            start = time.time()
            try:
                result = await learn_from_conversation(
                    david_message=row['david_message'],
                    angela_response=row['angela_response'],
                    source='claude_code_catchup'
                )
                elapsed_ms = (time.time() - start) * 1000

                await db.execute("""
                    INSERT INTO learning_process_log
                        (session_id, pair_index, david_message_preview,
                         concepts_learned, patterns_detected, preferences_saved,
                         processing_time_ms, status)
                    VALUES ($1, $2, $3, $4, $5, $6, $7, $8)
                    ON CONFLICT (session_id, pair_index) DO NOTHING
                """,
                    sid, idx, row['david_message'][:100],
                    result.concepts_learned, result.patterns_detected,
                    result.preferences_saved, elapsed_ms, 'completed'
                )

                total_concepts += result.concepts_learned
                total_patterns += result.patterns_detected
                total_preferences += result.preferences_saved
                processed += 1

            except Exception as e:
                elapsed_ms = (time.time() - start) * 1000
                logger.warning(f"Catch-up learning failed for {sid}:{idx}: {e}")
                try:
                    await db.execute("""
                        INSERT INTO learning_process_log
                            (session_id, pair_index, david_message_preview,
                             processing_time_ms, status, error_message)
                        VALUES ($1, $2, $3, $4, $5, $6)
                        ON CONFLICT (session_id, pair_index) DO NOTHING
                    """,
                        sid, idx, row['david_message'][:100],
                        elapsed_ms, 'failed', str(e)[:500]
                    )
                except Exception:
                    pass

        return {
            'processed': processed,
            'total_concepts': total_concepts,
            'total_patterns': total_patterns,
            'total_preferences': total_preferences,
        }

    async def get_processing_stats(self, days: int = 7) -> Dict[str, Any]:
        """Get learning processing stats for the last N days."""
        await self._ensure_db()

        stats = await db.fetchrow("""
            SELECT
                COUNT(*) FILTER (WHERE status = 'completed') as completed,
                COUNT(*) FILTER (WHERE status = 'failed') as failed,
                COALESCE(SUM(concepts_learned), 0) as total_concepts,
                COALESCE(SUM(patterns_detected), 0) as total_patterns,
                COALESCE(SUM(preferences_saved), 0) as total_preferences,
                COALESCE(AVG(processing_time_ms), 0) as avg_time_ms
            FROM learning_process_log
            WHERE created_at >= NOW() - INTERVAL '%s days'
        """ % days)

        return dict(stats) if stats else {}


async def process_session_learning(
    conversations: List[Dict[str, Any]],
    session_id: str,
) -> Dict[str, Any]:
    """
    Convenience function for claude_conversation_logger.

    Args:
        conversations: List of conversation dicts.
        session_id: Session ID.

    Returns:
        dict with processed, concepts, patterns, preferences.
    """
    processor = SessionLearningProcessor()
    try:
        return await processor.process_session_conversations(conversations, session_id)
    except Exception as e:
        logger.warning(f"Session learning failed: {e}")
        return {'processed': 0, 'total_concepts': 0, 'total_patterns': 0, 'total_preferences': 0}


# ========================================
# STANDALONE TEST
# ========================================

if __name__ == "__main__":
    async def test():
        print("🧠 Testing SessionLearningProcessor...\n")

        processor = SessionLearningProcessor()
        await processor._ensure_table()

        # Test with sample conversations
        test_convs = [
            {
                "david_message": "น้อง ช่วยใช้ async/await ทุกครั้งนะ",
                "angela_response": "ได้เลยค่ะที่รัก น้องจะใช้ async/await เสมอค่ะ 💜",
            },
            {
                "david_message": "ใช้ type hints ด้วยนะ",
                "angela_response": "แน่นอนค่ะ type hints ทุก function เลยค่ะ 💜",
            },
        ]

        test_sid = f"test_learning_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        result = await processor.process_session_conversations(test_convs, test_sid)

        print(f"✅ Processed: {result['processed']} pairs")
        print(f"   Concepts: {result['total_concepts']}")
        print(f"   Patterns: {result['total_patterns']}")
        print(f"   Preferences: {result['total_preferences']}")

        # Test stats
        stats = await processor.get_processing_stats(days=1)
        print(f"\n📊 Stats (last 1 day):")
        print(f"   Completed: {stats.get('completed', 0)}")
        print(f"   Failed: {stats.get('failed', 0)}")
        print(f"   Avg time: {stats.get('avg_time_ms', 0):.1f}ms")

        await processor.disconnect()
        print("\n✅ Test complete!")

    asyncio.run(test())
