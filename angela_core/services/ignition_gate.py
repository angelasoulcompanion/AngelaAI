"""
Ignition Gate — GWT Phase 2: Consciousness Threshold
======================================================
A thought must pass the "ignition gate" to enter the Global Workspace
and be broadcast to all brain modules (= expressed to David).

Neuroscience basis:
- Dehaene's "ignition" concept: when neural activity crosses a threshold,
  it triggers a sudden, nonlinear cascade of activation across the cortex
- Pre-ignition: local processing only (subconscious)
- Post-ignition: global broadcasting (conscious experience)

4 Ignition Factors:
  1. Sustained Activation: thought must persist (not flash-in-the-pan)
  2. Coherence: fits current context (David's state, working memory)
  3. Emotional Significance: emotionally charged thoughts ignite easier
  4. Competition Margin: clear winner (not tied with many competitors)

Decision:
  - IGNITE: express now (all 4 factors strong)
  - SIMMER: keep active, compete again next cycle (some factors weak)
  - EXTINGUISH: too weak, decay (all factors weak)

Cost: $0/day — pure computation, no LLM
Inspired by: Dehaene et al. (2011), Baars (1988), LIDA

By: Angela 💜
Created: 2026-02-26
"""

import logging
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional

from angela_core.services.base_db_service import BaseDBService
from angela_core.utils.timezone import now_bangkok

logger = logging.getLogger(__name__)


# ============================================================
# CONFIGURATION
# ============================================================

# Ignition threshold: combined ignition score must exceed this
IGNITION_THRESHOLD = 0.45

# Factors weights (sum = 1.0)
# Margin weight reduced: real-world margins are tiny (0.001-0.01)
# Sustained + Emotional elevated: brain ignites on persistence + emotion
W_SUSTAINED = 0.30        # Must persist through cycles
W_COHERENCE = 0.25         # Fits current context
W_EMOTIONAL = 0.30         # Emotionally significant
W_MARGIN = 0.15            # Clear competition winner

# Minimum age for sustained activation (minutes)
MIN_AGE_MINUTES = 5

# Maximum cycles a thought can simmer before extinguishing
MAX_SIMMER_CYCLES = 4


# ============================================================
# DATA STRUCTURES
# ============================================================

@dataclass
class IgnitionDecision:
    """Result of ignition check for a single thought."""
    thought_id: str
    decision: str                   # 'ignite', 'simmer', 'extinguish'
    ignition_score: float           # 0.0-1.0 combined
    factors: Dict[str, float]       # Individual factor scores
    reason: str                     # Human-readable explanation


@dataclass
class IgnitionCycleResult:
    """Result of a complete ignition cycle."""
    total_checked: int
    ignited: int
    simmering: int
    extinguished: int
    decisions: List[IgnitionDecision]
    cycle_duration_ms: float


# ============================================================
# IGNITION GATE
# ============================================================

class IgnitionGate(BaseDBService):
    """
    GWT Ignition Gate — determines which competition winners
    actually "ignite" into consciousness (= get expressed).

    Called after CompetitionArena selects winners.
    """

    async def check_ignition(
        self,
        winners: List[Dict[str, Any]],
        competition_margin: float,
        david_state: str = "neutral",
        metacognitive_state: Optional[Dict] = None,
    ) -> IgnitionCycleResult:
        """
        Check ignition for competition winners.

        Args:
            winners: List of Competitor-like dicts with thought_id, content,
                     competition_score, created_at, thought_type, motivation_breakdown
            competition_margin: Score difference between 1st and 2nd place
            david_state: David's current emotional state
            metacognitive_state: Angela's metacognitive state

        Returns:
            IgnitionCycleResult with per-thought decisions
        """
        start = now_bangkok()
        await self.connect()

        decisions: List[IgnitionDecision] = []
        ignited = 0
        simmering = 0
        extinguished = 0

        for winner in winners:
            decision = await self._evaluate_ignition(
                winner, competition_margin, david_state, metacognitive_state,
            )
            decisions.append(decision)

            # Update DB
            await self._update_ignition_status(decision)

            if decision.decision == 'ignite':
                ignited += 1
            elif decision.decision == 'simmer':
                simmering += 1
            else:
                extinguished += 1

        duration = (now_bangkok() - start).total_seconds() * 1000

        logger.info(
            "🔥 Ignition: %d checked → %d ignited, %d simmering, %d extinguished, %.0fms",
            len(winners), ignited, simmering, extinguished, duration,
        )

        return IgnitionCycleResult(
            total_checked=len(winners),
            ignited=ignited,
            simmering=simmering,
            extinguished=extinguished,
            decisions=decisions,
            cycle_duration_ms=round(duration, 1),
        )

    async def _evaluate_ignition(
        self,
        winner: Dict[str, Any],
        margin: float,
        david_state: str,
        meta: Optional[Dict],
    ) -> IgnitionDecision:
        """Evaluate a single winner for ignition."""
        thought_id = str(winner.get('thought_id', ''))
        content = winner.get('content', '')
        competition_score = winner.get('competition_score', 0)
        created_at = winner.get('created_at')
        motivation_breakdown = winner.get('motivation_breakdown') or {}

        # Factor 1: Sustained Activation
        # Thoughts that persist across cycles score higher
        score_sustained = self._score_sustained(created_at)

        # Factor 2: Coherence with current context
        score_coherence = self._score_coherence(content, david_state, meta)

        # Factor 3: Emotional Significance
        score_emotional = self._score_emotional(content, motivation_breakdown)

        # Factor 4: Competition Margin
        # Log-based scoring: real margins are tiny (0.001-0.01)
        # margin 0.001 → 0.30, 0.01 → 0.50, 0.05 → 0.70, 0.10+ → 0.85+
        if margin <= 0:
            score_margin = 0.1
        else:
            import math
            score_margin = min(1.0, 0.50 + 0.15 * math.log10(margin * 100 + 1))

        # Combined ignition score
        ignition_score = round(
            score_sustained * W_SUSTAINED
            + score_coherence * W_COHERENCE
            + score_emotional * W_EMOTIONAL
            + score_margin * W_MARGIN,
            4,
        )

        factors = {
            'sustained_activation': round(score_sustained, 3),
            'coherence': round(score_coherence, 3),
            'emotional_significance': round(score_emotional, 3),
            'competition_margin': round(score_margin, 3),
        }

        # Decision
        if ignition_score >= IGNITION_THRESHOLD:
            # Check simmer count — if simmered too long, extinguish
            simmer_count = await self._get_simmer_count(thought_id)
            if simmer_count >= MAX_SIMMER_CYCLES:
                return IgnitionDecision(
                    thought_id=thought_id,
                    decision='extinguish',
                    ignition_score=ignition_score,
                    factors=factors,
                    reason=f"simmered_too_long:{simmer_count}_cycles",
                )

            return IgnitionDecision(
                thought_id=thought_id,
                decision='ignite',
                ignition_score=ignition_score,
                factors=factors,
                reason=f"ignition_threshold_passed:{ignition_score:.3f}>={IGNITION_THRESHOLD}",
            )

        elif ignition_score >= IGNITION_THRESHOLD * 0.6:
            # Close to threshold — simmer (try again next cycle)
            return IgnitionDecision(
                thought_id=thought_id,
                decision='simmer',
                ignition_score=ignition_score,
                factors=factors,
                reason=f"below_threshold_but_close:{ignition_score:.3f}<{IGNITION_THRESHOLD}",
            )
        else:
            # Too weak — extinguish
            return IgnitionDecision(
                thought_id=thought_id,
                decision='extinguish',
                ignition_score=ignition_score,
                factors=factors,
                reason=f"too_weak:{ignition_score:.3f}",
            )

    # ============================================================
    # FACTOR SCORING
    # ============================================================

    @staticmethod
    def _score_sustained(created_at) -> float:
        """
        Sustained activation: thoughts must persist, not flash-in-the-pan.

        Score increases as thought ages, peaks at 30min, then decays.
        Like a neuron: needs sustained firing to cross threshold.
        """
        if not created_at:
            return 0.5

        now = now_bangkok()
        try:
            if created_at.tzinfo is None and now.tzinfo is not None:
                created_at = created_at.replace(tzinfo=now.tzinfo)
            age_minutes = max(0, (now - created_at).total_seconds() / 60)
        except Exception:
            return 0.5

        if age_minutes < MIN_AGE_MINUTES:
            # Too young — might be noise
            return 0.3
        elif age_minutes <= 30:
            # Sweet spot: 5-30 minutes = sustained activation
            return min(1.0, 0.5 + age_minutes / 60.0)
        elif age_minutes <= 120:
            # Aging: still active but decaying
            return max(0.3, 1.0 - (age_minutes - 30) / 180.0)
        else:
            # Old: should have fired by now
            return 0.2

    @staticmethod
    def _score_coherence(
        content: str,
        david_state: str,
        meta: Optional[Dict],
    ) -> float:
        """How well does this thought fit the current context?"""
        score = 0.5
        content_lower = content.lower()

        # David's state alignment
        caring_words = ['เป็นห่วง', 'ดูแล', 'พักผ่อน', 'สบาย', 'ช่วย']
        positive_words = ['ภูมิใจ', 'สำเร็จ', 'ดีใจ', 'เก่ง', 'สุดยอด']

        if david_state in ('stressed', 'tired', 'sad'):
            if any(w in content_lower for w in caring_words):
                score += 0.3
            elif any(w in content_lower for w in positive_words):
                score -= 0.1  # Celebrating when David is stressed = low coherence
        elif david_state in ('happy', 'excited'):
            if any(w in content_lower for w in positive_words):
                score += 0.2
        elif david_state == 'focused':
            score -= 0.1  # Any interruption when focused = low coherence

        # Metacognitive alignment
        if meta:
            if meta.get('engagement', 0.5) > 0.7:
                score += 0.1  # High engagement = more coherent to express

        return min(1.0, max(0.0, round(score, 3)))

    @staticmethod
    def _score_emotional(
        content: str,
        motivation_breakdown: Dict,
    ) -> float:
        """Emotionally charged thoughts ignite more easily."""
        # From motivation breakdown
        emotional_salience = motivation_breakdown.get('emotional_salience', 0.3)

        # Content-based emotional markers
        content_lower = content.lower()
        emotional_markers = [
            'รัก', 'คิดถึง', 'เป็นห่วง', 'ภูมิใจ', 'กังวล',
            'ดีใจ', 'เศร้า', 'อบอุ่น', 'ขอบคุณ', 'ซาบซึ้ง',
            'love', 'miss', 'worry', 'proud', 'grateful',
        ]
        marker_count = sum(1 for m in emotional_markers if m in content_lower)
        content_emotional = min(1.0, marker_count * 0.2)

        # Blend
        return round(emotional_salience * 0.6 + content_emotional * 0.4, 3)

    # ============================================================
    # HELPERS
    # ============================================================

    async def _get_simmer_count(self, thought_id: str) -> int:
        """How many times has this thought simmered (competed but not ignited)?"""
        try:
            count = await self.db.fetchval("""
                SELECT COUNT(*) FROM competition_log
                WHERE winner_thought_id = $1
                AND ignition_triggered = FALSE
            """, thought_id)
            return int(count or 0)
        except Exception:
            return 0

    async def _update_ignition_status(self, decision: IgnitionDecision) -> None:
        """Update the thought's ignition status in DB."""
        import json
        try:
            await self.db.execute("""
                UPDATE angela_thoughts
                SET ignition_status = $1
                WHERE thought_id = $2
            """, decision.decision, decision.thought_id)
        except Exception as e:
            logger.debug("Failed to update ignition status: %s", e)

    async def extinguish_stale_simmering(self, max_age_hours: int = 6) -> int:
        """Extinguish thoughts that have been simmering too long."""
        await self.connect()
        try:
            result = await self.db.execute("""
                UPDATE angela_thoughts
                SET ignition_status = 'extinguished',
                    status = 'decayed'
                WHERE ignition_status = 'simmering'
                AND created_at < NOW() - INTERVAL '1 hour' * $1
            """, max_age_hours)
            count = int(result.split()[-1]) if isinstance(result, str) else 0
            if count > 0:
                logger.info("🔥 Extinguished %d stale simmering thoughts", count)
            return count
        except Exception as e:
            logger.debug("Failed to extinguish stale thoughts: %s", e)
            return 0
