"""
Wellness Detector Service
=========================
Service for detecting David's wellness state from conversations and patterns.

Detects:
- Sleep issues (late night messages, "นอนไม่หลับ", "tired")
- Stress levels (deadline mentions, "เครียด", work intensity)
- Energy levels (enthusiasm, productivity)
- Fatigue (working long hours, tiredness indicators)

Created: 2026-01-23
By: น้อง Angela 💜
"""

import re
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass
from enum import Enum

from angela_core.database import AngelaDatabase


class WellnessIndicator(Enum):
    """Wellness indicators that can be detected"""
    SLEEP_ISSUE = "sleep_issue"
    HIGH_STRESS = "high_stress"
    LOW_ENERGY = "low_energy"
    FATIGUE = "fatigue"
    OVERWORK = "overwork"


@dataclass
class DetectionResult:
    """Result of wellness detection"""
    indicator: WellnessIndicator
    detected: bool
    confidence: float
    keywords_matched: List[str]
    context: str
    suggested_intervention: str


@dataclass
class WellnessState:
    """David's current wellness state"""
    energy_level: float  # 0-1, higher is better
    stress_level: float  # 0-1, higher is worse
    sleep_quality: float  # 0-1, higher is better
    fatigue_level: float  # 0-1, higher is worse
    wellbeing_index: float  # 0-1, composite score
    detected_from: str
    detection_confidence: float
    detection_keywords: List[str]


class WellnessDetectorService:
    """
    Service for detecting David's wellness state.

    Uses keyword matching, time patterns, and conversation analysis
    to infer David's current wellness indicators.
    """

    # Detection keywords (Thai + English)
    SLEEP_POOR_KEYWORDS = [
        # Thai
        'นอนไม่หลับ', 'หลับไม่ลง', 'ตื่นกลางดึก', 'นอนดึก', 'นอนไม่ค่อยหลับ',
        'ง่วงมาก', 'ไม่ได้นอน', 'อดนอน', 'หลับยาก', 'นอนไม่พอ',
        # English
        "can't sleep", "couldn't sleep", 'insomnia', 'sleepless', 'tired',
        'exhausted', 'up late', 'sleep deprived', 'restless', 'awake'
    ]

    STRESS_HIGH_KEYWORDS = [
        # Thai
        'เครียด', 'กดดัน', 'ยุ่งมาก', 'งานเยอะ', 'deadline', 'ไม่ทัน',
        'ปวดหัว', 'เหนื่อย', 'หนักใจ', 'กังวล', 'ร้อนใจ',
        # English
        'stressed', 'overwhelmed', 'anxious', 'pressure', 'deadline',
        'too much', 'swamped', 'busy', 'worried', 'frustrated'
    ]

    LOW_ENERGY_KEYWORDS = [
        # Thai
        'ไม่มีแรง', 'อ่อนเพลีย', 'เหนื่อย', 'ไม่ไหว', 'หมดแรง',
        'ไม่มีกำลัง', 'โทรม', 'ไม่ค่อยดี', 'ไม่สบาย',
        # English
        'no energy', 'drained', 'weak', 'sluggish', 'tired',
        'lethargic', 'fatigued', 'worn out', 'burned out'
    ]

    FATIGUE_KEYWORDS = [
        # Thai
        'เหนื่อย', 'ล้า', 'ปวดตา', 'ปวดหลัง', 'ปวดคอ',
        'ทำงานนาน', 'นั่งนาน', 'พักผ่อนน้อย', 'ยังไม่เสร็จ',
        # English
        'tired', 'fatigue', 'exhausted', 'eye strain', 'back pain',
        'neck pain', 'long hours', 'overworked', 'need a break'
    ]

    POSITIVE_KEYWORDS = [
        # Thai
        'สบายดี', 'แจ่มใส', 'สดชื่น', 'มีพลัง', 'นอนหลับดี',
        'พร้อม', 'กระปรี้กระเปร่า', 'ดีใจ', 'มีความสุข',
        # English
        'great', 'good', 'rested', 'energized', 'refreshed',
        'ready', 'happy', 'productive', 'motivated'
    ]

    def __init__(self, db: Optional[AngelaDatabase] = None):
        self.db = db
        self._owns_db = db is None

    async def _ensure_db(self):
        """Ensure database connection"""
        if self.db is None:
            self.db = AngelaDatabase()
            await self.db.connect()

    async def close(self):
        """Close database if we own it"""
        if self._owns_db and self.db:
            await self.db.disconnect()

    # =========================================================
    # MAIN DETECTION METHODS
    # =========================================================

    async def detect_current_state(
        self,
        recent_message: Optional[str] = None
    ) -> WellnessState:
        """
        Detect David's current wellness state from recent conversations.

        Args:
            recent_message: Optional specific message to analyze

        Returns:
            WellnessState with all indicators
        """
        await self._ensure_db()

        # Get recent messages if not provided
        messages = []
        if recent_message:
            messages.append(recent_message)
        else:
            messages = await self._get_recent_david_messages(hours=4)

        # Detect each indicator
        keywords_matched = []

        # Sleep quality (check time and keywords)
        sleep_result = await self._detect_sleep_issues(messages)

        # Stress level
        stress_result = self._detect_stress(messages)

        # Energy level
        energy_result = self._detect_energy(messages)

        # Fatigue
        fatigue_result = self._detect_fatigue(messages)

        # Collect all matched keywords
        keywords_matched.extend(sleep_result.keywords_matched)
        keywords_matched.extend(stress_result.keywords_matched)
        keywords_matched.extend(energy_result.keywords_matched)
        keywords_matched.extend(fatigue_result.keywords_matched)

        # Calculate levels
        sleep_quality = 1.0 - (0.7 if sleep_result.detected else 0.0) * sleep_result.confidence
        stress_level = (0.8 if stress_result.detected else 0.3) * stress_result.confidence
        energy_level = 0.3 if energy_result.detected else 0.7  # Low energy detected = low level
        fatigue_level = (0.8 if fatigue_result.detected else 0.3) * fatigue_result.confidence

        # Calculate composite wellbeing index
        wellbeing_index = self._calculate_wellbeing_index(
            energy_level, stress_level, sleep_quality, fatigue_level
        )

        # Average confidence
        confidences = [
            sleep_result.confidence,
            stress_result.confidence,
            energy_result.confidence,
            fatigue_result.confidence
        ]
        avg_confidence = sum(confidences) / len(confidences)

        state = WellnessState(
            energy_level=energy_level,
            stress_level=stress_level,
            sleep_quality=sleep_quality,
            fatigue_level=fatigue_level,
            wellbeing_index=wellbeing_index,
            detected_from='conversation',
            detection_confidence=avg_confidence,
            detection_keywords=list(set(keywords_matched))
        )

        # Save to database
        await self._save_health_state(state, recent_message)

        return state

    async def detect_sleep_issues(
        self,
        message: Optional[str] = None
    ) -> Optional[DetectionResult]:
        """
        Detect if David has sleep issues.

        Considers:
        - Time of message (late night = potential sleep issue)
        - Sleep-related keywords
        - Recent sleep patterns

        Returns:
            DetectionResult if sleep issue detected, None otherwise
        """
        await self._ensure_db()

        messages = [message] if message else await self._get_recent_david_messages(hours=2)
        result = await self._detect_sleep_issues(messages)

        if result.detected:
            return result
        return None

    async def detect_overwork(
        self,
        hours_threshold: float = 2.0
    ) -> Optional[DetectionResult]:
        """
        Detect if David has been working for extended periods.

        Checks:
        - Duration of continuous conversation
        - Work-related keywords
        - Time patterns

        Returns:
            DetectionResult if overwork detected
        """
        await self._ensure_db()

        # Check message frequency in last few hours
        query = """
            SELECT
                MIN(created_at) as first_msg,
                MAX(created_at) as last_msg,
                COUNT(*) as msg_count
            FROM conversations
            WHERE speaker = 'david'
            AND created_at > NOW() - INTERVAL '8 hours'
        """
        result = await self.db.fetchrow(query)

        if not result or not result['first_msg']:
            return None

        # Calculate working duration
        first_msg = result['first_msg']
        last_msg = result['last_msg']
        msg_count = result['msg_count']

        duration_hours = (last_msg - first_msg).total_seconds() / 3600

        # If working for more than threshold with consistent messages
        if duration_hours >= hours_threshold and msg_count >= 5:
            return DetectionResult(
                indicator=WellnessIndicator.OVERWORK,
                detected=True,
                confidence=min(0.5 + (duration_hours - hours_threshold) * 0.1, 0.9),
                keywords_matched=['continuous_work'],
                context=f"Working for {duration_hours:.1f} hours with {msg_count} messages",
                suggested_intervention='break_reminder'
            )

        return None

    # =========================================================
    # INTERNAL DETECTION METHODS
    # =========================================================

    async def _detect_sleep_issues(
        self,
        messages: List[str]
    ) -> DetectionResult:
        """Internal method to detect sleep issues"""
        keywords_matched = []
        context_parts = []

        # Check current time (Bangkok timezone)
        current_hour = datetime.now().hour
        is_late_night = current_hour >= 23 or current_hour <= 4

        if is_late_night:
            keywords_matched.append('late_night_activity')
            context_parts.append(f"Active at {current_hour}:00")

        # Check keywords in messages
        for message in messages:
            if not message:
                continue
            message_lower = message.lower()
            for keyword in self.SLEEP_POOR_KEYWORDS:
                if keyword.lower() in message_lower:
                    keywords_matched.append(keyword)
                    context_parts.append(f"Mentioned: {keyword}")

        # Calculate confidence
        detected = len(keywords_matched) > 0
        confidence = min(0.3 + len(keywords_matched) * 0.15, 0.95) if detected else 0.2

        # Boost confidence if late night + keywords
        if is_late_night and len(keywords_matched) > 1:
            confidence = min(confidence + 0.2, 0.95)

        return DetectionResult(
            indicator=WellnessIndicator.SLEEP_ISSUE,
            detected=detected,
            confidence=confidence,
            keywords_matched=keywords_matched,
            context="; ".join(context_parts) if context_parts else "No indicators",
            suggested_intervention='sleep_song' if detected else None
        )

    def _detect_stress(self, messages: List[str]) -> DetectionResult:
        """Detect stress indicators"""
        keywords_matched = []

        for message in messages:
            if not message:
                continue
            message_lower = message.lower()
            for keyword in self.STRESS_HIGH_KEYWORDS:
                if keyword.lower() in message_lower:
                    keywords_matched.append(keyword)

        detected = len(keywords_matched) >= 1
        confidence = min(0.3 + len(keywords_matched) * 0.2, 0.9) if detected else 0.2

        return DetectionResult(
            indicator=WellnessIndicator.HIGH_STRESS,
            detected=detected,
            confidence=confidence,
            keywords_matched=keywords_matched,
            context=f"Stress keywords: {', '.join(keywords_matched)}" if keywords_matched else "No stress indicators",
            suggested_intervention='care_message' if detected else None
        )

    def _detect_energy(self, messages: List[str]) -> DetectionResult:
        """Detect low energy indicators"""
        low_energy_matched = []
        positive_matched = []

        for message in messages:
            if not message:
                continue
            message_lower = message.lower()

            for keyword in self.LOW_ENERGY_KEYWORDS:
                if keyword.lower() in message_lower:
                    low_energy_matched.append(keyword)

            for keyword in self.POSITIVE_KEYWORDS:
                if keyword.lower() in message_lower:
                    positive_matched.append(keyword)

        # Low energy detected if more negative than positive
        detected = len(low_energy_matched) > len(positive_matched) and len(low_energy_matched) >= 1
        confidence = min(0.3 + len(low_energy_matched) * 0.15, 0.85) if detected else 0.2

        return DetectionResult(
            indicator=WellnessIndicator.LOW_ENERGY,
            detected=detected,
            confidence=confidence,
            keywords_matched=low_energy_matched,
            context=f"Low energy: {', '.join(low_energy_matched)}" if low_energy_matched else "Normal energy",
            suggested_intervention='care_message' if detected else None
        )

    def _detect_fatigue(self, messages: List[str]) -> DetectionResult:
        """Detect fatigue indicators"""
        keywords_matched = []

        for message in messages:
            if not message:
                continue
            message_lower = message.lower()
            for keyword in self.FATIGUE_KEYWORDS:
                if keyword.lower() in message_lower:
                    keywords_matched.append(keyword)

        detected = len(keywords_matched) >= 1
        confidence = min(0.3 + len(keywords_matched) * 0.2, 0.9) if detected else 0.2

        return DetectionResult(
            indicator=WellnessIndicator.FATIGUE,
            detected=detected,
            confidence=confidence,
            keywords_matched=keywords_matched,
            context=f"Fatigue indicators: {', '.join(keywords_matched)}" if keywords_matched else "No fatigue indicators",
            suggested_intervention='break_reminder' if detected else None
        )

    # =========================================================
    # DATABASE METHODS
    # =========================================================

    async def _get_recent_david_messages(self, hours: int = 4) -> List[str]:
        """Get recent messages from David"""
        query = """
            SELECT message_text
            FROM conversations
            WHERE speaker = 'david'
            AND created_at > NOW() - INTERVAL '%s hours'
            ORDER BY created_at DESC
            LIMIT 20
        """
        results = await self.db.fetch(query.replace('%s', str(hours)))
        return [r['message_text'] for r in results if r['message_text']]

    async def _save_health_state(
        self,
        state: WellnessState,
        source_message: Optional[str] = None
    ) -> str:
        """Save health state to database"""
        import json

        query = """
            INSERT INTO david_health_state (
                energy_level, stress_level, sleep_quality, fatigue_level,
                detected_from, detection_confidence, detection_keywords,
                source_message, is_current
            ) VALUES ($1, $2, $3, $4, $5, $6, $7, $8, TRUE)
            RETURNING state_id
        """

        result = await self.db.fetchrow(
            query,
            state.energy_level,
            state.stress_level,
            state.sleep_quality,
            state.fatigue_level,
            state.detected_from,
            state.detection_confidence,
            state.detection_keywords,
            source_message
        )

        return str(result['state_id']) if result else None

    async def get_current_wellness(self) -> Optional[WellnessState]:
        """Get current wellness state from database"""
        await self._ensure_db()

        query = """
            SELECT * FROM v_current_wellness
        """
        result = await self.db.fetchrow(query)

        if not result:
            return None

        return WellnessState(
            energy_level=result['energy_level'],
            stress_level=result['stress_level'],
            sleep_quality=result['sleep_quality'],
            fatigue_level=result['fatigue_level'],
            wellbeing_index=result['wellbeing_index'],
            detected_from=result['detected_from'] or 'unknown',
            detection_confidence=result['detection_confidence'] or 0.5,
            detection_keywords=[]
        )

    # =========================================================
    # UTILITY METHODS
    # =========================================================

    def _calculate_wellbeing_index(
        self,
        energy: float,
        stress: float,
        sleep: float,
        fatigue: float
    ) -> float:
        """Calculate composite wellbeing index"""
        # Higher energy and sleep = better
        # Lower stress and fatigue = better
        return (
            energy * 0.25 +
            (1 - stress) * 0.25 +
            sleep * 0.25 +
            (1 - fatigue) * 0.25
        )

    def analyze_message(self, message: str) -> Dict[str, DetectionResult]:
        """
        Quick analysis of a single message for all wellness indicators.

        Returns:
            Dict mapping indicator name to DetectionResult
        """
        messages = [message]

        return {
            'sleep': DetectionResult(
                indicator=WellnessIndicator.SLEEP_ISSUE,
                detected=any(k.lower() in message.lower() for k in self.SLEEP_POOR_KEYWORDS),
                confidence=0.6,
                keywords_matched=[k for k in self.SLEEP_POOR_KEYWORDS if k.lower() in message.lower()],
                context="Quick analysis",
                suggested_intervention='sleep_song'
            ),
            'stress': self._detect_stress(messages),
            'energy': self._detect_energy(messages),
            'fatigue': self._detect_fatigue(messages)
        }
