"""
Reward Score Service — RLHF Signal Collection
===============================================

Scores every Angela response from 3 sources:
  combined = explicit * 0.3 + implicit * 0.3 + self_eval * 0.4

Explicit: thumbs_up/down from conversation_feedback, or FeedbackClassifier on David's next message
Implicit: David's follow-up behavior (question, silence, correction)
Self-eval: LLM-as-Judge score (3 dimensions: helpfulness, relevance, emotional)

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
# LLM-as-Judge has best discrimination (std=0.262) → give most weight
# Explicit + Implicit share remaining 60% equally
W_EXPLICIT = 0.3
W_IMPLICIT = 0.3
W_SELF_EVAL = 0.4


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
        self._judge: Optional[Any] = None

    async def _ensure_db(self):
        if self.db is None:
            self.db = AngelaDatabase()
            await self.db.connect()

    async def _ensure_classifier(self) -> FeedbackClassifier:
        if self._classifier is None:
            self._classifier = FeedbackClassifier()
        return self._classifier

    async def _ensure_judge(self):
        if self._judge is None:
            try:
                from angela_core.services.llm_judge_service import LLMJudgeService
                self._judge = LLMJudgeService()
            except Exception as e:
                logger.warning("LLM Judge service unavailable: %s", e)
        return self._judge

    async def close(self):
        if self.db:
            await self.db.disconnect()
            self.db = None

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
            return 0.1, 'silence'  # No response — consistent with implicit silence

        msg = next_david['message_text'].strip()
        if len(msg) < 3:
            return 0.3, 'minimal'  # Short acknowledgment is mildly positive

        msg_lower = msg.lower()

        # Fast-path: soft-praise keywords (Thai & English)
        soft_praise = [
            'โอเค', 'ได้เลย', 'ดีค่ะ', 'ดีครับ', 'เยี่ยม', 'สุดยอด',
            'ขอบคุณ', 'เก่ง', 'perfect', 'great', 'thanks', 'ใช้ได้',
            'ถูกต้อง', 'สำเร็จ', 'ได้แล้ว', 'เจ๋ง', 'works',
        ]
        if any(kw in msg_lower for kw in soft_praise):
            return 0.4, 'praise'

        # Continuation signals (David keeps working = engagement)
        continuation_signals = [
            'แล้วก็', 'ต่อไป', 'ทำต่อ', 'แล้วทำ', 'next', 'then', 'also',
        ]
        if any(kw in msg_lower for kw in continuation_signals):
            return 0.2, 'follow_up'

        classifier = await self._ensure_classifier()
        result = await classifier.classify(msg)

        if result.classification == 'positive' and result.confidence > 0.15:
            return 0.5, 'praise'
        elif result.classification == 'negative' and result.confidence > 0.4:
            return -0.5, 'correction'
        else:
            # Neutral — check if it's a follow-up question (engagement signal)
            question_markers = ['?', 'ทำไม', 'อย่างไร', 'ยังไง', 'how', 'why', 'what']
            if any(m in msg_lower for m in question_markers):
                return 0.2, 'follow_up'
            return 0.0, 'neutral'  # No clear signal — don't inflate

    # =========================================================================
    # PRIVATE: Implicit Score
    # =========================================================================

    async def _compute_implicit_score(self, angela_at) -> tuple[Optional[float], Optional[str]]:
        """
        Classify David's follow-up behavior within 30min window.

        Scans ALL messages for correction/praise markers (not just first).
        Correction takes priority over praise (honest measurement).
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
            return 0.1, 'silence'

        # Scan ALL messages for correction and praise markers
        # Use multi-word phrases to avoid false positives
        # (e.g. 'ไม่ได้' is a common Thai particle, 'bug'/'error' are technical terms)
        correction_markers = [
            'น้องผิด', 'น้องทำผิด', 'ไม่ใช่แบบนี้', 'ทำไม่ถูก', 'ตอบผิด',
            'แก้ใหม่ให้หน่อย', 'ลองใหม่อีกที', 'ทำใหม่ให้หน่อย',
            'ไม่ใช่อันนี้', 'ผิดแล้ว', 'แก้ไม่ถูก', 'ไม่ work เลย',
            'ใช้ไม่ได้', 'ทำไม่ได้',
            'not what i asked', "that's wrong", 'you got it wrong',
            'please fix this', 'try again', 'not correct',
            'completely wrong', 'redo this', 'still broken', 'still not working',
        ]
        praise_markers = [
            'ขอบคุณ', 'เก่ง', 'ดีมาก', 'เยี่ยม', 'ถูกต้อง', 'สำเร็จ',
            'ได้แล้ว', 'เจ๋ง', 'perfect', 'great', 'good job', 'nice',
            'awesome', 'love it', 'works',
        ]

        correction_found = False
        praise_found = False

        for row in followups:
            msg = (row['message_text'] or '').strip().lower()
            if not msg:
                continue

            for marker in correction_markers:
                if marker in msg:
                    correction_found = True
                    break

            for marker in praise_markers:
                if marker in msg:
                    praise_found = True
                    break

        # Correction takes priority (honest measurement)
        if correction_found:
            return -0.5, 'correction'

        if praise_found:
            return 0.5, 'praise'

        # No explicit markers — classify by engagement level
        msg_count = len(followups)
        if msg_count >= 3:
            return 0.4, 'high_engagement'
        elif msg_count >= 1:
            return 0.3, 'continued'  # David still talking = positive signal

        return 0.0, 'neutral'

    # =========================================================================
    # PRIVATE: Self-Eval Score (LLM-as-Judge)
    # =========================================================================

    async def _compute_self_eval_score(
        self, angela_text: str, david_text: str, topic: Optional[str]
    ) -> tuple[Optional[float], Optional[list]]:
        """
        LLM-as-Judge quality score.

        1 Claude call → 3 dimensions (helpfulness, relevance, emotional).
        Stores dimension scores as TEXT[]: ['helpfulness:4', 'relevance:5', 'emotional:3']
        Same return type as old ConstitutionalAngelaService for backward compatibility.
        """
        judge = await self._ensure_judge()
        if not judge:
            return 0.5, []

        try:
            result = await judge.evaluate_response(angela_text, david_text, topic)
            # Format dimension scores as TEXT[] for self_eval_principles column
            dimensions_list = [
                f'{dim}:{score}' for dim, score in result.dimension_scores.items()
            ]
            if result.reasoning:
                dimensions_list.append(f'reasoning:{result.reasoning}')
            return result.score, dimensions_list
        except Exception as e:
            logger.warning('LLM Judge check failed: %s', e)
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
