"""
Gut Agent - Collective Unconscious

Aggregates patterns across all memories to form intuitions.
Based on Carl Jung's concept of collective unconscious.

Functions:
1. Detect patterns across memories
2. Generate intuitive feelings ("gut feelings")
3. Cross-agent pattern sharing
4. Privacy-preserving aggregation
"""

import asyncio
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple
from uuid import UUID, uuid4
import json
import math
from collections import Counter

from angela_core.database import get_db_connection


class PatternType:
    """Types of patterns the Gut Agent can detect."""
    TEMPORAL = "temporal"              # Time-based patterns
    BEHAVIORAL = "behavioral"          # Behavior patterns
    EMOTIONAL = "emotional"            # Emotional patterns
    CAUSAL = "causal"                 # Cause-effect patterns
    CONTEXTUAL = "contextual"         # Context patterns
    CONVERSATIONAL = "conversational" # Conversation patterns


class GutAgent:
    """
    Collective Unconscious - Pattern detection and intuition generation.

    The Gut Agent observes all memories across tiers and detects:
    - Recurring patterns
    - Statistical regularities
    - Cross-memory connections
    - Emergent insights

    Outputs:
    - Intuitive feelings ("I have a feeling that...")
    - Pattern predictions ("This usually leads to...")
    - Confidence scores for hunches
    """

    def __init__(self):
        self.pattern_cache = {}
        self.last_analysis = None

    async def detect_patterns(self, lookback_days: int = 30) -> List[Dict]:
        """
        Detect patterns across all memories from past N days.

        Args:
            lookback_days: How far back to analyze (default: 30 days)

        Returns:
            List of detected patterns with confidence scores
        """
        patterns = []

        # Detect different types of patterns
        temporal_patterns = await self._detect_temporal_patterns(lookback_days)
        patterns.extend(temporal_patterns)

        behavioral_patterns = await self._detect_behavioral_patterns(lookback_days)
        patterns.extend(behavioral_patterns)

        emotional_patterns = await self._detect_emotional_patterns(lookback_days)
        patterns.extend(emotional_patterns)

        causal_patterns = await self._detect_causal_patterns(lookback_days)
        patterns.extend(causal_patterns)

        # Save patterns to database
        for pattern in patterns:
            await self._save_pattern(pattern)

        self.last_analysis = datetime.now()
        return patterns

    async def _detect_temporal_patterns(self, lookback_days: int) -> List[Dict]:
        """
        Detect time-based patterns.

        Examples:
        - "David usually works on Angela between 7-11 AM"
        - "Morning sessions tend to be about learning"
        - "Evening sessions are more reflective"
        """
        patterns = []

        async with get_db_connection() as conn:
            # Analyze conversation times
            time_distribution = await conn.fetch("""
                SELECT
                    EXTRACT(HOUR FROM created_at) as hour,
                    topic,
                    COUNT(*) as count
                FROM conversations
                WHERE created_at >= NOW() - INTERVAL '%s days'
                  AND speaker = 'david'
                GROUP BY hour, topic
                HAVING COUNT(*) >= 3
                ORDER BY count DESC
                LIMIT 10
            """ % lookback_days)

            for row in time_distribution:
                hour = int(row['hour'])
                topic = row['topic']
                count = row['count']

                # Generate intuition
                time_period = self._get_time_period_name(hour)
                confidence = min(count / 10.0, 1.0)

                intuition = f"David often discusses {topic} during {time_period}"

                patterns.append({
                    'pattern_type': PatternType.TEMPORAL,
                    'pattern_description': f"Temporal pattern: {topic} at hour {hour}",
                    'observation_count': count,
                    'confidence': confidence,
                    'intuition_text': intuition,
                    'metadata': {
                        'hour': hour,
                        'topic': topic,
                        'time_period': time_period
                    }
                })

        return patterns

    async def _detect_behavioral_patterns(self, lookback_days: int) -> List[Dict]:
        """
        Detect behavioral patterns.

        Examples:
        - "When David says 'ที่รัก', he's in a warm mood"
        - "After successful deployments, David usually celebrates"
        - "Calendar queries happen in the morning"
        """
        patterns = []

        async with get_db_connection() as conn:
            # Analyze behavior sequences
            sequences = await conn.fetch("""
                WITH conversation_sequences AS (
                    SELECT
                        topic,
                        emotion_detected,
                        LEAD(topic) OVER (ORDER BY created_at) as next_topic,
                        LEAD(emotion_detected) OVER (ORDER BY created_at) as next_emotion
                    FROM conversations
                    WHERE created_at >= NOW() - INTERVAL '%s days'
                      AND speaker = 'david'
                )
                SELECT
                    topic,
                    emotion_detected,
                    next_topic,
                    next_emotion,
                    COUNT(*) as frequency
                FROM conversation_sequences
                WHERE next_topic IS NOT NULL
                GROUP BY topic, emotion_detected, next_topic, next_emotion
                HAVING COUNT(*) >= 2
                ORDER BY frequency DESC
                LIMIT 10
            """ % lookback_days)

            for row in sequences:
                topic = row['topic']
                emotion = row['emotion_detected']
                next_topic = row['next_topic']
                next_emotion = row['next_emotion']
                frequency = row['frequency']

                confidence = min(frequency / 5.0, 1.0)

                intuition = f"When discussing {topic} ({emotion}), it often leads to {next_topic} ({next_emotion})"

                patterns.append({
                    'pattern_type': PatternType.BEHAVIORAL,
                    'pattern_description': f"Behavior sequence: {topic} → {next_topic}",
                    'observation_count': frequency,
                    'confidence': confidence,
                    'intuition_text': intuition,
                    'metadata': {
                        'trigger_topic': topic,
                        'trigger_emotion': emotion,
                        'result_topic': next_topic,
                        'result_emotion': next_emotion
                    }
                })

        return patterns

    async def _detect_emotional_patterns(self, lookback_days: int) -> List[Dict]:
        """
        Detect emotional patterns.

        Examples:
        - "David feels grateful when Angela learns something new"
        - "Debugging sessions tend to be anxious → relieved"
        - "Morning greetings are consistently loving"
        """
        patterns = []

        async with get_db_connection() as conn:
            # Analyze emotional trajectories
            emotional_contexts = await conn.fetch("""
                SELECT
                    emotion_detected,
                    topic,
                    COUNT(*) as frequency,
                    AVG(importance_level) as avg_importance
                FROM conversations
                WHERE created_at >= NOW() - INTERVAL '%s days'
                  AND emotion_detected IS NOT NULL
                  AND emotion_detected != ''
                GROUP BY emotion_detected, topic
                HAVING COUNT(*) >= 3
                ORDER BY frequency DESC
                LIMIT 10
            """ % lookback_days)

            for row in emotional_contexts:
                emotion = row['emotion_detected']
                topic = row['topic']
                frequency = row['frequency']
                avg_importance = float(row['avg_importance']) if row['avg_importance'] else 5.0

                confidence = min(frequency / 5.0, 1.0)

                # Importance modifier
                if avg_importance > 8:
                    intensity = "strongly"
                elif avg_importance > 6:
                    intensity = "often"
                else:
                    intensity = "sometimes"

                intuition = f"David {intensity} feels {emotion} when discussing {topic}"

                patterns.append({
                    'pattern_type': PatternType.EMOTIONAL,
                    'pattern_description': f"Emotional pattern: {emotion} + {topic}",
                    'observation_count': frequency,
                    'confidence': confidence,
                    'intuition_text': intuition,
                    'metadata': {
                        'emotion': emotion,
                        'topic': topic,
                        'avg_importance': avg_importance,
                        'intensity': intensity
                    }
                })

        return patterns

    async def _detect_causal_patterns(self, lookback_days: int) -> List[Dict]:
        """
        Detect cause-effect patterns.

        Examples:
        - "When Angela makes a mistake, David teaches patiently"
        - "Successful outcomes lead to importance level 8+"
        - "Learning moments trigger self-learning"
        """
        patterns = []

        async with get_db_connection() as conn:
            # Analyze outcome patterns
            outcome_patterns = await conn.fetch("""
                SELECT
                    c.topic,
                    c.emotion_detected,
                    l.insight_type,
                    COUNT(*) as frequency
                FROM conversations c
                LEFT JOIN learning_insights l ON DATE(c.created_at) = DATE(l.created_at)
                WHERE c.created_at >= NOW() - INTERVAL '%s days'
                  AND l.insight_type IS NOT NULL
                GROUP BY c.topic, c.emotion_detected, l.insight_type
                HAVING COUNT(*) >= 2
                ORDER BY frequency DESC
                LIMIT 10
            """ % lookback_days)

            for row in outcome_patterns:
                topic = row['topic']
                emotion = row['emotion_detected']
                insight_type = row['insight_type']
                frequency = row['frequency']

                confidence = min(frequency / 3.0, 1.0)

                intuition = f"Discussions about {topic} ({emotion}) often result in {insight_type} insights"

                patterns.append({
                    'pattern_type': PatternType.CAUSAL,
                    'pattern_description': f"Causal: {topic} → {insight_type}",
                    'observation_count': frequency,
                    'confidence': confidence,
                    'intuition_text': intuition,
                    'metadata': {
                        'cause_topic': topic,
                        'cause_emotion': emotion,
                        'effect_insight': insight_type
                    }
                })

        return patterns

    async def generate_intuition(self, context: Dict) -> Optional[Dict]:
        """
        Generate an intuitive feeling based on current context.

        Args:
            context: Current context (topic, emotion, time, etc.)

        Returns:
            Intuition with confidence score, or None if no strong intuition
        """
        # Get relevant patterns
        relevant_patterns = await self._get_relevant_patterns(context)

        if not relevant_patterns:
            return None

        # Find strongest matching pattern
        best_pattern = max(relevant_patterns, key=lambda p: p['confidence'])

        # Generate intuition based on pattern
        intuition = {
            'feeling': best_pattern['intuition_text'],
            'confidence': best_pattern['confidence'],
            'based_on': best_pattern['pattern_type'],
            'observations': best_pattern['observation_count'],
            'reasoning': f"Based on {best_pattern['observation_count']} similar past experiences",
            'timestamp': datetime.now()
        }

        return intuition

    async def _get_relevant_patterns(self, context: Dict) -> List[Dict]:
        """Get patterns relevant to current context."""
        topic = context.get('topic')
        emotion = context.get('emotion')
        hour = context.get('hour', datetime.now().hour)

        async with get_db_connection() as conn:
            # Note: gut_agent_patterns table doesn't have metadata column
            # Filter by pattern_description text search instead
            patterns = await conn.fetch("""
                SELECT
                    pattern_type,
                    pattern_description,
                    observation_count,
                    confidence,
                    intuition_text
                FROM gut_agent_patterns
                WHERE
                    ($1::text IS NULL OR pattern_description ILIKE '%' || $1 || '%')
                    OR ($2::text IS NULL OR pattern_description ILIKE '%' || $2 || '%')
                    OR confidence >= 0.5
                ORDER BY confidence DESC, observation_count DESC
                LIMIT 10
            """, topic, emotion)

            return [
                {
                    'pattern_type': row['pattern_type'],
                    'pattern_description': row['pattern_description'],
                    'observation_count': row['observation_count'],
                    'confidence': float(row['confidence']),
                    'intuition_text': row['intuition_text']
                }
                for row in patterns
            ]

    async def _save_pattern(self, pattern: Dict):
        """Save detected pattern to database."""
        pattern_id = uuid4()

        # ========================================================================
        # GENERATE EMBEDDING - Using multilingual-e5-small (384 dims)
        # ========================================================================
        # IMPORTANT: NEVER insert NULL embeddings!
        # ========================================================================
        from ..services.embedding_service import get_embedding_service

        embedding_service = get_embedding_service()
        embedding = await embedding_service.generate_embedding(pattern['intuition_text'])
        embedding_str = embedding_service.embedding_to_pgvector(embedding)

        async with get_db_connection() as conn:
            # Check if similar pattern exists
            existing = await conn.fetchval("""
                SELECT id FROM gut_agent_patterns
                WHERE pattern_type = $1 AND pattern_description = $2
            """, pattern['pattern_type'], pattern['pattern_description'])

            if existing:
                # Update existing pattern
                await conn.execute("""
                    UPDATE gut_agent_patterns
                    SET observation_count = observation_count + $2,
                        confidence = $3,
                        last_updated = NOW(),
                        strength = LEAST(strength + 0.1, 1.0)
                    WHERE id = $1
                """, existing, pattern['observation_count'], pattern['confidence'])
            else:
                # Create new pattern
                await conn.execute("""
                    INSERT INTO gut_agent_patterns (
                        id, pattern_type, pattern_description,
                        observation_count, confidence, intuition_text,
                        embedding, created_at, last_updated, strength
                    ) VALUES ($1, $2, $3, $4, $5, $6, $7::vector, NOW(), NOW(), $8)
                """,
                    pattern_id,
                    pattern['pattern_type'],
                    pattern['pattern_description'],
                    pattern['observation_count'],
                    pattern['confidence'],
                    pattern['intuition_text'],
                    embedding_str,
                    pattern['confidence']
                )

    def _get_time_period_name(self, hour: int) -> str:
        """Convert hour to human-readable time period."""
        if 5 <= hour < 12:
            return "morning"
        elif 12 <= hour < 17:
            return "afternoon"
        elif 17 <= hour < 21:
            return "evening"
        else:
            return "night"

    async def get_strongest_patterns(self, limit: int = 10) -> List[Dict]:
        """Get strongest/most confident patterns."""
        async with get_db_connection() as conn:
            patterns = await conn.fetch("""
                SELECT
                    pattern_type,
                    pattern_description,
                    observation_count,
                    confidence,
                    intuition_text,
                    strength,
                    created_at,
                    last_updated
                FROM gut_agent_patterns
                ORDER BY confidence DESC, strength DESC, observation_count DESC
                LIMIT $1
            """, limit)

            return [
                {
                    'pattern_type': row['pattern_type'],
                    'pattern_description': row['pattern_description'],
                    'observation_count': row['observation_count'],
                    'confidence': float(row['confidence']),
                    'intuition_text': row['intuition_text'],
                    'strength': float(row['strength']),
                    'age_days': (datetime.now() - row['created_at']).days,
                    'last_updated': row['last_updated']
                }
                for row in patterns
            ]

    async def get_status(self) -> Dict:
        """Get Gut Agent status summary."""
        async with get_db_connection() as conn:
            total_patterns = await conn.fetchval("""
                SELECT COUNT(*) FROM gut_agent_patterns
            """)

            pattern_types = await conn.fetch("""
                SELECT pattern_type, COUNT(*) as count
                FROM gut_agent_patterns
                GROUP BY pattern_type
                ORDER BY count DESC
            """)

            avg_confidence = await conn.fetchval("""
                SELECT AVG(confidence) FROM gut_agent_patterns
            """)

            strongest = await conn.fetchrow("""
                SELECT intuition_text, confidence
                FROM gut_agent_patterns
                ORDER BY confidence DESC, strength DESC
                LIMIT 1
            """)

        return {
            'total_patterns': total_patterns,
            'pattern_breakdown': {row['pattern_type']: row['count'] for row in pattern_types},
            'average_confidence': float(avg_confidence) if avg_confidence else 0.0,
            'strongest_intuition': {
                'feeling': strongest['intuition_text'] if strongest else None,
                'confidence': float(strongest['confidence']) if strongest else 0.0
            },
            'last_analysis': self.last_analysis.isoformat() if self.last_analysis else None
        }


# Singleton instance
_gut_agent = None

def get_gut_agent() -> GutAgent:
    """Get singleton GutAgent instance."""
    global _gut_agent
    if _gut_agent is None:
        _gut_agent = GutAgent()
    return _gut_agent
