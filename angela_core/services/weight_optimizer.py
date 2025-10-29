"""
Weight Optimizer - Automatic adjustment of Analytics Agent signal weights

Uses machine learning techniques to optimize the 7-signal weights based on feedback.

Techniques:
1. Gradient descent - Adjust weights based on error gradients
2. Success analysis - Increase weights for signals that predict success
3. A/B testing - Test different weight combinations
4. Adaptive learning rate - Faster learning at first, slower over time
"""

import asyncio
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple
from uuid import UUID
import json
import statistics
import math

from angela_core.database import get_db_connection
from angela_core.services.feedback_loop_service import get_feedback_service


class WeightOptimizer:
    """
    Optimizes Analytics Agent signal weights based on feedback.

    Default weights:
    - success_score: 0.35
    - repetition_signal: 0.25
    - criticality: 0.20
    - pattern_novelty: 0.15
    - context_richness: 0.05

    Learning algorithm:
    1. Collect feedback on routing decisions
    2. Calculate error gradients for each signal
    3. Adjust weights proportionally
    4. Test new weights
    5. Keep if improvement, revert if worse
    """

    # Default weights (sum to 1.0)
    DEFAULT_WEIGHTS = {
        'success_score': 0.35,
        'repetition_signal': 0.25,
        'criticality': 0.20,
        'pattern_novelty': 0.15,
        'context_richness': 0.05
    }

    # Constraints
    MIN_WEIGHT = 0.05  # No signal should be less than 5%
    MAX_WEIGHT = 0.50  # No signal should exceed 50%

    def __init__(self, learning_rate: float = 0.05):
        """
        Initialize optimizer.

        Args:
            learning_rate: How fast to adjust weights (0.01-0.1)
        """
        self.learning_rate = learning_rate
        self.current_weights = self.DEFAULT_WEIGHTS.copy()
        self.weight_history = []
        self.feedback_service = get_feedback_service()

    async def optimize_weights(self, lookback_days: int = 30) -> Dict:
        """
        Optimize weights based on recent feedback.

        Args:
            lookback_days: How far back to analyze

        Returns:
            Optimization result with new weights and improvement
        """
        # Get decisions with feedback
        async with get_db_connection() as conn:
            decisions = await conn.fetch("""
                SELECT
                    signals,
                    target_tier,
                    composite_score,
                    feedback_score
                FROM analytics_decisions
                WHERE feedback_score IS NOT NULL
                  AND created_at >= NOW() - INTERVAL '%s days'
                ORDER BY created_at DESC
            """ % lookback_days)

            if len(decisions) < 20:
                return {
                    'status': 'insufficient_data',
                    'message': f'Need at least 20 feedback samples, have {len(decisions)}',
                    'current_weights': self.current_weights
                }

        # Load current weights from database (if any)
        await self._load_weights_from_db()

        # Calculate optimal weights
        new_weights = await self._calculate_optimal_weights(decisions)

        # Test new weights vs current weights
        improvement = await self._test_weights(decisions, new_weights, self.current_weights)

        if improvement > 0:
            # New weights are better!
            old_weights = self.current_weights.copy()
            self.current_weights = new_weights

            # Save to database
            await self._save_weights_to_db(new_weights, improvement)

            return {
                'status': 'improved',
                'old_weights': old_weights,
                'new_weights': new_weights,
                'improvement': improvement,
                'feedback_count': len(decisions),
                'timestamp': datetime.now()
            }
        else:
            # Current weights are still better
            return {
                'status': 'no_improvement',
                'message': 'Current weights are already optimal',
                'current_weights': self.current_weights,
                'feedback_count': len(decisions),
                'timestamp': datetime.now()
            }

    async def _calculate_optimal_weights(self, decisions: List[Dict]) -> Dict[str, float]:
        """
        Calculate optimal weights using gradient descent.

        For each signal:
        1. Calculate correlation with successful outcomes
        2. Calculate gradient (how much to adjust)
        3. Apply learning rate
        4. Normalize to sum to 1.0
        """
        # Initialize gradients
        gradients = {signal: 0.0 for signal in self.DEFAULT_WEIGHTS.keys()}

        # Calculate error gradients
        for decision in decisions:
            signals = json.loads(decision['signals']) if isinstance(decision['signals'], str) else decision['signals']
            feedback = float(decision['feedback_score'])
            composite = float(decision['composite_score'])

            # Error: how far off were we?
            error = feedback - composite

            # Update gradients based on signal contributions
            for signal_name in gradients.keys():
                if signal_name in signals:
                    signal_value = float(signals[signal_name])
                    # Gradient: error * signal_value
                    gradients[signal_name] += error * signal_value

        # Average gradients
        n = len(decisions)
        gradients = {k: v / n for k, v in gradients.items()}

        # Apply gradients to weights
        new_weights = {}
        for signal, weight in self.current_weights.items():
            # Adjust: weight + learning_rate * gradient
            adjusted = weight + (self.learning_rate * gradients.get(signal, 0))

            # Clamp to constraints
            adjusted = max(self.MIN_WEIGHT, min(self.MAX_WEIGHT, adjusted))

            new_weights[signal] = adjusted

        # Normalize to sum to 1.0
        total = sum(new_weights.values())
        new_weights = {k: v / total for k, v in new_weights.items()}

        return new_weights

    async def _test_weights(self,
                           decisions: List[Dict],
                           new_weights: Dict[str, float],
                           old_weights: Dict[str, float]) -> float:
        """
        Test new weights vs old weights on historical data.

        Returns:
            Improvement score (positive = better, negative = worse)
        """
        new_errors = []
        old_errors = []

        for decision in decisions:
            signals = json.loads(decision['signals']) if isinstance(decision['signals'], str) else decision['signals']
            feedback = float(decision['feedback_score'])

            # Calculate composite score with new weights
            new_composite = self._calculate_composite(signals, new_weights)
            new_error = abs(feedback - new_composite)
            new_errors.append(new_error)

            # Calculate composite score with old weights
            old_composite = self._calculate_composite(signals, old_weights)
            old_error = abs(feedback - old_composite)
            old_errors.append(old_error)

        # Average errors
        new_avg_error = statistics.mean(new_errors)
        old_avg_error = statistics.mean(old_errors)

        # Improvement: reduction in error
        improvement = old_avg_error - new_avg_error

        return improvement

    def _calculate_composite(self, signals: Dict, weights: Dict[str, float]) -> float:
        """Calculate composite score using given weights."""
        score = 0.0

        for signal_name, weight in weights.items():
            if signal_name in signals:
                score += float(signals[signal_name]) * weight

        # Apply emotional intensity multiplier
        if 'emotional_intensity' in signals:
            emotion_multiplier = 1.0 + (float(signals['emotional_intensity']) * 0.2)
            score *= emotion_multiplier

        return min(1.0, score)

    async def _load_weights_from_db(self):
        """Load most recent weights from database."""
        async with get_db_connection() as conn:
            latest = await conn.fetchrow("""
                SELECT weights
                FROM weight_optimization_history
                ORDER BY created_at DESC
                LIMIT 1
            """)

            if latest and latest['weights']:
                self.current_weights = json.loads(latest['weights']) if isinstance(latest['weights'], str) else latest['weights']

    async def _save_weights_to_db(self, weights: Dict[str, float], improvement: float):
        """Save optimized weights to database."""
        async with get_db_connection() as conn:
            await conn.execute("""
                INSERT INTO weight_optimization_history (
                    id, weights, improvement, created_at
                ) VALUES (gen_random_uuid(), $1, $2, NOW())
            """, json.dumps(weights), improvement)

            # Also update current_weights table
            await conn.execute("""
                INSERT INTO current_weights (
                    id, signal_name, weight, updated_at
                ) VALUES (gen_random_uuid(), 'current', $1, NOW())
                ON CONFLICT (signal_name) DO UPDATE
                SET weight = EXCLUDED.weight,
                    updated_at = NOW()
            """, json.dumps(weights))

    async def get_weight_history(self, limit: int = 10) -> List[Dict]:
        """Get history of weight optimizations."""
        async with get_db_connection() as conn:
            history = await conn.fetch("""
                SELECT
                    weights,
                    improvement,
                    created_at
                FROM weight_optimization_history
                ORDER BY created_at DESC
                LIMIT $1
            """, limit)

            return [
                {
                    'weights': json.loads(row['weights']) if isinstance(row['weights'], str) else row['weights'],
                    'improvement': float(row['improvement']),
                    'timestamp': row['created_at'].isoformat()
                }
                for row in history
            ]

    async def simulate_weight_adjustment(self, signal_adjustments: Dict[str, float]) -> Dict:
        """
        Simulate what would happen with manual weight adjustments.

        Args:
            signal_adjustments: Dictionary of signal -> adjustment amount
                Example: {'success_score': +0.05, 'criticality': -0.03}

        Returns:
            Simulated result with predicted improvement
        """
        # Apply adjustments
        simulated_weights = self.current_weights.copy()

        for signal, adjustment in signal_adjustments.items():
            if signal in simulated_weights:
                simulated_weights[signal] += adjustment

        # Normalize
        total = sum(simulated_weights.values())
        simulated_weights = {k: v / total for k, v in simulated_weights.items()}

        # Clamp
        simulated_weights = {
            k: max(self.MIN_WEIGHT, min(self.MAX_WEIGHT, v))
            for k, v in simulated_weights.items()
        }

        # Normalize again after clamping
        total = sum(simulated_weights.values())
        simulated_weights = {k: v / total for k, v in simulated_weights.items()}

        # Get recent decisions to test
        async with get_db_connection() as conn:
            decisions = await conn.fetch("""
                SELECT signals, feedback_score
                FROM analytics_decisions
                WHERE feedback_score IS NOT NULL
                  AND created_at >= NOW() - INTERVAL '30 days'
                LIMIT 100
            """)

        if decisions:
            # Test simulated weights
            predicted_improvement = await self._test_weights(
                decisions,
                simulated_weights,
                self.current_weights
            )
        else:
            predicted_improvement = 0.0

        return {
            'current_weights': self.current_weights,
            'simulated_weights': simulated_weights,
            'predicted_improvement': predicted_improvement,
            'recommendation': 'apply' if predicted_improvement > 0 else 'reject'
        }

    def get_current_weights(self) -> Dict[str, float]:
        """Get current weights."""
        return self.current_weights.copy()

    async def reset_to_defaults(self):
        """Reset weights to default values."""
        self.current_weights = self.DEFAULT_WEIGHTS.copy()

        # Save to database
        await self._save_weights_to_db(self.current_weights, 0.0)

        return {
            'status': 'reset',
            'weights': self.current_weights
        }


# Singleton instance
_optimizer = None

def get_weight_optimizer(learning_rate: float = 0.05) -> WeightOptimizer:
    """Get singleton WeightOptimizer instance."""
    global _optimizer
    if _optimizer is None:
        _optimizer = WeightOptimizer(learning_rate)
    return _optimizer
