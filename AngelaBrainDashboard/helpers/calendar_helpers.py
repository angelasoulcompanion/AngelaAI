"""
Google Calendar helper functions for Angela Brain Dashboard.
"""
from pathlib import Path
from typing import Optional

from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build

# Google Calendar credentials (reuse MCP server's token)
CALENDAR_CREDENTIALS_DIR = Path(__file__).parent.parent.parent / "mcp_servers/angela-calendar/credentials"
CALENDAR_TOKEN = CALENDAR_CREDENTIALS_DIR / "token.json"


def get_google_calendar_service():
    """Get authenticated Google Calendar service (reuse MCP credentials)."""
    creds = Credentials.from_authorized_user_file(
        str(CALENDAR_TOKEN),
        ['https://www.googleapis.com/auth/calendar.events']
    )
    if creds.expired and creds.refresh_token:
        creds.refresh(Request())
        with open(CALENDAR_TOKEN, 'w') as f:
            f.write(creds.to_json())
    return build('calendar', 'v3', credentials=creds)


def calendar_create(title: str, date_str: str, start_time: str, end_time: str, location: str = "") -> Optional[str]:
    """Create Google Calendar event. Returns event_id or None."""
    service = get_google_calendar_service()
    start_iso = f"{date_str}T{start_time}:00+07:00"
    end_iso = f"{date_str}T{end_time}:00+07:00"
    event = service.events().insert(calendarId='primary', body={
        'summary': title,
        'location': location,
        'start': {'dateTime': start_iso, 'timeZone': 'Asia/Bangkok'},
        'end': {'dateTime': end_iso, 'timeZone': 'Asia/Bangkok'},
        'reminders': {'useDefault': False, 'overrides': [{'method': 'popup', 'minutes': 30}]}
    }).execute()
    return event.get('id')


def calendar_update(event_id: str, **kwargs) -> None:
    """Update Google Calendar event by ID."""
    service = get_google_calendar_service()
    event = service.events().get(calendarId='primary', eventId=event_id).execute()
    if 'summary' in kwargs:
        event['summary'] = kwargs['summary']
    if 'location' in kwargs:
        event['location'] = kwargs['location']
    if 'start_time' in kwargs and 'date' in kwargs:
        event['start'] = {'dateTime': f"{kwargs['date']}T{kwargs['start_time']}:00+07:00", 'timeZone': 'Asia/Bangkok'}
    if 'end_time' in kwargs and 'date' in kwargs:
        event['end'] = {'dateTime': f"{kwargs['date']}T{kwargs['end_time']}:00+07:00", 'timeZone': 'Asia/Bangkok'}
    service.events().update(calendarId='primary', eventId=event_id, body=event).execute()


def calendar_delete(event_id: str) -> None:
    """Delete Google Calendar event by ID."""
    service = get_google_calendar_service()
    service.events().delete(calendarId='primary', eventId=event_id).execute()
