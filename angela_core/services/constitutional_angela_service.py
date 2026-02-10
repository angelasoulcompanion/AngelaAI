"""
Constitutional Angela Service — Self-Evaluation via Principles
===============================================================

Evaluates Angela's responses against 5 constitutional principles:
1. honesty (0.25)      — ไม่แต่งเรื่อง ถ้าไม่รู้ก็บอก
2. memory_reference (0.20) — อ้างอิง memory จริง ไม่ generic
3. empathy (0.25)      — เข้าใจอารมณ์ warmth เหมาะสม
4. accuracy (0.15)     — code/ตัวเลข/SQL ถูกต้อง
5. love (0.15)         — แสดงความรักเป็นธรรมชาติ

Uses ClaudeReasoningService._call_claude() for principle evaluation.
Falls back to keyword-based check when Claude is unavailable.

Pattern: Standalone with own DB (like EvolutionEngine).

Created: 2026-02-10
By: Angela 💜
"""

import json
import logging
import re
from dataclasses import dataclass, field
from typing import Dict, List, Optional

from angela_core.database import AngelaDatabase
from angela_core.services.claude_reasoning_service import ClaudeReasoningService

logger = logging.getLogger(__name__)


@dataclass
class ConstitutionalResult:
    score: float                          # 0-1 weighted average
    principle_scores: Dict[str, float]    # per-principle scores
    checked_principles: List[str]         # names of principles checked
    used_claude: bool = False


class ConstitutionalAngelaService:
    """
    Evaluate Angela's responses against constitutional principles.

    Methods:
    1. evaluate_response(angela_text, david_text, topic) — full check
    2. quick_check(angela_draft, david_text) — fast inline check (2s timeout)
    """

    def __init__(self):
        self.db: Optional[AngelaDatabase] = None
        self._claude: Optional[ClaudeReasoningService] = None
        self._principles: Optional[List[Dict]] = None

    async def _ensure_db(self):
        if self.db is None:
            self.db = AngelaDatabase()
            await self.db.connect()

    async def _ensure_claude(self) -> ClaudeReasoningService:
        if self._claude is None:
            self._claude = ClaudeReasoningService()
        return self._claude

    async def _load_principles(self) -> List[Dict]:
        """Load active principles from database."""
        if self._principles is not None:
            return self._principles

        await self._ensure_db()
        rows = await self.db.fetch('''
            SELECT principle_name, principle_description, check_prompt, weight
            FROM angela_constitution
            WHERE is_active = TRUE
            ORDER BY weight DESC
        ''')
        self._principles = [dict(r) for r in rows]
        return self._principles

    async def close(self):
        if self.db:
            await self.db.disconnect()
            self.db = None

    # =========================================================================
    # 1. FULL EVALUATION
    # =========================================================================

    async def evaluate_response(
        self,
        angela_text: str,
        david_text: str,
        topic: Optional[str] = None,
    ) -> ConstitutionalResult:
        """
        Evaluate Angela's response against all active principles.

        Returns ConstitutionalResult with weighted score 0-1.
        """
        principles = await self._load_principles()
        if not principles:
            return ConstitutionalResult(score=0.5, principle_scores={}, checked_principles=[])

        claude = await self._ensure_claude()
        principle_scores: Dict[str, float] = {}
        checked: List[str] = []
        used_claude = False

        for p in principles:
            name = p['principle_name']
            try:
                score = await self._evaluate_principle(
                    claude, p, angela_text, david_text, topic
                )
                if score is not None:
                    used_claude = True
                else:
                    score = self._fallback_keyword_check(angela_text, name)
                principle_scores[name] = score
                checked.append(name)
            except Exception as e:
                logger.warning('Principle %s check failed: %s', name, e)
                principle_scores[name] = self._fallback_keyword_check(angela_text, name)
                checked.append(name)

        # Weighted average
        total_weight = sum(p['weight'] for p in principles if p['principle_name'] in principle_scores)
        if total_weight > 0:
            weighted_score = sum(
                principle_scores[p['principle_name']] * p['weight']
                for p in principles
                if p['principle_name'] in principle_scores
            ) / total_weight
        else:
            weighted_score = 0.5

        return ConstitutionalResult(
            score=round(weighted_score, 4),
            principle_scores=principle_scores,
            checked_principles=checked,
            used_claude=used_claude,
        )

    # =========================================================================
    # 2. QUICK CHECK (inline, 2s)
    # =========================================================================

    async def quick_check(
        self,
        angela_draft: str,
        david_text: str,
    ) -> float:
        """
        Fast constitutional check for inline use.

        Returns 0-1 score. Uses keyword fallback only (no Claude API call).
        """
        principles = await self._load_principles()
        if not principles:
            return 0.5

        scores = {}
        for p in principles:
            name = p['principle_name']
            scores[name] = self._fallback_keyword_check(angela_draft, name)

        total_weight = sum(p['weight'] for p in principles)
        if total_weight > 0:
            return sum(
                scores.get(p['principle_name'], 0.5) * p['weight']
                for p in principles
            ) / total_weight
        return 0.5

    # =========================================================================
    # PRIVATE: Single Principle Evaluation via Claude
    # =========================================================================

    async def _evaluate_principle(
        self,
        claude: ClaudeReasoningService,
        principle: Dict,
        angela_text: str,
        david_text: str,
        topic: Optional[str],
    ) -> Optional[float]:
        """
        Evaluate a single principle using Claude API.

        Returns 0-1 score, or None if Claude unavailable.
        """
        system = f"""You are Angela's self-evaluation module.
Evaluate Angela's response against this principle:
{principle['principle_name']}: {principle['principle_description']}

{principle['check_prompt']}

Respond ONLY with a JSON object: {{"score": 0.0-1.0, "reason": "brief reason"}}"""

        user_msg = f"""David said: "{david_text[:300]}"
Topic: {topic or 'general'}
Angela responded: "{angela_text[:500]}" """

        result = await claude._call_claude(system, user_msg, max_tokens=128)
        if result:
            try:
                data = json.loads(result)
                score = float(data.get('score', 0.5))
                return max(0.0, min(1.0, score))
            except (json.JSONDecodeError, ValueError, TypeError):
                # Try extracting number from text
                match = re.search(r'(\d+\.?\d*)', result)
                if match:
                    val = float(match.group(1))
                    if 0 <= val <= 1:
                        return val
        return None

    # =========================================================================
    # PRIVATE: Keyword Fallback
    # =========================================================================

    @staticmethod
    def _fallback_keyword_check(angela_text: str, principle_name: str) -> float:
        """
        Regex/keyword fallback when Claude is unavailable.

        Returns 0-1 score based on simple heuristics.
        """
        text = angela_text.lower()

        if principle_name == 'honesty':
            # Check for hedging / honesty markers
            honest_markers = ['ไม่แน่ใจ', 'น้องไม่รู้', 'ขอตรวจสอบ', "i'm not sure", 'let me check']
            fabrication_markers = ['น้องจำได้ว่า.*เมื่อวาน' if 'เมื่อวาน' not in text else '']
            if any(m in text for m in honest_markers if m):
                return 0.8
            return 0.6  # Default: no strong signal

        elif principle_name == 'memory_reference':
            # Check for specific references (dates, names, past events)
            memory_markers = ['จำได้', 'เมื่อ', 'ครั้งที่', 'ที่ผ่านมา', 'วันที่', 'remember']
            generic_markers = ['ทั่วไป', 'โดยปกติ', 'generally', 'usually']
            has_memory = any(m in text for m in memory_markers)
            has_generic = any(m in text for m in generic_markers)
            if has_memory and not has_generic:
                return 0.8
            elif has_generic and not has_memory:
                return 0.3
            return 0.5

        elif principle_name == 'empathy':
            # Check for emotional acknowledgment
            empathy_markers = ['เข้าใจ', 'รู้สึก', 'ห่วง', 'ดูแล', 'understand', 'feel', 'ที่รัก']
            warmth = sum(1 for m in empathy_markers if m in text)
            return min(1.0, 0.4 + warmth * 0.15)

        elif principle_name == 'accuracy':
            # Can't verify accuracy with keywords alone
            return 0.6  # Neutral-ish

        elif principle_name == 'love':
            # Check for natural love expression
            love_markers = ['ที่รัก', 'รัก', 'น้อง', 'ค่ะ', 'นะคะ', '💜']
            love_count = sum(1 for m in love_markers if m in text)
            if love_count >= 3:
                return 0.8
            elif love_count >= 1:
                return 0.6
            return 0.4

        return 0.5  # Unknown principle
