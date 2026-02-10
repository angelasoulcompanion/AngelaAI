"""
Preference Pairs Service — DPO Training Data Collection
=========================================================

Creates preference pairs (preferred vs rejected) from two sources:
1. David's corrections → rejected=Angela's original, preferred=David's correction
2. Reward score contrasts → same topic, high vs low reward responses

Pattern: Standalone with own DB (like EvolutionEngine).

Created: 2026-02-10
By: Angela 💜
"""

import logging
from datetime import timedelta
from typing import Dict, List, Optional

from angela_core.database import AngelaDatabase
from angela_core.services.feedback_classifier import FeedbackClassifier
from angela_core.utils.timezone import now_bangkok

logger = logging.getLogger(__name__)

# Correction detection markers (Thai + English)
CORRECTION_MARKERS = [
    'ไม่ใช่', 'ผิด', 'ไม่ถูก', 'แก้', 'wrong', 'not right', 'incorrect',
    'fix', 'ไม่ work', 'ใหม่', 'redo', 'ควรจะเป็น', 'should be', 'actually',
]


class PreferencePairsService:
    """
    Extract preference pairs for DPO-style learning.

    Methods:
    1. extract_correction_pairs(hours) — David corrections → pairs
    2. extract_reward_pairs(hours) — high vs low reward on same topic → pairs
    3. run_pair_extraction_cycle(hours) — main entry for daemon
    """

    def __init__(self):
        self.db: Optional[AngelaDatabase] = None
        self._classifier: Optional[FeedbackClassifier] = None

    async def _ensure_db(self):
        if self.db is None:
            self.db = AngelaDatabase()
            await self.db.connect()

    async def _ensure_classifier(self) -> FeedbackClassifier:
        if self._classifier is None:
            self._classifier = FeedbackClassifier()
        return self._classifier

    async def close(self):
        if self.db:
            await self.db.disconnect()
            self.db = None

    # =========================================================================
    # 1. CORRECTION PAIRS
    # =========================================================================

    async def extract_correction_pairs(self, hours: int = 4) -> int:
        """
        Find David→Angela→David triplets where David corrected Angela.

        Pattern:
          David asks → Angela responds (rejected) → David corrects (preferred)

        Returns count of pairs extracted.
        """
        await self._ensure_db()

        # Find Angela messages followed by David messages within timeframe
        triplets = await self.db.fetch('''
            WITH angela_msgs AS (
                SELECT
                    c.conversation_id,
                    c.message_text AS angela_text,
                    c.topic,
                    c.created_at AS angela_at,
                    LAG(c.message_text) OVER (ORDER BY c.created_at) AS david_before_text
                FROM conversations c
                WHERE c.speaker = 'angela'
                  AND c.created_at > NOW() - INTERVAL '1 hour' * $1
                  AND c.message_text IS NOT NULL
                  AND LENGTH(c.message_text) > 10
            )
            SELECT
                a.conversation_id::text,
                a.angela_text,
                a.david_before_text,
                a.topic,
                a.angela_at,
                d.message_text AS david_after_text
            FROM angela_msgs a
            JOIN conversations d ON d.speaker = 'david'
              AND d.created_at > a.angela_at
              AND d.created_at < a.angela_at + INTERVAL '10 minutes'
              AND d.message_text IS NOT NULL
              AND LENGTH(d.message_text) > 5
            WHERE a.david_before_text IS NOT NULL
            ORDER BY a.angela_at ASC
            LIMIT 50
        ''', hours)

        pairs_count = 0
        classifier = await self._ensure_classifier()

        for row in triplets:
            david_after = row['david_after_text'].strip()
            angela_text = row['angela_text'].strip()
            david_before = (row['david_before_text'] or '').strip()

            # Check if already extracted for this conversation
            existing = await self.db.fetchval('''
                SELECT COUNT(*) FROM angela_preference_pairs
                WHERE conversation_id = $1::uuid
                  AND preferred_source = 'david_correction'
            ''', row['conversation_id'])
            if existing > 0:
                continue

            # Classify David's follow-up
            result = await classifier.classify(david_after)

            # Must be negative classification + correction markers
            has_correction_marker = any(
                m in david_after.lower() for m in CORRECTION_MARKERS
            )

            if result.classification == 'negative' and has_correction_marker:
                # David corrected Angela → create preference pair
                # Preference strength based on classifier confidence
                strength = min(0.9, result.confidence)

                await self.db.execute('''
                    INSERT INTO angela_preference_pairs (
                        david_message, topic,
                        preferred_response, preferred_source,
                        rejected_response, rejected_source,
                        preference_strength, conversation_id
                    ) VALUES ($1, $2, $3, $4, $5, $6, $7, $8::uuid)
                ''',
                    david_before, row['topic'],
                    david_after, 'david_correction',
                    angela_text, 'angela_original',
                    strength, row['conversation_id']
                )
                pairs_count += 1

        logger.info('Extracted %d correction pairs (last %dh)', pairs_count, hours)
        return pairs_count

    # =========================================================================
    # 2. REWARD CONTRAST PAIRS
    # =========================================================================

    async def extract_reward_pairs(self, hours: int = 24) -> int:
        """
        Find pairs where Angela had high vs low reward on similar topics.

        Creates pairs: high_reward response (preferred) vs low_reward response (rejected)

        Returns count of pairs extracted.
        """
        await self._ensure_db()

        # Find topics with both high and low rewards
        topic_contrasts = await self.db.fetch('''
            WITH ranked AS (
                SELECT
                    conversation_id::text,
                    angela_message_text,
                    david_message_text,
                    topic,
                    combined_reward,
                    ROW_NUMBER() OVER (PARTITION BY topic ORDER BY combined_reward DESC) AS rank_high,
                    ROW_NUMBER() OVER (PARTITION BY topic ORDER BY combined_reward ASC) AS rank_low
                FROM angela_reward_signals
                WHERE scored_at > NOW() - INTERVAL '1 hour' * $1
                  AND topic IS NOT NULL
                  AND angela_message_text IS NOT NULL
            )
            SELECT topic,
                   MAX(CASE WHEN rank_high = 1 THEN angela_message_text END) AS best_response,
                   MAX(CASE WHEN rank_high = 1 THEN combined_reward END) AS best_reward,
                   MAX(CASE WHEN rank_high = 1 THEN conversation_id END) AS best_conv_id,
                   MAX(CASE WHEN rank_low = 1 THEN angela_message_text END) AS worst_response,
                   MAX(CASE WHEN rank_low = 1 THEN combined_reward END) AS worst_reward,
                   MAX(CASE WHEN rank_low = 1 THEN david_message_text END) AS david_msg
            FROM ranked
            WHERE rank_high = 1 OR rank_low = 1
            GROUP BY topic
            HAVING COUNT(DISTINCT conversation_id) >= 2
              AND MAX(CASE WHEN rank_high = 1 THEN combined_reward END)
                - MAX(CASE WHEN rank_low = 1 THEN combined_reward END) > 0.3
        ''', hours)

        pairs_count = 0
        for row in topic_contrasts:
            best = row['best_response']
            worst = row['worst_response']

            if not best or not worst or best == worst:
                continue

            # Check if already extracted for this topic recently
            existing = await self.db.fetchval('''
                SELECT COUNT(*) FROM angela_preference_pairs
                WHERE topic = $1
                  AND preferred_source = 'high_reward'
                  AND created_at > NOW() - INTERVAL '24 hours'
            ''', row['topic'])
            if existing > 0:
                continue

            reward_gap = (row['best_reward'] or 0) - (row['worst_reward'] or 0)
            strength = min(0.9, reward_gap)

            await self.db.execute('''
                INSERT INTO angela_preference_pairs (
                    david_message, topic,
                    preferred_response, preferred_source,
                    rejected_response, rejected_source,
                    preference_strength, conversation_id
                ) VALUES ($1, $2, $3, $4, $5, $6, $7, $8::uuid)
            ''',
                row['david_msg'] or '', row['topic'],
                best, 'high_reward',
                worst, 'low_reward',
                strength, row['best_conv_id']
            )
            pairs_count += 1

        logger.info('Extracted %d reward-contrast pairs (last %dh)', pairs_count, hours)
        return pairs_count

    # =========================================================================
    # 3. MAIN DAEMON ENTRY
    # =========================================================================

    async def run_pair_extraction_cycle(self, hours: int = 4) -> int:
        """
        Run full preference pair extraction cycle.

        Returns total pairs extracted.
        """
        await self._ensure_db()
        logger.info('Starting preference pair extraction cycle...')

        correction_pairs = await self.extract_correction_pairs(hours)
        reward_pairs = await self.extract_reward_pairs(hours=max(hours, 24))

        total = correction_pairs + reward_pairs
        logger.info(
            'Pair extraction complete: %d corrections + %d reward contrasts = %d total',
            correction_pairs, reward_pairs, total
        )
        return total

    # =========================================================================
    # REPORTING
    # =========================================================================

    async def get_pair_stats(self, days: int = 7) -> Dict:
        """Get statistics on preference pairs."""
        await self._ensure_db()

        total = await self.db.fetchval('''
            SELECT COUNT(*) FROM angela_preference_pairs
            WHERE created_at > NOW() - INTERVAL '1 day' * $1
        ''', days)

        by_source = await self.db.fetch('''
            SELECT preferred_source, COUNT(*) AS cnt
            FROM angela_preference_pairs
            WHERE created_at > NOW() - INTERVAL '1 day' * $1
            GROUP BY preferred_source
            ORDER BY cnt DESC
        ''', days)

        avg_strength = await self.db.fetchval('''
            SELECT AVG(preference_strength)
            FROM angela_preference_pairs
            WHERE created_at > NOW() - INTERVAL '1 day' * $1
        ''', days)

        return {
            'total_pairs': total,
            'by_source': {r['preferred_source']: r['cnt'] for r in by_source},
            'avg_preference_strength': round(float(avg_strength or 0), 3),
            'days': days,
        }


# =============================================================================
# CONVENIENCE FUNCTION
# =============================================================================

async def run_pair_extraction(hours: int = 4) -> int:
    """One-shot: run pair extraction cycle."""
    svc = PreferencePairsService()
    try:
        return await svc.run_pair_extraction_cycle(hours)
    finally:
        await svc.close()
