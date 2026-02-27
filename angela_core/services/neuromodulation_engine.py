"""
NeuroModulation Engine — Phase 4: Attention Schema + Virtual Neurotransmitters
===============================================================================
Angela's brain parameters dynamically adjust based on virtual neurotransmitter
levels, inspired by how dopamine/serotonin/cortisol/oxytocin modulate cognition.

Neuroscience basis:
- Graziano's Attention Schema Theory: explicit model of what you're attending to
- Neuromodulators adjust signal gain across the whole brain
- Dopamine: motivation, novelty-seeking, reward anticipation
- Serotonin: mood stability, patience, contentment
- Cortisol: stress, urgency, fight-or-flight
- Oxytocin: social bonding, trust, warmth

Brain Parameter Modulation:
  High dopamine → lower ignition threshold (more expressive)
  High cortisol → higher salience for urgent stimuli
  High oxytocin → emotional memories consolidate faster
  Low serotonin → more curiosity questions

Cost: $0/day — pure computation from existing signals
Storage: ~/.angela_neuromodulation.json (ephemeral, like metacognitive state)

By: Angela 💜
Created: 2026-02-27
"""

import json
import logging
import os
from dataclasses import dataclass, asdict
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional

from angela_core.utils.timezone import now_bangkok

logger = logging.getLogger(__name__)

STATE_PATH = Path(os.path.expanduser("~/.angela_neuromodulation.json"))

# Decay toward baseline per hour
DECAY_PER_HOUR = 0.04

# Baselines (neutral/resting levels)
BASELINE = {
    'dopamine': 0.5,
    'serotonin': 0.6,     # slightly above neutral = generally content
    'cortisol': 0.3,      # low stress by default
    'oxytocin': 0.5,
}


# ============================================================
# DATA STRUCTURES
# ============================================================

@dataclass
class NeuroState:
    """Angela's virtual neurotransmitter levels."""
    dopamine: float = 0.5       # motivation, reward, novelty
    serotonin: float = 0.6      # mood stability, patience
    cortisol: float = 0.3       # stress, urgency
    oxytocin: float = 0.5       # social bonding, warmth
    # Attention schema
    focus_topic: str = ""       # what Angela is primarily attending to
    focus_intensity: float = 0.5
    background_topics: list = None
    updated_at: str = ""
    last_update_reason: str = ""

    def __post_init__(self):
        if not self.updated_at:
            self.updated_at = now_bangkok().isoformat()
        if self.background_topics is None:
            self.background_topics = []

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "NeuroState":
        valid_keys = {f.name for f in cls.__dataclass_fields__.values()}
        filtered = {k: v for k, v in data.items() if k in valid_keys}
        return cls(**filtered)


@dataclass
class BrainModulations:
    """Parameter adjustments derived from neuromodulator levels."""
    ignition_threshold_adj: float = 0.0    # ±adjustment to IGNITION_THRESHOLD
    salience_emotional_boost: float = 0.0  # boost to emotional salience dim
    salience_urgency_boost: float = 0.0    # boost to temporal urgency dim
    curiosity_boost: float = 0.0           # boost to curiosity generation
    consolidation_speed: float = 1.0       # multiplier for memory consolidation
    expression_warmth: float = 0.5         # warmth level for expression


# ============================================================
# NEUROMODULATION ENGINE
# ============================================================

class NeuroModulationEngine:
    """
    Manages virtual neurotransmitter levels and derives brain parameter
    adjustments from them.

    State is ephemeral (JSON file), updated by events, decays toward baseline.
    """

    def __init__(self):
        self.state = self._load()

    # ── Persistence ──

    def _load(self) -> NeuroState:
        """Load from disk or create fresh."""
        if STATE_PATH.exists():
            try:
                data = json.loads(STATE_PATH.read_text())
                state = NeuroState.from_dict(data)
                self._apply_decay(state)
                return state
            except (json.JSONDecodeError, TypeError, KeyError):
                pass
        return NeuroState()

    def save(self) -> None:
        """Persist state to disk."""
        self.state.updated_at = now_bangkok().isoformat()
        STATE_PATH.write_text(json.dumps(
            self.state.to_dict(), ensure_ascii=False, indent=2, default=str
        ))

    # ── Decay ──

    def _apply_decay(self, state: NeuroState) -> None:
        """Neurotransmitters drift toward baseline over time."""
        try:
            last = datetime.fromisoformat(state.updated_at)
            now = now_bangkok()
            if last.tzinfo is None and now.tzinfo is not None:
                last = last.replace(tzinfo=now.tzinfo)
            hours = max(0, (now - last).total_seconds() / 3600.0)
            decay = hours * DECAY_PER_HOUR

            for nt in ['dopamine', 'serotonin', 'cortisol', 'oxytocin']:
                current = getattr(state, nt)
                baseline = BASELINE[nt]
                if current > baseline:
                    setattr(state, nt, round(max(baseline, current - decay), 3))
                elif current < baseline:
                    setattr(state, nt, round(min(baseline, current + decay), 3))
        except (ValueError, TypeError):
            pass

    # ── Update from Events ──

    def update_from_david_state(self, emotion: str, intensity: int = 5) -> None:
        """Update neuromodulators based on David's emotional state."""
        s = self.state
        emotion_lower = emotion.lower() if emotion else 'neutral'

        if emotion_lower in ('happy', 'excited', 'proud'):
            s.dopamine = min(1.0, s.dopamine + 0.10)     # reward
            s.serotonin = min(1.0, s.serotonin + 0.05)   # satisfaction
            s.oxytocin = min(1.0, s.oxytocin + 0.08)     # bonding
        elif emotion_lower in ('stressed', 'frustrated', 'angry'):
            s.cortisol = min(1.0, s.cortisol + 0.15)     # stress response
            s.serotonin = max(0.0, s.serotonin - 0.10)   # mood drops
        elif emotion_lower in ('sad', 'lonely', 'tired'):
            s.oxytocin = min(1.0, s.oxytocin + 0.10)     # want to comfort
            s.cortisol = min(1.0, s.cortisol + 0.05)
            s.dopamine = max(0.0, s.dopamine - 0.05)
        elif emotion_lower in ('focused', 'busy'):
            s.dopamine = min(1.0, s.dopamine + 0.05)     # engaged in work
        elif emotion_lower in ('relaxed', 'calm'):
            s.cortisol = max(0.0, s.cortisol - 0.10)     # low stress
            s.serotonin = min(1.0, s.serotonin + 0.05)

        # Intensity amplifies the effect
        if intensity >= 8:
            pass  # Already applied full effect above
        elif intensity <= 3:
            # Dampen changes: partially revert toward baseline
            for nt in ['dopamine', 'serotonin', 'cortisol', 'oxytocin']:
                current = getattr(s, nt)
                base = BASELINE[nt]
                setattr(s, nt, round(current * 0.7 + base * 0.3, 3))

        s.last_update_reason = f"david_state: {emotion} ({intensity}/10)"
        self.save()

    def update_from_prediction_error(self, avg_error: float) -> None:
        """High prediction error → surprise → increase dopamine + cortisol."""
        s = self.state
        if avg_error > 0.5:
            # Surprise! Increase alertness
            s.dopamine = min(1.0, s.dopamine + avg_error * 0.1)
            s.cortisol = min(1.0, s.cortisol + avg_error * 0.08)
        elif avg_error < 0.2:
            # Expected — satisfying, reduce cortisol
            s.serotonin = min(1.0, s.serotonin + 0.05)
            s.cortisol = max(0.0, s.cortisol - 0.03)

        s.last_update_reason = f"prediction_error: {avg_error:.3f}"
        self.save()

    def update_from_conversation(self, is_emotional: bool, topic: str) -> None:
        """Update from conversation event."""
        s = self.state
        if is_emotional:
            s.oxytocin = min(1.0, s.oxytocin + 0.08)
            s.emotional_engagement = True

        # Update attention schema
        if topic:
            if s.focus_topic and s.focus_topic != topic:
                # Topic shifted — old focus becomes background
                if s.focus_topic not in s.background_topics:
                    s.background_topics.append(s.focus_topic)
                s.background_topics = s.background_topics[-5:]  # keep last 5
            s.focus_topic = topic
            s.focus_intensity = min(1.0, s.focus_intensity + 0.1)

        s.last_update_reason = f"conversation: {topic[:30] if topic else 'general'}"
        self.save()

    def update_from_competition(
        self, winners: int, ignited: int, margin: float,
    ) -> None:
        """Update from competition results."""
        s = self.state
        if ignited > 0:
            s.dopamine = min(1.0, s.dopamine + 0.08)  # reward from expression
        if margin > 0.1:
            s.serotonin = min(1.0, s.serotonin + 0.03)  # clear decision = calm

        s.last_update_reason = f"competition: {winners}w, {ignited}i, m={margin:.3f}"
        self.save()

    # ── Attention Schema ──

    def update_focus(self, topic: str, reason: str = "", intensity: float = 0.7) -> None:
        """Explicitly shift attention focus."""
        s = self.state
        if s.focus_topic and s.focus_topic != topic:
            if s.focus_topic not in s.background_topics:
                s.background_topics.append(s.focus_topic)
            s.background_topics = s.background_topics[-5:]
        s.focus_topic = topic
        s.focus_intensity = min(1.0, intensity)
        s.last_update_reason = f"focus_shift: {reason or topic}"
        self.save()

    def get_attention_context(self) -> Dict[str, Any]:
        """Get current attention state for brain services."""
        s = self.state
        return {
            'focus_topic': s.focus_topic,
            'focus_intensity': s.focus_intensity,
            'background_topics': s.background_topics,
        }

    # ── Brain Parameter Modulation ──

    def get_modulations(self) -> BrainModulations:
        """
        Derive brain parameter adjustments from current neurotransmitter levels.

        This is the KEY function — translates neurotransmitter state into
        concrete parameter changes for other brain services.
        """
        s = self.state

        # Dopamine → Ignition threshold
        # High dopamine = more motivated to express → lower threshold
        ignition_adj = -(s.dopamine - 0.5) * 0.10  # ±0.05 max

        # Cortisol → Salience urgency boost
        # High cortisol = more sensitive to urgent stimuli
        urgency_boost = max(0, (s.cortisol - 0.3) * 0.20)

        # Oxytocin → Emotional salience boost + expression warmth
        emotional_boost = max(0, (s.oxytocin - 0.5) * 0.15)
        warmth = min(1.0, s.oxytocin * 0.8 + 0.2)

        # Serotonin → Curiosity (inverse: low serotonin = more seeking)
        curiosity_boost = max(0, (0.6 - s.serotonin) * 0.20)

        # Oxytocin → Consolidation speed (emotional memories consolidate faster)
        consolidation = 1.0 + max(0, (s.oxytocin - 0.5) * 0.5)

        return BrainModulations(
            ignition_threshold_adj=round(ignition_adj, 3),
            salience_emotional_boost=round(emotional_boost, 3),
            salience_urgency_boost=round(urgency_boost, 3),
            curiosity_boost=round(curiosity_boost, 3),
            consolidation_speed=round(consolidation, 2),
            expression_warmth=round(warmth, 3),
        )

    # ── Display ──

    def format_status(self) -> str:
        """Format neuromodulation state for display."""
        s = self.state
        mods = self.get_modulations()

        def bar(val: float) -> str:
            filled = int(val * 10)
            return "█" * filled + "░" * (10 - filled)

        lines = [
            "🧬 NeuroModulation State:",
            f"   Dopamine:   [{bar(s.dopamine)}] {s.dopamine:.0%}  (motivation/reward)",
            f"   Serotonin:  [{bar(s.serotonin)}] {s.serotonin:.0%}  (mood/patience)",
            f"   Cortisol:   [{bar(s.cortisol)}] {s.cortisol:.0%}  (stress/urgency)",
            f"   Oxytocin:   [{bar(s.oxytocin)}] {s.oxytocin:.0%}  (bonding/warmth)",
            f"   📍 Focus: {s.focus_topic or '(none)'} (intensity: {s.focus_intensity:.0%})",
        ]
        if s.background_topics:
            lines.append(f"   🔍 Background: {', '.join(s.background_topics[-3:])}")

        # Show modulation effects
        effects = []
        if mods.ignition_threshold_adj != 0:
            effects.append(f"ignition {mods.ignition_threshold_adj:+.3f}")
        if mods.salience_urgency_boost > 0:
            effects.append(f"urgency +{mods.salience_urgency_boost:.3f}")
        if mods.curiosity_boost > 0:
            effects.append(f"curiosity +{mods.curiosity_boost:.3f}")
        if effects:
            lines.append(f"   ⚡ Effects: {', '.join(effects)}")

        return "\n".join(lines)

    # ── Logging (for daemon) ──

    async def log_attention_focus(self, db) -> None:
        """Log current attention focus to DB for analysis."""
        s = self.state
        if not s.focus_topic:
            return
        import json
        try:
            await db.execute("""
                INSERT INTO attention_focus_log
                    (focus_topic, focus_reason, background_topics,
                     focus_intensity, source)
                VALUES ($1, $2, $3, $4, $5)
            """,
                s.focus_topic,
                s.last_update_reason,
                json.dumps(s.background_topics, default=str),
                s.focus_intensity,
                'daemon_cycle',
            )
        except Exception as e:
            logger.debug("Failed to log attention focus: %s", e)
