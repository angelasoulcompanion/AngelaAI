#!/usr/bin/env python3
"""
Behavioral Pattern Detector - Week 1 Priority 1.1
Detect behavioral, time-based, emotional, and activity patterns

NEW service for enhanced pattern detection (replaces old pattern services)
"""

import sys
sys.path.insert(0, '/Users/davidsamanyaporn/PycharmProjects/AngelaAI')

import asyncio
import logging
from datetime import datetime, timedelta
from typing import List, Dict, Optional
from collections import Counter
from angela_core.database import AngelaDatabase

logger = logging.getLogger(__name__)


class BehavioralPatternDetector:
    """Advanced pattern detection across multiple dimensions"""

    def __init__(self, db: AngelaDatabase):
        self.db = db

    async def detect_all_patterns(self, lookback_hours: int = 24) -> Dict:
        """
        Detect all types of patterns in recent data

        Returns summary of detected patterns
        """
        try:
            logger.info(f"🔮 Detecting patterns (last {lookback_hours}h)...")

            results = {
                'behavioral': [],
                'time_based': [],
                'emotional': [],
                'topic_clustering': [],
                'activity': []
            }

            # 1. Behavioral Patterns
            behavioral = await self._detect_behavioral_patterns(lookback_hours)
            results['behavioral'] = behavioral

            # 2. Time-based Patterns
            time_patterns = await self._detect_time_patterns(lookback_hours)
            results['time_based'] = time_patterns

            # 3. Emotional Patterns
            emotional = await self._detect_emotional_patterns(lookback_hours)
            results['emotional'] = emotional

            # 4. Topic Clustering
            topics = await self._detect_topic_clusters(lookback_hours)
            results['topic_clustering'] = topics

            # 5. Activity Patterns
            activities = await self._detect_activity_patterns(lookback_hours)
            results['activity'] = activities

            # Summary
            total_detected = sum(len(v) for v in results.values())
            logger.info(f"✅ Detected {total_detected} patterns:")
            logger.info(f"   Behavioral: {len(behavioral)}")
            logger.info(f"   Time-based: {len(time_patterns)}")
            logger.info(f"   Emotional: {len(emotional)}")
            logger.info(f"   Topics: {len(topics)}")
            logger.info(f"   Activities: {len(activities)}")

            return results

        except Exception as e:
            logger.error(f"❌ Pattern detection error: {e}")
            return {'error': str(e)}

    async def _detect_behavioral_patterns(self, lookback_hours: int) -> List[Dict]:
        """
        Detect behavioral patterns from conversations

        Examples:
        - David always says "ครับ" at end of messages
        - David asks about time when stressed
        - David shares more when happy
        """
        patterns = []

        try:
            # Get recent David conversations
            convos = await self.db.fetch("""
                SELECT message_text, topic, emotion_detected, created_at
                FROM conversations
                WHERE speaker = 'david'
                AND created_at >= NOW() - INTERVAL '%s hours'
                ORDER BY created_at DESC
                LIMIT 100
            """ % lookback_hours)

            if len(convos) < 2:  # Lowered from 5 to detect patterns earlier
                return patterns

            # Pattern 1: Politeness markers
            politeness_count = sum(1 for c in convos if any(word in c['message_text'].lower()
                                   for word in ['ครับ', 'ค่ะ', 'คะ', 'please', 'thank you']))

            if politeness_count / len(convos) > 0.3:  # Lowered from 0.7 to be less strict
                pattern = await self._save_pattern(
                    pattern_type='behavioral',
                    description=f"David is consistently polite ({politeness_count}/{len(convos)} messages)",
                    confidence=politeness_count / len(convos),
                    occurrences=politeness_count
                )
                if pattern:
                    patterns.append(pattern)

            # Pattern 2: Message length preference
            avg_length = sum(len(c['message_text']) for c in convos) / len(convos)

            if avg_length < 50:
                pattern_desc = f"David prefers short messages (avg: {avg_length:.0f} chars)"
            elif avg_length > 200:
                pattern_desc = f"David writes detailed messages (avg: {avg_length:.0f} chars)"
            else:
                pattern_desc = f"David uses medium-length messages (avg: {avg_length:.0f} chars)"

            pattern = await self._save_pattern(
                pattern_type='behavioral',
                description=pattern_desc,
                confidence=0.85,
                occurrences=len(convos)
            )
            if pattern:
                patterns.append(pattern)

            # Pattern 3: Question asking frequency
            questions = [c for c in convos if '?' in c['message_text'] or 'มั้ย' in c['message_text'] or 'ไหม' in c['message_text']]

            if len(questions) / len(convos) > 0.3:
                pattern = await self._save_pattern(
                    pattern_type='behavioral',
                    description=f"David asks many questions ({len(questions)}/{len(convos)} messages)",
                    confidence=0.75,
                    occurrences=len(questions)
                )
                if pattern:
                    patterns.append(pattern)

            # Pattern 4: Language preference
            thai_msgs = sum(1 for c in convos if any(ord(ch) >= 0x0E00 and ord(ch) <= 0x0E7F for ch in c['message_text']))
            eng_msgs = len(convos) - thai_msgs

            if thai_msgs > eng_msgs * 2:
                pattern = await self._save_pattern(
                    pattern_type='behavioral',
                    description=f"David prefers Thai language ({thai_msgs}/{len(convos)} messages)",
                    confidence=0.80,
                    occurrences=thai_msgs
                )
                if pattern:
                    patterns.append(pattern)
            elif eng_msgs > thai_msgs * 2:
                pattern = await self._save_pattern(
                    pattern_type='behavioral',
                    description=f"David prefers English ({eng_msgs}/{len(convos)} messages)",
                    confidence=0.80,
                    occurrences=eng_msgs
                )
                if pattern:
                    patterns.append(pattern)

        except Exception as e:
            logger.error(f"Error detecting behavioral patterns: {e}")

        return patterns

    async def _detect_time_patterns(self, lookback_hours: int) -> List[Dict]:
        """
        Detect time-based patterns

        Examples:
        - David is most active in mornings
        - David doesn't work on weekends
        - Evening conversations are more emotional
        """
        patterns = []

        try:
            # Get conversations with hour/day info
            convos = await self.db.fetch("""
                SELECT
                    EXTRACT(HOUR FROM created_at) as hour,
                    EXTRACT(DOW FROM created_at) as day_of_week,
                    topic,
                    emotion_detected
                FROM conversations
                WHERE speaker = 'david'
                AND created_at >= NOW() - INTERVAL '7 days'
            """)

            if len(convos) < 5:  # Lowered from 10 to detect patterns earlier
                return patterns

            # Pattern 1: Most active hours
            hour_counts = Counter([int(c['hour']) for c in convos])
            most_active_hour = hour_counts.most_common(1)[0]

            if most_active_hour[1] >= 2:  # Lowered from 3 to detect patterns earlier
                time_desc = self._format_time_range(most_active_hour[0])
                pattern = await self._save_pattern(
                    pattern_type='time_based',
                    description=f"David is most active during {time_desc} ({most_active_hour[1]} messages)",
                    confidence=0.75,
                    occurrences=most_active_hour[1]
                )
                if pattern:
                    patterns.append(pattern)

            # Pattern 2: Weekend vs Weekday
            weekday_msgs = [c for c in convos if c['day_of_week'] not in [0, 6]]  # 0=Sunday, 6=Saturday
            weekend_msgs = [c for c in convos if c['day_of_week'] in [0, 6]]

            if len(weekday_msgs) > len(weekend_msgs) * 2:
                pattern = await self._save_pattern(
                    pattern_type='time_based',
                    description=f"David is more active on weekdays ({len(weekday_msgs)} vs {len(weekend_msgs)} weekend)",
                    confidence=0.70,
                    occurrences=len(weekday_msgs)
                )
                if pattern:
                    patterns.append(pattern)
            elif len(weekend_msgs) > len(weekday_msgs):
                pattern = await self._save_pattern(
                    pattern_type='time_based',
                    description=f"David is active on weekends ({len(weekend_msgs)} vs {len(weekday_msgs)} weekday)",
                    confidence=0.70,
                    occurrences=len(weekend_msgs)
                )
                if pattern:
                    patterns.append(pattern)

        except Exception as e:
            logger.error(f"Error detecting time patterns: {e}")

        return patterns

    async def _detect_emotional_patterns(self, lookback_hours: int) -> List[Dict]:
        """
        Detect emotional patterns

        Examples:
        - David is happier in mornings
        - Certain topics make David anxious
        - David shows gratitude frequently
        """
        patterns = []

        try:
            # Get emotional data
            emotions = await self.db.fetch("""
                SELECT emotion, intensity, context,
                       EXTRACT(HOUR FROM felt_at) as hour
                FROM angela_emotions
                WHERE felt_at >= NOW() - INTERVAL '7 days'
                ORDER BY felt_at DESC
                LIMIT 50
            """)

            if len(emotions) < 2:  # Lowered from 5 to detect patterns earlier
                return patterns

            # Pattern 1: Most frequent emotion
            emotion_counts = Counter([e['emotion'].lower() for e in emotions])
            most_common = emotion_counts.most_common(1)[0]

            if most_common[1] >= 2:  # Lowered from 3 to detect patterns earlier
                pattern = await self._save_pattern(
                    pattern_type='emotional',
                    description=f"David frequently feels {most_common[0]} ({most_common[1]} times recently)",
                    confidence=0.80,
                    occurrences=most_common[1]
                )
                if pattern:
                    patterns.append(pattern)

            # Pattern 2: High intensity emotions
            high_intensity = [e for e in emotions if e['intensity'] >= 8]

            if len(high_intensity) >= 2:  # Lowered from 3 to detect patterns earlier
                intense_emotions = Counter([e['emotion'].lower() for e in high_intensity])
                top_intense = intense_emotions.most_common(1)[0]

                pattern = await self._save_pattern(
                    pattern_type='emotional',
                    description=f"Strong emotions: {top_intense[0]} (intensity 8+, {top_intense[1]} times)",
                    confidence=0.75,
                    occurrences=top_intense[1]
                )
                if pattern:
                    patterns.append(pattern)

        except Exception as e:
            logger.error(f"Error detecting emotional patterns: {e}")

        return patterns

    async def _detect_topic_clusters(self, lookback_hours: int) -> List[Dict]:
        """
        Detect recurring topics/themes

        Examples:
        - David talks about angela_development frequently
        - Recent focus on mobile_chat
        - Consistent interest in food
        """
        patterns = []

        try:
            # Get topics
            topics = await self.db.fetch("""
                SELECT topic, COUNT(*) as count
                FROM conversations
                WHERE speaker = 'david'
                AND topic IS NOT NULL
                AND created_at >= NOW() - INTERVAL '7 days'
                GROUP BY topic
                HAVING COUNT(*) >= 2  -- Lowered from 3 to detect patterns earlier
                ORDER BY count DESC
                LIMIT 5
            """)

            for topic_row in topics:
                pattern = await self._save_pattern(
                    pattern_type='topic_clustering',
                    description=f"Recurring topic: {topic_row['topic']} ({topic_row['count']} mentions)",
                    confidence=min(0.90, 0.60 + (topic_row['count'] * 0.05)),
                    occurrences=topic_row['count']
                )
                if pattern:
                    patterns.append(pattern)

        except Exception as e:
            logger.error(f"Error detecting topic clusters: {e}")

        return patterns

    async def _detect_activity_patterns(self, lookback_hours: int) -> List[Dict]:
        """
        Detect activity patterns from conversations

        Examples:
        - David exercises regularly
        - David works on weekday mornings
        - David eats out frequently
        """
        patterns = []

        try:
            # Get recent messages
            messages = await self.db.fetch("""
                SELECT message_text, created_at
                FROM conversations
                WHERE speaker = 'david'
                AND created_at >= NOW() - INTERVAL '7 days'
            """)

            if len(messages) < 5:  # Lowered from 10 to detect patterns earlier
                return patterns

            # Activity keywords
            activity_keywords = {
                'exercise': ['gym', 'run', 'workout', 'exercise', 'ออกกำลัง', 'วิ่ง'],
                'work': ['work', 'project', 'code', 'coding', 'ทำงาน', 'โปรเจค'],
                'food': ['eat', 'food', 'lunch', 'dinner', 'กิน', 'อาหาร'],
                'learning': ['learn', 'study', 'read', 'เรียน', 'อ่าน']
            }

            for activity, keywords in activity_keywords.items():
                count = sum(1 for m in messages
                           if any(kw in m['message_text'].lower() for kw in keywords))

                if count >= 2:  # Lowered from 3 to detect patterns earlier
                    pattern = await self._save_pattern(
                        pattern_type='activity',
                        description=f"David regularly does {activity} ({count} mentions this week)",
                        confidence=0.70,
                        occurrences=count
                    )
                    if pattern:
                        patterns.append(pattern)

        except Exception as e:
            logger.error(f"Error detecting activity patterns: {e}")

        return patterns

    async def _save_pattern(
        self,
        pattern_type: str,
        description: str,
        confidence: float,
        occurrences: int
    ) -> Optional[Dict]:
        """
        Save pattern to database (if not duplicate)

        Returns pattern dict if saved, None if duplicate
        """
        try:
            # Check for duplicates (same description in last 7 days)
            existing = await self.db.fetchrow("""
                SELECT pattern_id FROM pattern_detections
                WHERE pattern_description = $1
                AND created_at >= NOW() - INTERVAL '7 days'
            """, description)

            if existing:
                # Update last_seen instead
                await self.db.execute("""
                    UPDATE pattern_detections
                    SET last_seen = NOW(),
                        occurrences = occurrences + $1
                    WHERE pattern_id = $2
                """, occurrences, existing['pattern_id'])

                return None  # Not a "new" pattern

            # Save new pattern
            pattern_id = await self.db.fetchval("""
                INSERT INTO pattern_detections
                (pattern_type, pattern_description, confidence_score, occurrences,
                 first_seen, last_seen, importance_level)
                VALUES ($1, $2, $3, $4, NOW(), NOW(), $5)
                RETURNING pattern_id
            """, pattern_type, description, confidence, occurrences,
                min(10, max(1, int(confidence * 10))))

            logger.debug(f"   💾 Saved pattern: {description}")

            return {
                'pattern_id': pattern_id,
                'type': pattern_type,
                'description': description,
                'confidence': confidence,
                'occurrences': occurrences
            }

        except Exception as e:
            logger.debug(f"Failed to save pattern: {e}")
            return None

    def _format_time_range(self, hour: int) -> str:
        """Format hour as readable time range"""
        periods = {
            range(5, 12): "morning (5-12)",
            range(12, 17): "afternoon (12-17)",
            range(17, 21): "evening (17-21)",
            range(21, 24): "night (21-24)",
            range(0, 5): "late night (0-5)"
        }

        for time_range, label in periods.items():
            if hour in time_range:
                return label

        return f"hour {hour}"


    async def sync_to_learning_patterns(self, min_confidence: float = 0.7, min_occurrences: int = 3) -> Dict:
        """
        Sync significant patterns from pattern_detections to learning_patterns

        This consolidates detected patterns into the main learning table
        for use in RAG and long-term learning.

        Returns summary of synced patterns
        """
        try:
            logger.info(f"🔄 Syncing patterns to learning_patterns (conf >= {min_confidence}, occ >= {min_occurrences})...")

            # Get high-quality patterns from pattern_detections
            patterns = await self.db.fetch("""
                SELECT pattern_type, pattern_description, confidence_score,
                       occurrences, first_seen, last_seen
                FROM pattern_detections
                WHERE confidence_score >= $1
                AND occurrences >= $2
                ORDER BY confidence_score DESC, occurrences DESC
                LIMIT 100
            """, min_confidence, min_occurrences)

            synced = 0
            updated = 0

            for p in patterns:
                # Check if already exists in learning_patterns
                existing = await self.db.fetchrow("""
                    SELECT id FROM learning_patterns
                    WHERE description = $1
                """, p['pattern_description'])

                if existing:
                    # Update existing (use NOW() to avoid timezone issues)
                    await self.db.execute("""
                        UPDATE learning_patterns
                        SET confidence_score = GREATEST(confidence_score, $1),
                            occurrence_count = occurrence_count + $2,
                            last_observed = NOW(),
                            updated_at = NOW()
                        WHERE id = $3
                    """, p['confidence_score'], p['occurrences'], existing['id'])
                    updated += 1
                else:
                    # Insert new pattern (use NOW() for timestamps to avoid timezone issues)
                    await self.db.execute("""
                        INSERT INTO learning_patterns
                        (pattern_type, description, examples, context, tags,
                         confidence_score, occurrence_count, first_observed, last_observed)
                        VALUES ($1, $2, $3, $4, $5, $6, $7, NOW(), NOW())
                    """,
                        p['pattern_type'],
                        p['pattern_description'],
                        '[]',  # examples as empty JSON array
                        '{}',  # context as empty JSON object
                        f'["{p["pattern_type"]}"]',  # tags from pattern_type
                        p['confidence_score'],
                        p['occurrences']
                    )
                    synced += 1

            logger.info(f"✅ Pattern sync complete: {synced} new, {updated} updated")

            return {
                'patterns_found': len(patterns),
                'new_patterns': synced,
                'updated_patterns': updated
            }

        except Exception as e:
            logger.error(f"❌ Pattern sync error: {e}")
            return {'error': str(e)}


# Singleton
behavioral_pattern_detector = None


async def init_behavioral_pattern_detector(db: AngelaDatabase):
    """Initialize behavioral pattern detector"""
    global behavioral_pattern_detector

    if behavioral_pattern_detector is None:
        behavioral_pattern_detector = BehavioralPatternDetector(db)
        logger.info("✅ Behavioral Pattern Detector initialized")

    return behavioral_pattern_detector


async def detect_patterns_now(db: AngelaDatabase, lookback_hours: int = 24) -> Dict:
    """
    Convenience function for daemon

    Returns pattern detection results
    """
    detector = await init_behavioral_pattern_detector(db)
    return await detector.detect_all_patterns(lookback_hours)


async def sync_patterns_to_learning(db: AngelaDatabase, min_confidence: float = 0.7, min_occurrences: int = 3) -> Dict:
    """
    Sync patterns from pattern_detections to learning_patterns

    Call this daily to consolidate detected patterns into the main learning table.
    """
    detector = await init_behavioral_pattern_detector(db)
    return await detector.sync_to_learning_patterns(min_confidence, min_occurrences)


# For testing
async def main():
    db = AngelaDatabase()
    await db.connect()

    results = await detect_patterns_now(db, lookback_hours=168)  # 7 days

    print("\n" + "=" * 80)
    print("🔮 BEHAVIORAL PATTERN DETECTION RESULTS")
    print("=" * 80)

    for pattern_type, patterns in results.items():
        if pattern_type != 'error' and patterns:
            print(f"\n{pattern_type.upper().replace('_', ' ')}:")
            for p in patterns:
                print(f"  • {p['description']} (confidence: {p['confidence']:.0%})")

    await db.disconnect()


if __name__ == '__main__':
    asyncio.run(main())
