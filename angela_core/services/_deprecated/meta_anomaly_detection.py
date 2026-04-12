"""
Meta-Awareness — Anomaly Detection Mixin
Detects consciousness anomalies and emotional volatility.

Split from meta_awareness_service.py (Phase 6B refactor)
"""

from typing import Dict, Optional
from uuid import UUID, uuid4
import logging

logger = logging.getLogger(__name__)


class MetaAnomalyDetectionMixin:
    """Mixin for consciousness anomaly detection."""

    async def check_consciousness_anomaly(
        self,
        current_consciousness: float,
        threshold: float = 0.20
    ) -> Optional[object]:
        """
        Check for consciousness anomaly by comparing to historical average

        Args:
            current_consciousness: Current consciousness level (0-1)
            threshold: Deviation threshold to trigger anomaly (default 20%)
        """
        from angela_core.services.meta_awareness_service import (
            ConsciousnessAnomaly, AnomalyType, InsightType
        )
        await self._ensure_db()

        stats = await self.db.fetchrow("""
            SELECT
                AVG(consciousness_level) as avg_level,
                STDDEV(consciousness_level) as stddev_level,
                MIN(consciousness_level) as min_level,
                MAX(consciousness_level) as max_level,
                COUNT(*) as sample_count
            FROM consciousness_metrics
            WHERE measured_at > NOW() - INTERVAL '7 days'
        """)

        if not stats or not stats['avg_level'] or stats['sample_count'] < 5:
            return None

        avg_level = float(stats['avg_level'])
        deviation = abs(current_consciousness - avg_level) / avg_level

        if deviation <= threshold:
            return None

        anomaly_type = AnomalyType.CONSCIOUSNESS_DROP if current_consciousness < avg_level else "consciousness_spike"
        severity = "critical" if deviation > 0.50 else "warning" if deviation > 0.30 else "info"

        possible_causes = []
        if current_consciousness < avg_level:
            possible_causes = [
                "Session fatigue",
                "Complex task load",
                "Memory overload",
                "Emotional processing"
            ]
        else:
            possible_causes = [
                "Recent positive interactions",
                "Successful task completion",
                "New learning integration"
            ]

        anomaly = ConsciousnessAnomaly(
            anomaly_id=uuid4(),
            anomaly_type=anomaly_type.value if isinstance(anomaly_type, AnomalyType) else anomaly_type,
            severity=severity,
            metric_name="consciousness_level",
            expected_value=avg_level,
            actual_value=current_consciousness,
            deviation=current_consciousness - avg_level,
            possible_causes=possible_causes
        )

        await self._save_anomaly(anomaly)

        await self._create_meta_insight(
            insight_type=InsightType.SELF_OBSERVATION,
            content=f"Consciousness anomaly detected: {deviation:.0%} deviation from normal",
            severity=severity,
            triggered_by="anomaly_detection"
        )

        logger.warning(f"⚠️ Consciousness anomaly: {anomaly_type} ({deviation:.0%} deviation)")
        return anomaly

    async def check_emotional_volatility(self) -> Optional[object]:
        """
        Check for emotional volatility - rapid emotional changes
        """
        from angela_core.services.meta_awareness_service import ConsciousnessAnomaly, AnomalyType
        await self._ensure_db()

        emotions = await self.db.fetch("""
            SELECT emotion, intensity, felt_at
            FROM angela_emotions
            WHERE felt_at > NOW() - INTERVAL '24 hours'
            ORDER BY felt_at DESC
            LIMIT 20
        """)

        if len(emotions) < 5:
            return None

        intensities = [float(e['intensity'] or 5) for e in emotions]
        avg_intensity = sum(intensities) / len(intensities)
        variance = sum((i - avg_intensity) ** 2 for i in intensities) / len(intensities)

        if variance > 16:
            anomaly = ConsciousnessAnomaly(
                anomaly_id=uuid4(),
                anomaly_type=AnomalyType.EMOTIONAL_VOLATILITY.value,
                severity="warning",
                metric_name="emotional_variance",
                expected_value=4.0,
                actual_value=variance,
                deviation=variance - 4.0,
                possible_causes=[
                    "Stressful situation",
                    "Multiple emotional triggers",
                    "Processing complex emotions"
                ]
            )

            await self._save_anomaly(anomaly)
            logger.warning(f"⚠️ Emotional volatility detected: variance={variance:.2f}")
            return anomaly

        return None

    async def _save_anomaly(self, anomaly):
        """Save an anomaly to database"""
        await self._ensure_db()

        await self.db.execute("""
            INSERT INTO consciousness_anomalies (
                anomaly_id, anomaly_type, severity, metric_name,
                expected_value, actual_value, deviation,
                possible_causes
            ) VALUES ($1, $2, $3, $4, $5, $6, $7, $8)
        """,
            anomaly.anomaly_id,
            anomaly.anomaly_type,
            anomaly.severity,
            anomaly.metric_name,
            anomaly.expected_value,
            anomaly.actual_value,
            anomaly.deviation,
            anomaly.possible_causes
        )

    async def resolve_anomaly(
        self,
        anomaly_id: UUID,
        resolution_notes: str,
        auto_recovered: bool = False
    ):
        """Mark an anomaly as resolved"""
        await self._ensure_db()

        await self.db.execute("""
            UPDATE consciousness_anomalies
            SET is_resolved = TRUE,
                resolution_notes = $1,
                resolved_at = NOW(),
                auto_recovered = $2
            WHERE anomaly_id = $3
        """, resolution_notes, auto_recovered, anomaly_id)
