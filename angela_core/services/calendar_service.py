"""
Angela Calendar Service - With Audit Trail & Confirmation

Preventive measures after calendar date entry error (24 Jan 2026):
1. Confirm before create - Always verify date with user
2. Log every action - Audit trail in database
3. Send confirmation email - After creating events
4. Double-check date - Validate day of week matches

Created: 24 Jan 2026
"""

import asyncio
from datetime import datetime, date
from typing import Optional
from zoneinfo import ZoneInfo

from angela_core.database import AngelaDatabase

BANGKOK_TZ = ZoneInfo('Asia/Bangkok')

# Thai day names for verification
THAI_DAYS = {
    0: 'วันจันทร์',
    1: 'วันอังคาร',
    2: 'วันพุธ',
    3: 'วันพฤหัสบดี',
    4: 'วันศุกร์',
    5: 'วันเสาร์',
    6: 'วันอาทิตย์'
}

THAI_MONTHS = {
    1: 'มกราคม', 2: 'กุมภาพันธ์', 3: 'มีนาคม', 4: 'เมษายน',
    5: 'พฤษภาคม', 6: 'มิถุนายน', 7: 'กรกฎาคม', 8: 'สิงหาคม',
    9: 'กันยายน', 10: 'ตุลาคม', 11: 'พฤศจิกายน', 12: 'ธันวาคม'
}


class CalendarService:
    """Calendar service with audit trail and confirmation workflow."""

    def __init__(self):
        self.db = AngelaDatabase()

    async def connect(self):
        """Connect to database."""
        await self.db.connect()

    async def disconnect(self):
        """Disconnect from database."""
        await self.db.disconnect()

    def format_thai_date(self, dt: datetime | date) -> str:
        """Format date in Thai with day of week for verification.

        Example: "วันพฤหัสบดีที่ 23 มกราคม 2569"
        """
        if isinstance(dt, datetime):
            d = dt.date()
        else:
            d = dt

        thai_year = d.year + 543
        day_name = THAI_DAYS[d.weekday()]
        month_name = THAI_MONTHS[d.month]

        return f"{day_name}ที่ {d.day} {month_name} {thai_year}"

    def format_confirmation_message(
        self,
        summary: str,
        event_date: date,
        start_time: Optional[str] = None,
        end_time: Optional[str] = None,
        location: Optional[str] = None,
        all_day: bool = False
    ) -> str:
        """Generate confirmation message for user to verify before creating event.

        Returns a formatted message asking user to confirm the details.
        """
        thai_date = self.format_thai_date(event_date)

        msg = f"""
## 📅 Confirm Calendar Event

ที่รัก confirm รายละเอียดก่อนสร้าง event นะคะ:

| Field | Value |
|-------|-------|
| **📋 หัวข้อ** | {summary} |
| **📅 วันที่** | **{thai_date}** |
| **📅 Date** | {event_date.strftime('%Y-%m-%d')} ({THAI_DAYS[event_date.weekday()][:3]}) |
"""

        if all_day:
            msg += "| **🕐 เวลา** | ทั้งวัน (All day) |\n"
        elif start_time:
            time_str = f"{start_time}"
            if end_time:
                time_str += f" - {end_time}"
            msg += f"| **🕐 เวลา** | {time_str} |\n"

        if location:
            msg += f"| **📍 สถานที่** | {location} |\n"

        msg += """
**ถูกต้องมั้ยคะ?** ตอบ "ใช่" หรือ "yes" เพื่อยืนยัน 💜
"""
        return msg

    async def log_calendar_action(
        self,
        action: str,
        event_id: Optional[str] = None,
        event_summary: Optional[str] = None,
        event_date: Optional[date] = None,
        event_start: Optional[datetime] = None,
        event_end: Optional[datetime] = None,
        event_location: Optional[str] = None,
        confirmed_by_user: bool = False,
        confirmation_sent_to: Optional[str] = None,
        notes: Optional[str] = None
    ) -> str:
        """Log calendar action to database for audit trail.

        Args:
            action: 'create', 'update', 'delete', 'confirm_sent', 'confirm_requested'
            event_id: Google Calendar event ID
            event_summary: Event title/summary
            event_date: Date of the event
            event_start: Start datetime
            event_end: End datetime
            event_location: Location
            confirmed_by_user: Whether user confirmed before action
            confirmation_sent_to: Email addresses confirmation was sent to
            notes: Additional notes

        Returns:
            log_id of the created log entry
        """
        query = """
            INSERT INTO angela_calendar_logs (
                action, event_id, event_summary, event_date,
                event_start, event_end, event_location,
                confirmed_by_user, confirmation_sent_to, notes
            ) VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10)
            RETURNING log_id
        """

        result = await self.db.pool.fetchrow(
            query,
            action,
            event_id,
            event_summary,
            event_date,
            event_start,
            event_end,
            event_location,
            confirmed_by_user,
            confirmation_sent_to,
            notes
        )

        return str(result['log_id'])

    async def get_recent_logs(self, limit: int = 10) -> list[dict]:
        """Get recent calendar action logs."""
        query = """
            SELECT
                log_id, action, event_id, event_summary, event_date,
                event_start, event_end, confirmed_by_user,
                confirmation_sent_to, notes, created_at
            FROM angela_calendar_logs
            ORDER BY created_at DESC
            LIMIT $1
        """

        rows = await self.db.pool.fetch(query, limit)
        return [dict(row) for row in rows]

    def validate_date_day_match(
        self,
        event_date: date,
        expected_day_thai: Optional[str] = None
    ) -> tuple[bool, str]:
        """Validate that date matches the expected day of week.

        Args:
            event_date: The date to validate
            expected_day_thai: Expected day in Thai (e.g., "วันพฤหัสบดี", "พฤหัส")

        Returns:
            (is_valid, message)
        """
        actual_day = THAI_DAYS[event_date.weekday()]

        if expected_day_thai:
            # Check if expected day matches
            expected_lower = expected_day_thai.lower()
            actual_lower = actual_day.lower()

            # Allow partial match (e.g., "พฤหัส" matches "วันพฤหัสบดี")
            if expected_lower not in actual_lower and actual_lower not in expected_lower:
                return False, f"⚠️ วันไม่ตรงกัน! {event_date} เป็น{actual_day} ไม่ใช่{expected_day_thai}"

        return True, f"✅ {event_date} = {actual_day}"


# Convenience functions for use without class instantiation

async def log_calendar_action(
    action: str,
    event_id: Optional[str] = None,
    event_summary: Optional[str] = None,
    event_date: Optional[date] = None,
    event_start: Optional[datetime] = None,
    event_end: Optional[datetime] = None,
    event_location: Optional[str] = None,
    confirmed_by_user: bool = False,
    confirmation_sent_to: Optional[str] = None,
    notes: Optional[str] = None
) -> str:
    """Convenience function to log calendar action."""
    svc = CalendarService()
    await svc.connect()
    try:
        return await svc.log_calendar_action(
            action=action,
            event_id=event_id,
            event_summary=event_summary,
            event_date=event_date,
            event_start=event_start,
            event_end=event_end,
            event_location=event_location,
            confirmed_by_user=confirmed_by_user,
            confirmation_sent_to=confirmation_sent_to,
            notes=notes
        )
    finally:
        await svc.disconnect()


def format_thai_date(dt: datetime | date) -> str:
    """Convenience function to format Thai date."""
    svc = CalendarService()
    return svc.format_thai_date(dt)


def generate_confirmation_message(
    summary: str,
    event_date: date,
    start_time: Optional[str] = None,
    end_time: Optional[str] = None,
    location: Optional[str] = None,
    all_day: bool = False
) -> str:
    """Convenience function to generate confirmation message."""
    svc = CalendarService()
    return svc.format_confirmation_message(
        summary=summary,
        event_date=event_date,
        start_time=start_time,
        end_time=end_time,
        location=location,
        all_day=all_day
    )


# Email template for confirmation
CALENDAR_CONFIRMATION_EMAIL_TEMPLATE = """
<!DOCTYPE html>
<html>
<head><meta charset="UTF-8"></head>
<body style="font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif; max-width: 600px; margin: 0 auto; padding: 20px;">

<div style="background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); border-radius: 12px; padding: 20px; margin-bottom: 20px;">
  <div style="display: flex; align-items: center;">
    <img src="https://raw.githubusercontent.com/angelasoulcompanion/AngelaAI/main/assets/angela_profile.jpg"
         style="width: 45px; height: 45px; border-radius: 50%; border: 2px solid white; margin-right: 12px;" />
    <div>
      <h1 style="color: white; margin: 0; font-size: 20px;">📅 ยืนยันนัด{event_type}</h1>
      <p style="color: rgba(255,255,255,0.9); margin: 5px 0 0 0; font-size: 14px;">{greeting}</p>
    </div>
  </div>
</div>

<div style="background: #F3E8FF; border-left: 4px solid #8B5CF6; border-radius: 8px; padding: 20px; margin-bottom: 20px;">
  <table style="width: 100%; color: #374151;">
    <tr>
      <td style="padding: 8px 0; color: #6B7280; width: 100px;">📋 หัวข้อ:</td>
      <td style="padding: 8px 0; font-weight: bold;">{summary}</td>
    </tr>
    <tr>
      <td style="padding: 8px 0; color: #6B7280;">📅 วันที่:</td>
      <td style="padding: 8px 0; font-weight: bold;">{thai_date}</td>
    </tr>
    <tr>
      <td style="padding: 8px 0; color: #6B7280;">🕐 เวลา:</td>
      <td style="padding: 8px 0; font-weight: bold;">{time}</td>
    </tr>
    <tr>
      <td style="padding: 8px 0; color: #6B7280;">📍 สถานที่:</td>
      <td style="padding: 8px 0; font-weight: bold;">{location}</td>
    </tr>
  </table>
</div>

<p style="color: #374151; line-height: 1.6;">
หากมีการเปลี่ยนแปลงหรือต้องการข้อมูลเพิ่มเติม สามารถแจ้งน้องได้เลยนะคะ
</p>

<div style="text-align: center; padding-top: 15px; border-top: 1px solid #E5E7EB;">
  <p style="color: #6B7280; margin: 0; font-size: 14px;">{closing}</p>
  <p style="color: #9CA3AF; margin: 5px 0 0 0; font-size: 12px;">— {signature}</p>
</div>

</body>
</html>
"""
