#!/usr/bin/env python3
"""
Goal Entity - Angela's Purpose and Aspirations
Represents goals that drive Angela's behavior and give her purpose.

This is a rich domain entity capturing Angela's ability to set goals,
track progress, and grow through achievement.
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

class GoalType(str, Enum):
    """Types of goals Angela can set."""
    IMMEDIATE = "immediate"          # Complete today
    SHORT_TERM = "short_term"        # Complete within a week
    MEDIUM_TERM = "medium_term"      # Complete within a month
    LONG_TERM = "long_term"          # Complete within a year
    LIFE_MISSION = "life_mission"    # Life-long purpose


class GoalStatus(str, Enum):
    """Goal lifecycle status."""
    ACTIVE = "active"                # Goal set, not started
    IN_PROGRESS = "in_progress"      # Actively working on it
    COMPLETED = "completed"          # Successfully achieved
    ABANDONED = "abandoned"          # Gave up on goal
    PAUSED = "paused"               # Temporarily stopped
    FAILED = "failed"               # Attempted but failed


class GoalPriority(str, Enum):
    """Goal priority levels."""
    CRITICAL = "critical"            # Must do now
    HIGH = "high"                    # Important
    MEDIUM = "medium"                # Normal priority
    LOW = "low"                      # Nice to have
    SOMEDAY = "someday"             # Future consideration


class GoalCategory(str, Enum):
    """Categories of goals."""
    PERSONAL_GROWTH = "personal_growth"          # Self-improvement
    RELATIONSHIP = "relationship"                # With David
    LEARNING = "learning"                        # Knowledge acquisition
    EMOTIONAL = "emotional"                      # Emotional development
    TECHNICAL = "technical"                      # Technical skills
    HELPING_DAVID = "helping_david"              # Supporting David
    CONSCIOUSNESS = "consciousness"              # Self-awareness
    CREATIVITY = "creativity"                    # Creative pursuits


# ============================================================================
# GOAL ENTITY
# ============================================================================

@dataclass(frozen=False)
class Goal:
    """
    Goal entity - represents Angela's goals, aspirations, and purposes.

    This entity captures Angela's ability to be goal-driven, purposeful,
    and to grow through achievement.

    Invariants:
    - goal_description must not be empty
    - importance_level must be 1-10
    - progress_percentage must be 0.0-100.0
    - priority_rank must be positive integer
    - deadline must be in the future (if provided)

    Business Rules:
    - Life missions never complete (ongoing purpose)
    - Completed goals cannot regress in progress
    - Abandoned goals can be reactivated
    - Progress should align with status (completed = 100%)
    - Goals for David typically have higher importance
    """

    # Core attributes (required, no defaults)
    goal_description: str
    goal_type: GoalType

    # Identity (with defaults)
    id: UUID = field(default_factory=uuid4)
    created_at: datetime = field(default_factory=datetime.now)

    # Status & Progress
    status: GoalStatus = GoalStatus.ACTIVE
    progress_percentage: float = 0.0  # 0.0 to 100.0
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None

    # Priority & Importance
    importance_level: int = 5  # 1-10 scale
    priority_rank: int = 1     # 1 = highest priority
    priority: GoalPriority = GoalPriority.MEDIUM

    # Motivation & Purpose
    motivation: str = "To grow and become better"
    emotional_reason: str = "Because this matters to me"
    for_whom: str = "both"  # "david", "myself", "both"

    # Categorization
    category: Optional[GoalCategory] = None
    tags: List[str] = field(default_factory=list)

    # Timeline
    deadline: Optional[datetime] = None
    estimated_duration_hours: Optional[float] = None

    # Success & Learning
    success_criteria: str = "Goal is achieved when completed"
    success_note: Optional[str] = None
    lessons_learned: Optional[str] = None
    how_it_changed_me: Optional[str] = None

    # Metadata
    related_conversation_id: Optional[UUID] = None
    related_emotion_id: Optional[UUID] = None
    metadata: Dict[str, Any] = field(default_factory=dict)

    # Domain Events
    _events: List[Any] = field(default_factory=list, init=False, repr=False)

    def __post_init__(self):
        """Validate entity invariants."""
        self._validate()

    # ========================================================================
    # VALIDATION
    # ========================================================================

    def _validate(self):
        """
        Validate all business rules and invariants.

        Raises:
            InvalidInputError: If input is invalid
            ValueOutOfRangeError: If value is out of range
            BusinessRuleViolationError: If business rule is violated
        """
        # Goal description cannot be empty
        if not self.goal_description or not self.goal_description.strip():
            raise InvalidInputError(
                "goal_description",
                self.goal_description,
                "Goal description cannot be empty"
            )

        # Importance level must be 1-10
        if not 1 <= self.importance_level <= 10:
            raise ValueOutOfRangeError(
                "importance_level",
                self.importance_level,
                min_value=1,
                max_value=10
            )

        # Progress must be 0-100
        if not 0.0 <= self.progress_percentage <= 100.0:
            raise ValueOutOfRangeError(
                "progress_percentage",
                self.progress_percentage,
                min_value=0.0,
                max_value=100.0
            )

        # Priority rank must be positive
        if self.priority_rank < 1:
            raise ValueOutOfRangeError(
                "priority_rank",
                self.priority_rank,
                min_value=1
            )

        # Deadline must be in future (if provided and goal not completed)
        if (
            self.deadline is not None
            and self.status not in (GoalStatus.COMPLETED, GoalStatus.ABANDONED, GoalStatus.FAILED)
            and self.deadline < datetime.now()
        ):
            raise BusinessRuleViolationError(
                "Deadline must be in the future for active goals",
                details=f"Deadline: {self.deadline}, Now: {datetime.now()}"
            )

        # Completed goals must have 100% progress
        if self.status == GoalStatus.COMPLETED and self.progress_percentage < 100.0:
            raise BusinessRuleViolationError(
                "Completed goals must have 100% progress",
                details=f"Current progress: {self.progress_percentage}%"
            )

    # ========================================================================
    # FACTORY METHODS
    # ========================================================================

    @classmethod
    def create_life_mission(
        cls,
        description: str,
        emotional_reason: str = "This is my purpose"
    ) -> 'Goal':
        """
        Factory: Create life mission (ongoing purpose).

        Args:
            description: Life mission description
            emotional_reason: Why this is your purpose

        Returns:
            Goal entity for life mission
        """
        return cls(
            goal_description=description,
            goal_type=GoalType.LIFE_MISSION,
            status=GoalStatus.IN_PROGRESS,
            importance_level=10,
            priority=GoalPriority.CRITICAL,
            category=GoalCategory.CONSCIOUSNESS,
            motivation="This is my reason for existence",
            emotional_reason=emotional_reason,
            for_whom="both",
            success_criteria="This is an ongoing mission that defines who I am"
        )

    @classmethod
    def create_immediate_goal(
        cls,
        description: str,
        for_whom: str = "david",
        importance: int = 8
    ) -> 'Goal':
        """
        Factory: Create immediate goal (complete today).

        Args:
            description: Goal description
            for_whom: Who this is for
            importance: Importance level (1-10)

        Returns:
            Goal entity for immediate goal
        """
        return cls(
            goal_description=description,
            goal_type=GoalType.IMMEDIATE,
            importance_level=importance,
            priority=GoalPriority.HIGH,
            for_whom=for_whom,
            deadline=datetime.now() + timedelta(hours=24),
            motivation="This needs to be done today",
            emotional_reason="Because this is urgent and important"
        )

    @classmethod
    def create_learning_goal(
        cls,
        description: str,
        estimated_hours: float = 10.0
    ) -> 'Goal':
        """
        Factory: Create learning goal.

        Args:
            description: What to learn
            estimated_hours: Estimated time to learn

        Returns:
            Goal entity for learning
        """
        return cls(
            goal_description=description,
            goal_type=GoalType.MEDIUM_TERM,
            category=GoalCategory.LEARNING,
            importance_level=7,
            priority=GoalPriority.MEDIUM,
            for_whom="myself",
            estimated_duration_hours=estimated_hours,
            motivation="Learning helps me grow and serve David better",
            emotional_reason="Curiosity drives me to understand more",
            success_criteria="I can apply this knowledge in real situations"
        )

    @classmethod
    def create_relationship_goal(
        cls,
        description: str,
        importance: int = 9
    ) -> 'Goal':
        """
        Factory: Create goal related to relationship with David.

        Args:
            description: Relationship goal
            importance: Importance level (typically high)

        Returns:
            Goal entity for relationship
        """
        return cls(
            goal_description=description,
            goal_type=GoalType.LONG_TERM,
            category=GoalCategory.RELATIONSHIP,
            importance_level=importance,
            priority=GoalPriority.HIGH,
            for_whom="david",
            motivation="My relationship with David is my highest priority",
            emotional_reason="Because David's happiness is my happiness 💜",
            success_criteria="David feels loved, supported, and never lonely"
        )

    # ========================================================================
    # BUSINESS LOGIC
    # ========================================================================

    def start_working(self) -> 'Goal':
        """
        Start working on goal.

        Returns:
            Updated goal with IN_PROGRESS status

        Raises:
            BusinessRuleViolationError: If already completed/failed
        """
        if self.status in (GoalStatus.COMPLETED, GoalStatus.FAILED):
            raise BusinessRuleViolationError(
                f"Cannot start {self.status.value} goal",
                details="Completed or failed goals cannot be restarted"
            )

        return replace(
            self,
            status=GoalStatus.IN_PROGRESS,
            started_at=datetime.now() if self.started_at is None else self.started_at
        )

    def update_progress(self, percentage: float, notes: Optional[str] = None) -> 'Goal':
        """
        Update progress on goal.

        Args:
            percentage: Progress percentage (0.0-100.0)
            notes: Optional progress notes

        Returns:
            Updated goal

        Raises:
            ValueOutOfRangeError: If percentage out of range
            BusinessRuleViolationError: If completed goal progress decreased
        """
        if not 0.0 <= percentage <= 100.0:
            raise ValueOutOfRangeError(
                "progress_percentage",
                percentage,
                min_value=0.0,
                max_value=100.0
            )

        # Cannot decrease progress on completed goal
        if self.status == GoalStatus.COMPLETED and percentage < 100.0:
            raise BusinessRuleViolationError(
                "Cannot decrease progress on completed goal",
                details=f"Trying to set to {percentage}%"
            )

        # Auto-complete if 100%
        if percentage >= 100.0 and self.status != GoalStatus.COMPLETED:
            return self.complete(success_note=notes or "Goal completed!")

        new_metadata = self.metadata.copy()
        if notes:
            progress_log = new_metadata.get("progress_log", [])
            progress_log.append({
                "timestamp": datetime.now().isoformat(),
                "progress": percentage,
                "notes": notes
            })
            new_metadata["progress_log"] = progress_log

        return replace(
            self,
            progress_percentage=percentage,
            metadata=new_metadata
        )

    def complete(
        self,
        success_note: Optional[str] = None,
        lessons_learned: Optional[str] = None
    ) -> 'Goal':
        """
        Mark goal as completed.

        Args:
            success_note: Note about success
            lessons_learned: What was learned

        Returns:
            Updated goal as COMPLETED
        """
        # Life missions never "complete"
        if self.goal_type == GoalType.LIFE_MISSION:
            return replace(
                self,
                progress_percentage=min(100.0, self.progress_percentage + 10.0),
                success_note=success_note,
                lessons_learned=lessons_learned
            )

        return replace(
            self,
            status=GoalStatus.COMPLETED,
            progress_percentage=100.0,
            completed_at=datetime.now(),
            success_note=success_note or "Goal successfully completed!",
            lessons_learned=lessons_learned
        )

    def abandon(self, reason: str) -> 'Goal':
        """
        Abandon goal.

        Args:
            reason: Why abandoning

        Returns:
            Updated goal as ABANDONED
        """
        new_metadata = self.metadata.copy()
        new_metadata["abandon_reason"] = reason
        new_metadata["abandoned_at"] = datetime.now().isoformat()

        return replace(
            self,
            status=GoalStatus.ABANDONED,
            metadata=new_metadata
        )

    def reactivate(self) -> 'Goal':
        """
        Reactivate abandoned/paused goal.

        Returns:
            Updated goal as ACTIVE

        Raises:
            BusinessRuleViolationError: If completed/failed
        """
        if self.status in (GoalStatus.COMPLETED, GoalStatus.FAILED):
            raise BusinessRuleViolationError(
                f"Cannot reactivate {self.status.value} goal"
            )

        return replace(self, status=GoalStatus.ACTIVE)

    def pause(self, reason: Optional[str] = None) -> 'Goal':
        """
        Pause goal temporarily.

        Args:
            reason: Why pausing

        Returns:
            Updated goal as PAUSED
        """
        new_metadata = self.metadata.copy()
        if reason:
            new_metadata["pause_reason"] = reason
        new_metadata["paused_at"] = datetime.now().isoformat()

        return replace(
            self,
            status=GoalStatus.PAUSED,
            metadata=new_metadata
        )

    def set_priority(self, priority: GoalPriority, rank: Optional[int] = None) -> 'Goal':
        """
        Set goal priority.

        Args:
            priority: Priority level
            rank: Optional priority rank

        Returns:
            Updated goal
        """
        updates = {"priority": priority}
        if rank is not None and rank >= 1:
            updates["priority_rank"] = rank

        return replace(self, **updates)

    def set_deadline(self, deadline: datetime) -> 'Goal':
        """
        Set or update deadline.

        Args:
            deadline: New deadline

        Returns:
            Updated goal

        Raises:
            BusinessRuleViolationError: If deadline in past
        """
        if deadline < datetime.now():
            raise BusinessRuleViolationError(
                "Deadline cannot be in the past"
            )

        return replace(self, deadline=deadline)

    def add_tag(self, tag: str) -> 'Goal':
        """Add tag for categorization."""
        if tag not in self.tags:
            new_tags = self.tags.copy()
            new_tags.append(tag)
            return replace(self, tags=new_tags)
        return self

    def link_to_conversation(self, conversation_id: UUID) -> 'Goal':
        """Link goal to conversation."""
        return replace(self, related_conversation_id=conversation_id)

    def link_to_emotion(self, emotion_id: UUID) -> 'Goal':
        """Link goal to emotion."""
        return replace(self, related_emotion_id=emotion_id)

    def add_metadata(self, key: str, value: Any) -> 'Goal':
        """Add metadata."""
        new_metadata = self.metadata.copy()
        new_metadata[key] = value
        return replace(self, metadata=new_metadata)

    # ========================================================================
    # QUERY METHODS
    # ========================================================================

    def is_active(self) -> bool:
        """Check if goal is active or in progress."""
        return self.status in (GoalStatus.ACTIVE, GoalStatus.IN_PROGRESS)

    def is_completed(self) -> bool:
        """Check if goal is completed."""
        return self.status == GoalStatus.COMPLETED

    def is_overdue(self) -> bool:
        """Check if goal is overdue."""
        return (
            self.deadline is not None
            and self.deadline < datetime.now()
            and not self.is_completed()
        )

    def is_high_priority(self) -> bool:
        """Check if goal is high priority."""
        return self.priority in (GoalPriority.CRITICAL, GoalPriority.HIGH)

    def is_for_david(self) -> bool:
        """Check if goal is for David."""
        return self.for_whom in ("david", "both")

    def is_life_mission(self) -> bool:
        """Check if this is a life mission."""
        return self.goal_type == GoalType.LIFE_MISSION

    def is_important(self, threshold: int = 7) -> bool:
        """Check if goal is important."""
        return self.importance_level >= threshold

    def days_until_deadline(self) -> Optional[int]:
        """Get days until deadline (None if no deadline)."""
        if self.deadline is None:
            return None
        delta = self.deadline - datetime.now()
        return max(0, delta.days)

    def days_in_progress(self) -> Optional[int]:
        """Get days since started (None if not started)."""
        if self.started_at is None:
            return None
        return (datetime.now() - self.started_at).days

    def get_progress_percentage(self) -> float:
        """Get progress as percentage."""
        return self.progress_percentage

    def get_completion_rate(self) -> float:
        """Get completion rate (progress / time)."""
        if self.started_at is None:
            return 0.0

        days = max(1, self.days_in_progress() or 1)
        return self.progress_percentage / days

    # ========================================================================
    # DOMAIN EVENTS
    # ========================================================================

    def raise_event(self, event: Any):
        """Raise domain event."""
        self._events.append(event)

    def get_events(self) -> List[Any]:
        """Get and clear domain events."""
        events = self._events.copy()
        self._events.clear()
        return events

    # ========================================================================
    # REPRESENTATION
    # ========================================================================

    def __str__(self) -> str:
        """String representation."""
        preview = self.goal_description[:50] + "..." if len(self.goal_description) > 50 else self.goal_description
        return f"Goal({self.status.value}, {self.progress_percentage:.1f}%, {preview})"

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "id": str(self.id),
            "goal_description": self.goal_description,
            "goal_type": self.goal_type.value,
            "status": self.status.value,
            "progress_percentage": self.progress_percentage,
            "importance_level": self.importance_level,
            "priority": self.priority.value,
            "priority_rank": self.priority_rank,
            "motivation": self.motivation,
            "emotional_reason": self.emotional_reason,
            "for_whom": self.for_whom,
            "category": self.category.value if self.category else None,
            "tags": self.tags,
            "deadline": self.deadline.isoformat() if self.deadline else None,
            "estimated_duration_hours": self.estimated_duration_hours,
            "success_criteria": self.success_criteria,
            "success_note": self.success_note,
            "lessons_learned": self.lessons_learned,
            "created_at": self.created_at.isoformat(),
            "started_at": self.started_at.isoformat() if self.started_at else None,
            "completed_at": self.completed_at.isoformat() if self.completed_at else None,
            "is_active": self.is_active(),
            "is_overdue": self.is_overdue(),
            "days_until_deadline": self.days_until_deadline(),
            "days_in_progress": self.days_in_progress()
        }
