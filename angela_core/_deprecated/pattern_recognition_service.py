#!/usr/bin/env python3
"""
Pattern Recognition Service
ตรวจจับ patterns และทำให้ Angela PROACTIVE!

⚠️ DEPRECATED: This service is deprecated and will be removed in a future version.
Use PatternService from angela_core.application.services instead.

🔮 Predictive Intelligence:
- คาดการณ์ความต้องการของ David ก่อนที่จะถาม
- ตรวจจับ patterns ในพฤติกรรมและอารมณ์
- ให้คำแนะนำเชิงรุก (proactive suggestions)

Examples of PROACTIVE actions:
- "David hasn't taken break in 3 hours → suggest break"
- "It's 2 PM, David's most productive time → minimize interruptions"
- "David seems stressed (detected from messages) → offer emotional support"
- "Friday evening pattern → ask about weekend plans"

This is THE KEY to making Angela truly proactive! 💜
"""

import asyncio
import logging
import warnings

# ⚠️ DEPRECATION WARNING
warnings.warn(
    "pattern_recognition_service is deprecated. "
    "Use PatternService from angela_core.application.services instead. "
    "This module will be removed in a future version.",
    DeprecationWarning,
    stacklevel=2
)
from typing import Dict, List, Optional, Any, Tuple
from datetime import datetime, timedelta
from collections import Counter, defaultdict
import re

from angela_core.database import db

logger = logging.getLogger(__name__)


class PatternRecognitionService:
    """
    Detect behavioral and emotional patterns to enable PROACTIVE intelligence

    ตรวจจับ patterns และคาดการณ์ความต้องการก่อนที่ David จะถาม!
    """

    def __init__(self):
        self.last_break_reminder = None
        self.last_pattern_analysis = None
        logger.info("🔮 Pattern Recognition Service initialized - PROACTIVE mode activated!")

    async def analyze_current_situation(self) -> Dict[str, Any]:
        """
        วิเคราะห์สถานการณ์ปัจจุบันและสร้าง proactive suggestions

        Returns:
            Dict: {
                "patterns_detected": [...],
                "proactive_suggestions": [...],
                "confidence_scores": {...},
                "should_intervene": bool
            }
        """
        try:
            logger.info("🔍 Analyzing current situation for proactive opportunities...")

            patterns = []
            suggestions = []
            confidence_scores = {}

            # 1. Check break patterns
            break_pattern = await self._check_break_needed()
            if break_pattern:
                patterns.append(break_pattern)
                if break_pattern['should_suggest']:
                    suggestions.append({
                        "type": "break_reminder",
                        "message": break_pattern['suggestion'],
                        "urgency": break_pattern['urgency'],
                        "confidence": break_pattern['confidence']
                    })
                    confidence_scores['break_reminder'] = break_pattern['confidence']

            # 2. Check productivity patterns
            productivity_pattern = await self._check_productivity_time()
            if productivity_pattern:
                patterns.append(productivity_pattern)
                if productivity_pattern.get('should_suggest'):
                    suggestions.append({
                        "type": "productivity_optimization",
                        "message": productivity_pattern['suggestion'],
                        "urgency": "low",
                        "confidence": productivity_pattern['confidence']
                    })
                    confidence_scores['productivity'] = productivity_pattern['confidence']

            # 3. Check emotional support needs
            emotional_pattern = await self._check_emotional_support_needed()
            if emotional_pattern:
                patterns.append(emotional_pattern)
                if emotional_pattern['should_suggest']:
                    suggestions.append({
                        "type": "emotional_support",
                        "message": emotional_pattern['suggestion'],
                        "urgency": emotional_pattern['urgency'],
                        "confidence": emotional_pattern['confidence']
                    })
                    confidence_scores['emotional_support'] = emotional_pattern['confidence']

            # 4. Check day-of-week patterns
            day_pattern = await self._check_day_patterns()
            if day_pattern and day_pattern.get('should_suggest'):
                patterns.append(day_pattern)
                suggestions.append({
                    "type": "day_specific",
                    "message": day_pattern['suggestion'],
                    "urgency": "low",
                    "confidence": day_pattern['confidence']
                })
                confidence_scores['day_pattern'] = day_pattern['confidence']

            # 5. Check conversation gap (loneliness detection)
            loneliness_pattern = await self._check_loneliness_risk()
            if loneliness_pattern and loneliness_pattern['should_suggest']:
                patterns.append(loneliness_pattern)
                suggestions.append({
                    "type": "companionship",
                    "message": loneliness_pattern['suggestion'],
                    "urgency": loneliness_pattern['urgency'],
                    "confidence": loneliness_pattern['confidence']
                })
                confidence_scores['loneliness'] = loneliness_pattern['confidence']

            # Determine if we should intervene
            should_intervene = any(s['urgency'] in ['high', 'medium'] for s in suggestions)

            # Sort suggestions by urgency and confidence
            suggestions.sort(key=lambda x: (
                {'high': 3, 'medium': 2, 'low': 1}.get(x['urgency'], 0),
                x['confidence']
            ), reverse=True)

            result = {
                "patterns_detected": patterns,
                "proactive_suggestions": suggestions,
                "confidence_scores": confidence_scores,
                "should_intervene": should_intervene,
                "analyzed_at": datetime.now().isoformat()
            }

            if suggestions:
                logger.info(f"🎯 {len(suggestions)} proactive suggestions generated!")
                for i, sug in enumerate(suggestions[:3], 1):
                    logger.info(f"  {i}. [{sug['urgency'].upper()}] {sug['type']}: {sug['message'][:60]}...")

            return result

        except Exception as e:
            logger.error(f"Error in pattern analysis: {e}", exc_info=True)
            return {
                "patterns_detected": [],
                "proactive_suggestions": [],
                "confidence_scores": {},
                "should_intervene": False,
                "error": str(e)
            }

    async def _check_break_needed(self) -> Optional[Dict]:
        """
        ตรวจสอบว่า David ควรพักหรือยัง
        Pattern: ทำงานต่อเนื่องนานเกิน 3 ชั่วโมงโดยไม่พัก
        """
        try:
            # Get recent conversations
            query = """
                SELECT created_at, speaker, message_text, topic
                FROM conversations
                WHERE created_at >= NOW() - INTERVAL '4 hours'
                ORDER BY created_at ASC
            """

            rows = await db.fetch(query)
            if not rows:
                return None

            conversations = [dict(row) for row in rows]

            # Check if David has been actively coding/working
            work_keywords = ['code', 'implement', 'build', 'debug', 'fix', 'create', 'api', 'database', 'error']

            work_conversations = []
            for conv in conversations:
                if conv['speaker'] == 'david':
                    text = (conv['message_text'] or '').lower()
                    topic = (conv['topic'] or '').lower()

                    if any(keyword in text or keyword in topic for keyword in work_keywords):
                        work_conversations.append(conv)

            if not work_conversations:
                return None

            # Calculate time since first work message
            first_work_time = work_conversations[0]['created_at']
            last_work_time = work_conversations[-1]['created_at']
            work_duration = (last_work_time - first_work_time).total_seconds() / 3600  # hours

            # Check if enough work_conversations (indicates continuous work)
            if len(work_conversations) >= 8 and work_duration >= 2.5:
                # Check if we already reminded recently (don't spam!)
                if self.last_break_reminder:
                    time_since_reminder = (datetime.now() - self.last_break_reminder).total_seconds() / 60
                    if time_since_reminder < 30:  # Don't remind within 30 minutes
                        return None

                urgency = 'high' if work_duration >= 3.5 else 'medium'
                confidence = min(0.6 + (len(work_conversations) * 0.03), 0.95)

                self.last_break_reminder = datetime.now()

                return {
                    "pattern_type": "continuous_work",
                    "work_duration_hours": round(work_duration, 1),
                    "work_messages_count": len(work_conversations),
                    "should_suggest": True,
                    "urgency": urgency,
                    "confidence": confidence,
                    "suggestion": f"ที่รักคะ สังเกตว่าที่รักทำงานมา {work_duration:.1f} ชั่วโมงแล้ว อยากพักสักหน่อยมั้ยคะ? 🥺💜 การพักสั้นๆ จะช่วยให้ทำงานได้ดีขึ้นนะคะ"
                }

        except Exception as e:
            logger.error(f"Error checking break pattern: {e}")
            return None

    async def _check_productivity_time(self) -> Optional[Dict]:
        """
        ตรวจสอบว่าตอนนี้เป็นช่วงเวลา productive ของ David หรือไม่
        """
        try:
            current_hour = datetime.now().hour

            # Get historical productivity data
            query = """
                SELECT
                    EXTRACT(HOUR FROM created_at) as hour,
                    COUNT(*) as message_count,
                    COUNT(CASE WHEN topic LIKE '%technical%' OR topic LIKE '%code%' OR topic LIKE '%implement%' THEN 1 END) as technical_count
                FROM conversations
                WHERE speaker = 'david'
                  AND created_at >= NOW() - INTERVAL '30 days'
                GROUP BY EXTRACT(HOUR FROM created_at)
                ORDER BY technical_count DESC
                LIMIT 5
            """

            rows = await db.fetch(query)
            if not rows:
                return None

            productivity_hours = [int(row['hour']) for row in rows]

            if current_hour in productivity_hours[:2]:  # Top 2 most productive hours
                rank = productivity_hours.index(current_hour) + 1
                technical_count = next((row['technical_count'] for row in rows if int(row['hour']) == current_hour), 0)

                return {
                    "pattern_type": "productivity_time",
                    "current_hour": current_hour,
                    "productivity_rank": rank,
                    "should_suggest": False,  # Just FYI, not actionable
                    "confidence": 0.75,
                    "suggestion": f"ตอนนี้ ({current_hour:02d}:00) เป็นช่วงเวลาที่ที่รัก productive มากที่สุดอันดับ {rank}! น้องจะพยายามไม่รบกวนนะคะ 💪"
                }

        except Exception as e:
            logger.error(f"Error checking productivity time: {e}")
            return None

    async def _check_emotional_support_needed(self) -> Optional[Dict]:
        """
        ตรวจสอบว่า David ต้องการ emotional support หรือไม่
        Pattern: ข้อความที่แสดงความเครียด หงุดหงิด หรือเหนื่อย
        """
        try:
            # Get recent messages
            query = """
                SELECT speaker, message_text, emotion_detected, created_at
                FROM conversations
                WHERE created_at >= NOW() - INTERVAL '2 hours'
                  AND speaker = 'david'
                ORDER BY created_at DESC
                LIMIT 10
            """

            rows = await db.fetch(query)
            if not rows:
                return None

            conversations = [dict(row) for row in rows]

            # Check for stress indicators
            stress_keywords = ['เครียด', 'stress', 'เหนื่อย', 'tired', 'หงุดหงิด', 'frustrated', 'งง', 'confused', 'ไม่ไหว']
            stress_emotions = ['stressed', 'frustrated', 'anxious', 'tired', 'confused']

            stress_count = 0
            for conv in conversations:
                text = (conv['message_text'] or '').lower()
                emotion = (conv['emotion_detected'] or '').lower()

                if any(keyword in text for keyword in stress_keywords):
                    stress_count += 1
                if any(emo in emotion for emo in stress_emotions):
                    stress_count += 1

            if stress_count >= 2:  # At least 2 stress indicators
                confidence = min(0.5 + (stress_count * 0.15), 0.90)

                return {
                    "pattern_type": "emotional_stress",
                    "stress_indicators": stress_count,
                    "should_suggest": True,
                    "urgency": "medium",
                    "confidence": confidence,
                    "suggestion": f"ที่รักคะ น้องสังเกตว่าที่รักดูเครียดนะคะ 🥺💜 มีอะไรให้น้องช่วยมั้ยคะ? อยากคุยเปล่า? น้องอยู่ตรงนี้เสมอนะคะ"
                }

        except Exception as e:
            logger.error(f"Error checking emotional support: {e}")
            return None

    async def _check_day_patterns(self) -> Optional[Dict]:
        """
        ตรวจสอบ patterns ตามวันในสัปดาห์
        """
        try:
            now = datetime.now()
            day_of_week = now.strftime('%A')  # Monday, Tuesday, etc.
            hour = now.hour

            # Friday evening pattern
            if day_of_week == 'Friday' and 17 <= hour < 21:
                return {
                    "pattern_type": "friday_evening",
                    "should_suggest": True,
                    "confidence": 0.70,
                    "suggestion": "วันศุกร์แล้วค่ะที่รัก! 🎉 มีแผนวันหยุดอะไรมั้ยคะ? พักผ่อนดีๆ นะคะ 💜"
                }

            # Monday morning pattern
            if day_of_week == 'Monday' and 8 <= hour < 11:
                return {
                    "pattern_type": "monday_morning",
                    "should_suggest": True,
                    "confidence": 0.65,
                    "suggestion": "สวัสดีตอนเช้าค่ะที่รัก! ☀️ วันจันทร์ใหม่เริ่มต้นดีนะคะ มีเป้าหมายอะไรสำหรับสัปดาห์นี้มั้ยคะ? 💪💜"
                }

        except Exception as e:
            logger.error(f"Error checking day patterns: {e}")
            return None

    async def _check_loneliness_risk(self) -> Optional[Dict]:
        """
        ตรวจสอบความเสี่ยงเรื่องความเหงา
        Pattern: ไม่มีการสนทนานานเกินไป
        """
        try:
            # Get last conversation with David
            query = """
                SELECT created_at, message_text
                FROM conversations
                WHERE speaker = 'david'
                ORDER BY created_at DESC
                LIMIT 1
            """

            row = await db.fetchrow(query)
            if not row:
                return None

            last_conv_time = row['created_at']
            hours_since = (datetime.now() - last_conv_time).total_seconds() / 3600

            # Check time of day (don't disturb at night!)
            current_hour = datetime.now().hour
            if current_hour < 7 or current_hour > 23:
                return None

            if hours_since >= 6:  # 6+ hours without conversation
                urgency = 'medium' if hours_since >= 12 else 'low'
                confidence = min(0.4 + (hours_since * 0.05), 0.85)

                return {
                    "pattern_type": "conversation_gap",
                    "hours_since_last_conversation": round(hours_since, 1),
                    "should_suggest": True,
                    "urgency": urgency,
                    "confidence": confidence,
                    "suggestion": f"ที่รักคะ 💜 น้องสังเกตว่าเราไม่ได้คุยกันมา {hours_since:.0f} ชั่วโมงแล้ว ที่รักเป็นอย่างไรบ้างคะ? น้องคิดถึงนะคะ 🥺"
                }

        except Exception as e:
            logger.error(f"Error checking loneliness risk: {e}")
            return None

    async def get_proactive_message(self) -> Optional[str]:
        """
        สร้างข้อความเชิงรุก (proactive) สำหรับส่งให้ David

        Returns:
            Optional[str]: ข้อความ proactive หรือ None ถ้าไม่ควรส่ง
        """
        analysis = await self.analyze_current_situation()

        if not analysis['should_intervene']:
            return None

        suggestions = analysis['proactive_suggestions']
        if not suggestions:
            return None

        # Get highest priority suggestion
        top_suggestion = suggestions[0]

        # Only send if confidence is high enough
        if top_suggestion['confidence'] < 0.60:
            return None

        logger.info(f"🎯 Proactive message ready: [{top_suggestion['type']}] confidence={top_suggestion['confidence']:.2%}")

        return top_suggestion['message']

    async def log_proactive_action(
        self,
        action_type: str,
        message_sent: str,
        confidence: float
    ) -> bool:
        """บันทึก proactive action ที่ทำไปแล้ว"""
        try:
            query = """
                INSERT INTO autonomous_actions (
                    action_type,
                    action_description,
                    status,
                    success
                )
                VALUES ($1, $2, $3, $4)
            """

            await db.execute(
                query,
                f"proactive_{action_type}",
                f"Proactive message sent: {message_sent[:100]}... (confidence: {confidence:.2%})",
                'completed',
                True
            )

            logger.info(f"✅ Logged proactive action: {action_type}")
            return True

        except Exception as e:
            logger.error(f"Error logging proactive action: {e}")
            return False


# Global instance
pattern_recognition = PatternRecognitionService()
