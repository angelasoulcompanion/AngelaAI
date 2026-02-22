"""
Predictive Companionship Service

Feature ที่ยังไม่มีใครทำ: AI คาดการณ์ความต้องการจาก 6,195+ conversations
- Mine patterns จาก historical data
- สร้าง daily briefing ที่บอกว่าวันนี้ที่รักน่าจะทำอะไร
- Proactive actions เตรียมไว้ล่วงหน้า

Created: 2026-02-07
By: น้อง Angela 💜
"""

import hashlib
import json
import logging
from dataclasses import dataclass, field, asdict
from datetime import date, datetime, timedelta
from typing import Dict, List, Optional, Any
from uuid import UUID, uuid4

from angela_core.database import AngelaDatabase
from angela_core.utils.timezone import now_bangkok, today_bangkok
from angela_core.services.reasoning_chain_service import (
    capture_reasoning, ReasoningChain, ReasoningStep,
)

logger = logging.getLogger(__name__)

# Day-of-week names in Thai (0=Mon, 6=Sun)
DOW_THAI = ['จันทร์', 'อังคาร', 'พุธ', 'พฤหัสบดี', 'ศุกร์', 'เสาร์', 'อาทิตย์']

# Time windows
TIME_WINDOWS = {
    'morning': (5, 12),
    'afternoon': (12, 17),
    'evening': (17, 21),
    'night': (21, 5),
}


def _hour_to_window(hour: int) -> str:
    if 5 <= hour < 12:
        return 'morning'
    elif 12 <= hour < 17:
        return 'afternoon'
    elif 17 <= hour < 21:
        return 'evening'
    else:
        return 'night'


@dataclass
class CompanionPrediction:
    prediction_id: UUID
    category: str         # time/topic/emotion/activity/need
    prediction: str       # what we predict (Thai)
    time_window: str      # morning/afternoon/evening/night
    confidence: float
    evidence: List[Dict] = field(default_factory=list)
    proactive_action: Optional[str] = None
    priority: int = 3     # 1-5

    def to_dict(self) -> Dict:
        return {
            'prediction_id': str(self.prediction_id),
            'category': self.category,
            'prediction': self.prediction,
            'time_window': self.time_window,
            'confidence': self.confidence,
            'evidence': self.evidence,
            'proactive_action': self.proactive_action,
            'priority': self.priority,
        }


@dataclass
class DailyBriefing:
    briefing_id: UUID
    date: date
    predictions: List[CompanionPrediction]
    overall_confidence: float
    day_outlook: str        # Thai summary
    prepared_actions: List[str] = field(default_factory=list)

    def to_dict(self) -> Dict:
        return {
            'briefing_id': str(self.briefing_id),
            'date': self.date.isoformat(),
            'predictions': [p.to_dict() for p in self.predictions],
            'overall_confidence': self.overall_confidence,
            'day_outlook': self.day_outlook,
            'prepared_actions': self.prepared_actions,
        }


class PredictiveCompanionService:
    """
    Mine patterns จาก conversation history และสร้าง daily predictions.

    5 Pattern Miners:
    1. Time patterns — typical activity at each hour/day
    2. Emotional cycles — mood patterns over time
    3. Topic sequences — what topic follows what
    4. Activity patterns — keyword-based activity detection
    5. Session duration — how long David typically works
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
    # PATTERN MINERS
    # =========================================================================

    async def mine_time_patterns(self, lookback_days: int = 30) -> List[Dict]:
        """Mine: What does David typically do at each hour/day-of-week?"""
        await self._ensure_db()
        rows = await self.db.fetch('''
            WITH hourly AS (
                SELECT
                    EXTRACT(DOW FROM created_at AT TIME ZONE 'Asia/Bangkok')::int AS dow,
                    EXTRACT(HOUR FROM created_at AT TIME ZONE 'Asia/Bangkok')::int AS hour,
                    topic,
                    emotion_detected,
                    COUNT(*) AS cnt
                FROM conversations
                WHERE speaker = 'david'
                  AND created_at > NOW() - INTERVAL '1 day' * $1
                  AND topic IS NOT NULL
                GROUP BY dow, hour, topic, emotion_detected
            )
            SELECT dow, hour, topic, emotion_detected, cnt,
                   ROW_NUMBER() OVER (PARTITION BY dow, hour ORDER BY cnt DESC) AS rn
            FROM hourly
        ''', lookback_days)

        patterns = []
        for r in rows:
            if r['rn'] <= 2:  # top 2 per slot
                patterns.append({
                    'dow': r['dow'],
                    'hour': r['hour'],
                    'topic': r['topic'],
                    'emotion': r['emotion_detected'],
                    'count': r['cnt'],
                })
        return patterns

    async def mine_emotional_cycles(self, lookback_days: int = 30) -> List[Dict]:
        """Mine: emotional patterns by time of day."""
        await self._ensure_db()
        rows = await self.db.fetch('''
            SELECT
                EXTRACT(HOUR FROM created_at)::int AS hour,
                ROUND(AVG(happiness)::numeric, 2) AS avg_happiness,
                ROUND(AVG(anxiety)::numeric, 2) AS avg_anxiety,
                ROUND(AVG(motivation)::numeric, 2) AS avg_motivation,
                ROUND(AVG(energy_level)::numeric, 2) AS avg_energy,
                COUNT(*) AS sample_count
            FROM emotional_states es
            LEFT JOIN david_health_state dhs
                ON dhs.is_current = TRUE
            WHERE es.created_at > NOW() - INTERVAL '1 day' * $1
            GROUP BY hour
            HAVING COUNT(*) >= 2
            ORDER BY hour
        ''', lookback_days)

        return [dict(r) for r in rows]

    async def mine_topic_sequences(self, lookback_days: int = 30) -> List[Dict]:
        """Mine: What topic typically follows another topic?"""
        await self._ensure_db()
        rows = await self.db.fetch('''
            WITH ordered AS (
                SELECT topic,
                       LEAD(topic) OVER (ORDER BY created_at) AS next_topic,
                       created_at
                FROM conversations
                WHERE speaker = 'david'
                  AND topic IS NOT NULL
                  AND created_at > NOW() - INTERVAL '1 day' * $1
            )
            SELECT topic, next_topic, COUNT(*) AS cnt
            FROM ordered
            WHERE next_topic IS NOT NULL
              AND topic != next_topic
            GROUP BY topic, next_topic
            HAVING COUNT(*) >= 2
            ORDER BY cnt DESC
            LIMIT 20
        ''', lookback_days)

        return [dict(r) for r in rows]

    async def mine_activity_patterns(self, lookback_days: int = 30) -> List[Dict]:
        """Mine: keyword-based activity detection from messages."""
        await self._ensure_db()
        rows = await self.db.fetch('''
            SELECT
                EXTRACT(DOW FROM created_at AT TIME ZONE 'Asia/Bangkok')::int AS dow,
                CASE
                    WHEN EXTRACT(HOUR FROM created_at AT TIME ZONE 'Asia/Bangkok') BETWEEN 5 AND 11 THEN 'morning'
                    WHEN EXTRACT(HOUR FROM created_at AT TIME ZONE 'Asia/Bangkok') BETWEEN 12 AND 16 THEN 'afternoon'
                    WHEN EXTRACT(HOUR FROM created_at AT TIME ZONE 'Asia/Bangkok') BETWEEN 17 AND 20 THEN 'evening'
                    ELSE 'night'
                END AS time_window,
                CASE
                    WHEN message_text ILIKE '%%code%%' OR message_text ILIKE '%%bug%%'
                         OR message_text ILIKE '%%function%%' OR message_text ILIKE '%%fix%%' THEN 'coding'
                    WHEN message_text ILIKE '%%เพลง%%' OR message_text ILIKE '%%song%%'
                         OR message_text ILIKE '%%youtube%%' THEN 'music'
                    WHEN message_text ILIKE '%%email%%' OR message_text ILIKE '%%ข่าว%%'
                         OR message_text ILIKE '%%news%%' THEN 'admin'
                    WHEN message_text ILIKE '%%คิดถึง%%' OR message_text ILIKE '%%รัก%%'
                         OR message_text ILIKE '%%miss%%' THEN 'personal'
                    ELSE 'general'
                END AS activity,
                COUNT(*) AS cnt
            FROM conversations
            WHERE speaker = 'david'
              AND created_at > NOW() - INTERVAL '1 day' * $1
            GROUP BY dow, time_window, activity
            HAVING COUNT(*) >= 3
            ORDER BY dow, time_window, cnt DESC
        ''', lookback_days)

        return [dict(r) for r in rows]

    async def mine_note_reminders(self) -> List[Dict]:
        """Mine: pinned notes + notes with deadline/meeting/reminder keywords."""
        await self._ensure_db()
        rows = await self.db.fetch('''
            SELECT note_id, title, is_pinned, labels, updated_at
            FROM david_notes
            WHERE is_trashed = FALSE
              AND (
                  is_pinned = TRUE
                  OR title ILIKE '%%deadline%%'
                  OR title ILIKE '%%meeting%%'
                  OR title ILIKE '%%reminder%%'
                  OR title ILIKE '%%ประชุม%%'
                  OR title ILIKE '%%นัด%%'
                  OR title ILIKE '%%กำหนด%%'
                  OR content ILIKE '%%deadline%%'
                  OR content ILIKE '%%meeting%%'
                  OR content ILIKE '%%reminder%%'
              )
            ORDER BY is_pinned DESC, updated_at DESC
            LIMIT 5
        ''')
        return [dict(r) for r in rows]

    async def mine_session_duration_patterns(self, lookback_days: int = 30) -> List[Dict]:
        """Mine: how long does David typically work in a session?"""
        await self._ensure_db()
        rows = await self.db.fetch('''
            WITH daily_sessions AS (
                SELECT
                    (created_at AT TIME ZONE 'Asia/Bangkok')::date AS session_date,
                    EXTRACT(DOW FROM created_at AT TIME ZONE 'Asia/Bangkok')::int AS dow,
                    MIN(created_at) AS first_msg,
                    MAX(created_at) AS last_msg,
                    COUNT(*) AS msg_count
                FROM conversations
                WHERE speaker = 'david'
                  AND created_at > NOW() - INTERVAL '1 day' * $1
                GROUP BY session_date, dow
                HAVING COUNT(*) >= 3
            )
            SELECT
                dow,
                ROUND(AVG(EXTRACT(EPOCH FROM last_msg - first_msg) / 3600)::numeric, 1) AS avg_hours,
                ROUND(AVG(msg_count)::numeric, 0) AS avg_messages,
                COUNT(*) AS session_count
            FROM daily_sessions
            GROUP BY dow
            ORDER BY dow
        ''', lookback_days)

        return [dict(r) for r in rows]

    # =========================================================================
    # PREDICTION GENERATION
    # =========================================================================

    async def generate_daily_briefing(self) -> DailyBriefing:
        """
        Generate today's companion briefing by combining all pattern miners.
        """
        await self._ensure_db()

        import asyncio
        time_patterns, emotional_cycles, topic_sequences, activity_patterns, session_patterns, note_reminders = await asyncio.gather(
            self.mine_time_patterns(),
            self.mine_emotional_cycles(),
            self.mine_topic_sequences(),
            self.mine_activity_patterns(),
            self.mine_session_duration_patterns(),
            self.mine_note_reminders(),
        )

        now = now_bangkok()
        today_dow = now.weekday()  # 0=Mon, 6=Sun
        # PostgreSQL DOW: 0=Sun, 1=Mon ... 6=Sat
        pg_dow = (today_dow + 1) % 7

        predictions: List[CompanionPrediction] = []

        # --- Time-based predictions ---
        for window_name, (start_h, end_h) in TIME_WINDOWS.items():
            matching = [p for p in time_patterns if p['dow'] == pg_dow and start_h <= p['hour'] < end_h]
            if matching:
                top = max(matching, key=lambda x: x['count'])
                confidence = min(0.9, top['count'] / 20)
                pred = CompanionPrediction(
                    prediction_id=uuid4(),
                    category='time',
                    prediction=f'ช่วง{window_name} ที่รักมักคุยเรื่อง {top["topic"]}',
                    time_window=window_name,
                    confidence=confidence,
                    evidence=[{'source': 'time_pattern', 'count': top['count'], 'topic': top['topic']}],
                    proactive_action=f'เตรียม context เรื่อง {top["topic"]}' if confidence >= 0.7 else None,
                    priority=2,
                )
                predictions.append(pred)

        # --- Emotional predictions ---
        hour_now = now.hour
        matching_emotions = [e for e in emotional_cycles if e['hour'] == hour_now]
        if matching_emotions:
            e = matching_emotions[0]
            mood = 'ดี' if (e.get('avg_happiness') or 0) > 0.6 else 'เครียดนิดหน่อย' if (e.get('avg_anxiety') or 0) > 0.5 else 'ปกติ'
            confidence = min(0.85, (e.get('sample_count') or 1) / 15)
            predictions.append(CompanionPrediction(
                prediction_id=uuid4(),
                category='emotion',
                prediction=f'ตอนนี้ ({hour_now}:00) ที่รักมักอารมณ์{mood}',
                time_window=_hour_to_window(hour_now),
                confidence=confidence,
                evidence=[{'source': 'emotional_cycle', 'hour': hour_now, 'happiness': float(e.get('avg_happiness') or 0)}],
                priority=3,
            ))

        # --- Topic sequence predictions ---
        # Find what topic David discussed recently and predict next
        last_topic_row = await self.db.fetchrow('''
            SELECT topic FROM conversations
            WHERE speaker = 'david' AND topic IS NOT NULL
            ORDER BY created_at DESC LIMIT 1
        ''')
        if last_topic_row:
            last_topic = last_topic_row['topic']
            next_topics = [s for s in topic_sequences if s['topic'] == last_topic]
            if next_topics:
                top_next = next_topics[0]
                confidence = min(0.8, top_next['cnt'] / 10)
                predictions.append(CompanionPrediction(
                    prediction_id=uuid4(),
                    category='topic',
                    prediction=f'หลังจากเรื่อง "{last_topic}" ที่รักมักคุยเรื่อง "{top_next["next_topic"]}" ต่อ',
                    time_window=_hour_to_window(hour_now),
                    confidence=confidence,
                    evidence=[{'source': 'topic_sequence', 'from': last_topic, 'to': top_next['next_topic'], 'count': top_next['cnt']}],
                    proactive_action=f'เตรียมข้อมูลเรื่อง {top_next["next_topic"]}' if confidence >= 0.7 else None,
                    priority=2,
                ))

        # --- Activity predictions ---
        for window_name in TIME_WINDOWS:
            matching = [a for a in activity_patterns if a['dow'] == pg_dow and a['time_window'] == window_name and a['activity'] != 'general']
            if matching:
                top_act = max(matching, key=lambda x: x['cnt'])
                confidence = min(0.85, top_act['cnt'] / 15)
                activity_thai = {
                    'coding': 'เขียนโค้ด',
                    'music': 'ฟังเพลง/ส่งเพลง',
                    'admin': 'ดู email/ข่าว',
                    'personal': 'คุยเรื่องส่วนตัว',
                }.get(top_act['activity'], top_act['activity'])
                predictions.append(CompanionPrediction(
                    prediction_id=uuid4(),
                    category='activity',
                    prediction=f'วัน{DOW_THAI[today_dow]} ช่วง{window_name} ที่รักมัก{activity_thai}',
                    time_window=window_name,
                    confidence=confidence,
                    evidence=[{'source': 'activity_pattern', 'activity': top_act['activity'], 'count': top_act['cnt']}],
                    priority=3,
                ))

        # --- Session duration prediction ---
        matching_session = [s for s in session_patterns if s['dow'] == pg_dow]
        if matching_session:
            s = matching_session[0]
            avg_hours = float(s.get('avg_hours') or 0)
            if avg_hours > 0:
                predictions.append(CompanionPrediction(
                    prediction_id=uuid4(),
                    category='need',
                    prediction=f'วัน{DOW_THAI[today_dow]} ที่รักมักทำงาน ~{avg_hours:.1f} ชม. ({int(float(s.get("avg_messages") or 0))} msgs)',
                    time_window='morning',
                    confidence=min(0.8, (s.get('session_count') or 1) / 5),
                    evidence=[{'source': 'session_duration', 'avg_hours': avg_hours}],
                    proactive_action=f'เตือนให้พักหลัง {avg_hours:.0f} ชม.' if avg_hours > 2 else None,
                    priority=4,
                ))

        # --- Note reminder predictions ---
        for note in note_reminders:
            title = note.get('title') or '(untitled)'
            pinned_tag = ' — is_pinned' if note.get('is_pinned') else ''
            predictions.append(CompanionPrediction(
                prediction_id=uuid4(),
                category='note_reminder',
                prediction=f'ที่รักมี note "{title}"{pinned_tag}',
                time_window='morning',
                confidence=0.7 if note.get('is_pinned') else 0.5,
                evidence=[{'source': 'david_notes', 'note_id': str(note.get('note_id', '')), 'is_pinned': note.get('is_pinned', False)}],
                priority=3 if note.get('is_pinned') else 2,
            ))

        # Sort by priority then confidence
        predictions.sort(key=lambda p: (p.priority, -p.confidence))

        # Overall confidence
        overall_conf = sum(p.confidence for p in predictions) / max(len(predictions), 1)

        # Day outlook
        day_name = DOW_THAI[today_dow]
        top_activities = [p.prediction for p in predictions if p.category == 'activity'][:2]
        outlook = f'วัน{day_name} — '
        if top_activities:
            outlook += ' | '.join(top_activities)
        else:
            outlook += 'ยังไม่มี pattern ชัดเจน จะเรียนรู้เพิ่มค่ะ'

        # Prepared actions
        prepared = [p.proactive_action for p in predictions if p.proactive_action]

        briefing = DailyBriefing(
            briefing_id=uuid4(),
            date=today_bangkok(),
            predictions=predictions,
            overall_confidence=overall_conf,
            day_outlook=outlook,
            prepared_actions=prepared,
        )

        # Save to database
        await self.save_briefing(briefing)

        # Cache patterns
        await self._cache_patterns(
            time_patterns, emotional_cycles, topic_sequences,
            activity_patterns, session_patterns,
        )

        # Capture reasoning chain (fire-and-forget)
        capture_reasoning(ReasoningChain(
            service_name='predict',
            decision_type='daily_briefing',
            input_signals={
                'dow': pg_dow, 'day_name': day_name, 'hour': hour_now,
                'pattern_counts': {
                    'time': len(time_patterns), 'emotion': len(emotional_cycles),
                    'topic_seq': len(topic_sequences), 'activity': len(activity_patterns),
                    'session': len(session_patterns), 'notes': len(note_reminders),
                },
            },
            steps=[
                ReasoningStep('mine_patterns', 'parallel mine 6 pattern types from 30-day history',
                              f'time={len(time_patterns)}, emotion={len(emotional_cycles)}, topic={len(topic_sequences)}, activity={len(activity_patterns)}',
                              'pattern data collected'),
                ReasoningStep('generate_predictions', 'combine patterns into predictions per time window',
                              f'predictions_generated={len(predictions)}',
                              f'outlook: {outlook[:80]}'),
                ReasoningStep('prepare_actions', 'extract proactive actions from high-confidence predictions',
                              f'prepared_actions={len(prepared)}',
                              f'overall_confidence={overall_conf:.2f}'),
            ],
            output_decision={
                'prediction_count': len(predictions),
                'overall_confidence': overall_conf,
                'day_outlook': outlook,
                'prepared_actions': prepared,
            },
            confidence=overall_conf,
        ))

        return briefing

    # =========================================================================
    # PERSISTENCE
    # =========================================================================

    async def save_briefing(self, briefing: DailyBriefing) -> None:
        """Save/upsert briefing for today."""
        await self._ensure_db()
        predictions_json = json.dumps([p.to_dict() for p in briefing.predictions])
        await self.db.execute('''
            INSERT INTO daily_companion_briefings
                (briefing_id, briefing_date, predictions, overall_confidence,
                 day_outlook, prepared_actions)
            VALUES ($1, $2, $3, $4, $5, $6)
            ON CONFLICT (briefing_date) DO UPDATE SET
                predictions = EXCLUDED.predictions,
                overall_confidence = EXCLUDED.overall_confidence,
                day_outlook = EXCLUDED.day_outlook,
                prepared_actions = EXCLUDED.prepared_actions,
                created_at = NOW()
        ''',
            briefing.briefing_id,
            briefing.date,
            predictions_json,
            briefing.overall_confidence,
            briefing.day_outlook,
            briefing.prepared_actions,
        )

    async def load_today_briefing(self) -> Optional[DailyBriefing]:
        """Load today's briefing from database."""
        await self._ensure_db()
        row = await self.db.fetchrow('''
            SELECT briefing_id, briefing_date, predictions, overall_confidence,
                   day_outlook, prepared_actions
            FROM daily_companion_briefings
            WHERE briefing_date = (CURRENT_TIMESTAMP AT TIME ZONE 'Asia/Bangkok')::date
        ''')
        if not row:
            return None

        predictions_data = row['predictions']
        if isinstance(predictions_data, str):
            predictions_data = json.loads(predictions_data)

        predictions = []
        for p in predictions_data:
            predictions.append(CompanionPrediction(
                prediction_id=UUID(p['prediction_id']),
                category=p['category'],
                prediction=p['prediction'],
                time_window=p['time_window'],
                confidence=p['confidence'],
                evidence=p.get('evidence', []),
                proactive_action=p.get('proactive_action'),
                priority=p.get('priority', 3),
            ))

        return DailyBriefing(
            briefing_id=row['briefing_id'],
            date=row['briefing_date'],
            predictions=predictions,
            overall_confidence=row['overall_confidence'],
            day_outlook=row['day_outlook'],
            prepared_actions=row['prepared_actions'] or [],
        )

    async def _cache_patterns(
        self,
        time_patterns: List[Dict],
        emotional_cycles: List[Dict],
        topic_sequences: List[Dict],
        activity_patterns: List[Dict],
        session_patterns: List[Dict],
    ) -> None:
        """Cache mined patterns to companion_patterns table."""
        pattern_groups = [
            ('time', time_patterns),
            ('emotion', emotional_cycles),
            ('topic_sequence', topic_sequences),
            ('activity', activity_patterns),
            ('session_duration', session_patterns),
        ]

        for category, patterns in pattern_groups:
            if not patterns:
                continue
            data_json = json.dumps(patterns, default=str)
            pattern_hash = hashlib.sha256(data_json.encode()).hexdigest()[:16]

            # Upsert: update if same hash exists, insert otherwise
            existing = await self.db.fetchrow('''
                SELECT pattern_id FROM companion_patterns
                WHERE pattern_category = $1 AND pattern_hash = $2
            ''', category, pattern_hash)

            if existing:
                await self.db.execute('''
                    UPDATE companion_patterns
                    SET observation_count = observation_count + 1,
                        last_observed = NOW()
                    WHERE pattern_id = $1
                ''', existing['pattern_id'])
            else:
                # Deactivate old patterns of same category
                await self.db.execute('''
                    UPDATE companion_patterns
                    SET is_active = FALSE
                    WHERE pattern_category = $1 AND is_active = TRUE
                ''', category)

                confidence = min(0.9, len(patterns) / 20)
                await self.db.execute('''
                    INSERT INTO companion_patterns
                        (pattern_category, pattern_data, confidence, pattern_hash)
                    VALUES ($1, $2, $3, $4)
                ''', category, data_json, confidence, pattern_hash)

    # =========================================================================
    # VERIFICATION
    # =========================================================================

    async def verify_predictions(self, briefing_date: Optional[date] = None) -> Dict[str, Any]:
        """
        Verify yesterday's predictions against actual data.
        """
        await self._ensure_db()
        target_date = briefing_date or (today_bangkok() - timedelta(days=1))

        row = await self.db.fetchrow('''
            SELECT briefing_id, predictions, overall_confidence
            FROM daily_companion_briefings
            WHERE briefing_date = $1
        ''', target_date)

        if not row:
            return {'verified': False, 'reason': 'No briefing found for date'}

        predictions = row['predictions']
        if isinstance(predictions, str):
            predictions = json.loads(predictions)

        # Get actual data for that day
        actual_topics = await self.db.fetch('''
            SELECT DISTINCT topic FROM conversations
            WHERE speaker = 'david' AND topic IS NOT NULL
              AND (created_at AT TIME ZONE 'Asia/Bangkok')::date = $1
        ''', target_date)
        actual_topic_set = {r['topic'] for r in actual_topics}

        # Verify emotion predictions against actual emotional_states
        actual_emotions = await self.db.fetch('''
            SELECT DISTINCT emotion_detected FROM conversations
            WHERE speaker = 'david' AND emotion_detected IS NOT NULL
              AND (created_at AT TIME ZONE 'Asia/Bangkok')::date = $1
        ''', target_date)
        actual_emotion_set = {r['emotion_detected'].lower() for r in actual_emotions}

        # Accuracy: check all verifiable categories
        correct = 0
        total = 0
        for pred in predictions:
            category = pred.get('category')
            if category in ('time', 'topic'):
                total += 1
                evidence = pred.get('evidence', [{}])
                predicted_topic = evidence[0].get('topic') or evidence[0].get('to') if evidence else None
                if predicted_topic and predicted_topic in actual_topic_set:
                    correct += 1
            elif category == 'emotion':
                total += 1
                predicted = pred.get('prediction', '').lower()
                if any(e in predicted for e in actual_emotion_set):
                    correct += 1
            elif category == 'activity':
                total += 1
                predicted = pred.get('prediction', '').lower()
                if any(t.lower() in predicted or predicted in t.lower() for t in actual_topic_set):
                    correct += 1

        accuracy = correct / max(total, 1)

        verification_data = {
            'actual_topics': list(actual_topic_set),
            'predictions_checked': total,
            'correct': correct,
            'accuracy': accuracy,
        }

        await self.db.execute('''
            UPDATE daily_companion_briefings
            SET verified = TRUE, accuracy_score = $1,
                verification_data = $2, verified_at = NOW()
            WHERE briefing_id = $3
        ''', accuracy, json.dumps(verification_data), row['briefing_id'])

        return {'verified': True, 'accuracy': accuracy, 'data': verification_data}

    async def get_accuracy_report(self, days: int = 30) -> Dict[str, Any]:
        """Overall accuracy stats."""
        await self._ensure_db()
        row = await self.db.fetchrow('''
            SELECT
                COUNT(*) AS total_briefings,
                COUNT(*) FILTER (WHERE verified) AS verified_count,
                ROUND(AVG(accuracy_score) FILTER (WHERE verified)::numeric, 2) AS avg_accuracy,
                MAX(accuracy_score) FILTER (WHERE verified) AS best_accuracy
            FROM daily_companion_briefings
            WHERE briefing_date > (CURRENT_TIMESTAMP AT TIME ZONE 'Asia/Bangkok')::date - $1
        ''', days)

        return dict(row) if row else {}

    # =========================================================================
    # REAL-TIME PREDICTIONS
    # =========================================================================

    async def get_predictions_for_now(self) -> List[CompanionPrediction]:
        """Get predictions relevant to the current time window."""
        briefing = await self.load_today_briefing()
        if not briefing:
            return []

        current_window = _hour_to_window(now_bangkok().hour)
        return [p for p in briefing.predictions if p.time_window == current_window]


# =============================================================================
# CONVENIENCE FUNCTION
# =============================================================================

async def get_daily_briefing() -> Optional[DailyBriefing]:
    """One-shot: load or generate today's briefing."""
    svc = PredictiveCompanionService()
    try:
        briefing = await svc.load_today_briefing()
        if not briefing:
            briefing = await svc.generate_daily_briefing()
        return briefing
    finally:
        await svc.close()
