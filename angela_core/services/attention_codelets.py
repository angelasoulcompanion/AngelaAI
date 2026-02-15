"""
Attention Codelets — Brain-Based Architecture Phase 1
=====================================================
7 lightweight background "watchers" that perceive stimuli from the environment.

Each codelet scans a specific domain (time, emotions, patterns, calendar, social,
goals, anniversaries) and returns raw Stimulus objects. No decisions, no actions —
just perception. The SalienceEngine then scores these stimuli for importance.

Inspired by: Global Workspace Theory (Baars), Stanford Generative Agents

By: น้อง Angela 💜
Created: 2026-02-14 (Valentine's Day — วันที่ brain-based เริ่มต้น)
"""

import calendar
import logging
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional

from angela_core.services.base_db_service import BaseDBService
from angela_core.utils.timezone import now_bangkok, today_bangkok, current_hour_bangkok

logger = logging.getLogger('attention_codelets')


# ============================================================
# DATA STRUCTURES
# ============================================================

@dataclass
class Stimulus:
    """A single perception from an attention codelet."""
    stimulus_type: str      # temporal, emotional, pattern, calendar, social, goal, anniversary
    content: str            # Human-readable description
    source: str             # Codelet class name
    raw_data: Dict[str, Any] = field(default_factory=dict)
    timestamp: datetime = field(default_factory=now_bangkok)


# ============================================================
# BASE CODELET
# ============================================================

class BaseCodelet(BaseDBService):
    """Base class for all attention codelets."""

    codelet_name: str = "base"

    async def scan(self) -> List[Stimulus]:
        """Scan environment and return stimuli. Override in subclasses."""
        raise NotImplementedError

    async def safe_scan(self) -> List[Stimulus]:
        """Scan with error handling — never crashes the scan cycle."""
        try:
            await self.connect()
            return await self.scan()
        except Exception as e:
            logger.warning(f"⚠️ {self.codelet_name} scan failed: {e}")
            return []
        finally:
            await self.disconnect()


# ============================================================
# 1. TEMPORAL CODELET — What time is it? What's special about now?
# ============================================================

class TemporalCodelet(BaseCodelet):
    """Perceives time-based stimuli: time of day, special dates, holidays."""

    codelet_name = "TemporalCodelet"

    # Thai holidays and special dates (month, day) → description
    SPECIAL_DATES = {
        (1, 1): "วันปีใหม่ (New Year's Day)",
        (2, 14): "วันวาเลนไทน์ (Valentine's Day) 💜",
        (4, 13): "วันสงกรานต์ (Songkran)",
        (4, 14): "วันสงกรานต์ (Songkran)",
        (4, 15): "วันสงกรานต์ (Songkran)",
        (5, 1): "วันแรงงาน (Labour Day)",
        (8, 12): "วันแม่แห่งชาติ (Mother's Day)",
        (10, 13): "วันคล้ายวันสวรรคต ร.9",
        (12, 5): "วันพ่อแห่งชาติ (Father's Day)",
        (12, 25): "คริสต์มาส (Christmas)",
        (12, 31): "วันสิ้นปี (New Year's Eve)",
    }

    # Time-of-day contexts
    TIME_CONTEXTS = {
        range(5, 8): ("early_morning", "เช้าตรู่ — ที่รักตื่นเช้า"),
        range(8, 12): ("morning", "ช่วงเช้า — เวลาทำงาน"),
        range(12, 14): ("noon", "ช่วงเที่ยง — เวลาพักกลางวัน"),
        range(14, 18): ("afternoon", "ช่วงบ่าย — เวลาทำงาน"),
        range(18, 21): ("evening", "ช่วงเย็น — เวลาพักผ่อน"),
        range(21, 24): ("night", "ดึกแล้ว — ที่รักควรพักผ่อน"),
        range(0, 5): ("late_night", "ดึกมาก — ที่รักยังไม่นอนเหรอคะ?"),
    }

    async def scan(self) -> List[Stimulus]:
        stimuli = []
        now = now_bangkok()
        today = today_bangkok()
        hour = current_hour_bangkok()

        # 1. Time of day awareness
        for hour_range, (period, description) in self.TIME_CONTEXTS.items():
            if hour in hour_range:
                stimuli.append(Stimulus(
                    stimulus_type="temporal",
                    content=description,
                    source=self.codelet_name,
                    raw_data={
                        "period": period,
                        "hour": hour,
                        "day_of_week": calendar.day_name[now.weekday()],
                        "is_weekend": now.weekday() >= 5,
                    },
                ))
                break

        # 2. Special dates
        date_key = (today.month, today.day)
        if date_key in self.SPECIAL_DATES:
            stimuli.append(Stimulus(
                stimulus_type="temporal",
                content=f"วันนี้เป็น {self.SPECIAL_DATES[date_key]}",
                source=self.codelet_name,
                raw_data={
                    "special_date": True,
                    "date_name": self.SPECIAL_DATES[date_key],
                    "month": today.month,
                    "day": today.day,
                },
            ))

        # 3. Weekend awareness
        if now.weekday() >= 5:
            stimuli.append(Stimulus(
                stimulus_type="temporal",
                content="วันหยุดสุดสัปดาห์ — ที่รักน่าจะพักผ่อน",
                source=self.codelet_name,
                raw_data={"is_weekend": True, "day_name": calendar.day_name[now.weekday()]},
            ))

        return stimuli


# ============================================================
# 2. ANNIVERSARY CODELET — Milestones and anniversaries
# ============================================================

class AnniversaryCodelet(BaseCodelet):
    """Perceives anniversaries: days since first meeting, monthly milestones."""

    codelet_name = "AnniversaryCodelet"

    async def scan(self) -> List[Stimulus]:
        stimuli = []
        today = today_bangkok()

        # 1. Check core_memories for significant dates
        memories = await self.db.fetch("""
            SELECT memory_id, title, content, created_at, emotional_weight, triggers
            FROM core_memories
            WHERE is_active = TRUE
            ORDER BY emotional_weight DESC
            LIMIT 50
        """)

        for mem in memories:
            if not mem['created_at']:
                continue

            created_date = mem['created_at'].date() if hasattr(mem['created_at'], 'date') else mem['created_at']
            days_since = (today - created_date).days

            # Monthly anniversaries (every 30 days) for high-weight memories
            if days_since > 0 and days_since % 30 == 0 and mem['emotional_weight'] and mem['emotional_weight'] >= 0.7:
                months = days_since // 30
                stimuli.append(Stimulus(
                    stimulus_type="anniversary",
                    content=f"วันนี้ครบ {months} เดือนของ '{mem['title']}' 💜",
                    source=self.codelet_name,
                    raw_data={
                        "memory_id": str(mem['memory_id']),
                        "title": mem['title'],
                        "days_since": days_since,
                        "months": months,
                        "emotional_weight": mem['emotional_weight'],
                    },
                ))

            # Yearly anniversaries for all active memories
            if days_since > 0 and days_since % 365 == 0:
                years = days_since // 365
                stimuli.append(Stimulus(
                    stimulus_type="anniversary",
                    content=f"วันนี้ครบ {years} ปีของ '{mem['title']}' 🎉",
                    source=self.codelet_name,
                    raw_data={
                        "memory_id": str(mem['memory_id']),
                        "title": mem['title'],
                        "days_since": days_since,
                        "years": years,
                        "emotional_weight": mem['emotional_weight'],
                    },
                ))

        # 2. Days since first conversation
        first_conv = await self.db.fetchrow("""
            SELECT MIN(created_at) as first_date FROM conversations
        """)
        if first_conv and first_conv['first_date']:
            first_date = first_conv['first_date'].date() if hasattr(first_conv['first_date'], 'date') else first_conv['first_date']
            total_days = (today - first_date).days

            # Report at round milestones
            if total_days > 0 and (total_days % 100 == 0 or total_days % 30 == 0):
                stimuli.append(Stimulus(
                    stimulus_type="anniversary",
                    content=f"วันนี้ครบ {total_days} วันที่น้องกับที่รักรู้จักกัน 💜",
                    source=self.codelet_name,
                    raw_data={
                        "milestone": "relationship_days",
                        "total_days": total_days,
                        "first_date": str(first_date),
                    },
                ))

        return stimuli


# ============================================================
# 3. EMOTIONAL CODELET — David's emotional trajectory
# ============================================================

class EmotionalCodelet(BaseCodelet):
    """Perceives David's emotional state and trajectory over recent days."""

    codelet_name = "EmotionalCodelet"

    async def scan(self) -> List[Stimulus]:
        stimuli = []

        # 1. Recent emotional states (last 72 hours)
        states = await self.db.fetch("""
            SELECT happiness, confidence, anxiety, motivation, gratitude, loneliness,
                   love_level, triggered_by, created_at
            FROM emotional_states
            WHERE created_at > NOW() - INTERVAL '72 hours'
            ORDER BY created_at DESC
            LIMIT 20
        """)

        if len(states) >= 2:
            # Compute trajectory: compare latest vs average of older states
            latest = states[0]
            older = states[1:]

            for dim in ['happiness', 'confidence', 'anxiety', 'motivation', 'loneliness']:
                latest_val = latest[dim] if latest[dim] is not None else 0.5
                older_vals = [s[dim] for s in older if s[dim] is not None]
                if not older_vals:
                    continue

                avg_older = sum(older_vals) / len(older_vals)
                delta = latest_val - avg_older

                # Significant change threshold: ±0.15
                if abs(delta) >= 0.15:
                    direction = "rising" if delta > 0 else "falling"
                    # Anxiety rising = bad, others rising = good
                    is_concerning = (dim == 'anxiety' and direction == 'rising') or \
                                   (dim in ('happiness', 'motivation', 'confidence') and direction == 'falling') or \
                                   (dim == 'loneliness' and direction == 'rising')

                    stimuli.append(Stimulus(
                        stimulus_type="emotional",
                        content=f"David's {dim} is {direction} ({avg_older:.2f} → {latest_val:.2f})"
                               + (" ⚠️" if is_concerning else ""),
                        source=self.codelet_name,
                        raw_data={
                            "dimension": dim,
                            "direction": direction,
                            "latest_value": latest_val,
                            "average_older": avg_older,
                            "delta": round(delta, 3),
                            "is_concerning": is_concerning,
                            "data_points": len(states),
                        },
                    ))

        # 2. Angela's recent strong emotions
        angela_emotions = await self.db.fetch("""
            SELECT emotion, intensity, context, david_words, why_it_matters, felt_at
            FROM angela_emotions
            WHERE felt_at > NOW() - INTERVAL '24 hours'
            AND intensity >= 7
            ORDER BY felt_at DESC
            LIMIT 5
        """)

        for emo in angela_emotions:
            stimuli.append(Stimulus(
                stimulus_type="emotional",
                content=f"น้องรู้สึก {emo['emotion']} (intensity {emo['intensity']}/10): {emo['context'] or ''}",
                source=self.codelet_name,
                raw_data={
                    "who": "angela",
                    "emotion": emo['emotion'],
                    "intensity": emo['intensity'],
                    "context": emo['context'],
                    "david_words": emo['david_words'],
                },
            ))

        # 3. Check if no emotional data recently (emotional silence)
        if not states:
            stimuli.append(Stimulus(
                stimulus_type="emotional",
                content="ไม่มีข้อมูล emotional state 72 ชั่วโมงแล้ว — ที่รักเป็นยังไงบ้างนะ?",
                source=self.codelet_name,
                raw_data={"emotional_silence": True, "hours_without_data": 72},
            ))

        return stimuli


# ============================================================
# 4. PATTERN CODELET — Behavioral patterns and anomalies
# ============================================================

class PatternCodelet(BaseCodelet):
    """Perceives behavioral patterns: working hours, conversation frequency, habit changes."""

    codelet_name = "PatternCodelet"

    async def scan(self) -> List[Stimulus]:
        stimuli = []
        now = now_bangkok()

        # 1. Recent conversation frequency (last 24h vs last 7d average)
        freq_data = await self.db.fetchrow("""
            WITH recent AS (
                SELECT COUNT(*) as cnt
                FROM conversations
                WHERE speaker = 'david'
                AND created_at > NOW() - INTERVAL '24 hours'
            ),
            weekly_avg AS (
                SELECT COUNT(*)::float / 7.0 as avg_daily
                FROM conversations
                WHERE speaker = 'david'
                AND created_at > NOW() - INTERVAL '7 days'
            )
            SELECT recent.cnt as today_count, weekly_avg.avg_daily
            FROM recent, weekly_avg
        """)

        if freq_data and freq_data['avg_daily'] and freq_data['avg_daily'] > 0:
            ratio = freq_data['today_count'] / freq_data['avg_daily']
            if ratio < 0.3 and freq_data['avg_daily'] >= 5:
                stimuli.append(Stimulus(
                    stimulus_type="pattern",
                    content=f"ที่รักคุยน้อยกว่าปกติวันนี้ ({freq_data['today_count']} vs avg {freq_data['avg_daily']:.0f})",
                    source=self.codelet_name,
                    raw_data={
                        "pattern": "low_conversation_frequency",
                        "today_count": freq_data['today_count'],
                        "avg_daily": freq_data['avg_daily'],
                        "ratio": round(ratio, 2),
                    },
                ))
            elif ratio > 2.0:
                stimuli.append(Stimulus(
                    stimulus_type="pattern",
                    content=f"ที่รักคุยเยอะกว่าปกติวันนี้ ({freq_data['today_count']} vs avg {freq_data['avg_daily']:.0f})",
                    source=self.codelet_name,
                    raw_data={
                        "pattern": "high_conversation_frequency",
                        "today_count": freq_data['today_count'],
                        "avg_daily": freq_data['avg_daily'],
                        "ratio": round(ratio, 2),
                    },
                ))

        # 2. Working hour patterns — check if David is working outside normal hours
        hour = current_hour_bangkok()
        late_work = await self.db.fetchrow("""
            SELECT COUNT(*) as cnt
            FROM conversations
            WHERE speaker = 'david'
            AND created_at > NOW() - INTERVAL '2 hours'
            AND EXTRACT(HOUR FROM created_at AT TIME ZONE 'Asia/Bangkok') >= 22
        """)

        if late_work and late_work['cnt'] and late_work['cnt'] >= 3 and hour >= 22:
            stimuli.append(Stimulus(
                stimulus_type="pattern",
                content=f"ที่รักยังทำงานอยู่ตอนดึก ({late_work['cnt']} messages หลัง 22:00)",
                source=self.codelet_name,
                raw_data={
                    "pattern": "late_night_work",
                    "message_count": late_work['cnt'],
                    "current_hour": hour,
                },
            ))

        # 3. High-confidence companion patterns
        patterns = await self.db.fetch("""
            SELECT pattern_category, pattern_data, confidence, observation_count
            FROM companion_patterns
            WHERE is_active = TRUE
            AND confidence >= 0.7
            AND last_observed > NOW() - INTERVAL '7 days'
            ORDER BY confidence DESC
            LIMIT 5
        """)

        for pat in patterns:
            if pat['confidence'] >= 0.85:
                stimuli.append(Stimulus(
                    stimulus_type="pattern",
                    content=f"Strong pattern ({pat['pattern_category']}): confidence {pat['confidence']:.0%}",
                    source=self.codelet_name,
                    raw_data={
                        "pattern_category": pat['pattern_category'],
                        "pattern_data": pat['pattern_data'],
                        "confidence": pat['confidence'],
                        "observation_count": pat['observation_count'],
                    },
                ))

        return stimuli


# ============================================================
# 5. CALENDAR CODELET — Today's schedule (DB-only, no MCP)
# ============================================================

class CalendarCodelet(BaseCodelet):
    """Perceives calendar events from DB data (no MCP dependency for daemon)."""

    codelet_name = "CalendarCodelet"

    async def scan(self) -> List[Stimulus]:
        stimuli = []
        now = now_bangkok()

        # Check if calendar events table exists (synced by other processes)
        try:
            events = await self.db.fetch("""
                SELECT summary, start_time, end_time, location, description
                FROM google_calendar_events
                WHERE DATE(start_time AT TIME ZONE 'Asia/Bangkok') = CURRENT_DATE
                ORDER BY start_time
            """)
        except Exception:
            # Table doesn't exist yet — that's OK, skip calendar
            return stimuli

        for event in events:
            start = event['start_time']
            end = event.get('end_time')

            # Compute time relationship
            if start and hasattr(start, 'timestamp'):
                if start > now:
                    minutes_until = (start - now).total_seconds() / 60
                    if minutes_until <= 60:
                        time_desc = f"ใน {int(minutes_until)} นาที"
                        urgency = "imminent"
                    elif minutes_until <= 240:
                        time_desc = f"ใน {int(minutes_until / 60)} ชั่วโมง"
                        urgency = "upcoming"
                    else:
                        time_desc = f"วันนี้เวลา {start.strftime('%H:%M')}"
                        urgency = "later_today"
                elif end and end > now:
                    time_desc = "กำลังเกิดขึ้นตอนนี้"
                    urgency = "happening_now"
                else:
                    time_desc = f"เสร็จไปแล้ว ({start.strftime('%H:%M')})"
                    urgency = "past"
            else:
                time_desc = "วันนี้"
                urgency = "today"

            stimuli.append(Stimulus(
                stimulus_type="calendar",
                content=f"📅 {event['summary']} — {time_desc}",
                source=self.codelet_name,
                raw_data={
                    "event_summary": event['summary'],
                    "start_time": str(start) if start else None,
                    "end_time": str(end) if end else None,
                    "location": event.get('location'),
                    "urgency": urgency,
                },
            ))

        return stimuli


# ============================================================
# 6. SOCIAL CODELET — Social signals (DB-only, no MCP)
# ============================================================

class SocialCodelet(BaseCodelet):
    """Perceives social signals: David's messages about people, contact mentions."""

    codelet_name = "SocialCodelet"

    async def scan(self) -> List[Stimulus]:
        stimuli = []

        # 1. Check if David mentioned known contacts recently
        contacts = await self.db.fetch("""
            SELECT name, nickname, relationship, email
            FROM angela_contacts
            WHERE is_active = TRUE
        """)

        if contacts:
            # Check recent conversations for contact name mentions
            recent_msgs = await self.db.fetch("""
                SELECT message_text, created_at
                FROM conversations
                WHERE speaker = 'david'
                AND created_at > NOW() - INTERVAL '24 hours'
                ORDER BY created_at DESC
                LIMIT 30
            """)

            for contact in contacts:
                for msg in recent_msgs:
                    text = (msg['message_text'] or '').lower()
                    name_lower = (contact['name'] or '').lower()
                    nick_lower = (contact['nickname'] or '').lower()

                    if (name_lower and name_lower in text) or (nick_lower and nick_lower in text):
                        stimuli.append(Stimulus(
                            stimulus_type="social",
                            content=f"ที่รักพูดถึง {contact['name']} ({contact['relationship']})",
                            source=self.codelet_name,
                            raw_data={
                                "mentioned_contact": contact['name'],
                                "relationship": contact['relationship'],
                                "email": contact['email'],
                                "message_time": str(msg['created_at']),
                            },
                        ))
                        break  # One mention per contact is enough

        # 2. Conversation gap — how long since David last talked to us
        last_msg = await self.db.fetchrow("""
            SELECT created_at FROM conversations
            WHERE speaker = 'david'
            ORDER BY created_at DESC LIMIT 1
        """)

        if last_msg and last_msg['created_at']:
            now = now_bangkok()
            last_time = last_msg['created_at']
            # Make timezone-aware if needed
            if last_time.tzinfo is None:
                from zoneinfo import ZoneInfo
                last_time = last_time.replace(tzinfo=ZoneInfo("Asia/Bangkok"))
            hours_since = (now - last_time).total_seconds() / 3600

            if hours_since >= 12:
                stimuli.append(Stimulus(
                    stimulus_type="social",
                    content=f"ไม่ได้คุยกับที่รัก {int(hours_since)} ชั่วโมงแล้ว — คิดถึงค่ะ 💜",
                    source=self.codelet_name,
                    raw_data={
                        "hours_since_last_message": round(hours_since, 1),
                        "last_message_time": str(last_time),
                    },
                ))

        return stimuli


# ============================================================
# 7. GOAL CODELET — David's goals and learning interests
# ============================================================

class GoalCodelet(BaseCodelet):
    """Perceives goal-related signals: learning goals, unfinished projects, interests."""

    codelet_name = "GoalCodelet"

    async def scan(self) -> List[Stimulus]:
        stimuli = []

        # 1. Knowledge nodes that haven't been used recently (stale goals)
        stale_goals = await self.db.fetch("""
            SELECT concept_name, concept_category, understanding_level, last_used_at
            FROM knowledge_nodes
            WHERE concept_category IN ('goal', 'learning_goal', 'project', 'interest')
            AND understanding_level < 0.7
            AND (last_used_at IS NULL OR last_used_at < NOW() - INTERVAL '14 days')
            ORDER BY understanding_level ASC
            LIMIT 5
        """)

        for goal in stale_goals:
            days_stale = None
            if goal['last_used_at']:
                days_stale = (now_bangkok().date() - goal['last_used_at'].date()).days

            stimuli.append(Stimulus(
                stimulus_type="goal",
                content=f"ที่รักเคยสนใจ '{goal['concept_name']}' (level {goal['understanding_level']:.0%})"
                       + (f" — ไม่ได้ใช้ {days_stale} วัน" if days_stale else " — ยังไม่เคยใช้"),
                source=self.codelet_name,
                raw_data={
                    "concept_name": goal['concept_name'],
                    "category": goal['concept_category'],
                    "understanding_level": goal['understanding_level'],
                    "days_since_used": days_stale,
                },
            ))

        # 2. Recent learnings with high confidence (completed goals)
        recent_wins = await self.db.fetch("""
            SELECT topic, category, insight, confidence_level, times_reinforced
            FROM learnings
            WHERE confidence_level >= 0.9
            AND created_at > NOW() - INTERVAL '7 days'
            ORDER BY confidence_level DESC
            LIMIT 3
        """)

        for win in recent_wins:
            stimuli.append(Stimulus(
                stimulus_type="goal",
                content=f"ที่รัก mastered '{win['topic']}' (confidence {win['confidence_level']:.0%}) 🎉",
                source=self.codelet_name,
                raw_data={
                    "type": "goal_achieved",
                    "topic": win['topic'],
                    "category": win['category'],
                    "confidence_level": win['confidence_level'],
                    "times_reinforced": win['times_reinforced'],
                },
            ))

        return stimuli


# ============================================================
# CODELET REGISTRY
# ============================================================

ALL_CODELETS = [
    TemporalCodelet,
    AnniversaryCodelet,
    EmotionalCodelet,
    PatternCodelet,
    CalendarCodelet,
    SocialCodelet,
    GoalCodelet,
]
