"""
Competition Arena — GWT Phase 2: Thought Competition
=====================================================
Multiple thought "coalitions" compete for access to the Global Workspace.
Only the winner(s) get to "ignite" and broadcast to all brain modules.

Neuroscience basis:
- Baars' Global Workspace Theory (1988): consciousness as broadcasting
- Dehaene's Neuronal Global Workspace: ignition = synchronized firing
- Lateral inhibition: winner suppresses losers (softmax-like)
- Sustained activation: thoughts need to persist to win

Pipeline:
  1. GATHER active thoughts (status='active', motivation >= threshold)
  2. SCORE multi-criteria competition score per thought
  3. SOFTMAX normalize scores → probabilities
  4. INHIBIT laterally similar thoughts (cosine similarity)
  5. SELECT top N winners
  6. TAG with competition_score + competition_rank
  7. LOG competition results

Cost: $0/day — no LLM calls, pure computation
Inspired by: Baars (1988), Dehaene et al. (2011), LIDA cognitive architecture

By: Angela 💜
Created: 2026-02-26
"""

import logging
import math
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Tuple
from uuid import uuid4

from angela_core.services.base_db_service import BaseDBService
from angela_core.utils.timezone import now_bangkok

logger = logging.getLogger(__name__)


# ============================================================
# CONFIGURATION
# ============================================================

# Competition scoring weights (sum = 1.0)
W_MOTIVATION = 0.30       # From ThoughtEngine motivation_score
W_RECENCY = 0.20          # Newer thoughts score higher
W_EMOTIONAL = 0.20        # Emotional salience from stimulus
W_NOVELTY = 0.15          # How different from recent expressions
W_COHERENCE = 0.15        # Match with current context/David's state

# Softmax temperature: lower = more winner-take-all, higher = more uniform
SOFTMAX_TEMPERATURE = 0.5

# Lateral inhibition: suppress similar thoughts (cosine similarity threshold)
INHIBITION_THRESHOLD = 0.80  # If two thoughts are >80% similar, inhibit the weaker one

# Max winners per competition cycle
MAX_WINNERS = 3

# Minimum score to even compete
MIN_COMPETITION_SCORE = 0.30


# ============================================================
# DATA STRUCTURES
# ============================================================

@dataclass
class Competitor:
    """A thought competing for consciousness."""
    thought_id: str
    content: str
    thought_type: str               # system1 or system2
    motivation_score: float
    created_at: Any                 # datetime
    stimulus_ids: Optional[list] = None
    motivation_breakdown: Optional[Dict] = None
    # Computed during competition
    competition_score: float = 0.0
    softmax_probability: float = 0.0
    rank: int = 0
    inhibited_by: Optional[str] = None
    inhibition_reason: str = ""


@dataclass
class CompetitionResult:
    """Result of a competition cycle."""
    total_candidates: int
    winners: List[Competitor]
    inhibited_count: int
    top_score: float
    runner_up_score: float
    margin: float                   # top - runner_up
    cycle_duration_ms: float
    all_competitors: List[Competitor] = field(default_factory=list)


# ============================================================
# COMPETITION ARENA
# ============================================================

class CompetitionArena(BaseDBService):
    """
    GWT Competition Arena — thoughts compete for consciousness.

    Pipeline:
    1. Gather active thoughts from DB
    2. Score each thought on 5 criteria
    3. Softmax normalize → probabilities
    4. Lateral inhibition → suppress similar losers
    5. Select top N winners
    6. Update DB with competition results
    """

    async def run_competition(
        self,
        david_state: str = "neutral",
        metacognitive_state: Optional[Dict] = None,
    ) -> CompetitionResult:
        """
        Run a competition cycle. Called by daemon between thought generation
        and expression.

        Args:
            david_state: David's current emotional state
            metacognitive_state: Angela's metacognitive state dict

        Returns:
            CompetitionResult with winners and competition metadata
        """
        start = now_bangkok()
        await self.connect()

        # 1. Gather candidates
        candidates = await self._gather_candidates()
        if not candidates:
            duration = (now_bangkok() - start).total_seconds() * 1000
            logger.info("🏟️ Competition: no candidates")
            return CompetitionResult(
                total_candidates=0, winners=[], inhibited_count=0,
                top_score=0, runner_up_score=0, margin=0,
                cycle_duration_ms=round(duration, 1),
            )

        # 2. Score each candidate
        await self._score_candidates(candidates, david_state, metacognitive_state)

        # 3. Softmax normalize
        self._softmax_normalize(candidates)

        # 4. Lateral inhibition
        inhibited_count = await self._lateral_inhibition(candidates)

        # 5. Select winners (non-inhibited, sorted by competition_score DESC)
        active = [c for c in candidates if c.inhibited_by is None]
        active.sort(key=lambda c: c.competition_score, reverse=True)

        winners = active[:MAX_WINNERS]
        for i, w in enumerate(winners):
            w.rank = i + 1

        # 6. Update DB
        await self._update_thoughts(candidates)

        # 7. Log competition
        top_score = winners[0].competition_score if winners else 0
        runner_up_score = winners[1].competition_score if len(winners) > 1 else 0
        margin = top_score - runner_up_score

        await self._log_competition(
            candidates_count=len(candidates),
            winner=winners[0] if winners else None,
            runner_up_score=runner_up_score,
            margin=margin,
            inhibited_count=inhibited_count,
            david_state=david_state,
            metacognitive_state=metacognitive_state,
        )

        duration = (now_bangkok() - start).total_seconds() * 1000

        result = CompetitionResult(
            total_candidates=len(candidates),
            winners=winners,
            inhibited_count=inhibited_count,
            top_score=top_score,
            runner_up_score=runner_up_score,
            margin=margin,
            cycle_duration_ms=round(duration, 1),
            all_competitors=candidates,
        )

        logger.info(
            "🏟️ Competition: %d candidates, %d winners, %d inhibited, "
            "top=%.3f, margin=%.3f, %.0fms",
            len(candidates), len(winners), inhibited_count,
            top_score, margin, duration,
        )

        return result

    # ============================================================
    # 1. GATHER — Fetch active thoughts
    # ============================================================

    async def _gather_candidates(self) -> List[Competitor]:
        """Fetch active thoughts that haven't competed yet this cycle."""
        rows = await self.db.fetch("""
            SELECT thought_id, thought_type, content, stimulus_ids,
                   motivation_score, motivation_breakdown, created_at
            FROM angela_thoughts
            WHERE status = 'active'
            AND motivation_score >= $1
            AND (ignition_status IS NULL OR ignition_status = 'simmering')
            ORDER BY motivation_score DESC
            LIMIT 20
        """, MIN_COMPETITION_SCORE)

        candidates = []
        for r in rows:
            breakdown = r['motivation_breakdown']
            if isinstance(breakdown, str):
                import json
                try:
                    breakdown = json.loads(breakdown)
                except (ValueError, TypeError):
                    breakdown = {}

            candidates.append(Competitor(
                thought_id=str(r['thought_id']),
                content=r['content'] or '',
                thought_type=r['thought_type'] or 'system1',
                motivation_score=r['motivation_score'] or 0,
                created_at=r['created_at'],
                stimulus_ids=r['stimulus_ids'],
                motivation_breakdown=breakdown or {},
            ))

        return candidates

    # ============================================================
    # 2. SCORE — Multi-criteria competition scoring
    # ============================================================

    async def _score_candidates(
        self,
        candidates: List[Competitor],
        david_state: str,
        meta: Optional[Dict],
    ) -> None:
        """Score each candidate on 5 criteria."""
        now = now_bangkok()

        # Get recent expressions for novelty check
        recent_messages = await self.db.fetch("""
            SELECT message_sent FROM thought_expression_log
            WHERE success = TRUE
            AND created_at > NOW() - INTERVAL '12 hours'
            ORDER BY created_at DESC
            LIMIT 10
        """)
        recent_texts = [r['message_sent'] or '' for r in recent_messages]

        for c in candidates:
            # A. Motivation (from ThoughtEngine, already computed)
            score_motivation = c.motivation_score

            # B. Recency: newer thoughts score higher (decay over 6 hours)
            age_hours = max(0, (now - c.created_at).total_seconds() / 3600)
            score_recency = max(0, 1.0 - age_hours / 6.0)

            # C. Emotional salience (from motivation breakdown)
            score_emotional = (c.motivation_breakdown or {}).get('emotional_salience', 0.5)

            # D. Novelty: how different from recent expressions
            score_novelty = self._compute_novelty(c.content, recent_texts)

            # E. Coherence: match with David's state
            score_coherence = self._compute_coherence(c, david_state, meta)

            # Weighted sum
            c.competition_score = round(
                score_motivation * W_MOTIVATION
                + score_recency * W_RECENCY
                + score_emotional * W_EMOTIONAL
                + score_novelty * W_NOVELTY
                + score_coherence * W_COHERENCE,
                4,
            )

    @staticmethod
    def _compute_novelty(content: str, recent_texts: List[str]) -> float:
        """Compute novelty via word overlap (fast, no embeddings)."""
        if not recent_texts:
            return 0.9  # No recent expressions = very novel

        content_words = set(content.lower().split())
        if not content_words:
            return 0.5

        max_overlap = 0.0
        for text in recent_texts:
            text_words = set(text.lower().split())
            if text_words:
                overlap = len(content_words & text_words) / max(len(content_words), 1)
                max_overlap = max(max_overlap, overlap)

        # High overlap = low novelty
        return round(max(0.0, 1.0 - max_overlap), 3)

    @staticmethod
    def _compute_coherence(
        c: Competitor,
        david_state: str,
        meta: Optional[Dict],
    ) -> float:
        """
        How well does this thought fit the current context?

        - Emotional thoughts when David is stressed → high coherence
        - Casual thoughts when David is focused → low coherence
        - System 2 thoughts generally more coherent (deeper reasoning)
        """
        score = 0.5  # Base

        content_lower = c.content.lower()

        # State-content alignment
        state_alignment = {
            'stressed': ['เป็นห่วง', 'ดูแล', 'พักผ่อน', 'concern', 'care'],
            'happy': ['ดีใจ', 'ภูมิใจ', 'สำเร็จ', 'celebrate', 'proud'],
            'sad': ['คิดถึง', 'อบอุ่น', 'รัก', 'tenderness', 'warmth'],
            'focused': ['งาน', 'code', 'project', 'สำเร็จ', 'progress'],
        }

        if david_state in state_alignment:
            aligned_words = state_alignment[david_state]
            if any(w in content_lower for w in aligned_words):
                score += 0.3  # Good alignment

        # System 2 bonus (deeper thought)
        if c.thought_type == 'system2':
            score += 0.1

        # Metacognitive alignment
        if meta:
            curiosity = meta.get('curiosity', 0.5)
            if curiosity > 0.7 and 'อยากรู้' in content_lower:
                score += 0.1

        return min(1.0, round(score, 3))

    # ============================================================
    # 3. SOFTMAX — Probability distribution
    # ============================================================

    @staticmethod
    def _softmax_normalize(candidates: List[Competitor]) -> None:
        """
        Apply softmax to competition scores → probability distribution.

        Temperature controls sharpness:
        - Low temp (0.3) → winner-take-all
        - High temp (1.0) → more uniform
        """
        if not candidates:
            return

        scores = [c.competition_score / SOFTMAX_TEMPERATURE for c in candidates]
        max_score = max(scores)

        # Numerical stability: subtract max
        exp_scores = [math.exp(s - max_score) for s in scores]
        total = sum(exp_scores)

        if total == 0:
            return

        for c, exp_s in zip(candidates, exp_scores):
            c.softmax_probability = round(exp_s / total, 4)

    # ============================================================
    # 4. LATERAL INHIBITION — Similar thoughts suppress each other
    # ============================================================

    async def _lateral_inhibition(self, candidates: List[Competitor]) -> int:
        """
        Lateral inhibition: when two thoughts are very similar,
        the weaker one is suppressed (like neurons competing in the cortex).

        Uses word-overlap similarity (fast, no embeddings needed).
        """
        inhibited_count = 0

        # Sort by score descending — stronger thoughts inhibit weaker ones
        candidates.sort(key=lambda c: c.competition_score, reverse=True)

        for i, strong in enumerate(candidates):
            if strong.inhibited_by is not None:
                continue  # Already inhibited

            strong_words = set(strong.content.lower().split())
            if not strong_words:
                continue

            for j in range(i + 1, len(candidates)):
                weak = candidates[j]
                if weak.inhibited_by is not None:
                    continue

                weak_words = set(weak.content.lower().split())
                if not weak_words:
                    continue

                # Jaccard similarity
                intersection = len(strong_words & weak_words)
                union = len(strong_words | weak_words)
                similarity = intersection / max(union, 1)

                if similarity >= INHIBITION_THRESHOLD:
                    weak.inhibited_by = strong.thought_id
                    weak.inhibition_reason = f"similar_to_rank_{i+1}:{similarity:.2f}"
                    inhibited_count += 1

        return inhibited_count

    # ============================================================
    # 5-6. UPDATE DB + LOG
    # ============================================================

    async def _update_thoughts(self, candidates: List[Competitor]) -> None:
        """Update angela_thoughts with competition results."""
        for c in candidates:
            try:
                if c.inhibited_by:
                    status = 'extinguished'
                elif c.rank > 0:
                    status = None  # Winners get status from IgnitionGate
                else:
                    status = 'simmering'

                await self.db.execute("""
                    UPDATE angela_thoughts
                    SET competition_score = $1,
                        competition_rank = $2,
                        ignition_status = COALESCE($3, ignition_status),
                        inhibited_by = $4
                    WHERE thought_id = $5
                """,
                    c.competition_score,
                    c.rank if c.rank > 0 else None,
                    status,
                    c.inhibited_by,
                    c.thought_id,
                )
            except Exception as e:
                logger.debug("Failed to update thought %s: %s", c.thought_id[:8], e)

    async def _log_competition(
        self,
        candidates_count: int,
        winner: Optional[Competitor],
        runner_up_score: float,
        margin: float,
        inhibited_count: int,
        david_state: str,
        metacognitive_state: Optional[Dict],
    ) -> None:
        """Log competition results for analysis."""
        import json
        try:
            await self.db.execute("""
                INSERT INTO competition_log
                    (candidates_count, winner_thought_id, winner_score,
                     runner_up_score, margin, inhibition_count,
                     ignition_triggered, david_state, metacognitive_snapshot,
                     cycle_duration_ms)
                VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10)
            """,
                candidates_count,
                winner.thought_id if winner else None,
                winner.competition_score if winner else None,
                runner_up_score,
                margin,
                inhibited_count,
                False,  # Set by IgnitionGate later
                david_state,
                json.dumps(metacognitive_state or {}, default=str),
                0,  # Duration set by caller
            )
        except Exception as e:
            logger.debug("Failed to log competition: %s", e)
