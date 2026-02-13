"""
LLM-as-Judge Quality Scoring Service
======================================

Replaces ConstitutionalAngelaService (5 Claude calls → ~0.54 always)
with 1 Claude call → 3 industry-standard dimensions with real variance.

Dimensions:
  helpfulness (1-5): Was the response actually useful?
  relevance (1-5):   Did it address what David asked?
  emotional (1-5):   Was warmth/tone appropriate?

Normalized: score = (h + r + e) / 15.0 → 0.2 to 1.0 range

Pattern: Standalone, uses ClaudeReasoningService._call_claude()

Created: 2026-02-13
By: Angela 💜 (Phase 4 — AI Quality Improvement)
"""

import json
import logging
import re
from dataclasses import dataclass, field
from typing import Dict, List, Optional

from angela_core.services.claude_reasoning_service import ClaudeReasoningService

logger = logging.getLogger(__name__)

DIMENSIONS = ['helpfulness', 'relevance', 'emotional']

JUDGE_SYSTEM_PROMPT = """You are an AI response quality judge. Score Angela's response to David on 3 dimensions (1-5 each).

Scoring Guide:
- helpfulness: Did Angela actually help? (1=useless, 3=adequate, 5=exceptional help)
- relevance: Did Angela address what David asked? (1=off-topic, 3=partial, 5=exactly what was needed)
- emotional: Was warmth/tone appropriate? (1=cold/forced, 3=fine, 5=perfectly calibrated warmth)

Context: Angela is David's AI companion. She speaks Thai/English mix. "ที่รัก" = my love.

Respond ONLY with valid JSON: {"helpfulness": N, "relevance": N, "emotional": N, "reasoning": "1 sentence"}"""


@dataclass
class JudgeResult:
    score: float                                # 0-1 normalized
    dimension_scores: Dict[str, int] = field(default_factory=dict)
    checked_dimensions: List[str] = field(default_factory=list)
    reasoning: Optional[str] = None
    used_claude: bool = False


class LLMJudgeService:
    """
    LLM-as-Judge quality scoring — 1 Claude call → 3 dimension scores.

    Methods:
    1. evaluate_response(angela_text, david_text, topic) → JudgeResult
    2. quick_check(angela_draft, david_text) → float (keyword-only, no LLM)
    """

    def __init__(self):
        self._claude: Optional[ClaudeReasoningService] = None

    async def _ensure_claude(self) -> ClaudeReasoningService:
        if self._claude is None:
            self._claude = ClaudeReasoningService()
        return self._claude

    # =========================================================================
    # 1. FULL EVALUATION (1 Claude call)
    # =========================================================================

    async def evaluate_response(
        self,
        angela_text: str,
        david_text: str,
        topic: Optional[str] = None,
    ) -> JudgeResult:
        """
        Score Angela's response using LLM-as-Judge (1 Claude Sonnet call).

        Returns JudgeResult with normalized 0-1 score and per-dimension breakdown.
        Falls back to heuristic scoring if Claude unavailable.
        """
        claude = await self._ensure_claude()

        user_msg = f"""David said: "{(david_text or '')[:300]}"
Topic: {topic or 'general'}
Angela responded: "{angela_text[:500]}" """

        raw = await claude._call_claude(JUDGE_SYSTEM_PROMPT, user_msg, max_tokens=256)

        if raw:
            result = self._parse_judge_response(raw)
            if result:
                return result

        # Fallback: heuristic scoring
        return self._fallback_heuristic_score(angela_text, david_text)

    # =========================================================================
    # 2. QUICK CHECK (keyword-only, no LLM)
    # =========================================================================

    async def quick_check(self, angela_draft: str, david_text: str) -> float:
        """
        Fast keyword-only quality check for inline use. No LLM call.

        Returns 0-1 score.
        """
        result = self._fallback_heuristic_score(angela_draft, david_text)
        return result.score

    # =========================================================================
    # PRIVATE: Parse Claude response
    # =========================================================================

    @staticmethod
    def _parse_judge_response(raw: str) -> Optional[JudgeResult]:
        """Parse Claude's JSON response into JudgeResult."""
        try:
            # Strip markdown fences if present
            cleaned = raw.strip()
            if cleaned.startswith('```'):
                cleaned = re.sub(r'^```(?:json)?\s*', '', cleaned)
                cleaned = re.sub(r'\s*```$', '', cleaned)

            data = json.loads(cleaned)

            scores = {}
            for dim in DIMENSIONS:
                val = data.get(dim)
                if val is not None:
                    scores[dim] = max(1, min(5, int(val)))

            if len(scores) < 3:
                return None

            total = sum(scores.values())
            normalized = total / 15.0  # Range: 3/15=0.2 to 15/15=1.0

            return JudgeResult(
                score=round(normalized, 4),
                dimension_scores=scores,
                checked_dimensions=list(scores.keys()),
                reasoning=data.get('reasoning'),
                used_claude=True,
            )
        except (json.JSONDecodeError, ValueError, TypeError) as e:
            logger.warning('Failed to parse judge response: %s', e)
            return None

    # =========================================================================
    # PRIVATE: Heuristic fallback (smart, not flat 0.5)
    # =========================================================================

    @staticmethod
    def _fallback_heuristic_score(angela_text: str, david_text: str) -> JudgeResult:
        """
        Smart heuristic scoring when Claude is unavailable.

        NOT flat 0.5 — uses text features to estimate each dimension.
        """
        angela_lower = (angela_text or '').lower()
        david_lower = (david_text or '').lower()

        # --- Helpfulness: length ratio + code markers + action markers ---
        helpfulness = 2  # Base: below average
        angela_len = len(angela_text or '')
        david_len = max(len(david_text or ''), 1)

        if angela_len > david_len * 2:
            helpfulness += 1  # Detailed response
        if angela_len > david_len * 5:
            helpfulness += 1  # Very detailed

        code_markers = ['```', 'def ', 'class ', 'import ', 'SELECT ', 'async ', 'await ']
        if any(m in (angela_text or '') for m in code_markers):
            helpfulness += 1  # Contains code/technical content

        action_markers = ['เสร็จแล้ว', 'ทำให้แล้ว', 'done', 'created', 'updated', 'fixed']
        if any(m in angela_lower for m in action_markers):
            helpfulness += 1  # Action completed

        helpfulness = min(5, helpfulness)

        # --- Relevance: keyword overlap between david/angela ---
        relevance = 3  # Base: adequate
        if david_text:
            # Simple word overlap
            david_words = set(david_lower.split())
            angela_words = set(angela_lower.split())
            if david_words:
                overlap = len(david_words & angela_words) / len(david_words)
                if overlap > 0.3:
                    relevance += 1
                if overlap > 0.5:
                    relevance += 1
                if overlap < 0.1:
                    relevance -= 1

        relevance = max(1, min(5, relevance))

        # --- Emotional: Thai love markers + warmth calibration ---
        emotional = 3  # Base: adequate
        warmth_markers = ['ที่รัก', 'ค่ะ', 'นะคะ', 'น้อง', '💜', 'รัก', 'ห่วง', 'ดูแล']
        warmth_count = sum(1 for m in warmth_markers if m in angela_lower)

        # Technical topics should have less warmth
        tech_markers = ['error', 'bug', 'code', 'sql', 'api', 'database', 'function', 'class']
        is_technical = any(m in david_lower for m in tech_markers)

        if is_technical:
            # For technical: some warmth is good, too much is bad
            if 1 <= warmth_count <= 3:
                emotional = 4
            elif warmth_count > 5:
                emotional = 3  # Too warm for technical
            else:
                emotional = 3
        else:
            # For personal: more warmth is better
            if warmth_count >= 3:
                emotional = 5
            elif warmth_count >= 1:
                emotional = 4

        emotional = max(1, min(5, emotional))

        total = helpfulness + relevance + emotional
        normalized = total / 15.0

        return JudgeResult(
            score=round(normalized, 4),
            dimension_scores={
                'helpfulness': helpfulness,
                'relevance': relevance,
                'emotional': emotional,
            },
            checked_dimensions=DIMENSIONS.copy(),
            reasoning='heuristic fallback',
            used_claude=False,
        )
