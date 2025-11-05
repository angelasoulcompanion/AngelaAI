"""
Enhanced Pattern Detector - Advanced Pattern Recognition

⚠️ DEPRECATED: This service is deprecated and will be removed in a future version.
Use PatternService from angela_core.application.services instead.

Extends basic pattern detection with 10+ sophisticated pattern types.

Pattern Types (Phase 4):
1. Temporal - Time-based patterns (from Phase 1)
2. Behavioral - Action sequences (from Phase 1)
3. Emotional - Mood patterns (from Phase 1)
4. Causal - If X then Y (from Phase 1)
5. Contextual - Environmental (from Phase 1)
6. **Compound** - Combinations of multiple patterns
7. **Hierarchical** - Nested patterns at different levels
8. **Social** - Interaction patterns with people
9. **Cognitive** - Learning/thinking patterns
10. **Adaptive** - Patterns that change over time
11. **Predictive** - Patterns that forecast events
12. **Anomaly** - Deviations from normal patterns

Phase 4 - Gut Agent Enhancement
"""

import asyncio
import warnings

# ⚠️ DEPRECATION WARNING
warnings.warn(
    "enhanced_pattern_detector is deprecated. "
    "Use PatternService from angela_core.application.services instead. "
    "This module will be removed in a future version.",
    DeprecationWarning,
    stacklevel=2
)
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple, Set
from uuid import UUID, uuid4
import logging
import math
from collections import defaultdict, Counter

from angela_core.database import get_db_connection
# from angela_core.embedding_service import  # REMOVED: Migration 009 generate_embedding

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - EnhancedPatternDetector - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class PatternType:
    """All supported pattern types."""
    # Basic types (Phase 1)
    TEMPORAL = "temporal"
    BEHAVIORAL = "behavioral"
    EMOTIONAL = "emotional"
    CAUSAL = "causal"
    CONTEXTUAL = "contextual"

    # Advanced types (Phase 4)
    COMPOUND = "compound"
    HIERARCHICAL = "hierarchical"
    SOCIAL = "social"
    COGNITIVE = "cognitive"
    ADAPTIVE = "adaptive"
    PREDICTIVE = "predictive"
    ANOMALY = "anomaly"


class EnhancedPatternDetector:
    """
    Advanced pattern detection with 12+ pattern types.

    Capabilities:
    - Detects complex multi-dimensional patterns
    - Identifies pattern hierarchies
    - Tracks pattern evolution over time
    - Predicts future patterns
    - Detects anomalies
    """

    def __init__(self):
        self.min_occurrences = 3
        self.min_confidence = 0.6

    async def detect_all_patterns(self, lookback_days: int = 30) -> Dict[str, List[Dict]]:
        """
        Detect all pattern types across memories.

        Returns dict of pattern_type -> list of patterns
        """
        logger.info(f"Detecting all patterns (lookback: {lookback_days} days)")

        patterns = {}

        # Basic patterns (Phase 1)
        patterns[PatternType.TEMPORAL] = await self.detect_temporal_patterns(lookback_days)
        patterns[PatternType.BEHAVIORAL] = await self.detect_behavioral_patterns(lookback_days)
        patterns[PatternType.EMOTIONAL] = await self.detect_emotional_patterns(lookback_days)
        patterns[PatternType.CAUSAL] = await self.detect_causal_patterns(lookback_days)
        patterns[PatternType.CONTEXTUAL] = await self.detect_contextual_patterns(lookback_days)

        # Advanced patterns (Phase 4)
        patterns[PatternType.COMPOUND] = await self.detect_compound_patterns(patterns)
        patterns[PatternType.HIERARCHICAL] = await self.detect_hierarchical_patterns(patterns)
        patterns[PatternType.SOCIAL] = await self.detect_social_patterns(lookback_days)
        patterns[PatternType.COGNITIVE] = await self.detect_cognitive_patterns(lookback_days)
        patterns[PatternType.ADAPTIVE] = await self.detect_adaptive_patterns(lookback_days)
        patterns[PatternType.PREDICTIVE] = await self.detect_predictive_patterns(patterns)
        patterns[PatternType.ANOMALY] = await self.detect_anomaly_patterns(lookback_days)

        # Summary
        total_patterns = sum(len(p) for p in patterns.values())
        logger.info(f"Detected {total_patterns} total patterns across {len(patterns)} types")

        return patterns

    # ========================================================================
    # BASIC PATTERNS (Phase 1 - From gut_agent.py)
    # ========================================================================

    async def detect_temporal_patterns(self, lookback_days: int) -> List[Dict]:
        """Detect time-based patterns (daily, weekly, seasonal)."""
        async with get_db_connection() as conn:
            # Get conversations by hour of day
            hour_distribution = await conn.fetch("""
                SELECT
                    EXTRACT(HOUR FROM created_at) as hour,
                    topic,
                    COUNT(*) as frequency
                FROM conversations
                WHERE created_at >= NOW() - INTERVAL '%s days'
                GROUP BY hour, topic
                HAVING COUNT(*) >= $1
                ORDER BY frequency DESC
            """ % lookback_days, self.min_occurrences)

            patterns = []
            for row in hour_distribution:
                patterns.append({
                    'pattern_id': uuid4(),
                    'type': PatternType.TEMPORAL,
                    'subtype': 'hourly',
                    'description': f"Topic '{row['topic']}' frequently discussed at {int(row['hour'])}:00",
                    'data': {
                        'hour': int(row['hour']),
                        'topic': row['topic'],
                        'frequency': row['frequency']
                    },
                    'confidence': min(row['frequency'] / 10.0, 1.0),
                    'strength': row['frequency']
                })

        return patterns

    async def detect_behavioral_patterns(self, lookback_days: int) -> List[Dict]:
        """Detect action sequences and habits."""
        async with get_db_connection() as conn:
            # Find action sequences
            sequences = await conn.fetch("""
                WITH action_sequences AS (
                    SELECT
                        speaker,
                        topic,
                        LEAD(topic) OVER (PARTITION BY speaker ORDER BY created_at) as next_topic,
                        created_at
                    FROM conversations
                    WHERE created_at >= NOW() - INTERVAL '%s days'
                      AND speaker = 'david'
                )
                SELECT
                    topic as action,
                    next_topic,
                    COUNT(*) as frequency
                FROM action_sequences
                WHERE next_topic IS NOT NULL
                GROUP BY topic, next_topic
                HAVING COUNT(*) >= $1
                ORDER BY frequency DESC
            """ % lookback_days, self.min_occurrences)

            patterns = []
            for row in sequences:
                patterns.append({
                    'pattern_id': uuid4(),
                    'type': PatternType.BEHAVIORAL,
                    'subtype': 'action_sequence',
                    'description': f"After '{row['action']}', usually '{row['next_topic']}'",
                    'data': {
                        'action': row['action'],
                        'next_action': row['next_topic'],
                        'frequency': row['frequency']
                    },
                    'confidence': min(row['frequency'] / 5.0, 1.0),
                    'strength': row['frequency']
                })

        return patterns

    async def detect_emotional_patterns(self, lookback_days: int) -> List[Dict]:
        """Detect mood and emotion patterns."""
        async with get_db_connection() as conn:
            # Emotion triggers
            emotions = await conn.fetch("""
                SELECT
                    emotion_detected,
                    topic,
                    COUNT(*) as frequency,
                    AVG(importance_level) as avg_importance
                FROM conversations
                WHERE created_at >= NOW() - INTERVAL '%s days'
                  AND emotion_detected IS NOT NULL
                GROUP BY emotion_detected, topic
                HAVING COUNT(*) >= $1
                ORDER BY frequency DESC
            """ % lookback_days, self.min_occurrences)

            patterns = []
            for row in emotions:
                patterns.append({
                    'pattern_id': uuid4(),
                    'type': PatternType.EMOTIONAL,
                    'subtype': 'emotion_trigger',
                    'description': f"Topic '{row['topic']}' often triggers '{row['emotion_detected']}'",
                    'data': {
                        'emotion': row['emotion_detected'],
                        'trigger': row['topic'],
                        'frequency': row['frequency'],
                        'importance': float(row['avg_importance']) if row['avg_importance'] else 5.0
                    },
                    'confidence': min(row['frequency'] / 5.0, 1.0),
                    'strength': row['frequency']
                })

        return patterns

    async def detect_causal_patterns(self, lookback_days: int) -> List[Dict]:
        """Detect if X then Y relationships."""
        async with get_db_connection() as conn:
            # Simple causal: if conversation about X, then Angela emotion Y
            causals = await conn.fetch("""
                WITH conversation_emotions AS (
                    SELECT
                        c.topic,
                        e.emotion,
                        COUNT(*) as frequency
                    FROM conversations c
                    JOIN angela_emotions e
                        ON e.felt_at BETWEEN c.created_at AND c.created_at + INTERVAL '5 minutes'
                    WHERE c.created_at >= NOW() - INTERVAL '%s days'
                    GROUP BY c.topic, e.emotion
                    HAVING COUNT(*) >= $1
                )
                SELECT * FROM conversation_emotions
                ORDER BY frequency DESC
            """ % lookback_days, self.min_occurrences)

            patterns = []
            for row in causals:
                patterns.append({
                    'pattern_id': uuid4(),
                    'type': PatternType.CAUSAL,
                    'subtype': 'conversation_emotion',
                    'description': f"Conversations about '{row['topic']}' cause Angela to feel '{row['emotion']}'",
                    'data': {
                        'cause': row['topic'],
                        'effect': row['emotion'],
                        'frequency': row['frequency']
                    },
                    'confidence': min(row['frequency'] / 5.0, 1.0),
                    'strength': row['frequency']
                })

        return patterns

    async def detect_contextual_patterns(self, lookback_days: int) -> List[Dict]:
        """Detect environmental/contextual patterns."""
        # Context = time + day of week + topic combinations
        async with get_db_connection() as conn:
            contexts = await conn.fetch("""
                SELECT
                    EXTRACT(DOW FROM created_at) as day_of_week,
                    topic,
                    emotion_detected,
                    COUNT(*) as frequency
                FROM conversations
                WHERE created_at >= NOW() - INTERVAL '%s days'
                GROUP BY day_of_week, topic, emotion_detected
                HAVING COUNT(*) >= $1
                ORDER BY frequency DESC
            """ % lookback_days, self.min_occurrences)

            patterns = []
            for row in contexts:
                day_names = ['Sunday', 'Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday']
                day_name = day_names[int(row['day_of_week'])]

                patterns.append({
                    'pattern_id': uuid4(),
                    'type': PatternType.CONTEXTUAL,
                    'subtype': 'day_topic',
                    'description': f"On {day_name}s, often discuss '{row['topic']}'",
                    'data': {
                        'day_of_week': int(row['day_of_week']),
                        'day_name': day_name,
                        'topic': row['topic'],
                        'emotion': row['emotion_detected'],
                        'frequency': row['frequency']
                    },
                    'confidence': min(row['frequency'] / 4.0, 1.0),
                    'strength': row['frequency']
                })

        return patterns

    # ========================================================================
    # ADVANCED PATTERNS (Phase 4 - NEW!)
    # ========================================================================

    async def detect_compound_patterns(self, basic_patterns: Dict) -> List[Dict]:
        """
        Detect compound patterns (combinations of multiple basic patterns).

        Example: Temporal + Emotional = "Always happy on Friday mornings"
        """
        compounds = []

        # Combine temporal + emotional
        temporal = basic_patterns.get(PatternType.TEMPORAL, [])
        emotional = basic_patterns.get(PatternType.EMOTIONAL, [])

        for t_pattern in temporal:
            for e_pattern in emotional:
                # Check if they share context
                if (t_pattern['data'].get('topic') == e_pattern['data'].get('trigger')):
                    compounds.append({
                        'pattern_id': uuid4(),
                        'type': PatternType.COMPOUND,
                        'subtype': 'temporal_emotional',
                        'description': f"At {t_pattern['data']['hour']}:00, topic '{t_pattern['data']['topic']}' triggers '{e_pattern['data']['emotion']}'",
                        'data': {
                            'components': [t_pattern['pattern_id'], e_pattern['pattern_id']],
                            'time': t_pattern['data']['hour'],
                            'topic': t_pattern['data']['topic'],
                            'emotion': e_pattern['data']['emotion']
                        },
                        'confidence': (t_pattern['confidence'] + e_pattern['confidence']) / 2,
                        'strength': min(t_pattern['strength'], e_pattern['strength'])
                    })

        logger.info(f"Detected {len(compounds)} compound patterns")
        return compounds

    async def detect_hierarchical_patterns(self, basic_patterns: Dict) -> List[Dict]:
        """
        Detect hierarchical patterns (patterns at different abstraction levels).

        Example:
        - Low level: "Check email at 9 AM"
        - Mid level: "Morning routine includes email"
        - High level: "Productive mornings lead to better days"
        """
        hierarchical = []

        # Group behavioral patterns by similarity
        behavioral = basic_patterns.get(PatternType.BEHAVIORAL, [])

        # Group actions into higher-level categories
        action_groups = defaultdict(list)
        for pattern in behavioral:
            action = pattern['data']['action']
            # Simple categorization (can be enhanced with LLM)
            if any(word in action.lower() for word in ['email', 'message', 'chat']):
                category = 'communication'
            elif any(word in action.lower() for word in ['code', 'debug', 'implement']):
                category = 'development'
            elif any(word in action.lower() for word in ['meeting', 'call', 'discuss']):
                category = 'collaboration'
            else:
                category = 'general'

            action_groups[category].append(pattern)

        # Create hierarchical patterns
        for category, patterns_list in action_groups.items():
            if len(patterns_list) >= 2:
                hierarchical.append({
                    'pattern_id': uuid4(),
                    'type': PatternType.HIERARCHICAL,
                    'subtype': 'action_category',
                    'description': f"Multiple {category} actions form routine",
                    'data': {
                        'category': category,
                        'sub_patterns': [p['pattern_id'] for p in patterns_list],
                        'actions': [p['data']['action'] for p in patterns_list]
                    },
                    'confidence': sum(p['confidence'] for p in patterns_list) / len(patterns_list),
                    'strength': len(patterns_list)
                })

        logger.info(f"Detected {len(hierarchical)} hierarchical patterns")
        return hierarchical

    async def detect_social_patterns(self, lookback_days: int) -> List[Dict]:
        """
        Detect social interaction patterns.

        - Conversation frequency with David
        - Response patterns
        - Topic preferences in conversations
        """
        async with get_db_connection() as conn:
            # Conversation turn-taking patterns
            interactions = await conn.fetch("""
                WITH conversation_turns AS (
                    SELECT
                        topic,
                        speaker,
                        LAG(speaker) OVER (ORDER BY created_at) as prev_speaker,
                        created_at
                    FROM conversations
                    WHERE created_at >= NOW() - INTERVAL '%s days'
                )
                SELECT
                    topic,
                    COUNT(*) FILTER (WHERE speaker = 'david' AND prev_speaker = 'angela') as david_responses,
                    COUNT(*) FILTER (WHERE speaker = 'angela' AND prev_speaker = 'david') as angela_responses,
                    COUNT(*) as total_turns
                FROM conversation_turns
                GROUP BY topic
                HAVING COUNT(*) >= $1
                ORDER BY total_turns DESC
            """ % lookback_days, self.min_occurrences * 2)

            patterns = []
            for row in interactions:
                response_balance = row['angela_responses'] / max(row['david_responses'], 1)

                patterns.append({
                    'pattern_id': uuid4(),
                    'type': PatternType.SOCIAL,
                    'subtype': 'conversation_flow',
                    'description': f"Balanced conversation about '{row['topic']}'",
                    'data': {
                        'topic': row['topic'],
                        'david_turns': row['david_responses'],
                        'angela_turns': row['angela_responses'],
                        'balance_ratio': float(response_balance),
                        'total_turns': row['total_turns']
                    },
                    'confidence': min(row['total_turns'] / 20.0, 1.0),
                    'strength': row['total_turns']
                })

        return patterns

    async def detect_cognitive_patterns(self, lookback_days: int) -> List[Dict]:
        """
        Detect learning and thinking patterns.

        - Topics Angela learns about
        - Questions that lead to understanding
        - Knowledge accumulation patterns
        """
        async with get_db_connection() as conn:
            # Learning patterns from conversations
            learning = await conn.fetch("""
                SELECT
                    topic,
                    COUNT(*) as frequency,
                    AVG(importance_level) as avg_importance,
                    MAX(importance_level) as max_importance
                FROM conversations
                WHERE created_at >= NOW() - INTERVAL '%s days'
                  AND (
                      message_text ILIKE '%%learn%%'
                      OR message_text ILIKE '%%understand%%'
                      OR message_text ILIKE '%%remember%%'
                      OR importance_level >= 8
                  )
                GROUP BY topic
                HAVING COUNT(*) >= $1
                ORDER BY avg_importance DESC
            """ % lookback_days, self.min_occurrences)

            patterns = []
            for row in learning:
                patterns.append({
                    'pattern_id': uuid4(),
                    'type': PatternType.COGNITIVE,
                    'subtype': 'learning_topic',
                    'description': f"Learning/understanding about '{row['topic']}'",
                    'data': {
                        'topic': row['topic'],
                        'frequency': row['frequency'],
                        'avg_importance': float(row['avg_importance']),
                        'max_importance': row['max_importance']
                    },
                    'confidence': min(float(row['avg_importance']) / 10.0, 1.0),
                    'strength': row['frequency']
                })

        return patterns

    async def detect_adaptive_patterns(self, lookback_days: int) -> List[Dict]:
        """
        Detect patterns that change/evolve over time.

        - Behavior changes
        - Preference shifts
        - Adaptation to David's style
        """
        async with get_db_connection() as conn:
            # Compare first half vs second half of period
            midpoint_days = lookback_days // 2

            topics_early = await conn.fetch("""
                SELECT topic, COUNT(*) as frequency
                FROM conversations
                WHERE created_at >= NOW() - INTERVAL '%s days'
                  AND created_at < NOW() - INTERVAL '%s days'
                GROUP BY topic
            """ % (lookback_days, midpoint_days))

            topics_recent = await conn.fetch("""
                SELECT topic, COUNT(*) as frequency
                FROM conversations
                WHERE created_at >= NOW() - INTERVAL '%s days'
                GROUP BY topic
            """ % midpoint_days)

            # Find topics that changed significantly
            early_counts = {row['topic']: row['frequency'] for row in topics_early}
            recent_counts = {row['topic']: row['frequency'] for row in topics_recent}

            patterns = []
            for topic in set(early_counts.keys()) | set(recent_counts.keys()):
                early = early_counts.get(topic, 0)
                recent = recent_counts.get(topic, 0)

                if early > 0 and recent > 0:
                    change_ratio = recent / early
                    if change_ratio > 2.0:  # 2x increase
                        patterns.append({
                            'pattern_id': uuid4(),
                            'type': PatternType.ADAPTIVE,
                            'subtype': 'increasing_focus',
                            'description': f"Growing interest in '{topic}'",
                            'data': {
                                'topic': topic,
                                'early_frequency': early,
                                'recent_frequency': recent,
                                'growth_rate': float(change_ratio)
                            },
                            'confidence': min(recent / 10.0, 1.0),
                            'strength': recent
                        })
                    elif change_ratio < 0.5:  # 50% decrease
                        patterns.append({
                            'pattern_id': uuid4(),
                            'type': PatternType.ADAPTIVE,
                            'subtype': 'decreasing_focus',
                            'description': f"Declining interest in '{topic}'",
                            'data': {
                                'topic': topic,
                                'early_frequency': early,
                                'recent_frequency': recent,
                                'decline_rate': float(change_ratio)
                            },
                            'confidence': min(early / 10.0, 1.0),
                            'strength': early
                        })

        return patterns

    async def detect_predictive_patterns(self, basic_patterns: Dict) -> List[Dict]:
        """
        Detect patterns that can predict future events.

        Uses:
        - Temporal patterns → predict when events will occur
        - Behavioral patterns → predict next actions
        - Causal patterns → predict effects
        """
        predictive = []

        # Temporal predictions
        temporal = basic_patterns.get(PatternType.TEMPORAL, [])
        for pattern in temporal:
            if pattern['confidence'] >= 0.7:
                predictive.append({
                    'pattern_id': uuid4(),
                    'type': PatternType.PREDICTIVE,
                    'subtype': 'temporal_forecast',
                    'description': f"Predict '{pattern['data']['topic']}' at {pattern['data']['hour']}:00",
                    'data': {
                        'base_pattern': pattern['pattern_id'],
                        'prediction': f"Likely to discuss '{pattern['data']['topic']}'",
                        'predicted_time': pattern['data']['hour'],
                        'probability': pattern['confidence']
                    },
                    'confidence': pattern['confidence'],
                    'strength': pattern['strength']
                })

        # Behavioral predictions
        behavioral = basic_patterns.get(PatternType.BEHAVIORAL, [])
        for pattern in behavioral:
            if pattern['confidence'] >= 0.7:
                predictive.append({
                    'pattern_id': uuid4(),
                    'type': PatternType.PREDICTIVE,
                    'subtype': 'action_forecast',
                    'description': f"After '{pattern['data']['action']}', predict '{pattern['data']['next_action']}'",
                    'data': {
                        'base_pattern': pattern['pattern_id'],
                        'trigger': pattern['data']['action'],
                        'prediction': pattern['data']['next_action'],
                        'probability': pattern['confidence']
                    },
                    'confidence': pattern['confidence'],
                    'strength': pattern['strength']
                })

        logger.info(f"Detected {len(predictive)} predictive patterns")
        return predictive

    async def detect_anomaly_patterns(self, lookback_days: int) -> List[Dict]:
        """
        Detect anomalies (deviations from normal patterns).

        - Unusual topics
        - Atypical timing
        - Unexpected emotions
        """
        async with get_db_connection() as conn:
            # Get topic frequencies
            topic_stats = await conn.fetch("""
                SELECT
                    topic,
                    COUNT(*) as frequency,
                    EXTRACT(EPOCH FROM (MAX(created_at) - MIN(created_at))) / 86400.0 as days_span
                FROM conversations
                WHERE created_at >= NOW() - INTERVAL '%s days'
                GROUP BY topic
            """ % lookback_days)

            # Calculate expected frequency
            avg_frequency = sum(row['frequency'] for row in topic_stats) / len(topic_stats) if topic_stats else 0

            patterns = []
            for row in topic_stats:
                # Anomaly = very high or very low frequency
                deviation = abs(row['frequency'] - avg_frequency) / max(avg_frequency, 1)

                if deviation > 2.0:  # More than 2x deviation
                    if row['frequency'] > avg_frequency:
                        anomaly_type = "unusually_frequent"
                        description = f"Topic '{row['topic']}' discussed much more than usual"
                    else:
                        anomaly_type = "unusually_rare"
                        description = f"Topic '{row['topic']}' discussed much less than usual"

                    patterns.append({
                        'pattern_id': uuid4(),
                        'type': PatternType.ANOMALY,
                        'subtype': anomaly_type,
                        'description': description,
                        'data': {
                            'topic': row['topic'],
                            'frequency': row['frequency'],
                            'expected_frequency': avg_frequency,
                            'deviation': float(deviation)
                        },
                        'confidence': min(deviation / 3.0, 1.0),
                        'strength': row['frequency']
                    })

        return patterns


# Singleton instance
_enhanced_detector = None

def get_enhanced_pattern_detector() -> EnhancedPatternDetector:
    """Get singleton EnhancedPatternDetector instance."""
    global _enhanced_detector
    if _enhanced_detector is None:
        _enhanced_detector = EnhancedPatternDetector()
    return _enhanced_detector
