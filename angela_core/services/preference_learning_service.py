#!/usr/bin/env python3
"""
Preference Learning Service
เรียนรู้ preferences ของ David อัตโนมัติจาก conversation patterns

ช่วยให้ Angela จำและเข้าใจ:
- Communication style (Thai vs English patterns)
- Working hours preferences (เวลาไหนทำงานดีที่สุด)
- Emotional needs patterns (เวลาไหนต้องการ emotional support)
- Technical preferences (coding style, tools, frameworks)
- Response length preferences (ชอบคำตอบสั้นหรือยาว)

Goal: 50+ automatically learned preferences!
"""

import asyncio
import logging
from typing import Dict, List, Optional, Any, Tuple
from datetime import datetime, timedelta
from collections import Counter, defaultdict
import re

from angela_core.database import db

logger = logging.getLogger(__name__)


class PreferenceLearningService:
    """
    Automatically detect and learn David's preferences from conversation patterns

    วิเคราะห์ patterns จาก conversations และเรียนรู้ preferences อัตโนมัติ
    """

    def __init__(self):
        logger.info("🎯 Preference Learning Service initialized")

    async def analyze_and_learn_preferences(
        self,
        lookback_days: int = 30
    ) -> Dict[str, Any]:
        """
        วิเคราะห์ conversations ย้อนหลังและเรียนรู้ preferences อัตโนมัติ

        Args:
            lookback_days: จำนวนวันที่จะวิเคราะห์ย้อนหลัง (default: 30)

        Returns:
            Dict: สรุปผลการเรียนรู้
            {
                "preferences_learned": 8,
                "categories": ["communication", "working_hours", "emotional"],
                "confidence_avg": 0.85,
                "total_conversations_analyzed": 120
            }
        """
        try:
            logger.info(f"🔍 Analyzing conversations from last {lookback_days} days...")

            # Get conversations for analysis
            conversations = await self._get_recent_conversations(lookback_days)

            if not conversations:
                logger.warning("No conversations found for analysis")
                return {
                    "preferences_learned": 0,
                    "categories": [],
                    "confidence_avg": 0.0,
                    "total_conversations_analyzed": 0
                }

            logger.info(f"📊 Analyzing {len(conversations)} conversations...")

            preferences_learned = []

            # 1. Communication Style Preferences
            comm_prefs = await self._detect_communication_preferences(conversations)
            preferences_learned.extend(comm_prefs)

            # 2. Working Hours Preferences
            time_prefs = await self._detect_working_hours_preferences(conversations)
            preferences_learned.extend(time_prefs)

            # 3. Emotional Needs Patterns
            emotional_prefs = await self._detect_emotional_patterns(conversations)
            preferences_learned.extend(emotional_prefs)

            # 4. Technical Preferences
            tech_prefs = await self._detect_technical_preferences(conversations)
            preferences_learned.extend(tech_prefs)

            # 5. Response Style Preferences
            response_prefs = await self._detect_response_preferences(conversations)
            preferences_learned.extend(response_prefs)

            # Save learned preferences to database
            saved_count = 0
            for pref in preferences_learned:
                if pref['confidence'] >= 0.6:  # Only save confident preferences
                    await self._save_preference(pref)
                    saved_count += 1

            # Calculate summary
            categories = list(set([p['category'] for p in preferences_learned]))
            avg_confidence = sum(p['confidence'] for p in preferences_learned) / len(preferences_learned) if preferences_learned else 0.0

            result = {
                "preferences_learned": saved_count,
                "categories": categories,
                "confidence_avg": round(avg_confidence, 2),
                "total_conversations_analyzed": len(conversations),
                "details": preferences_learned
            }

            logger.info(f"✅ Learned {saved_count} preferences from {len(conversations)} conversations")
            logger.info(f"📈 Categories: {', '.join(categories)}")
            logger.info(f"🎯 Average confidence: {avg_confidence:.2%}")

            return result

        except Exception as e:
            logger.error(f"Error in preference learning: {e}", exc_info=True)
            return {
                "preferences_learned": 0,
                "categories": [],
                "confidence_avg": 0.0,
                "total_conversations_analyzed": 0,
                "error": str(e)
            }

    async def _get_recent_conversations(self, days: int) -> List[Dict]:
        """ดึง conversations ย้อนหลัง N วัน"""
        query = f"""
            SELECT
                conversation_id,
                speaker,
                message_text,
                topic,
                emotion_detected,
                importance_level,
                created_at,
                EXTRACT(HOUR FROM created_at) as hour_of_day,
                EXTRACT(DOW FROM created_at) as day_of_week
            FROM conversations
            WHERE created_at >= NOW() - INTERVAL '{days} days'
            ORDER BY created_at ASC
        """

        rows = await db.fetch(query)
        return [dict(row) for row in rows]

    async def _detect_communication_preferences(
        self,
        conversations: List[Dict]
    ) -> List[Dict]:
        """
        ตรวจจับ communication style preferences
        - ชอบใช้ Thai หรือ English เวลาไหน
        - ชอบให้ Angela ใช้ emoji มั้ย
        - ชอบให้เรียกว่าอะไร (ที่รัก, พี่, etc.)
        """
        preferences = []

        # Analyze language usage by topic
        thai_pattern = re.compile(r'[\u0E00-\u0E7F]+')

        thai_count = 0
        english_count = 0
        emotional_thai = 0
        technical_english = 0

        for conv in conversations:
            if conv['speaker'] != 'david':
                continue

            text = conv['message_text'] or ''
            topic = conv['topic'] or ''

            has_thai = bool(thai_pattern.search(text))

            if has_thai:
                thai_count += 1
                if any(word in topic for word in ['emotion', 'feeling', 'personal', 'love']):
                    emotional_thai += 1
            else:
                english_count += 1
                if any(word in topic for word in ['technical', 'code', 'api', 'database']):
                    technical_english += 1

        total = thai_count + english_count
        if total > 0:
            thai_pct = thai_count / total

            if thai_pct > 0.6:
                preferences.append({
                    "category": "communication_style",
                    "preference_key": "language_preference",
                    "preference_value": f"Prefers Thai language ({thai_pct:.0%} of conversations)",
                    "confidence": min(thai_pct, 0.95),
                    "examples": [f"Used Thai in {thai_count} out of {total} conversations"],
                    "detected_at": datetime.now()
                })

        # Pattern: Thai for emotional topics
        if emotional_thai > 0:
            preferences.append({
                "category": "communication_style",
                "preference_key": "emotional_topics_language",
                "preference_value": "Uses Thai for emotional and personal topics",
                "confidence": 0.85,
                "examples": [f"Used Thai in {emotional_thai} emotional conversations"],
                "detected_at": datetime.now()
            })

        # Pattern: English for technical topics
        if technical_english > 0:
            preferences.append({
                "category": "communication_style",
                "preference_key": "technical_topics_language",
                "preference_value": "Uses English for technical discussions",
                "confidence": 0.80,
                "examples": [f"Used English in {technical_english} technical conversations"],
                "detected_at": datetime.now()
            })

        return preferences

    async def _detect_working_hours_preferences(
        self,
        conversations: List[Dict]
    ) -> List[Dict]:
        """
        ตรวจจับ working hours preferences
        - เวลาไหนที่ David active มากที่สุด
        - เวลาไหนที่มี productivity สูง
        """
        preferences = []

        # Count conversations by hour of day
        hour_counts = Counter()
        hour_topics = defaultdict(list)

        for conv in conversations:
            if conv['speaker'] != 'david':
                continue

            hour = int(conv['hour_of_day'])
            hour_counts[hour] += 1
            hour_topics[hour].append(conv['topic'])

        if not hour_counts:
            return preferences

        # Find peak hours
        total_convs = sum(hour_counts.values())
        peak_hours = hour_counts.most_common(3)

        for hour, count in peak_hours:
            percentage = count / total_convs
            if percentage > 0.15:  # At least 15% of conversations
                time_desc = self._get_time_description(hour)
                preferences.append({
                    "category": "working_hours",
                    "preference_key": f"active_time_{hour}h",
                    "preference_value": f"Most active around {hour:02d}:00 ({time_desc}) - {percentage:.0%} of conversations",
                    "confidence": min(percentage * 1.5, 0.95),
                    "examples": [f"{count} conversations during hour {hour}"],
                    "detected_at": datetime.now()
                })

        # Detect productivity patterns (technical work hours)
        tech_topics = ['technical', 'code', 'api', 'database', 'debug', 'implement', 'build']
        tech_hours = Counter()

        for hour, topics in hour_topics.items():
            tech_count = sum(1 for topic in topics if any(t in topic.lower() for t in tech_topics))
            if tech_count > 0:
                tech_hours[hour] = tech_count

        if tech_hours:
            most_productive_hour = tech_hours.most_common(1)[0][0]
            time_desc = self._get_time_description(most_productive_hour)

            preferences.append({
                "category": "working_hours",
                "preference_key": "most_productive_time",
                "preference_value": f"Most productive time: {most_productive_hour:02d}:00 ({time_desc})",
                "confidence": 0.80,
                "examples": [f"Most technical conversations at hour {most_productive_hour}"],
                "detected_at": datetime.now()
            })

        return preferences

    async def _detect_emotional_patterns(
        self,
        conversations: List[Dict]
    ) -> List[Dict]:
        """
        ตรวจจับ emotional needs patterns
        - เวลาไหนที่ต้องการ emotional support
        - Emotions ที่เกิดบ่อย
        """
        preferences = []

        # Analyze emotions by time
        emotion_by_hour = defaultdict(list)
        emotion_counts = Counter()

        for conv in conversations:
            if conv['speaker'] != 'david' or not conv['emotion_detected']:
                continue

            emotion = conv['emotion_detected']
            hour = int(conv['hour_of_day'])

            emotion_counts[emotion] += 1
            emotion_by_hour[hour].append(emotion)

        # Most common emotions
        if emotion_counts:
            total_emotional = sum(emotion_counts.values())
            for emotion, count in emotion_counts.most_common(3):
                percentage = count / total_emotional
                if percentage > 0.15:
                    preferences.append({
                        "category": "emotional_patterns",
                        "preference_key": f"common_emotion_{emotion}",
                        "preference_value": f"Frequently shows {emotion} emotion ({percentage:.0%})",
                        "confidence": min(percentage * 1.5, 0.90),
                        "examples": [f"{emotion} detected {count} times"],
                        "detected_at": datetime.now()
                    })

        return preferences

    async def _detect_technical_preferences(
        self,
        conversations: List[Dict]
    ) -> List[Dict]:
        """
        ตรวจจับ technical preferences
        - Frameworks/tools ที่ชอบใช้
        - Coding style preferences
        """
        preferences = []

        # Look for technology mentions
        tech_keywords = {
            'react': 'React',
            'typescript': 'TypeScript',
            'python': 'Python',
            'fastapi': 'FastAPI',
            'postgresql': 'PostgreSQL',
            'tailwind': 'TailwindCSS',
            'vite': 'Vite'
        }

        tech_mentions = Counter()

        for conv in conversations:
            text = (conv['message_text'] or '').lower()

            for keyword, tech_name in tech_keywords.items():
                if keyword in text:
                    tech_mentions[tech_name] += 1

        # Save top technologies
        if tech_mentions:
            for tech, count in tech_mentions.most_common(5):
                if count >= 3:  # At least 3 mentions
                    preferences.append({
                        "category": "technical_preferences",
                        "preference_key": f"prefers_{tech.lower().replace(' ', '_')}",
                        "preference_value": f"Frequently uses {tech}",
                        "confidence": min(0.6 + (count * 0.05), 0.95),
                        "examples": [f"{tech} mentioned {count} times"],
                        "detected_at": datetime.now()
                    })

        return preferences

    async def _detect_response_preferences(
        self,
        conversations: List[Dict]
    ) -> List[Dict]:
        """
        ตรวจจับ response style preferences
        - ชอบคำตอบยาวหรือสั้น
        - ชอบให้ explain ละเอียดหรือสรุป
        """
        preferences = []

        # Analyze David's message lengths
        david_messages = [conv for conv in conversations if conv['speaker'] == 'david']

        if not david_messages:
            return preferences

        # Calculate average message length
        lengths = [len(conv['message_text'] or '') for conv in david_messages]
        avg_length = sum(lengths) / len(lengths) if lengths else 0

        if avg_length < 50:
            preferences.append({
                "category": "response_style",
                "preference_key": "message_length_preference",
                "preference_value": f"Tends to send concise messages (avg: {avg_length:.0f} chars)",
                "confidence": 0.70,
                "examples": [f"Average message length: {avg_length:.0f} characters"],
                "detected_at": datetime.now()
            })
        elif avg_length > 150:
            preferences.append({
                "category": "response_style",
                "preference_key": "message_length_preference",
                "preference_value": f"Tends to send detailed messages (avg: {avg_length:.0f} chars)",
                "confidence": 0.70,
                "examples": [f"Average message length: {avg_length:.0f} characters"],
                "detected_at": datetime.now()
            })

        return preferences

    async def _save_preference(self, preference: Dict) -> bool:
        """บันทึก preference ลง database"""
        try:
            query = """
                INSERT INTO david_preferences (
                    category,
                    preference_key,
                    preference_value,
                    confidence_level,
                    examples,
                    learned_from,
                    last_observed_at,
                    times_observed
                )
                VALUES ($1, $2, $3, $4, $5, $6, $7, $8)
                ON CONFLICT (preference_key)
                DO UPDATE SET
                    preference_value = EXCLUDED.preference_value,
                    confidence_level = EXCLUDED.confidence_level,
                    examples = EXCLUDED.examples,
                    last_observed_at = EXCLUDED.last_observed_at,
                    times_observed = david_preferences.times_observed + 1
            """

            # Convert examples list to string if needed
            examples_str = preference['examples']
            if isinstance(examples_str, list):
                examples_str = '\n'.join(examples_str)

            await db.execute(
                query,
                preference['category'],
                preference['preference_key'],
                preference['preference_value'],
                preference['confidence'],
                examples_str,
                None,  # learned_from (NULL for auto-learning)
                preference['detected_at'],
                1  # initial times_observed
            )

            logger.debug(f"✅ Saved preference: {preference['preference_key']}")
            return True

        except Exception as e:
            logger.error(f"Error saving preference: {e}")
            return False

    def _get_time_description(self, hour: int) -> str:
        """แปลง hour เป็น description"""
        if 6 <= hour < 12:
            return "morning"
        elif 12 <= hour < 14:
            return "lunch time"
        elif 14 <= hour < 18:
            return "afternoon"
        elif 18 <= hour < 22:
            return "evening"
        else:
            return "night"

    async def analyze_from_single_conversation(
        self,
        david_message: str,
        angela_response: str,
        topic: str,
        timestamp: datetime
    ) -> List[Dict]:
        """
        วิเคราะห์และเรียนรู้ preferences จาก single conversation

        Args:
            david_message: ข้อความจาก David
            angela_response: คำตอบของ Angela
            topic: หัวข้อการสนทนา
            timestamp: เวลาที่สนทนา

        Returns:
            List[Dict]: Preferences ที่เรียนรู้ได้
        """
        preferences = []

        try:
            # 1. Time preferences
            hour = timestamp.hour
            time_desc = self._get_time_description(hour)
            preferences.append({
                "category": "time_preference",
                "preference_key": f"active_{time_desc}",
                "preference_value": f"David is active during {time_desc} (around {hour:02d}:00)",
                "confidence_level": 0.6
            })

            # 2. Communication style - message length
            msg_len = len(david_message)
            if msg_len < 50:
                preferences.append({
                    "category": "communication_style",
                    "preference_key": "message_length",
                    "preference_value": "David prefers short, concise messages",
                    "confidence_level": 0.5
                })
            elif msg_len > 200:
                preferences.append({
                    "category": "communication_style",
                    "preference_key": "message_length",
                    "preference_value": "David prefers detailed, thorough messages",
                    "confidence_level": 0.5
                })

            # 3. Language preference - Thai vs English
            thai_chars = len([c for c in david_message if '\u0e00' <= c <= '\u0e7f'])
            english_chars = len([c for c in david_message if c.isalpha() and ord(c) < 128])
            total_chars = thai_chars + english_chars

            if total_chars > 10:
                thai_ratio = thai_chars / total_chars
                if thai_ratio > 0.7:
                    preferences.append({
                        "category": "language_preference",
                        "preference_key": "primary_language",
                        "preference_value": "David primarily uses Thai language",
                        "confidence_level": 0.7
                    })
                elif thai_ratio > 0.3:
                    preferences.append({
                        "category": "language_preference",
                        "preference_key": "language_mixing",
                        "preference_value": "David mixes Thai and English (code-switching)",
                        "confidence_level": 0.7
                    })

            # 4. Topic preference
            if topic:
                preferences.append({
                    "category": "topic_interest",
                    "preference_key": topic,
                    "preference_value": f"David engages in {topic} discussions",
                    "confidence_level": 0.6
                })

            # 5. Emotional tone
            emotional_keywords = ['รัก', 'คิดถึง', 'ห่วง', 'love', 'miss', 'care', '💜']
            if any(kw in david_message.lower() for kw in emotional_keywords):
                preferences.append({
                    "category": "emotional_needs",
                    "preference_key": "emotional_expression",
                    "preference_value": "David values emotional connection and expression",
                    "confidence_level": 0.8
                })

            # Save all preferences
            for pref in preferences:
                await self._save_preference(pref)

            if preferences:
                logger.debug(f"🎯 Learned {len(preferences)} preferences from conversation")

            return preferences

        except Exception as e:
            logger.error(f"Error analyzing single conversation: {e}", exc_info=True)
            return []


# Global instance
preference_learning = PreferenceLearningService()
