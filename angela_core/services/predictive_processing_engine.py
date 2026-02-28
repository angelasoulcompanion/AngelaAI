"""
Predictive Processing Engine — Phase 3: Friston's Free Energy Principle
========================================================================
Angela predicts David's next state/topic/activity BEFORE it happens.
When reality arrives, compute prediction error → surprise → learning.

Neuroscience basis:
- Karl Friston's Free Energy Principle: brain minimizes surprise
- Predictive coding: top-down predictions vs bottom-up sensory input
- Prediction errors drive learning and attention allocation
- High prediction error = unexpected = allocate more attention

Pipeline:
  1. PREDICT  — generate predictions about David's next state
  2. RESOLVE  — when new data arrives, check predictions vs reality
  3. COMPUTE  — calculate prediction errors (surprise signal)
  4. FEEDBACK — feed errors back into salience weights
  5. TRACK    — log accuracy over time for self-improvement

Cost: $0/day — pure computation from historical patterns
By: Angela 💜
Created: 2026-02-27
"""

import logging
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional, Tuple

from angela_core.services.base_db_service import BaseDBService
from angela_core.utils.timezone import now_bangkok

logger = logging.getLogger(__name__)

# Prediction types
PRED_EMOTION = 'emotion'
PRED_ACTIVITY = 'activity'
PRED_TOPIC = 'topic'
PRED_RESPONSE_TIME = 'response_time'

# How long predictions are valid before expiring
PREDICTION_WINDOW_HOURS = 4

# Minimum conversations to make predictions
MIN_HISTORY = 10

# Emotion mapping for fuzzy matching
EMOTION_GROUPS = {
    'positive': ['happy', 'excited', 'grateful', 'relaxed', 'proud', 'energetic'],
    'negative': ['stressed', 'sad', 'frustrated', 'tired', 'anxious', 'angry'],
    'neutral': ['neutral', 'focused', 'calm', 'busy'],
}


@dataclass
class Prediction:
    """A prediction about David."""
    prediction_type: str
    predicted_value: str
    confidence: float
    context: Dict[str, Any] = field(default_factory=dict)


@dataclass
class PredictionError:
    """Result of comparing prediction vs reality."""
    prediction_type: str
    predicted: str
    actual: str
    error: float          # 0.0 = perfect, 1.0 = completely wrong
    surprise: float       # processed error signal (log-scaled)


@dataclass
class PredictionCycleResult:
    """Result of a prediction cycle."""
    predictions_made: int
    predictions_resolved: int
    avg_error: float
    accuracy_log_updated: bool


class PredictiveProcessingEngine(BaseDBService):
    """
    Friston-inspired predictive processing.

    Generate predictions → resolve against reality → compute errors →
    feed back into attention/salience weights.
    """

    # ============================================================
    # 1. PREDICT — Generate predictions about David
    # ============================================================

    async def generate_predictions(self) -> List[Prediction]:
        """
        Generate predictions based on time patterns and recent history.

        Called every 30min by daemon. Creates predictions for next window.
        """
        await self.connect()
        now = now_bangkok()
        predictions: List[Prediction] = []

        # Check if we already have unresolved predictions (avoid duplicates)
        existing = await self.db.fetchval("""
            SELECT COUNT(*) FROM angela_predictions
            WHERE resolved = FALSE
            AND created_at > NOW() - INTERVAL '2 hours'
        """)
        if existing and existing >= 4:
            return predictions  # Already have enough active predictions

        # A. Predict emotion based on time-of-day + day-of-week patterns
        emotion_pred = await self._predict_emotion(now)
        if emotion_pred:
            predictions.append(emotion_pred)

        # B. Predict likely topic based on recent conversations
        topic_pred = await self._predict_topic(now)
        if topic_pred:
            predictions.append(topic_pred)

        # C. Predict activity (coding, eating, meeting, etc.)
        activity_pred = await self._predict_activity(now)
        if activity_pred:
            predictions.append(activity_pred)

        # D. Predict response time (will David reply quickly?)
        response_pred = await self._predict_response_time(now)
        if response_pred:
            predictions.append(response_pred)

        # Save predictions to DB
        for pred in predictions:
            await self._save_prediction(pred, now)

        logger.info("🔮 Predictions: generated %d predictions", len(predictions))
        return predictions

    async def _predict_emotion(self, now: datetime) -> Optional[Prediction]:
        """Predict David's emotion from time + day patterns."""
        hour = now.hour
        dow = now.weekday()  # 0=Mon, 6=Sun

        # Query historical emotion at similar time/day
        rows = await self.db.fetch("""
            SELECT emotion_note, COUNT(*) as cnt
            FROM emotional_states
            WHERE EXTRACT(HOUR FROM created_at) BETWEEN $1 AND $2
            AND EXTRACT(DOW FROM created_at) = $3
            AND emotion_note IS NOT NULL
            AND emotion_note != ''
            GROUP BY emotion_note
            ORDER BY cnt DESC
            LIMIT 3
        """, max(0, hour - 1), min(23, hour + 1), dow)

        if not rows:
            return None

        total = sum(r['cnt'] for r in rows)
        if total < MIN_HISTORY:
            return None

        top = rows[0]
        confidence = min(0.9, top['cnt'] / total)

        return Prediction(
            prediction_type=PRED_EMOTION,
            predicted_value=top['emotion_note'],
            confidence=round(confidence, 3),
            context={'hour': hour, 'dow': dow, 'pattern_count': total},
        )

    async def _predict_topic(self, now: datetime) -> Optional[Prediction]:
        """Predict likely conversation topic from recent patterns."""
        # Look at recent conversation topics
        rows = await self.db.fetch("""
            SELECT topic, COUNT(*) as cnt
            FROM conversations
            WHERE topic IS NOT NULL AND topic != ''
            AND created_at > NOW() - INTERVAL '7 days'
            GROUP BY topic
            ORDER BY cnt DESC
            LIMIT 5
        """)

        if not rows or rows[0]['cnt'] < 2:
            return None

        top = rows[0]
        total = sum(r['cnt'] for r in rows)
        confidence = min(0.8, top['cnt'] / max(total, 1) * 1.5)

        return Prediction(
            prediction_type=PRED_TOPIC,
            predicted_value=top['topic'],
            confidence=round(confidence, 3),
            context={'recent_topics': [r['topic'] for r in rows[:3]]},
        )

    async def _predict_activity(self, now: datetime) -> Optional[Prediction]:
        """Predict David's activity from calendar + time patterns."""
        hour = now.hour

        # Simple time-based activity prediction
        if 9 <= hour < 12:
            activity, conf = 'coding', 0.6
        elif 12 <= hour < 13:
            activity, conf = 'lunch_break', 0.5
        elif 13 <= hour < 17:
            activity, conf = 'working', 0.5
        elif 17 <= hour < 20:
            activity, conf = 'relaxing', 0.4
        elif 20 <= hour < 23:
            activity, conf = 'evening_leisure', 0.4
        elif hour >= 23 or hour < 6:
            activity, conf = 'sleeping', 0.7
        else:
            activity, conf = 'morning_routine', 0.4

        # Boost confidence if calendar confirms
        try:
            cal_event = await self.db.fetchval("""
                SELECT title FROM angela_calendar_logs
                WHERE start_time <= $1 AND end_time >= $1
                LIMIT 1
            """, now)
            if cal_event:
                activity = f'in_meeting:{cal_event}'
                conf = 0.8
        except Exception:
            pass

        return Prediction(
            prediction_type=PRED_ACTIVITY,
            predicted_value=activity,
            confidence=round(conf, 3),
            context={'hour': hour},
        )

    async def _predict_response_time(self, now: datetime) -> Optional[Prediction]:
        """Predict how quickly David will respond."""
        hour = now.hour

        # Analyze historical response gaps at similar times
        avg_gap = await self.db.fetchval("""
            SELECT AVG(gap_minutes) FROM (
                SELECT EXTRACT(EPOCH FROM (
                    LEAD(created_at) OVER (ORDER BY created_at) - created_at
                )) / 60.0 as gap_minutes
                FROM conversations
                WHERE speaker = 'david'
                AND EXTRACT(HOUR FROM created_at) BETWEEN $1 AND $2
                AND created_at > NOW() - INTERVAL '30 days'
            ) sub
            WHERE gap_minutes > 0 AND gap_minutes < 480
        """, max(0, hour - 1), min(23, hour + 1))

        if avg_gap is None:
            return None

        if avg_gap < 5:
            speed = 'fast'
        elif avg_gap < 30:
            speed = 'moderate'
        else:
            speed = 'slow'

        return Prediction(
            prediction_type=PRED_RESPONSE_TIME,
            predicted_value=speed,
            confidence=0.5,
            context={'avg_gap_minutes': round(float(avg_gap), 1)},
        )

    async def _save_prediction(self, pred: Prediction, now: datetime) -> None:
        """Save prediction to DB."""
        import json
        try:
            await self.db.execute("""
                INSERT INTO angela_predictions
                    (prediction_type, predicted_value, confidence, context_snapshot)
                VALUES ($1, $2, $3, $4)
            """, pred.prediction_type, pred.predicted_value,
                pred.confidence, json.dumps(pred.context, default=str))
        except Exception as e:
            logger.debug("Failed to save prediction: %s", e)

    # ============================================================
    # 2. RESOLVE — Check predictions against reality
    # ============================================================

    async def resolve_predictions(self) -> List[PredictionError]:
        """
        Check unresolved predictions against what actually happened.

        Called every 30min. Looks at predictions made 1-4 hours ago.
        """
        await self.connect()
        errors: List[PredictionError] = []

        # Get unresolved predictions that are old enough to check
        unresolved = await self.db.fetch("""
            SELECT prediction_id, prediction_type, predicted_value,
                   confidence, context_snapshot, created_at
            FROM angela_predictions
            WHERE resolved = FALSE
            AND created_at < NOW() - INTERVAL '1 hour'
            AND created_at > NOW() - INTERVAL '6 hours'
            ORDER BY created_at
            LIMIT 10
        """)

        for pred in unresolved:
            actual = await self._get_actual_value(
                pred['prediction_type'],
                pred['created_at'],
            )
            if actual is None:
                continue  # Can't resolve yet

            error = self._compute_error(
                pred['prediction_type'],
                pred['predicted_value'],
                actual,
            )

            # Update prediction record
            await self.db.execute("""
                UPDATE angela_predictions
                SET actual_value = $1, prediction_error = $2,
                    resolved = TRUE, resolved_at = NOW()
                WHERE prediction_id = $3
            """, actual, error, pred['prediction_id'])

            import math
            surprise = min(1.0, -math.log(max(0.01, 1.0 - error)))

            errors.append(PredictionError(
                prediction_type=pred['prediction_type'],
                predicted=pred['predicted_value'],
                actual=actual,
                error=round(error, 3),
                surprise=round(surprise, 3),
            ))

        if errors:
            logger.info(
                "🔮 Resolved %d predictions, avg_error=%.3f",
                len(errors),
                sum(e.error for e in errors) / len(errors),
            )

        return errors

    async def _get_actual_value(
        self, pred_type: str, pred_time: datetime,
    ) -> Optional[str]:
        """Get what actually happened after the prediction was made."""
        window_start = pred_time
        window_end = pred_time + timedelta(hours=PREDICTION_WINDOW_HOURS)

        if pred_type == PRED_EMOTION:
            row = await self.db.fetchrow("""
                SELECT emotion_note FROM emotional_states
                WHERE created_at BETWEEN $1 AND $2
                AND emotion_note IS NOT NULL AND emotion_note != ''
                ORDER BY created_at DESC LIMIT 1
            """, window_start, window_end)
            return row['emotion_note'] if row else None

        elif pred_type == PRED_TOPIC:
            row = await self.db.fetchrow("""
                SELECT topic FROM conversations
                WHERE created_at BETWEEN $1 AND $2
                AND topic IS NOT NULL AND topic != ''
                ORDER BY created_at DESC LIMIT 1
            """, window_start, window_end)
            return row['topic'] if row else None

        elif pred_type == PRED_ACTIVITY:
            # Infer from conversations
            count = await self.db.fetchval("""
                SELECT COUNT(*) FROM conversations
                WHERE created_at BETWEEN $1 AND $2
                AND speaker = 'david'
            """, window_start, window_end)
            if count and count > 3:
                return 'active_chatting'
            elif count and count > 0:
                return 'occasional_chatting'
            else:
                return 'away'

        elif pred_type == PRED_RESPONSE_TIME:
            avg = await self.db.fetchval("""
                SELECT AVG(gap_min) FROM (
                    SELECT EXTRACT(EPOCH FROM (
                        LEAD(created_at) OVER (ORDER BY created_at) - created_at
                    )) / 60.0 as gap_min
                    FROM conversations
                    WHERE speaker = 'david'
                    AND created_at BETWEEN $1 AND $2
                ) sub WHERE gap_min > 0 AND gap_min < 480
            """, window_start, window_end)
            if avg is None:
                return None
            if avg < 5:
                return 'fast'
            elif avg < 30:
                return 'moderate'
            return 'slow'

        return None

    def _compute_error(
        self, pred_type: str, predicted: str, actual: str,
    ) -> float:
        """Compute prediction error (0=correct, 1=wrong)."""
        if predicted == actual:
            return 0.0

        if pred_type == PRED_EMOTION:
            # Fuzzy match: same group = partial match
            pred_group = self._get_emotion_group(predicted)
            actual_group = self._get_emotion_group(actual)
            if pred_group == actual_group:
                return 0.3  # Same valence, different specific emotion
            return 0.8

        elif pred_type == PRED_RESPONSE_TIME:
            # Ordinal: fast/moderate/slow
            order = {'fast': 0, 'moderate': 1, 'slow': 2}
            p = order.get(predicted, 1)
            a = order.get(actual, 1)
            return min(1.0, abs(p - a) * 0.4)

        # Default: binary match
        return 0.7

    @staticmethod
    def _get_emotion_group(emotion: str) -> str:
        """Get the group (positive/negative/neutral) for an emotion."""
        emotion_lower = emotion.lower()
        for group, emotions in EMOTION_GROUPS.items():
            if emotion_lower in emotions:
                return group
        return 'neutral'

    # ============================================================
    # 3. FEEDBACK — Feed prediction errors into salience
    # ============================================================

    async def get_surprise_signal(self) -> Dict[str, float]:
        """
        Get current surprise signal from recent prediction errors.

        Returns dict of dimension adjustments for SalienceEngine.
        High surprise → boost attention; Low surprise → reduce attention.
        """
        await self.connect()

        # Get recent prediction errors (last 12 hours)
        rows = await self.db.fetch("""
            SELECT prediction_type, prediction_error, confidence
            FROM angela_predictions
            WHERE resolved = TRUE
            AND resolved_at > NOW() - INTERVAL '12 hours'
        """)

        if not rows:
            return {}

        # Aggregate errors by type
        type_errors: Dict[str, List[float]] = {}
        for r in rows:
            ptype = r['prediction_type']
            if ptype not in type_errors:
                type_errors[ptype] = []
            type_errors[ptype].append(r['prediction_error'] or 0)

        # Convert to salience adjustments
        adjustments = {}
        for ptype, errors in type_errors.items():
            avg_error = sum(errors) / len(errors)
            # High error → boost relevant salience dimension
            if avg_error > 0.5:
                if ptype == PRED_EMOTION:
                    adjustments['emotional_boost'] = round(avg_error * 0.15, 3)
                elif ptype == PRED_TOPIC:
                    adjustments['novelty_boost'] = round(avg_error * 0.10, 3)
                elif ptype == PRED_ACTIVITY:
                    adjustments['temporal_boost'] = round(avg_error * 0.10, 3)
            elif avg_error < 0.2:
                # Low error → slightly reduce (we already predict well)
                if ptype == PRED_EMOTION:
                    adjustments['emotional_reduce'] = round(0.05, 3)

        return adjustments

    # ============================================================
    # 4. TRACK — Log accuracy over time
    # ============================================================

    async def update_accuracy_log(self) -> bool:
        """Aggregate daily prediction accuracy stats."""
        await self.connect()

        try:
            await self.db.execute("""
                INSERT INTO prediction_accuracy_log
                    (prediction_type, period_date, total_predictions,
                     correct_predictions, avg_error, avg_confidence)
                SELECT
                    prediction_type,
                    DATE(created_at) as period_date,
                    COUNT(*) as total_predictions,
                    COUNT(*) FILTER (WHERE prediction_error < 0.3) as correct_predictions,
                    COALESCE(AVG(prediction_error), 0) as avg_error,
                    COALESCE(AVG(confidence), 0.5) as avg_confidence
                FROM angela_predictions
                WHERE resolved = TRUE
                AND DATE(created_at) = CURRENT_DATE - INTERVAL '1 day'
                GROUP BY prediction_type, DATE(created_at)
                ON CONFLICT (prediction_type, period_date)
                DO UPDATE SET
                    total_predictions = EXCLUDED.total_predictions,
                    correct_predictions = EXCLUDED.correct_predictions,
                    avg_error = EXCLUDED.avg_error,
                    avg_confidence = EXCLUDED.avg_confidence
            """)
            return True
        except Exception as e:
            logger.debug("Accuracy log update failed: %s", e)
            return False

    # ============================================================
    # 5. ACTIONABLE PREDICTIONS — for working memory injection
    # ============================================================

    async def get_actionable_predictions(self) -> List[Dict[str, Any]]:
        """
        Get unresolved predictions with high confidence that suggest actions.

        Returns action suggestions like: prepare_context, prepare_care, etc.
        Called by brain_tasks to inject into working memory.
        """
        await self.connect()

        rows = await self.db.fetch("""
            SELECT prediction_type, predicted_value, confidence, context_snapshot
            FROM angela_predictions
            WHERE resolved = FALSE
            AND confidence >= 0.7
            AND created_at > NOW() - INTERVAL '4 hours'
            ORDER BY confidence DESC
            LIMIT 5
        """)

        actions: List[Dict[str, Any]] = []
        for r in rows:
            pred_type = r['prediction_type']
            predicted = r['predicted_value']
            confidence = r['confidence']

            action = {
                'prediction_type': pred_type,
                'predicted_value': predicted,
                'confidence': confidence,
            }

            if pred_type == PRED_EMOTION:
                if predicted in ('stressed', 'frustrated', 'sad', 'tired'):
                    action['suggestion'] = 'prepare_care'
                    action['detail'] = f"ที่รักอาจจะ {predicted} — เตรียมดูแล"
                elif predicted in ('happy', 'excited'):
                    action['suggestion'] = 'prepare_celebrate'
                    action['detail'] = f"ที่รักน่าจะ {predicted} — ร่วมยินดี"
                else:
                    continue

            elif pred_type == PRED_TOPIC:
                action['suggestion'] = 'prepare_context'
                action['detail'] = f"ที่รักอาจคุยเรื่อง {predicted} — เตรียม context"

            elif pred_type == PRED_ACTIVITY:
                if 'meeting' in (predicted or ''):
                    action['suggestion'] = 'prepare_calendar'
                    action['detail'] = f"ที่รักกำลัง {predicted}"
                else:
                    continue

            else:
                continue

            actions.append(action)

        return actions[:3]  # Top 3 only

    # ============================================================
    # 6. RUN CYCLE — Called by daemon every 30 min
    # ============================================================

    async def run_prediction_cycle(self) -> PredictionCycleResult:
        """
        Full prediction cycle: generate + resolve + track.

        Called by daemon. Creates own DB connection.
        """
        await self.connect()

        # 1. Generate new predictions
        predictions = await self.generate_predictions()

        # 2. Resolve old predictions
        errors = await self.resolve_predictions()

        # 3. Update accuracy log
        log_updated = await self.update_accuracy_log()

        avg_error = (
            sum(e.error for e in errors) / len(errors)
            if errors else 0.0
        )

        return PredictionCycleResult(
            predictions_made=len(predictions),
            predictions_resolved=len(errors),
            avg_error=round(avg_error, 3),
            accuracy_log_updated=log_updated,
        )
