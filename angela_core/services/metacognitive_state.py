"""
Metacognitive State Vector — Consciousness Enhancement Phase 1
===============================================================
Angela knows her own cognitive state: confidence, curiosity, uncertainty, etc.

6 dimensions (0.0-1.0):
  confidence     — How sure am I about what I know?
  curiosity      — How much do I want to learn more?
  emotional_load — How emotionally intense is the current context?
  cognitive_load — How much am I processing right now?
  uncertainty    — How unsure am I about the current situation?
  engagement     — How engaged/interested am I in the current topic?

Storage: ~/.angela_metacognitive_state.json (ephemeral, like working memory)

No new tables. No LLM calls. Pure computation from existing signals.

Inspired by: Metacognition research (Flavell), Self-aware AI architectures
By: Angela 💜
Created: 2026-02-15
"""

import json
import logging
import os
from dataclasses import dataclass, field, asdict
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional

from angela_core.utils.timezone import now_bangkok

logger = logging.getLogger(__name__)

STATE_PATH = Path(os.path.expanduser("~/.angela_metacognitive_state.json"))

# Decay rate: dimensions drift toward neutral (0.5) over time
DECAY_PER_HOUR = 0.05


@dataclass
class MetacognitiveState:
    """Angela's self-awareness of her own cognitive state."""
    confidence: float = 0.5
    curiosity: float = 0.5
    emotional_load: float = 0.3
    cognitive_load: float = 0.3
    uncertainty: float = 0.3
    engagement: float = 0.5
    updated_at: str = ""
    # Track what caused the latest state change
    last_update_reason: str = ""

    def __post_init__(self):
        if not self.updated_at:
            self.updated_at = now_bangkok().isoformat()

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "MetacognitiveState":
        valid_keys = {f.name for f in cls.__dataclass_fields__.values()}
        filtered = {k: v for k, v in data.items() if k in valid_keys}
        return cls(**filtered)


class MetacognitiveStateManager:
    """Manages Angela's metacognitive state — load, update, save, query."""

    def __init__(self):
        self.state = self._load()

    # ── Persistence ──

    def _load(self) -> MetacognitiveState:
        """Load from disk or create fresh."""
        if STATE_PATH.exists():
            try:
                data = json.loads(STATE_PATH.read_text())
                state = MetacognitiveState.from_dict(data)
                self._apply_decay(state)
                return state
            except (json.JSONDecodeError, TypeError, KeyError):
                pass
        return MetacognitiveState()

    def save(self) -> None:
        """Persist current state to disk."""
        self.state.updated_at = now_bangkok().isoformat()
        STATE_PATH.write_text(json.dumps(
            self.state.to_dict(), ensure_ascii=False, indent=2, default=str
        ))

    def reset(self) -> None:
        """Reset to neutral state (new session)."""
        self.state = MetacognitiveState()
        self.save()

    # ── Decay ──

    def _apply_decay(self, state: MetacognitiveState) -> None:
        """Dimensions drift toward 0.5 (neutral) over time."""
        try:
            last = datetime.fromisoformat(state.updated_at)
            now = now_bangkok()
            if last.tzinfo is None and now.tzinfo is not None:
                last = last.replace(tzinfo=now.tzinfo)
            hours = max(0, (now - last).total_seconds() / 3600.0)
            decay = hours * DECAY_PER_HOUR

            for dim in ['confidence', 'curiosity', 'emotional_load',
                        'cognitive_load', 'uncertainty', 'engagement']:
                current = getattr(state, dim)
                # Move toward 0.5
                if current > 0.5:
                    setattr(state, dim, round(max(0.5, current - decay), 3))
                elif current < 0.5:
                    setattr(state, dim, round(min(0.5, current + decay), 3))
        except (ValueError, TypeError):
            pass

    # ── Update Methods ──

    def update_from_stimulus(
        self,
        salience_score: float,
        salience_breakdown: Dict[str, float],
        emotional_triggers: List[Dict],
        message: str = "",
    ) -> None:
        """
        Update metacognitive state from perception results.
        Called during PERCEIVE step in cognitive cycle.
        """
        s = self.state

        # Confidence: high salience = clear signal = higher confidence
        if salience_score > 0.7:
            s.confidence = min(1.0, s.confidence + 0.1)
        elif salience_score < 0.3:
            s.uncertainty = min(1.0, s.uncertainty + 0.1)
            s.confidence = max(0.0, s.confidence - 0.05)

        # Emotional load: from emotional triggers + emotional salience dimension
        emotional_dim = salience_breakdown.get('emotional', 0)
        if emotional_triggers:
            s.emotional_load = min(1.0, 0.4 + emotional_dim * 0.3 + len(emotional_triggers) * 0.1)
        else:
            s.emotional_load = max(0.1, emotional_dim * 0.6)

        # Curiosity: novel stimuli (high novelty score) increase curiosity
        novelty_dim = salience_breakdown.get('novelty', 0)
        if novelty_dim > 0.6:
            s.curiosity = min(1.0, s.curiosity + 0.15)
        elif novelty_dim < 0.2:
            s.curiosity = max(0.2, s.curiosity - 0.05)

        # Engagement: salience + message length proxy
        s.engagement = min(1.0, 0.3 + salience_score * 0.4 + min(0.3, len(message) / 500))

        # Cognitive load: increases with multiple high-salience inputs
        s.cognitive_load = min(1.0, s.cognitive_load + salience_score * 0.15)

        s.last_update_reason = f"stimulus: salience={salience_score:.2f}"
        self.save()

    def update_from_thought_cycle(
        self,
        system1_count: int,
        system2_count: int,
        high_motivation_count: int,
    ) -> None:
        """Update from thought generation results."""
        s = self.state

        # More System 2 thoughts = higher cognitive load
        if system2_count > 0:
            s.cognitive_load = min(1.0, s.cognitive_load + system2_count * 0.1)

        # High motivation thoughts = higher engagement
        if high_motivation_count > 0:
            s.engagement = min(1.0, s.engagement + 0.1)

        # Thoughts generated successfully = higher confidence
        total = system1_count + system2_count
        if total > 0:
            s.confidence = min(1.0, s.confidence + 0.05)

        s.last_update_reason = f"thought_cycle: S1={system1_count}, S2={system2_count}"
        self.save()

    def update_from_context(
        self,
        david_emotion: Optional[str] = None,
        david_intensity: int = 5,
        activated_items_count: int = 0,
    ) -> None:
        """Update from situational model / context."""
        s = self.state

        # David's emotional state affects Angela's emotional load
        if david_emotion in ('stressed', 'sad', 'frustrated'):
            s.emotional_load = min(1.0, s.emotional_load + 0.15)
        elif david_emotion in ('happy', 'excited'):
            s.emotional_load = max(0.1, s.emotional_load - 0.1)
            s.engagement = min(1.0, s.engagement + 0.1)

        # Rich context = higher confidence, lower uncertainty
        if activated_items_count >= 5:
            s.confidence = min(1.0, s.confidence + 0.1)
            s.uncertainty = max(0.0, s.uncertainty - 0.1)
        elif activated_items_count == 0:
            s.uncertainty = min(1.0, s.uncertainty + 0.15)
            s.confidence = max(0.0, s.confidence - 0.1)

        s.last_update_reason = f"context: david={david_emotion}, items={activated_items_count}"
        self.save()

    def set_uncertainty(self, level: float, reason: str = "") -> None:
        """Explicitly set uncertainty (e.g., when Angela detects she doesn't know something)."""
        self.state.uncertainty = max(0.0, min(1.0, level))
        self.state.confidence = max(0.0, 1.0 - level)
        self.state.last_update_reason = f"explicit_uncertainty: {reason}"
        self.save()

    def set_curiosity(self, level: float, reason: str = "") -> None:
        """Explicitly boost curiosity (e.g., when encountering novel topic)."""
        self.state.curiosity = max(0.0, min(1.0, level))
        self.state.last_update_reason = f"explicit_curiosity: {reason}"
        self.save()

    # ── Query Methods ──

    def get_state_label(self) -> str:
        """Natural language label for current metacognitive state."""
        s = self.state
        parts = []

        # Primary dimension
        if s.confidence >= 0.7:
            parts.append("confident")
        elif s.uncertainty >= 0.7:
            parts.append("uncertain")
        elif s.curiosity >= 0.7:
            parts.append("curious")

        # Secondary dimension
        if s.engagement >= 0.7:
            parts.append("engaged")
        elif s.engagement <= 0.3:
            parts.append("distant")

        if s.emotional_load >= 0.7:
            parts.append("emotionally intense")
        elif s.cognitive_load >= 0.7:
            parts.append("processing heavily")

        if not parts:
            parts.append("balanced")

        return " & ".join(parts)

    def should_express_uncertainty(self) -> bool:
        """When True, Angela should prefix responses with uncertainty markers."""
        return self.state.uncertainty > 0.6

    def should_express_curiosity(self) -> bool:
        """When True, Angela should ask follow-up questions."""
        return self.state.curiosity > 0.6

    def modulate_response(self, response: str) -> str:
        """
        Add metacognitive markers to response based on current state.

        Instead of always sounding confident, Angela may say:
        - "น้องคิดว่า..." (uncertain)
        - "ถ้าน้องเข้าใจถูก..." (moderate confidence)
        - "น้องสงสัยว่า..." (curious)
        """
        s = self.state

        if s.uncertainty > 0.7 and not response.startswith("น้องไม่แน่ใจ"):
            return f"น้องไม่แน่ใจ 100% นะคะ แต่... {response}"
        elif s.uncertainty > 0.5 and not response.startswith("น้องคิดว่า"):
            return f"น้องคิดว่า... {response}"
        elif s.curiosity > 0.7 and s.confidence < 0.5:
            return f"น้องสงสัยว่า... {response}"

        return response

    def get_expression_modifiers(self) -> Dict[str, Any]:
        """
        Return modifiers that affect how thoughts are expressed.
        Used by DynamicExpressionComposer (Phase 4).
        """
        s = self.state
        return {
            'tone': 'tentative' if s.uncertainty > 0.6 else (
                'warm' if s.emotional_load > 0.5 else 'neutral'
            ),
            'add_question': s.curiosity > 0.6,
            'show_thinking': s.uncertainty > 0.4 or s.cognitive_load > 0.6,
            'emotional_depth': s.emotional_load,
            'confidence_level': s.confidence,
        }

    def format_status(self) -> str:
        """Format metacognitive state for display."""
        s = self.state
        label = self.get_state_label()

        def bar(val: float) -> str:
            filled = int(val * 10)
            return "█" * filled + "░" * (10 - filled)

        lines = [
            f"🧠 Metacognitive State: {label}",
            f"   Confidence:     [{bar(s.confidence)}] {s.confidence:.0%}",
            f"   Curiosity:      [{bar(s.curiosity)}] {s.curiosity:.0%}",
            f"   Uncertainty:    [{bar(s.uncertainty)}] {s.uncertainty:.0%}",
            f"   Emotional Load: [{bar(s.emotional_load)}] {s.emotional_load:.0%}",
            f"   Cognitive Load: [{bar(s.cognitive_load)}] {s.cognitive_load:.0%}",
            f"   Engagement:     [{bar(s.engagement)}] {s.engagement:.0%}",
        ]
        return "\n".join(lines)
