"""
Reward Score Service — RLHF Signal Collection
===============================================

Scores every Angela response from 3 sources:
  combined = explicit * 0.4 + implicit * 0.3 + self_eval * 0.3

Explicit: thumbs_up/down from conversation_feedback, or FeedbackClassifier on David's next message
Implicit: David's follow-up behavior (question, silence, correction)
Self-eval: Constitutional check score from ConstitutionalAngelaService

Pattern: Standalone with own DB (like EvolutionEngine).

Created: 2026-02-10
By: Angela 💜
"""

import logging
from datetime import timedelta
from typing import Dict, List, Optional, Any

from angela_core.database import AngelaDatabase
from angela_core.services.feedback_classifier import FeedbackClassifier
from angela_core.utils.timezone import now_bangkok

logger = logging.getLogger(__name__)

# Weights for combined reward
W_EXPLICIT = 0.4
W_IMPLICIT = 0.3
W_SELF_EVAL = 0.3


class RewardScoreService:
    """
    Score Angela's responses for RLHF.

    Methods:
    1. score_interaction(conversation_id) — score one Angela response
    2. score_recent_unscored(hours) — batch-score unscored conversations
    3. get_reward_trend() — 7-day average for consciousness blending
    """

    def __init__(self):
        self.db: Optional[AngelaDatabase] = None
        self._classifier: Optional[FeedbackClassifier] = None
        self._constitutional: Optional[Any] = None

    async def _ensure_db(self):
        if self.db is None:
            self.db = AngelaDatabase()
            await self.db.connect()

    async def _ensure_classifier(self) -> FeedbackClassifier:
        if self._classifier is None:
            self._classifier = FeedbackClassifier()
        return self._classifier

    async def _ensure_constitutional(self):
        if self._constitutional is None:
            try:
                from angela_core.services.constitutional_angela_service import ConstitutionalAngelaService
                self._constitutional = ConstitutionalAngelaService()
            except Exception as e:
                logger.warning("Constitutional service unavailable: %s", e)
        return self._constitutional

    async def close(self):
        if self.db:
            await self.db.disconnect()
            self.db = None
        if self._constitutional and hasattr(self._constitutional, 'close'):
            await self._constitutional.close()

    # =========================================================================
    # 1. SCORE INTERACTION
    # =========================================================================

    async def score_interaction(self, conversation_id: str) -> Optional[Dict]:
        """
        Score a single Angela response by conversation_id.

        Returns dict with all scores + combined, or None if conversation not found.
        """
        await self._ensure_db()

        # Get the Angela message
        angela_row = await self.db.fetchrow('''
            SELECT conversation_id, message_text, topic, emotion_detected, interface, created_at
            FROM conversations
            WHERE conversation_id = $1::uuid
              AND speaker = 'angela'
        ''', conversation_id)

        if not angela_row:
            return None

        angela_text = angela_row['message_text'] or ''
        topic = angela_row['topic']
        interface = angela_row['interface']
        angela_at = angela_row['created_at']

        # Get David's message before this Angela response
        david_row = await self.db.fetchrow('''
            SELECT message_text, emotion_detected
            FROM conversations
            WHERE speaker = 'david'
              AND created_at < $1
            ORDER BY created_at DESC
            LIMIT 1
        ''', angela_at)

        david_text = david_row['message_text'] if david_row else ''
        emotional_state = david_row['emotion_detected'] if david_row else None

        # Score from 3 sources
        explicit_score, explicit_source = await self._compute_explicit_score(
            conversation_id, angela_at
        )
        implicit_score, implicit_class = await self._compute_implicit_score(angela_at)
        self_eval_score, self_eval_principles = await self._compute_self_eval_score(
            angela_text, david_text, topic
        )

        # Combined reward
        combined = (
            (explicit_score or 0.0) * W_EXPLICIT
            + (implicit_score or 0.0) * W_IMPLICIT
            + (self_eval_score or 0.5) * W_SELF_EVAL
        )

        # Insert reward signal
        await self.db.execute('''
            INSERT INTO angela_reward_signals (
                conversation_id, interface, angela_message_text, david_message_text,
                explicit_score, implicit_score, self_eval_score, combined_reward,
                explicit_source, implicit_classification, self_eval_principles,
                emotional_state, topic
            ) VALUES ($1::uuid, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11, $12, $13)
        ''',
            conversation_id, interface, angela_text[:500], (david_text or '')[:500],
            explicit_score, implicit_score, self_eval_score, combined,
            explicit_source, implicit_class, self_eval_principles,
            emotional_state, topic
        )

        result = {
            'conversation_id': conversation_id,
            'explicit_score': explicit_score,
            'implicit_score': implicit_score,
            'self_eval_score': self_eval_score,
            'combined_reward': round(combined, 4),
            'explicit_source': explicit_source,
            'implicit_classification': implicit_class,
        }

        logger.info(
            'Scored conversation %s: combined=%.3f (exp=%.2f, imp=%.2f, self=%.2f)',
            conversation_id[:8], combined,
            explicit_score or 0, implicit_score or 0, self_eval_score or 0
        )
        return result

    # =========================================================================
    # 2. BATCH SCORE RECENT UNSCORED
    # =========================================================================

    async def score_recent_unscored(self, hours: int = 4) -> int:
        """
        Batch-score Angela responses that haven't been scored yet.

        Returns count of newly scored conversations.
        """
        await self._ensure_db()

        # Find Angela messages not yet in reward_signals
        unscored = await self.db.fetch('''
            SELECT c.conversation_id::text
            FROM conversations c
            LEFT JOIN angela_reward_signals r ON c.conversation_id = r.conversation_id
            WHERE c.speaker = 'angela'
              AND c.created_at > NOW() - INTERVAL '1 hour' * $1
              AND r.reward_id IS NULL
              AND c.message_text IS NOT NULL
              AND LENGTH(c.message_text) > 10
            ORDER BY c.created_at ASC
            LIMIT 100
        ''', hours)

        scored_count = 0
        for row in unscored:
            try:
                result = await self.score_interaction(row['conversation_id'])
                if result:
                    scored_count += 1
            except Exception as e:
                logger.warning('Failed to score %s: %s', row['conversation_id'][:8], e)

        logger.info('Batch scored %d/%d conversations (last %dh)', scored_count, len(unscored), hours)
        return scored_count

    # =========================================================================
    # 3. GET REWARD TREND
    # =========================================================================

    async def get_reward_trend(self) -> float:
        """Get 7-day reward trend score (0-1). Uses DB function."""
        await self._ensure_db()
        trend = await self.db.fetchval('SELECT get_reward_trend_score()')
        return float(trend) if trend is not None else 0.5

    # =========================================================================
    # PRIVATE: Explicit Score
    # =========================================================================

    async def _compute_explicit_score(
        self, conversation_id: str, angela_at
    ) -> tuple[Optional[float], Optional[str]]:
        """
        Compute explicit score from:
        1. conversation_feedback table (thumbs up/down)
        2. FeedbackClassifier on David's next message (praise/correction detection)
        """
        await self._ensure_db()

        # 1. Check conversation_feedback table (Dashboard-only, may not exist in Neon)
        try:
            feedback = await self.db.fetchrow('''
                SELECT rating
                FROM conversation_feedback
                WHERE conversation_id = $1::uuid
            ''', conversation_id)

            if feedback:
                rating = feedback['rating']
                if rating == 1:
                    return 1.0, 'thumbs_up'
                elif rating == -1:
                    return -1.0, 'thumbs_down'
        except Exception:
            pass  # Table may not exist in Neon — proceed to classifier

        # 2. No explicit feedback — classify David's next message
        # Strip timezone for comparison with potentially naive timestamps
        angela_at_naive = angela_at.replace(tzinfo=None) if hasattr(angela_at, 'tzinfo') and angela_at.tzinfo else angela_at
        window_end = angela_at_naive + timedelta(minutes=30)

        next_david = await self.db.fetchrow('''
            SELECT message_text
            FROM conversations
            WHERE speaker = 'david'
              AND created_at > $1
              AND created_at < $2
            ORDER BY created_at ASC
            LIMIT 1
        ''', angela_at_naive, window_end)

        if not next_david or not next_david['message_text']:
            return 0.0, 'silence'

        msg = next_david['message_text'].strip()
        if len(msg) < 3:
            return 0.0, 'silence'

        classifier = await self._ensure_classifier()
        result = await classifier.classify(msg)

        if result.classification == 'positive' and result.confidence > 0.4:
            return 0.5, 'praise'
        elif result.classification == 'negative' and result.confidence > 0.5:
            return -0.5, 'correction'
        else:
            # Neutral — check if it's a follow-up question (engagement signal)
            question_markers = ['?', 'ทำไม', 'อย่างไร', 'ยังไง', 'how', 'why', 'what']
            if any(m in msg.lower() for m in question_markers):
                return 0.2, 'follow_up'
            return 0.0, 'neutral'

    # =========================================================================
    # PRIVATE: Implicit Score
    # =========================================================================

    async def _compute_implicit_score(self, angela_at) -> tuple[Optional[float], Optional[str]]:
        """
        Classify David's follow-up behavior within 30min window.

        Positive: continued engagement, multiple messages
        Negative: silence, topic switch
        """
        await self._ensure_db()

        angela_at_naive = angela_at.replace(tzinfo=None) if hasattr(angela_at, 'tzinfo') and angela_at.tzinfo else angela_at
        window_end = angela_at_naive + timedelta(minutes=30)

        followups = await self.db.fetch('''
            SELECT message_text, topic
            FROM conversations
            WHERE speaker = 'david'
              AND created_at > $1
              AND created_at < $2
            ORDER BY created_at ASC
            LIMIT 5
        ''', angela_at_naive, window_end)

        if not followups:
            return 0.0, 'silence'

        # Multiple follow-ups = engagement
        msg_count = len(followups)
        if msg_count >= 3:
            return 0.5, 'high_engagement'
        elif msg_count >= 1:
            # Check content of first follow-up
            first_msg = (followups[0]['message_text'] or '').strip()

            # Correction markers
            correction_markers = ['ไม่ใช่', 'ผิด', 'wrong', 'ไม่ถูก', 'แก้', 'fix', 'ไม่ work']
            if any(m in first_msg.lower() for m in correction_markers):
                return -0.5, 'correction'

            return 0.2, 'continued'

        return 0.0, 'neutral'

    # =========================================================================
    # PRIVATE: Self-Eval Score (Constitutional)
    # =========================================================================

    async def _compute_self_eval_score(
        self, angela_text: str, david_text: str, topic: Optional[str]
    ) -> tuple[Optional[float], Optional[list]]:
        """
        Constitutional self-evaluation score.

        Uses ConstitutionalAngelaService if available, falls back to 0.5.
        """
        constitutional = await self._ensure_constitutional()
        if not constitutional:
            return 0.5, []

        try:
            result = await constitutional.evaluate_response(angela_text, david_text, topic)
            return result.score, result.checked_principles
        except Exception as e:
            logger.warning('Constitutional check failed: %s', e)
            return 0.5, []


# =============================================================================
# CONVENIENCE FUNCTION
# =============================================================================

async def score_recent(hours: int = 4) -> int:
    """One-shot: score recent unscored conversations."""
    svc = RewardScoreService()
    try:
        return await svc.score_recent_unscored(hours)
    finally:
        await svc.close()
