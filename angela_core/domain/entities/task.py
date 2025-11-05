#!/usr/bin/env python3
"""
Task Entity - Angela's Task Management System

Represents tasks and reminders with completion tracking, priority management,
and calendar integration support.

Angela's task system helps David stay organized:
- Tasks can have due dates and priorities
- Support for recurring tasks
- Calendar integration (EventKit)
- Tracks completion and importance
"""

from dataclasses import dataclass, field, replace
from datetime import datetime, timedelta
from typing import Optional, List, Dict, Any
from uuid import UUID, uuid4
from enum import Enum

from angela_core.shared.exceptions import (
    BusinessRuleViolationError,
    InvalidInputError,
    ValueOutOfRangeError
)


# ============================================================================
# ENUMS & VALUE OBJECTS
# ============================================================================

class TaskType(str, Enum):
    """
    Task types for categorization.
    """
    PERSONAL = "personal"              # Personal task
    WORK = "work"                      # Work-related task
    HEALTH = "health"                  # Health and wellness
    LEARNING = "learning"              # Learning and education
    SOCIAL = "social"                  # Social commitments
    MAINTENANCE = "maintenance"        # Maintenance tasks
    SHOPPING = "shopping"              # Shopping lists
    REMINDER = "reminder"              # Simple reminder
    OTHER = "other"                    # Uncategorized


class TaskPriority(str, Enum):
    """
    Task priority levels (human-readable).

    Maps to priority integer (0-10):
    - NONE: 0
    - LOW: 1-3
    - MEDIUM: 4-6
    - HIGH: 7-8
    - URGENT: 9-10
    """
    NONE = "none"          # 0
    LOW = "low"            # 1-3
    MEDIUM = "medium"      # 4-6
    HIGH = "high"          # 7-8
    URGENT = "urgent"      # 9-10

    @staticmethod
    def from_int(priority: int) -> 'TaskPriority':
        """Convert integer priority to enum."""
        if priority == 0:
            return TaskPriority.NONE
        elif priority <= 3:
            return TaskPriority.LOW
        elif priority <= 6:
            return TaskPriority.MEDIUM
        elif priority <= 8:
            return TaskPriority.HIGH
        else:
            return TaskPriority.URGENT


class SyncStatus(str, Enum):
    """
    Calendar sync status.
    """
    SYNCED = "synced"              # Successfully synced
    PENDING = "pending"            # Waiting to sync
    FAILED = "failed"              # Sync failed
    NOT_SYNCED = "not_synced"      # Not yet synced


# ============================================================================
# TASK ENTITY
# ============================================================================

@dataclass(frozen=False)
class Task:
    """
    Task entity - represents tasks and reminders for David.

    Handles task management with completion tracking, priority management,
    and calendar integration (EventKit).

    Invariants:
    - title cannot be empty
    - priority must be 0-10
    - importance_level must be 1-10
    - confidence_score must be 0.0-1.0
    - completion_date requires is_completed = True

    Business Rules:
    - Overdue tasks (past due_date and not completed) should be highlighted
    - Completed tasks cannot be marked incomplete
    - High-priority tasks (>= 7) should be shown prominently
    - Recurring tasks create new instances when completed
    """

    # Core content (required)
    title: str

    # Identity (with defaults)
    id: UUID = field(default_factory=uuid4)

    # Description & Notes
    notes: Optional[str] = None

    # Priority & Importance
    priority: int = 0  # 0-10 scale (0 = none, 10 = urgent)
    importance_level: int = 5  # 1-10 scale (Angela's assessment)

    # Scheduling
    due_date: Optional[datetime] = None
    completion_date: Optional[datetime] = None
    is_completed: bool = False

    # Categorization
    task_type: Optional[TaskType] = None
    context_tags: List[str] = field(default_factory=list)

    # Recurrence
    is_recurring: bool = False
    recurrence_rule: Optional[str] = None  # iCalendar RRULE format

    # Source & Context
    conversation_id: Optional[UUID] = None
    david_words: Optional[str] = None  # David's original request
    angela_interpretation: Optional[str] = None  # Angela's understanding
    confidence_score: float = 0.5  # 0.0-1.0 (Angela's confidence in interpretation)
    auto_created: bool = False  # Created automatically vs. explicitly

    # Calendar Integration (EventKit)
    eventkit_identifier: Optional[str] = None
    eventkit_calendar_identifier: Optional[str] = None
    sync_status: SyncStatus = SyncStatus.NOT_SYNCED
    sync_error: Optional[str] = None
    last_synced_at: Optional[datetime] = None

    # Timestamps
    created_at: datetime = field(default_factory=datetime.now)
    updated_at: datetime = field(default_factory=datetime.now)

    def __post_init__(self):
        """Validate task after initialization."""
        self._validate()

    # ========================================================================
    # VALIDATION
    # ========================================================================

    def _validate(self):
        """Validate all business rules."""
        # Title validation
        if not self.title or not self.title.strip():
            raise InvalidInputError("Task title cannot be empty")

        # Priority validation
        if not (0 <= self.priority <= 10):
            raise ValueOutOfRangeError(
                "priority",
                self.priority,
                "Priority must be between 0 and 10"
            )

        # Importance validation
        if not (1 <= self.importance_level <= 10):
            raise ValueOutOfRangeError(
                "importance_level",
                self.importance_level,
                "Importance must be between 1 and 10"
            )

        # Confidence validation
        if not (0.0 <= self.confidence_score <= 1.0):
            raise ValueOutOfRangeError(
                "confidence_score",
                self.confidence_score,
                "Confidence must be between 0.0 and 1.0"
            )

        # Completion date requires is_completed
        if self.completion_date and not self.is_completed:
            raise BusinessRuleViolationError(
                "completion_date can only be set when is_completed is True"
            )

    # ========================================================================
    # PRIORITY MANAGEMENT
    # ========================================================================

    def get_priority_label(self) -> TaskPriority:
        """Get human-readable priority level."""
        return TaskPriority.from_int(self.priority)

    def is_high_priority(self) -> bool:
        """Check if task is high priority (>= 7)."""
        return self.priority >= 7

    def is_urgent(self) -> bool:
        """Check if task is urgent (>= 9)."""
        return self.priority >= 9

    def update_priority(self, new_priority: int) -> 'Task':
        """
        Update task priority.

        Args:
            new_priority: New priority level (0-10)

        Returns:
            Updated Task with new priority

        Raises:
            ValueOutOfRangeError: If priority is invalid
        """
        if not (0 <= new_priority <= 10):
            raise ValueOutOfRangeError(
                "new_priority",
                new_priority,
                "Priority must be between 0 and 10"
            )

        return replace(
            self,
            priority=new_priority,
            updated_at=datetime.now()
        )

    # ========================================================================
    # DATE & TIME MANAGEMENT
    # ========================================================================

    def is_overdue(self) -> bool:
        """Check if task is overdue (past due date and not completed)."""
        if self.is_completed or not self.due_date:
            return False
        return datetime.now() > self.due_date

    def is_due_soon(self, hours: int = 24) -> bool:
        """
        Check if task is due within N hours.

        Args:
            hours: Number of hours (default 24)

        Returns:
            True if due within specified hours
        """
        if self.is_completed or not self.due_date:
            return False

        threshold = datetime.now() + timedelta(hours=hours)
        return self.due_date <= threshold

    def is_due_today(self) -> bool:
        """Check if task is due today."""
        if self.is_completed or not self.due_date:
            return False

        now = datetime.now()
        return self.due_date.date() == now.date()

    def reschedule(self, new_due_date: datetime) -> 'Task':
        """
        Reschedule task to new due date.

        Args:
            new_due_date: New due date

        Returns:
            Updated Task with new due date
        """
        return replace(
            self,
            due_date=new_due_date,
            updated_at=datetime.now()
        )

    # ========================================================================
    # COMPLETION
    # ========================================================================

    def complete(self, completion_note: Optional[str] = None) -> 'Task':
        """
        Mark task as completed.

        Args:
            completion_note: Optional note about completion

        Returns:
            Updated Task marked as completed

        Raises:
            BusinessRuleViolationError: If task is already completed
        """
        if self.is_completed:
            raise BusinessRuleViolationError("Task is already completed")

        # Append completion note to notes if provided
        updated_notes = self.notes
        if completion_note:
            if self.notes:
                updated_notes = f"{self.notes}\n\n[Completed: {datetime.now().strftime('%Y-%m-%d')}]\n{completion_note}"
            else:
                updated_notes = f"[Completed: {datetime.now().strftime('%Y-%m-%d')}]\n{completion_note}"

        return replace(
            self,
            is_completed=True,
            completion_date=datetime.now(),
            notes=updated_notes,
            updated_at=datetime.now()
        )

    def reopen(self, reason: Optional[str] = None) -> 'Task':
        """
        Reopen completed task.

        Args:
            reason: Optional reason for reopening

        Returns:
            Updated Task marked as not completed

        Raises:
            BusinessRuleViolationError: If task is not completed
        """
        if not self.is_completed:
            raise BusinessRuleViolationError("Task is not completed")

        # Append reopen reason to notes if provided
        updated_notes = self.notes
        if reason:
            if self.notes:
                updated_notes = f"{self.notes}\n\n[Reopened: {datetime.now().strftime('%Y-%m-%d')}]\n{reason}"
            else:
                updated_notes = f"[Reopened: {datetime.now().strftime('%Y-%m-%d')}]\n{reason}"

        return replace(
            self,
            is_completed=False,
            completion_date=None,
            notes=updated_notes,
            updated_at=datetime.now()
        )

    # ========================================================================
    # FACTORY METHODS
    # ========================================================================

    @classmethod
    def create_simple_task(
        cls,
        title: str,
        due_date: Optional[datetime] = None,
        priority: int = 5,
        notes: Optional[str] = None
    ) -> 'Task':
        """
        Create a simple task.

        Args:
            title: Task title
            due_date: Optional due date
            priority: Priority (0-10, default 5)
            notes: Optional notes

        Returns:
            New Task entity
        """
        return cls(
            title=title,
            due_date=due_date,
            priority=priority,
            notes=notes,
            task_type=TaskType.PERSONAL,
            importance_level=5
        )

    @classmethod
    def create_recurring_task(
        cls,
        title: str,
        recurrence_rule: str,
        priority: int = 5,
        notes: Optional[str] = None
    ) -> 'Task':
        """
        Create a recurring task.

        Args:
            title: Task title
            recurrence_rule: iCalendar RRULE string
            priority: Priority (0-10, default 5)
            notes: Optional notes

        Returns:
            New recurring Task entity
        """
        return cls(
            title=title,
            priority=priority,
            notes=notes,
            is_recurring=True,
            recurrence_rule=recurrence_rule,
            task_type=TaskType.REMINDER,
            importance_level=5
        )

    @classmethod
    def create_from_conversation(
        cls,
        title: str,
        conversation_id: UUID,
        david_words: str,
        angela_interpretation: str,
        due_date: Optional[datetime] = None,
        priority: int = 5,
        confidence: float = 0.8
    ) -> 'Task':
        """
        Create task from conversation with David.

        Args:
            title: Task title (extracted from conversation)
            conversation_id: Source conversation ID
            david_words: David's original words
            angela_interpretation: Angela's interpretation
            due_date: Optional due date (extracted)
            priority: Priority (extracted, default 5)
            confidence: Angela's confidence in interpretation (0.0-1.0)

        Returns:
            New Task entity
        """
        return cls(
            title=title,
            due_date=due_date,
            priority=priority,
            conversation_id=conversation_id,
            david_words=david_words,
            angela_interpretation=angela_interpretation,
            confidence_score=confidence,
            auto_created=True,
            task_type=TaskType.PERSONAL,
            importance_level=priority if priority <= 10 else 10
        )

    # ========================================================================
    # UTILITY METHODS
    # ========================================================================

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary (for serialization)."""
        return {
            "task_id": str(self.id),
            "title": self.title,
            "notes": self.notes,
            "priority": self.priority,
            "priority_label": self.get_priority_label().value,
            "importance_level": self.importance_level,
            "due_date": self.due_date.isoformat() if self.due_date else None,
            "completion_date": self.completion_date.isoformat() if self.completion_date else None,
            "is_completed": self.is_completed,
            "is_overdue": self.is_overdue(),
            "is_due_soon": self.is_due_soon(),
            "task_type": self.task_type.value if self.task_type else None,
            "context_tags": self.context_tags,
            "is_recurring": self.is_recurring,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }

    def __str__(self) -> str:
        """Human-readable representation."""
        status = "✓" if self.is_completed else "○"
        priority_label = self.get_priority_label().value.upper()
        due = f" (due: {self.due_date.strftime('%Y-%m-%d')})" if self.due_date else ""
        return f"{status} [{priority_label}] {self.title[:50]}{due}"

    def __repr__(self) -> str:
        """Developer representation."""
        return (
            f"Task(id={self.id}, title='{self.title[:30]}...', "
            f"priority={self.priority}, completed={self.is_completed})"
        )


# ============================================================================
# MODULE EXPORTS
# ============================================================================

__all__ = [
    'Task',
    'TaskType',
    'TaskPriority',
    'SyncStatus',
]
