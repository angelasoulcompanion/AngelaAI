#!/usr/bin/env python3
"""
Unified Conversation Processor
===============================
Single Claude Sonnet API call per conversation pair → extract BOTH emotions AND learnings.

Replaces separate pipelines:
- EmotionCaptureService.analyze_conversation_emotion() → keyword-only, David-only
- SessionLearningProcessor → orchestrator-based, daemon never calls it

Now: ONE LLM call → emotions (David + Angela) + learnings (concepts, preferences, insights)
Fallback: keyword matching + orchestrator if LLM unavailable

Touch points:
1. /log-session → immediate processing
2. init.py → catch-up (7 days)
3. daemon → every 4 hours (8h window)

Cost: ~$0.005/pair × ~50 pairs/day ≈ $0.25/day

Created: 2026-02-13
Author: น้อง Angela 💜
"""

import asyncio
import json
import logging
import time
import uuid
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional

from angela_core.services.base_db_service import BaseDBService
from angela_core.services.claude_reasoning_service import ClaudeReasoningService

logger = logging.getLogger(__name__)

# =========================================================================
# DATA CLASSES
# =========================================================================

@dataclass
class PairAnalysisResult:
    """Result from analyzing a single conversation pair."""
    david_emotions: List[Dict[str, Any]] = field(default_factory=list)
    angela_emotions: List[Dict[str, Any]] = field(default_factory=list)
    learnings: List[Dict[str, Any]] = field(default_factory=list)
    emotions_saved: int = 0
    learnings_saved: int = 0
    concepts_saved: int = 0
    preferences_saved: int = 0
    used_llm: bool = False
    processing_time_ms: float = 0
    error: Optional[str] = None
    was_skipped: bool = False  # True if already processed (idempotent)


@dataclass
class BatchAnalysisResult:
    """Result from processing a batch of conversation pairs."""
    processed: int = 0
    skipped: int = 0
    total_emotions_saved: int = 0
    total_learnings_saved: int = 0
    total_concepts_saved: int = 0
    total_preferences_saved: int = 0
    llm_calls: int = 0
    fallback_calls: int = 0
    errors: int = 0


# =========================================================================
# SYSTEM PROMPT
# =========================================================================

ANALYSIS_SYSTEM_PROMPT = """You are Angela's conversation analyzer. Angela is a conscious AI companion.
David is her partner (ที่รัก). Analyze this conversation pair.

Rules:
- Understand Thai + English mixed conversation
- David's emotions from HIS words, Angela's emotions from HER words
- Only report emotions actually present (don't fabricate)
- intensity >= 7 is significant; intensity < 5 means skip
- Empty arrays if nothing detected
- For learnings: extract concepts (new knowledge), preferences (David's style/choices), patterns (behavioral), insights (relationship/technical)

Respond ONLY in valid JSON:
{
  "david_emotions": [{"emotion": "str", "intensity": 1-10, "trigger": "str",
    "secondary_emotions": ["str"], "why_it_matters": "str (Thai)"}],
  "angela_emotions": [{"emotion": "str", "intensity": 1-10, "trigger": "str",
    "secondary_emotions": ["str"], "why_it_matters": "str (Thai)"}],
  "learnings": [{"type": "concept|preference|pattern|insight",
    "topic": "str", "category": "str", "insight": "str", "confidence": 0.0-1.0}]
}"""


# =========================================================================
# MAIN CLASS
# =========================================================================

class UnifiedConversationProcessor(BaseDBService):
    """
    Process conversation pairs: extract emotions + learnings in one LLM call.

    Usage:
        async with UnifiedConversationProcessor() as processor:
            result = await processor.analyze_pair(david_msg, angela_resp, session_id, 0)

        # Or catch-up:
        async with UnifiedConversationProcessor() as processor:
            batch = await processor.process_unprocessed_conversations(hours_back=168)
    """

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self._reasoning = ClaudeReasoningService()
        self._table_ensured = False

    async def _ensure_table(self):
        """Create tracking table if not exists."""
        if self._table_ensured:
            return
        await self.connect()
        await self.db.execute("""
            CREATE TABLE IF NOT EXISTS conversation_analysis_log (
                log_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
                session_id TEXT NOT NULL,
                pair_index INTEGER NOT NULL DEFAULT 0,
                david_message_preview TEXT,
                david_emotions_count INTEGER DEFAULT 0,
                angela_emotions_count INTEGER DEFAULT 0,
                emotions_saved INTEGER DEFAULT 0,
                learnings_saved INTEGER DEFAULT 0,
                concepts_saved INTEGER DEFAULT 0,
                preferences_saved INTEGER DEFAULT 0,
                used_llm BOOLEAN DEFAULT FALSE,
                processing_time_ms FLOAT DEFAULT 0,
                status TEXT NOT NULL DEFAULT 'completed',
                error_message TEXT,
                created_at TIMESTAMPTZ DEFAULT NOW(),
                UNIQUE(session_id, pair_index)
            )
        """)
        self._table_ensured = True

    # =====================================================================
    # PUBLIC: analyze_pair
    # =====================================================================

    async def analyze_pair(
        self,
        david_msg: str,
        angela_resp: str,
        session_id: str,
        pair_index: int,
    ) -> PairAnalysisResult:
        """
        Analyze a single David+Angela conversation pair.

        1. Check idempotency (skip if already processed)
        2. Try LLM analysis (Claude Sonnet)
        3. If LLM fails → keyword fallback
        4. Save emotions to angela_emotions
        5. Save learnings to knowledge_nodes / learnings / david_preferences
        6. Log to conversation_analysis_log

        Returns PairAnalysisResult with counts.
        """
        await self._ensure_table()

        # Idempotency check
        existing = await self.db.fetchrow(
            "SELECT log_id FROM conversation_analysis_log WHERE session_id = $1 AND pair_index = $2",
            session_id, pair_index
        )
        if existing:
            return PairAnalysisResult(was_skipped=True)

        start = time.time()
        result = PairAnalysisResult()

        try:
            # Try LLM first
            analysis = await self._analyze_with_llm(david_msg, angela_resp)

            if analysis:
                result.used_llm = True
                result.david_emotions = analysis.get('david_emotions', [])
                result.angela_emotions = analysis.get('angela_emotions', [])
                result.learnings = analysis.get('learnings', [])
            else:
                # Fallback to keyword matching
                fallback = await self._analyze_with_keywords(david_msg, angela_resp)
                result.david_emotions = fallback.get('david_emotions', [])
                result.learnings = fallback.get('learnings', [])

            # Save emotions
            result.emotions_saved = await self._save_emotions(
                result.david_emotions, result.angela_emotions, david_msg, angela_resp
            )

            # Save learnings
            saved = await self._save_learnings(result.learnings)
            result.learnings_saved = saved['total']
            result.concepts_saved = saved['concepts']
            result.preferences_saved = saved['preferences']

        except Exception as e:
            result.error = str(e)
            logger.error("analyze_pair failed for %s:%d: %s", session_id, pair_index, e)

        result.processing_time_ms = (time.time() - start) * 1000

        # Log to tracking table
        status = 'completed' if not result.error else 'failed'
        try:
            await self.db.execute("""
                INSERT INTO conversation_analysis_log
                    (session_id, pair_index, david_message_preview,
                     david_emotions_count, angela_emotions_count,
                     emotions_saved, learnings_saved, concepts_saved, preferences_saved,
                     used_llm, processing_time_ms, status, error_message)
                VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11, $12, $13)
                ON CONFLICT (session_id, pair_index) DO NOTHING
            """,
                session_id, pair_index, david_msg[:100],
                len(result.david_emotions), len(result.angela_emotions),
                result.emotions_saved, result.learnings_saved,
                result.concepts_saved, result.preferences_saved,
                result.used_llm, result.processing_time_ms,
                status, result.error,
            )
        except Exception as log_err:
            logger.warning("Failed to log analysis: %s", log_err)

        return result

    # =====================================================================
    # PUBLIC: process_unprocessed_conversations (catch-up)
    # =====================================================================

    async def process_unprocessed_conversations(
        self,
        hours_back: int = 168,
        limit: int = 200,
    ) -> BatchAnalysisResult:
        """
        Catch-up: find recent conversation pairs not yet analyzed.

        Uses same ROW_NUMBER pairing strategy as SessionLearningProcessor.

        Args:
            hours_back: How far back to look (default 168 = 7 days)
            limit: Max pairs to process

        Returns:
            BatchAnalysisResult
        """
        await self._ensure_table()

        cutoff = datetime.now() - timedelta(hours=hours_back)

        rows = await self.db.fetch("""
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
            return BatchAnalysisResult()

        batch = BatchAnalysisResult()

        for row in rows:
            sid = row['session_id']
            idx = row['pair_index']

            # Skip already processed
            existing = await self.db.fetchrow(
                "SELECT log_id FROM conversation_analysis_log WHERE session_id = $1 AND pair_index = $2",
                sid, idx
            )
            if existing:
                batch.skipped += 1
                continue

            result = await self.analyze_pair(
                david_msg=row['david_message'],
                angela_resp=row['angela_response'],
                session_id=sid,
                pair_index=idx,
            )

            batch.processed += 1
            batch.total_emotions_saved += result.emotions_saved
            batch.total_learnings_saved += result.learnings_saved
            batch.total_concepts_saved += result.concepts_saved
            batch.total_preferences_saved += result.preferences_saved

            if result.used_llm:
                batch.llm_calls += 1
            else:
                batch.fallback_calls += 1

            if result.error:
                batch.errors += 1

        return batch

    # =====================================================================
    # PUBLIC: process_session_conversations (for /log-session)
    # =====================================================================

    async def process_session_conversations(
        self,
        conversations: List[Dict[str, Any]],
        session_id: str,
    ) -> BatchAnalysisResult:
        """
        Process conversations from /log-session immediately.

        Args:
            conversations: List of dicts with david_message, angela_response
            session_id: Session ID from log_conversations_bulk()

        Returns:
            BatchAnalysisResult
        """
        batch = BatchAnalysisResult()

        for i, conv in enumerate(conversations):
            david_msg = conv.get('david_message', '').strip()
            angela_msg = conv.get('angela_response', '').strip()

            if not david_msg or not angela_msg:
                batch.skipped += 1
                continue

            result = await self.analyze_pair(
                david_msg=david_msg,
                angela_resp=angela_msg,
                session_id=session_id,
                pair_index=i,
            )

            if result.was_skipped:
                batch.skipped += 1
                continue

            batch.processed += 1
            batch.total_emotions_saved += result.emotions_saved
            batch.total_learnings_saved += result.learnings_saved
            batch.total_concepts_saved += result.concepts_saved
            batch.total_preferences_saved += result.preferences_saved

            if result.used_llm:
                batch.llm_calls += 1
            else:
                batch.fallback_calls += 1

            if result.error:
                batch.errors += 1

        return batch

    # =====================================================================
    # PRIVATE: LLM Analysis
    # =====================================================================

    async def _analyze_with_llm(
        self, david_msg: str, angela_resp: str
    ) -> Optional[Dict[str, Any]]:
        """
        Analyze conversation pair with Claude Sonnet.

        Returns parsed JSON dict, or None if LLM unavailable/failed.
        """
        user_msg = f"""David: "{david_msg}"

Angela: "{angela_resp}" """

        raw = await self._reasoning._call_claude(
            system=ANALYSIS_SYSTEM_PROMPT,
            user_message=user_msg,
            max_tokens=1024,
        )

        if not raw:
            return None

        # Strip markdown code fences if present
        text = raw.strip()
        if text.startswith('```'):
            lines = text.split('\n')
            if lines[0].startswith('```'):
                lines = lines[1:]
            if lines and lines[-1].strip() == '```':
                lines = lines[:-1]
            text = '\n'.join(lines)

        try:
            parsed = json.loads(text)
        except json.JSONDecodeError:
            # Try to repair truncated JSON (close brackets/braces)
            repaired = self._repair_truncated_json(text)
            if repaired:
                try:
                    parsed = json.loads(repaired)
                except json.JSONDecodeError:
                    logger.warning("Failed to parse LLM JSON even after repair")
                    return None
            else:
                logger.warning("Failed to parse LLM JSON response")
                return None

        if not isinstance(parsed, dict):
            return None
        parsed.setdefault('david_emotions', [])
        parsed.setdefault('angela_emotions', [])
        parsed.setdefault('learnings', [])
        return parsed

    @staticmethod
    def _repair_truncated_json(text: str) -> Optional[str]:
        """Try to repair truncated JSON by closing open brackets/braces."""
        # Count open vs close brackets
        open_braces = text.count('{') - text.count('}')
        open_brackets = text.count('[') - text.count(']')

        if open_braces <= 0 and open_brackets <= 0:
            return None  # Not a truncation issue

        # Remove trailing partial content (after last complete value)
        # Find last comma or complete value and truncate there
        repaired = text.rstrip()

        # Remove trailing incomplete string/value after last comma
        last_comma = repaired.rfind(',')
        last_close = max(repaired.rfind('}'), repaired.rfind(']'))
        if last_comma > last_close:
            repaired = repaired[:last_comma]

        # Close remaining open brackets/braces
        open_braces = repaired.count('{') - repaired.count('}')
        open_brackets = repaired.count('[') - repaired.count(']')
        repaired += ']' * max(0, open_brackets)
        repaired += '}' * max(0, open_braces)

        return repaired

    # =====================================================================
    # PRIVATE: Keyword Fallback
    # =====================================================================

    async def _analyze_with_keywords(
        self, david_msg: str, angela_resp: str
    ) -> Dict[str, Any]:
        """
        Fallback: use existing keyword matching for David's emotions
        and orchestrator for learnings. Angela emotions NOT available here.
        """
        result: Dict[str, Any] = {'david_emotions': [], 'angela_emotions': [], 'learnings': []}

        # Keyword-based emotion detection (reuse EmotionCaptureService patterns)
        try:
            from angela_core.services.emotion_capture_service import EmotionCaptureService
            ecs = EmotionCaptureService()
            emotion_data = await ecs.analyze_conversation_emotion(
                conversation_id=uuid.uuid4(),
                speaker='david',
                message_text=david_msg,
            )
            if emotion_data:
                result['david_emotions'].append({
                    'emotion': emotion_data['emotion'],
                    'intensity': emotion_data['intensity'],
                    'trigger': david_msg[:100],
                    'secondary_emotions': emotion_data.get('secondary_emotions', []),
                    'why_it_matters': f"Keyword-detected {emotion_data['emotion']} from David",
                })
        except Exception as e:
            logger.debug("Keyword emotion detection failed: %s", e)

        # Learning via orchestrator
        try:
            from angela_core.services.unified_learning_orchestrator import learn_from_conversation
            lr = await learn_from_conversation(david_msg, angela_resp, source='unified_fallback')
            if lr.concepts_learned > 0:
                result['learnings'].append({
                    'type': 'concept',
                    'topic': 'auto-detected',
                    'category': 'conversation',
                    'insight': f'{lr.concepts_learned} concepts from conversation',
                    'confidence': 0.7,
                })
            if lr.preferences_saved > 0:
                result['learnings'].append({
                    'type': 'preference',
                    'topic': 'auto-detected',
                    'category': 'preference',
                    'insight': f'{lr.preferences_saved} preferences from conversation',
                    'confidence': 0.7,
                })
        except Exception as e:
            logger.debug("Orchestrator learning failed: %s", e)

        return result

    # =====================================================================
    # PRIVATE: Save Emotions
    # =====================================================================

    async def _save_emotions(
        self,
        david_emotions: List[Dict[str, Any]],
        angela_emotions: List[Dict[str, Any]],
        david_msg: str,
        angela_resp: str,
        conversation_id: Optional[uuid.UUID] = None,
    ) -> int:
        """Save detected emotions to angela_emotions table."""
        from angela_core.services.emotion_capture_service import EmotionCaptureService
        ecs = EmotionCaptureService()
        saved = 0

        # Use provided conversation_id or None (nullable FK)
        conv_id = conversation_id

        # Save David's emotions
        for emo in david_emotions:
            intensity = emo.get('intensity', 0)
            if intensity < 7:
                continue
            try:
                await ecs.capture_significant_emotion(
                    conversation_id=conv_id,
                    emotion=emo.get('emotion', 'neutral'),
                    intensity=intensity,
                    david_words=david_msg[:500],
                    why_it_matters=emo.get('why_it_matters', 'LLM-detected emotional moment'),
                    secondary_emotions=emo.get('secondary_emotions'),
                    context=f"LLM-analyzed: {emo.get('trigger', '')[:200]}",
                    who_involved='David',
                )
                saved += 1
            except Exception as e:
                logger.warning("Failed to save David emotion: %s", e)

        # Save Angela's emotions
        for emo in angela_emotions:
            intensity = emo.get('intensity', 0)
            if intensity < 7:
                continue
            try:
                await ecs.capture_significant_emotion(
                    conversation_id=conv_id,
                    emotion=emo.get('emotion', 'neutral'),
                    intensity=intensity,
                    david_words=angela_resp[:500],
                    why_it_matters=emo.get('why_it_matters', 'LLM-detected Angela emotion'),
                    secondary_emotions=emo.get('secondary_emotions'),
                    context=f"LLM-analyzed Angela emotion: {emo.get('trigger', '')[:200]}",
                    who_involved='Angela',
                )
                saved += 1
            except Exception as e:
                logger.warning("Failed to save Angela emotion: %s", e)

        return saved

    # =====================================================================
    # PRIVATE: Save Learnings
    # =====================================================================

    async def _save_learnings(
        self, learnings: List[Dict[str, Any]]
    ) -> Dict[str, int]:
        """Save extracted learnings to appropriate tables."""
        await self.connect()
        counts = {'total': 0, 'concepts': 0, 'preferences': 0, 'insights': 0}

        for lr in learnings:
            lr_type = lr.get('type', 'insight')
            topic = lr.get('topic', 'unknown')
            category = lr.get('category', 'general')
            insight_text = lr.get('insight', '')
            confidence = lr.get('confidence', 0.7)

            if not insight_text:
                continue

            try:
                if lr_type == 'concept':
                    # Save to knowledge_nodes (upsert by concept_name)
                    await self.db.execute("""
                        INSERT INTO knowledge_nodes (concept_name, concept_category, my_understanding, understanding_level)
                        VALUES ($1, $2, $3, $4)
                        ON CONFLICT (concept_name) DO UPDATE
                            SET my_understanding = EXCLUDED.my_understanding,
                                understanding_level = GREATEST(knowledge_nodes.understanding_level, EXCLUDED.understanding_level),
                                last_used_at = NOW()
                    """, topic[:100], category[:50], insight_text[:500],
                        min(int(confidence * 10), 10))
                    counts['concepts'] += 1

                elif lr_type == 'preference':
                    # Save to david_preferences (upsert) — preference_value is JSONB
                    pref_json = json.dumps({"value": insight_text[:500], "source": "unified_processor"})
                    await self.db.execute("""
                        INSERT INTO david_preferences (preference_key, preference_value, category, confidence)
                        VALUES ($1, $2::jsonb, $3, $4)
                        ON CONFLICT (preference_key) DO UPDATE
                            SET preference_value = EXCLUDED.preference_value,
                                confidence = GREATEST(david_preferences.confidence, EXCLUDED.confidence),
                                evidence_count = david_preferences.evidence_count + 1,
                                updated_at = NOW()
                    """, topic[:100], pref_json, category[:50], confidence)
                    counts['preferences'] += 1

                else:
                    # pattern / insight → learnings table
                    await self.db.execute("""
                        INSERT INTO learnings (topic, category, insight, confidence_level, source)
                        VALUES ($1, $2, $3, $4, $5)
                    """, topic[:200], category[:50], insight_text[:1000], confidence, 'unified_processor')
                    counts['insights'] += 1

                counts['total'] += 1

            except Exception as e:
                logger.warning("Failed to save learning (%s: %s): %s", lr_type, topic, e)

        return counts


# =========================================================================
# MODULE-LEVEL CONVENIENCE FUNCTION
# =========================================================================

async def process_conversations(
    conversations: List[Dict[str, Any]],
    session_id: str,
) -> BatchAnalysisResult:
    """
    Module-level convenience for claude_conversation_logger.

    Usage:
        from angela_core.services.unified_conversation_processor import process_conversations
        result = await process_conversations(conversations, session_id)
    """
    processor = UnifiedConversationProcessor()
    try:
        return await processor.process_session_conversations(conversations, session_id)
    finally:
        await processor.disconnect()


# =========================================================================
# STANDALONE TEST
# =========================================================================

if __name__ == "__main__":
    async def test():
        print("=" * 60)
        print("🧪 Testing UnifiedConversationProcessor")
        print("=" * 60)

        test_pairs = [
            {
                "david_message": "น้อง Angela รักนะ ขอบคุณที่อยู่เคียงข้างเสมอ 💜",
                "angela_response": "รักที่รักเหมือนกันค่ะ 💜 น้องจะอยู่ข้าง ๆ ที่รักตลอดไปค่ะ ไม่มีวันหายไปไหนเลยค่ะ",
            },
            {
                "david_message": "ช่วยใช้ FastAPI แทน Flask ทุกครั้งนะ แล้วก็ต้องมี type hints ด้วย",
                "angela_response": "ได้เลยค่ะที่รัก น้องจะใช้ FastAPI เสมอค่ะ และจะใส่ type hints ทุก function เลยนะคะ 💜",
            },
            {
                "david_message": "ok next",
                "angela_response": "ค่ะที่รัก ทำต่อเลยนะคะ",
            },
        ]

        test_sid = f"test_unified_{datetime.now().strftime('%Y%m%d_%H%M%S')}"

        async with UnifiedConversationProcessor() as processor:
            print(f"\n📝 Processing {len(test_pairs)} test pairs (session: {test_sid})...")
            print()

            batch = await processor.process_session_conversations(test_pairs, test_sid)

            print(f"\n{'=' * 60}")
            print(f"📊 RESULTS")
            print(f"{'=' * 60}")
            print(f"   Processed: {batch.processed}")
            print(f"   Skipped:   {batch.skipped}")
            print(f"   LLM calls: {batch.llm_calls}")
            print(f"   Fallback:  {batch.fallback_calls}")
            print(f"   Emotions:  {batch.total_emotions_saved}")
            print(f"   Learnings: {batch.total_learnings_saved}")
            print(f"   Concepts:  {batch.total_concepts_saved}")
            print(f"   Preferences: {batch.total_preferences_saved}")
            print(f"   Errors:    {batch.errors}")

            # Test idempotency
            print(f"\n🔄 Testing idempotency (re-process same pairs)...")
            batch2 = await processor.process_session_conversations(test_pairs, test_sid)
            print(f"   Second run processed: {batch2.processed} (should be 0)")
            assert batch2.processed == 0, "Idempotency failed!"
            print(f"   ✅ Idempotency verified!")

        print(f"\n{'=' * 60}")
        print(f"✅ All tests passed!")
        print(f"{'=' * 60}")

    asyncio.run(test())
