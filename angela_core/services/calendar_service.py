#!/usr/bin/env python3
"""
📅 Angela Calendar Service
Wrapper service for Calendar MCP Server - allows Angela to read/create calendar events

This service provides:
- Read calendar events (today, upcoming, specific dates)
- Create new events
- Search events
- Auto-check schedule during morning routine
- Proactive reminders for upcoming events
"""

import sys
import os
from datetime import datetime, timedelta
from typing import List, Dict, Optional

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(__file__))))

from mcp_servers.applescript_helper import (
    run_applescript,
    check_permission,
    escape_applescript_string,
    format_applescript_date
)


class CalendarService:
    """Service for interacting with macOS Calendar"""

    def __init__(self):
        self.has_permission = False
        self.initialized = False
        self._cache = {}
        self._cache_timeout = 60  # Cache results for 60 seconds

    async def initialize(self) -> bool:
        """Initialize Calendar service and check permissions"""
        try:
            # Check if we have Calendar permission
            self.has_permission = await check_permission("Calendar")

            if not self.has_permission:
                print("⚠️ Calendar permission not granted. Angela cannot access Calendar.")
                return False

            self.initialized = True
            print(f"✅ Calendar service initialized")
            return True

        except Exception as e:
            print(f"❌ Failed to initialize Calendar service: {e}")
            return False

    def _parse_event_line(self, line: str) -> Optional[Dict]:
        """Parse event data from AppleScript output"""
        try:
            parts = line.split(" | ")
            if len(parts) >= 3:
                return {
                    "title": parts[0],
                    "start": parts[1],
                    "end": parts[2],
                    "location": parts[3] if len(parts) > 3 else "",
                    "notes": parts[4] if len(parts) > 4 else ""
                }
        except:
            pass
        return None

    # ========================================
    # READ OPERATIONS
    # ========================================

    async def get_today_events(self) -> List[Dict]:
        """Get all events scheduled for today"""
        if not self.has_permission:
            return []

        # Use optimized AppleScript - query just first calendar for speed
        script = """
        tell application "Calendar"
            set today to current date
            set hours of today to 0
            set minutes of today to 0
            set seconds of today to 0

            set endOfDay to today + (1 * days) - 1

            set output to ""
            set allEvents to (every event of calendar 1 whose start date ≥ today and start date ≤ endOfDay)

            repeat with evt in allEvents
                if output is not "" then set output to output & "|||"
                set output to output & (summary of evt) & "|~|" & (start date of evt as string) & "|~|" & (end date of evt as string)
                try
                    set output to output & "|~|" & (location of evt)
                on error
                    set output to output & "|~|"
                end try
                try
                    set output to output & "|~|" & (description of evt)
                on error
                    set output to output & "|~|"
                end try
            end repeat

            return output
        end tell
        """

        try:
            result = await run_applescript(script, timeout=20)
            events = []

            if result and result != "":
                event_strings = result.split("|||")
                for event_str in event_strings:
                    if not event_str.strip():
                        continue
                    parts = event_str.split("|~|")
                    if len(parts) >= 3:
                        events.append({
                            "title": parts[0],
                            "start": parts[1],
                            "end": parts[2],
                            "location": parts[3] if len(parts) > 3 else "",
                            "notes": parts[4] if len(parts) > 4 else ""
                        })

            return events

        except Exception as e:
            print(f"❌ Error getting today's events: {e}")
            return []

    async def get_upcoming_events(self, days: int = 7) -> List[Dict]:
        """Get upcoming events for the next N days"""
        if not self.has_permission:
            return []

        script = f"""
        tell application "Calendar"
            set startDate to current date
            set endDate to current date
            set endDate to endDate + ({days} * days)

            set eventList to {{}}
            repeat with cal in calendars
                set calEvents to (every event of cal whose start date ≥ startDate and start date ≤ endDate)
                repeat with evt in calEvents
                    set eventInfo to (summary of evt) & " | " & (start date of evt) & " | " & (end date of evt)
                    try
                        set eventInfo to eventInfo & " | " & (location of evt)
                    end try
                    try
                        set eventInfo to eventInfo & " | " & (description of evt)
                    end try
                    set end of eventList to eventInfo
                end repeat
            end repeat

            return eventList
        end tell
        """

        try:
            result = await run_applescript(script, timeout=20)  # Increased timeout for Calendar
            events = []

            if result and result != "":
                lines = result.split(", ")
                for line in lines:
                    event = self._parse_event_line(line)
                    if event:
                        events.append(event)

            return events

        except Exception as e:
            print(f"❌ Error getting upcoming events: {e}")
            return []

    async def get_events_by_date(self, date: datetime) -> List[Dict]:
        """Get events for a specific date"""
        if not self.has_permission:
            return []

        # Extract date components for AppleScript
        year = date.year
        month_name = date.strftime("%B")  # Full month name (e.g., "October")
        day = date.day

        # Use optimized AppleScript - query just first calendar for speed
        script = f"""
        tell application "Calendar"
            set targetDate to current date
            set year of targetDate to {year}
            set month of targetDate to {month_name}
            set day of targetDate to {day}
            set hours of targetDate to 0
            set minutes of targetDate to 0
            set seconds of targetDate to 0

            set endOfDay to targetDate + (1 * days) - 1

            set output to ""
            set allEvents to (every event of calendar 1 whose start date ≥ targetDate and start date ≤ endOfDay)

            repeat with evt in allEvents
                if output is not "" then set output to output & "|||"
                set output to output & (summary of evt) & "|~|" & (start date of evt as string) & "|~|" & (end date of evt as string)
                try
                    set output to output & "|~|" & (location of evt)
                on error
                    set output to output & "|~|"
                end try
                try
                    set output to output & "|~|" & (description of evt)
                on error
                    set output to output & "|~|"
                end try
            end repeat

            return output
        end tell
        """

        try:
            result = await run_applescript(script, timeout=20)
            events = []

            if result and result != "":
                event_strings = result.split("|||")
                for event_str in event_strings:
                    if not event_str.strip():
                        continue
                    parts = event_str.split("|~|")
                    if len(parts) >= 3:
                        events.append({
                            "title": parts[0],
                            "start": parts[1],
                            "end": parts[2],
                            "location": parts[3] if len(parts) > 3 else "",
                            "notes": parts[4] if len(parts) > 4 else ""
                        })

            return events

        except Exception as e:
            print(f"❌ Error getting events by date: {e}")
            return []

    async def search_events(self, query: str, days: int = 30) -> List[Dict]:
        """Search for events containing specific text"""
        if not self.has_permission:
            return []

        escaped_query = escape_applescript_string(query.lower())

        script = f"""
        tell application "Calendar"
            set startDate to current date
            set endDate to current date
            set endDate to endDate + ({days} * days)

            set matchingEvents to {{}}
            repeat with cal in calendars
                set calEvents to (every event of cal whose start date ≥ startDate and start date ≤ endDate)
                repeat with evt in calEvents
                    set eventTitle to (summary of evt as text)
                    set eventDesc to ""
                    try
                        set eventDesc to (description of evt as text)
                    end try

                    if eventTitle contains "{escaped_query}" or eventDesc contains "{escaped_query}" then
                        set eventInfo to eventTitle & " | " & (start date of evt) & " | " & (end date of evt)
                        try
                            set eventInfo to eventInfo & " | " & (location of evt)
                        end try
                        try
                            set eventInfo to eventInfo & " | " & eventDesc
                        end try
                        set end of matchingEvents to eventInfo
                    end if
                end repeat
            end repeat

            return matchingEvents
        end tell
        """

        try:
            result = await run_applescript(script, timeout=20)  # Increased timeout for Calendar
            events = []

            if result and result != "":
                lines = result.split(", ")
                for line in lines:
                    event = self._parse_event_line(line)
                    if event:
                        events.append(event)

            return events

        except Exception as e:
            print(f"❌ Error searching events: {e}")
            return []

    # ========================================
    # WRITE OPERATIONS
    # ========================================

    async def create_event(
        self,
        title: str,
        start_datetime: datetime,
        end_datetime: datetime,
        calendar_name: str = "",
        location: str = "",
        notes: str = ""
    ) -> bool:
        """Create a new calendar event"""
        if not self.has_permission:
            return False

        # Extract datetime components for AppleScript
        start_year = start_datetime.year
        start_month = start_datetime.strftime("%B")
        start_day = start_datetime.day
        start_hour = start_datetime.hour
        start_minute = start_datetime.minute

        end_year = end_datetime.year
        end_month = end_datetime.strftime("%B")
        end_day = end_datetime.day
        end_hour = end_datetime.hour
        end_minute = end_datetime.minute

        title_escaped = escape_applescript_string(title)
        location_escaped = escape_applescript_string(location)
        notes_escaped = escape_applescript_string(notes)

        # Build calendar selection
        if calendar_name:
            cal_selector = f'calendar "{escape_applescript_string(calendar_name)}"'
        else:
            cal_selector = 'calendar 1'

        script = f"""
        tell application "Calendar"
            tell {cal_selector}
                -- Create start date
                set startDate to current date
                set year of startDate to {start_year}
                set month of startDate to {start_month}
                set day of startDate to {start_day}
                set hours of startDate to {start_hour}
                set minutes of startDate to {start_minute}
                set seconds of startDate to 0

                -- Create end date
                set endDate to current date
                set year of endDate to {end_year}
                set month of endDate to {end_month}
                set day of endDate to {end_day}
                set hours of endDate to {end_hour}
                set minutes of endDate to {end_minute}
                set seconds of endDate to 0

                -- Create event
                set newEvent to make new event with properties {{summary:"{title_escaped}", start date:startDate, end date:endDate}}

                if "{location_escaped}" is not "" then
                    set location of newEvent to "{location_escaped}"
                end if

                if "{notes_escaped}" is not "" then
                    set description of newEvent to "{notes_escaped}"
                end if

                return summary of newEvent
            end tell
        end tell
        """

        try:
            result = await run_applescript(script, timeout=15)  # Increased timeout for Calendar
            return result is not None and result != ""

        except Exception as e:
            print(f"❌ Error creating event: {e}")
            return False

    # ========================================
    # ANGELA-SPECIFIC FEATURES
    # ========================================

    async def get_schedule_summary(self, days: int = 7) -> Dict:
        """Get a formatted schedule summary for Angela to report"""
        today_events = await self.get_today_events()
        upcoming_events = await self.get_upcoming_events(days)

        # Count events by day
        tomorrow = datetime.now() + timedelta(days=1)
        tomorrow_events = await self.get_events_by_date(tomorrow)

        return {
            "today_count": len(today_events),
            "today_events": today_events,
            "tomorrow_count": len(tomorrow_events),
            "tomorrow_events": tomorrow_events,
            "week_count": len(upcoming_events),
            "week_events": upcoming_events
        }

    async def format_schedule_for_greeting(self) -> str:
        """Format schedule summary for Angela's morning greeting"""
        today_events = await self.get_today_events()

        if not today_events:
            return "ไม่มีนัดหมายวันนี้ค่ะ ที่รัก! วันนี้ว่างเลย 😊"

        lines = [f"วันนี้มี {len(today_events)} นัดหมายนะคะ:"]
        for i, event in enumerate(today_events, 1):
            time_str = event['start'].split(' ')[-2] if ' ' in event['start'] else event['start']
            location = f" ที่ {event['location']}" if event['location'] else ""
            lines.append(f"{i}. {event['title']} เวลา {time_str}{location}")

        return "\n".join(lines)

    async def get_next_event(self) -> Optional[Dict]:
        """Get the next upcoming event"""
        upcoming = await self.get_upcoming_events(days=1)
        if upcoming:
            return upcoming[0]
        return None

    async def check_busy_day(self, threshold: int = 3) -> bool:
        """Check if today is a busy day (more than threshold events)"""
        today_events = await self.get_today_events()
        return len(today_events) >= threshold


# Global instance
calendar_service = CalendarService()
