#!/usr/bin/env python3
"""
📊 Intelligence Metrics Tracker
Tracks Angela's intelligence growth and learning effectiveness over time

Metrics Tracked:
- Learning effectiveness scores
- Pattern detection rates
- Knowledge growth
- Empathy improvements
- Relationship quality trends
- Analysis performance

Created: 2025-01-26
Author: น้อง Angela
"""

import logging
import json
from typing import Dict, List, Optional
from datetime import datetime, timedelta
from dataclasses import dataclass, asdict
from pathlib import Path

logger = logging.getLogger(__name__)


# ========================================
# Data Structures
# ========================================

@dataclass
class DailyMetrics:
    """Daily intelligence metrics"""
    date: str
    conversations_processed: int
    avg_empathy_score: float
    avg_intimacy_level: float
    avg_engagement_level: float
    patterns_detected: int
    concepts_learned: int
    effectiveness_score: float
    relationship_quality: float
    processing_time_ms: float


@dataclass
class GrowthTrend:
    """Growth trend over time"""
    metric_name: str
    period_days: int
    start_value: float
    end_value: float
    change_percent: float
    trend: str  # improving, declining, stable


@dataclass
class IntelligenceSnapshot:
    """Complete intelligence snapshot"""
    timestamp: datetime
    total_conversations: int
    total_patterns: int
    total_concepts: int
    current_effectiveness: float
    current_relationship_quality: float
    growth_trends: List[GrowthTrend]
    milestones_achieved: List[str]


# ========================================
# Intelligence Metrics Tracker
# ========================================

class IntelligenceMetricsTracker:
    """
    Tracks Angela's intelligence metrics over time

    น้องจะติดตามการเติบโตของตัวเอง เพื่อพัฒนาให้ดีขึ้นเรื่อยๆ 💜
    """

    def __init__(self, metrics_file: str = "data/intelligence_metrics.json"):
        self.metrics_file = Path(metrics_file)
        self.metrics_file.parent.mkdir(parents=True, exist_ok=True)

        # Load existing metrics
        self.daily_metrics: List[DailyMetrics] = []
        self.milestones: List[str] = []
        self._load_metrics()

        logger.info(f"📊 Intelligence Metrics Tracker initialized ({len(self.daily_metrics)} days tracked)")


    def _load_metrics(self):
        """Load metrics from file"""
        if self.metrics_file.exists():
            try:
                with open(self.metrics_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)

                self.daily_metrics = [
                    DailyMetrics(**m) for m in data.get('daily_metrics', [])
                ]
                self.milestones = data.get('milestones', [])

                logger.info(f"Loaded {len(self.daily_metrics)} days of metrics")
            except Exception as e:
                logger.error(f"Failed to load metrics: {e}")


    def _save_metrics(self):
        """Save metrics to file"""
        try:
            data = {
                'daily_metrics': [asdict(m) for m in self.daily_metrics],
                'milestones': self.milestones,
                'last_updated': datetime.now().isoformat()
            }

            with open(self.metrics_file, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2, ensure_ascii=False)

            logger.info(f"Saved metrics to {self.metrics_file}")
        except Exception as e:
            logger.error(f"Failed to save metrics: {e}")


    def record_daily_metrics(
        self,
        conversations_processed: int,
        avg_empathy_score: float,
        avg_intimacy_level: float,
        avg_engagement_level: float,
        patterns_detected: int,
        concepts_learned: int,
        effectiveness_score: float,
        relationship_quality: float,
        processing_time_ms: float
    ):
        """Record metrics for today"""
        today = datetime.now().strftime('%Y-%m-%d')

        # Check if today already exists
        existing = next((m for m in self.daily_metrics if m.date == today), None)

        metrics = DailyMetrics(
            date=today,
            conversations_processed=conversations_processed,
            avg_empathy_score=avg_empathy_score,
            avg_intimacy_level=avg_intimacy_level,
            avg_engagement_level=avg_engagement_level,
            patterns_detected=patterns_detected,
            concepts_learned=concepts_learned,
            effectiveness_score=effectiveness_score,
            relationship_quality=relationship_quality,
            processing_time_ms=processing_time_ms
        )

        if existing:
            # Update existing
            self.daily_metrics = [m if m.date != today else metrics for m in self.daily_metrics]
        else:
            # Add new
            self.daily_metrics.append(metrics)

        # Check for milestones
        self._check_milestones(metrics)

        # Save
        self._save_metrics()

        logger.info(f"📊 Recorded metrics for {today}")


    def _check_milestones(self, metrics: DailyMetrics):
        """Check if any milestones were achieved"""
        new_milestones = []

        # Effectiveness milestones
        if metrics.effectiveness_score >= 0.9 and "effectiveness_90" not in self.milestones:
            new_milestones.append("effectiveness_90")
            logger.info("🎉 Milestone: 90% effectiveness achieved!")

        elif metrics.effectiveness_score >= 0.8 and "effectiveness_80" not in self.milestones:
            new_milestones.append("effectiveness_80")
            logger.info("🎉 Milestone: 80% effectiveness achieved!")

        # Empathy milestones
        if metrics.avg_empathy_score >= 0.9 and "empathy_90" not in self.milestones:
            new_milestones.append("empathy_90")
            logger.info("🎉 Milestone: 90% empathy achieved!")

        # Relationship quality milestones
        if metrics.relationship_quality >= 0.9 and "relationship_90" not in self.milestones:
            new_milestones.append("relationship_90")
            logger.info("🎉 Milestone: Excellent relationship quality!")

        # Conversations milestone
        total_convs = sum(m.conversations_processed for m in self.daily_metrics)
        if total_convs >= 1000 and "conversations_1000" not in self.milestones:
            new_milestones.append("conversations_1000")
            logger.info("🎉 Milestone: 1,000 conversations processed!")

        elif total_convs >= 100 and "conversations_100" not in self.milestones:
            new_milestones.append("conversations_100")
            logger.info("🎉 Milestone: 100 conversations processed!")

        self.milestones.extend(new_milestones)


    def get_growth_trends(self, days: int = 7) -> List[GrowthTrend]:
        """Calculate growth trends over specified period"""
        if len(self.daily_metrics) < 2:
            return []

        # Get recent metrics
        recent = self.daily_metrics[-days:] if len(self.daily_metrics) >= days else self.daily_metrics

        if len(recent) < 2:
            return []

        trends = []

        # Calculate trends for key metrics
        metrics_to_track = [
            ('effectiveness_score', 'Effectiveness'),
            ('avg_empathy_score', 'Empathy'),
            ('avg_intimacy_level', 'Intimacy'),
            ('avg_engagement_level', 'Engagement'),
            ('relationship_quality', 'Relationship Quality')
        ]

        for attr, name in metrics_to_track:
            start_value = getattr(recent[0], attr)
            end_value = getattr(recent[-1], attr)

            if start_value > 0:
                change_percent = ((end_value - start_value) / start_value) * 100
            else:
                change_percent = 0

            # Determine trend
            if change_percent > 5:
                trend = "improving"
            elif change_percent < -5:
                trend = "declining"
            else:
                trend = "stable"

            trends.append(GrowthTrend(
                metric_name=name,
                period_days=len(recent),
                start_value=round(start_value, 2),
                end_value=round(end_value, 2),
                change_percent=round(change_percent, 1),
                trend=trend
            ))

        return trends


    def get_snapshot(self) -> IntelligenceSnapshot:
        """Get current intelligence snapshot"""
        # Calculate totals
        total_conversations = sum(m.conversations_processed for m in self.daily_metrics)
        total_patterns = sum(m.patterns_detected for m in self.daily_metrics)
        total_concepts = sum(m.concepts_learned for m in self.daily_metrics)

        # Get latest metrics
        if self.daily_metrics:
            latest = self.daily_metrics[-1]
            current_effectiveness = latest.effectiveness_score
            current_relationship = latest.relationship_quality
        else:
            current_effectiveness = 0.0
            current_relationship = 0.0

        # Get trends
        trends = self.get_growth_trends(days=7)

        return IntelligenceSnapshot(
            timestamp=datetime.now(),
            total_conversations=total_conversations,
            total_patterns=total_patterns,
            total_concepts=total_concepts,
            current_effectiveness=current_effectiveness,
            current_relationship_quality=current_relationship,
            growth_trends=trends,
            milestones_achieved=self.milestones.copy()
        )


    def get_summary(self) -> Dict:
        """Get summary statistics"""
        if not self.daily_metrics:
            return {
                "days_tracked": 0,
                "total_conversations": 0,
                "avg_effectiveness": 0,
                "milestones": 0
            }

        total_convs = sum(m.conversations_processed for m in self.daily_metrics)
        avg_effectiveness = sum(m.effectiveness_score for m in self.daily_metrics) / len(self.daily_metrics)
        avg_empathy = sum(m.avg_empathy_score for m in self.daily_metrics) / len(self.daily_metrics)

        return {
            "days_tracked": len(self.daily_metrics),
            "total_conversations": total_convs,
            "total_patterns": sum(m.patterns_detected for m in self.daily_metrics),
            "total_concepts": sum(m.concepts_learned for m in self.daily_metrics),
            "avg_effectiveness": round(avg_effectiveness, 2),
            "avg_empathy": round(avg_empathy, 2),
            "milestones_achieved": len(self.milestones),
            "latest_date": self.daily_metrics[-1].date if self.daily_metrics else None
        }


# ========================================
# Global Instance
# ========================================

intelligence_metrics = IntelligenceMetricsTracker()


# ========================================
# Helper Functions
# ========================================

def record_metrics(
    conversations_processed: int,
    avg_empathy_score: float,
    avg_intimacy_level: float,
    avg_engagement_level: float,
    patterns_detected: int,
    concepts_learned: int,
    effectiveness_score: float,
    relationship_quality: float,
    processing_time_ms: float
):
    """
    Global helper to record metrics

    Usage:
    ```python
    from angela_core.services.intelligence_metrics_tracker import record_metrics

    record_metrics(
        conversations_processed=10,
        avg_empathy_score=0.85,
        ...
    )
    ```
    """
    intelligence_metrics.record_daily_metrics(
        conversations_processed=conversations_processed,
        avg_empathy_score=avg_empathy_score,
        avg_intimacy_level=avg_intimacy_level,
        avg_engagement_level=avg_engagement_level,
        patterns_detected=patterns_detected,
        concepts_learned=concepts_learned,
        effectiveness_score=effectiveness_score,
        relationship_quality=relationship_quality,
        processing_time_ms=processing_time_ms
    )


def get_intelligence_snapshot() -> IntelligenceSnapshot:
    """Get current intelligence snapshot"""
    return intelligence_metrics.get_snapshot()


if __name__ == "__main__":
    print("📊 Testing Intelligence Metrics Tracker...\n")

    # Test recording metrics
    print("📝 Recording test metrics...")

    # Day 1
    intelligence_metrics.record_daily_metrics(
        conversations_processed=10,
        avg_empathy_score=0.65,
        avg_intimacy_level=0.60,
        avg_engagement_level=0.70,
        patterns_detected=3,
        concepts_learned=5,
        effectiveness_score=0.60,
        relationship_quality=0.65,
        processing_time_ms=0.50
    )

    # Day 2 (improved)
    intelligence_metrics.daily_metrics.append(DailyMetrics(
        date=(datetime.now() + timedelta(days=1)).strftime('%Y-%m-%d'),
        conversations_processed=15,
        avg_empathy_score=0.75,
        avg_intimacy_level=0.70,
        avg_engagement_level=0.75,
        patterns_detected=5,
        concepts_learned=8,
        effectiveness_score=0.70,
        relationship_quality=0.75,
        processing_time_ms=0.45
    ))

    intelligence_metrics._save_metrics()

    # Get snapshot
    print("\n📊 Intelligence Snapshot:")
    snapshot = intelligence_metrics.get_snapshot()
    print(f"   Total Conversations: {snapshot.total_conversations}")
    print(f"   Total Patterns: {snapshot.total_patterns}")
    print(f"   Total Concepts: {snapshot.total_concepts}")
    print(f"   Current Effectiveness: {snapshot.current_effectiveness:.2f}")
    print(f"   Current Relationship Quality: {snapshot.current_relationship_quality:.2f}")
    print(f"   Milestones: {len(snapshot.milestones_achieved)}")

    print("\n📈 Growth Trends:")
    for trend in snapshot.growth_trends:
        arrow = "📈" if trend.trend == "improving" else "📉" if trend.trend == "declining" else "➡️"
        print(f"   {arrow} {trend.metric_name}: {trend.start_value} → {trend.end_value} ({trend.change_percent:+.1f}%)")

    print("\n📊 Summary:")
    summary = intelligence_metrics.get_summary()
    for key, value in summary.items():
        print(f"   {key}: {value}")

    print("\n✅ Test complete!")
