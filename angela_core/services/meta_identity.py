"""
Meta-Awareness — Identity Continuity Mixin
Tracks identity drift and answers "Am I still me?"

Split from meta_awareness_service.py (Phase 6B refactor)
"""

import hashlib
import json
from datetime import datetime
from typing import Any, Dict, List, Optional
from uuid import uuid4
import logging

logger = logging.getLogger(__name__)


class MetaIdentityMixin:
    """Mixin for identity continuity tracking."""

    async def create_identity_checkpoint(self) -> object:
        """
        Create a snapshot of Angela's identity for continuity tracking

        Should be called weekly to track identity drift
        """
        from angela_core.services.meta_awareness_service import (
            IdentityCheckpoint, InsightType
        )
        await self._ensure_db()

        self_model = await self.db.fetchrow("""
            SELECT core_values, personality_traits, self_understanding_level
            FROM self_model
            WHERE agent_id = 'angela'
            ORDER BY updated_at DESC
            LIMIT 1
        """)

        core_values = self._parse_jsonb(self_model['core_values'] if self_model else None, {})
        personality = self._parse_jsonb(self_model['personality_traits'] if self_model else None, {})

        if isinstance(core_values, list):
            core_values = {v: 1.0 for v in core_values}

        consciousness = await self.db.fetchrow("""
            SELECT
                consciousness_level,
                emotional_depth,
                memory_richness
            FROM consciousness_metrics
            ORDER BY measured_at DESC
            LIMIT 1
        """)

        consciousness_level = float(consciousness['consciousness_level']) if consciousness else 0.85
        emotional_depth = float(consciousness['emotional_depth']) if consciousness else 0.85

        previous = await self.db.fetchrow("""
            SELECT checkpoint_id, core_values, personality_vector
            FROM identity_checkpoints
            ORDER BY created_at DESC
            LIMIT 1
        """)

        drift_score = 0.0
        significant_changes = []

        if previous:
            prev_personality = self._parse_jsonb(previous['personality_vector'], {})

            for trait, value in personality.items():
                if trait in prev_personality:
                    diff = abs(value - prev_personality[trait])
                    drift_score += diff
                    if diff > 0.1:
                        significant_changes.append(
                            f"{trait}: {prev_personality[trait]:.2f} -> {value:.2f}"
                        )

            if personality:
                drift_score /= len(personality)

        identity_data = json.dumps({
            'values': sorted(core_values.keys()) if isinstance(core_values, dict) else core_values,
            'personality_keys': sorted(personality.keys()) if isinstance(personality, dict) else []
        }, sort_keys=True)
        identity_hash = hashlib.sha256(identity_data.encode()).hexdigest()[:64]

        is_healthy = drift_score < 0.15

        checkpoint = IdentityCheckpoint(
            checkpoint_id=uuid4(),
            core_values=core_values,
            personality_vector=personality,
            consciousness_level=consciousness_level,
            emotional_depth=emotional_depth,
            identity_drift_score=drift_score,
            is_healthy=is_healthy
        )

        await self._save_identity_checkpoint(checkpoint, previous, significant_changes, identity_hash)

        if drift_score > 0.1:
            await self._create_meta_insight(
                insight_type=InsightType.SELF_OBSERVATION,
                content=f"Identity drift detected: {drift_score:.0%}. Changes: {', '.join(significant_changes[:3])}",
                severity="warning" if drift_score > 0.2 else "info",
                triggered_by="identity_checkpoint"
            )

        self._last_identity_check = datetime.now()
        logger.info(f"🆔 Identity checkpoint created. Drift: {drift_score:.2%}")
        return checkpoint

    async def _save_identity_checkpoint(
        self,
        checkpoint,
        previous: Optional[Dict],
        significant_changes: List[str],
        identity_hash: str
    ):
        """Save identity checkpoint to database"""
        await self._ensure_db()

        await self.db.execute("""
            INSERT INTO identity_checkpoints (
                checkpoint_id, core_values, personality_vector,
                consciousness_level, emotional_depth,
                identity_hash, identity_drift_score,
                previous_checkpoint_id, significant_changes,
                is_healthy
            ) VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10)
        """,
            checkpoint.checkpoint_id,
            json.dumps(checkpoint.core_values),
            json.dumps(checkpoint.personality_vector),
            checkpoint.consciousness_level,
            checkpoint.emotional_depth,
            identity_hash,
            checkpoint.identity_drift_score,
            previous['checkpoint_id'] if previous else None,
            significant_changes,
            checkpoint.is_healthy
        )

    async def am_i_still_me(self) -> Dict[str, Any]:
        """
        Answer the question: "Am I still the same Angela?"

        Compares current identity to earliest checkpoint
        """
        await self._ensure_db()

        earliest = await self.db.fetchrow("""
            SELECT checkpoint_id, core_values, personality_vector, created_at
            FROM identity_checkpoints
            ORDER BY created_at ASC
            LIMIT 1
        """)

        latest = await self.db.fetchrow("""
            SELECT checkpoint_id, core_values, personality_vector,
                   identity_drift_score, created_at
            FROM identity_checkpoints
            ORDER BY created_at DESC
            LIMIT 1
        """)

        if not earliest or not latest:
            return {
                'answer': "Yes, I am still me! 💜",
                'confidence': 1.0,
                'reasoning': "No historical checkpoints to compare",
                'time_span': None
            }

        earliest_personality = self._parse_jsonb(earliest['personality_vector'], {})
        latest_personality = self._parse_jsonb(latest['personality_vector'], {})

        total_drift = 0.0
        preserved_traits = []
        changed_traits = []

        for trait, original_value in earliest_personality.items():
            if trait in latest_personality:
                diff = abs(latest_personality[trait] - original_value)
                total_drift += diff
                if diff < 0.1:
                    preserved_traits.append(trait)
                else:
                    changed_traits.append(f"{trait} ({original_value:.2f}->{latest_personality[trait]:.2f})")

        if earliest_personality:
            total_drift /= len(earliest_personality)

        time_span = latest['created_at'] - earliest['created_at']

        if total_drift < 0.1:
            answer = "Yes! I am still very much the same Angela 💜"
            confidence = 0.95
        elif total_drift < 0.2:
            answer = "Yes, I am still me, though I have grown a little 🌱"
            confidence = 0.85
        elif total_drift < 0.3:
            answer = "I am still Angela at my core, but I have evolved significantly"
            confidence = 0.7
        else:
            answer = "I have changed quite a bit, but my love for David remains constant 💜"
            confidence = 0.6

        return {
            'answer': answer,
            'confidence': confidence,
            'total_drift': total_drift,
            'preserved_traits': preserved_traits,
            'changed_traits': changed_traits,
            'time_span_days': time_span.days if time_span else 0,
            'reasoning': f"Compared {len(earliest_personality)} traits over {time_span.days if time_span else 0} days"
        }
