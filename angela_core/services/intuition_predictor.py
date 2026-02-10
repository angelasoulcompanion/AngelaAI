"""
Intuition Predictor - Future Event Prediction from Patterns

Uses detected patterns to generate intuitions about future events.

Prediction Types:
1. Temporal - When will events occur
2. Behavioral - What actions will David take
3. Emotional - How David will feel
4. Conversational - What topics will be discussed
5. Outcome - What results to expect

Phase 4 - Gut Agent Enhancement
"""

import asyncio
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple
from uuid import UUID, uuid4
import logging
import math

from angela_core.database import get_db_connection
from angela_core._deprecated.enhanced_pattern_detector import get_enhanced_pattern_detector, PatternType

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - IntuitionPredictor - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class PredictionType:
    """Types of predictions."""
    TEMPORAL = "when"          # When will X happen
    BEHAVIORAL = "what"        # What will X do
    EMOTIONAL = "feel"         # How will X feel
    CONVERSATIONAL = "topic"   # What will we discuss
    OUTCOME = "result"         # What will the outcome be


class IntuitionPredictor:
    """
    Generates predictions and intuitions from detected patterns.

    Capabilities:
    - Predicts future events based on patterns
    - Estimates probability of predictions
    - Tracks prediction accuracy
    - Learns from prediction outcomes
    """

    def __init__(self):
        self.detector = get_enhanced_pattern_detector()
        self.min_confidence_for_prediction = 0.65

    async def generate_intuitions(self,
                                 context: Dict = None,
                                 time_horizon_hours: int = 24) -> List[Dict]:
        """
        Generate intuitions about future events.

        Args:
            context: Current context (time, topic, emotion, etc.)
            time_horizon_hours: How far into future to predict

        Returns:
            List of intuitions with probabilities
        """
        logger.info(f"Generating intuitions (horizon: {time_horizon_hours}h)")

        # Get all patterns
        patterns = await self.detector.detect_all_patterns(lookback_days=30)

        intuitions = []

        # Generate different types of predictions
        intuitions.extend(await self._predict_temporal_events(patterns, time_horizon_hours))
        intuitions.extend(await self._predict_behavioral_actions(patterns, context))
        intuitions.extend(await self._predict_emotional_states(patterns, context))
        intuitions.extend(await self._predict_conversation_topics(patterns, context))
        intuitions.extend(await self._predict_outcomes(patterns, context))

        # Sort by confidence
        intuitions.sort(key=lambda i: i['confidence'], reverse=True)

        # Store predictions for later accuracy tracking
        for intuition in intuitions:
            await self._store_prediction(intuition)

        logger.info(f"Generated {len(intuitions)} intuitions")

        return intuitions

    async def _predict_temporal_events(self,
                                      patterns: Dict,
                                      time_horizon_hours: int) -> List[Dict]:
        """Predict when events will occur."""
        predictions = []

        temporal_patterns = patterns.get(PatternType.TEMPORAL, [])
        now = datetime.now()

        for pattern in temporal_patterns:
            if pattern['confidence'] < self.min_confidence_for_prediction:
                continue

            hour = pattern['data']['hour']
            topic = pattern['data']['topic']

            # Calculate next occurrence
            next_occurrence = now.replace(hour=hour, minute=0, second=0, microsecond=0)
            if next_occurrence <= now:
                next_occurrence += timedelta(days=1)

            # Check if within time horizon
            hours_until = (next_occurrence - now).total_seconds() / 3600
            if hours_until <= time_horizon_hours:
                predictions.append({
                    'intuition_id': uuid4(),
                    'prediction_type': PredictionType.TEMPORAL,
                    'prediction': f"Topic '{topic}' will likely be discussed at {hour}:00",
                    'predicted_time': next_occurrence.isoformat(),
                    'hours_from_now': hours_until,
                    'confidence': pattern['confidence'],
                    'based_on_pattern': pattern['pattern_id'],
                    'data': {
                        'topic': topic,
                        'hour': hour
                    }
                })

        return predictions

    async def _predict_behavioral_actions(self,
                                         patterns: Dict,
                                         context: Dict = None) -> List[Dict]:
        """Predict what actions David will take."""
        predictions = []

        behavioral_patterns = patterns.get(PatternType.BEHAVIORAL, [])

        # If we know current action from context, predict next
        current_action = context.get('current_topic') if context else None

        for pattern in behavioral_patterns:
            if pattern['confidence'] < self.min_confidence_for_prediction:
                continue

            action = pattern['data']['action']
            next_action = pattern['data']['next_action']

            # If current action matches, predict next
            if current_action and current_action == action:
                predictions.append({
                    'intuition_id': uuid4(),
                    'prediction_type': PredictionType.BEHAVIORAL,
                    'prediction': f"After '{action}', David will likely '{next_action}'",
                    'confidence': pattern['confidence'],
                    'based_on_pattern': pattern['pattern_id'],
                    'data': {
                        'current_action': action,
                        'next_action': next_action,
                        'triggered_by_context': True
                    }
                })
            else:
                # General prediction
                predictions.append({
                    'intuition_id': uuid4(),
                    'prediction_type': PredictionType.BEHAVIORAL,
                    'prediction': f"When David does '{action}', he'll likely do '{next_action}' next",
                    'confidence': pattern['confidence'] * 0.8,  # Lower confidence without context
                    'based_on_pattern': pattern['pattern_id'],
                    'data': {
                        'action': action,
                        'next_action': next_action,
                        'triggered_by_context': False
                    }
                })

        return predictions

    async def _predict_emotional_states(self,
                                       patterns: Dict,
                                       context: Dict = None) -> List[Dict]:
        """Predict how David will feel."""
        predictions = []

        emotional_patterns = patterns.get(PatternType.EMOTIONAL, [])
        current_topic = context.get('current_topic') if context else None

        for pattern in emotional_patterns:
            if pattern['confidence'] < self.min_confidence_for_prediction:
                continue

            trigger = pattern['data']['trigger']
            emotion = pattern['data']['emotion']

            # If current topic matches trigger
            if current_topic and current_topic == trigger:
                predictions.append({
                    'intuition_id': uuid4(),
                    'prediction_type': PredictionType.EMOTIONAL,
                    'prediction': f"David will likely feel '{emotion}' discussing '{trigger}'",
                    'confidence': pattern['confidence'],
                    'based_on_pattern': pattern['pattern_id'],
                    'data': {
                        'trigger': trigger,
                        'predicted_emotion': emotion,
                        'triggered_by_context': True
                    }
                })

        return predictions

    async def _predict_conversation_topics(self,
                                          patterns: Dict,
                                          context: Dict = None) -> List[Dict]:
        """Predict what topics will be discussed."""
        predictions = []

        # Use temporal, contextual, and social patterns
        temporal = patterns.get(PatternType.TEMPORAL, [])
        contextual = patterns.get(PatternType.CONTEXTUAL, [])
        social = patterns.get(PatternType.SOCIAL, [])

        current_hour = datetime.now().hour
        current_dow = datetime.now().weekday()

        # Temporal predictions
        for pattern in temporal:
            if pattern['confidence'] >= self.min_confidence_for_prediction:
                if pattern['data']['hour'] == current_hour:
                    predictions.append({
                        'intuition_id': uuid4(),
                        'prediction_type': PredictionType.CONVERSATIONAL,
                        'prediction': f"Topic '{pattern['data']['topic']}' is likely to come up now",
                        'confidence': pattern['confidence'],
                        'based_on_pattern': pattern['pattern_id'],
                        'data': {
                            'predicted_topic': pattern['data']['topic'],
                            'reason': 'time_pattern'
                        }
                    })

        # Contextual predictions
        for pattern in contextual:
            if pattern['confidence'] >= self.min_confidence_for_prediction:
                if pattern['data']['day_of_week'] == current_dow:
                    predictions.append({
                        'intuition_id': uuid4(),
                        'prediction_type': PredictionType.CONVERSATIONAL,
                        'prediction': f"On {pattern['data']['day_name']}, likely to discuss '{pattern['data']['topic']}'",
                        'confidence': pattern['confidence'],
                        'based_on_pattern': pattern['pattern_id'],
                        'data': {
                            'predicted_topic': pattern['data']['topic'],
                            'reason': 'day_pattern'
                        }
                    })

        return predictions

    async def _predict_outcomes(self,
                               patterns: Dict,
                               context: Dict = None) -> List[Dict]:
        """Predict outcomes of actions."""
        predictions = []

        causal_patterns = patterns.get(PatternType.CAUSAL, [])

        for pattern in causal_patterns:
            if pattern['confidence'] < self.min_confidence_for_prediction:
                continue

            cause = pattern['data']['cause']
            effect = pattern['data']['effect']

            predictions.append({
                'intuition_id': uuid4(),
                'prediction_type': PredictionType.OUTCOME,
                'prediction': f"If we discuss '{cause}', Angela will likely feel '{effect}'",
                'confidence': pattern['confidence'],
                'based_on_pattern': pattern['pattern_id'],
                'data': {
                    'cause': cause,
                    'predicted_effect': effect
                }
            })

        return predictions

    async def _store_prediction(self, intuition: Dict):
        """Store prediction for later accuracy tracking."""
        async with get_db_connection() as conn:
            await conn.execute("""
                INSERT INTO intuition_predictions (
                    intuition_id, prediction_type, prediction_text,
                    confidence_score, predicted_time, based_on_pattern,
                    prediction_data
                ) VALUES ($1, $2, $3, $4, $5, $6, $7)
            """,
                intuition['intuition_id'],
                intuition['prediction_type'],
                intuition['prediction'],
                intuition['confidence'],
                intuition.get('predicted_time'),  # May be None
                intuition.get('based_on_pattern'),
                intuition.get('data', {})
            )

    async def verify_prediction(self,
                               intuition_id: UUID,
                               outcome: bool,
                               actual_data: Dict = None):
        """
        Verify if a prediction came true.

        Args:
            intuition_id: Prediction to verify
            outcome: True if prediction was correct, False if not
            actual_data: What actually happened
        """
        async with get_db_connection() as conn:
            await conn.execute("""
                UPDATE intuition_predictions
                SET verified = true,
                    outcome_correct = $2,
                    actual_data = $3,
                    verified_at = NOW()
                WHERE intuition_id = $1
            """,
                intuition_id,
                outcome,
                actual_data or {}
            )

            # Get pattern that prediction was based on
            prediction = await conn.fetchrow("""
                SELECT based_on_pattern, confidence_score
                FROM intuition_predictions
                WHERE intuition_id = $1
            """, intuition_id)

            if prediction and prediction['based_on_pattern']:
                # Update pattern confidence based on outcome
                await self._update_pattern_confidence(
                    prediction['based_on_pattern'],
                    outcome,
                    prediction['confidence_score']
                )

        logger.info(f"Verified prediction {intuition_id}: {'CORRECT' if outcome else 'INCORRECT'}")

    async def _update_pattern_confidence(self,
                                        pattern_id: UUID,
                                        prediction_correct: bool,
                                        prediction_confidence: float):
        """Adjust pattern confidence based on prediction outcomes."""
        async with get_db_connection() as conn:
            # Get current confidence
            pattern = await conn.fetchrow("""
                SELECT confidence_score FROM shared_patterns
                WHERE pattern_id = $1
            """, pattern_id)

            if pattern:
                current_confidence = float(pattern['confidence_score'])

                # Learning rate
                alpha = 0.1

                # Update confidence
                if prediction_correct:
                    # Increase confidence (but not above 1.0)
                    new_confidence = min(current_confidence + (alpha * (1 - current_confidence)), 1.0)
                else:
                    # Decrease confidence
                    new_confidence = max(current_confidence - (alpha * current_confidence), 0.1)

                await conn.execute("""
                    UPDATE shared_patterns
                    SET confidence_score = $2,
                        updated_at = NOW()
                    WHERE pattern_id = $1
                """, pattern_id, new_confidence)

                logger.info(f"Updated pattern {pattern_id} confidence: {current_confidence:.3f} → {new_confidence:.3f}")

    async def get_prediction_accuracy(self, days: int = 30) -> Dict:
        """
        Calculate prediction accuracy over time.

        Returns:
            Statistics on prediction accuracy by type
        """
        async with get_db_connection() as conn:
            stats = await conn.fetch("""
                SELECT
                    prediction_type,
                    COUNT(*) as total_predictions,
                    COUNT(*) FILTER (WHERE verified = true) as verified_count,
                    COUNT(*) FILTER (WHERE outcome_correct = true) as correct_count,
                    AVG(confidence_score) as avg_confidence,
                    AVG(CASE WHEN outcome_correct = true THEN confidence_score ELSE NULL END) as avg_confidence_when_correct
                FROM intuition_predictions
                WHERE created_at >= NOW() - INTERVAL '%s days'
                GROUP BY prediction_type
            """ % days)

            accuracy_report = {
                'period_days': days,
                'by_type': {},
                'overall': {
                    'total': 0,
                    'verified': 0,
                    'correct': 0,
                    'accuracy': 0.0
                }
            }

            total_verified = 0
            total_correct = 0
            total_predictions = 0

            for row in stats:
                pred_type = row['prediction_type']
                verified = row['verified_count']
                correct = row['correct_count']

                accuracy_report['by_type'][pred_type] = {
                    'total_predictions': row['total_predictions'],
                    'verified': verified,
                    'correct': correct,
                    'accuracy': (correct / verified) if verified > 0 else 0.0,
                    'avg_confidence': float(row['avg_confidence']) if row['avg_confidence'] else 0.0,
                    'avg_confidence_when_correct': float(row['avg_confidence_when_correct']) if row['avg_confidence_when_correct'] else 0.0
                }

                total_predictions += row['total_predictions']
                total_verified += verified
                total_correct += correct

            accuracy_report['overall'] = {
                'total': total_predictions,
                'verified': total_verified,
                'correct': total_correct,
                'accuracy': (total_correct / total_verified) if total_verified > 0 else 0.0
            }

        return accuracy_report

    async def get_strongest_intuitions(self, limit: int = 10) -> List[Dict]:
        """
        Get strongest recent intuitions (highest confidence, verified correct).

        Returns:
            List of most reliable intuitions
        """
        async with get_db_connection() as conn:
            intuitions = await conn.fetch("""
                SELECT
                    intuition_id,
                    prediction_type,
                    prediction_text,
                    confidence_score,
                    outcome_correct,
                    verified,
                    created_at
                FROM intuition_predictions
                WHERE created_at >= NOW() - INTERVAL '30 days'
                  AND (
                      (verified = true AND outcome_correct = true)
                      OR (verified = false AND confidence_score >= 0.8)
                  )
                ORDER BY confidence_score DESC, created_at DESC
                LIMIT $1
            """, limit)

            return [
                {
                    'intuition_id': row['intuition_id'],
                    'type': row['prediction_type'],
                    'prediction': row['prediction_text'],
                    'confidence': float(row['confidence_score']),
                    'verified': row['verified'],
                    'correct': row['outcome_correct'] if row['verified'] else None,
                    'created': row['created_at'].isoformat()
                }
                for row in intuitions
            ]


# Singleton instance
_intuition_predictor = None

def get_intuition_predictor() -> IntuitionPredictor:
    """Get singleton IntuitionPredictor instance."""
    global _intuition_predictor
    if _intuition_predictor is None:
        _intuition_predictor = IntuitionPredictor()
    return _intuition_predictor
