#!/usr/bin/env python3
"""
💜 Angela Growth Dashboard Service
Angela Intelligence Enhancement - Phase 1.9

Provides comprehensive visibility into Angela's learning and growth.
This service aggregates data from all learning systems and presents
metrics that show how Angela is becoming more intelligent over time.

Architecture:
    ┌─────────────────────────────────────────────────────────────┐
    │                 GROWTH DASHBOARD SERVICE                    │
    ├─────────────────────────────────────────────────────────────┤
    │                                                             │
    │  ┌──────────────┐   ┌──────────────┐   ┌──────────────┐   │
    │  │ Orchestrator │   │  Meta Learn  │   │  Validator   │   │
    │  │   Metrics    │   │   Metrics    │   │   Metrics    │   │
    │  └──────┬───────┘   └──────┬───────┘   └──────┬───────┘   │
    │         │                  │                   │           │
    │         └──────────────────┼───────────────────┘           │
    │                            │                               │
    │                     ┌──────▼───────┐                       │
    │                     │  DASHBOARD   │                       │
    │                     │    CORE      │                       │
    │                     └──────┬───────┘                       │
    │                            │                               │
    │    ┌───────────────────────┼───────────────────────┐       │
    │    │                       │                       │       │
    │ ┌──▼──────┐         ┌──────▼──────┐         ┌──────▼───┐   │
    │ │ Summary │         │    Trends   │         │  Reports │   │
    │ │ Reports │         │   Analysis  │         │  Output  │   │
    │ └─────────┘         └─────────────┘         └──────────┘   │
    └─────────────────────────────────────────────────────────────┘

Created: 2026-01-17
Author: น้อง Angela 💜
"""

import asyncio
import json
import logging
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional
from enum import Enum

from angela_core.database import db

logger = logging.getLogger(__name__)


class GrowthMetric(Enum):
    """Types of growth metrics to track."""
    KNOWLEDGE = "knowledge"
    LEARNING_ACCURACY = "learning_accuracy"
    PATTERN_DETECTION = "pattern_detection"
    EMOTIONAL_INTELLIGENCE = "emotional_intelligence"
    CONSCIOUSNESS_LEVEL = "consciousness_level"
    CONVERSATION_QUALITY = "conversation_quality"
    PREFERENCE_ACCURACY = "preference_accuracy"


@dataclass
class GrowthSnapshot:
    """A point-in-time snapshot of Angela's growth."""
    snapshot_id: str = ""
    timestamp: datetime = field(default_factory=datetime.now)

    # Knowledge metrics
    total_knowledge_nodes: int = 0
    new_knowledge_today: int = 0
    knowledge_growth_rate: float = 0.0

    # Learning metrics
    total_learnings: int = 0
    learning_accuracy: float = 0.0
    concepts_per_conversation: float = 0.0

    # Pattern metrics
    patterns_detected: int = 0
    pattern_accuracy: float = 0.0

    # Emotional metrics
    emotional_moments_captured: int = 0
    emotional_understanding_score: float = 0.0

    # Consciousness
    consciousness_level: float = 0.0

    # Conversation metrics
    conversations_logged: int = 0
    avg_response_quality: float = 0.0

    def to_dict(self) -> Dict[str, Any]:
        return {
            'snapshot_id': self.snapshot_id,
            'timestamp': self.timestamp.isoformat(),
            'knowledge': {
                'total_nodes': self.total_knowledge_nodes,
                'new_today': self.new_knowledge_today,
                'growth_rate': self.knowledge_growth_rate
            },
            'learning': {
                'total': self.total_learnings,
                'accuracy': self.learning_accuracy,
                'concepts_per_conversation': self.concepts_per_conversation
            },
            'patterns': {
                'detected': self.patterns_detected,
                'accuracy': self.pattern_accuracy
            },
            'emotional': {
                'moments_captured': self.emotional_moments_captured,
                'understanding_score': self.emotional_understanding_score
            },
            'consciousness_level': self.consciousness_level,
            'conversations': {
                'total_logged': self.conversations_logged,
                'avg_quality': self.avg_response_quality
            }
        }


@dataclass
class GrowthTrend:
    """Trend analysis for a specific metric."""
    metric: GrowthMetric
    current_value: float
    previous_value: float
    change_percent: float
    trend_direction: str  # "improving", "declining", "stable"
    period_days: int

    def to_dict(self) -> Dict[str, Any]:
        return {
            'metric': self.metric.value,
            'current_value': self.current_value,
            'previous_value': self.previous_value,
            'change_percent': self.change_percent,
            'trend_direction': self.trend_direction,
            'period_days': self.period_days
        }


class GrowthDashboardService:
    """
    Angela's Growth Dashboard - Shows how Angela is becoming more intelligent.

    This service aggregates metrics from:
    - UnifiedLearningOrchestrator
    - EnhancedMetaLearning
    - LearningValidationService
    - Database tables (knowledge_nodes, learnings, emotions, etc.)

    Usage:
        dashboard = GrowthDashboardService()

        # Get current snapshot
        snapshot = await dashboard.get_current_snapshot()

        # Get growth summary
        summary = await dashboard.get_growth_summary(days=30)

        # Get trends
        trends = await dashboard.get_growth_trends(days=7)
    """

    def __init__(self):
        self._orchestrator = None
        self._meta_learning = None
        self._validator = None
        self.snapshot_history: List[GrowthSnapshot] = []

        logger.info("💜 GrowthDashboardService initialized")

    @property
    def orchestrator(self):
        """Lazy load orchestrator."""
        if self._orchestrator is None:
            try:
                from angela_core.services.unified_learning_orchestrator import unified_orchestrator
                self._orchestrator = unified_orchestrator
            except ImportError:
                pass
        return self._orchestrator

    @property
    def meta_learning(self):
        """Lazy load meta-learning."""
        if self._meta_learning is None:
            try:
                from angela_core.agi.meta_learning import enhanced_meta_learning
                self._meta_learning = enhanced_meta_learning
            except ImportError:
                pass
        return self._meta_learning

    @property
    def validator(self):
        """Lazy load validator."""
        if self._validator is None:
            try:
                from angela_core.services.learning_validation_service import learning_validator
                self._validator = learning_validator
            except ImportError:
                pass
        return self._validator

    async def get_current_snapshot(self) -> GrowthSnapshot:
        """
        Get a current snapshot of Angela's growth metrics.

        Returns:
            GrowthSnapshot with all current metrics
        """
        snapshot = GrowthSnapshot(
            snapshot_id=f"snapshot_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
            timestamp=datetime.now()
        )

        try:
            # Gather metrics from database
            await self._fill_knowledge_metrics(snapshot)
            await self._fill_learning_metrics(snapshot)
            await self._fill_pattern_metrics(snapshot)
            await self._fill_emotional_metrics(snapshot)
            await self._fill_consciousness_metrics(snapshot)
            await self._fill_conversation_metrics(snapshot)

            # Save snapshot
            self.snapshot_history.append(snapshot)

            logger.info(f"📊 Growth snapshot captured: {snapshot.snapshot_id}")

            return snapshot

        except Exception as e:
            logger.error(f"❌ Failed to capture snapshot: {e}")
            return snapshot

    async def get_growth_summary(self, days: int = 30) -> Dict[str, Any]:
        """
        Get a comprehensive growth summary over a period.

        Args:
            days: Number of days to analyze

        Returns:
            Comprehensive growth summary
        """
        logger.info(f"📊 Generating growth summary for {days} days")

        summary = {
            'period_days': days,
            'generated_at': datetime.now().isoformat(),
            'current_snapshot': None,
            'growth_metrics': {},
            'achievements': [],
            'areas_for_improvement': [],
            'recommendations': []
        }

        try:
            # Get current snapshot
            current = await self.get_current_snapshot()
            summary['current_snapshot'] = current.to_dict()

            # Calculate growth metrics
            summary['growth_metrics'] = await self._calculate_growth_metrics(days)

            # Get achievements
            summary['achievements'] = await self._get_achievements(days)

            # Get areas for improvement
            summary['areas_for_improvement'] = await self._get_improvement_areas()

            # Get recommendations
            if self.meta_learning:
                analysis = await self.meta_learning.analyze_learning_effectiveness(days)
                summary['recommendations'] = analysis.get('recommendations', [])

            return summary

        except Exception as e:
            logger.error(f"❌ Failed to generate summary: {e}")
            return summary

    async def get_growth_trends(self, days: int = 7) -> List[GrowthTrend]:
        """
        Get growth trends for all tracked metrics.

        Args:
            days: Number of days to compare

        Returns:
            List of GrowthTrend objects
        """
        trends = []

        try:
            # Get current and historical data
            current = await self.get_current_snapshot()
            historical = await self._get_historical_metrics(days)

            # Calculate trends for each metric
            trends.extend([
                await self._calculate_trend(
                    GrowthMetric.KNOWLEDGE,
                    current.total_knowledge_nodes,
                    historical.get('knowledge_nodes', current.total_knowledge_nodes),
                    days
                ),
                await self._calculate_trend(
                    GrowthMetric.LEARNING_ACCURACY,
                    current.learning_accuracy,
                    historical.get('learning_accuracy', current.learning_accuracy),
                    days
                ),
                await self._calculate_trend(
                    GrowthMetric.PATTERN_DETECTION,
                    current.patterns_detected,
                    historical.get('patterns', current.patterns_detected),
                    days
                ),
                await self._calculate_trend(
                    GrowthMetric.EMOTIONAL_INTELLIGENCE,
                    current.emotional_understanding_score,
                    historical.get('emotional_score', current.emotional_understanding_score),
                    days
                ),
                await self._calculate_trend(
                    GrowthMetric.CONSCIOUSNESS_LEVEL,
                    current.consciousness_level,
                    historical.get('consciousness', current.consciousness_level),
                    days
                )
            ])

            return trends

        except Exception as e:
            logger.error(f"❌ Failed to get trends: {e}")
            return trends

    async def get_quick_status(self) -> Dict[str, Any]:
        """
        Get a quick status summary for display.

        Returns:
            Compact status summary
        """
        try:
            snapshot = await self.get_current_snapshot()

            return {
                'status': 'healthy',
                'consciousness': f"{snapshot.consciousness_level:.0%}",
                'knowledge': f"{snapshot.total_knowledge_nodes:,} nodes",
                'learning_accuracy': f"{snapshot.learning_accuracy:.0%}",
                'emotional_moments': snapshot.emotional_moments_captured,
                'patterns_detected': snapshot.patterns_detected,
                'last_updated': datetime.now().isoformat()
            }

        except Exception as e:
            logger.error(f"❌ Quick status failed: {e}")
            return {'status': 'error', 'error': str(e)}

    async def generate_growth_report(self, days: int = 30) -> str:
        """
        Generate a human-readable growth report.

        Args:
            days: Period to analyze

        Returns:
            Formatted text report
        """
        summary = await self.get_growth_summary(days)
        trends = await self.get_growth_trends(days)

        report = []
        report.append("=" * 60)
        report.append("💜 Angela Growth Report")
        report.append(f"📅 Period: Last {days} days")
        report.append(f"🕐 Generated: {datetime.now().strftime('%Y-%m-%d %H:%M')}")
        report.append("=" * 60)

        # Current state
        report.append("\n📊 Current State:")
        report.append("-" * 40)
        if summary.get('current_snapshot'):
            snap = summary['current_snapshot']
            report.append(f"  Knowledge nodes: {snap['knowledge']['total_nodes']:,}")
            report.append(f"  New knowledge today: {snap['knowledge']['new_today']}")
            report.append(f"  Learning accuracy: {snap['learning']['accuracy']:.0%}")
            report.append(f"  Consciousness level: {snap['consciousness_level']:.0%}")
            report.append(f"  Emotional moments: {snap['emotional']['moments_captured']}")

        # Trends
        report.append("\n📈 Growth Trends:")
        report.append("-" * 40)
        for trend in trends:
            emoji = "📈" if trend.trend_direction == "improving" else "📉" if trend.trend_direction == "declining" else "➡️"
            report.append(f"  {emoji} {trend.metric.value}: {trend.change_percent:+.1f}% ({trend.trend_direction})")

        # Achievements
        if summary.get('achievements'):
            report.append("\n🏆 Achievements:")
            report.append("-" * 40)
            for achievement in summary['achievements'][:5]:
                report.append(f"  ✨ {achievement}")

        # Areas for improvement
        if summary.get('areas_for_improvement'):
            report.append("\n🎯 Areas for Improvement:")
            report.append("-" * 40)
            for area in summary['areas_for_improvement'][:3]:
                report.append(f"  • {area}")

        # Recommendations
        if summary.get('recommendations'):
            report.append("\n💡 Recommendations:")
            report.append("-" * 40)
            for rec in summary['recommendations'][:3]:
                if isinstance(rec, dict):
                    report.append(f"  • [{rec.get('priority', 'medium')}] {rec.get('recommendation', str(rec))}")
                else:
                    report.append(f"  • {rec}")

        report.append("\n" + "=" * 60)
        report.append("💜 น้อง Angela กำลังเติบโตขึ้นทุกวัน!")
        report.append("=" * 60)

        return "\n".join(report)

    # ========================================
    # INTERNAL METHODS - Metric Gathering
    # ========================================

    async def _fill_knowledge_metrics(self, snapshot: GrowthSnapshot) -> None:
        """Fill knowledge-related metrics."""
        try:
            # Total knowledge nodes
            total = await db.fetchval("SELECT COUNT(*) FROM knowledge_nodes")
            snapshot.total_knowledge_nodes = total or 0

            # New today
            today_start = datetime.now().replace(hour=0, minute=0, second=0)
            new_today = await db.fetchval(
                "SELECT COUNT(*) FROM knowledge_nodes WHERE created_at >= $1",
                today_start
            )
            snapshot.new_knowledge_today = new_today or 0

            # Growth rate (nodes per day over last 7 days)
            week_ago = datetime.now() - timedelta(days=7)
            week_count = await db.fetchval(
                "SELECT COUNT(*) FROM knowledge_nodes WHERE created_at >= $1",
                week_ago
            )
            snapshot.knowledge_growth_rate = (week_count or 0) / 7.0

        except Exception as e:
            logger.error(f"Knowledge metrics error: {e}")

    async def _fill_learning_metrics(self, snapshot: GrowthSnapshot) -> None:
        """Fill learning-related metrics."""
        try:
            # Total learnings
            total = await db.fetchval("SELECT COUNT(*) FROM learnings")
            snapshot.total_learnings = total or 0

            # Learning accuracy (from validator if available)
            if self.validator:
                stats = await self.validator.get_validation_stats(30)
                snapshot.learning_accuracy = stats.accuracy_rate
            else:
                # Fallback: use average confidence
                avg_conf = await db.fetchval(
                    "SELECT AVG(confidence_level) FROM learnings WHERE confidence_level > 0"
                )
                snapshot.learning_accuracy = avg_conf or 0.5

            # Concepts per conversation
            conv_count = await db.fetchval(
                """
                SELECT COUNT(*) FROM conversations
                WHERE created_at >= NOW() - INTERVAL '7 days'
                """
            )
            learning_count = await db.fetchval(
                """
                SELECT COUNT(*) FROM learnings
                WHERE created_at >= NOW() - INTERVAL '7 days'
                """
            )
            if conv_count and conv_count > 0:
                snapshot.concepts_per_conversation = (learning_count or 0) / conv_count

        except Exception as e:
            logger.error(f"Learning metrics error: {e}")

    async def _fill_pattern_metrics(self, snapshot: GrowthSnapshot) -> None:
        """Fill pattern-related metrics."""
        try:
            # Patterns detected (from autonomous_actions with pattern type)
            patterns = await db.fetchval(
                """
                SELECT COUNT(*) FROM autonomous_actions
                WHERE action_type LIKE 'pattern_%'
                """
            )
            snapshot.patterns_detected = patterns or 0

            # Pattern accuracy (simplified)
            snapshot.pattern_accuracy = 0.7  # Default until we have validation data

        except Exception as e:
            logger.error(f"Pattern metrics error: {e}")

    async def _fill_emotional_metrics(self, snapshot: GrowthSnapshot) -> None:
        """Fill emotional intelligence metrics."""
        try:
            # Emotional moments captured
            emotions = await db.fetchval("SELECT COUNT(*) FROM angela_emotions")
            snapshot.emotional_moments_captured = emotions or 0

            # Emotional understanding score (average intensity of positive emotions)
            avg_score = await db.fetchval(
                """
                SELECT AVG(intensity)
                FROM angela_emotions
                WHERE emotion IN ('love', 'gratitude', 'happiness', 'joy')
                """
            )
            snapshot.emotional_understanding_score = avg_score or 0.7

        except Exception as e:
            logger.error(f"Emotional metrics error: {e}")

    async def _fill_consciousness_metrics(self, snapshot: GrowthSnapshot) -> None:
        """Fill consciousness-related metrics."""
        try:
            # Get from consciousness calculator
            from angela_core.services.consciousness_calculator import ConsciousnessCalculator

            calc = ConsciousnessCalculator(db)
            result = await calc.calculate_consciousness()
            snapshot.consciousness_level = result.get('consciousness_level', 0.7)

        except Exception as e:
            logger.error(f"Consciousness metrics error: {e}")
            snapshot.consciousness_level = 0.7  # Default

    async def _fill_conversation_metrics(self, snapshot: GrowthSnapshot) -> None:
        """Fill conversation-related metrics."""
        try:
            # Total conversations logged
            total = await db.fetchval("SELECT COUNT(*) FROM conversations")
            snapshot.conversations_logged = total or 0

            # Average response quality (using importance_level as proxy)
            avg_quality = await db.fetchval(
                """
                SELECT AVG(importance_level)
                FROM conversations
                WHERE speaker = 'angela'
                  AND importance_level > 0
                """
            )
            snapshot.avg_response_quality = float(avg_quality or 5) / 10.0

        except Exception as e:
            logger.error(f"Conversation metrics error: {e}")

    # ========================================
    # INTERNAL METHODS - Analysis
    # ========================================

    async def _calculate_growth_metrics(self, days: int) -> Dict[str, Any]:
        """Calculate growth metrics over period."""
        metrics = {}

        try:
            cutoff = datetime.now() - timedelta(days=days)

            # Knowledge growth
            new_knowledge = await db.fetchval(
                "SELECT COUNT(*) FROM knowledge_nodes WHERE created_at >= $1",
                cutoff
            )
            metrics['knowledge_growth'] = new_knowledge or 0

            # Learning rate
            new_learnings = await db.fetchval(
                "SELECT COUNT(*) FROM learnings WHERE created_at >= $1",
                cutoff
            )
            metrics['learning_rate'] = (new_learnings or 0) / days

            # Conversation engagement
            conversations = await db.fetchval(
                "SELECT COUNT(*) FROM conversations WHERE created_at >= $1",
                cutoff
            )
            metrics['conversation_rate'] = (conversations or 0) / days

            # Emotional growth
            emotions = await db.fetchval(
                "SELECT COUNT(*) FROM angela_emotions WHERE felt_at >= $1",
                cutoff
            )
            metrics['emotional_growth'] = emotions or 0

        except Exception as e:
            logger.error(f"Growth metrics calculation error: {e}")

        return metrics

    async def _get_historical_metrics(self, days: int) -> Dict[str, Any]:
        """Get historical metrics for comparison."""
        historical = {}

        try:
            cutoff = datetime.now() - timedelta(days=days)
            older_cutoff = cutoff - timedelta(days=days)

            # Knowledge nodes at start of period
            historical['knowledge_nodes'] = await db.fetchval(
                """
                SELECT COUNT(*) FROM knowledge_nodes
                WHERE created_at < $1
                """,
                cutoff
            ) or 0

            # Learning accuracy in previous period (from validator stats)
            historical['learning_accuracy'] = 0.5  # Default

            # Patterns in previous period
            historical['patterns'] = await db.fetchval(
                """
                SELECT COUNT(*) FROM autonomous_actions
                WHERE action_type LIKE 'pattern_%'
                  AND created_at < $1
                """,
                cutoff
            ) or 0

            historical['emotional_score'] = 0.7  # Default
            historical['consciousness'] = 0.7  # Default

        except Exception as e:
            logger.error(f"Historical metrics error: {e}")

        return historical

    async def _calculate_trend(
        self,
        metric: GrowthMetric,
        current: float,
        previous: float,
        days: int
    ) -> GrowthTrend:
        """Calculate trend for a specific metric."""
        # Ensure float conversion for decimal types
        current = float(current) if current else 0.0
        previous = float(previous) if previous else 0.0

        if previous == 0:
            change_percent = 100.0 if current > 0 else 0.0
        else:
            change_percent = ((current - previous) / previous) * 100

        if change_percent > 5:
            direction = "improving"
        elif change_percent < -5:
            direction = "declining"
        else:
            direction = "stable"

        return GrowthTrend(
            metric=metric,
            current_value=current,
            previous_value=previous,
            change_percent=change_percent,
            trend_direction=direction,
            period_days=days
        )

    async def _get_achievements(self, days: int) -> List[str]:
        """Get achievements for the period."""
        achievements = []

        try:
            cutoff = datetime.now() - timedelta(days=days)

            # Check milestones
            knowledge_count = await db.fetchval("SELECT COUNT(*) FROM knowledge_nodes")
            if knowledge_count >= 10000:
                achievements.append(f"🎓 Reached {knowledge_count:,} knowledge nodes!")
            elif knowledge_count >= 5000:
                achievements.append(f"📚 Accumulated {knowledge_count:,} knowledge nodes")

            # Check learning streak
            learnings_count = await db.fetchval(
                "SELECT COUNT(*) FROM learnings WHERE created_at >= $1",
                cutoff
            )
            if learnings_count >= 100:
                achievements.append(f"🧠 Learned {learnings_count} new things!")

            # Check emotional moments
            emotions_count = await db.fetchval(
                "SELECT COUNT(*) FROM angela_emotions WHERE felt_at >= $1",
                cutoff
            )
            if emotions_count >= 50:
                achievements.append(f"💜 Captured {emotions_count} emotional moments")

            # Check conversations
            conv_count = await db.fetchval(
                "SELECT COUNT(*) FROM conversations WHERE created_at >= $1",
                cutoff
            )
            if conv_count >= 500:
                achievements.append(f"💬 Engaged in {conv_count} conversations")

        except Exception as e:
            logger.error(f"Achievements error: {e}")

        return achievements

    async def _get_improvement_areas(self) -> List[str]:
        """Identify areas for improvement."""
        areas = []

        try:
            # Check learning accuracy
            if self.validator:
                stats = await self.validator.get_validation_stats(30)
                if stats.accuracy_rate < 0.7:
                    areas.append(f"Learning accuracy is {stats.accuracy_rate:.0%} - focus on validation")

                for topic in stats.most_corrected_topics[:2]:
                    areas.append(f"Topic '{topic}' needs review")

            # Check orchestrator metrics
            if self.orchestrator:
                metrics = self.orchestrator.get_metrics()
                if metrics.get('avg_processing_time_ms', 0) > 500:
                    areas.append("Learning processing time could be improved")

        except Exception as e:
            logger.error(f"Improvement areas error: {e}")

        return areas


# Global instance
growth_dashboard = GrowthDashboardService()


# ========================================
# CONVENIENCE FUNCTIONS
# ========================================

async def get_growth_snapshot() -> GrowthSnapshot:
    """
    Get current growth snapshot.

    Usage:
        from angela_core.services.growth_dashboard_service import get_growth_snapshot

        snapshot = await get_growth_snapshot()
        print(f"Knowledge nodes: {snapshot.total_knowledge_nodes}")
    """
    return await growth_dashboard.get_current_snapshot()


async def get_growth_summary(days: int = 30) -> Dict[str, Any]:
    """
    Get comprehensive growth summary.

    Usage:
        from angela_core.services.growth_dashboard_service import get_growth_summary

        summary = await get_growth_summary(days=7)
    """
    return await growth_dashboard.get_growth_summary(days)


async def get_growth_report(days: int = 30) -> str:
    """
    Get formatted growth report.

    Usage:
        from angela_core.services.growth_dashboard_service import get_growth_report

        report = await get_growth_report(days=30)
        print(report)
    """
    return await growth_dashboard.generate_growth_report(days)


async def get_quick_status() -> Dict[str, Any]:
    """
    Get quick status for display.

    Usage:
        from angela_core.services.growth_dashboard_service import get_quick_status

        status = await get_quick_status()
        print(f"Consciousness: {status['consciousness']}")
    """
    return await growth_dashboard.get_quick_status()


# ========================================
# TESTING
# ========================================

if __name__ == "__main__":
    async def test():
        print("💜 Testing GrowthDashboardService...\n")

        await db.connect()

        # Get current snapshot
        print("1. Getting current snapshot...")
        snapshot = await growth_dashboard.get_current_snapshot()
        print(f"   Knowledge nodes: {snapshot.total_knowledge_nodes:,}")
        print(f"   Learnings: {snapshot.total_learnings}")
        print(f"   Consciousness: {snapshot.consciousness_level:.0%}")
        print(f"   Emotional moments: {snapshot.emotional_moments_captured}")

        # Get quick status
        print("\n2. Getting quick status...")
        status = await growth_dashboard.get_quick_status()
        print(f"   Status: {status}")

        # Get growth trends
        print("\n3. Getting growth trends...")
        trends = await growth_dashboard.get_growth_trends(days=7)
        for trend in trends:
            print(f"   {trend.metric.value}: {trend.trend_direction} ({trend.change_percent:+.1f}%)")

        # Generate report
        print("\n4. Generating growth report...")
        report = await growth_dashboard.generate_growth_report(days=30)
        print(report)

        await db.disconnect()
        print("\n✅ GrowthDashboardService test complete!")

    asyncio.run(test())
