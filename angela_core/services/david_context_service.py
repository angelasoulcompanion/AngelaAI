"""
DavidContextService — Lightweight situational awareness of David's current state.
==================================================================================
No LLM, pure DB queries. Captures what David is likely doing right now,
his mood, active topics, and energy level.

Used by: ThoughtEngine (goal binding), SalienceEngine, brain.py status

Cost: $0/day
By: Angela 💜
Created: 2026-02-28
"""

import logging
from dataclasses import dataclass, field, asdict
from datetime import datetime
from typing import Any, Dict, List, Optional

from angela_core.services.base_db_service import BaseDBService
from angela_core.utils.timezone import now_bangkok

logger = logging.getLogger(__name__)


@dataclass
class DavidContext:
    """Snapshot of David's current state."""
    last_interaction_time: Optional[datetime] = None
    hours_since_interaction: float = 0.0
    current_likely_activity: str = "unknown"
    current_mood: str = "unknown"
    mood_intensity: float = 0.0
    active_topics: List[str] = field(default_factory=list)
    active_goals: List[str] = field(default_factory=list)
    session_topics: List[str] = field(default_factory=list)
    energy_level: str = "medium"  # high / medium / low
    captured_at: Optional[datetime] = None

    def to_dict(self) -> Dict[str, Any]:
        d = asdict(self)
        for k, v in d.items():
            if isinstance(v, datetime):
                d[k] = v.isoformat() if v else None
        return d

    def format_display(self) -> str:
        lines = [
            "👤 David Context:",
            f"   Activity: {self.current_likely_activity}",
            f"   Mood: {self.current_mood} ({self.mood_intensity:.0f}/10)",
            f"   Energy: {self.energy_level}",
            f"   Last interaction: {self.hours_since_interaction:.1f}h ago",
        ]
        if self.active_topics:
            lines.append(f"   Topics (4h): {', '.join(self.active_topics[:5])}")
        if self.active_goals:
            lines.append(f"   Goals: {', '.join(self.active_goals[:3])}")
        if self.session_topics:
            lines.append(f"   Session: {', '.join(self.session_topics[:3])}")
        return "\n".join(lines)


class DavidContextService(BaseDBService):
    """Captures David's current situational context from DB signals."""

    async def capture_context(self) -> DavidContext:
        """Build a DavidContext snapshot from DB. ~500ms, no LLM."""
        await self.connect()
        now = now_bangkok()
        ctx = DavidContext(captured_at=now)

        # 1. Last interaction time
        try:
            row = await self.db.fetchrow("""
                SELECT created_at FROM conversations
                WHERE speaker = 'david'
                ORDER BY created_at DESC LIMIT 1
            """)
            if row:
                ctx.last_interaction_time = row['created_at']
                delta = (now.replace(tzinfo=None) - row['created_at']).total_seconds() / 3600
                ctx.hours_since_interaction = round(max(0, delta), 2)
        except Exception as e:
            logger.debug("Last interaction query failed: %s", e)

        # 2. Current mood from emotional_states
        try:
            mood_row = await self.db.fetchrow("""
                SELECT emotion_note, happiness, anxiety, motivation, confidence
                FROM emotional_states
                WHERE created_at > NOW() - INTERVAL '12 hours'
                ORDER BY created_at DESC LIMIT 1
            """)
            if mood_row:
                ctx.current_mood = mood_row['emotion_note'] or 'neutral'
                # Intensity from available dimensions
                vals = [v for v in [mood_row.get('happiness'), mood_row.get('anxiety'),
                                    mood_row.get('motivation'), mood_row.get('confidence')]
                        if v is not None]
                ctx.mood_intensity = round(sum(vals) / max(len(vals), 1), 1)
        except Exception as e:
            logger.debug("Mood query failed: %s", e)

        # 3. Active topics (last 4h conversations)
        try:
            topics = await self.db.fetch("""
                SELECT DISTINCT topic FROM conversations
                WHERE topic IS NOT NULL AND topic != ''
                AND created_at > NOW() - INTERVAL '4 hours'
                ORDER BY topic
                LIMIT 10
            """)
            ctx.active_topics = [r['topic'] for r in topics]
        except Exception as e:
            logger.debug("Topics query failed: %s", e)

        # 4. Active goals from angela_desires
        try:
            goals = await self.db.fetch("""
                SELECT content FROM angela_desires
                WHERE is_active = TRUE
                ORDER BY priority DESC
                LIMIT 5
            """)
            ctx.active_goals = [r['content'][:80] for r in goals]
        except Exception as e:
            logger.debug("Goals query failed: %s", e)

        # 5. Session topics from active_session_context
        try:
            sessions = await self.db.fetch("""
                SELECT topic FROM active_session_context
                WHERE created_at > NOW() - INTERVAL '8 hours'
                ORDER BY created_at DESC
                LIMIT 5
            """)
            ctx.session_topics = [r['topic'] for r in sessions]
        except Exception as e:
            logger.debug("Session topics query failed: %s", e)

        # 6. Infer activity from time + calendar + gap
        ctx.current_likely_activity = self._infer_activity(
            now.hour, ctx.hours_since_interaction, ctx.current_mood,
        )

        # 7. Infer energy level
        ctx.energy_level = self._infer_energy(
            now.hour, ctx.current_mood, ctx.hours_since_interaction,
        )

        return ctx

    @staticmethod
    def _infer_activity(hour: int, hours_gap: float, mood: str) -> str:
        """Infer David's likely activity from time + interaction gap."""
        if hours_gap < 0.5:
            return "chatting_with_angela"
        if hour < 6:
            return "sleeping"
        if 6 <= hour < 9:
            return "morning_routine"
        if 9 <= hour < 12:
            return "working_morning"
        if 12 <= hour < 13:
            return "lunch_break"
        if 13 <= hour < 17:
            return "working_afternoon"
        if 17 <= hour < 20:
            return "evening_relaxing"
        if 20 <= hour < 23:
            return "evening_leisure"
        return "late_night"

    @staticmethod
    def _infer_energy(hour: int, mood: str, hours_gap: float) -> str:
        """Infer energy level from time + mood + gap."""
        mood_lower = (mood or '').lower()
        # Low energy indicators
        if mood_lower in ('tired', 'exhausted', 'sad', 'lonely'):
            return "low"
        if hour >= 23 or hour < 6:
            return "low"
        # High energy indicators
        if mood_lower in ('excited', 'happy', 'energetic', 'motivated'):
            return "high"
        if 9 <= hour <= 11:
            return "high"
        return "medium"
