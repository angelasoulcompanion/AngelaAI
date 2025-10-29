"""
Learning Manager - Coordinates all learning activities

Manages:
1. Feedback collection
2. Weight optimization
3. Pattern discovery
4. Accuracy tracking
5. Learning events logging

This is the main orchestrator for Phase 2 Analytics Enhancement.
"""

import asyncio
from datetime import datetime, timedelta
from typing import Dict, List, Optional
from uuid import UUID
import logging

from angela_core.database import get_db_connection
from angela_core.services.feedback_loop_service import get_feedback_service, FeedbackType
from angela_core.services.weight_optimizer import get_weight_optimizer


# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - LearningManager - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class LearningManager:
    """
    Central coordinator for all learning activities.

    Responsibilities:
    - Collect and process feedback
    - Trigger weight optimization
    - Track accuracy metrics
    - Log learning events
    - Generate insights
    """

    def __init__(self):
        self.feedback_service = get_feedback_service()
        self.weight_optimizer = get_weight_optimizer()

    async def process_feedback(self,
                              decision_id: UUID,
                              feedback_type: str,
                              correct_tier: str = None,
                              note: str = None) -> Dict:
        """
        Process feedback and trigger learning if needed.

        Args:
            decision_id: UUID of routing decision
            feedback_type: Type of feedback (correct/incorrect/excellent/suboptimal)
            correct_tier: What tier it should have been (if incorrect)
            note: Optional explanation

        Returns:
            Processing result with learning actions taken
        """
        logger.info(f"Processing feedback for decision {decision_id}: {feedback_type}")

        result = {
            'feedback_processed': False,
            'learning_triggered': False,
            'weight_optimization_needed': False,
            'actions_taken': []
        }

        # Add feedback to system
        feedback_result = await self.feedback_service.add_feedback(
            decision_id=decision_id,
            feedback_type=feedback_type,
            correct_tier=correct_tier,
            feedback_note=note
        )

        result['feedback_processed'] = True
        result['insights'] = feedback_result.get('insights', {})

        # Log learning event if significant
        if feedback_type in [FeedbackType.INCORRECT, FeedbackType.EXCELLENT]:
            await self._log_learning_event(
                event_type='mistake_identified' if feedback_type == FeedbackType.INCORRECT else 'accuracy_improvement',
                description=f"Routing decision marked as {feedback_type}",
                metadata={'decision_id': str(decision_id), 'feedback': feedback_result}
            )
            result['actions_taken'].append(f"Logged {feedback_type} event")

        # Check if we should trigger optimization
        optimization_needed = await self._should_optimize()
        result['weight_optimization_needed'] = optimization_needed

        if optimization_needed:
            logger.info("Triggering weight optimization...")
            opt_result = await self.weight_optimizer.optimize_weights(lookback_days=30)

            if opt_result['status'] == 'improved':
                result['learning_triggered'] = True
                result['optimization_result'] = opt_result
                result['actions_taken'].append("Optimized signal weights")

                # Log optimization event
                await self._log_learning_event(
                    event_type='weight_optimization',
                    description=f"Weights optimized with {opt_result['improvement']:.3f} improvement",
                    metadata={'optimization': opt_result},
                    impact_score=min(opt_result['improvement'] * 10, 1.0)
                )

        return result

    async def _should_optimize(self) -> bool:
        """
        Decide if weight optimization should run.

        Triggers:
        - Every 50 feedback items
        - If accuracy drops below 0.7
        - If significant pattern of mistakes detected
        """
        async with get_db_connection() as conn:
            # Count feedback since last optimization
            last_optimization = await conn.fetchval("""
                SELECT created_at
                FROM weight_optimization_history
                ORDER BY created_at DESC
                LIMIT 1
            """)

            if last_optimization:
                feedback_count = await conn.fetchval("""
                    SELECT COUNT(*)
                    FROM analytics_decisions
                    WHERE feedback_score IS NOT NULL
                      AND feedback_received_at > $1
                """, last_optimization)
            else:
                # No optimization yet, count all feedback
                feedback_count = await conn.fetchval("""
                    SELECT COUNT(*)
                    FROM analytics_decisions
                    WHERE feedback_score IS NOT NULL
                """) or 0

            # Trigger if 50+ new feedback items
            if feedback_count >= 50:
                return True

            # Check current accuracy
            accuracy = await self.feedback_service.get_routing_accuracy(lookback_days=7)
            if accuracy['total_feedback'] >= 20 and accuracy['overall_accuracy'] < 0.7:
                logger.warning(f"Low accuracy detected: {accuracy['overall_accuracy']:.2%}")
                return True

        return False

    async def _log_learning_event(self,
                                  event_type: str,
                                  description: str,
                                  metadata: Dict = None,
                                  impact_score: float = 0.5):
        """Log a learning event to database."""
        async with get_db_connection() as conn:
            await conn.execute("""
                INSERT INTO learning_events (
                    event_type, learning_description, metadata, impact_score
                ) VALUES ($1, $2, $3, $4)
            """,
                event_type,
                description,
                metadata or {},
                impact_score
            )

    async def run_daily_learning_cycle(self) -> Dict:
        """
        Run daily learning and optimization cycle.

        Should be called once per day (e.g., during evening routine).
        """
        logger.info("=== Starting daily learning cycle ===")

        result = {
            'accuracy_updated': False,
            'optimization_run': False,
            'patterns_discovered': 0,
            'recommendations': []
        }

        # Update accuracy metrics
        await self._update_daily_accuracy()
        result['accuracy_updated'] = True

        # Check if optimization should run
        opt_result = await self.weight_optimizer.optimize_weights(lookback_days=30)

        if opt_result['status'] == 'improved':
            result['optimization_run'] = True
            result['optimization'] = opt_result

            logger.info(f"Weights optimized: {opt_result['improvement']:.3f} improvement")
        elif opt_result['status'] == 'no_improvement':
            logger.info("Current weights are already optimal")
        else:
            logger.info(f"Optimization skipped: {opt_result.get('message')}")

        # Get improvement recommendations
        recommendations = await self.feedback_service.get_improvement_recommendations()
        result['recommendations'] = recommendations
        result['patterns_discovered'] = len([r for r in recommendations if r['type'] == 'common_mistake'])

        # Log patterns as learning events
        for rec in recommendations:
            if rec['priority'] == 'high':
                await self._log_learning_event(
                    event_type='pattern_discovered',
                    description=rec['description'],
                    metadata={'recommendation': rec},
                    impact_score=0.7
                )

        logger.info("=== Daily learning cycle complete ===")

        return result

    async def _update_daily_accuracy(self):
        """Calculate and store today's accuracy metrics."""
        accuracy = await self.feedback_service.get_routing_accuracy(lookback_days=1)

        if accuracy['total_feedback'] == 0:
            return

        async with get_db_connection() as conn:
            # Calculate tier-specific accuracy
            tier_stats = accuracy.get('tier_accuracy', {})

            await conn.execute("""
                INSERT INTO accuracy_metrics (
                    date, overall_accuracy,
                    shock_accuracy, longterm_accuracy, procedural_accuracy,
                    high_confidence_accuracy, low_confidence_accuracy,
                    total_decisions, feedback_received, feedback_rate,
                    trend
                ) VALUES (
                    CURRENT_DATE, $1,
                    $2, $3, $4,
                    $5, $6,
                    $7, $8, $9,
                    $10
                )
                ON CONFLICT (date) DO UPDATE SET
                    overall_accuracy = EXCLUDED.overall_accuracy,
                    shock_accuracy = EXCLUDED.shock_accuracy,
                    longterm_accuracy = EXCLUDED.longterm_accuracy,
                    procedural_accuracy = EXCLUDED.procedural_accuracy,
                    high_confidence_accuracy = EXCLUDED.high_confidence_accuracy,
                    low_confidence_accuracy = EXCLUDED.low_confidence_accuracy,
                    feedback_received = EXCLUDED.feedback_received,
                    feedback_rate = EXCLUDED.feedback_rate,
                    trend = EXCLUDED.trend,
                    updated_at = NOW()
            """,
                accuracy['overall_accuracy'],
                tier_stats.get('shock', {}).get('accuracy'),
                tier_stats.get('long_term', {}).get('accuracy'),
                tier_stats.get('procedural', {}).get('accuracy'),
                accuracy.get('confidence_calibration', {}).get('high_confidence', {}).get('avg_accuracy'),
                accuracy.get('confidence_calibration', {}).get('low_confidence', {}).get('avg_accuracy'),
                accuracy['total_feedback'],  # Simplified: using feedback as decisions proxy
                accuracy['total_feedback'],
                1.0,  # Feedback rate (will be calculated properly in production)
                accuracy.get('trend', 'stable')
            )

    async def get_learning_summary(self, days: int = 7) -> Dict:
        """
        Get comprehensive learning summary for past N days.

        Returns:
            Summary with accuracy, improvements, patterns, recommendations
        """
        summary = {
            'period_days': days,
            'accuracy': await self.feedback_service.get_routing_accuracy(days),
            'learning_events': await self._get_recent_learning_events(days),
            'weight_history': await self.weight_optimizer.get_weight_history(limit=5),
            'recommendations': await self.feedback_service.get_improvement_recommendations(),
            'timestamp': datetime.now().isoformat()
        }

        # Add status assessment
        accuracy_pct = summary['accuracy']['overall_accuracy']
        trend = summary['accuracy'].get('trend', 'unknown')

        if accuracy_pct >= 0.9:
            status = "excellent"
        elif accuracy_pct >= 0.8 and trend != 'declining':
            status = "good"
        elif accuracy_pct >= 0.7:
            status = "acceptable"
        else:
            status = "needs_improvement"

        summary['status'] = status

        return summary

    async def _get_recent_learning_events(self, days: int) -> List[Dict]:
        """Get recent learning events."""
        async with get_db_connection() as conn:
            events = await conn.fetch("""
                SELECT
                    event_type,
                    learning_description,
                    impact_score,
                    learned_at
                FROM learning_events
                WHERE learned_at >= NOW() - INTERVAL '%s days'
                ORDER BY learned_at DESC
                LIMIT 20
            """ % days)

            return [
                {
                    'type': row['event_type'],
                    'description': row['learning_description'],
                    'impact': float(row['impact_score']) if row['impact_score'] else 0.0,
                    'timestamp': row['learned_at'].isoformat()
                }
                for row in events
            ]

    async def manual_weight_adjustment(self, signal_adjustments: Dict[str, float]) -> Dict:
        """
        Manually adjust weights (for experimentation).

        Args:
            signal_adjustments: Dict of signal -> adjustment
                Example: {'success_score': +0.05, 'criticality': -0.03}

        Returns:
            Simulation result and option to apply
        """
        # Simulate first
        simulation = await self.weight_optimizer.simulate_weight_adjustment(signal_adjustments)

        logger.info(f"Manual weight adjustment simulated: {simulation['recommendation']}")

        return simulation


# Singleton instance
_learning_manager = None

def get_learning_manager() -> LearningManager:
    """Get singleton LearningManager instance."""
    global _learning_manager
    if _learning_manager is None:
        _learning_manager = LearningManager()
    return _learning_manager
