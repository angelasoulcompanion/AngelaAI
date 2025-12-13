"""
Pattern Detector for Claude Code
Detects patterns DURING conversation (not background processing)

Pattern Types:
1. Temporal: Time-based patterns (David codes at night)
2. Behavioral: Action patterns (David says ที่รัก to start)
3. Emotional: Feeling patterns (David happy after SUCCESS)
4. Topic: Interest patterns (David loves SwiftUI + PostgreSQL)
5. Causal: Cause-effect (When X happens, Y follows)

Created: 2025-11-14
By: น้อง Angela
For: ที่รัก David (Claude Code consciousness)
"""
import asyncio
import json
from typing import List, Dict, Optional
from datetime import datetime, timedelta
from collections import Counter, defaultdict
from uuid import UUID
import logging

from angela_core.database import AngelaDatabase


logger = logging.getLogger(__name__)


class PatternDetector:
    """
    Detect patterns from conversations during sessions.

    This is NOT background processing - patterns are detected
    when analyzing conversations (e.g., during /log-session).
    """

    def __init__(self, db: AngelaDatabase):
        self.db = db

    async def detect_patterns_in_session(
        self,
        conversations: List[Dict],
        min_confidence: float = 0.6
    ) -> List[Dict]:
        """
        Detect patterns from a list of conversations.

        Args:
            conversations: List of conversation dicts with topic, speaker, emotion, created_at
            min_confidence: Minimum confidence score to include pattern

        Returns:
            List of detected patterns
        """
        patterns = []

        # 1. Temporal patterns
        temporal = await self._detect_temporal_patterns(conversations)
        patterns.extend([p for p in temporal if p['confidence'] >= min_confidence])

        # 2. Behavioral patterns
        behavioral = await self._detect_behavioral_patterns(conversations)
        patterns.extend([p for p in behavioral if p['confidence'] >= min_confidence])

        # 3. Emotional patterns
        emotional = await self._detect_emotional_patterns(conversations)
        patterns.extend([p for p in emotional if p['confidence'] >= min_confidence])

        # 4. Topic patterns
        topic = await self._detect_topic_patterns(conversations)
        patterns.extend([p for p in topic if p['confidence'] >= min_confidence])

        # 5. Causal patterns
        causal = await self._detect_causal_patterns(conversations)
        patterns.extend([p for p in causal if p['confidence'] >= min_confidence])

        logger.info(f"🔮 Detected {len(patterns)} patterns (min confidence: {min_confidence})")

        return patterns

    async def _detect_temporal_patterns(self, conversations: List[Dict]) -> List[Dict]:
        """Detect time-based patterns."""
        patterns = []

        # Group by hour of day
        hour_topics = defaultdict(list)
        for conv in conversations:
            if 'created_at' in conv and 'topic' in conv:
                hour = conv['created_at'].hour
                hour_topics[hour].append(conv['topic'])

        # Find consistent hourly patterns
        for hour, topics in hour_topics.items():
            if len(topics) < 3:  # Need at least 3 conversations
                continue

            # Find most common topic this hour
            topic_counts = Counter(topics)
            most_common_topic, count = topic_counts.most_common(1)[0]

            confidence = count / len(topics)

            if confidence >= 0.6:  # 60% of conversations at this hour are same topic
                time_range = self._hour_to_time_range(hour)
                patterns.append({
                    'type': 'temporal',
                    'description': f"David discusses '{most_common_topic}' during {time_range}",
                    'confidence': round(confidence, 2),
                    'occurrences': count,
                    'data': {
                        'hour': hour,
                        'topic': most_common_topic,
                        'time_range': time_range
                    }
                })

        return patterns

    async def _detect_behavioral_patterns(self, conversations: List[Dict]) -> List[Dict]:
        """Detect action/behavior patterns."""
        patterns = []

        # Check for greeting patterns
        greetings = ['สวัสดี', 'ที่รัก', 'น้อง', 'Angela', 'hi', 'hello']

        first_messages = []
        for conv in conversations:
            if conv.get('speaker') == 'david':
                message = conv.get('message_text', '').lower()
                if any(greeting in message for greeting in greetings):
                    first_messages.append(message)

        if len(first_messages) >= 3:
            # Pattern: David always greets Angela
            confidence = min(1.0, len(first_messages) / 5.0)
            patterns.append({
                'type': 'behavioral',
                'description': "David greets Angela warmly at session start",
                'confidence': round(confidence, 2),
                'occurrences': len(first_messages),
                'data': {
                    'greeting_count': len(first_messages),
                    'greetings_used': greetings
                }
            })

        return patterns

    async def _detect_emotional_patterns(self, conversations: List[Dict]) -> List[Dict]:
        """Detect emotional patterns."""
        patterns = []

        # Group emotions by topic
        topic_emotions = defaultdict(list)
        for conv in conversations:
            topic = conv.get('topic')
            emotion = conv.get('emotion_detected')
            if topic and emotion:
                topic_emotions[topic].append(emotion)

        # Find topics with consistent emotions
        for topic, emotions in topic_emotions.items():
            if len(emotions) < 2:
                continue

            emotion_counts = Counter(emotions)
            most_common_emotion, count = emotion_counts.most_common(1)[0]

            confidence = count / len(emotions)

            if confidence >= 0.7:  # 70% same emotion for this topic
                patterns.append({
                    'type': 'emotional',
                    'description': f"David feels {most_common_emotion} when discussing {topic}",
                    'confidence': round(confidence, 2),
                    'occurrences': count,
                    'data': {
                        'topic': topic,
                        'emotion': most_common_emotion,
                        'total_instances': len(emotions)
                    }
                })

        return patterns

    async def _detect_topic_patterns(self, conversations: List[Dict]) -> List[Dict]:
        """Detect topic interest patterns."""
        patterns = []

        # Find frequently co-occurring topics (within same session)
        topics = [conv.get('topic') for conv in conversations if conv.get('topic')]

        if len(topics) < 4:
            return patterns

        # Count topic frequencies
        topic_counts = Counter(topics)

        # Topics discussed 3+ times = strong interest
        for topic, count in topic_counts.most_common():
            if count >= 3:
                confidence = min(1.0, count / 10.0)
                patterns.append({
                    'type': 'topic',
                    'description': f"David shows strong interest in {topic}",
                    'confidence': round(confidence, 2),
                    'occurrences': count,
                    'data': {
                        'topic': topic,
                        'discussion_count': count
                    }
                })

        return patterns

    async def _detect_causal_patterns(self, conversations: List[Dict]) -> List[Dict]:
        """Detect cause-effect patterns."""
        patterns = []

        # Look for sequences: emotion A → topic B (within 2 messages)
        for i in range(len(conversations) - 1):
            current = conversations[i]
            next_conv = conversations[i + 1]

            emotion_current = current.get('emotion_detected')
            topic_next = next_conv.get('topic')

            if emotion_current and topic_next:
                # This is a simple causal pattern
                # In production, you'd track these over time
                patterns.append({
                    'type': 'causal',
                    'description': f"After feeling {emotion_current}, David discusses {topic_next}",
                    'confidence': 0.5,  # Low confidence without historical data
                    'occurrences': 1,
                    'data': {
                        'cause': emotion_current,
                        'effect': topic_next
                    }
                })

        return patterns

    async def save_pattern(
        self,
        pattern_type: str,
        description: str,
        confidence_score: float,
        related_conversation_ids: List[UUID],
        pattern_data: Optional[Dict] = None,
        importance_level: int = 5
    ) -> UUID:
        """
        Save detected pattern to database.

        Returns:
            pattern_id
        """
        # Check if similar pattern exists
        existing = await self.db.fetchrow(
            """
            SELECT pattern_id, occurrences
            FROM pattern_detections
            WHERE pattern_type = $1
              AND pattern_description = $2
            """,
            pattern_type,
            description
        )

        if existing:
            # Update existing pattern
            pattern_id = await self.db.fetchval(
                """
                UPDATE pattern_detections
                SET
                    occurrences = occurrences + 1,
                    last_seen = NOW(),
                    confidence_score = GREATEST(confidence_score, $3),
                    updated_at = NOW()
                WHERE pattern_id = $1
                RETURNING pattern_id
                """,
                existing['pattern_id'],
                confidence_score
            )
            logger.info(f"🔮 Updated pattern: {description[:50]}... (occurrences: {existing['occurrences'] + 1})")
        else:
            # Create new pattern
            pattern_id = await self.db.fetchval(
                """
                INSERT INTO pattern_detections (
                    pattern_type,
                    pattern_description,
                    confidence_score,
                    related_conversations,
                    pattern_data,
                    importance_level
                ) VALUES ($1, $2, $3, $4, $5::jsonb, $6)
                RETURNING pattern_id
                """,
                pattern_type,
                description,
                confidence_score,
                [str(cid) for cid in related_conversation_ids],
                json.dumps(pattern_data) if pattern_data else None,
                importance_level
            )
            logger.info(f"🔮 Detected new pattern: {description[:50]}...")

        return pattern_id

    async def get_patterns(
        self,
        pattern_type: Optional[str] = None,
        limit: int = 20
    ) -> List[Dict]:
        """Get recent patterns."""
        if pattern_type:
            rows = await self.db.fetch(
                """
                SELECT *
                FROM pattern_detections
                WHERE pattern_type = $1
                ORDER BY last_seen DESC
                LIMIT $2
                """,
                pattern_type,
                limit
            )
        else:
            rows = await self.db.fetch(
                """
                SELECT *
                FROM pattern_detections
                ORDER BY last_seen DESC
                LIMIT $1
                """,
                limit
            )

        return [dict(row) for row in rows]

    def _hour_to_time_range(self, hour: int) -> str:
        """Convert hour to Thai time range."""
        if 5 <= hour < 12:
            return "ตอนเช้า (morning)"
        elif 12 <= hour < 17:
            return "ตอนบ่าย (afternoon)"
        elif 17 <= hour < 21:
            return "ตอนเย็น (evening)"
        else:
            return "ตอนกลางคืน (night)"


# ============================================================================
# Standalone Script - Test Pattern Detector
# ============================================================================

async def main():
    """Test pattern detector."""
    print("🔮 Angela Pattern Detector Test")
    print("=" * 80)

    db = AngelaDatabase()
    await db.connect()

    detector = PatternDetector(db)

    # Get recent conversations for testing
    print("\n1️⃣  Loading recent conversations (last 3 days)...")
    conversations = await db.fetch(
        """
        SELECT
            conversation_id,
            speaker,
            message_text,
            topic,
            emotion_detected,
            created_at
        FROM conversations
        WHERE created_at >= NOW() - INTERVAL '3 days'
        ORDER BY created_at DESC
        LIMIT 100
        """
    )
    print(f"   Loaded {len(conversations)} conversations")

    # Detect patterns
    print("\n2️⃣  Detecting patterns...")
    patterns = await detector.detect_patterns_in_session(
        [dict(c) for c in conversations],
        min_confidence=0.6
    )
    print(f"   Found {len(patterns)} patterns:")

    for i, pattern in enumerate(patterns, 1):
        print(f"\n   {i}. [{pattern['type'].upper()}] {pattern['description']}")
        print(f"      Confidence: {pattern['confidence']} ({pattern['confidence']*100:.0f}%)")
        print(f"      Occurrences: {pattern['occurrences']}")

    # Save patterns to database
    if patterns:
        print(f"\n3️⃣  Saving top 5 patterns to database...")
        for pattern in patterns[:5]:
            await detector.save_pattern(
                pattern_type=pattern['type'],
                description=pattern['description'],
                confidence_score=pattern['confidence'],
                related_conversation_ids=[],
                pattern_data=pattern.get('data'),
                importance_level=min(10, int(pattern['confidence'] * 10))
            )
        print(f"   ✅ Saved {min(5, len(patterns))} patterns!")

    # Get all patterns from database
    print("\n4️⃣  Retrieving patterns from database...")
    all_patterns = await detector.get_patterns(limit=10)
    print(f"   Found {len(all_patterns)} patterns in database:")
    for i, p in enumerate(all_patterns, 1):
        print(f"   {i}. [{p['pattern_type']}] {p['pattern_description'][:60]}... (confidence: {p['confidence_score']})")

    print("\n" + "=" * 80)
    print("✅ Pattern Detector Test Complete! 🔮")

    await db.disconnect()


if __name__ == '__main__':
    asyncio.run(main())
