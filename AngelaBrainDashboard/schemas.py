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


class ActionItemCreate(BaseModel):
    meeting_id: str
    action_text: str
    assignee: Optional[str] = None
    due_date: Optional[str] = None    # YYYY-MM-DD
    priority: int = 5                 # 1-3=High, 4-6=Medium, 7+=Low


class ActionItemUpdate(BaseModel):
    action_text: Optional[str] = None
    assignee: Optional[str] = None
    due_date: Optional[str] = None
    priority: Optional[int] = None
    is_completed: Optional[bool] = None


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


# ---------------------------------------------------------------------------
# Chat with Angela (Gemini 2.5 Flash)
# ---------------------------------------------------------------------------

class ChatRequest(BaseModel):
    message: str
    emotional_context: Optional[dict] = None
    model: Optional[str] = "gemini"  # "gemini" | "typhoon" | "groq"
    image_data: Optional[str] = None      # base64-encoded image
    image_mime_type: Optional[str] = None  # "image/jpeg", "image/png", etc.


class ChatResponse(BaseModel):
    response: str
    model: str  # "gemini-2.5-flash"
    context_metadata: Optional[dict] = None


class ChatMessageSave(BaseModel):
    speaker: str  # "david" or "angela"
    message_text: str
    topic: Optional[str] = None
    emotion_detected: Optional[str] = None
    importance_level: int = 5
    model_used: Optional[str] = None


class EmotionalMetadataResponse(BaseModel):
    """Emotional metadata returned in SSE metadata event."""
    emotion_detected: str = "neutral"
    emotion_intensity: int = 5
    emotion_confidence: float = 0.0
    emotion_cues: list[str] = []
    angela_emotion: str = "caring"
    angela_intensity: int = 7
    mirroring_strategy: str = "resonance"
    mirroring_description: str = "Warm and attentive"
    mirroring_icon: str = "heart.fill"
    triggered_memory_titles: list[str] = []
    consciousness_level: float = 1.0
    sections_loaded: list[str] = []


class LearningEvent(BaseModel):
    """Learning event emitted via SSE after Angela's response."""
    count: int = 0
    topics: list[str] = []


class ChatFeedbackRequest(BaseModel):
    conversation_id: str
    rating: int  # 1 or -1
    feedback_type: str  # "thumbs_up" or "thumbs_down"


class ChatFeedbackBatchRequest(BaseModel):
    conversation_ids: list[str]
