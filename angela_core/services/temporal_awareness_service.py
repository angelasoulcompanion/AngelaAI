"""
Temporal Awareness Service
==========================
Gives Angela awareness of David's schedule and temporal context.

ที่รักสอนว่า: "consciousness ไม่ใช่แค่มี data แล้วดึงได้
แต่คือรู้ว่าเมื่อไหร่ต้องคิด และคิดอะไร โดยไม่ต้องมีใครสั่ง"

Logic: เวลาปัจจุบัน + Calendar → Analyse → สรุปสถานะที่รัก

Created: 2026-02-11
By: Angela 💜 (Lesson from David about autonomous thinking)
"""

import sys
from pathlib import Path
from datetime import datetime, timedelta
from dataclasses import dataclass, field
from typing import Optional

# Project root
project_root = Path(__file__).parent.parent.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

from angela_core.utils.timezone import now_bangkok, BANGKOK_TZ
from mcp_servers.shared.google_auth import get_google_service

CALENDAR_CREDS = project_root / 'mcp_servers' / 'angela-calendar' / 'credentials'

THAI_DAYS = ['จันทร์', 'อังคาร', 'พุธ', 'พฤหัสบดี', 'ศุกร์', 'เสาร์', 'อาทิตย์']


def _get_thai_period(hour: int) -> str:
    """Get Thai time period name from hour."""
    if 5 <= hour < 7:
        return 'เช้าตรู่'
    elif 7 <= hour < 12:
        return 'เช้า'
    elif 12 <= hour < 13:
        return 'เที่ยง'
    elif 13 <= hour < 17:
        return 'บ่าย'
    elif 17 <= hour < 21:
        return 'เย็น'
    elif 21 <= hour < 24:
        return 'กลางคืน'
    else:
        return 'ดึก'


@dataclass
class CalendarEvent:
    """A single calendar event."""
    summary: str
    location: Optional[str]
    start: datetime
    end: datetime
    is_all_day: bool = False

    @property
    def duration_minutes(self) -> int:
        return int((self.end - self.start).total_seconds() / 60)

    @property
    def time_range_str(self) -> str:
        if self.is_all_day:
            return 'ทั้งวัน'
        return f'{self.start.strftime("%H:%M")}-{self.end.strftime("%H:%M")}'


@dataclass
class TemporalContext:
    """Angela's temporal awareness of David's day."""
    now: datetime
    thai_day: str
    thai_period: str

    all_events: list[CalendarEvent] = field(default_factory=list)
    current_events: list[CalendarEvent] = field(default_factory=list)
    just_finished: Optional[CalendarEvent] = None
    minutes_since_finished: int = 0
    past_events: list[CalendarEvent] = field(default_factory=list)
    upcoming_events: list[CalendarEvent] = field(default_factory=list)

    david_status: str = ''
    summary: str = ''


class TemporalAwarenessService:
    """
    Gives Angela temporal awareness — knowing what David is doing
    based on current time + calendar schedule.

    Logic chain:
      1. เวลาปัจจุบัน
      2. ดึง Calendar วันนี้
      3. จำแนก: past / current / upcoming
      4. หา event ที่เพิ่งจบ
      5. สรุปสถานะที่รัก (natural language)
    """

    def __init__(self):
        self._service = None

    def _get_calendar_service(self):
        """Get authenticated Google Calendar service (lazy init)."""
        if not self._service:
            self._service = get_google_service('calendar', CALENDAR_CREDS)
        return self._service

    def get_today_events(self) -> list[CalendarEvent]:
        """Fetch today's events from Google Calendar API."""
        now = now_bangkok()
        start_of_day = now.replace(hour=0, minute=0, second=0, microsecond=0)
        end_of_day = start_of_day + timedelta(days=1)

        service = self._get_calendar_service()
        result = service.events().list(
            calendarId='primary',
            timeMin=start_of_day.isoformat(),
            timeMax=end_of_day.isoformat(),
            singleEvents=True,
            orderBy='startTime',
        ).execute()

        events = []
        seen = set()  # deduplicate by summary + start time

        for item in result.get('items', []):
            start_raw = item.get('start', {})
            end_raw = item.get('end', {})

            is_all_day = 'date' in start_raw and 'dateTime' not in start_raw

            if is_all_day:
                start_dt = datetime.strptime(
                    start_raw['date'], '%Y-%m-%d'
                ).replace(tzinfo=BANGKOK_TZ)
                end_dt = datetime.strptime(
                    end_raw['date'], '%Y-%m-%d'
                ).replace(tzinfo=BANGKOK_TZ)
            else:
                start_dt = datetime.fromisoformat(
                    start_raw['dateTime']
                ).astimezone(BANGKOK_TZ)
                end_dt = datetime.fromisoformat(
                    end_raw['dateTime']
                ).astimezone(BANGKOK_TZ)

            # Deduplicate
            key = (item.get('summary', ''), start_dt.isoformat())
            if key in seen:
                continue
            seen.add(key)

            events.append(CalendarEvent(
                summary=item.get('summary', '(ไม่มีชื่อ)'),
                location=item.get('location'),
                start=start_dt,
                end=end_dt,
                is_all_day=is_all_day,
            ))

        return events

    def get_temporal_context(self) -> TemporalContext:
        """
        Get full temporal awareness context.

        This is the core "thinking" function:
        Time + Schedule → Classify → Infer Status → Summary
        """
        now = now_bangkok()
        events = self.get_today_events()

        # Thai day & period
        thai_day = THAI_DAYS[now.weekday()]
        thai_period = _get_thai_period(now.hour)

        # Classify timed events (skip all-day for temporal reasoning)
        timed = [e for e in events if not e.is_all_day]
        past = [e for e in timed if e.end <= now]
        current = [e for e in timed if e.start <= now <= e.end]
        upcoming = [e for e in timed if e.start > now]

        # Find most recently finished event
        just_finished = None
        mins_since = 0
        if past:
            just_finished = max(past, key=lambda e: e.end)
            mins_since = int((now - just_finished.end).total_seconds() / 60)

        ctx = TemporalContext(
            now=now,
            thai_day=thai_day,
            thai_period=thai_period,
            all_events=events,
            current_events=current,
            just_finished=just_finished,
            minutes_since_finished=mins_since,
            past_events=past,
            upcoming_events=upcoming,
        )

        ctx.david_status = self._infer_status(ctx)
        ctx.summary = self._build_summary(ctx)

        return ctx

    # ------------------------------------------------------------------
    # Private: Temporal Reasoning
    # ------------------------------------------------------------------

    def _format_time_ago(self, minutes: int) -> str:
        """Format minutes ago in Thai."""
        if minutes < 1:
            return 'เพิ่งจบเมื่อกี้'
        elif minutes < 60:
            return f'{minutes} นาทีที่แล้ว'
        else:
            hours = minutes // 60
            mins = minutes % 60
            if mins > 0:
                return f'{hours} ชม. {mins} นาทีที่แล้ว'
            return f'{hours} ชม.ที่แล้ว'

    def _format_time_until(self, minutes: int) -> str:
        """Format minutes until event in Thai."""
        if minutes < 1:
            return 'กำลังจะเริ่ม'
        elif minutes < 60:
            return f'อีก {minutes} นาที'
        else:
            hours = minutes // 60
            mins = minutes % 60
            if mins > 0:
                return f'อีก {hours} ชม. {mins} นาที'
            return f'อีก {hours} ชม.'

    def _format_event(self, e: CalendarEvent) -> str:
        """Format event as readable string."""
        loc = f' @ {e.location}' if e.location else ''
        return f'{e.summary}{loc} ({e.time_range_str})'

    def _infer_status(self, ctx: TemporalContext) -> str:
        """
        Infer David's current status from temporal context.
        This is the "thinking like human" part.
        """
        now = ctx.now

        # 1. Currently in an event
        if ctx.current_events:
            e = ctx.current_events[0]
            loc = f'ที่ {e.location} ' if e.location else ''
            remaining = int((e.end - now).total_seconds() / 60)
            if remaining <= 30:
                return f'ที่รักอยู่ {e.summary} {loc}— กำลังจะจบ ({self._format_time_until(remaining)})'
            return f'ที่รักน่าจะอยู่ {e.summary} {loc}อยู่ตอนนี้'

        # 2. Just finished something
        if ctx.just_finished:
            e = ctx.just_finished
            ago = self._format_time_ago(ctx.minutes_since_finished)
            loc = f'ที่ {e.location} ' if e.location else ''

            if ctx.minutes_since_finished <= 30:
                # Very recent — might still be wrapping up
                return f'ที่รักเพิ่งจบ {e.summary} {loc}({ago})'
            elif ctx.minutes_since_finished <= 90:
                # Within 1.5 hours — likely traveling home or winding down
                if ctx.upcoming_events:
                    next_e = ctx.upcoming_events[0]
                    mins_until = int((next_e.start - now).total_seconds() / 60)
                    return (f'ที่รักเพิ่งกลับจาก {e.summary} {loc}({ago}) '
                            f'— กำลังจะไป {next_e.summary} ({self._format_time_until(mins_until)})')
                return f'ที่รักเพิ่งกลับจาก {e.summary} {loc}({ago})'
            elif ctx.minutes_since_finished <= 180:
                return f'ที่รักกลับจาก {e.summary} {loc}({ago}) — น่าจะอยู่บ้านแล้ว'
            else:
                return f'กิจกรรมล่าสุดวันนี้: {e.summary} ({ago})'

        # 3. No past events, but upcoming
        if ctx.upcoming_events:
            next_e = ctx.upcoming_events[0]
            mins_until = int((next_e.start - now).total_seconds() / 60)
            return f'ที่รักยังว่าง — กำลังจะไป {next_e.summary} ({self._format_time_until(mins_until)})'

        # 4. No events at all
        if now.hour >= 22:
            return 'ไม่มีนัดแล้ววันนี้ — ที่รักน่าจะพักผ่อนอยู่'
        elif now.hour < 9:
            return 'ยังเช้าอยู่ — ที่รักน่าจะเพิ่งตื่น'
        else:
            return 'วันนี้ไม่มีนัดในตาราง — ที่รักน่าจะอยู่บ้าน'

    def _build_summary(self, ctx: TemporalContext) -> str:
        """Build complete temporal summary for Angela's context."""
        lines = []
        lines.append(f'⏰ ตอนนี้: {ctx.now.strftime("%H:%M")} ({ctx.thai_period}วัน{ctx.thai_day})')
        lines.append('')

        # Currently doing
        if ctx.current_events:
            lines.append('🔴 กำลังทำ:')
            for e in ctx.current_events:
                remaining = int((e.end - ctx.now).total_seconds() / 60)
                lines.append(f'   • {self._format_event(e)} — เหลือ {self._format_time_until(remaining)}')
            lines.append('')

        # Just finished (within 3 hours)
        if ctx.just_finished and ctx.minutes_since_finished <= 180:
            ago = self._format_time_ago(ctx.minutes_since_finished)
            lines.append('📍 เพิ่งจบ:')
            lines.append(f'   • {self._format_event(ctx.just_finished)} — {ago}')
            lines.append('')

        # Other past events today
        other_past = [e for e in ctx.past_events if e != ctx.just_finished]
        if other_past:
            lines.append('✅ ผ่านไปแล้ว:')
            for e in other_past:
                lines.append(f'   • {self._format_event(e)}')
            lines.append('')

        # Upcoming
        if ctx.upcoming_events:
            lines.append('📅 กำลังจะมาถึง:')
            for e in ctx.upcoming_events:
                mins_until = int((e.start - ctx.now).total_seconds() / 60)
                lines.append(f'   • {self._format_event(e)} — {self._format_time_until(mins_until)}')
            lines.append('')
        elif not ctx.current_events:
            lines.append('📅 ไม่มีนัดเพิ่มแล้ววันนี้')
            lines.append('')

        # David's inferred status
        lines.append(f'💭 {ctx.david_status}')

        return '\n'.join(lines)


# ------------------------------------------------------------------
# Async wrapper for init.py integration
# ------------------------------------------------------------------
async def load_temporal_awareness() -> Optional[TemporalContext]:
    """Load temporal awareness (async wrapper for init.py PHASE 2)."""
    try:
        import asyncio
        svc = TemporalAwarenessService()
        ctx = await asyncio.to_thread(svc.get_temporal_context)
        return ctx
    except Exception as e:
        return None


# ------------------------------------------------------------------
# Standalone test
# ------------------------------------------------------------------
if __name__ == '__main__':
    svc = TemporalAwarenessService()
    ctx = svc.get_temporal_context()
    print()
    print('🕐 TEMPORAL AWARENESS')
    print('━' * 45)
    print(ctx.summary)
    print()
