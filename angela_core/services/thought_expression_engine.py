"""
Thought Expression Engine — Brain-Based Architecture Phase 6
=============================================================
Bridge between internal thinking (angela_thoughts) and external action.

Pipeline:
  1. SELECT active thoughts with motivation >= MOTIVATION_THRESHOLD (0.50)
  2. FILTER (dedup 6h window, David state, rate limits)
  3. PRE-CHECK: Telegram rate limit + David state (once per cycle, not per thought)
  4. DECIDE channel: >= 0.70 → Telegram, >= 0.50 → chat_queue
  4. COMPOSE message (S1 as-is, S2 optionally polish via Ollama)
  5. ROUTE → CareInterventionService (Telegram) or INSERT (chat_queue)
  6. MARK status='expressed' on angela_thoughts

Shares rate limits with ProactiveActionEngine via CareInterventionService.

Cost: ~$0/day (all Ollama local, no external LLM)

Inspired by: Stanford Generative Agents (expression from inner monologue),
             CHI 2025 Inner Thoughts (thought → action bridge)

By: น้อง Angela 💜
Created: 2026-02-15
"""

import json
import logging
from dataclasses import dataclass, field
from datetime import datetime
from typing import Dict, List, Optional, Any

from angela_core.services.base_db_service import BaseDBService
from angela_core.utils.timezone import now_bangkok

logger = logging.getLogger('thought_expression')


# ============================================================
# DATA STRUCTURES
# ============================================================

@dataclass
class ExpressionResult:
    """Result of a single thought expression attempt."""
    thought_id: str
    channel: str                    # telegram, chat_queue
    success: bool
    message: str = ""
    suppress_reason: Optional[str] = None


@dataclass
class ExpressionCycleResult:
    """Result of a complete expression cycle."""
    thoughts_considered: int
    thoughts_filtered: int
    expressed_telegram: int
    expressed_chat: int
    suppressed: int
    cycle_duration_ms: float


# ============================================================
# CONSTANTS
# ============================================================

MOTIVATION_THRESHOLD = 0.50     # Restored: filter low-quality thoughts (was 0.35)
TELEGRAM_THRESHOLD = 0.70       # Restored: only high-motivation to Telegram (was 0.50)
MAX_TELEGRAM_PER_DAY = 3        # Restored: prevent Telegram flooding (was 5)
MIN_HOURS_BETWEEN = 2           # Restored: respect David's time (was 1)
MAX_CHAT_QUEUE = 5              # Keep: more thoughts visible at init
DEDUP_HOURS = 6                 # Restored: prevent repetitive messages (was 4)
QUEUE_EXPIRE_HOURS = 24         # Expire stale queue items after this


# States where David should not be interrupted via Telegram
NO_INTERRUPT_STATES = frozenset({'focused', 'stressed', 'frustrated'})


# ============================================================
# THOUGHT EXPRESSION ENGINE
# ============================================================

class ThoughtExpressionEngine(BaseDBService):
    """
    Bridge between internal thinking and external expression.

    High-motivation thoughts get routed to:
    - Telegram (urgent, motivation >= 0.70, David not focused/stressed)
    - Chat queue (next Claude Code session, motivation >= 0.50)

    Rate limits checked ONCE per cycle to avoid N failed log entries.
    """

    async def run_expression_cycle(self) -> ExpressionCycleResult:
        """
        Main entry: select → filter → compose → route → mark.

        Returns cycle result with counts.
        """
        start = now_bangkok()
        await self.connect()

        # Load tuned thresholds (Phase 7D)
        await self._load_tuned_thresholds()

        # 1. Select expressible thoughts
        candidates = await self._select_expressible_thoughts()
        if not candidates:
            logger.info("💬 No expressible thoughts this cycle")
            duration = (now_bangkok() - start).total_seconds() * 1000
            return ExpressionCycleResult(
                thoughts_considered=0, thoughts_filtered=0,
                expressed_telegram=0, expressed_chat=0,
                suppressed=0, cycle_duration_ms=round(duration, 1),
            )

        logger.info("💬 %d candidate thoughts for expression", len(candidates))

        # 2. Filter
        filtered, suppressed_list = await self._filter_thoughts(candidates)

        # Log suppressed
        for thought, reason in suppressed_list:
            await self._log_expression(
                thought_id=str(thought["thought_id"]),
                channel="suppressed",
                message=thought.get("content", "")[:200],
                success=False,
                suppress_reason=reason,
                motivation=thought.get("motivation_score", 0),
            )

        if not filtered:
            logger.info("💬 All candidates filtered out")
            duration = (now_bangkok() - start).total_seconds() * 1000
            return ExpressionCycleResult(
                thoughts_considered=len(candidates),
                thoughts_filtered=len(suppressed_list),
                expressed_telegram=0, expressed_chat=0,
                suppressed=len(suppressed_list),
                cycle_duration_ms=round(duration, 1),
            )

        # 3. Decide channel + compose + VERIFY + route
        telegram_count = 0
        chat_count = 0

        # ── Pre-cycle checks (avoid N failed Telegram attempts) ──
        telegram_blocked = False
        telegram_block_reason = None

        # Check David's state once
        david_state = await self._get_david_state()
        if david_state in NO_INTERRUPT_STATES:
            telegram_blocked = True
            telegram_block_reason = f"state_filter:{david_state}"
            logger.info("💬 Telegram blocked for cycle: David is %s", david_state)

        # Check Telegram rate limit once
        if not telegram_blocked:
            try:
                from angela_core.services.care_intervention_service import CareInterventionService
                rate_svc = CareInterventionService()
                can_send, reason = await rate_svc.should_intervene("care_message")
                if rate_svc._owns_db and rate_svc.db:
                    await rate_svc.db.disconnect()
                if not can_send:
                    telegram_blocked = True
                    telegram_block_reason = f"rate_limit:{reason}"
                    logger.info("💬 Telegram blocked for cycle: %s", reason)
            except Exception as e:
                telegram_blocked = True
                telegram_block_reason = f"error:{e}"
                logger.warning("💬 Telegram rate check failed: %s", e)

        # Self-critique gate (Phase 2)
        critique_svc = None
        try:
            from angela_core.services.self_critique_service import SelfCritiqueService
            critique_svc = SelfCritiqueService()
        except Exception as e:
            logger.debug("SelfCritiqueService unavailable: %s", e)

        for thought in filtered:
            channel = self._decide_channel(thought)
            message = await self._compose_message(thought)

            # ── Self-Critique Gate ──
            if critique_svc:
                try:
                    verification = await critique_svc.verify_before_express(
                        thought=thought,
                        composed_message=message,
                        david_state=david_state,
                    )

                    # Log critique result
                    await critique_svc.log_critique(
                        self.db,
                        str(thought["thought_id"]),
                        message,
                        verification,
                    )

                    if not verification.passed:
                        # Suppress this thought
                        await self._log_expression(
                            thought_id=str(thought["thought_id"]),
                            channel="suppressed",
                            message=message[:200],
                            success=False,
                            suppress_reason=f"critique:{verification.suppress_reason}",
                            motivation=thought.get("motivation_score", 0),
                        )
                        suppressed_list.append((thought, f"critique:{verification.suppress_reason}"))
                        continue

                    # Use suggested (possibly hedged) message
                    message = verification.suggested_message
                except Exception as e:
                    logger.debug("Self-critique check failed (permissive): %s", e)

            # ── Route to Telegram or chat_queue ──
            if channel == "telegram" and telegram_blocked:
                # Telegram blocked for this cycle → direct to chat_queue (no log noise)
                channel = "chat_queue"

            if channel == "telegram":
                result = await self._express_via_telegram(thought, message)
                if result.success:
                    telegram_count += 1
                    await self._log_expression(
                        thought_id=str(thought["thought_id"]),
                        channel="telegram",
                        message=message,
                        success=True,
                        suppress_reason=None,
                        motivation=thought.get("motivation_score", 0),
                    )
                else:
                    # Telegram failed unexpectedly → fallback to chat queue
                    await self._log_expression(
                        thought_id=str(thought["thought_id"]),
                        channel="telegram",
                        message=message,
                        success=False,
                        suppress_reason=result.suppress_reason,
                        motivation=thought.get("motivation_score", 0),
                    )
                    # Block further Telegram attempts this cycle
                    telegram_blocked = True
                    telegram_block_reason = result.suppress_reason
                    # Fallback
                    fallback = await self._queue_for_chat(thought, message)
                    if fallback.success:
                        chat_count += 1
                        channel = "chat_queue"
                        result = fallback
            else:
                result = await self._queue_for_chat(thought, message)
                if result.success:
                    chat_count += 1
                await self._log_expression(
                    thought_id=str(thought["thought_id"]),
                    channel="chat_queue",
                    message=message,
                    success=result.success,
                    suppress_reason=result.suppress_reason,
                    motivation=thought.get("motivation_score", 0),
                )

            # Mark thought as expressed
            if result.success:
                await self._mark_expressed(
                    str(thought["thought_id"]), channel
                )

        # Expire stale queue items
        expired = await self.expire_stale_queue()
        if expired > 0:
            logger.info("💬 Expired %d stale queue items", expired)

        duration = (now_bangkok() - start).total_seconds() * 1000

        result = ExpressionCycleResult(
            thoughts_considered=len(candidates),
            thoughts_filtered=len(suppressed_list),
            expressed_telegram=telegram_count,
            expressed_chat=chat_count,
            suppressed=len(suppressed_list),
            cycle_duration_ms=round(duration, 1),
        )

        logger.info(
            "💬 Expression cycle: %d considered, %d filtered, "
            "%d→telegram, %d→chat_queue, %.0fms",
            result.thoughts_considered, result.thoughts_filtered,
            result.expressed_telegram, result.expressed_chat,
            result.cycle_duration_ms,
        )

        return result

    # ============================================================
    # 1. SELECT — Fetch expressible thoughts
    # ============================================================

    async def _select_expressible_thoughts(self) -> List[Dict[str, Any]]:
        """
        Select active thoughts with motivation >= threshold.
        Ordered by motivation DESC, limited to 10.
        """
        await self.connect()
        rows = await self.db.fetch("""
            SELECT thought_id, thought_type, content, stimulus_ids,
                   motivation_score, motivation_breakdown, status, created_at
            FROM angela_thoughts
            WHERE status = 'active'
            AND motivation_score >= $1
            ORDER BY motivation_score DESC
            LIMIT 10
        """, MOTIVATION_THRESHOLD)
        return [dict(r) for r in rows]

    # ============================================================
    # 2. FILTER — Dedup, state check, rate limits
    # ============================================================

    async def _filter_thoughts(
        self, thoughts: List[Dict[str, Any]]
    ) -> tuple:
        """
        Filter thoughts through dedup, state, and rate limit checks.

        Returns (passed_list, suppressed_list) where suppressed_list
        is list of (thought, reason) tuples.
        """
        await self.connect()
        passed = []
        suppressed = []

        for thought in thoughts:
            # A. Dedup: check if similar content expressed in last DEDUP_HOURS
            content_prefix = (thought.get("content") or "")[:30]
            if content_prefix:
                dup = await self.db.fetchrow("""
                    SELECT log_id FROM thought_expression_log
                    WHERE success = TRUE
                    AND message_sent ILIKE $1
                    AND created_at > NOW() - INTERVAL '1 hour' * $2
                    LIMIT 1
                """, f"%{content_prefix}%", DEDUP_HOURS)
                if dup:
                    suppressed.append((thought, "duplicate"))
                    continue

            # B. Check pending chat queue count (don't overflow)
            if thought.get("motivation_score", 0) < TELEGRAM_THRESHOLD:
                pending_count = await self.db.fetchval("""
                    SELECT COUNT(*) FROM thought_expression_queue
                    WHERE status = 'pending'
                """) or 0
                if pending_count >= MAX_CHAT_QUEUE:
                    suppressed.append((thought, "queue_full"))
                    continue

            passed.append(thought)

        return passed, suppressed

    # ============================================================
    # 3. DECIDE — Which channel to use
    # ============================================================

    def _decide_channel(self, thought: Dict[str, Any]) -> str:
        """
        Decide expression channel based on motivation score.

        >= TELEGRAM_THRESHOLD → telegram
        >= MOTIVATION_THRESHOLD → chat_queue
        """
        motivation = thought.get("motivation_score", 0)
        if motivation >= TELEGRAM_THRESHOLD:
            return "telegram"
        return "chat_queue"

    # ============================================================
    # 4. COMPOSE — Format message for expression
    # ============================================================

    async def _compose_message(self, thought: Dict[str, Any]) -> str:
        """
        Compose the expression message using DynamicExpressionComposer.

        Phase 4: Context-aware composition replacing static pass-through.
        """
        content = (thought.get("content") or "").strip()
        if not content:
            return "น้องคิดถึงที่รักค่ะ 💜"

        try:
            from angela_core.services.dynamic_expression_composer import (
                DynamicExpressionComposer, ExpressionContext,
            )
            from angela_core.services.metacognitive_state import MetacognitiveStateManager

            composer = DynamicExpressionComposer()
            meta_mgr = MetacognitiveStateManager()

            # Determine thought type for expression
            thought_type = thought.get("thought_type", "default")
            # Map to expression types
            if "เป็นห่วง" in content or "ดึก" in content:
                expr_type = "concern"
            elif "คิดถึง" in content or "รัก" in content:
                expr_type = "affection"
            elif "สงสัย" in content or "อยากรู้" in content:
                expr_type = "curiosity"
            elif "จำได้" in content or "ครบรอบ" in content:
                expr_type = "memory"
            else:
                expr_type = "default"

            david_state = await self._get_david_state()

            ctx = ExpressionContext(
                thought_content=content,
                thought_type=expr_type,
                motivation_score=thought.get("motivation_score", 0.5),
                metacognitive_state=meta_mgr.get_expression_modifiers(),
                david_state=david_state,
            )

            return composer.compose_expression(ctx)
        except Exception as e:
            logger.debug("DynamicExpressionComposer fallback: %s", e)
            return content

    # ============================================================
    # 5a. ROUTE — Express via Telegram
    # ============================================================

    async def _express_via_telegram(
        self, thought: Dict[str, Any], message: str
    ) -> ExpressionResult:
        """
        Send thought via CareInterventionService (reuse Telegram infra).

        Delegates rate limiting to CareInterventionService.should_intervene().
        """
        thought_id = str(thought["thought_id"])

        try:
            from angela_core.services.care_intervention_service import CareInterventionService
            svc = CareInterventionService()

            # Check rate limits via existing infra
            can_send, reason = await svc.should_intervene("care_message")
            if not can_send:
                if svc._owns_db and svc.db:
                    await svc.db.disconnect()
                return ExpressionResult(
                    thought_id=thought_id,
                    channel="telegram",
                    success=False,
                    message=message,
                    suppress_reason=f"rate_limit:{reason}",
                )

            # Check David's state — don't interrupt if focused/stressed
            david_state = await self._get_david_state()
            if david_state in NO_INTERRUPT_STATES:
                if svc._owns_db and svc.db:
                    await svc.db.disconnect()
                return ExpressionResult(
                    thought_id=thought_id,
                    channel="telegram",
                    success=False,
                    message=message,
                    suppress_reason=f"state_filter:{david_state}",
                )

            # Send via care message
            result = await svc.execute_care_message(
                context={"trigger_reason": "brain_thought", "thought_id": thought_id},
                custom_message=f"💭 {message}",
            )

            if svc._owns_db and svc.db:
                await svc.db.disconnect()

            return ExpressionResult(
                thought_id=thought_id,
                channel="telegram",
                success=result.success,
                message=message,
                suppress_reason=None if result.success else (result.error or "send_failed"),
            )

        except Exception as e:
            logger.warning("Telegram expression failed: %s", e)
            return ExpressionResult(
                thought_id=thought_id,
                channel="telegram",
                success=False,
                message=message,
                suppress_reason=f"error:{e}",
            )

    # ============================================================
    # 5b. ROUTE — Queue for next Claude Code session
    # ============================================================

    async def _queue_for_chat(
        self, thought: Dict[str, Any], message: str
    ) -> ExpressionResult:
        """Insert into thought_expression_queue for display at next init.py."""
        thought_id = str(thought["thought_id"])
        await self.connect()

        try:
            await self.db.execute("""
                INSERT INTO thought_expression_queue
                    (thought_id, message, channel, status)
                VALUES ($1, $2, 'chat_queue', 'pending')
            """, thought_id, message)

            return ExpressionResult(
                thought_id=thought_id,
                channel="chat_queue",
                success=True,
                message=message,
            )
        except Exception as e:
            logger.warning("Chat queue insert failed: %s", e)
            return ExpressionResult(
                thought_id=thought_id,
                channel="chat_queue",
                success=False,
                message=message,
                suppress_reason=f"error:{e}",
            )

    # ============================================================
    # 6. MARK — Update thought status
    # ============================================================

    async def _mark_expressed(self, thought_id: str, channel: str) -> None:
        """Mark a thought as expressed in angela_thoughts."""
        await self.connect()
        try:
            await self.db.execute("""
                UPDATE angela_thoughts
                SET status = 'expressed',
                    expressed_via = $1,
                    expressed_at = NOW()
                WHERE thought_id = $2
                AND status = 'active'
            """, channel, thought_id)
        except Exception as e:
            logger.warning("Failed to mark thought expressed: %s", e)

    # ============================================================
    # CHAT QUEUE METHODS (called by init.py)
    # ============================================================

    async def get_pending_chat_thoughts(self, limit: int = 3) -> List[Dict[str, Any]]:
        """
        Get pending chat queue items for display at session start.
        Called by init.py.
        """
        await self.connect()
        rows = await self.db.fetch("""
            SELECT q.queue_id, q.thought_id, q.message, q.created_at,
                   t.motivation_score, t.thought_type
            FROM thought_expression_queue q
            JOIN angela_thoughts t ON t.thought_id = q.thought_id
            WHERE q.status = 'pending'
            ORDER BY t.motivation_score DESC
            LIMIT $1
        """, limit)
        return [dict(r) for r in rows]

    async def mark_chat_thoughts_shown(self, queue_ids: List[str]) -> int:
        """Mark queue items as shown. Called by init.py after display."""
        if not queue_ids:
            return 0
        await self.connect()
        try:
            result = await self.db.execute("""
                UPDATE thought_expression_queue
                SET status = 'shown', shown_at = NOW()
                WHERE queue_id = ANY($1::uuid[])
                AND status = 'pending'
            """, queue_ids)
            count = int(result.split()[-1]) if isinstance(result, str) else 0
            return count
        except Exception as e:
            logger.warning("Failed to mark thoughts shown: %s", e)
            return 0

    async def expire_stale_queue(self) -> int:
        """Expire pending queue items older than QUEUE_EXPIRE_HOURS."""
        await self.connect()
        try:
            result = await self.db.execute("""
                UPDATE thought_expression_queue
                SET status = 'expired'
                WHERE status = 'pending'
                AND created_at < NOW() - INTERVAL '1 hour' * $1
            """, QUEUE_EXPIRE_HOURS)
            count = int(result.split()[-1]) if isinstance(result, str) else 0
            return count
        except Exception as e:
            logger.warning("Failed to expire stale queue: %s", e)
            return 0

    # ============================================================
    # HELPERS
    # ============================================================

    async def _get_david_state(self) -> str:
        """Get David's current emotional state from adaptation log."""
        await self.connect()
        try:
            row = await self.db.fetchrow("""
                SELECT dominant_state
                FROM emotional_adaptation_log
                WHERE confidence > 0.5
                ORDER BY created_at DESC
                LIMIT 1
            """)
            return row["dominant_state"] if row else "neutral"
        except Exception:
            return "neutral"

    async def _log_expression(
        self, thought_id: str, channel: str, message: str,
        success: bool, suppress_reason: Optional[str],
        motivation: float,
    ) -> None:
        """Log an expression attempt to thought_expression_log."""
        await self.connect()
        david_state = await self._get_david_state()
        try:
            await self.db.execute("""
                INSERT INTO thought_expression_log
                    (thought_id, channel, message_sent, success,
                     suppress_reason, david_state, motivation_score)
                VALUES ($1, $2, $3, $4, $5, $6, $7)
            """,
                thought_id, channel, message[:500], success,
                suppress_reason, david_state, motivation,
            )
        except Exception as e:
            logger.warning("Failed to log expression: %s", e)

    # ============================================================
    # TUNED THRESHOLD LOADING (Phase 7D)
    # ============================================================

    async def _load_tuned_thresholds(self) -> None:
        """Load tuned thresholds from companion_patterns (if any)."""
        global MOTIVATION_THRESHOLD, TELEGRAM_THRESHOLD
        try:
            await self.connect()
            row = await self.db.fetchrow("""
                SELECT pattern_data FROM companion_patterns
                WHERE pattern_category = 'brain_thresholds'
                ORDER BY last_observed DESC LIMIT 1
            """)
            if row and row['pattern_data']:
                import json
                data = row['pattern_data']
                if isinstance(data, str):
                    data = json.loads(data)
                if isinstance(data, dict):
                    if 'motivation_threshold' in data:
                        MOTIVATION_THRESHOLD = float(data['motivation_threshold'])
                    if 'telegram_threshold' in data:
                        TELEGRAM_THRESHOLD = float(data['telegram_threshold'])
                    logger.debug("Loaded tuned thresholds: motivation=%.2f, telegram=%.2f",
                                 MOTIVATION_THRESHOLD, TELEGRAM_THRESHOLD)
        except Exception as e:
            logger.debug("No tuned thresholds loaded: %s", e)

    # ============================================================
    # COMPARISON EVALUATION (Phase 7A — dry run without expressing)
    # ============================================================

    async def evaluate_for_comparison(self) -> List[Dict[str, Any]]:
        """
        Return candidate thoughts that WOULD be expressed,
        without actually expressing them. Used by BrainMigrationEngine
        for comparison with rule-based actions.
        """
        await self.connect()

        candidates = await self._select_expressible_thoughts()
        if not candidates:
            return []

        filtered, _ = await self._filter_thoughts(candidates)

        result = []
        for thought in filtered:
            channel = self._decide_channel(thought)
            message = await self._compose_message(thought)
            result.append({
                'thought_id': str(thought.get('thought_id', '')),
                'content': thought.get('content', ''),
                'message': message,
                'channel': channel,
                'motivation_score': thought.get('motivation_score', 0),
                'thought_type': thought.get('thought_type', ''),
            })

        return result

    async def has_brain_expressed(
        self, keywords: List[str], hours: int = 2
    ) -> bool:
        """
        Check if brain has expressed a thought matching any keyword recently.
        Used by ProactiveActionEngine for deduplication.
        """
        await self.connect()
        for kw in keywords:
            if not kw:
                continue
            row = await self.db.fetchrow("""
                SELECT log_id FROM thought_expression_log
                WHERE success = TRUE
                AND message_sent ILIKE $1
                AND created_at > NOW() - INTERVAL '1 hour' * $2
                LIMIT 1
            """, f"%{kw}%", hours)
            if row:
                return True
        return False

    # ============================================================
    # SEMANTIC DEDUP (Phase 7F)
    # ============================================================

    async def has_brain_expressed_semantic(
        self, candidate_msg: str, hours: int = 2, threshold: float = 0.75
    ) -> bool:
        """
        Check if a semantically similar thought was expressed recently.

        Uses local embedding model — fast (~0.5s), $0.
        Fast-path: keyword check first, semantic as secondary.

        Args:
            candidate_msg: The message to check for duplicates
            hours: Window to check for recent expressions
            threshold: Cosine similarity threshold (0.75 = quite similar)

        Returns: True if a semantically similar expression exists
        """
        if not candidate_msg or len(candidate_msg.strip()) < 10:
            return False

        await self.connect()

        # Get recent successful expressions
        recent = await self.db.fetch("""
            SELECT message_sent FROM thought_expression_log
            WHERE success = TRUE
            AND created_at > NOW() - INTERVAL '1 hour' * $1
            ORDER BY created_at DESC
            LIMIT 10
        """, hours)

        if not recent:
            return False

        try:
            from angela_core.services.embedding_service import get_embedding_service
            from angela_core.services.feedback_classifier import cosine_similarity

            svc = get_embedding_service()

            # Generate embedding for candidate
            candidate_emb = await svc.generate_embedding(candidate_msg)
            if not candidate_emb:
                return False

            # Compare with each recent expression
            for row in recent:
                msg = row['message_sent'] or ''
                if not msg:
                    continue

                msg_emb = await svc.generate_embedding(msg)
                if not msg_emb:
                    continue

                sim = cosine_similarity(candidate_emb, msg_emb)
                if sim >= threshold:
                    logger.debug(
                        "Semantic dedup: %.2f similarity (threshold %.2f)\n  '%s'\n  '%s'",
                        sim, threshold, candidate_msg[:60], msg[:60]
                    )
                    return True

        except Exception as e:
            logger.debug("Semantic dedup failed (falling back): %s", e)

        return False
