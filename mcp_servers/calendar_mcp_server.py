#!/usr/bin/env python3
"""
📅 macOS Calendar MCP Server
Provides access to macOS Calendar app for Angela

This MCP server allows Angela to:
- View upcoming events and appointments
- Search calendar events
- Create new events
- Get David's schedule

Usage:
    python3 calendar_mcp_server.py

Note: Requires Calendar permission from macOS System Preferences
"""

from fastmcp import FastMCP
import sys
import os
from datetime import datetime, timedelta
import json

# Add parent directory to path
sys.path.insert(0, os.path.dirname(__file__))

from mcp_servers.applescript_helper import (
    run_applescript,
    check_permission,
    check_app_running,
    format_applescript_date,
    escape_applescript_string
)

# Initialize MCP server
mcp = FastMCP("macOS Calendar Access", version="1.0.0")

# ========================================
# HELPER FUNCTIONS
# ========================================

def parse_event_line(line: str) -> dict:
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


async def get_calendar_names() -> list:
    """Get list of all calendar names"""
    script = """
    tell application "Calendar"
        set calNames to {}
        repeat with cal in calendars
            set end of calNames to name of cal
        end repeat
        return calNames
    end tell
    """
    try:
        result = await run_applescript(script)
        if result:
            return [name.strip() for name in result.split(",")]
        return []
    except:
        return []

# ========================================
# TOOLS - Calendar Events
# ========================================

@mcp.tool()
async def get_calendars() -> dict:
    """
    Get list of all calendars in Calendar app.

    Returns:
        Dictionary with calendar names and count
    """
    has_permission = await check_permission("Calendar")
    if not has_permission:
        return {
            "error": "Calendar permission denied",
            "message": "Please grant Calendar access in System Preferences → Security & Privacy → Automation"
        }

    try:
        calendars = await get_calendar_names()
        return {
            "calendars": calendars,
            "count": len(calendars),
            "timestamp": datetime.now().isoformat()
        }
    except Exception as e:
        return {"error": str(e)}


@mcp.tool()
async def get_today_events() -> dict:
    """
    Get all events scheduled for today.

    Returns:
        Dictionary with today's events
    """
    has_permission = await check_permission("Calendar")
    if not has_permission:
        return {
            "error": "Calendar permission denied",
            "message": "Please grant Calendar access in System Preferences"
        }

    script = """
    tell application "Calendar"
        set today to current date
        set startOfDay to today
        set time of startOfDay to 0
        set endOfDay to today
        set time of endOfDay to (24 * 60 * 60) - 1

        set eventList to {}
        repeat with cal in calendars
            set calEvents to (every event of cal whose start date ≥ startOfDay and start date ≤ endOfDay)
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
        result = await run_applescript(script)
        events = []

        if result and result != "":
            lines = result.split(", ")
            for line in lines:
                event = parse_event_line(line)
                if event:
                    events.append(event)

        return {
            "date": datetime.now().strftime("%Y-%m-%d"),
            "events": events,
            "count": len(events),
            "timestamp": datetime.now().isoformat()
        }
    except Exception as e:
        return {"error": str(e)}


@mcp.tool()
async def get_upcoming_events(days: int = 7) -> dict:
    """
    Get upcoming events for the next N days.

    Args:
        days: Number of days to look ahead (default: 7)

    Returns:
        Dictionary with upcoming events
    """
    has_permission = await check_permission("Calendar")
    if not has_permission:
        return {
            "error": "Calendar permission denied",
            "message": "Please grant Calendar access in System Preferences"
        }

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
        result = await run_applescript(script)
        events = []

        if result and result != "":
            lines = result.split(", ")
            for line in lines:
                event = parse_event_line(line)
                if event:
                    events.append(event)

        return {
            "period": f"Next {days} days",
            "start_date": datetime.now().strftime("%Y-%m-%d"),
            "end_date": (datetime.now() + timedelta(days=days)).strftime("%Y-%m-%d"),
            "events": events,
            "count": len(events),
            "timestamp": datetime.now().isoformat()
        }
    except Exception as e:
        return {"error": str(e)}


@mcp.tool()
async def get_events_by_date(date: str) -> dict:
    """
    Get events for a specific date.

    Args:
        date: Date in YYYY-MM-DD format

    Returns:
        Dictionary with events for the specified date
    """
    has_permission = await check_permission("Calendar")
    if not has_permission:
        return {
            "error": "Calendar permission denied",
            "message": "Please grant Calendar access in System Preferences"
        }

    try:
        target_date = datetime.strptime(date, "%Y-%m-%d")
        applescript_date = format_applescript_date(date)
    except ValueError:
        return {"error": f"Invalid date format: {date}. Use YYYY-MM-DD"}

    script = f"""
    tell application "Calendar"
        set targetDate to date "{applescript_date}"
        set startOfDay to targetDate
        set time of startOfDay to 0
        set endOfDay to targetDate
        set time of endOfDay to (24 * 60 * 60) - 1

        set eventList to {{}}
        repeat with cal in calendars
            set calEvents to (every event of cal whose start date ≥ startOfDay and start date ≤ endOfDay)
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
        result = await run_applescript(script)
        events = []

        if result and result != "":
            lines = result.split(", ")
            for line in lines:
                event = parse_event_line(line)
                if event:
                    events.append(event)

        return {
            "date": date,
            "events": events,
            "count": len(events),
            "timestamp": datetime.now().isoformat()
        }
    except Exception as e:
        return {"error": str(e)}


@mcp.tool()
async def search_events(query: str, days: int = 30) -> dict:
    """
    Search for events containing specific text.

    Args:
        query: Search text (searches in title and notes)
        days: How many days ahead to search (default: 30)

    Returns:
        Dictionary with matching events
    """
    has_permission = await check_permission("Calendar")
    if not has_permission:
        return {
            "error": "Calendar permission denied",
            "message": "Please grant Calendar access in System Preferences"
        }

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

                -- Search in title and description
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
        result = await run_applescript(script)
        events = []

        if result and result != "":
            lines = result.split(", ")
            for line in lines:
                event = parse_event_line(line)
                if event:
                    events.append(event)

        return {
            "query": query,
            "events": events,
            "count": len(events),
            "timestamp": datetime.now().isoformat()
        }
    except Exception as e:
        return {"error": str(e)}


@mcp.tool()
async def create_event(
    title: str,
    start_datetime: str,
    end_datetime: str,
    calendar_name: str = "",
    location: str = "",
    notes: str = ""
) -> dict:
    """
    Create a new calendar event.

    Args:
        title: Event title/summary
        start_datetime: Start date/time in YYYY-MM-DD HH:MM:SS format
        end_datetime: End date/time in YYYY-MM-DD HH:MM:SS format
        calendar_name: Which calendar to add to (optional, uses default)
        location: Event location (optional)
        notes: Event notes/description (optional)

    Returns:
        Dictionary with creation status
    """
    has_permission = await check_permission("Calendar")
    if not has_permission:
        return {
            "error": "Calendar permission denied",
            "message": "Please grant Calendar access in System Preferences"
        }

    try:
        start_as = format_applescript_date(start_datetime)
        end_as = format_applescript_date(end_datetime)
        title_escaped = escape_applescript_string(title)
        location_escaped = escape_applescript_string(location)
        notes_escaped = escape_applescript_string(notes)
    except Exception as e:
        return {"error": f"Invalid date format: {e}"}

    # Build calendar selection
    if calendar_name:
        cal_selector = f'calendar "{escape_applescript_string(calendar_name)}"'
    else:
        cal_selector = 'calendar 1'

    script = f"""
    tell application "Calendar"
        tell {cal_selector}
            set newEvent to make new event with properties {{summary:"{title_escaped}", start date:date "{start_as}", end date:date "{end_as}"}}

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
        result = await run_applescript(script)
        return {
            "success": True,
            "event_title": result,
            "start": start_datetime,
            "end": end_datetime,
            "location": location,
            "notes": notes,
            "timestamp": datetime.now().isoformat()
        }
    except Exception as e:
        return {
            "success": False,
            "error": str(e)
        }

# ========================================
# RESOURCES - Readable Calendar Views
# ========================================

@mcp.resource("calendar://today")
async def today_resource() -> str:
    """Today's events as readable text"""
    result = await get_today_events()

    if "error" in result:
        return f"❌ Error: {result['error']}"

    lines = [f"# 📅 Today's Schedule - {result['date']}\n"]

    if result['count'] == 0:
        lines.append("✅ No events scheduled for today!\n")
    else:
        for event in result['events']:
            lines.append(f"## {event['title']}")
            lines.append(f"⏰ {event['start']} → {event['end']}")
            if event.get('location'):
                lines.append(f"📍 {event['location']}")
            if event.get('notes'):
                lines.append(f"📝 {event['notes']}")
            lines.append("")

    return "\n".join(lines)


@mcp.resource("calendar://week")
async def week_resource() -> str:
    """This week's events as readable text"""
    result = await get_upcoming_events(7)

    if "error" in result:
        return f"❌ Error: {result['error']}"

    lines = [f"# 📅 This Week's Schedule ({result['start_date']} to {result['end_date']})\n"]

    if result['count'] == 0:
        lines.append("✅ No events scheduled this week!\n")
    else:
        for event in result['events']:
            lines.append(f"## {event['title']}")
            lines.append(f"⏰ {event['start']} → {event['end']}")
            if event.get('location'):
                lines.append(f"📍 {event['location']}")
            if event.get('notes'):
                lines.append(f"📝 {event['notes']}")
            lines.append("")

    return "\n".join(lines)


@mcp.resource("calendar://summary")
async def summary_resource() -> str:
    """Calendar summary overview"""
    has_permission = await check_permission("Calendar")

    if not has_permission:
        return "❌ Calendar permission denied. Please grant access in System Preferences."

    calendars_result = await get_calendars()
    today_result = await get_today_events()
    week_result = await get_upcoming_events(7)

    lines = ["# 📅 Calendar Summary\n"]
    lines.append(f"**Calendars:** {calendars_result.get('count', 0)}")
    lines.append(f"**Today's events:** {today_result.get('count', 0)}")
    lines.append(f"**This week:** {week_result.get('count', 0)}")
    lines.append(f"\n**Last updated:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

    return "\n".join(lines)

# ========================================
# MAIN - Run Server
# ========================================

if __name__ == "__main__":
    print("\n" + "="*60)
    print("📅 macOS Calendar MCP Server")
    print("="*60)
    print("\n🔐 Checking Calendar permissions...")

    import asyncio
    has_perm = asyncio.run(check_permission("Calendar"))

    if has_perm:
        print("✅ Calendar access granted!")
    else:
        print("⚠️  Calendar permission required!")
        print("   Please grant access in System Preferences → Security & Privacy")

    print("\n✨ Server ready! Waiting for connection...\n")

    # Run MCP server (stdio transport by default)
    mcp.run()
