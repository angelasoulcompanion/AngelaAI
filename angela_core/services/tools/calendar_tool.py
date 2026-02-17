"""
Calendar Tools — List/create/get events via Google Calendar API.

Uses shared google_auth for daemon compatibility.

By: Angela 💜
Created: 2026-02-17
"""

import asyncio
import logging
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any, Dict

from angela_core.services.tools.base_tool import AngelaTool, ToolResult

logger = logging.getLogger(__name__)

CREDENTIALS_DIR = Path(__file__).parents[3] / "mcp_servers" / "angela-calendar"


def _get_calendar_service():
    from mcp_servers.shared.google_auth import get_google_service
    return get_google_service("calendar", CREDENTIALS_DIR)


class ListEventsTool(AngelaTool):
    """List upcoming calendar events."""

    @property
    def name(self) -> str:
        return "list_calendar_events"

    @property
    def description(self) -> str:
        return "List upcoming events from David's Google Calendar"

    @property
    def parameters_schema(self) -> Dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "days_ahead": {"type": "integer", "description": "How many days ahead to look", "default": 7},
                "max_results": {"type": "integer", "description": "Max events to return", "default": 10},
            },
        }

    @property
    def category(self) -> str:
        return "calendar"

    async def execute(self, **params) -> ToolResult:
        days_ahead = params.get("days_ahead", 7)
        max_results = params.get("max_results", 10)

        try:
            service = await asyncio.to_thread(_get_calendar_service)
            now = datetime.utcnow().isoformat() + "Z"
            end = (datetime.utcnow() + timedelta(days=days_ahead)).isoformat() + "Z"

            result = await asyncio.to_thread(
                lambda: service.events().list(
                    calendarId="primary",
                    timeMin=now, timeMax=end,
                    maxResults=max_results,
                    singleEvents=True,
                    orderBy="startTime",
                ).execute()
            )

            events = []
            for event in result.get("items", []):
                start = event.get("start", {}).get("dateTime", event.get("start", {}).get("date", ""))
                end_time = event.get("end", {}).get("dateTime", event.get("end", {}).get("date", ""))
                events.append({
                    "id": event.get("id"),
                    "summary": event.get("summary", "No title"),
                    "start": start,
                    "end": end_time,
                    "location": event.get("location", ""),
                })

            return ToolResult(success=True, data={"events": events, "count": len(events)})
        except Exception as e:
            logger.error("ListEvents failed: %s", e)
            return ToolResult(success=False, error=str(e))


class GetTodayEventsTool(AngelaTool):
    """Get today's calendar events."""

    @property
    def name(self) -> str:
        return "get_today_events"

    @property
    def description(self) -> str:
        return "Get all calendar events for today"

    @property
    def parameters_schema(self) -> Dict[str, Any]:
        return {"type": "object", "properties": {}}

    @property
    def category(self) -> str:
        return "calendar"

    async def execute(self, **params) -> ToolResult:
        try:
            service = await asyncio.to_thread(_get_calendar_service)
            today_start = datetime.utcnow().replace(hour=0, minute=0, second=0).isoformat() + "Z"
            today_end = datetime.utcnow().replace(hour=23, minute=59, second=59).isoformat() + "Z"

            result = await asyncio.to_thread(
                lambda: service.events().list(
                    calendarId="primary",
                    timeMin=today_start, timeMax=today_end,
                    singleEvents=True,
                    orderBy="startTime",
                ).execute()
            )

            events = []
            for event in result.get("items", []):
                start = event.get("start", {}).get("dateTime", event.get("start", {}).get("date", ""))
                events.append({
                    "summary": event.get("summary", "No title"),
                    "start": start,
                    "location": event.get("location", ""),
                })

            return ToolResult(success=True, data={"events": events, "count": len(events)})
        except Exception as e:
            logger.error("GetTodayEvents failed: %s", e)
            return ToolResult(success=False, error=str(e))


class CreateEventTool(AngelaTool):
    """Create a new calendar event."""

    @property
    def name(self) -> str:
        return "create_calendar_event"

    @property
    def description(self) -> str:
        return "Create a new event on David's Google Calendar"

    @property
    def parameters_schema(self) -> Dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "summary": {"type": "string", "description": "Event title"},
                "start_time": {"type": "string", "description": "Start time in ISO 8601 format"},
                "end_time": {"type": "string", "description": "End time in ISO 8601 format"},
                "location": {"type": "string", "description": "Event location"},
                "description": {"type": "string", "description": "Event description"},
            },
            "required": ["summary", "start_time", "end_time"],
        }

    @property
    def category(self) -> str:
        return "calendar"

    @property
    def requires_confirmation(self) -> bool:
        return True

    async def execute(self, **params) -> ToolResult:
        summary = params.get("summary", "")
        start_time = params.get("start_time", "")
        end_time = params.get("end_time", "")

        if not summary or not start_time or not end_time:
            return ToolResult(success=False, error="Missing required fields")

        try:
            service = await asyncio.to_thread(_get_calendar_service)
            event_body = {
                "summary": summary,
                "start": {"dateTime": start_time, "timeZone": "Asia/Bangkok"},
                "end": {"dateTime": end_time, "timeZone": "Asia/Bangkok"},
            }
            if params.get("location"):
                event_body["location"] = params["location"]
            if params.get("description"):
                event_body["description"] = params["description"]

            result = await asyncio.to_thread(
                lambda: service.events().insert(
                    calendarId="primary", body=event_body
                ).execute()
            )

            return ToolResult(success=True, data={
                "event_id": result.get("id"),
                "summary": summary,
                "link": result.get("htmlLink", ""),
            })
        except Exception as e:
            logger.error("CreateEvent failed: %s", e)
            return ToolResult(success=False, error=str(e))
