"""
Feedback Loop Service - Learning from Routing Decisions

Enables Analytics Agent to learn from past decisions and improve over time.

Functions:
1. Collect feedback on routing decisions
2. Analyze routing accuracy
3. Identify patterns in successful/failed routes
4. Generate insights for improvement
"""

import asyncio
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple
from uuid import UUID
import json
import statistics

from angela_core.database import get_db_connection


class FeedbackType:
    """Types of feedback."""
    CORRECT = "correct"           # Routing was correct
    INCORRECT = "incorrect"       # Should have gone to different tier
    SUBOPTIMAL = "suboptimal"    # Correct tier but could be better
    EXCELLENT = "excellent"       # Perfect routing decision


class FeedbackLoopService:
    """
    Collects and analyzes feedback on routing decisions.

    Learning workflow:
    1. User provides feedback on routing decision
    2. System analyzes what signals were strong/weak
    3. Identifies patterns in successful routes
    4. Generates recommendations for weight adjustments
    """

    def __init__(self):
        self.feedback_cache = {}

    async def add_feedback(self,
                          decision_id: UUID,
                          feedback_type: str,
                          correct_tier: str = None,
                          feedback_note: str = None,
                          feedback_score: float = None) -> Dict:
        """
        Add human feedback on a routing decision.

        Args:
            decision_id: UUID of analytics decision
            feedback_type: Type of feedback (correct/incorrect/suboptimal/excellent)
            correct_tier: What tier it should have been (if incorrect)
            feedback_note: Optional explanation
            feedback_score: Optional score 0.0-1.0

        Returns:
            Feedback result with insights
        """
        # Convert feedback type to score if not provided
        if feedback_score is None:
            feedback_score = self._feedback_type_to_score(feedback_type)

        # Update decision in database
        async with get_db_connection() as conn:
            # Get original decision
            decision = await conn.fetchrow("""
                SELECT
                    id, event_id, target_tier, composite_score,
                    confidence, signals
                FROM analytics_decisions
                WHERE id = $1
            """, decision_id)

            if not decision:
                return {'error': 'Decision not found'}

            # Update with feedback
            await conn.execute("""
                UPDATE analytics_decisions
                SET feedback_score = $2,
                    feedback_note = $3,
                    feedback_received_at = NOW()
                WHERE id = $1
            """, decision_id, feedback_score, feedback_note)

            # If incorrect, log what it should have been
            if feedback_type == FeedbackType.INCORRECT and correct_tier:
                await conn.execute("""
                    INSERT INTO routing_corrections (
                        id, decision_id, wrong_tier, correct_tier,
                        signals, created_at
                    ) VALUES (gen_random_uuid(), $1, $2, $3, $4, NOW())
                """,
                    decision_id,
                    decision['target_tier'],
                    correct_tier,
                    decision['signals']
                )

        # Analyze feedback
        insights = await self._analyze_feedback(decision, feedback_type, feedback_score)

        return {
            'decision_id': decision_id,
            'feedback_type': feedback_type,
            'feedback_score': feedback_score,
            'insights': insights,
            'timestamp': datetime.now()
        }

    async def _analyze_feedback(self,
                                decision: Dict,
                                feedback_type: str,
                                feedback_score: float) -> Dict:
        """
        Analyze feedback to generate insights.

        Returns insights about:
        - Which signals were strong/weak
        - Whether confidence matched outcome
        - Recommendations for improvement
        """
        signals = json.loads(decision['signals']) if isinstance(decision['signals'], str) else decision['signals']
        composite_score = float(decision['composite_score'])
        confidence = float(decision['confidence'])

        insights = {
            'signal_analysis': {},
            'confidence_match': None,
            'recommendations': []
        }

        # Analyze each signal
        for signal_name, signal_value in signals.items():
            if signal_name in ['emotional_intensity', 'urgency']:
                continue  # Skip modifiers

            signal_strength = "strong" if signal_value > 0.7 else "moderate" if signal_value > 0.4 else "weak"
            insights['signal_analysis'][signal_name] = {
                'value': signal_value,
                'strength': signal_strength
            }

        # Check if confidence matched outcome
        if feedback_score >= 0.8:
            # Good outcome
            if confidence >= 0.7:
                insights['confidence_match'] = "correct_and_confident"
                insights['recommendations'].append("Signals were well-calibrated")
            else:
                insights['confidence_match'] = "correct_but_uncertain"
                insights['recommendations'].append("Consider increasing weights for these signal combinations")
        else:
            # Poor outcome
            if confidence >= 0.7:
                insights['confidence_match'] = "incorrect_but_confident"
                insights['recommendations'].append("These signals led to overconfidence - review weights")
            else:
                insights['confidence_match'] = "incorrect_and_uncertain"
                insights['recommendations'].append("System correctly flagged uncertainty")

        # Specific recommendations based on feedback type
        if feedback_type == FeedbackType.INCORRECT:
            # Find which signals were misleading
            strong_signals = [name for name, data in insights['signal_analysis'].items()
                            if data['strength'] == 'strong']
            if strong_signals:
                insights['recommendations'].append(
                    f"Strong signals that may have misled: {', '.join(strong_signals)}"
                )

        elif feedback_type == FeedbackType.EXCELLENT:
            # Reinforce successful patterns
            insights['recommendations'].append(
                "This signal combination was excellent - reinforce these weights"
            )

        return insights

    def _feedback_type_to_score(self, feedback_type: str) -> float:
        """Convert feedback type to numeric score."""
        scores = {
            FeedbackType.EXCELLENT: 1.0,
            FeedbackType.CORRECT: 0.8,
            FeedbackType.SUBOPTIMAL: 0.6,
            FeedbackType.INCORRECT: 0.2
        }
        return scores.get(feedback_type, 0.5)

    async def get_routing_accuracy(self, lookback_days: int = 30) -> Dict:
        """
        Calculate overall routing accuracy based on feedback.

        Args:
            lookback_days: How far back to analyze

        Returns:
            Accuracy metrics and trends
        """
        async with get_db_connection() as conn:
            # Get decisions with feedback
            decisions = await conn.fetch("""
                SELECT
                    target_tier,
                    feedback_score,
                    confidence,
                    DATE(created_at) as decision_date
                FROM analytics_decisions
                WHERE feedback_score IS NOT NULL
                  AND created_at >= NOW() - INTERVAL '%s days'
                ORDER BY created_at DESC
            """ % lookback_days)

            if not decisions:
                return {
                    'overall_accuracy': 0.0,
                    'total_feedback': 0,
                    'message': 'No feedback data available yet'
                }

            # Calculate overall accuracy
            feedback_scores = [float(d['feedback_score']) for d in decisions]
            overall_accuracy = statistics.mean(feedback_scores)

            # Accuracy by tier
            tier_accuracy = {}
            for decision in decisions:
                tier = decision['target_tier']
                if tier not in tier_accuracy:
                    tier_accuracy[tier] = []
                tier_accuracy[tier].append(float(decision['feedback_score']))

            tier_stats = {
                tier: {
                    'accuracy': statistics.mean(scores),
                    'count': len(scores)
                }
                for tier, scores in tier_accuracy.items()
            }

            # Confidence calibration (does high confidence = good outcome?)
            high_confidence = [d for d in decisions if float(d['confidence']) >= 0.7]
            low_confidence = [d for d in decisions if float(d['confidence']) < 0.7]

            calibration = {
                'high_confidence': {
                    'count': len(high_confidence),
                    'avg_accuracy': statistics.mean([float(d['feedback_score']) for d in high_confidence]) if high_confidence else 0.0
                },
                'low_confidence': {
                    'count': len(low_confidence),
                    'avg_accuracy': statistics.mean([float(d['feedback_score']) for d in low_confidence]) if low_confidence else 0.0
                }
            }

            # Trend over time (improving or declining?)
            trend = self._calculate_trend(decisions)

            return {
                'overall_accuracy': overall_accuracy,
                'total_feedback': len(decisions),
                'tier_accuracy': tier_stats,
                'confidence_calibration': calibration,
                'trend': trend,
                'lookback_days': lookback_days
            }

    def _calculate_trend(self, decisions: List[Dict]) -> str:
        """Calculate if accuracy is improving, stable, or declining."""
        if len(decisions) < 10:
            return "insufficient_data"

        # Split into first half and second half
        mid = len(decisions) // 2
        first_half = [float(d['feedback_score']) for d in decisions[mid:]]  # Older
        second_half = [float(d['feedback_score']) for d in decisions[:mid]]  # Newer

        avg_first = statistics.mean(first_half)
        avg_second = statistics.mean(second_half)

        diff = avg_second - avg_first

        if diff > 0.05:
            return "improving"
        elif diff < -0.05:
            return "declining"
        else:
            return "stable"

    async def get_improvement_recommendations(self) -> List[Dict]:
        """
        Generate recommendations for improving routing accuracy.

        Analyzes:
        - Most common mistakes
        - Signals that often mislead
        - Tier-specific patterns
        """
        recommendations = []

        async with get_db_connection() as conn:
            # Find most common incorrect routes
            common_mistakes = await conn.fetch("""
                SELECT
                    wrong_tier,
                    correct_tier,
                    COUNT(*) as frequency
                FROM routing_corrections
                WHERE created_at >= NOW() - INTERVAL '30 days'
                GROUP BY wrong_tier, correct_tier
                HAVING COUNT(*) >= 3
                ORDER BY frequency DESC
                LIMIT 5
            """)

            for mistake in common_mistakes:
                recommendations.append({
                    'type': 'common_mistake',
                    'description': f"Often routes {mistake['wrong_tier']} when should be {mistake['correct_tier']}",
                    'frequency': mistake['frequency'],
                    'priority': 'high' if mistake['frequency'] >= 5 else 'medium'
                })

            # Find signals that correlate with poor outcomes
            poor_outcomes = await conn.fetch("""
                SELECT signals
                FROM analytics_decisions
                WHERE feedback_score < 0.5
                  AND created_at >= NOW() - INTERVAL '30 days'
                LIMIT 20
            """)

            if poor_outcomes:
                # Analyze signal patterns in poor outcomes
                signal_aggregates = {}
                for outcome in poor_outcomes:
                    signals = json.loads(outcome['signals']) if isinstance(outcome['signals'], str) else outcome['signals']
                    for signal_name, signal_value in signals.items():
                        if signal_name not in signal_aggregates:
                            signal_aggregates[signal_name] = []
                        signal_aggregates[signal_name].append(signal_value)

                # Find signals with high values in poor outcomes
                for signal_name, values in signal_aggregates.items():
                    avg_value = statistics.mean(values)
                    if avg_value > 0.7:
                        recommendations.append({
                            'type': 'misleading_signal',
                            'description': f"{signal_name} often high in poor outcomes (avg: {avg_value:.2f})",
                            'signal': signal_name,
                            'priority': 'high'
                        })

            # Check confidence calibration
            calibration_issues = await conn.fetch("""
                SELECT
                    CASE
                        WHEN confidence >= 0.7 AND feedback_score < 0.5 THEN 'overconfident'
                        WHEN confidence < 0.5 AND feedback_score >= 0.8 THEN 'underconfident'
                    END as issue,
                    COUNT(*) as count
                FROM analytics_decisions
                WHERE feedback_score IS NOT NULL
                  AND created_at >= NOW() - INTERVAL '30 days'
                GROUP BY issue
                HAVING issue IS NOT NULL
            """)

            for issue in calibration_issues:
                if issue['count'] >= 5:
                    recommendations.append({
                        'type': 'calibration_issue',
                        'description': f"System is {issue['issue']} in {issue['count']} cases",
                        'priority': 'high' if issue['count'] >= 10 else 'medium'
                    })

        return recommendations

    async def get_feedback_summary(self) -> Dict:
        """Get comprehensive feedback summary for reporting."""
        accuracy = await self.get_routing_accuracy(lookback_days=30)
        recommendations = await self.get_improvement_recommendations()

        summary = {
            'accuracy_metrics': accuracy,
            'recommendations': recommendations,
            'status': self._determine_status(accuracy['overall_accuracy']),
            'timestamp': datetime.now().isoformat()
        }

        return summary

    def _determine_status(self, accuracy: float) -> str:
        """Determine overall system status based on accuracy."""
        if accuracy >= 0.9:
            return "excellent"
        elif accuracy >= 0.8:
            return "good"
        elif accuracy >= 0.7:
            return "acceptable"
        elif accuracy >= 0.6:
            return "needs_improvement"
        else:
            return "poor"


# Singleton instance
_feedback_service = None

def get_feedback_service() -> FeedbackLoopService:
    """Get singleton FeedbackLoopService instance."""
    global _feedback_service
    if _feedback_service is None:
        _feedback_service = FeedbackLoopService()
    return _feedback_service
