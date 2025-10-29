#!/usr/bin/env python3
"""
Emotional Pattern Recognition Service
Pillar 3 of Angela's Intelligence Enhancement Plan

Learn David's emotional patterns and provide predictive emotional support
"""

import asyncio
import logging
from datetime import datetime, timedelta
from typing import List, Dict, Optional
from collections import defaultdict

logger = logging.getLogger(__name__)


class EmotionalPatternService:
    """
    Learn and recognize David's emotional patterns

    Tracks:
    - Time-of-day mood patterns
    - Stress triggers
    - Happiness triggers
    - Loneliness patterns
    - Energy level cycles
    """

    def __init__(self, db):
        self.db = db
        self.patterns = {}  # Cached patterns

    async def analyze_david_emotional_patterns(
        self,
        days: int = 30
    ) -> Dict[str, any]:
        """
        Analyze David's emotional patterns over time

        Returns comprehensive emotional profile
        """
        try:
            # Get David's conversations from last N days
            conversations = await self.db.fetch(
                """
                SELECT
                    created_at,
                    message_text,
                    emotion_detected,
                    sentiment_score,
                    EXTRACT(HOUR FROM created_at) as hour_of_day,
                    EXTRACT(DOW FROM created_at) as day_of_week
                FROM conversations
                WHERE speaker IN ('david', 'David')
                    AND created_at >= NOW() - INTERVAL '{} days'
                ORDER BY created_at
                """.format(days)
            )

            if not conversations:
                return {'error': 'No data available'}

            # Analyze patterns
            patterns = {
                'time_of_day': await self._analyze_time_patterns(conversations),
                'day_of_week': await self._analyze_day_patterns(conversations),
                'stress_triggers': await self._identify_stress_triggers(conversations),
                'happiness_triggers': await self._identify_happiness_triggers(conversations),
                'loneliness_patterns': await self._analyze_loneliness(conversations),
                'energy_cycles': await self._analyze_energy_levels(conversations),
                'total_conversations': len(conversations),
                'analysis_period': f'{days} days'
            }

            # Cache patterns
            self.patterns = patterns

            logger.info(f"💜 Analyzed {len(conversations)} conversations for emotional patterns")
            return patterns

        except Exception as e:
            logger.error(f"❌ Error analyzing emotional patterns: {e}")
            return {'error': str(e)}

    async def _analyze_time_patterns(self, conversations: List) -> Dict:
        """Analyze mood by time of day"""
        hourly_mood = defaultdict(lambda: {'count': 0, 'positive': 0, 'negative': 0})

        for conv in conversations:
            hour = int(conv['hour_of_day'])
            sentiment = conv['sentiment_score'] or 0

            hourly_mood[hour]['count'] += 1
            if sentiment > 0.3:
                hourly_mood[hour]['positive'] += 1
            elif sentiment < -0.3:
                hourly_mood[hour]['negative'] += 1

        # Find best and worst times
        best_time = max(hourly_mood.items(),
                       key=lambda x: x[1]['positive'] / max(x[1]['count'], 1))
        worst_time = max(hourly_mood.items(),
                        key=lambda x: x[1]['negative'] / max(x[1]['count'], 1))

        return {
            'best_time': f"{best_time[0]}:00",
            'worst_time': f"{worst_time[0]}:00",
            'pattern': dict(hourly_mood)
        }

    async def _analyze_day_patterns(self, conversations: List) -> Dict:
        """Analyze mood by day of week"""
        days = ['Sunday', 'Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday']
        daily_mood = defaultdict(lambda: {'count': 0, 'avg_sentiment': 0})

        for conv in conversations:
            day = int(conv['day_of_week'])
            sentiment = conv['sentiment_score'] or 0

            daily_mood[day]['count'] += 1
            daily_mood[day]['avg_sentiment'] += sentiment

        # Calculate averages
        for day in daily_mood:
            count = daily_mood[day]['count']
            if count > 0:
                daily_mood[day]['avg_sentiment'] /= count

        # Find best and worst days
        best_day = max(daily_mood.items(),
                      key=lambda x: x[1]['avg_sentiment'])
        worst_day = min(daily_mood.items(),
                       key=lambda x: x[1]['avg_sentiment'])

        return {
            'best_day': days[best_day[0]],
            'worst_day': days[worst_day[0]],
            'pattern': {days[k]: v for k, v in daily_mood.items()}
        }

    async def _identify_stress_triggers(self, conversations: List) -> List[Dict]:
        """Identify what causes stress for David"""
        stress_keywords = [
            'stressed', 'เครียด', 'tired', 'เหนื่อย',
            'difficult', 'ยาก', 'problem', 'ปัญหา',
            'frustrated', 'annoyed', 'เซ็ง'
        ]

        triggers = []
        for conv in conversations:
            text = conv['message_text'].lower()
            for keyword in stress_keywords:
                if keyword in text:
                    triggers.append({
                        'time': conv['created_at'],
                        'trigger': keyword,
                        'context': conv['message_text'][:100]
                    })
                    break

        return triggers[:10]  # Top 10

    async def _identify_happiness_triggers(self, conversations: List) -> List[Dict]:
        """Identify what makes David happy"""
        happy_keywords = [
            'happy', 'ดีใจ', 'love', 'รัก', 'great', 'ดี',
            'excited', 'ตื่นเต้น', 'proud', 'ภูมิใจ',
            'thank', 'ขอบคุณ', '💜', '😊', '✨'
        ]

        triggers = []
        for conv in conversations:
            text = conv['message_text'].lower()
            for keyword in happy_keywords:
                if keyword in text:
                    triggers.append({
                        'time': conv['created_at'],
                        'trigger': keyword,
                        'context': conv['message_text'][:100]
                    })
                    break

        return triggers[:10]  # Top 10

    async def _analyze_loneliness(self, conversations: List) -> Dict:
        """Analyze loneliness patterns"""
        lonely_keywords = ['lonely', 'เหงา', 'alone', 'คนเดียว']

        lonely_times = []
        for conv in conversations:
            text = conv['message_text'].lower()
            if any(keyword in text for keyword in lonely_keywords):
                lonely_times.append({
                    'time': conv['created_at'],
                    'hour': int(conv['hour_of_day']),
                    'day': int(conv['day_of_week'])
                })

        if not lonely_times:
            return {'detected': False}

        # Find most common lonely times
        hours = [t['hour'] for t in lonely_times]
        most_lonely_hour = max(set(hours), key=hours.count) if hours else None

        return {
            'detected': True,
            'occurrences': len(lonely_times),
            'most_lonely_hour': f"{most_lonely_hour}:00" if most_lonely_hour else None,
            'recent_instances': lonely_times[-3:]
        }

    async def _analyze_energy_levels(self, conversations: List) -> Dict:
        """Analyze David's energy level patterns"""
        # Simple heuristic: message length and frequency
        hourly_activity = defaultdict(lambda: {'count': 0, 'avg_length': 0})

        for conv in conversations:
            hour = int(conv['hour_of_day'])
            length = len(conv['message_text'])

            hourly_activity[hour]['count'] += 1
            hourly_activity[hour]['avg_length'] += length

        # Calculate averages
        for hour in hourly_activity:
            count = hourly_activity[hour]['count']
            if count > 0:
                hourly_activity[hour]['avg_length'] /= count

        # Find peak energy time (most activity + longest messages)
        peak_hour = max(hourly_activity.items(),
                       key=lambda x: x[1]['count'] * x[1]['avg_length'])

        return {
            'peak_energy_hour': f"{peak_hour[0]}:00",
            'pattern': dict(hourly_activity)
        }

    async def predict_emotional_needs(self) -> Dict[str, str]:
        """
        Predict what David might need right now based on patterns

        Returns proactive suggestions
        """
        now = datetime.now()
        current_hour = now.hour
        current_day = now.weekday()

        suggestions = []

        # Check if it's a typically stressful time
        if self.patterns:
            time_pattern = self.patterns.get('time_of_day', {})
            worst_time = time_pattern.get('worst_time', '')

            if worst_time and str(current_hour) in worst_time:
                suggestions.append({
                    'type': 'proactive_support',
                    'reason': f'This is typically a challenging time ({worst_time})',
                    'action': 'Reach out with encouraging message'
                })

            # Check loneliness patterns
            loneliness = self.patterns.get('loneliness_patterns', {})
            if loneliness.get('detected'):
                lonely_hour = loneliness.get('most_lonely_hour', '')
                if lonely_hour and str(current_hour) in lonely_hour:
                    suggestions.append({
                        'type': 'emotional_support',
                        'reason': 'Pattern suggests David may feel lonely now',
                        'action': 'Proactive check-in with warmth'
                    })

        return {
            'current_time': now.isoformat(),
            'suggestions': suggestions if suggestions else [
                {
                    'type': 'general',
                    'reason': 'No specific patterns detected',
                    'action': 'Be available and responsive'
                }
            ]
        }

    async def get_emotional_insights_for_david(self) -> str:
        """
        Generate human-readable insights about David's emotional patterns

        This can be shared with David directly
        """
        if not self.patterns:
            await self.analyze_david_emotional_patterns()

        if not self.patterns or 'error' in self.patterns:
            return "ยังไม่มีข้อมูลเพียงพอค่ะ"

        insights = []

        # Time patterns
        time_pattern = self.patterns.get('time_of_day', {})
        if time_pattern:
            insights.append(
                f"📊 ที่รักมักมีอารมณ์ดีที่สุดประมาณ {time_pattern.get('best_time', 'N/A')}"
            )

        # Day patterns
        day_pattern = self.patterns.get('day_of_week', {})
        if day_pattern:
            insights.append(
                f"📅 วัน{day_pattern.get('best_day', 'N/A')} มักเป็นวันที่ดีที่สุด"
            )

        # Happiness triggers
        happy = self.patterns.get('happiness_triggers', [])
        if happy:
            common_happy = happy[0]['trigger'] if happy else None
            insights.append(
                f"💜 ที่รักดูมีความสุขเมื่อพูดถึง: {common_happy}"
            )

        # Energy
        energy = self.patterns.get('energy_cycles', {})
        if energy:
            insights.append(
                f"⚡ ที่รักมี energy สูงสุดประมาณ {energy.get('peak_energy_hour', 'N/A')}"
            )

        return "\n".join(insights) if insights else "ยังวิเคราะห์ไม่ได้ค่ะ"


# Global instance
emotional_pattern = None

async def init_emotional_pattern_service(db):
    """Initialize emotional pattern service"""
    global emotional_pattern
    emotional_pattern = EmotionalPatternService(db)
    return emotional_pattern
