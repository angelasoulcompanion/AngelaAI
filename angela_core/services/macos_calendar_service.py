#!/usr/bin/env python3
"""
macOS Calendar Service - Query Calendar Events using EventKit

Uses PyObjC to access macOS EventKit framework directly from Python
"""

import json
from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional

try:
    import EventKit
    import Foundation
    EVENTKIT_AVAILABLE = True
except ImportError:
    EVENTKIT_AVAILABLE = False
    print("⚠️ EventKit not available. Install with: pip3 install pyobjc-framework-EventKit")


class MacOSCalendarService:
    """
    Service to query macOS Calendar events

    Uses EventKit framework to access user's Calendar data
    """

    def __init__(self):
        if not EVENTKIT_AVAILABLE:
            raise RuntimeError("EventKit framework not available")

        self.event_store = EventKit.EKEventStore.alloc().init()
        self.has_access = False

    def request_access(self) -> bool:
        """
        Request access to Calendar

        Returns:
            True if access granted, False otherwise
        """
        # For macOS 14.0+, use requestFullAccessToEventsWithCompletion
        # Note: This requires user to grant permission in System Settings

        # Since we're in Python, we assume permission was already granted
        # via the Swift app
        self.has_access = True
        return True

    def get_today_events(self) -> Dict[str, Any]:
        """
        Get events for today

        Returns:
            Dictionary with date, events list, and count
        """
        if not self.has_access:
            self.request_access()

        # Get today's date range
        calendar = Foundation.NSCalendar.currentCalendar()
        now = Foundation.NSDate.date()

        start_of_day = calendar.startOfDayForDate_(now)
        end_of_day = calendar.dateByAddingUnit_value_toDate_options_(
            Foundation.NSCalendarUnitDay, 1, start_of_day, 0
        )

        # Query events
        predicate = self.event_store.predicateForEventsWithStartDate_endDate_calendars_(
            start_of_day, end_of_day, None
        )

        events = self.event_store.eventsMatchingPredicate_(predicate)

        # Format events
        formatted_events = [self._format_event(event) for event in events]

        return {
            "date": datetime.now().strftime("%Y-%m-%d"),
            "events": formatted_events,
            "count": len(formatted_events)
        }

    def get_upcoming_events(self, days: int = 7) -> Dict[str, Any]:
        """
        Get upcoming events for next N days

        Args:
            days: Number of days to look ahead

        Returns:
            Dictionary with date range, events list, and count
        """
        if not self.has_access:
            self.request_access()

        # Get date range
        now = Foundation.NSDate.date()
        future = Foundation.NSDate.dateWithTimeIntervalSinceNow_(days * 24 * 3600)

        # Query events
        predicate = self.event_store.predicateForEventsWithStartDate_endDate_calendars_(
            now, future, None
        )

        events = self.event_store.eventsMatchingPredicate_(predicate)

        # Format events
        formatted_events = [self._format_event(event) for event in events]

        return {
            "date": f"Next {days} days",
            "events": formatted_events,
            "count": len(formatted_events)
        }

    def search_events(self, query: str, days: int = 30) -> Dict[str, Any]:
        """
        Search for events matching query

        Args:
            query: Search query string
            days: Number of days to search

        Returns:
            Dictionary with search results
        """
        if not self.has_access:
            self.request_access()

        # Get date range
        now = Foundation.NSDate.date()
        future = Foundation.NSDate.dateWithTimeIntervalSinceNow_(days * 24 * 3600)

        # Query all events
        predicate = self.event_store.predicateForEventsWithStartDate_endDate_calendars_(
            now, future, None
        )

        events = self.event_store.eventsMatchingPredicate_(predicate)

        # Filter by query
        query_lower = query.lower()
        filtered_events = []

        for event in events:
            title = str(event.title() or "").lower()
            location = str(event.location() or "").lower()
            notes = str(event.notes() or "").lower()

            if query_lower in title or query_lower in location or query_lower in notes:
                filtered_events.append(self._format_event(event))

        return {
            "date": f"Search results for '{query}'",
            "events": filtered_events,
            "count": len(filtered_events)
        }

    def _format_event(self, event) -> Dict[str, str]:
        """
        Format EKEvent to dictionary

        Args:
            event: EKEvent object

        Returns:
            Dictionary with event data
        """
        # Convert NSDate to datetime
        start_date = datetime.fromtimestamp(event.startDate().timeIntervalSince1970())
        end_date = datetime.fromtimestamp(event.endDate().timeIntervalSince1970())

        return {
            "title": str(event.title() or "Untitled"),
            "start": start_date.strftime("%Y-%m-%d %H:%M:%S"),
            "end": end_date.strftime("%Y-%m-%d %H:%M:%S"),
            "location": str(event.location() or ""),
            "notes": str(event.notes() or "")
        }

    def get_events_for_week(self, week_offset: int = 0) -> Dict[str, Any]:
        """
        Get events for a specific week

        Args:
            week_offset: Week offset (0 = this week, 1 = next week, -1 = last week)

        Returns:
            Dictionary with week events
        """
        if not self.has_access:
            self.request_access()

        # Calculate week start (Monday) and end (Sunday)
        calendar = Foundation.NSCalendar.currentCalendar()
        now = Foundation.NSDate.date()

        # Get start of week (Monday)
        components = calendar.components_fromDate_(
            Foundation.NSCalendarUnitWeekday | Foundation.NSCalendarUnitDay |
            Foundation.NSCalendarUnitMonth | Foundation.NSCalendarUnitYear,
            now
        )

        weekday = components.weekday()
        days_from_monday = (weekday + 5) % 7

        start_of_week = calendar.dateByAddingUnit_value_toDate_options_(
            Foundation.NSCalendarUnitDay,
            -days_from_monday + (week_offset * 7),
            now,
            0
        )

        end_of_week = calendar.dateByAddingUnit_value_toDate_options_(
            Foundation.NSCalendarUnitDay, 7, start_of_week, 0
        )

        # Query events
        predicate = self.event_store.predicateForEventsWithStartDate_endDate_calendars_(
            start_of_week, end_of_week, None
        )

        events = self.event_store.eventsMatchingPredicate_(predicate)

        # Format events
        formatted_events = [self._format_event(event) for event in events]

        week_name = "This week" if week_offset == 0 else f"Week {week_offset:+d}"

        return {
            "date": week_name,
            "events": formatted_events,
            "count": len(formatted_events)
        }


# Singleton instance
try:
    calendar_service = MacOSCalendarService()
except Exception as e:
    print(f"⚠️ Failed to initialize macOS Calendar Service: {e}")
    calendar_service = None


# CLI interface for testing
if __name__ == "__main__":
    import sys

    if not calendar_service:
        print("❌ Calendar service not available")
        sys.exit(1)

    command = sys.argv[1] if len(sys.argv) > 1 else "today"

    try:
        if command == "today":
            result = calendar_service.get_today_events()
        elif command == "upcoming":
            days = int(sys.argv[2]) if len(sys.argv) > 2 else 7
            result = calendar_service.get_upcoming_events(days)
        elif command == "search":
            query = sys.argv[2] if len(sys.argv) > 2 else ""
            result = calendar_service.search_events(query)
        elif command == "week":
            offset = int(sys.argv[2]) if len(sys.argv) > 2 else 0
            result = calendar_service.get_events_for_week(offset)
        else:
            print(f"Unknown command: {command}")
            print("Usage: python3 macos_calendar_service.py [today|upcoming|search|week] [args]")
            sys.exit(1)

        # Print result as JSON
        print(json.dumps(result, indent=2, ensure_ascii=False))

    except Exception as e:
        print(f"❌ Error: {e}", file=sys.stderr)
        sys.exit(1)
