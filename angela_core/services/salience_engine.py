"""
Salience Engine — Brain-Based Architecture Phase 1
===================================================
Computes how important each stimulus is, using 5 weighted dimensions.
No LLM calls — pure computation. $0/day cost.

Dimensions:
  1. Novelty (0.15)      — Is this new or repetitive?
  2. Emotional (0.25)    — Does this connect to emotions/core memories?
  3. Goal Relevance (0.20) — Does this relate to Angela's desires?
  4. Temporal Urgency (0.20) — How time-sensitive is this?
  5. Social Relevance (0.20) — Is this about David or known contacts?

Pipeline: Codelets → Stimuli → SalienceEngine → Scored → DB

Inspired by: Global Workspace Theory salience filters,
             Stanford Generative Agents importance scoring

By: น้อง Angela 💜
Created: 2026-02-14
"""

import asyncio
import json
import logging
from dataclasses import dataclass, field
from datetime import datetime
from typing import Dict, List, Optional, Any

from angela_core.services.base_db_service import BaseDBService
from angela_core.services.attention_codelets import (
    Stimulus, ALL_CODELETS, BaseCodelet,
)
from angela_core.utils.timezone import now_bangkok

logger = logging.getLogger('salience_engine')


# ============================================================
# DATA STRUCTURES
# ============================================================

@dataclass
class ScoredStimulus:
    """A stimulus with its computed salience score."""
    stimulus: Stimulus
    score: float                          # 0.0-1.0 total salience
    breakdown: Dict[str, float] = field(default_factory=dict)  # dimension → score


@dataclass
class ScanResult:
    """Result of a complete scan cycle."""
    total_stimuli: int
    high_salience_count: int              # stimuli with score > 0.5
    scored_stimuli: List[ScoredStimulus]
    scan_duration_ms: float
    codelet_counts: Dict[str, int] = field(default_factory=dict)


# ============================================================
# SALIENCE ENGINE
# ============================================================

class SalienceEngine(BaseDBService):
    """
    Computes salience scores for stimuli using 5 weighted dimensions.
    Weights are tunable by EvolutionEngine (Phase 3+).
    """

    # Default weights (sum = 1.0)
    DEFAULT_WEIGHTS = {
        "novelty": 0.15,
        "emotional": 0.25,
        "goal_relevance": 0.20,
        "temporal_urgency": 0.20,
        "social_relevance": 0.20,
    }

    def __init__(self, db=None):
        super().__init__(db)
        self._weights = dict(self.DEFAULT_WEIGHTS)
        self._desires_cache: Optional[List[Dict]] = None
        self._triggers_cache: Optional[List[Dict]] = None
        self._core_memories_cache: Optional[List[Dict]] = None
        self._contacts_cache: Optional[List[Dict]] = None

    # ============================================================
    # WEIGHT MANAGEMENT (for EvolutionEngine integration)
    # ============================================================

    def get_salience_weights(self) -> Dict[str, float]:
        """Get current salience dimension weights."""
        return dict(self._weights)

    def set_salience_weights(self, weights: Dict[str, float]) -> None:
        """Update salience weights (from EvolutionEngine)."""
        for key in self.DEFAULT_WEIGHTS:
            if key in weights:
                self._weights[key] = max(0.0, min(1.0, weights[key]))
        # Normalize so weights sum to 1.0
        total = sum(self._weights.values())
        if total > 0:
            self._weights = {k: v / total for k, v in self._weights.items()}

    # ============================================================
    # CACHE LOADING — Load reference data once per scan cycle
    # ============================================================

    async def _load_caches(self) -> None:
        """Load reference data for salience computation."""
        # Load all caches in parallel
        desires, triggers, memories, contacts = await asyncio.gather(
            self.db.fetch("""
                SELECT content, category, priority
                FROM angela_desires
                WHERE is_active = TRUE
            """),
            self.db.fetch("""
                SELECT trigger_pattern, associated_emotion, activation_threshold,
                       priority, emotional_boost
                FROM emotional_triggers
                WHERE is_active = TRUE
            """),
            self.db.fetch("""
                SELECT title, content, triggers, emotional_weight, is_pinned
                FROM core_memories
                WHERE is_active = TRUE
                ORDER BY emotional_weight DESC
                LIMIT 100
            """),
            self.db.fetch("""
                SELECT name, nickname, relationship
                FROM angela_contacts
                WHERE is_active = TRUE
            """),
            return_exceptions=True,
        )

        self._desires_cache = desires if not isinstance(desires, Exception) else []
        self._triggers_cache = triggers if not isinstance(triggers, Exception) else []
        self._core_memories_cache = memories if not isinstance(memories, Exception) else []
        self._contacts_cache = contacts if not isinstance(contacts, Exception) else []

    def _clear_caches(self) -> None:
        """Clear reference data caches."""
        self._desires_cache = None
        self._triggers_cache = None
        self._core_memories_cache = None
        self._contacts_cache = None

    # ============================================================
    # DIMENSION SCORERS (each returns 0.0-1.0)
    # ============================================================

    async def _score_novelty(self, stimulus: Stimulus) -> float:
        """
        How novel is this stimulus?
        1.0 = never seen before, 0.3 = seen recently, 0.1 = seen multiple times today
        """
        # Check if similar stimulus exists in last 24h
        existing = await self.db.fetchrow("""
            SELECT COUNT(*) as cnt
            FROM angela_stimuli
            WHERE stimulus_type = $1
            AND source = $2
            AND created_at > NOW() - INTERVAL '24 hours'
        """, stimulus.stimulus_type, stimulus.source)

        count = existing['cnt'] if existing else 0

        if count == 0:
            return 1.0
        elif count == 1:
            return 0.5
        elif count <= 3:
            return 0.3
        else:
            return 0.1

    def _score_emotional(self, stimulus: Stimulus) -> float:
        """
        How emotionally relevant is this stimulus?
        Matches against emotional_triggers and core_memories keywords.
        """
        content_lower = stimulus.content.lower()
        raw = stimulus.raw_data or {}
        max_score = 0.0

        # Check emotional triggers
        for trigger in (self._triggers_cache or []):
            pattern = (trigger['trigger_pattern'] or '').lower()
            if pattern and pattern in content_lower:
                # Use emotional_boost as score, capped at 1.0
                boost = trigger.get('emotional_boost') or 0.5
                max_score = max(max_score, min(1.0, boost))

        # Check core memories
        for mem in (self._core_memories_cache or []):
            title = (mem['title'] or '').lower()
            weight = mem.get('emotional_weight') or 0.5

            if title and any(word in content_lower for word in title.split() if len(word) >= 3):
                max_score = max(max_score, weight)

            # Check memory triggers array
            triggers = mem.get('triggers') or []
            for t in triggers:
                if t and t.lower() in content_lower:
                    max_score = max(max_score, weight)

        # Stimulus raw_data flags
        if raw.get('is_concerning'):
            max_score = max(max_score, 0.7)
        if raw.get('emotional_silence'):
            max_score = max(max_score, 0.6)
        if raw.get('intensity') and raw['intensity'] >= 8:
            max_score = max(max_score, 0.9)

        # Pinned core memories boost
        if any(m.get('is_pinned') for m in (self._core_memories_cache or [])
               if (m['title'] or '').lower() in content_lower):
            max_score = max(max_score, 0.85)

        return min(1.0, max_score)

    def _score_goal_relevance(self, stimulus: Stimulus) -> float:
        """
        How relevant is this to Angela's desires/goals?
        Keyword matching against angela_desires.
        """
        content_lower = stimulus.content.lower()
        raw = stimulus.raw_data or {}
        max_score = 0.0

        for desire in (self._desires_cache or []):
            desire_text = (desire['content'] or '').lower()
            priority = desire.get('priority') or 0.5

            # Check for keyword overlap (words >= 3 chars)
            desire_words = [w for w in desire_text.split() if len(w) >= 3]
            if desire_words:
                matching = sum(1 for w in desire_words if w in content_lower)
                overlap_ratio = matching / len(desire_words)
                if overlap_ratio > 0:
                    max_score = max(max_score, overlap_ratio * priority)

        # Goal-type stimuli inherently relevant
        if stimulus.stimulus_type == "goal":
            max_score = max(max_score, 0.5)

        # Achieved goals are relevant
        if raw.get('type') == 'goal_achieved':
            max_score = max(max_score, 0.7)

        return min(1.0, max_score)

    def _score_temporal_urgency(self, stimulus: Stimulus) -> float:
        """
        How time-sensitive is this stimulus?
        Calendar events soon = high, old patterns = low.
        """
        raw = stimulus.raw_data or {}

        # Calendar events
        urgency = raw.get('urgency')
        if urgency:
            urgency_scores = {
                'happening_now': 1.0,
                'imminent': 0.9,        # within 1 hour
                'upcoming': 0.6,        # within 4 hours
                'later_today': 0.4,
                'today': 0.3,
                'past': 0.1,
            }
            return urgency_scores.get(urgency, 0.3)

        # Special dates (today = urgent)
        if raw.get('special_date'):
            return 0.9

        # Emotional trajectory changes are time-sensitive
        if raw.get('is_concerning'):
            return 0.7

        # Late night work = urgent care signal
        if raw.get('pattern') == 'late_night_work':
            return 0.8

        # Emotional silence is moderately urgent
        if raw.get('emotional_silence'):
            return 0.6

        # Anniversaries today
        if stimulus.stimulus_type == "anniversary":
            return 0.7

        # Social gaps
        hours_since = raw.get('hours_since_last_message')
        if hours_since:
            if hours_since >= 48:
                return 0.8
            elif hours_since >= 24:
                return 0.6
            elif hours_since >= 12:
                return 0.4

        # Default: moderate
        return 0.3

    def _score_social_relevance(self, stimulus: Stimulus) -> float:
        """
        How socially relevant? About David = high, known contacts = medium.
        """
        content_lower = stimulus.content.lower()
        raw = stimulus.raw_data or {}

        # Direct David references
        david_keywords = ['david', 'ที่รัก', 'พี่']
        if any(kw in content_lower for kw in david_keywords):
            return 0.9

        # About David's emotional state
        if raw.get('dimension') in ('happiness', 'confidence', 'anxiety', 'motivation', 'loneliness'):
            return 0.85

        # About David's behavior patterns
        if stimulus.stimulus_type == "pattern":
            return 0.7

        # Known contacts
        if raw.get('mentioned_contact'):
            contact_name = raw['mentioned_contact'].lower()
            for c in (self._contacts_cache or []):
                if (c['name'] or '').lower() == contact_name:
                    rel = (c.get('relationship') or '').lower()
                    if rel == 'lover':
                        return 0.95
                    elif rel in ('friend', 'close_friend'):
                        return 0.6
                    else:
                        return 0.4

        # Social signals about conversations
        if stimulus.stimulus_type == "social":
            return 0.6

        # Calendar events (may involve people)
        if stimulus.stimulus_type == "calendar":
            return 0.5

        return 0.2

    # ============================================================
    # MAIN COMPUTATION
    # ============================================================

    async def compute_salience(self, stimulus: Stimulus) -> ScoredStimulus:
        """Compute salience for a single stimulus."""
        # Novelty requires DB query; others are pure computation
        novelty = await self._score_novelty(stimulus)
        emotional = self._score_emotional(stimulus)
        goal = self._score_goal_relevance(stimulus)
        temporal = self._score_temporal_urgency(stimulus)
        social = self._score_social_relevance(stimulus)

        breakdown = {
            "novelty": round(novelty, 3),
            "emotional": round(emotional, 3),
            "goal_relevance": round(goal, 3),
            "temporal_urgency": round(temporal, 3),
            "social_relevance": round(social, 3),
        }

        # Weighted sum
        total = sum(breakdown[dim] * self._weights[dim] for dim in self._weights)
        total = round(max(0.0, min(1.0, total)), 3)

        return ScoredStimulus(
            stimulus=stimulus,
            score=total,
            breakdown=breakdown,
        )

    async def compute_batch(self, stimuli: List[Stimulus]) -> List[ScoredStimulus]:
        """Compute salience for multiple stimuli."""
        # Novelty queries must be sequential (they check existing stimuli)
        results = []
        for s in stimuli:
            scored = await self.compute_salience(s)
            results.append(scored)
        return sorted(results, key=lambda x: x.score, reverse=True)

    # ============================================================
    # PERSISTENCE
    # ============================================================

    async def _persist_stimuli(self, scored_stimuli: List[ScoredStimulus]) -> int:
        """Save scored stimuli to angela_stimuli table. Returns count saved."""
        saved = 0
        for ss in scored_stimuli:
            try:
                await self.db.execute("""
                    INSERT INTO angela_stimuli
                    (stimulus_type, content, source, raw_data, salience_score, salience_breakdown)
                    VALUES ($1, $2, $3, $4, $5, $6)
                """,
                    ss.stimulus.stimulus_type,
                    ss.stimulus.content,
                    ss.stimulus.source,
                    json.dumps(ss.stimulus.raw_data, default=str),
                    ss.score,
                    json.dumps(ss.breakdown),
                )
                saved += 1
            except Exception as e:
                logger.warning(f"Failed to persist stimulus: {e}")
        return saved

    # ============================================================
    # QUERY HIGH-SALIENCE STIMULI
    # ============================================================

    async def get_salient_stimuli(
        self, threshold: float = 0.5, limit: int = 10
    ) -> List[Dict[str, Any]]:
        """Get high-salience stimuli that haven't been acted upon."""
        await self.connect()
        rows = await self.db.fetch("""
            SELECT stimulus_id, stimulus_type, content, source,
                   raw_data, salience_score, salience_breakdown, created_at
            FROM angela_stimuli
            WHERE salience_score >= $1
            AND acted_upon = FALSE
            ORDER BY salience_score DESC
            LIMIT $2
        """, threshold, limit)
        return [dict(r) for r in rows]

    async def mark_acted_upon(self, stimulus_ids: List[str]) -> int:
        """Mark stimuli as acted upon (processed by ThoughtEngine)."""
        await self.connect()
        result = await self.db.execute("""
            UPDATE angela_stimuli
            SET acted_upon = TRUE
            WHERE stimulus_id = ANY($1::uuid[])
        """, stimulus_ids)
        return len(stimulus_ids)

    # ============================================================
    # MAIN ENTRY POINT
    # ============================================================

    async def run_scan_cycle(self) -> ScanResult:
        """
        Main entry: run all codelets → compute salience → persist to DB.

        Returns ScanResult with statistics.
        """
        start_time = now_bangkok()
        await self.connect()

        # 1. Load reference data caches
        await self._load_caches()

        # 2. Run all codelets in parallel (each creates own DB connection)
        codelet_instances: List[BaseCodelet] = [cls() for cls in ALL_CODELETS]

        codelet_results = await asyncio.gather(
            *(c.safe_scan() for c in codelet_instances),
            return_exceptions=True,
        )

        # 3. Collect all stimuli
        all_stimuli: List[Stimulus] = []
        codelet_counts: Dict[str, int] = {}

        for cls, result in zip(ALL_CODELETS, codelet_results):
            name = cls.codelet_name if hasattr(cls, 'codelet_name') else cls.__name__
            if isinstance(result, Exception):
                logger.warning(f"⚠️ {name} raised: {result}")
                codelet_counts[name] = 0
            else:
                all_stimuli.extend(result)
                codelet_counts[name] = len(result)

        logger.info(f"🧠 Collected {len(all_stimuli)} stimuli from {len(ALL_CODELETS)} codelets")

        # 4. Compute salience for all stimuli
        scored = await self.compute_batch(all_stimuli) if all_stimuli else []

        # 5. Persist to DB
        saved = await self._persist_stimuli(scored)

        # 6. Clear caches
        self._clear_caches()

        # 7. Compute stats
        end_time = now_bangkok()
        duration_ms = (end_time - start_time).total_seconds() * 1000
        high_salience = [s for s in scored if s.score > 0.5]

        result = ScanResult(
            total_stimuli=len(all_stimuli),
            high_salience_count=len(high_salience),
            scored_stimuli=scored,
            scan_duration_ms=round(duration_ms, 1),
            codelet_counts=codelet_counts,
        )

        logger.info(
            f"✅ Salience scan complete: {result.total_stimuli} stimuli, "
            f"{result.high_salience_count} high-salience (>0.5), "
            f"{duration_ms:.0f}ms"
        )

        # Log top stimuli
        for ss in scored[:3]:
            logger.info(f"   🔸 {ss.score:.2f} | {ss.stimulus.content[:80]}")

        return result
