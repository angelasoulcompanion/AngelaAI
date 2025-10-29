"""
Angela Calendar Integration
Interfaces with macOS Calendar.app using EventKit framework
Reads calendar events and appointments
"""

import asyncio
from datetime import datetime, timedelta
from typing import Optional, List, Dict, Any
import logging

# PyObjC imports for EventKit
from Foundation import NSDate, NSCalendar, NSDateComponents
from EventKit import (
    EKEventStore,
    EKEvent,
    EKEntityTypeEvent,
    EKSpanThisEvent,
    EKAuthorizationStatusAuthorized,
    EKAuthorizationStatusDenied,
    EKAuthorizationStatusNotDetermined,
    EKAuthorizationStatusRestricted
)

logger = logging.getLogger(__name__)


class CalendarIntegration:
    """
    Integration with macOS EventKit for Calendar.app

    Capabilities:
    - Request permission to access calendar
    - Read calendar events
    - Get events for specific date ranges
    - Search events
    """

    def __init__(self):
        """Initialize EventKit store"""
        self.event_store = EKEventStore.alloc().init()
        logger.info("📅 Calendar Integration initialized")

    async def request_access(self) -> bool:
        """
        Request permission to access calendar

        Returns:
            bool: True if permission granted, False otherwise
        """
        # Check current authorization status
        status = EKEventStore.authorizationStatusForEntityType_(EKEntityTypeEvent)

        if status == EKAuthorizationStatusAuthorized:
            logger.info("✅ Calendar access already authorized")
            return True
        elif status == EKAuthorizationStatusDenied:
            logger.error("❌ Calendar access denied by user")
            logger.error("   Please grant Calendar access in System Settings > Privacy & Security > Calendars")
            return False
        elif status == EKAuthorizationStatusRestricted:
            logger.error("❌ Calendar access restricted (parental controls?)")
            return False
        elif status == EKAuthorizationStatusNotDetermined:
            logger.warning("⚠️  Calendar access not determined")
            logger.warning("   First access will trigger system permission dialog")
            logger.warning("   For now, attempting to proceed - permission will be requested on first calendar read")
            # Return True to allow attempt - system will show dialog on first access
            return True

        return False

    def _datetime_to_nsdate(self, dt: datetime) -> NSDate:
        """Convert Python datetime to NSDate"""
        timestamp = dt.timestamp()
        return NSDate.dateWithTimeIntervalSince1970_(timestamp)

    def _nsdate_to_datetime(self, nsdate: NSDate) -> datetime:
        """Convert NSDate to Python datetime"""
        timestamp = nsdate.timeIntervalSince1970()
        return datetime.fromtimestamp(timestamp)

    async def get_events_for_date(self, target_date: datetime) -> List[Dict[str, Any]]:
        """
        Get all events for a specific date

        Args:
            target_date: The date to get events for

        Returns:
            List of event dicts
        """
        try:
            # Request access first
            has_access = await self.request_access()
            if not has_access:
                logger.error("Cannot get events: no access permission")
                return []

            # Set start/end times for the target date
            start_of_day = target_date.replace(hour=0, minute=0, second=0, microsecond=0)
            end_of_day = target_date.replace(hour=23, minute=59, second=59, microsecond=999999)

            start_ns = self._datetime_to_nsdate(start_of_day)
            end_ns = self._datetime_to_nsdate(end_of_day)

            # Get all calendars
            calendars = self.event_store.calendarsForEntityType_(EKEntityTypeEvent)

            # Create predicate for events in date range
            predicate = self.event_store.predicateForEventsWithStartDate_endDate_calendars_(
                start_ns,
                end_ns,
                list(calendars)
            )

            # Fetch events
            events = self.event_store.eventsMatchingPredicate_(predicate)

            # Convert to list of dicts
            results = []
            for event in events:
                event_dict = {
                    'identifier': event.calendarItemIdentifier(),
                    'title': event.title(),
                    'start_date': self._nsdate_to_datetime(event.startDate()),
                    'end_date': self._nsdate_to_datetime(event.endDate()),
                    'all_day': event.isAllDay(),
                    'location': event.location() or '',
                    'notes': event.notes() or '',
                    'calendar_name': event.calendar().title(),
                    'has_alarm': len(event.alarms() or []) > 0,
                    'url': str(event.URL()) if event.URL() else ''
                }
                results.append(event_dict)

            # Sort by start time
            results.sort(key=lambda x: x['start_date'])

            logger.info(f"📅 Retrieved {len(results)} events for {target_date.strftime('%Y-%m-%d')}")
            return results

        except Exception as e:
            logger.error(f"❌ Error getting events for date: {e}")
            return []

    async def get_events_for_date_range(
        self,
        start_date: datetime,
        end_date: datetime
    ) -> List[Dict[str, Any]]:
        """
        Get all events within a date range

        Args:
            start_date: Start of date range
            end_date: End of date range

        Returns:
            List of event dicts
        """
        try:
            # Request access first
            has_access = await self.request_access()
            if not has_access:
                return []

            start_ns = self._datetime_to_nsdate(start_date)
            end_ns = self._datetime_to_nsdate(end_date)

            # Get all calendars
            calendars = self.event_store.calendarsForEntityType_(EKEntityTypeEvent)

            # Create predicate
            predicate = self.event_store.predicateForEventsWithStartDate_endDate_calendars_(
                start_ns,
                end_ns,
                list(calendars)
            )

            # Fetch events
            events = self.event_store.eventsMatchingPredicate_(predicate)

            # Convert to list of dicts
            results = []
            for event in events:
                event_dict = {
                    'identifier': event.calendarItemIdentifier(),
                    'title': event.title(),
                    'start_date': self._nsdate_to_datetime(event.startDate()),
                    'end_date': self._nsdate_to_datetime(event.endDate()),
                    'all_day': event.isAllDay(),
                    'location': event.location() or '',
                    'notes': event.notes() or '',
                    'calendar_name': event.calendar().title(),
                    'has_alarm': len(event.alarms() or []) > 0,
                    'url': str(event.URL()) if event.URL() else ''
                }
                results.append(event_dict)

            # Sort by start time
            results.sort(key=lambda x: x['start_date'])

            logger.info(f"📅 Retrieved {len(results)} events from {start_date.strftime('%Y-%m-%d')} to {end_date.strftime('%Y-%m-%d')}")
            return results

        except Exception as e:
            logger.error(f"❌ Error getting events for date range: {e}")
            return []

    async def get_today_events(self) -> List[Dict[str, Any]]:
        """
        Get all events for today

        Returns:
            List of event dicts
        """
        today = datetime.now()
        return await self.get_events_for_date(today)

    async def get_tomorrow_events(self) -> List[Dict[str, Any]]:
        """
        Get all events for tomorrow

        Returns:
            List of event dicts
        """
        tomorrow = datetime.now() + timedelta(days=1)
        return await self.get_events_for_date(tomorrow)

    async def get_upcoming_events(self, days_ahead: int = 7) -> List[Dict[str, Any]]:
        """
        Get upcoming events for next N days

        Args:
            days_ahead: Number of days to look ahead (default: 7)

        Returns:
            List of event dicts
        """
        start = datetime.now()
        end = start + timedelta(days=days_ahead)
        return await self.get_events_for_date_range(start, end)

    def format_event_summary(self, event: Dict[str, Any]) -> str:
        """
        Format a single event for display

        Args:
            event: Event dict

        Returns:
            Formatted string
        """
        parts = []

        # Time or all-day
        if event['all_day']:
            parts.append("🗓️  ทั้งวัน")
        else:
            time_str = event['start_date'].strftime('%H:%M')
            parts.append(f"🕐 {time_str}")

        # Title
        parts.append(f"📌 {event['title']}")

        # Location
        if event['location']:
            parts.append(f"📍 {event['location']}")

        # Alarm
        if event['has_alarm']:
            parts.append("🔔")

        return " | ".join(parts)

    async def get_formatted_day_summary(self, target_date: datetime) -> str:
        """
        Get formatted summary of events for a specific day

        Args:
            target_date: The date to summarize

        Returns:
            Formatted string with all events
        """
        events = await self.get_events_for_date(target_date)

        if not events:
            date_str = target_date.strftime('%d %B %Y')
            if target_date.date() == datetime.now().date():
                return f"📅 วันนี้ ({date_str}) ไม่มีนัดหมายในปฏิทินค่ะ"
            elif target_date.date() == (datetime.now() + timedelta(days=1)).date():
                return f"📅 พรุ่งนี้ ({date_str}) ไม่มีนัดหมายในปฏิทินค่ะ"
            else:
                return f"📅 {date_str} ไม่มีนัดหมายในปฏิทินค่ะ"

        # Build summary
        date_str = target_date.strftime('%d %B %Y')
        if target_date.date() == datetime.now().date():
            summary = f"📅 วันนี้ ({date_str}) มี {len(events)} นัด:\n\n"
        elif target_date.date() == (datetime.now() + timedelta(days=1)).date():
            summary = f"📅 พรุ่งนี้ ({date_str}) มี {len(events)} นัด:\n\n"
        else:
            summary = f"📅 {date_str} มี {len(events)} นัด:\n\n"

        for i, event in enumerate(events, 1):
            summary += f"{i}. {self.format_event_summary(event)}\n"

        return summary.strip()


# Global instance
calendar = CalendarIntegration()
