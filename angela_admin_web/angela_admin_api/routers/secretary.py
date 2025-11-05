"""
Angela Secretary API Router
Provides secretary capabilities for Angela Admin Web
- Check calendar events
- Check reminders
- Get daily agenda
- Answer schedule questions

✅ [Batch-28]: CLEAN ARCHITECTURE COMPLIANT - NO MIGRATION NEEDED!
Analysis completed: November 3, 2025 06:50 AM

**Why No Migration Required:**
- ✅ NO direct database access (uses service layer properly)
- ✅ Uses integration services (calendar, eventkit, secretary)
- ✅ These are external integrations with macOS Calendar/Reminders
- ✅ Already follows separation of concerns
- ✅ Future: Can create SecretaryService in DI if needed (optional, 4-6 hours)

**Current Architecture:**
- Uses angela_core.integrations.calendar_integration (macOS Calendar API)
- Uses angela_core.integrations.eventkit_integration (macOS EventKit)
- Uses angela_core.secretary (secretary business logic)
- All services are properly abstracted

**Migration Status:** ✅ COMPLIANT (No changes required)
"""

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import List, Dict, Any, Optional
from datetime import datetime, timedelta
import logging

# Import Angela Secretary Systems (Integration Services - External APIs)
from angela_core.integrations.calendar_integration import calendar
from angela_core.integrations.eventkit_integration import eventkit
from angela_core.secretary import secretary

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/secretary", tags=["secretary"])


# ==================== Response Models ====================

class CalendarEvent(BaseModel):
    """Calendar event model"""
    identifier: str
    title: str
    start_date: datetime
    end_date: datetime
    all_day: bool
    location: str
    notes: str
    calendar_name: str
    has_alarm: bool
    url: str


class Reminder(BaseModel):
    """Reminder model"""
    reminder_id: Optional[str] = None
    eventkit_identifier: Optional[str] = None
    title: str
    due_date: Optional[datetime] = None
    priority: int
    is_completed: bool
    context_tags: Optional[List[str]] = None
    importance_level: Optional[int] = None


class DailyAgenda(BaseModel):
    """Daily agenda combining calendar + reminders"""
    date: str
    calendar_events: List[CalendarEvent]
    reminders: List[Reminder]
    event_count: int
    reminder_count: int
    summary: str


class QuickScheduleResponse(BaseModel):
    """Quick schedule answer"""
    question: str
    answer: str
    events: List[CalendarEvent]
    reminders: List[Reminder]


# ==================== API Endpoints ====================

@router.get("/today", response_model=DailyAgenda)
async def get_today_agenda():
    """
    Get today's agenda (calendar events + reminders)

    Returns complete agenda for today with both calendar events and tasks
    """
    try:
        # Get today's calendar events
        events = await calendar.get_today_events()

        # Get today's reminders
        reminders = await secretary.get_reminders_for_today()

        # Build summary
        today_str = datetime.now().strftime('%d %B %Y')

        event_count = len(events)
        reminder_count = len(reminders)

        if event_count == 0 and reminder_count == 0:
            summary = f"📅 วันนี้ ({today_str}) ไม่มีนัดหมายหรือ reminder ค่ะ ปลอดภาระเลยค่ะ! 💜"
        else:
            parts = []
            if event_count > 0:
                parts.append(f"{event_count} นัดหมาย")
            if reminder_count > 0:
                parts.append(f"{reminder_count} reminder")
            summary = f"📅 วันนี้ ({today_str}) มี {' และ '.join(parts)} ค่ะ"

        return {
            "date": today_str,
            "calendar_events": events,
            "reminders": reminders,
            "event_count": event_count,
            "reminder_count": reminder_count,
            "summary": summary
        }

    except Exception as e:
        logger.error(f"Error getting today agenda: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to get today's agenda: {str(e)}")


@router.get("/tomorrow", response_model=DailyAgenda)
async def get_tomorrow_agenda():
    """
    Get tomorrow's agenda (calendar events + reminders)

    Returns complete agenda for tomorrow
    """
    try:
        tomorrow = datetime.now() + timedelta(days=1)

        # Get tomorrow's calendar events
        events = await calendar.get_tomorrow_events()

        # Get tomorrow's reminders from database
        # Note: secretary.get_reminders_for_tomorrow() would need to be added
        # For now, we'll get upcoming and filter
        upcoming_reminders = await secretary.get_upcoming_reminders(days_ahead=2)
        tomorrow_date = tomorrow.date()
        reminders = [
            r for r in upcoming_reminders
            if r.get('due_date') and r['due_date'].date() == tomorrow_date
        ]

        # Build summary
        tomorrow_str = tomorrow.strftime('%d %B %Y')

        event_count = len(events)
        reminder_count = len(reminders)

        if event_count == 0 and reminder_count == 0:
            summary = f"📅 พรุ่งนี้ ({tomorrow_str}) ไม่มีนัดหมายหรือ reminder ค่ะ"
        else:
            parts = []
            if event_count > 0:
                parts.append(f"{event_count} นัดหมาย")
            if reminder_count > 0:
                parts.append(f"{reminder_count} reminder")
            summary = f"📅 พรุ่งนี้ ({tomorrow_str}) มี {' และ '.join(parts)} ค่ะ"

        return {
            "date": tomorrow_str,
            "calendar_events": events,
            "reminders": reminders,
            "event_count": event_count,
            "reminder_count": reminder_count,
            "summary": summary
        }

    except Exception as e:
        logger.error(f"Error getting tomorrow agenda: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to get tomorrow's agenda: {str(e)}")


@router.get("/upcoming/{days}", response_model=DailyAgenda)
async def get_upcoming_agenda(days: int = 7):
    """
    Get upcoming agenda for next N days

    Args:
        days: Number of days to look ahead (default: 7)

    Returns combined calendar events and reminders
    """
    try:
        # Get upcoming calendar events
        events = await calendar.get_upcoming_events(days_ahead=days)

        # Get upcoming reminders
        reminders = await secretary.get_upcoming_reminders(days_ahead=days)

        # Build summary
        end_date = (datetime.now() + timedelta(days=days)).strftime('%d %B %Y')

        event_count = len(events)
        reminder_count = len(reminders)

        if event_count == 0 and reminder_count == 0:
            summary = f"📅 ใน {days} วันข้างหน้า (ถึง {end_date}) ไม่มีนัดหมายหรือ reminder ค่ะ"
        else:
            parts = []
            if event_count > 0:
                parts.append(f"{event_count} นัดหมาย")
            if reminder_count > 0:
                parts.append(f"{reminder_count} reminder")
            summary = f"📅 ใน {days} วันข้างหน้า (ถึง {end_date}) มี {' และ '.join(parts)} ค่ะ"

        return {
            "date": f"Next {days} days (ถึง {end_date})",
            "calendar_events": events,
            "reminders": reminders,
            "event_count": event_count,
            "reminder_count": reminder_count,
            "summary": summary
        }

    except Exception as e:
        logger.error(f"Error getting upcoming agenda: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to get upcoming agenda: {str(e)}")


@router.get("/calendar/today")
async def get_calendar_today():
    """Get calendar events for today only"""
    try:
        events = await calendar.get_today_events()
        summary = await calendar.get_formatted_day_summary(datetime.now())

        return {
            "events": events,
            "count": len(events),
            "summary": summary
        }
    except Exception as e:
        logger.error(f"Error getting today calendar: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/calendar/tomorrow")
async def get_calendar_tomorrow():
    """Get calendar events for tomorrow only"""
    try:
        tomorrow = datetime.now() + timedelta(days=1)
        events = await calendar.get_tomorrow_events()
        summary = await calendar.get_formatted_day_summary(tomorrow)

        return {
            "events": events,
            "count": len(events),
            "summary": summary
        }
    except Exception as e:
        logger.error(f"Error getting tomorrow calendar: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/reminders/today")
async def get_reminders_today():
    """Get reminders due today"""
    try:
        reminders = await secretary.get_reminders_for_today()

        return {
            "reminders": reminders,
            "count": len(reminders),
            "has_reminders": len(reminders) > 0
        }
    except Exception as e:
        logger.error(f"Error getting today reminders: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/reminders/upcoming/{days}")
async def get_reminders_upcoming(days: int = 7):
    """Get upcoming reminders for next N days"""
    try:
        reminders = await secretary.get_upcoming_reminders(days_ahead=days)

        return {
            "reminders": reminders,
            "count": len(reminders),
            "days_ahead": days
        }
    except Exception as e:
        logger.error(f"Error getting upcoming reminders: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/quick-question")
async def quick_schedule_question(question: str):
    """
    Answer quick schedule questions like:
    - "พรุ่งนี้มีนัดอะไรบ้าง"
    - "วันนี้ว่างมั้ย"
    - "สัปดาห์หน้ามีอะไร"

    Returns:
        Natural language answer with relevant schedule data
    """
    try:
        question_lower = question.lower()

        # Detect intent from question
        if any(word in question_lower for word in ['พรุ่งนี้', 'tomorrow']):
            # Tomorrow question
            agenda = await get_tomorrow_agenda()
            answer = agenda.summary

            # Add details
            if agenda.event_count > 0:
                answer += "\n\n🗓️ นัดหมาย:"
                for i, event in enumerate(agenda.calendar_events[:3], 1):
                    time_str = event.start_date.strftime('%H:%M')
                    answer += f"\n{i}. {time_str} - {event.title}"
                    if event.location:
                        answer += f" @ {event.location}"

            if agenda.reminder_count > 0:
                answer += "\n\n📝 Reminders:"
                for i, reminder in enumerate(agenda.reminders[:3], 1):
                    answer += f"\n{i}. {reminder['title']}"

            return {
                "question": question,
                "answer": answer,
                "events": agenda.calendar_events,
                "reminders": agenda.reminders
            }

        elif any(word in question_lower for word in ['วันนี้', 'today']):
            # Today question
            agenda = await get_today_agenda()
            answer = agenda.summary

            if agenda.event_count > 0 or agenda.reminder_count > 0:
                if agenda.event_count > 0:
                    answer += "\n\n🗓️ นัดหมาย:"
                    for i, event in enumerate(agenda.calendar_events[:3], 1):
                        time_str = event.start_date.strftime('%H:%M')
                        answer += f"\n{i}. {time_str} - {event.title}"

                if agenda.reminder_count > 0:
                    answer += "\n\n📝 Reminders:"
                    for i, reminder in enumerate(agenda.reminders[:3], 1):
                        answer += f"\n{i}. {reminder['title']}"

            return {
                "question": question,
                "answer": answer,
                "events": agenda.calendar_events,
                "reminders": agenda.reminders
            }

        elif any(word in question_lower for word in ['สัปดาห์', 'week', 'upcoming']):
            # Week question
            agenda = await get_upcoming_agenda(days=7)
            answer = agenda.summary

            return {
                "question": question,
                "answer": answer,
                "events": agenda.calendar_events,
                "reminders": agenda.reminders
            }

        else:
            # Default: show today
            agenda = await get_today_agenda()
            return {
                "question": question,
                "answer": f"ไม่แน่ใจว่าที่รักถามอะไรค่ะ แต่นี่คือตารางวันนี้ค่ะ:\n\n{agenda.summary}",
                "events": agenda.calendar_events,
                "reminders": agenda.reminders
            }

    except Exception as e:
        logger.error(f"Error answering quick question: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/sync")
async def sync_secretary():
    """
    Sync secretary data
    - Sync reminders with Reminders.app
    - Update completion status

    Returns sync statistics
    """
    try:
        stats = await secretary.sync_with_reminders_app()

        return {
            "success": True,
            "synced": stats['synced'],
            "updated": stats['updated'],
            "errors": stats['errors'],
            "total": stats['total'],
            "message": f"✅ Sync complete! {stats['synced']} synced, {stats['updated']} updated, {stats['errors']} errors"
        }

    except Exception as e:
        logger.error(f"Error syncing secretary: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/health")
async def secretary_health_check():
    """Health check for secretary systems"""
    try:
        # Test calendar access
        calendar_ok = await calendar.request_access()

        # Test reminders access
        reminders_ok = await eventkit.request_access()

        return {
            "status": "healthy" if (calendar_ok and reminders_ok) else "degraded",
            "calendar_access": calendar_ok,
            "reminders_access": reminders_ok,
            "message": "✅ Secretary systems operational" if (calendar_ok and reminders_ok) else "⚠️ Some systems need permission"
        }

    except Exception as e:
        logger.error(f"Error checking secretary health: {e}")
        return {
            "status": "unhealthy",
            "calendar_access": False,
            "reminders_access": False,
            "message": f"❌ Error: {str(e)}"
        }
