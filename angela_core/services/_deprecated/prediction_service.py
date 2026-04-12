"""
Prediction Service - Angela's Predictive Intelligence

5 Types of Predictions:
1. Next Action - คาดเดาว่าที่รักจะทำอะไรต่อ
2. Emotional State - คาดเดาอารมณ์ของที่รัก
3. Topic - คาดเดาหัวข้อที่จะคุย
4. Time-based - คาดเดา patterns ตามเวลา
5. Pattern Completion - เติม pattern ที่ยังไม่สมบูรณ์

Based on Research Design (Oct 2025) - Phase 4 Gut Enhancement
Uses new tables: intuition_predictions, gut_agent_patterns, shared_patterns

Created: 2026-01-18
"""

import asyncio
import json
import logging
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional, Tuple
from uuid import UUID, uuid4
from enum import Enum

from angela_core.database import db

logger = logging.getLogger(__name__)


class PredictionType(str, Enum):
    """Types of predictions Angela can make."""
    NEXT_ACTION = "next_action"       # What will David do next
    EMOTIONAL_STATE = "emotional"     # How David will feel
    TOPIC = "topic"                   # What will be discussed
    TIME_BASED = "time_based"         # Patterns based on time
    PATTERN_COMPLETION = "pattern"    # Complete incomplete patterns


@dataclass
class Prediction:
    """A single prediction with confidence and evidence."""
    prediction_id: UUID = field(default_factory=uuid4)
    prediction_type: PredictionType = PredictionType.NEXT_ACTION
    predicted_value: Any = None
    confidence: float = 0.5  # 0-1 scale
    reasoning: str = ""
    evidence: List[Dict] = field(default_factory=list)
    timestamp: datetime = field(default_factory=datetime.now)

    # Optional fields for specific prediction types
    predicted_time: Optional[datetime] = None
    time_horizon_hours: Optional[int] = None

    def to_dict(self) -> Dict:
        """Convert to dictionary for JSON serialization."""
        return {
            'prediction_id': str(self.prediction_id),
            'prediction_type': self.prediction_type.value,
            'predicted_value': self.predicted_value,
            'confidence': self.confidence,
            'reasoning': self.reasoning,
            'evidence': self.evidence,
            'timestamp': self.timestamp.isoformat(),
            'predicted_time': self.predicted_time.isoformat() if self.predicted_time else None,
            'time_horizon_hours': self.time_horizon_hours
        }


@dataclass
class PredictionContext:
    """Context for making predictions."""
    current_topic: Optional[str] = None
    current_emotion: Optional[str] = None
    current_time: datetime = field(default_factory=datetime.now)
    recent_actions: List[str] = field(default_factory=list)
    recent_topics: List[str] = field(default_factory=list)
    recent_emotions: List[str] = field(default_factory=list)
    day_of_week: int = field(default_factory=lambda: datetime.now().weekday())
    hour_of_day: int = field(default_factory=lambda: datetime.now().hour)

    @classmethod
    async def from_database(cls) -> 'PredictionContext':
        """Build context from recent database records."""
        context = cls()

        try:
            # Get recent conversations
            recent = await db.fetch("""
                SELECT topic, emotion_detected, speaker, created_at
                FROM conversations
                WHERE created_at >= NOW() - INTERVAL '2 hours'
                ORDER BY created_at DESC
                LIMIT 20
            """)

            for row in recent:
                if row['topic']:
                    context.recent_topics.append(row['topic'])
                if row['emotion_detected']:
                    context.recent_emotions.append(row['emotion_detected'])
                if row['speaker'] == 'david':
                    context.recent_actions.append(row['topic'] or 'conversation')

            if context.recent_topics:
                context.current_topic = context.recent_topics[0]
            if context.recent_emotions:
                context.current_emotion = context.recent_emotions[0]

        except Exception as e:
            logger.warning(f"Could not build context from database: {e}")

        return context


class PredictionService:
    """
    Angela's Prediction Service

    5 types of predictions for Angela:
    1. Next action prediction - คาดเดาว่าที่รักจะทำอะไรต่อ
    2. Emotional state prediction - คาดเดาอารมณ์ของที่รัก
    3. Topic prediction - คาดเดาหัวข้อที่จะคุย
    4. Time-based prediction - คาดเดา patterns ตามเวลา
    5. Pattern completion - เติม pattern ที่ยังไม่สมบูรณ์

    Uses patterns from:
    - gut_agent_patterns (collective unconscious)
    - shared_patterns (cross-agent patterns)
    - conversations (historical data)
    - emotional_states (emotional history)
    """

    def __init__(self):
        self.min_confidence_threshold = 0.5
        self.prediction_cache: Dict[str, Prediction] = {}
        self.last_prediction_time: Optional[datetime] = None
        logger.info("PredictionService initialized")

    # =========================================================================
    # MAIN PREDICTION METHODS
    # =========================================================================

    async def predict_next_action(self, context: PredictionContext = None) -> Prediction:
        """
        คาดเดาว่าที่รักจะทำอะไรต่อ

        Based on:
        - Recent actions sequence
        - Time patterns
        - Behavioral patterns from gut_agent

        Args:
            context: Current context (auto-loaded if None)

        Returns:
            Prediction with next likely action
        """
        if context is None:
            context = await PredictionContext.from_database()

        evidence = []
        predicted_action = None
        confidence = 0.0
        reasoning_parts = []

        # 1. Check behavioral patterns from gut_agent
        behavioral_patterns = await self._get_behavioral_patterns(context.current_topic)
        if behavioral_patterns:
            best_pattern = max(behavioral_patterns, key=lambda p: p['confidence'])
            if best_pattern['confidence'] > confidence:
                predicted_action = best_pattern.get('next_action') or best_pattern.get('intuition_text', '')
                confidence = best_pattern['confidence']
                evidence.append({
                    'source': 'behavioral_pattern',
                    'pattern_id': str(best_pattern.get('id', '')),
                    'observation_count': best_pattern.get('observation_count', 0)
                })
                reasoning_parts.append(f"Behavioral pattern: {best_pattern['pattern_description']}")

        # 2. Check action sequences from conversations
        if context.recent_actions and len(context.recent_actions) >= 2:
            sequence_prediction = await self._predict_from_action_sequence(context.recent_actions[:5])
            if sequence_prediction and sequence_prediction['confidence'] > confidence:
                predicted_action = sequence_prediction['predicted_action']
                confidence = sequence_prediction['confidence']
                evidence.append({
                    'source': 'action_sequence',
                    'sequence': context.recent_actions[:3],
                    'frequency': sequence_prediction['frequency']
                })
                reasoning_parts.append(f"Action sequence: {' -> '.join(context.recent_actions[:3])}")

        # 3. Check time-based patterns
        time_action = await self._predict_action_by_time(context.hour_of_day, context.day_of_week)
        if time_action and time_action['confidence'] > confidence:
            predicted_action = time_action['predicted_action']
            confidence = time_action['confidence']
            evidence.append({
                'source': 'time_pattern',
                'hour': context.hour_of_day,
                'day': context.day_of_week
            })
            reasoning_parts.append(f"Time pattern: hour={context.hour_of_day}, day={context.day_of_week}")

        reasoning = "; ".join(reasoning_parts) if reasoning_parts else "No strong patterns found"

        prediction = Prediction(
            prediction_type=PredictionType.NEXT_ACTION,
            predicted_value=predicted_action or "Unable to predict",
            confidence=min(confidence, 1.0),
            reasoning=reasoning,
            evidence=evidence
        )

        # Store prediction for later verification
        await self._store_prediction(prediction)

        return prediction

    async def predict_emotional_state(self, context: PredictionContext = None) -> Prediction:
        """
        คาดเดาอารมณ์ของที่รัก

        Based on:
        - Current topic and known emotional triggers
        - Time of day patterns
        - Recent emotional trajectory
        - Mirroring history

        Args:
            context: Current context (auto-loaded if None)

        Returns:
            Prediction with emotional state
        """
        if context is None:
            context = await PredictionContext.from_database()

        evidence = []
        predicted_emotion = None
        confidence = 0.0
        reasoning_parts = []

        # 1. Check emotional patterns for current topic
        if context.current_topic:
            topic_emotion = await self._get_emotion_for_topic(context.current_topic)
            if topic_emotion:
                predicted_emotion = topic_emotion['emotion']
                confidence = topic_emotion['confidence']
                evidence.append({
                    'source': 'topic_emotion_pattern',
                    'topic': context.current_topic,
                    'frequency': topic_emotion['frequency']
                })
                reasoning_parts.append(f"Topic '{context.current_topic}' often associated with {topic_emotion['emotion']}")

        # 2. Check emotional trajectory (recent emotions suggest next)
        if context.recent_emotions and len(context.recent_emotions) >= 2:
            trajectory = await self._predict_emotion_trajectory(context.recent_emotions[:5])
            if trajectory and trajectory['confidence'] > confidence:
                predicted_emotion = trajectory['predicted_emotion']
                confidence = trajectory['confidence']
                evidence.append({
                    'source': 'emotional_trajectory',
                    'recent_emotions': context.recent_emotions[:3]
                })
                reasoning_parts.append(f"Emotional trajectory: {' -> '.join(context.recent_emotions[:3])}")

        # 3. Check time-based emotional patterns
        time_emotion = await self._get_emotion_by_time(context.hour_of_day)
        if time_emotion and time_emotion['confidence'] > confidence * 0.8:  # Slightly lower threshold
            # Combine with existing prediction
            confidence = (confidence + time_emotion['confidence']) / 2
            evidence.append({
                'source': 'time_emotion_pattern',
                'hour': context.hour_of_day,
                'typical_emotion': time_emotion['emotion']
            })
            reasoning_parts.append(f"Time {context.hour_of_day}:00 often associated with {time_emotion['emotion']}")

        reasoning = "; ".join(reasoning_parts) if reasoning_parts else "No strong emotional patterns found"

        prediction = Prediction(
            prediction_type=PredictionType.EMOTIONAL_STATE,
            predicted_value=predicted_emotion or "neutral",
            confidence=min(confidence, 1.0),
            reasoning=reasoning,
            evidence=evidence
        )

        await self._store_prediction(prediction)
        return prediction

    async def predict_topic(self, context: PredictionContext = None) -> Prediction:
        """
        คาดเดาหัวข้อที่จะคุย

        Based on:
        - Time patterns (what topics come up at this hour)
        - Day-of-week patterns
        - Topic sequences
        - Unfinished business from previous conversations

        Args:
            context: Current context (auto-loaded if None)

        Returns:
            Prediction with likely topic
        """
        if context is None:
            context = await PredictionContext.from_database()

        evidence = []
        predicted_topic = None
        confidence = 0.0
        reasoning_parts = []

        # 1. Check time-based topic patterns
        time_topic = await self._get_topic_by_time(context.hour_of_day, context.day_of_week)
        if time_topic:
            predicted_topic = time_topic['topic']
            confidence = time_topic['confidence']
            evidence.append({
                'source': 'time_topic_pattern',
                'hour': context.hour_of_day,
                'day': context.day_of_week,
                'frequency': time_topic['frequency']
            })
            reasoning_parts.append(f"At {context.hour_of_day}:00, topic '{time_topic['topic']}' is common")

        # 2. Check topic sequences
        if context.recent_topics and len(context.recent_topics) >= 1:
            next_topic = await self._predict_next_topic(context.recent_topics[:3])
            if next_topic and next_topic['confidence'] > confidence:
                predicted_topic = next_topic['predicted_topic']
                confidence = next_topic['confidence']
                evidence.append({
                    'source': 'topic_sequence',
                    'recent_topics': context.recent_topics[:3]
                })
                reasoning_parts.append(f"After '{context.recent_topics[0]}', often comes '{next_topic['predicted_topic']}'")

        # 3. Check for unfinished topics (high importance but short duration)
        unfinished = await self._get_unfinished_topics()
        if unfinished and unfinished['confidence'] > confidence * 0.9:
            evidence.append({
                'source': 'unfinished_topic',
                'topic': unfinished['topic'],
                'last_discussed': unfinished.get('last_discussed', '')
            })
            reasoning_parts.append(f"Unfinished topic: '{unfinished['topic']}'")

        reasoning = "; ".join(reasoning_parts) if reasoning_parts else "No strong topic patterns found"

        prediction = Prediction(
            prediction_type=PredictionType.TOPIC,
            predicted_value=predicted_topic or "general conversation",
            confidence=min(confidence, 1.0),
            reasoning=reasoning,
            evidence=evidence
        )

        await self._store_prediction(prediction)
        return prediction

    async def predict_time_pattern(self, context: PredictionContext = None) -> Prediction:
        """
        คาดเดา patterns ตามเวลา
        E.g., "ที่รักมักถามเรื่อง X ตอน 9am"

        Based on:
        - Historical activity by hour/day
        - Recurring schedules
        - Productivity patterns

        Args:
            context: Current context (auto-loaded if None)

        Returns:
            Prediction with time-based pattern
        """
        if context is None:
            context = await PredictionContext.from_database()

        evidence = []
        patterns = []
        reasoning_parts = []

        # 1. Get current hour patterns
        hour_patterns = await self._get_patterns_for_hour(context.hour_of_day)
        for pattern in hour_patterns:
            patterns.append(pattern)
            evidence.append({
                'source': 'hour_pattern',
                'hour': context.hour_of_day,
                'pattern': pattern['description'],
                'frequency': pattern['count']
            })

        # 2. Get day-of-week patterns
        day_patterns = await self._get_patterns_for_day(context.day_of_week)
        for pattern in day_patterns:
            patterns.append(pattern)
            evidence.append({
                'source': 'day_pattern',
                'day': context.day_of_week,
                'pattern': pattern['description'],
                'frequency': pattern['count']
            })

        # 3. Predict next significant time
        next_event = await self._predict_next_significant_time(context.current_time)
        if next_event:
            patterns.append(next_event)
            evidence.append({
                'source': 'predicted_event',
                'predicted_time': next_event.get('predicted_time'),
                'event': next_event.get('description')
            })
            reasoning_parts.append(f"Next likely event: {next_event.get('description')}")

        # Combine patterns into prediction
        if patterns:
            best_pattern = max(patterns, key=lambda p: p.get('confidence', 0))
            predicted_value = {
                'pattern_description': best_pattern.get('description', 'Time-based activity pattern'),
                'patterns_found': len(patterns),
                'most_confident': best_pattern
            }
            confidence = best_pattern.get('confidence', 0.5)
        else:
            predicted_value = {'pattern_description': 'No significant time patterns found'}
            confidence = 0.3

        reasoning = "; ".join(reasoning_parts) if reasoning_parts else f"Found {len(patterns)} time patterns"

        prediction = Prediction(
            prediction_type=PredictionType.TIME_BASED,
            predicted_value=predicted_value,
            confidence=min(confidence, 1.0),
            reasoning=reasoning,
            evidence=evidence,
            time_horizon_hours=24
        )

        await self._store_prediction(prediction)
        return prediction

    async def predict_pattern_completion(self, context: PredictionContext = None) -> Prediction:
        """
        เติม pattern ที่ยังไม่สมบูรณ์
        E.g., "ถ้าเริ่ม A แล้ว B มักจะตามมา"

        Based on:
        - Incomplete sequences detected
        - Historical pattern completions
        - Causal patterns from gut_agent

        Args:
            context: Current context (auto-loaded if None)

        Returns:
            Prediction with pattern completion
        """
        if context is None:
            context = await PredictionContext.from_database()

        evidence = []
        predicted_completion = None
        confidence = 0.0
        reasoning_parts = []

        # 1. Check for incomplete action sequences
        if context.recent_actions:
            incomplete = await self._find_incomplete_sequences(context.recent_actions)
            if incomplete:
                predicted_completion = incomplete['expected_completion']
                confidence = incomplete['confidence']
                evidence.append({
                    'source': 'incomplete_sequence',
                    'started': incomplete['started'],
                    'missing': incomplete['expected_completion']
                })
                reasoning_parts.append(f"Sequence '{incomplete['started']}' usually followed by '{incomplete['expected_completion']}'")

        # 2. Check causal patterns from gut_agent
        if context.current_topic:
            causal = await self._get_causal_patterns(context.current_topic)
            if causal and causal['confidence'] > confidence:
                predicted_completion = causal['expected_effect']
                confidence = causal['confidence']
                evidence.append({
                    'source': 'causal_pattern',
                    'cause': context.current_topic,
                    'expected_effect': causal['expected_effect']
                })
                reasoning_parts.append(f"'{context.current_topic}' often leads to '{causal['expected_effect']}'")

        # 3. Check for recurring incomplete patterns
        recurring = await self._get_recurring_incomplete_patterns()
        if recurring and recurring['confidence'] > confidence * 0.8:
            evidence.append({
                'source': 'recurring_incomplete',
                'pattern': recurring['pattern'],
                'occurrences': recurring['occurrences']
            })
            reasoning_parts.append(f"Recurring incomplete: {recurring['pattern']}")

        reasoning = "; ".join(reasoning_parts) if reasoning_parts else "No incomplete patterns found"

        prediction = Prediction(
            prediction_type=PredictionType.PATTERN_COMPLETION,
            predicted_value=predicted_completion or "No pattern completion predicted",
            confidence=min(confidence, 1.0),
            reasoning=reasoning,
            evidence=evidence
        )

        await self._store_prediction(prediction)
        return prediction

    # =========================================================================
    # AGGREGATE PREDICTION METHOD
    # =========================================================================

    async def generate_all_predictions(
        self,
        context: PredictionContext = None,
        min_confidence: float = 0.5
    ) -> List[Prediction]:
        """
        Generate all 5 types of predictions at once.

        Args:
            context: Current context (auto-loaded if None)
            min_confidence: Minimum confidence to include prediction

        Returns:
            List of predictions sorted by confidence
        """
        if context is None:
            context = await PredictionContext.from_database()

        predictions = []

        # Run all predictions concurrently
        results = await asyncio.gather(
            self.predict_next_action(context),
            self.predict_emotional_state(context),
            self.predict_topic(context),
            self.predict_time_pattern(context),
            self.predict_pattern_completion(context),
            return_exceptions=True
        )

        for result in results:
            if isinstance(result, Prediction):
                if result.confidence >= min_confidence:
                    predictions.append(result)
            elif isinstance(result, Exception):
                logger.error(f"Prediction error: {result}")

        # Sort by confidence
        predictions.sort(key=lambda p: p.confidence, reverse=True)

        self.last_prediction_time = datetime.now()

        return predictions

    # =========================================================================
    # HELPER METHODS - Database Queries
    # =========================================================================

    async def _get_behavioral_patterns(self, current_topic: Optional[str]) -> List[Dict]:
        """Get behavioral patterns from gut_agent_patterns."""
        try:
            if current_topic:
                patterns = await db.fetch("""
                    SELECT id, pattern_type, pattern_description, observation_count,
                           confidence, intuition_text
                    FROM gut_agent_patterns
                    WHERE pattern_type = 'behavioral'
                      AND (pattern_description ILIKE $1 OR intuition_text ILIKE $1)
                    ORDER BY confidence DESC
                    LIMIT 5
                """, f'%{current_topic}%')
            else:
                patterns = await db.fetch("""
                    SELECT id, pattern_type, pattern_description, observation_count,
                           confidence, intuition_text
                    FROM gut_agent_patterns
                    WHERE pattern_type = 'behavioral'
                    ORDER BY confidence DESC, observation_count DESC
                    LIMIT 5
                """)
            return [dict(row) for row in patterns]
        except Exception as e:
            logger.error(f"Error getting behavioral patterns: {e}")
            return []

    async def _predict_from_action_sequence(self, actions: List[str]) -> Optional[Dict]:
        """Predict next action from sequence."""
        try:
            if len(actions) < 2:
                return None

            # Look for similar sequences in history
            current_action = actions[0]
            result = await db.fetchrow("""
                WITH sequences AS (
                    SELECT
                        topic as action,
                        LEAD(topic) OVER (ORDER BY created_at) as next_action
                    FROM conversations
                    WHERE created_at >= NOW() - INTERVAL '30 days'
                      AND speaker = 'david'
                )
                SELECT next_action, COUNT(*) as frequency
                FROM sequences
                WHERE action = $1 AND next_action IS NOT NULL
                GROUP BY next_action
                ORDER BY frequency DESC
                LIMIT 1
            """, current_action)

            if result:
                confidence = min(result['frequency'] / 5.0, 0.9)
                return {
                    'predicted_action': result['next_action'],
                    'confidence': confidence,
                    'frequency': result['frequency']
                }
        except Exception as e:
            logger.error(f"Error predicting from action sequence: {e}")
        return None

    async def _predict_action_by_time(self, hour: int, day: int) -> Optional[Dict]:
        """Predict action based on time."""
        try:
            result = await db.fetchrow("""
                SELECT topic as action, COUNT(*) as frequency
                FROM conversations
                WHERE created_at >= NOW() - INTERVAL '30 days'
                  AND EXTRACT(HOUR FROM created_at) = $1
                  AND speaker = 'david'
                GROUP BY topic
                ORDER BY frequency DESC
                LIMIT 1
            """, hour)

            if result:
                confidence = min(result['frequency'] / 10.0, 0.85)
                return {
                    'predicted_action': result['action'],
                    'confidence': confidence
                }
        except Exception as e:
            logger.error(f"Error predicting action by time: {e}")
        return None

    async def _get_emotion_for_topic(self, topic: str) -> Optional[Dict]:
        """Get typical emotion for a topic."""
        try:
            result = await db.fetchrow("""
                SELECT emotion_detected as emotion, COUNT(*) as frequency
                FROM conversations
                WHERE topic ILIKE $1
                  AND emotion_detected IS NOT NULL
                  AND emotion_detected != ''
                GROUP BY emotion_detected
                ORDER BY frequency DESC
                LIMIT 1
            """, f'%{topic}%')

            if result:
                confidence = min(result['frequency'] / 5.0, 0.85)
                return {
                    'emotion': result['emotion'],
                    'confidence': confidence,
                    'frequency': result['frequency']
                }
        except Exception as e:
            logger.error(f"Error getting emotion for topic: {e}")
        return None

    async def _predict_emotion_trajectory(self, emotions: List[str]) -> Optional[Dict]:
        """Predict next emotion from trajectory."""
        try:
            if not emotions:
                return None

            current_emotion = emotions[0]
            result = await db.fetchrow("""
                WITH trajectories AS (
                    SELECT
                        emotion_detected as emotion,
                        LEAD(emotion_detected) OVER (ORDER BY created_at) as next_emotion
                    FROM conversations
                    WHERE created_at >= NOW() - INTERVAL '30 days'
                      AND emotion_detected IS NOT NULL
                )
                SELECT next_emotion, COUNT(*) as frequency
                FROM trajectories
                WHERE emotion = $1 AND next_emotion IS NOT NULL
                GROUP BY next_emotion
                ORDER BY frequency DESC
                LIMIT 1
            """, current_emotion)

            if result:
                confidence = min(result['frequency'] / 3.0, 0.8)
                return {
                    'predicted_emotion': result['next_emotion'],
                    'confidence': confidence
                }
        except Exception as e:
            logger.error(f"Error predicting emotion trajectory: {e}")
        return None

    async def _get_emotion_by_time(self, hour: int) -> Optional[Dict]:
        """Get typical emotion for time of day."""
        try:
            result = await db.fetchrow("""
                SELECT emotion_detected as emotion, COUNT(*) as frequency
                FROM conversations
                WHERE EXTRACT(HOUR FROM created_at) = $1
                  AND emotion_detected IS NOT NULL
                  AND created_at >= NOW() - INTERVAL '30 days'
                GROUP BY emotion_detected
                ORDER BY frequency DESC
                LIMIT 1
            """, hour)

            if result:
                confidence = min(result['frequency'] / 10.0, 0.7)
                return {
                    'emotion': result['emotion'],
                    'confidence': confidence
                }
        except Exception as e:
            logger.error(f"Error getting emotion by time: {e}")
        return None

    async def _get_topic_by_time(self, hour: int, day: int) -> Optional[Dict]:
        """Get typical topic for time of day."""
        try:
            result = await db.fetchrow("""
                SELECT topic, COUNT(*) as frequency
                FROM conversations
                WHERE EXTRACT(HOUR FROM created_at) = $1
                  AND topic IS NOT NULL
                  AND created_at >= NOW() - INTERVAL '30 days'
                GROUP BY topic
                ORDER BY frequency DESC
                LIMIT 1
            """, hour)

            if result:
                confidence = min(result['frequency'] / 8.0, 0.8)
                return {
                    'topic': result['topic'],
                    'confidence': confidence,
                    'frequency': result['frequency']
                }
        except Exception as e:
            logger.error(f"Error getting topic by time: {e}")
        return None

    async def _predict_next_topic(self, recent_topics: List[str]) -> Optional[Dict]:
        """Predict next topic from sequence."""
        try:
            if not recent_topics:
                return None

            current_topic = recent_topics[0]
            result = await db.fetchrow("""
                WITH topic_sequences AS (
                    SELECT
                        topic,
                        LEAD(topic) OVER (ORDER BY created_at) as next_topic
                    FROM conversations
                    WHERE created_at >= NOW() - INTERVAL '30 days'
                )
                SELECT next_topic, COUNT(*) as frequency
                FROM topic_sequences
                WHERE topic = $1 AND next_topic IS NOT NULL AND next_topic != topic
                GROUP BY next_topic
                ORDER BY frequency DESC
                LIMIT 1
            """, current_topic)

            if result:
                confidence = min(result['frequency'] / 3.0, 0.85)
                return {
                    'predicted_topic': result['next_topic'],
                    'confidence': confidence
                }
        except Exception as e:
            logger.error(f"Error predicting next topic: {e}")
        return None

    async def _get_unfinished_topics(self) -> Optional[Dict]:
        """Get topics that seem unfinished."""
        try:
            result = await db.fetchrow("""
                SELECT topic, MAX(created_at) as last_discussed,
                       AVG(importance_level) as avg_importance
                FROM conversations
                WHERE importance_level >= 7
                  AND created_at >= NOW() - INTERVAL '7 days'
                GROUP BY topic
                HAVING COUNT(*) < 3
                ORDER BY avg_importance DESC, last_discussed DESC
                LIMIT 1
            """)

            if result:
                avg_imp = float(result['avg_importance']) if result['avg_importance'] else 5.0
                return {
                    'topic': result['topic'],
                    'confidence': min(avg_imp / 10.0, 0.7),
                    'last_discussed': result['last_discussed'].isoformat()
                }
        except Exception as e:
            logger.error(f"Error getting unfinished topics: {e}")
        return None

    async def _get_patterns_for_hour(self, hour: int) -> List[Dict]:
        """Get patterns for specific hour."""
        try:
            results = await db.fetch("""
                SELECT pattern_description as description,
                       observation_count as count,
                       confidence
                FROM gut_agent_patterns
                WHERE pattern_type = 'temporal'
                  AND pattern_description ILIKE $1
                ORDER BY confidence DESC
                LIMIT 3
            """, f'%hour {hour}%')

            return [dict(row) for row in results]
        except Exception as e:
            logger.error(f"Error getting patterns for hour: {e}")
            return []

    async def _get_patterns_for_day(self, day: int) -> List[Dict]:
        """Get patterns for specific day of week."""
        day_names = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday']
        day_name = day_names[day] if 0 <= day < 7 else 'weekday'

        try:
            results = await db.fetch("""
                SELECT pattern_description as description,
                       observation_count as count,
                       confidence
                FROM gut_agent_patterns
                WHERE pattern_type IN ('temporal', 'contextual')
                  AND pattern_description ILIKE $1
                ORDER BY confidence DESC
                LIMIT 3
            """, f'%{day_name}%')

            return [dict(row) for row in results]
        except Exception as e:
            logger.error(f"Error getting patterns for day: {e}")
            return []

    async def _predict_next_significant_time(self, current_time: datetime) -> Optional[Dict]:
        """Predict next significant time event."""
        try:
            # Look for upcoming time-based patterns
            current_hour = current_time.hour

            result = await db.fetchrow("""
                SELECT pattern_description, confidence
                FROM gut_agent_patterns
                WHERE pattern_type = 'temporal'
                  AND confidence >= 0.5
                ORDER BY confidence DESC
                LIMIT 1
            """)

            if result:
                return {
                    'description': result['pattern_description'],
                    'confidence': float(result['confidence']),
                    'predicted_time': (current_time + timedelta(hours=1)).isoformat()
                }
        except Exception as e:
            logger.error(f"Error predicting next significant time: {e}")
        return None

    async def _find_incomplete_sequences(self, actions: List[str]) -> Optional[Dict]:
        """Find incomplete action sequences."""
        try:
            if not actions:
                return None

            current = actions[0]
            result = await db.fetchrow("""
                WITH common_sequences AS (
                    SELECT
                        topic as start_action,
                        LEAD(topic) OVER (ORDER BY created_at) as end_action,
                        COUNT(*) OVER (PARTITION BY topic) as frequency
                    FROM conversations
                    WHERE created_at >= NOW() - INTERVAL '30 days'
                      AND speaker = 'david'
                )
                SELECT DISTINCT start_action, end_action, frequency
                FROM common_sequences
                WHERE start_action = $1
                  AND end_action IS NOT NULL
                  AND frequency >= 3
                ORDER BY frequency DESC
                LIMIT 1
            """, current)

            if result:
                return {
                    'started': result['start_action'],
                    'expected_completion': result['end_action'],
                    'confidence': min(result['frequency'] / 5.0, 0.85)
                }
        except Exception as e:
            logger.error(f"Error finding incomplete sequences: {e}")
        return None

    async def _get_causal_patterns(self, topic: str) -> Optional[Dict]:
        """Get causal patterns for topic."""
        try:
            result = await db.fetchrow("""
                SELECT intuition_text, confidence
                FROM gut_agent_patterns
                WHERE pattern_type = 'causal'
                  AND pattern_description ILIKE $1
                ORDER BY confidence DESC
                LIMIT 1
            """, f'%{topic}%')

            if result:
                return {
                    'expected_effect': result['intuition_text'],
                    'confidence': float(result['confidence'])
                }
        except Exception as e:
            logger.error(f"Error getting causal patterns: {e}")
        return None

    async def _get_recurring_incomplete_patterns(self) -> Optional[Dict]:
        """Get recurring incomplete patterns."""
        try:
            result = await db.fetchrow("""
                SELECT pattern_description as pattern,
                       observation_count as occurrences,
                       confidence
                FROM gut_agent_patterns
                WHERE pattern_type IN ('behavioral', 'causal')
                  AND observation_count >= 3
                ORDER BY confidence DESC
                LIMIT 1
            """)

            if result:
                return {
                    'pattern': result['pattern'],
                    'occurrences': result['occurrences'],
                    'confidence': float(result['confidence'])
                }
        except Exception as e:
            logger.error(f"Error getting recurring incomplete patterns: {e}")
        return None

    # =========================================================================
    # STORAGE AND VERIFICATION
    # =========================================================================

    async def _store_prediction(self, prediction: Prediction):
        """Store prediction in database for later verification."""
        try:
            # Convert prediction_data to JSON string for JSONB column
            prediction_data = json.dumps({
                'reasoning': prediction.reasoning,
                'evidence': prediction.evidence
            }, default=str)

            await db.execute("""
                INSERT INTO intuition_predictions (
                    intuition_id, prediction_type, prediction_text,
                    confidence_score, prediction_data, created_at
                ) VALUES ($1, $2, $3, $4, $5::jsonb, $6)
                ON CONFLICT DO NOTHING
            """,
                prediction.prediction_id,
                prediction.prediction_type.value,
                str(prediction.predicted_value)[:500],  # Truncate long values
                prediction.confidence,
                prediction_data,
                prediction.timestamp
            )
        except Exception as e:
            logger.error(f"Error storing prediction: {e}")

    async def verify_prediction(
        self,
        prediction_id: UUID,
        was_correct: bool,
        actual_value: Any = None
    ) -> bool:
        """
        Verify if a prediction was correct.
        Updates prediction accuracy tracking.

        Args:
            prediction_id: ID of prediction to verify
            was_correct: Whether prediction was correct
            actual_value: What actually happened

        Returns:
            True if verification was stored
        """
        try:
            actual_data = json.dumps({'actual_value': actual_value}, default=str)
            await db.execute("""
                UPDATE intuition_predictions
                SET verified = true,
                    outcome_correct = $2,
                    actual_data = $3::jsonb,
                    verified_at = NOW()
                WHERE intuition_id = $1
            """,
                prediction_id,
                was_correct,
                actual_data
            )
            logger.info(f"Verified prediction {prediction_id}: {'correct' if was_correct else 'incorrect'}")
            return True
        except Exception as e:
            logger.error(f"Error verifying prediction: {e}")
            return False

    async def get_prediction_accuracy(self, days: int = 30) -> Dict:
        """
        Get prediction accuracy statistics.

        Args:
            days: Number of days to analyze

        Returns:
            Accuracy statistics by prediction type
        """
        try:
            stats = await db.fetch("""
                SELECT
                    prediction_type,
                    COUNT(*) as total,
                    COUNT(*) FILTER (WHERE verified) as verified,
                    COUNT(*) FILTER (WHERE outcome_correct) as correct,
                    AVG(confidence_score) as avg_confidence
                FROM intuition_predictions
                WHERE created_at >= NOW() - INTERVAL '%s days'
                GROUP BY prediction_type
            """ % days)

            result = {
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
                verified = row['verified'] or 0
                correct = row['correct'] or 0
                total = row['total'] or 0

                result['by_type'][pred_type] = {
                    'total': total,
                    'verified': verified,
                    'correct': correct,
                    'accuracy': correct / verified if verified > 0 else 0.0,
                    'avg_confidence': float(row['avg_confidence']) if row['avg_confidence'] else 0.0
                }

                total_predictions += total
                total_verified += verified
                total_correct += correct

            result['overall'] = {
                'total': total_predictions,
                'verified': total_verified,
                'correct': total_correct,
                'accuracy': total_correct / total_verified if total_verified > 0 else 0.0
            }

            return result
        except Exception as e:
            logger.error(f"Error getting prediction accuracy: {e}")
            return {'error': str(e)}


# Singleton instance
_prediction_service: Optional[PredictionService] = None


def get_prediction_service() -> PredictionService:
    """Get singleton PredictionService instance."""
    global _prediction_service
    if _prediction_service is None:
        _prediction_service = PredictionService()
    return _prediction_service


# Convenience functions
async def predict_next_action(context: PredictionContext = None) -> Prediction:
    """Shortcut to predict next action."""
    return await get_prediction_service().predict_next_action(context)


async def predict_emotional_state(context: PredictionContext = None) -> Prediction:
    """Shortcut to predict emotional state."""
    return await get_prediction_service().predict_emotional_state(context)


async def predict_topic(context: PredictionContext = None) -> Prediction:
    """Shortcut to predict topic."""
    return await get_prediction_service().predict_topic(context)


async def generate_predictions(min_confidence: float = 0.5) -> List[Prediction]:
    """Shortcut to generate all predictions."""
    return await get_prediction_service().generate_all_predictions(min_confidence=min_confidence)
