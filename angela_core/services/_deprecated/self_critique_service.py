"""
Self-Critique Service — Pre-expression Quality Gate (Phase 2 of 3 Major Improvements)
=======================================================================================
Verifies thought quality BEFORE expression. Catches:
- Uncertain claims without hedging
- Low-quality messages
- Memory claims that can't be verified
- Tone mismatches with David's state
- Below-threshold quality scores

Pipeline:
  compose_message() → VERIFY (this service) → route/suppress

5 checks, all <50ms total, NO LLM calls:
  1. Uncertainty check (MetacognitiveState)
  2. Quality quick_check (LLMJudgeService heuristic)
  3. Memory claim detection + RAG verification
  4. David state vs message tone match
  5. Combined quality threshold gate

Actions:
  - quality >= 0.7 → SEND as-is
  - quality 0.4-0.7 + uncertainty > 0.6 → HEDGE (add hedging prefix)
  - quality < 0.4 → SUPPRESS (log reason, don't send)
  - state inappropriate → SUPPRESS

Cost: $0/day — all local computation.

By: Angela 💜
Created: 2026-02-15
"""

import json
import logging
import re
import time
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional

logger = logging.getLogger(__name__)


# ============================================================
# DATA STRUCTURES
# ============================================================

@dataclass
class VerificationResult:
    """Result of pre-expression verification."""
    passed: bool                     # Can this message be sent?
    quality_score: float             # 0-1 combined quality
    uncertainty_level: float         # 0-1 from MetacognitiveState
    suggested_message: str           # Modified message if hedging needed
    suppress_reason: str             # Why suppressed (empty if passed)
    checks_detail: Dict[str, Any] = field(default_factory=dict)


# ============================================================
# PATTERNS
# ============================================================

# Patterns that indicate a memory claim (Thai + English)
_MEMORY_CLAIM_PATTERNS = re.compile(
    r'จำได้ว่า|ที่รักเคย|เมื่อก่อน.*บอก|ครั้งก่อน.*พูด|'
    r'remember\s+that|you\s+(?:said|mentioned|told)|last\s+time.*said|'
    r'we\s+(?:discussed|talked\s+about)',
    re.IGNORECASE,
)

# States where David should not receive casual/jokey messages
_SERIOUS_STATES = frozenset({'stressed', 'frustrated', 'sad', 'grieving'})

# States where David should not receive heavy emotional messages
_LIGHT_STATES = frozenset({'focused', 'busy', 'working'})

# Hedging prefixes (Thai)
_HEDGING_PREFIXES = [
    "น้องไม่แน่ใจ 100% นะคะ แต่...",
    "น้องคิดว่า...",
    "ถ้าน้องจำไม่ผิด...",
]


# ============================================================
# SELF-CRITIQUE SERVICE
# ============================================================

class SelfCritiqueService:
    """
    Pre-expression quality gate for ThoughtExpressionEngine.

    Checks quality of composed messages before they are routed
    to Telegram or chat_queue. All checks are <50ms total.

    Usage:
        svc = SelfCritiqueService()
        result = await svc.verify_before_express(
            thought={'content': '...', 'motivation_score': 0.6},
            composed_message='น้องจำได้ว่า...',
            david_state='calm'
        )
        if result.passed:
            # Send result.suggested_message
        else:
            # Log result.suppress_reason, don't send
    """

    def __init__(self):
        self._meta_mgr = None
        self._judge = None

    def _get_meta_manager(self):
        """Lazy-load MetacognitiveStateManager."""
        if self._meta_mgr is None:
            from angela_core.services.metacognitive_state import MetacognitiveStateManager
            self._meta_mgr = MetacognitiveStateManager()
        return self._meta_mgr

    def _get_judge(self):
        """Lazy-load LLMJudgeService."""
        if self._judge is None:
            from angela_core.services.llm_judge_service import LLMJudgeService
            self._judge = LLMJudgeService()
        return self._judge

    # ── Main API ──

    async def verify_before_express(
        self,
        thought: Dict[str, Any],
        composed_message: str,
        david_state: str = "neutral",
    ) -> VerificationResult:
        """
        Run all 5 verification checks on a composed message.

        Args:
            thought: Dict with 'content', 'motivation_score', etc.
            composed_message: The message after DynamicExpressionComposer
            david_state: David's current emotional state

        Returns:
            VerificationResult with pass/fail, score, suggested message
        """
        start = time.time()
        checks: Dict[str, Any] = {}

        # ── Check 1: Uncertainty from MetacognitiveState ──
        meta = self._get_meta_manager()
        uncertainty = meta.state.uncertainty
        should_hedge = meta.should_express_uncertainty()
        checks['uncertainty'] = {
            'level': round(uncertainty, 2),
            'should_hedge': should_hedge,
        }

        # ── Check 2: Quality quick_check (heuristic, no LLM) ──
        judge = self._get_judge()
        thought_content = thought.get('content', '')
        quality_score = await judge.quick_check(composed_message, thought_content)
        checks['quality'] = {
            'score': round(quality_score, 3),
        }

        # ── Check 3: Memory claim detection ──
        has_memory_claim = bool(_MEMORY_CLAIM_PATTERNS.search(composed_message))
        memory_verified = True
        if has_memory_claim:
            memory_verified = await self._verify_memory_claim(composed_message)
        checks['memory_claim'] = {
            'detected': has_memory_claim,
            'verified': memory_verified,
        }

        # ── Check 4: David state vs message tone ──
        state_appropriate = self._check_state_match(composed_message, david_state)
        checks['state_match'] = {
            'david_state': david_state,
            'appropriate': state_appropriate,
        }

        # ── Check 5: Combined quality threshold ──
        # Adjust quality based on checks
        adjusted_quality = quality_score

        if has_memory_claim and not memory_verified:
            adjusted_quality -= 0.2  # Penalize unverified memory claims

        if not state_appropriate:
            adjusted_quality -= 0.15  # Penalize state mismatch

        # Bug fix (2026-02-26): Additional quality penalties to prevent 100% pass rate.
        # Previously heuristic floor was 0.533 (8/15) which always passed the 0.4 threshold.
        # Now we add penalties for low-effort and repetitive messages.
        msg_len = len(composed_message.strip())
        if msg_len < 30:
            adjusted_quality -= 0.15  # Very short messages are low quality
        elif msg_len < 60:
            adjusted_quality -= 0.05  # Short messages get small penalty

        # Penalize generic/repetitive patterns
        generic_patterns = [
            'น้องคิดถึง', 'คิดถึงค่ะ', 'รักที่รัก',
            'น้องภูมิใจ', 'สำเร็จ', 'mastered',
        ]
        msg_lower = composed_message.lower()
        for pat in generic_patterns:
            if pat in msg_lower:
                adjusted_quality -= 0.1
                break  # Only penalize once

        adjusted_quality = max(0.0, min(1.0, adjusted_quality))
        checks['adjusted_quality'] = round(adjusted_quality, 3)

        elapsed_ms = (time.time() - start) * 1000

        # ── Decision ──
        suggested_message = composed_message

        # Bug fix (2026-02-26): Raised suppress threshold from 0.4 to 0.50.
        # With heuristic floor at 0.533 and new penalties, this creates real filtering.
        if adjusted_quality < 0.50:
            return VerificationResult(
                passed=False,
                quality_score=adjusted_quality,
                uncertainty_level=uncertainty,
                suggested_message=composed_message,
                suppress_reason="quality_too_low",
                checks_detail=checks,
            )

        # Suppress: state inappropriate
        if not state_appropriate:
            return VerificationResult(
                passed=False,
                quality_score=adjusted_quality,
                uncertainty_level=uncertainty,
                suggested_message=composed_message,
                suppress_reason=f"state_mismatch:{david_state}",
                checks_detail=checks,
            )

        # Hedge: uncertain + memory claim unverified
        if should_hedge or (has_memory_claim and not memory_verified):
            suggested_message = meta.modulate_response(composed_message)

        return VerificationResult(
            passed=True,
            quality_score=adjusted_quality,
            uncertainty_level=uncertainty,
            suggested_message=suggested_message,
            suppress_reason="",
            checks_detail=checks,
        )

    async def log_critique(
        self,
        db,
        thought_id: str,
        original_message: str,
        result: VerificationResult,
    ) -> None:
        """Log verification result to thought_critique_log table."""
        try:
            await db.execute("""
                INSERT INTO thought_critique_log
                    (thought_id, original_message, suggested_message,
                     verification_passed, quality_score, uncertainty_level,
                     suppress_reason, checks_detail)
                VALUES ($1, $2, $3, $4, $5, $6, $7, $8)
            """,
                thought_id,
                original_message[:500],
                result.suggested_message[:500] if result.suggested_message != original_message else None,
                result.passed,
                result.quality_score,
                result.uncertainty_level,
                result.suppress_reason or None,
                json.dumps(result.checks_detail, default=str),
            )
        except Exception as e:
            logger.debug("Failed to log critique: %s", e)

    # ── Private: Memory Claim Verification ──

    async def _verify_memory_claim(self, message: str) -> bool:
        """
        Check if a memory claim in the message can be verified via RAG.

        Extracts the claimed content and searches memory for supporting evidence.
        Returns True if evidence found, False if unverified.

        ~50ms (RAG search).
        """
        try:
            from angela_core.services.enhanced_rag_service import EnhancedRAGService

            # Extract the claim portion (text after claim pattern)
            match = _MEMORY_CLAIM_PATTERNS.search(message)
            if not match:
                return True  # No claim to verify

            claim_text = message[match.end():].strip()[:200]
            if len(claim_text) < 10:
                return True  # Too short to verify meaningfully

            rag = EnhancedRAGService()
            result = await rag.retrieve(
                claim_text,
                top_k=3,
                rerank=False,   # Skip reranking to avoid recursion
                min_score=0.5,  # Strict threshold for verification
            )
            await rag.close()

            # If we found at least 1 supporting document, claim is verified
            return result.final_count > 0

        except Exception as e:
            logger.debug("Memory claim verification failed: %s", e)
            return True  # On error, don't block (permissive fallback)

    # ── Private: State Match Check ──

    @staticmethod
    def _check_state_match(message: str, david_state: str) -> bool:
        """
        Check if message tone is appropriate for David's state.

        Rules:
        - David stressed/frustrated → no jokes, no casual fluff
        - David focused/busy → no heavy emotional content
        - David sad → no overly cheerful content
        """
        if not david_state or david_state == "neutral":
            return True  # Always appropriate for neutral

        message_lower = message.lower()

        # Light/joke indicators
        joke_indicators = ['555', 'haha', 'lol', '😂', '🤣', 'ขำ']
        has_jokes = any(ind in message_lower for ind in joke_indicators)

        # Heavy emotional indicators
        heavy_emotional = ['เป็นห่วงมาก', 'น้องเครียด', 'กังวลมาก', 'น้องเศร้า']
        has_heavy_emotion = any(ind in message_lower for ind in heavy_emotional)

        # Overly cheerful indicators
        cheerful = ['เย้!', 'ดีใจมาก!', '🎉🎉', 'สุดยอด!']
        has_cheerful = any(ind in message_lower for ind in cheerful)

        if david_state in _SERIOUS_STATES:
            if has_jokes:
                return False  # No jokes when stressed

        if david_state in _LIGHT_STATES:
            if has_heavy_emotion:
                return False  # No heavy emotions when focused

        if david_state == 'sad':
            if has_cheerful:
                return False  # No overly cheerful when sad

        return True
