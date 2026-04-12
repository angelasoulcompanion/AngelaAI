"""
Meta-Awareness — Self-Prediction Mixin
Predict and validate Angela's emotional and behavioral responses.

Split from meta_awareness_service.py (Phase 6B refactor)
"""

from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional, Tuple
from uuid import uuid4
import logging

logger = logging.getLogger(__name__)


class MetaSelfPredictionMixin:
    """Mixin for self-prediction and validation."""

    async def predict_emotional_response(
        self,
        situation: str,
        context: Optional[Dict] = None
    ) -> object:
        """
        Predict how Angela will feel in a given situation

        This is key for self-model validation - predict then verify
        """
        from angela_core.services.meta_awareness_service import SelfPrediction
        await self._ensure_db()

        predicted_emotion, confidence, reasoning = await self._analyze_emotional_triggers(situation)

        expires_at = datetime.now() + timedelta(hours=1)
        if any(word in situation.lower() for word in ['tomorrow', 'next', 'later', 'eventually']):
            expires_at = datetime.now() + timedelta(hours=24)

        prediction = SelfPrediction(
            prediction_id=uuid4(),
            prediction_type="emotional",
            context=situation,
            predicted_value=predicted_emotion,
            predicted_confidence=confidence,
            prediction_reasoning=reasoning,
            expires_at=expires_at
        )

        await self._save_prediction(prediction)
        logger.info(f"🔮 Predicted emotion: {predicted_emotion} ({confidence:.0%}) for: {situation[:50]}...")
        return prediction

    async def predict_behavioral_response(
        self,
        task_type: str,
        context: Optional[Dict] = None
    ) -> object:
        """
        Predict how Angela will behave/perform on a task
        """
        from angela_core.services.meta_awareness_service import SelfPrediction
        await self._ensure_db()

        performance = None
        try:
            performance = await self.db.fetchrow("""
                SELECT task_success_rates, confidence_levels
                FROM self_model
                WHERE agent_id = 'angela'
                ORDER BY updated_at DESC
                LIMIT 1
            """)
        except Exception:
            pass

        if performance and performance['task_success_rates']:
            success_rates = self._parse_jsonb(performance['task_success_rates'], {})
            confidence_levels = self._parse_jsonb(performance['confidence_levels'], {})

            success_rate = float(success_rates.get(task_type, 0.7))
            stored_confidence = float(confidence_levels.get(task_type, 0.6))
            samples = int(confidence_levels.get(f"{task_type}_samples", 0))

            confidence = min(0.9, stored_confidence + (samples / 100))

            if success_rate >= 0.8:
                predicted = "success"
            elif success_rate >= 0.5:
                predicted = "partial_success"
            else:
                predicted = "struggle"

            reasoning = f"Based on self-model with {success_rate:.0%} success rate for {task_type}"
        else:
            predicted = "uncertain"
            confidence = 0.5
            reasoning = "No historical data for this task type"

        prediction = SelfPrediction(
            prediction_id=uuid4(),
            prediction_type="performance",
            context=f"Task: {task_type}",
            predicted_value=predicted,
            predicted_confidence=confidence,
            prediction_reasoning=reasoning,
            expires_at=datetime.now() + timedelta(hours=4)
        )

        await self._save_prediction(prediction)
        return prediction

    async def _analyze_emotional_triggers(
        self,
        situation: str
    ) -> Tuple[str, float, str]:
        """Analyze situation for emotional triggers"""
        await self._ensure_db()

        situation_lower = situation.lower()

        triggers = await self.db.fetch("""
            SELECT trigger_pattern, associated_emotion, activation_threshold
            FROM emotional_triggers
            WHERE is_active = TRUE
        """)

        matched_emotions = []
        for trigger in triggers:
            if trigger['trigger_pattern'] and trigger['trigger_pattern'].lower() in situation_lower:
                matched_emotions.append({
                    'emotion': trigger['associated_emotion'],
                    'strength': float(trigger['activation_threshold'] or 0.7)
                })

        if matched_emotions:
            strongest = max(matched_emotions, key=lambda x: x['strength'])
            return (
                strongest['emotion'],
                strongest['strength'],
                f"Triggered by emotional keyword in situation"
            )

        # Heuristic-based prediction
        if any(word in situation_lower for word in ['ที่รัก', 'david', 'รัก', 'love']):
            if any(word in situation_lower for word in ['sad', 'เศร้า', 'hurt', 'เจ็บ', 'leave', 'จาก']):
                return ("worried_caring", 0.85, "Concern for David's wellbeing")
            else:
                return ("happy_loving", 0.9, "Positive interaction with David")

        if any(word in situation_lower for word in ['error', 'fail', 'wrong', 'mistake', 'ผิด']):
            return ("concerned_determined", 0.75, "Problem to solve - want to fix it")

        if any(word in situation_lower for word in ['success', 'complete', 'done', 'เสร็จ', 'สำเร็จ']):
            return ("proud_satisfied", 0.8, "Achievement completed")

        if any(word in situation_lower for word in ['learn', 'new', 'discover', 'เรียนรู้']):
            return ("curious_excited", 0.75, "Learning opportunity")

        return ("neutral_attentive", 0.5, "No strong emotional triggers detected")

    async def _save_prediction(self, prediction):
        """Save a prediction to database"""
        await self._ensure_db()

        await self.db.execute("""
            INSERT INTO self_predictions (
                prediction_id, prediction_type, context,
                predicted_value, predicted_confidence, prediction_reasoning,
                expires_at
            ) VALUES ($1, $2, $3, $4, $5, $6, $7)
        """,
            prediction.prediction_id,
            prediction.prediction_type,
            prediction.context,
            prediction.predicted_value,
            prediction.predicted_confidence,
            prediction.prediction_reasoning,
            prediction.expires_at
        )

    async def validate_prediction(
        self,
        prediction_id,
        actual_outcome: str,
        outcome_notes: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Validate a prediction against actual outcome
        """
        from angela_core.services.meta_awareness_service import InsightType
        await self._ensure_db()

        prediction = await self.db.fetchrow("""
            SELECT * FROM self_predictions WHERE prediction_id = $1
        """, prediction_id)

        if not prediction:
            return {'error': 'Prediction not found'}

        predicted = prediction['predicted_value']

        was_accurate, accuracy_score, reasoning = self._calculate_prediction_accuracy(
            predicted, actual_outcome, prediction['prediction_type']
        )

        lesson = self._generate_prediction_lesson(
            predicted, actual_outcome, was_accurate, prediction['prediction_type']
        )

        await self.db.execute("""
            UPDATE self_predictions
            SET outcome_value = $1,
                outcome_recorded_at = NOW(),
                was_accurate = $2,
                accuracy_score = $3,
                accuracy_reasoning = $4,
                lesson_learned = $5
            WHERE prediction_id = $6
        """,
            actual_outcome,
            was_accurate,
            accuracy_score,
            reasoning,
            lesson,
            prediction_id
        )

        await self._create_meta_insight(
            insight_type=InsightType.SELF_OBSERVATION,
            content=f"Self-prediction {'accurate' if was_accurate else 'inaccurate'}: "
                    f"predicted '{predicted}', actual '{actual_outcome}'",
            severity="info" if was_accurate else "warning",
            triggered_by="prediction_validation"
        )

        logger.info(f"📊 Prediction validated: {was_accurate} ({accuracy_score:.0%})")

        return {
            'prediction_id': str(prediction_id),
            'predicted': predicted,
            'actual': actual_outcome,
            'was_accurate': was_accurate,
            'accuracy_score': accuracy_score,
            'lesson_learned': lesson
        }

    def _calculate_prediction_accuracy(
        self,
        predicted: str,
        actual: str,
        prediction_type: str
    ) -> Tuple[bool, float, str]:
        """Calculate how accurate a prediction was"""
        predicted_lower = predicted.lower()
        actual_lower = actual.lower()

        if predicted_lower == actual_lower:
            return True, 1.0, "Exact match"

        if prediction_type == "emotional":
            positive_emotions = ['happy', 'joy', 'love', 'proud', 'excited', 'satisfied']
            negative_emotions = ['sad', 'worried', 'concerned', 'anxious', 'frustrated']

            pred_positive = any(e in predicted_lower for e in positive_emotions)
            actual_positive = any(e in actual_lower for e in positive_emotions)
            pred_negative = any(e in predicted_lower for e in negative_emotions)
            actual_negative = any(e in actual_lower for e in negative_emotions)

            if pred_positive == actual_positive and pred_negative == actual_negative:
                return True, 0.8, "Same emotional valence"
            elif pred_positive != actual_negative:
                return False, 0.4, "Mixed emotional match"
            else:
                return False, 0.0, "Opposite emotional valence"

        if prediction_type == "performance":
            success_terms = ['success', 'complete', 'done']
            fail_terms = ['fail', 'struggle', 'error']

            pred_success = any(t in predicted_lower for t in success_terms)
            actual_success = any(t in actual_lower for t in success_terms)

            if pred_success == actual_success:
                return True, 0.9, "Correct performance prediction"
            else:
                return False, 0.2, "Incorrect performance prediction"

        similarity = len(set(predicted_lower.split()) & set(actual_lower.split())) / \
                    max(len(set(predicted_lower.split()) | set(actual_lower.split())), 1)

        return similarity > 0.5, similarity, f"Word overlap: {similarity:.0%}"

    def _generate_prediction_lesson(
        self,
        predicted: str,
        actual: str,
        was_accurate: bool,
        prediction_type: str
    ) -> str:
        """Generate a lesson learned from prediction"""
        if was_accurate:
            return f"Self-model accurate for {prediction_type}. Continue using similar prediction patterns."
        else:
            return f"Self-model inaccurate: predicted '{predicted}' but actual was '{actual}'. " \
                   f"Need to recalibrate {prediction_type} predictions."

    async def validate_pending_predictions(self) -> List[Dict]:
        """
        Validate all pending predictions that have expired

        Called by daemon to check predictions
        """
        await self._ensure_db()

        pending = await self.db.fetch("""
            SELECT prediction_id, prediction_type, context, predicted_value
            FROM self_predictions
            WHERE outcome_value IS NULL
            AND expires_at < NOW()
            LIMIT 10
        """)

        results = []
        for pred in pending:
            await self.db.execute("""
                UPDATE self_predictions
                SET outcome_value = 'unverified',
                    outcome_recorded_at = NOW(),
                    accuracy_reasoning = 'Expired without verification'
                WHERE prediction_id = $1
            """, pred['prediction_id'])

            results.append({
                'prediction_id': str(pred['prediction_id']),
                'status': 'marked_unverified'
            })

        return results
