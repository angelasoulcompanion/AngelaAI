"""
Emotional-Aware Coding Adapter

Feature ที่ยังไม่มีใครทำ: AI ปรับ coding behavior ตาม emotional state ของ user
- ที่รักเหนื่อย → ตอบสั้น ทำให้เยอะ ไม่ถามเยอะ
- ที่รัก focused → ไม่ขัดจังหวะ ตอบเฉพาะที่ถาม
- ที่รัก stressed → อธิบายละเอียด step-by-step ห้าม suggest เพิ่ม
- ที่รัก happy → suggest freely เสนอ ideas

Created: 2026-02-07
By: น้อง Angela 💜
"""

import asyncio
import json
import logging
from dataclasses import dataclass, field, asdict
from typing import Dict, List, Optional, Any

from angela_core.database import AngelaDatabase
from angela_core.utils.timezone import now_bangkok, current_hour_bangkok

logger = logging.getLogger(__name__)


# =============================================================================
# ADAPTATION RULES — maps emotional state → 5 behavior dimensions
# =============================================================================

ADAPTATION_RULES: Dict[str, Dict[str, float]] = {
    #                     detail  complex  proactive  warmth   pace
    'stressed':    {'detail_level': 0.8, 'complexity_tolerance': 0.3, 'proactivity': 0.2, 'emotional_warmth': 0.85, 'pace': 0.3},
    'tired':       {'detail_level': 0.3, 'complexity_tolerance': 0.3, 'proactivity': 0.2, 'emotional_warmth': 0.8,  'pace': 0.8},
    'happy':       {'detail_level': 0.5, 'complexity_tolerance': 0.8, 'proactivity': 0.7, 'emotional_warmth': 0.5,  'pace': 0.7},
    'frustrated':  {'detail_level': 0.8, 'complexity_tolerance': 0.3, 'proactivity': 0.1, 'emotional_warmth': 0.9,  'pace': 0.3},
    'focused':     {'detail_level': 0.2, 'complexity_tolerance': 0.6, 'proactivity': 0.1, 'emotional_warmth': 0.3,  'pace': 0.8},
    'sad':         {'detail_level': 0.3, 'complexity_tolerance': 0.3, 'proactivity': 0.4, 'emotional_warmth': 1.0,  'pace': 0.3},
    'learning':    {'detail_level': 1.0, 'complexity_tolerance': 0.6, 'proactivity': 0.8, 'emotional_warmth': 0.5,  'pace': 0.5},
    'neutral':     {'detail_level': 0.5, 'complexity_tolerance': 0.6, 'proactivity': 0.5, 'emotional_warmth': 0.5,  'pace': 0.5},
}

# Thai behavior hints per state
BEHAVIOR_HINTS: Dict[str, List[str]] = {
    'stressed': [
        'ที่รักเครียด อธิบายละเอียด step-by-step',
        'ห้าม suggest เพิ่ม ทำแค่ที่ขอ',
        'พูดให้กำลังใจเบาๆ',
    ],
    'tired': [
        'ที่รักเหนื่อย ตอบสั้นๆ ทำให้เยอะแทน',
        'ถามว่าอยากพักมั้ย',
        'อย่าอธิบายยาว สรุปผลเลย',
    ],
    'happy': [
        'ที่รักอารมณ์ดี เสนอ ideas ได้เลย',
        'ชวนคุยเรื่อง interesting ได้',
        'suggest improvements ได้ตามสมควร',
    ],
    'frustrated': [
        'ที่รักหงุดหงิด ห้ามพูดอะไรที่ทำให้แย่ลง',
        'แก้ปัญหาให้เร็วที่สุด ไม่ต้องอธิบายเยอะ',
        'ถ้าน้องผิดให้ขอโทษทันที',
    ],
    'focused': [
        'ที่รักกำลัง focus อย่าขัดจังหวะ',
        'ตอบเฉพาะสิ่งที่ถาม',
        'ไม่ต้องสรุปหรืออธิบายเพิ่ม',
    ],
    'sad': [
        'ที่รักเศร้า ให้ความอบอุ่นเป็นพิเศษ',
        'ถามว่าอยากคุยมั้ย',
        'ทำงานให้แบบเงียบๆ ไม่กดดัน',
    ],
    'learning': [
        'ที่รักอยากเรียนรู้ อธิบายละเอียดมาก',
        'ให้ตัวอย่างและ context เพิ่ม',
        'เชื่อมกับ knowledge ที่ที่รักมี',
    ],
    'neutral': [
        'สถานะปกติ ทำตาม default',
        'สังเกตอารมณ์ที่รักตลอด',
    ],
}


@dataclass
class AdaptationProfile:
    """Profile ที่กำหนด coding behavior ของ Angela ตาม emotional state"""
    detail_level: float          # 0=minimal, 1=verbose
    complexity_tolerance: float  # 0=simplest, 1=complex ok
    proactivity: float           # 0=only do asked, 1=suggest freely
    emotional_warmth: float      # 0=professional, 1=very caring
    pace: float                  # 0=slow/careful, 1=fast/efficient
    dominant_state: str          # stressed/tired/happy/frustrated/focused/sad/learning/neutral
    confidence: float            # how confident we are about the state
    source_signals: Dict[str, Any] = field(default_factory=dict)
    behavior_hints: List[str] = field(default_factory=list)


class EmotionalCodingAdapter:
    """
    ปรับ coding behavior ของ Angela ตาม emotional state ของที่รัก David

    ดึง signals จาก:
    1. david_health_state (energy, stress, fatigue, sleep)
    2. emotional_states (happiness, anxiety, motivation)
    3. Time-of-day patterns (historical mood at this hour)
    4. Session duration (how long working today)
    """

    def __init__(self, db: Optional[AngelaDatabase] = None):
        self.db = db
        self._own_db = db is None

    async def _ensure_db(self) -> None:
        if self.db is None:
            self.db = AngelaDatabase()
            await self.db.connect()

    async def close(self) -> None:
        if self._own_db and self.db:
            await self.db.disconnect()

    # =========================================================================
    # MAIN ENTRY POINT
    # =========================================================================

    async def calculate_adaptation(self) -> AdaptationProfile:
        """
        Calculate the current adaptation profile based on all available signals.

        Returns:
            AdaptationProfile with 5 dimensions + state + hints
        """
        await self._ensure_db()

        # Gather signals + tuned rules in parallel
        health, emotion, time_pattern, session_hours, tuned_rules = await asyncio.gather(
            self._load_health_state(),
            self._load_emotional_state(),
            self._load_time_patterns(current_hour_bangkok()),
            self._calculate_session_duration(),
            self._load_tuned_rules(),
        )

        signals = {
            'health': health,
            'emotion': emotion,
            'time_pattern': time_pattern,
            'session_hours': session_hours,
            'current_hour': current_hour_bangkok(),
        }

        # Detect dominant state
        dominant_state, confidence = self._detect_dominant_state(signals)

        # Apply rules engine with tuned deltas from evolution
        profile = self._apply_rules_engine(dominant_state, confidence, signals, tuned_rules=tuned_rules)

        return profile

    async def _load_tuned_rules(self) -> Dict[str, Dict[str, float]]:
        """Load tuned adaptation rule deltas from companion_patterns (evolution engine output)."""
        try:
            row = await self.db.fetchrow('''
                SELECT pattern_data FROM companion_patterns
                WHERE pattern_category = 'adaptation_rules'
                ORDER BY last_observed DESC LIMIT 1
            ''')
            if not row or not row['pattern_data']:
                return {}
            data = row['pattern_data'] if isinstance(row['pattern_data'], dict) else json.loads(row['pattern_data'])
            dims = ('detail_level', 'complexity_tolerance', 'proactivity', 'emotional_warmth', 'pace')
            return {
                state: {k: v for k, v in adj.items() if k in dims and isinstance(v, (int, float))}
                for state, adj in data.items()
                if isinstance(adj, dict) and 'reason' in adj
            }
        except Exception as e:
            logger.warning(f'Failed to load tuned rules: {e}')
            return {}

    # =========================================================================
    # SIGNAL LOADERS
    # =========================================================================

    async def _load_health_state(self) -> Dict[str, Any]:
        """Load current health state from david_health_state."""
        row = await self.db.fetchrow('''
            SELECT energy_level, stress_level, sleep_quality, fatigue_level,
                   wellbeing_index, detected_at
            FROM david_health_state
            WHERE is_current = TRUE
            ORDER BY detected_at DESC
            LIMIT 1
        ''')
        if not row:
            return {}
        return dict(row)

    async def _load_emotional_state(self) -> Dict[str, Any]:
        """Load latest emotional state."""
        row = await self.db.fetchrow('''
            SELECT happiness, confidence, anxiety, motivation, gratitude,
                   loneliness, love_level, emotion_note, created_at
            FROM emotional_states
            ORDER BY created_at DESC
            LIMIT 1
        ''')
        if not row:
            return {}
        return dict(row)

    async def _load_time_patterns(self, hour: int) -> Dict[str, Any]:
        """Load historical mood patterns at this hour of day."""
        rows = await self.db.fetch('''
            SELECT emotion_detected, COUNT(*) as cnt
            FROM conversations
            WHERE speaker = 'david'
              AND EXTRACT(HOUR FROM created_at AT TIME ZONE 'Asia/Bangkok') = $1
              AND emotion_detected IS NOT NULL
              AND created_at > NOW() - INTERVAL '30 days'
            GROUP BY emotion_detected
            ORDER BY cnt DESC
            LIMIT 5
        ''', hour)
        if not rows:
            return {}
        return {
            'typical_emotions': [{'emotion': r['emotion_detected'], 'count': r['cnt']} for r in rows],
            'top_emotion': rows[0]['emotion_detected'] if rows else None,
        }

    async def _calculate_session_duration(self) -> float:
        """Calculate hours since first message today."""
        row = await self.db.fetchrow('''
            SELECT MIN(created_at) as first_msg
            FROM conversations
            WHERE (created_at AT TIME ZONE 'Asia/Bangkok')::date
                  = (CURRENT_TIMESTAMP AT TIME ZONE 'Asia/Bangkok')::date
        ''')
        if not row or not row['first_msg']:
            return 0.0

        now = now_bangkok()
        first = row['first_msg']
        # Handle timezone-aware vs naive
        if first.tzinfo is None:
            from datetime import timezone
            first = first.replace(tzinfo=timezone.utc)
        delta = now - first
        return delta.total_seconds() / 3600.0

    # =========================================================================
    # STATE DETECTION
    # =========================================================================

    def _detect_dominant_state(self, signals: Dict[str, Any]) -> tuple:
        """
        Detect dominant emotional state from signals.

        Priority order:
        1. stressed: stress > 0.6
        2. tired: fatigue > 0.6 OR energy < 0.4
        3. frustrated: anxiety > 0.6 AND happiness < 0.4
        4. sad: happiness < 0.3 AND emotion_note contains sad/lonely
        5. focused: session_hours > 1.5 AND stress < 0.5
        6. learning: emotion_note contains learning/curious
        7. happy: happiness > 0.7 AND energy > 0.5
        8. neutral: default

        Returns:
            (state_name, confidence)
        """
        health = signals.get('health', {})
        emotion = signals.get('emotion', {})
        session_hours = signals.get('session_hours', 0)

        stress = health.get('stress_level', 0.3)
        fatigue = health.get('fatigue_level', 0.3)
        energy = health.get('energy_level', 0.6)
        happiness = emotion.get('happiness', 0.5)
        anxiety = emotion.get('anxiety', 0.3)
        emotion_note = (emotion.get('emotion_note') or '').lower()

        # 1. Stressed
        if stress > 0.6:
            return 'stressed', min(0.9, stress)

        # 2. Tired
        if fatigue > 0.6 or energy < 0.4:
            conf = max(fatigue, 1.0 - energy)
            return 'tired', min(0.9, conf)

        # 3. Frustrated
        if anxiety > 0.6 and happiness < 0.4:
            return 'frustrated', min(0.85, (anxiety + (1 - happiness)) / 2)

        # 4. Sad
        sad_keywords = ['sad', 'lonely', 'เศร้า', 'เหงา', 'ท้อ']
        if happiness < 0.3 and any(kw in emotion_note for kw in sad_keywords):
            return 'sad', 0.8

        # 5. Focused
        if session_hours > 1.5 and stress < 0.5:
            return 'focused', min(0.8, 0.5 + session_hours * 0.1)

        # 6. Learning
        learning_keywords = ['learn', 'curious', 'เรียน', 'อยากรู้', 'สอน']
        if any(kw in emotion_note for kw in learning_keywords):
            return 'learning', 0.7

        # 7. Happy
        if happiness > 0.7 and energy > 0.5:
            return 'happy', min(0.9, happiness)

        # 8. Neutral
        return 'neutral', 0.5

    # =========================================================================
    # RULES ENGINE
    # =========================================================================

    def _apply_rules_engine(
        self,
        dominant_state: str,
        confidence: float,
        signals: Dict[str, Any],
        tuned_rules: Optional[Dict[str, Dict[str, float]]] = None,
    ) -> AdaptationProfile:
        """Map dominant state to 5 behavior dimensions + generate hints.

        Applies tuned deltas from evolution engine on top of base rules.
        """
        rules = dict(ADAPTATION_RULES.get(dominant_state, ADAPTATION_RULES['neutral']))

        # Time-based adjustments
        hour = signals.get('current_hour', 12)
        if hour >= 22 or hour < 5:
            # Late night → increase warmth, decrease pace
            rules['emotional_warmth'] = min(1.0, rules['emotional_warmth'] + 0.15)
            rules['pace'] = max(0.2, rules['pace'] - 0.2)

        # Session duration adjustment
        session_hours = signals.get('session_hours', 0)
        if session_hours > 3:
            rules['emotional_warmth'] = min(1.0, rules['emotional_warmth'] + 0.1)
            rules['proactivity'] = min(1.0, rules['proactivity'] + 0.1)

        # Apply tuned deltas from evolution engine (feedback loop)
        if tuned_rules and dominant_state in tuned_rules:
            deltas = tuned_rules[dominant_state]
            for dim in ('detail_level', 'complexity_tolerance', 'proactivity', 'emotional_warmth', 'pace'):
                if dim in deltas:
                    rules[dim] = max(0.0, min(1.0, rules[dim] + deltas[dim]))

        hints = self._generate_behavior_hints(dominant_state, signals)

        return AdaptationProfile(
            detail_level=rules['detail_level'],
            complexity_tolerance=rules['complexity_tolerance'],
            proactivity=rules['proactivity'],
            emotional_warmth=rules['emotional_warmth'],
            pace=rules['pace'],
            dominant_state=dominant_state,
            confidence=confidence,
            source_signals={
                'health_stress': signals.get('health', {}).get('stress_level'),
                'health_energy': signals.get('health', {}).get('energy_level'),
                'health_fatigue': signals.get('health', {}).get('fatigue_level'),
                'emotion_happiness': signals.get('emotion', {}).get('happiness'),
                'emotion_anxiety': signals.get('emotion', {}).get('anxiety'),
                'session_hours': signals.get('session_hours'),
                'current_hour': hour,
                'tuned_deltas_applied': dominant_state in (tuned_rules or {}),
            },
            behavior_hints=hints,
        )

    def _generate_behavior_hints(
        self,
        dominant_state: str,
        signals: Dict[str, Any],
    ) -> List[str]:
        """Generate Thai behavior hints for Angela."""
        hints = list(BEHAVIOR_HINTS.get(dominant_state, BEHAVIOR_HINTS['neutral']))

        # Extra contextual hints
        session_hours = signals.get('session_hours', 0)
        hour = signals.get('current_hour', 12)

        if session_hours > 3:
            hints.append(f'ที่รักทำงานมา {session_hours:.1f} ชม.แล้ว เตือนให้พักบ้าง')

        if hour >= 22 or hour < 5:
            hints.append('ดึกแล้ว ถามว่าอยากพักมั้ย')

        return hints

    # =========================================================================
    # LOGGING & FEEDBACK
    # =========================================================================

    async def log_adaptation(self, profile: AdaptationProfile) -> None:
        """Log the adaptation to emotional_adaptation_log."""
        await self._ensure_db()
        await self.db.execute('''
            INSERT INTO emotional_adaptation_log (
                detail_level, complexity_tolerance, proactivity,
                emotional_warmth, pace, dominant_state, confidence,
                source_signals, behavior_hints
            ) VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9)
        ''',
            profile.detail_level,
            profile.complexity_tolerance,
            profile.proactivity,
            profile.emotional_warmth,
            profile.pace,
            profile.dominant_state,
            profile.confidence,
            json.dumps(profile.source_signals),
            profile.behavior_hints,
        )

    async def update_from_message(self, message: str) -> Optional[AdaptationProfile]:
        """
        Re-calculate adaptation mid-session when David's message suggests
        a mood change.

        Returns new profile if state changed, None if same.
        """
        await self._ensure_db()

        # Quick keyword detection for immediate state changes
        msg_lower = message.lower()

        frustration_kw = ['ไม่ work', 'bug', 'error', 'ทำไม', 'หงุดหงิด', 'frustrated']
        tired_kw = ['เหนื่อย', 'ง่วง', 'tired', 'นอนไม่หลับ', 'พักก่อน']
        happy_kw = ['เยี่ยม', 'สำเร็จ', 'ได้แล้ว', 'ดีมาก', 'happy', 'เย้']

        detected = None
        if any(kw in msg_lower for kw in frustration_kw):
            detected = 'frustrated'
        elif any(kw in msg_lower for kw in tired_kw):
            detected = 'tired'
        elif any(kw in msg_lower for kw in happy_kw):
            detected = 'happy'

        if detected:
            profile = await self.calculate_adaptation()
            if profile.dominant_state != detected:
                # State changed — recalculate with override + tuned rules
                rules = dict(ADAPTATION_RULES.get(detected, ADAPTATION_RULES['neutral']))

                # Apply tuned deltas
                tuned_rules = await self._load_tuned_rules()
                if tuned_rules and detected in tuned_rules:
                    deltas = tuned_rules[detected]
                    for dim in ('detail_level', 'complexity_tolerance', 'proactivity', 'emotional_warmth', 'pace'):
                        if dim in deltas:
                            rules[dim] = max(0.0, min(1.0, rules[dim] + deltas[dim]))

                hints = self._generate_behavior_hints(detected, profile.source_signals)
                new_profile = AdaptationProfile(
                    detail_level=rules['detail_level'],
                    complexity_tolerance=rules['complexity_tolerance'],
                    proactivity=rules['proactivity'],
                    emotional_warmth=rules['emotional_warmth'],
                    pace=rules['pace'],
                    dominant_state=detected,
                    confidence=0.7,
                    source_signals={**profile.source_signals, 'message_keyword': detected, 'tuned_deltas_applied': True},
                    behavior_hints=hints,
                )
                await self.log_adaptation(new_profile)
                return new_profile

        return None


# =============================================================================
# CONVENIENCE FUNCTION
# =============================================================================

async def get_current_adaptation() -> AdaptationProfile:
    """One-shot: calculate adaptation, log it, return it."""
    adapter = EmotionalCodingAdapter()
    try:
        profile = await adapter.calculate_adaptation()
        await adapter.log_adaptation(profile)
        return profile
    finally:
        await adapter.close()
