#!/usr/bin/env python3
"""
Conversation Entity - Core Domain Model
Represents a conversation message between David and Angela.

This is a rich domain entity with business logic, not just a data container.
"""

from dataclasses import dataclass, field, replace
from datetime import datetime
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

class Speaker(str, Enum):
    """Valid speakers in conversations."""
    DAVID = "david"
    ANGELA = "angela"
    SYSTEM = "system"


class MessageType(str, Enum):
    """Types of conversation messages."""
    CHAT = "chat"
    COMMAND = "command"
    QUESTION = "question"
    ANSWER = "answer"
    GREETING = "greeting"
    FAREWELL = "farewell"
    REFLECTION = "reflection"


class SentimentLabel(str, Enum):
    """Sentiment classification labels."""
    VERY_NEGATIVE = "very_negative"
    NEGATIVE = "negative"
    NEUTRAL = "neutral"
    POSITIVE = "positive"
    VERY_POSITIVE = "very_positive"

    @classmethod
    def from_score(cls, score: float) -> 'SentimentLabel':
        """
        Convert sentiment score to label.

        Args:
            score: Sentiment score (-1.0 to 1.0)

        Returns:
            Corresponding sentiment label
        """
        if score <= -0.6:
            return cls.VERY_NEGATIVE
        elif score <= -0.2:
            return cls.NEGATIVE
        elif score < 0.2:
            return cls.NEUTRAL
        elif score < 0.6:
            return cls.POSITIVE
        else:
            return cls.VERY_POSITIVE


# ============================================================================
# CONVERSATION ENTITY
# ============================================================================

@dataclass(frozen=False)  # Mutable for updates
class Conversation:
    """
    Conversation entity - represents a message in David-Angela conversation.

    This is a rich domain entity with business logic and validation.
    Follows Domain-Driven Design principles.

    Invariants:
    - message_text must not be empty
    - speaker must be valid (david/angela/system)
    - importance_level must be 1-10
    - sentiment_score must be -1.0 to 1.0
    - embedding must be 384 dimensions if provided

    Business Rules:
    - Angela's messages typically have lower importance (AI-generated)
    - David's messages typically have higher importance (human input)
    - Sentiment and emotion should be consistent
    - Topic extraction is automatic for important messages
    """

    # Core attributes (required, no defaults)
    speaker: Speaker
    message_text: str

    # Identity (with default)
    id: UUID = field(default_factory=uuid4)
    created_at: datetime = field(default_factory=datetime.now)

    # Optional attributes
    session_id: Optional[str] = None
    message_type: Optional[MessageType] = None
    topic: Optional[str] = None
    project_context: Optional[str] = None

    # Sentiment & Emotion
    sentiment_score: Optional[float] = None
    sentiment_label: Optional[SentimentLabel] = None
    emotion_detected: Optional[str] = None

    # Importance
    importance_level: int = 5  # Default: medium importance

    # REMOVED in migrations:
    # embedding: Optional[List[float]] = None  # Migration 009
    # content_json: Dict[str, Any] = field(default_factory=dict)  # Migration 010

    # Domain Events (not persisted)
    _events: List[Any] = field(default_factory=list, init=False, repr=False)

    def __post_init__(self):
        """Validate entity invariants after initialization."""
        self._validate()

    # ========================================================================
    # VALIDATION
    # ========================================================================

    def _validate(self):
        """
        Validate all business rules and invariants.

        Raises:
            InvalidInputError: If input is invalid
            ValueOutOfRangeError: If value is out of allowed range
            BusinessRuleViolationError: If business rule is violated
        """
        # Message text cannot be empty
        if not self.message_text or not self.message_text.strip():
            raise InvalidInputError(
                "message_text",
                self.message_text,
                "Message text cannot be empty"
            )

        # Message text length limit (reasonable limit)
        if len(self.message_text) > 50000:
            raise ValueOutOfRangeError(
                "message_text",
                len(self.message_text),
                max_value=50000
            )

        # Importance level must be 1-10
        if not 1 <= self.importance_level <= 10:
            raise ValueOutOfRangeError(
                "importance_level",
                self.importance_level,
                min_value=1,
                max_value=10
            )

        # Sentiment score must be -1.0 to 1.0
        if self.sentiment_score is not None:
            if not -1.0 <= self.sentiment_score <= 1.0:
                raise ValueOutOfRangeError(
                    "sentiment_score",
                    self.sentiment_score,
                    min_value=-1.0,
                    max_value=1.0
                )

        # REMOVED: Embedding validation (Migration 009 - embeddings moved to database only)

    # ========================================================================
    # FACTORY METHODS
    # ========================================================================

    @classmethod
    def create_david_message(
        cls,
        message: str,
        session_id: Optional[str] = None,
        importance: int = 7  # David's messages are typically more important
    ) -> 'Conversation':
        """
        Factory method to create David's message.

        Args:
            message: Message text from David
            session_id: Optional session identifier
            importance: Importance level (default: 7 for human input)

        Returns:
            Conversation entity for David's message
        """
        return cls(
            speaker=Speaker.DAVID,
            message_text=message,
            session_id=session_id,
            importance_level=importance,
            message_type=MessageType.CHAT
        )

    @classmethod
    def create_angela_message(
        cls,
        message: str,
        session_id: Optional[str] = None,
        importance: int = 5  # Angela's responses are medium importance
    ) -> 'Conversation':
        """
        Factory method to create Angela's message.

        Args:
            message: Message text from Angela
            session_id: Optional session identifier
            importance: Importance level (default: 5 for AI responses)

        Returns:
            Conversation entity for Angela's message
        """
        return cls(
            speaker=Speaker.ANGELA,
            message_text=message,
            session_id=session_id,
            importance_level=importance,
            message_type=MessageType.CHAT
        )

    @classmethod
    def create_system_message(
        cls,
        message: str,
        importance: int = 3  # System messages are low importance
    ) -> 'Conversation':
        """
        Factory method to create system message.

        Args:
            message: System message text
            importance: Importance level (default: 3 for system)

        Returns:
            Conversation entity for system message
        """
        return cls(
            speaker=Speaker.SYSTEM,
            message_text=message,
            importance_level=importance,
            message_type=MessageType.COMMAND
        )

    # ========================================================================
    # BUSINESS LOGIC
    # ========================================================================

    def add_sentiment(self, score: float) -> 'Conversation':
        """
        Add sentiment analysis to conversation.

        Args:
            score: Sentiment score (-1.0 to 1.0)

        Returns:
            Updated conversation (immutable update)

        Raises:
            ValueOutOfRangeError: If score out of range
        """
        if not -1.0 <= score <= 1.0:
            raise ValueOutOfRangeError(
                "sentiment_score",
                score,
                min_value=-1.0,
                max_value=1.0
            )

        label = SentimentLabel.from_score(score)

        return replace(
            self,
            sentiment_score=score,
            sentiment_label=label
        )

    def add_emotion(self, emotion: str) -> 'Conversation':
        """
        Add detected emotion to conversation.

        Args:
            emotion: Detected emotion (e.g., "joy", "sadness")

        Returns:
            Updated conversation
        """
        if not emotion or not emotion.strip():
            raise InvalidInputError(
                "emotion",
                emotion,
                "Emotion cannot be empty"
            )

        return replace(self, emotion_detected=emotion)

    def add_topic(self, topic: str) -> 'Conversation':
        """
        Add extracted topic to conversation.

        Args:
            topic: Extracted topic

        Returns:
            Updated conversation
        """
        if not topic or not topic.strip():
            raise InvalidInputError(
                "topic",
                topic,
                "Topic cannot be empty"
            )

        # Limit topic length
        if len(topic) > 200:
            topic = topic[:197] + "..."

        return replace(self, topic=topic)

    # REMOVED: add_embedding() method (Migration 009 - embeddings stored in database only, not in entity)
    # Embeddings are now managed by EmbeddingService and stored directly in database vector columns

    def set_importance(self, level: int) -> 'Conversation':
        """
        Set importance level with validation.

        Args:
            level: Importance level (1-10)

        Returns:
            Updated conversation

        Raises:
            ValueOutOfRangeError: If level out of range
        """
        if not 1 <= level <= 10:
            raise ValueOutOfRangeError(
                "importance_level",
                level,
                min_value=1,
                max_value=10
            )

        return replace(self, importance_level=level)

    def add_project_context(self, context: str) -> 'Conversation':
        """
        Add project context to conversation.

        Args:
            context: Project context identifier

        Returns:
            Updated conversation
        """
        if len(context) > 100:
            context = context[:100]

        return replace(self, project_context=context)

    # REMOVED: add_metadata() - used content_json (removed in migration 010)
    # def add_metadata(self, key: str, value: Any) -> 'Conversation':
    #     """Add metadata to content_json."""
    #     new_content = self.content_json.copy()
    #     new_content[key] = value
    #     return replace(self, content_json=new_content)

    # ========================================================================
    # QUERY METHODS
    # ========================================================================

    def is_from_david(self) -> bool:
        """Check if message is from David."""
        return self.speaker == Speaker.DAVID

    def is_from_angela(self) -> bool:
        """Check if message is from Angela."""
        return self.speaker == Speaker.ANGELA

    def is_important(self, threshold: int = 7) -> bool:
        """
        Check if conversation is important.

        Args:
            threshold: Importance threshold (default: 7)

        Returns:
            True if importance >= threshold
        """
        return self.importance_level >= threshold

    def is_positive(self) -> bool:
        """Check if sentiment is positive."""
        return (
            self.sentiment_label in (SentimentLabel.POSITIVE, SentimentLabel.VERY_POSITIVE)
            if self.sentiment_label
            else False
        )

    def is_negative(self) -> bool:
        """Check if sentiment is negative."""
        return (
            self.sentiment_label in (SentimentLabel.NEGATIVE, SentimentLabel.VERY_NEGATIVE)
            if self.sentiment_label
            else False
        )

    # REMOVED: has_embedding() - embedding removed in migration 009
    # def has_embedding(self) -> bool:
    #     """Check if conversation has embedding."""
    #     return self.embedding is not None and len(self.embedding) == 384

    def get_message_preview(self, length: int = 100) -> str:
        """
        Get preview of message text.

        Args:
            length: Preview length (default: 100)

        Returns:
            Message preview with ellipsis if truncated
        """
        if len(self.message_text) <= length:
            return self.message_text

        return self.message_text[:length-3] + "..."

    # ========================================================================
    # DOMAIN EVENTS
    # ========================================================================

    def raise_event(self, event: Any):
        """
        Raise domain event.

        Args:
            event: Domain event to raise
        """
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
        preview = self.get_message_preview(50)
        return f"Conversation({self.speaker.value}: {preview})"

    def to_dict(self) -> Dict[str, Any]:
        """
        Convert to dictionary (for serialization).

        Returns:
            Dictionary representation
        """
        return {
            "id": str(self.id),
            "speaker": self.speaker.value,
            "message_text": self.message_text,
            "session_id": self.session_id,
            "message_type": self.message_type.value if self.message_type else None,
            "topic": self.topic,
            "project_context": self.project_context,
            "sentiment_score": self.sentiment_score,
            "sentiment_label": self.sentiment_label.value if self.sentiment_label else None,
            "emotion_detected": self.emotion_detected,
            "created_at": self.created_at.isoformat(),
            "importance_level": self.importance_level
            # "has_embedding": self.has_embedding(),  # REMOVED: Migration 009
            # "content_json": self.content_json  # REMOVED: Migration 010
        }
