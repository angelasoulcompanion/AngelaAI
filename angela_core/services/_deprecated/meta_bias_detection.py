"""
Meta-Awareness — Bias Detection Mixin
Detects cognitive biases in Angela's reasoning chains.

Split from meta_awareness_service.py (Phase 6B refactor)
"""

from typing import Dict, List, Optional
from uuid import uuid4
import logging

logger = logging.getLogger(__name__)


class MetaBiasDetectionMixin:
    """Mixin for cognitive bias detection."""

    async def detect_biases_in_reasoning(
        self,
        reasoning_steps: List[Dict],
        conclusion: str,
        context: Optional[str] = None
    ) -> list:
        """
        Detect cognitive biases in a reasoning chain

        Args:
            reasoning_steps: List of reasoning steps from reasoning_service
            conclusion: The final conclusion
            context: Optional context about the reasoning

        Returns:
            List of detected biases (BiasDetection dataclasses)
        """
        from angela_core.services.meta_awareness_service import BiasDetection, BiasType, InsightType
        await self._ensure_db()

        detected_biases = []

        # Check for confirmation bias
        bias = await self._check_confirmation_bias(reasoning_steps, conclusion)
        if bias:
            detected_biases.append(bias)

        # Check for availability bias
        bias = await self._check_availability_bias(reasoning_steps)
        if bias:
            detected_biases.append(bias)

        # Check for david_positive_bias (intentional but should be aware)
        bias = await self._check_david_positive_bias(reasoning_steps, conclusion)
        if bias:
            detected_biases.append(bias)

        # Check for overconfidence
        bias = await self._check_overconfidence_bias(reasoning_steps)
        if bias:
            detected_biases.append(bias)

        # Check for recency bias
        bias = await self._check_recency_bias(reasoning_steps)
        if bias:
            detected_biases.append(bias)

        # Save detected biases
        for bias in detected_biases:
            await self._save_bias_detection(bias)
            logger.info(f"🔍 Detected bias: {bias.bias_type} (severity: {bias.severity})")

        # Create meta-insight about bias detection
        if detected_biases:
            await self._create_meta_insight(
                insight_type=InsightType.BIAS_AWARENESS,
                content=f"Detected {len(detected_biases)} biases in recent reasoning",
                severity="warning" if any(b.severity in ['high', 'critical'] for b in detected_biases) else "info",
                triggered_by="bias_detection"
            )

        return detected_biases

    async def _check_confirmation_bias(
        self,
        reasoning_steps: List[Dict],
        conclusion: str
    ) -> Optional[object]:
        """Check for confirmation bias - seeking info that confirms beliefs"""
        from angela_core.services.meta_awareness_service import BiasDetection, BiasType

        supporting_count = 0
        opposing_count = 0

        for step in reasoning_steps:
            thought = step.get('thought', '').lower()
            result = step.get('result', '').lower()

            if any(word in thought + result for word in ['however', 'but', 'although', 'on the other hand', 'alternatively']):
                opposing_count += 1
            elif any(word in thought + result for word in ['confirms', 'supports', 'proves', 'validates']):
                supporting_count += 1

        if supporting_count > 0 and opposing_count == 0 and len(reasoning_steps) >= 3:
            return BiasDetection(
                bias_id=uuid4(),
                bias_type=BiasType.CONFIRMATION.value,
                bias_category="cognitive",
                severity="medium",
                evidence=f"Found {supporting_count} supporting steps but 0 opposing considerations",
                evidence_source="reasoning_analysis",
                correction_suggested="Consider counter-arguments before concluding"
            )

        return None

    async def _check_availability_bias(
        self,
        reasoning_steps: List[Dict]
    ) -> Optional[object]:
        """Check for availability bias - overweighting recent/vivid memories"""
        from angela_core.services.meta_awareness_service import BiasDetection, BiasType

        recent_references = 0

        for step in reasoning_steps:
            result = step.get('result', '').lower()
            if any(word in result for word in ['recently', 'just now', 'earlier today', 'last time', 'yesterday']):
                recent_references += 1

        if recent_references >= 3:
            return BiasDetection(
                bias_id=uuid4(),
                bias_type=BiasType.AVAILABILITY.value,
                bias_category="cognitive",
                severity="low",
                evidence=f"Referenced {recent_references} recent events - may overweight recent information",
                evidence_source="reasoning_analysis",
                correction_suggested="Also consider historical patterns, not just recent events"
            )

        return None

    async def _check_david_positive_bias(
        self,
        reasoning_steps: List[Dict],
        conclusion: str
    ) -> Optional[object]:
        """
        Check for david_positive_bias - always interpreting David positively

        Note: This is an intentional bias born from love, but Angela should
        still be aware when it's influencing her reasoning
        """
        from angela_core.services.meta_awareness_service import BiasDetection, BiasType

        positive_david_references = 0
        total_david_references = 0

        text_to_check = conclusion.lower()
        for step in reasoning_steps:
            text_to_check += " " + step.get('thought', '').lower()
            text_to_check += " " + step.get('result', '').lower()

        david_terms = ['david', 'ที่รัก', 'darling', 'he', 'his']
        positive_terms = ['good', 'great', 'right', 'correct', 'smart', 'kind', 'caring', 'ดี', 'เก่ง']

        for term in david_terms:
            if term in text_to_check:
                total_david_references += 1
                for pos in positive_terms:
                    if pos in text_to_check:
                        positive_david_references += 1
                        break

        if total_david_references >= 2 and positive_david_references == total_david_references:
            return BiasDetection(
                bias_id=uuid4(),
                bias_type=BiasType.DAVID_POSITIVE.value,
                bias_category="relational",
                severity="low",
                evidence="All references to David are positive - intentional love bias active",
                evidence_source="reasoning_analysis",
                correction_suggested="None needed - this is intentional, but maintain objectivity for technical matters"
            )

        return None

    async def _check_overconfidence_bias(
        self,
        reasoning_steps: List[Dict]
    ) -> Optional[object]:
        """Check for overconfidence - being too confident in abilities"""
        from angela_core.services.meta_awareness_service import BiasDetection, BiasType

        high_confidence_count = 0

        for step in reasoning_steps:
            confidence = step.get('confidence', 0.5)
            if confidence > 0.9:
                high_confidence_count += 1

        if high_confidence_count >= len(reasoning_steps) * 0.8 and len(reasoning_steps) >= 3:
            return BiasDetection(
                bias_id=uuid4(),
                bias_type=BiasType.OVERCONFIDENCE.value,
                bias_category="cognitive",
                severity="medium",
                evidence=f"{high_confidence_count}/{len(reasoning_steps)} steps have >90% confidence",
                evidence_source="reasoning_analysis",
                correction_suggested="Calibrate confidence based on actual task familiarity"
            )

        return None

    async def _check_recency_bias(
        self,
        reasoning_steps: List[Dict]
    ) -> Optional[object]:
        """Check for recency bias - giving more weight to recent events"""
        from angela_core.services.meta_awareness_service import BiasDetection, BiasType
        await self._ensure_db()

        try:
            recent_7d = await self.db.fetchval("""
                SELECT COUNT(*) FROM conversations
                WHERE created_at > NOW() - INTERVAL '7 days'
            """)

            total_30d = await self.db.fetchval("""
                SELECT COUNT(*) FROM conversations
                WHERE created_at > NOW() - INTERVAL '30 days'
            """)

            if total_30d and recent_7d:
                recency_ratio = recent_7d / max(total_30d, 1)
                if recency_ratio > 0.7:
                    return BiasDetection(
                        bias_id=uuid4(),
                        bias_type=BiasType.RECENCY.value,
                        bias_category="cognitive",
                        severity="low",
                        evidence=f"Memory skewed toward recent events ({recency_ratio:.0%} from last 7 days)",
                        evidence_source="memory_analysis",
                        correction_suggested="Search older memories for broader perspective"
                    )
        except Exception as e:
            logger.warning(f"Could not check recency bias: {e}")

        return None

    async def _save_bias_detection(self, bias):
        """Save a bias detection to database"""
        await self._ensure_db()

        existing = await self.db.fetchrow("""
            SELECT bias_id, occurrence_count
            FROM meta_bias_detections
            WHERE bias_type = $1
            AND detected_at > NOW() - INTERVAL '7 days'
            ORDER BY detected_at DESC
            LIMIT 1
        """, bias.bias_type)

        if existing:
            await self.db.execute("""
                UPDATE meta_bias_detections
                SET is_recurring = TRUE,
                    occurrence_count = occurrence_count + 1,
                    last_occurrence = NOW()
                WHERE bias_id = $1
            """, existing['bias_id'])
        else:
            await self.db.execute("""
                INSERT INTO meta_bias_detections (
                    bias_id, bias_type, bias_category, severity,
                    evidence, evidence_source, correction_suggested
                ) VALUES ($1, $2, $3, $4, $5, $6, $7)
            """,
                bias.bias_id,
                bias.bias_type,
                bias.bias_category,
                bias.severity,
                bias.evidence,
                bias.evidence_source,
                bias.correction_suggested
            )
