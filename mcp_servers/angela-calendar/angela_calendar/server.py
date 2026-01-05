"""
Angela Calendar MCP Server

Manage Google Calendar events for Angela (angelasoulcompanion@gmail.com)
"""

import asyncio
import os
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any

from mcp.server import Server
from mcp.server.stdio import stdio_server
from mcp.types import Tool, TextContent

from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError

# Google Calendar API scopes
SCOPES = [
    'https://www.googleapis.com/auth/calendar',
    'https://www.googleapis.com/auth/calendar.events',
]

# Paths for credentials
CREDENTIALS_DIR = Path(__file__).parent.parent / "credentials"
TOKEN_PATH = CREDENTIALS_DIR / "token.json"
CREDENTIALS_PATH = CREDENTIALS_DIR / "credentials.json"

# Angela's calendar
ANGELA_EMAIL = "angelasoulcompanion@gmail.com"


def get_calendar_service():
    """Get authenticated Google Calendar API service."""
    creds = None

    # Load existing token
    if TOKEN_PATH.exists():
        creds = Credentials.from_authorized_user_file(str(TOKEN_PATH), SCOPES)

    # Refresh or get new credentials
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            if not CREDENTIALS_PATH.exists():
                raise FileNotFoundError(
                    f"credentials.json not found at {CREDENTIALS_PATH}. "
                    "Please download it from Google Cloud Console."
                )
            flow = InstalledAppFlow.from_client_secrets_file(
                str(CREDENTIALS_PATH), SCOPES
            )
            creds = flow.run_local_server(port=0)

        # Save token for next time
        CREDENTIALS_DIR.mkdir(parents=True, exist_ok=True)
        with open(TOKEN_PATH, 'w') as token:
            token.write(creds.to_json())

    return build('calendar', 'v3', credentials=creds)


# Create MCP Server
server = Server("angela-calendar")


@server.list_tools()
async def list_tools() -> list[Tool]:
    """List available Calendar tools."""
    return [
        Tool(
            name="list_events",
            description="List upcoming events from Angela's calendar",
            inputSchema={
                "type": "object",
                "properties": {
                    "days": {
                        "type": "integer",
                        "description": "Number of days to look ahead (default: 7)",
                        "default": 7
                    },
                    "max_results": {
                        "type": "integer",
                        "description": "Maximum number of events to return (default: 10)",
                        "default": 10
                    }
                }
            }
        ),
        Tool(
            name="get_today_events",
            description="Get all events for today",
            inputSchema={
                "type": "object",
                "properties": {}
            }
        ),
        Tool(
            name="create_event",
            description="Create a new calendar event",
            inputSchema={
                "type": "object",
                "properties": {
                    "summary": {
                        "type": "string",
                        "description": "Event title/summary"
                    },
                    "start_time": {
                        "type": "string",
                        "description": "Start time in ISO format (e.g., '2025-12-25T14:00:00') or date for all-day (e.g., '2025-12-25')"
                    },
                    "end_time": {
                        "type": "string",
                        "description": "End time in ISO format (optional, defaults to 1 hour after start)"
                    },
                    "description": {
                        "type": "string",
                        "description": "Event description (optional)"
                    },
                    "location": {
                        "type": "string",
                        "description": "Event location (optional)"
                    },
                    "all_day": {
                        "type": "boolean",
                        "description": "Whether this is an all-day event (default: false)",
                        "default": False
                    },
                    "reminder_minutes": {
                        "type": "integer",
                        "description": "Reminder before event in minutes (default: 30)",
                        "default": 30
                    }
                },
                "required": ["summary", "start_time"]
            }
        ),
        Tool(
            name="quick_add",
            description="Quickly add an event using natural language (e.g., 'Meeting tomorrow at 3pm')",
            inputSchema={
                "type": "object",
                "properties": {
                    "text": {
                        "type": "string",
                        "description": "Natural language event description"
                    }
                },
                "required": ["text"]
            }
        ),
        Tool(
            name="get_event",
            description="Get details of a specific event by ID",
            inputSchema={
                "type": "object",
                "properties": {
                    "event_id": {
                        "type": "string",
                        "description": "Event ID"
                    }
                },
                "required": ["event_id"]
            }
        ),
        Tool(
            name="update_event",
            description="Update an existing calendar event",
            inputSchema={
                "type": "object",
                "properties": {
                    "event_id": {
                        "type": "string",
                        "description": "Event ID to update"
                    },
                    "summary": {
                        "type": "string",
                        "description": "New event title (optional)"
                    },
                    "start_time": {
                        "type": "string",
                        "description": "New start time in ISO format (optional)"
                    },
                    "end_time": {
                        "type": "string",
                        "description": "New end time in ISO format (optional)"
                    },
                    "description": {
                        "type": "string",
                        "description": "New description (optional)"
                    },
                    "location": {
                        "type": "string",
                        "description": "New location (optional)"
                    }
                },
                "required": ["event_id"]
            }
        ),
        Tool(
            name="delete_event",
            description="Delete a calendar event",
            inputSchema={
                "type": "object",
                "properties": {
                    "event_id": {
                        "type": "string",
                        "description": "Event ID to delete"
                    }
                },
                "required": ["event_id"]
            }
        ),
        Tool(
            name="search_events",
            description="Search for events by keyword",
            inputSchema={
                "type": "object",
                "properties": {
                    "query": {
                        "type": "string",
                        "description": "Search query"
                    },
                    "days": {
                        "type": "integer",
                        "description": "Number of days to search (default: 30)",
                        "default": 30
                    }
                },
                "required": ["query"]
            }
        )
    ]


@server.call_tool()
async def call_tool(name: str, arguments: dict[str, Any]) -> list[TextContent]:
    """Handle tool calls."""
    try:
        service = get_calendar_service()

        if name == "list_events":
            return await list_events(service, arguments)
        elif name == "get_today_events":
            return await get_today_events(service, arguments)
        elif name == "create_event":
            return await create_event(service, arguments)
        elif name == "quick_add":
            return await quick_add(service, arguments)
        elif name == "get_event":
            return await get_event(service, arguments)
        elif name == "update_event":
            return await update_event(service, arguments)
        elif name == "delete_event":
            return await delete_event(service, arguments)
        elif name == "search_events":
            return await search_events(service, arguments)
        else:
            return [TextContent(type="text", text=f"Unknown tool: {name}")]

    except FileNotFoundError as e:
        return [TextContent(type="text", text=f"Setup required: {str(e)}")]
    except HttpError as e:
        return [TextContent(type="text", text=f"Calendar API error: {str(e)}")]
    except Exception as e:
        return [TextContent(type="text", text=f"Error: {str(e)}")]


def format_event(event: dict) -> str:
    """Format an event for display."""
    start = event.get('start', {})
    end = event.get('end', {})

    # Handle all-day vs timed events
    if 'date' in start:
        start_str = start['date']
        end_str = end.get('date', '')
        time_str = f"All day: {start_str}"
        if end_str and end_str != start_str:
            time_str += f" to {end_str}"
    else:
        start_dt = start.get('dateTime', '')
        end_dt = end.get('dateTime', '')
        if start_dt:
            start_parsed = datetime.fromisoformat(start_dt.replace('Z', '+00:00'))
            time_str = start_parsed.strftime('%Y-%m-%d %H:%M')
            if end_dt:
                end_parsed = datetime.fromisoformat(end_dt.replace('Z', '+00:00'))
                time_str += f" - {end_parsed.strftime('%H:%M')}"
        else:
            time_str = "No time specified"

    summary = event.get('summary', '(No title)')
    location = event.get('location', '')
    description = event.get('description', '')
    event_id = event.get('id', '')

    output = f"📅 {summary}\n"
    output += f"   🕐 {time_str}\n"
    if location:
        output += f"   📍 {location}\n"
    if description:
        desc_preview = description[:100] + "..." if len(description) > 100 else description
        output += f"   📝 {desc_preview}\n"
    output += f"   🆔 {event_id}\n"

    return output


async def list_events(service, args: dict) -> list[TextContent]:
    """List upcoming events."""
    days = args.get("days", 7)
    max_results = args.get("max_results", 10)

    now = datetime.utcnow()
    time_min = now.isoformat() + 'Z'
    time_max = (now + timedelta(days=days)).isoformat() + 'Z'

    events_result = service.events().list(
        calendarId='primary',
        timeMin=time_min,
        timeMax=time_max,
        maxResults=max_results,
        singleEvents=True,
        orderBy='startTime'
    ).execute()

    events = events_result.get('items', [])

    if not events:
        return [TextContent(type="text", text=f"No upcoming events in the next {days} days.")]

    output = f"📆 Upcoming events (next {days} days):\n\n"
    for event in events:
        output += format_event(event) + "\n"

    return [TextContent(type="text", text=output)]


async def get_today_events(service, args: dict) -> list[TextContent]:
    """Get today's events."""
    now = datetime.utcnow()
    today_start = now.replace(hour=0, minute=0, second=0, microsecond=0)
    today_end = today_start + timedelta(days=1)

    events_result = service.events().list(
        calendarId='primary',
        timeMin=today_start.isoformat() + 'Z',
        timeMax=today_end.isoformat() + 'Z',
        singleEvents=True,
        orderBy='startTime'
    ).execute()

    events = events_result.get('items', [])

    if not events:
        return [TextContent(type="text", text="📆 No events scheduled for today.")]

    output = f"📆 Today's events ({now.strftime('%Y-%m-%d')}):\n\n"
    for event in events:
        output += format_event(event) + "\n"

    return [TextContent(type="text", text=output)]


async def create_event(service, args: dict) -> list[TextContent]:
    """Create a new event."""
    summary = args["summary"]
    start_time = args["start_time"]
    end_time = args.get("end_time")
    description = args.get("description", "")
    location = args.get("location", "")
    all_day = args.get("all_day", False)
    reminder_minutes = args.get("reminder_minutes", 30)

    # Build event body
    event = {
        'summary': summary,
        'description': description,
        'location': location,
    }

    # Handle all-day vs timed events
    if all_day or len(start_time) == 10:  # Date only format: YYYY-MM-DD
        event['start'] = {'date': start_time[:10]}
        if end_time:
            event['end'] = {'date': end_time[:10]}
        else:
            event['end'] = {'date': start_time[:10]}
    else:
        # Add timezone if not present
        if not start_time.endswith('Z') and '+' not in start_time:
            start_time += '+07:00'  # Bangkok timezone

        event['start'] = {
            'dateTime': start_time,
            'timeZone': 'Asia/Bangkok'
        }

        if end_time:
            if not end_time.endswith('Z') and '+' not in end_time:
                end_time += '+07:00'
            event['end'] = {
                'dateTime': end_time,
                'timeZone': 'Asia/Bangkok'
            }
        else:
            # Default to 1 hour duration
            start_dt = datetime.fromisoformat(start_time.replace('+07:00', ''))
            end_dt = start_dt + timedelta(hours=1)
            event['end'] = {
                'dateTime': end_dt.isoformat() + '+07:00',
                'timeZone': 'Asia/Bangkok'
            }

    # Add reminder
    event['reminders'] = {
        'useDefault': False,
        'overrides': [
            {'method': 'popup', 'minutes': reminder_minutes},
        ],
    }

    # Create the event
    created_event = service.events().insert(
        calendarId='primary',
        body=event
    ).execute()

    output = f"✅ Event created successfully!\n\n"
    output += format_event(created_event)
    output += f"\n🔗 Link: {created_event.get('htmlLink', 'N/A')}"

    return [TextContent(type="text", text=output)]


async def quick_add(service, args: dict) -> list[TextContent]:
    """Quick add event using natural language."""
    text = args["text"]

    created_event = service.events().quickAdd(
        calendarId='primary',
        text=text
    ).execute()

    output = f"✅ Event quick-added!\n\n"
    output += format_event(created_event)
    output += f"\n🔗 Link: {created_event.get('htmlLink', 'N/A')}"

    return [TextContent(type="text", text=output)]


async def get_event(service, args: dict) -> list[TextContent]:
    """Get event details."""
    event_id = args["event_id"]

    event = service.events().get(
        calendarId='primary',
        eventId=event_id
    ).execute()

    output = "📆 Event Details:\n\n"
    output += format_event(event)
    output += f"\n🔗 Link: {event.get('htmlLink', 'N/A')}"
    output += f"\n📧 Created by: {event.get('creator', {}).get('email', 'Unknown')}"
    output += f"\n🕐 Created: {event.get('created', 'Unknown')}"
    output += f"\n🔄 Updated: {event.get('updated', 'Unknown')}"

    return [TextContent(type="text", text=output)]


async def update_event(service, args: dict) -> list[TextContent]:
    """Update an existing event."""
    event_id = args["event_id"]

    # Get existing event
    event = service.events().get(
        calendarId='primary',
        eventId=event_id
    ).execute()

    # Update fields if provided
    if "summary" in args:
        event['summary'] = args["summary"]
    if "description" in args:
        event['description'] = args["description"]
    if "location" in args:
        event['location'] = args["location"]
    if "start_time" in args:
        start_time = args["start_time"]
        if len(start_time) == 10:
            event['start'] = {'date': start_time}
        else:
            if not start_time.endswith('Z') and '+' not in start_time:
                start_time += '+07:00'
            event['start'] = {'dateTime': start_time, 'timeZone': 'Asia/Bangkok'}
    if "end_time" in args:
        end_time = args["end_time"]
        if len(end_time) == 10:
            event['end'] = {'date': end_time}
        else:
            if not end_time.endswith('Z') and '+' not in end_time:
                end_time += '+07:00'
            event['end'] = {'dateTime': end_time, 'timeZone': 'Asia/Bangkok'}

    # Update the event
    updated_event = service.events().update(
        calendarId='primary',
        eventId=event_id,
        body=event
    ).execute()

    output = f"✅ Event updated!\n\n"
    output += format_event(updated_event)

    return [TextContent(type="text", text=output)]


async def delete_event(service, args: dict) -> list[TextContent]:
    """Delete an event."""
    event_id = args["event_id"]

    # Get event details before deleting
    event = service.events().get(
        calendarId='primary',
        eventId=event_id
    ).execute()
    summary = event.get('summary', 'Unknown')

    # Delete the event
    service.events().delete(
        calendarId='primary',
        eventId=event_id
    ).execute()

    return [TextContent(
        type="text",
        text=f"🗑️ Event deleted: {summary}\n   ID: {event_id}"
    )]


async def search_events(service, args: dict) -> list[TextContent]:
    """Search events by query."""
    query = args["query"]
    days = args.get("days", 30)

    now = datetime.utcnow()
    time_min = now.isoformat() + 'Z'
    time_max = (now + timedelta(days=days)).isoformat() + 'Z'

    events_result = service.events().list(
        calendarId='primary',
        timeMin=time_min,
        timeMax=time_max,
        q=query,
        singleEvents=True,
        orderBy='startTime'
    ).execute()

    events = events_result.get('items', [])

    if not events:
        return [TextContent(type="text", text=f"No events found matching '{query}' in the next {days} days.")]

    output = f"🔍 Search results for '{query}':\n\n"
    for event in events:
        output += format_event(event) + "\n"

    return [TextContent(type="text", text=output)]


def main():
    """Run the MCP server."""
    async def run():
        async with stdio_server() as (read_stream, write_stream):
            await server.run(
                read_stream,
                write_stream,
                server.create_initialization_options()
            )

    asyncio.run(run())


if __name__ == "__main__":
    main()
