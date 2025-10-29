"""
Calendar Routes - Access macOS Calendar Events

Provides endpoints to query Calendar events for Angela
"""

import logging
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import List, Dict, Any, Optional

from angela_core.services.macos_calendar_service import calendar_service

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/calendar", tags=["calendar"])


class CalendarEvent(BaseModel):
    """Calendar event model"""
    title: str
    start: str
    end: str
    location: str
    notes: str


class CalendarResponse(BaseModel):
    """Calendar response model"""
    date: str
    events: List[Dict[str, str]]
    count: int


@router.get("/today", response_model=CalendarResponse)
async def get_today_events():
    """
    Get today's calendar events

    Returns all events for today from macOS Calendar
    """
    try:
        if not calendar_service:
            raise HTTPException(
                status_code=503,
                detail="Calendar service not available. Install pyobjc-framework-EventKit"
            )

        result = calendar_service.get_today_events()
        logger.info(f"📅 Retrieved {result['count']} events for today")

        return CalendarResponse(**result)

    except Exception as e:
        logger.error(f"❌ Failed to get today events: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/upcoming", response_model=CalendarResponse)
async def get_upcoming_events(days: int = 7):
    """
    Get upcoming calendar events

    Args:
        days: Number of days to look ahead (default: 7)

    Returns all events for the next N days
    """
    try:
        if not calendar_service:
            raise HTTPException(
                status_code=503,
                detail="Calendar service not available"
            )

        result = calendar_service.get_upcoming_events(days=days)
        logger.info(f"📅 Retrieved {result['count']} events for next {days} days")

        return CalendarResponse(**result)

    except Exception as e:
        logger.error(f"❌ Failed to get upcoming events: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/week/{week_offset}", response_model=CalendarResponse)
async def get_week_events(week_offset: int = 0):
    """
    Get events for a specific week

    Args:
        week_offset: Week offset (0 = this week, 1 = next week, -1 = last week)

    Returns all events for the specified week
    """
    try:
        if not calendar_service:
            raise HTTPException(
                status_code=503,
                detail="Calendar service not available"
            )

        result = calendar_service.get_events_for_week(week_offset=week_offset)
        logger.info(f"📅 Retrieved {result['count']} events for week {week_offset:+d}")

        return CalendarResponse(**result)

    except Exception as e:
        logger.error(f"❌ Failed to get week events: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/search", response_model=CalendarResponse)
async def search_events(query: str, days: int = 30):
    """
    Search calendar events

    Args:
        query: Search query string
        days: Number of days to search (default: 30)

    Returns events matching the query
    """
    try:
        if not calendar_service:
            raise HTTPException(
                status_code=503,
                detail="Calendar service not available"
            )

        result = calendar_service.search_events(query=query, days=days)
        logger.info(f"📅 Found {result['count']} events matching '{query}'")

        return CalendarResponse(**result)

    except Exception as e:
        logger.error(f"❌ Failed to search events: {e}")
        raise HTTPException(status_code=500, detail=str(e))
