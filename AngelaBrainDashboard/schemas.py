"""
Pydantic request/response models for Angela Brain Dashboard API.
"""
from typing import Optional

from pydantic import BaseModel


class MeetingCreate(BaseModel):
    title: str
    location: str
    meeting_date: str              # YYYY-MM-DD
    start_time: str                # HH:MM
    end_time: str                  # HH:MM
    meeting_type: str              # standard, site_visit, testing, bod
    attendees: Optional[list[str]] = None
    project_name: Optional[str] = None


class MeetingUpdate(BaseModel):
    title: Optional[str] = None
    location: Optional[str] = None
    meeting_date: Optional[str] = None      # YYYY-MM-DD
    start_time: Optional[str] = None        # HH:MM
    end_time: Optional[str] = None          # HH:MM
    meeting_type: Optional[str] = None
    attendees: Optional[list[str]] = None
    project_name: Optional[str] = None
    things3_status: Optional[str] = None    # open, completed
    notes: Optional[str] = None             # raw meeting notes


class ScheduledTaskCreate(BaseModel):
    task_name: str
    description: Optional[str] = None
    task_type: str  # 'python' or 'shell'
    command: str
    schedule_type: str  # 'time' or 'interval'
    schedule_time: Optional[str] = None  # HH:MM
    interval_minutes: Optional[int] = None


class ScheduledTaskUpdate(BaseModel):
    task_name: Optional[str] = None
    description: Optional[str] = None
    task_type: Optional[str] = None
    command: Optional[str] = None
    schedule_type: Optional[str] = None
    schedule_time: Optional[str] = None
    interval_minutes: Optional[int] = None
    is_active: Optional[bool] = None


class ScriptContentUpdate(BaseModel):
    path: str
    content: str
