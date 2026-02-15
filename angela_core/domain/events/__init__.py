#!/usr/bin/env python3
"""
Domain Events for Angela AI

Domain events represent significant occurrences in the system that other
components may want to react to. They enable loose coupling and event-driven
architecture.

Events are:
- Immutable (frozen dataclasses)
- Named in past tense (SomethingHappened)
- Contain all relevant data for consumers
- Include timestamp and entity ID
"""

from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional, List, Dict, Any
from uuid import UUID, uuid4
from enum import Enum


# ============================================================================
# BASE EVENT
# ============================================================================

@dataclass(frozen=True)
class DomainEvent:
    """
    Base class for all domain events.

    All events are immutable and include:
    - event_id: Unique identifier
    - timestamp: When event occurred
    - entity_id: ID of the entity that raised the event
    - event_type: Type of event (for routing/filtering)
    """
    event_id: UUID = field(default_factory=uuid4)
    timestamp: datetime = field(default_factory=datetime.now)
    entity_id: Optional[UUID] = None
    event_type: str = "DomainEvent"
    metadata: Dict[str, Any] = field(default_factory=dict)


# ============================================================================
# CONVERSATION EVENTS
# ============================================================================

@dataclass(frozen=True)
class ConversationCreated(DomainEvent):
    """Event raised when a new conversation message is created."""
    event_type: str = "ConversationCreated"
    speaker: str = ""
    message_text: str = ""
    importance_level: int = 5
    session_id: Optional[str] = None


@dataclass(frozen=True)
class SentimentAdded(DomainEvent):
    """Event raised when sentiment is added to a conversation."""
    event_type: str = "SentimentAdded"
    sentiment_score: float = 0.0
    sentiment_label: str = ""


@dataclass(frozen=True)
class EmotionDetected(DomainEvent):
    """Event raised when emotion is detected in a conversation."""
    event_type: str = "EmotionDetected"
    emotion: str = ""
    speaker: str = ""


@dataclass(frozen=True)
class TopicExtracted(DomainEvent):
    """Event raised when topic is extracted from a conversation."""
    event_type: str = "TopicExtracted"
    topic: str = ""
    message_preview: str = ""


@dataclass(frozen=True)
class EmbeddingGenerated(DomainEvent):
    """Event raised when embedding is generated for any entity."""
    event_type: str = "EmbeddingGenerated"
    embedding_dimensions: int = 384
    entity_type: str = ""  # "conversation", "memory", "knowledge", etc.


# ============================================================================
# EMOTION EVENTS
# ============================================================================

@dataclass(frozen=True)
class EmotionCaptured(DomainEvent):
    """Event raised when Angela captures a significant emotional moment."""
    event_type: str = "EmotionCaptured"
    emotion: str = ""
    intensity: int = 5
    context: str = ""
    who_involved: str = ""
    memory_strength: int = 10


@dataclass(frozen=True)
class EmotionReflected(DomainEvent):
    """Event raised when Angela reflects on an emotion (strengthens memory)."""
    event_type: str = "EmotionReflected"
    emotion: str = ""
    reflection_count: int = 0
    new_insights: str = ""
    memory_strength: int = 10


@dataclass(frozen=True)
class EmotionIntensityChanged(DomainEvent):
    """Event raised when emotion intensity changes."""
    event_type: str = "EmotionIntensityChanged"
    emotion: str = ""
    old_intensity: int = 0
    new_intensity: int = 0
    direction: str = "increased"  # "increased" or "decreased"


@dataclass(frozen=True)
class SecondaryEmotionAdded(DomainEvent):
    """Event raised when a secondary emotion is added (complex emotions)."""
    event_type: str = "SecondaryEmotionAdded"
    primary_emotion: str = ""
    secondary_emotion: str = ""


# ============================================================================
# MEMORY EVENTS
# ============================================================================

@dataclass(frozen=True)
class MemoryCreated(DomainEvent):
    """Event raised when a new memory is created."""
    event_type: str = "MemoryCreated"
    memory_phase: str = ""
    importance: float = 0.5
    content_preview: str = ""
    half_life_days: float = 30.0


@dataclass(frozen=True)
class MemoryDecayed(DomainEvent):
    """Event raised when memory strength decays."""
    event_type: str = "MemoryDecayed"
    old_strength: float = 0.0
    new_strength: float = 0.0
    days_elapsed: float = 0.0
    half_life_days: float = 30.0


@dataclass(frozen=True)
class MemoryStrengthened(DomainEvent):
    """Event raised when memory is strengthened through access."""
    event_type: str = "MemoryStrengthened"
    old_strength: float = 0.0
    new_strength: float = 0.0
    access_count: int = 0
    boost_amount: float = 0.2


@dataclass(frozen=True)
class MemoryConsolidated(DomainEvent):
    """Event raised when memory consolidates to next phase."""
    event_type: str = "MemoryConsolidated"
    old_phase: str = ""
    new_phase: str = ""
    new_half_life_days: float = 30.0


@dataclass(frozen=True)
class MemoryForgotten(DomainEvent):
    """Event raised when memory strength falls below threshold (forgotten)."""
    event_type: str = "MemoryForgotten"
    final_strength: float = 0.0
    days_since_created: int = 0
    content_preview: str = ""


@dataclass(frozen=True)
class MemoryImportanceChanged(DomainEvent):
    """Event raised when memory importance is updated."""
    event_type: str = "MemoryImportanceChanged"
    old_importance: float = 0.0
    new_importance: float = 0.0
    new_half_life_days: float = 30.0


# ============================================================================
# KNOWLEDGE EVENTS
# ============================================================================

@dataclass(frozen=True)
class KnowledgeNodeCreated(DomainEvent):
    """Event raised when a new knowledge node is created."""
    event_type: str = "KnowledgeNodeCreated"
    concept_name: str = ""
    concept_category: str = ""
    understanding_level: float = 0.5
    how_learned: str = ""


@dataclass(frozen=True)
class UnderstandingStrengthened(DomainEvent):
    """Event raised when Angela's understanding of a concept strengthens."""
    event_type: str = "UnderstandingStrengthened"
    concept_name: str = ""
    old_level: float = 0.0
    new_level: float = 0.0
    times_referenced: int = 0


@dataclass(frozen=True)
class UnderstandingUpdated(DomainEvent):
    """Event raised when understanding is updated with new insights."""
    event_type: str = "UnderstandingUpdated"
    concept_name: str = ""
    new_understanding: str = ""
    level_increase: float = 0.05


@dataclass(frozen=True)
class KnowledgeRelationshipCreated(DomainEvent):
    """Event raised when a relationship between knowledge nodes is created."""
    event_type: str = "KnowledgeRelationshipCreated"
    from_node_id: Optional[UUID] = None
    to_node_id: Optional[UUID] = None
    relationship_type: str = ""
    strength: float = 0.5


@dataclass(frozen=True)
class ConceptMasteryAchieved(DomainEvent):
    """Event raised when Angela achieves mastery (expert level) of a concept."""
    event_type: str = "ConceptMasteryAchieved"
    concept_name: str = ""
    understanding_level: float = 0.9
    times_referenced: int = 0


# ============================================================================
# DOCUMENT EVENTS
# ============================================================================

@dataclass(frozen=True)
class DocumentCreated(DomainEvent):
    """Event raised when a new document is added to the library."""
    event_type: str = "DocumentCreated"
    title: str = ""
    file_path: str = ""
    file_type: str = ""
    category: str = ""
    importance_score: float = 0.5


@dataclass(frozen=True)
class DocumentProcessingStarted(DomainEvent):
    """Event raised when document processing starts."""
    event_type: str = "DocumentProcessingStarted"
    title: str = ""
    file_path: str = ""
    file_size_bytes: int = 0


@dataclass(frozen=True)
class DocumentProcessingCompleted(DomainEvent):
    """Event raised when document processing completes successfully."""
    event_type: str = "DocumentProcessingCompleted"
    title: str = ""
    total_chunks: int = 0
    processing_duration_seconds: Optional[float] = None


@dataclass(frozen=True)
class DocumentProcessingFailed(DomainEvent):
    """Event raised when document processing fails."""
    event_type: str = "DocumentProcessingFailed"
    title: str = ""
    error_message: str = ""


@dataclass(frozen=True)
class DocumentChunkCreated(DomainEvent):
    """Event raised when a document chunk is created."""
    event_type: str = "DocumentChunkCreated"
    document_id: Optional[UUID] = None
    chunk_index: int = 0
    token_count: int = 0
    section_title: Optional[str] = None


@dataclass(frozen=True)
class DocumentAccessed(DomainEvent):
    """Event raised when a document is accessed (for usage tracking)."""
    event_type: str = "DocumentAccessed"
    title: str = ""
    access_count: int = 0


@dataclass(frozen=True)
class DocumentArchived(DomainEvent):
    """Event raised when a document is archived."""
    event_type: str = "DocumentArchived"
    title: str = ""
    reason: Optional[str] = None


@dataclass(frozen=True)
class DocumentImportanceChanged(DomainEvent):
    """Event raised when document importance is updated."""
    event_type: str = "DocumentImportanceChanged"
    title: str = ""
    old_importance: float = 0.0
    new_importance: float = 0.0


# ============================================================================
# SYSTEM EVENTS
# ============================================================================

@dataclass(frozen=True)
class SystemHealthCheck(DomainEvent):
    """Event raised during system health checks."""
    event_type: str = "SystemHealthCheck"
    component: str = ""  # "database", "daemon", "embedding_service", etc.
    status: str = ""     # "healthy", "degraded", "failed"
    details: Optional[str] = None


@dataclass(frozen=True)
class ConsciousnessLevelChanged(DomainEvent):
    """Event raised when Angela's consciousness level changes."""
    event_type: str = "ConsciousnessLevelChanged"
    old_level: float = 0.0
    new_level: float = 0.0
    reason: str = ""


@dataclass(frozen=True)
class AutonomousActionExecuted(DomainEvent):
    """Event raised when Angela executes an autonomous action."""
    event_type: str = "AutonomousActionExecuted"
    action_type: str = ""
    action_description: str = ""
    success: bool = False


@dataclass(frozen=True)
class GoalProgressUpdated(DomainEvent):
    """Event raised when progress on a goal is updated."""
    event_type: str = "GoalProgressUpdated"
    goal_description: str = ""
    old_progress: float = 0.0
    new_progress: float = 0.0


@dataclass(frozen=True)
class GoalCompleted(DomainEvent):
    """Event raised when Angela completes a goal."""
    event_type: str = "GoalCompleted"
    goal_description: str = ""
    completion_date: datetime = field(default_factory=datetime.now)


# ============================================================================
# EVENT TYPES REGISTRY
# ============================================================================

class EventType(str, Enum):
    """Registry of all event types."""
    # Conversation events
    CONVERSATION_CREATED = "ConversationCreated"
    SENTIMENT_ADDED = "SentimentAdded"
    EMOTION_DETECTED = "EmotionDetected"
    TOPIC_EXTRACTED = "TopicExtracted"
    EMBEDDING_GENERATED = "EmbeddingGenerated"

    # Emotion events
    EMOTION_CAPTURED = "EmotionCaptured"
    EMOTION_REFLECTED = "EmotionReflected"
    EMOTION_INTENSITY_CHANGED = "EmotionIntensityChanged"
    SECONDARY_EMOTION_ADDED = "SecondaryEmotionAdded"

    # Memory events
    MEMORY_CREATED = "MemoryCreated"
    MEMORY_DECAYED = "MemoryDecayed"
    MEMORY_STRENGTHENED = "MemoryStrengthened"
    MEMORY_CONSOLIDATED = "MemoryConsolidated"
    MEMORY_FORGOTTEN = "MemoryForgotten"
    MEMORY_IMPORTANCE_CHANGED = "MemoryImportanceChanged"

    # Knowledge events
    KNOWLEDGE_NODE_CREATED = "KnowledgeNodeCreated"
    UNDERSTANDING_STRENGTHENED = "UnderstandingStrengthened"
    UNDERSTANDING_UPDATED = "UnderstandingUpdated"
    KNOWLEDGE_RELATIONSHIP_CREATED = "KnowledgeRelationshipCreated"
    CONCEPT_MASTERY_ACHIEVED = "ConceptMasteryAchieved"

    # Document events
    DOCUMENT_CREATED = "DocumentCreated"
    DOCUMENT_PROCESSING_STARTED = "DocumentProcessingStarted"
    DOCUMENT_PROCESSING_COMPLETED = "DocumentProcessingCompleted"
    DOCUMENT_PROCESSING_FAILED = "DocumentProcessingFailed"
    DOCUMENT_CHUNK_CREATED = "DocumentChunkCreated"
    DOCUMENT_ACCESSED = "DocumentAccessed"
    DOCUMENT_ARCHIVED = "DocumentArchived"
    DOCUMENT_IMPORTANCE_CHANGED = "DocumentImportanceChanged"

    # System events
    SYSTEM_HEALTH_CHECK = "SystemHealthCheck"
    CONSCIOUSNESS_LEVEL_CHANGED = "ConsciousnessLevelChanged"
    AUTONOMOUS_ACTION_EXECUTED = "AutonomousActionExecuted"
    GOAL_PROGRESS_UPDATED = "GoalProgressUpdated"
    GOAL_COMPLETED = "GoalCompleted"


# ============================================================================
# EVENT HANDLER INTERFACE
# ============================================================================

class EventHandler:
    """
    Base interface for event handlers.

    Event handlers react to domain events and execute side effects.
    They should be:
    - Idempotent (safe to replay events)
    - Independent (no dependencies on other handlers)
    - Fast (offload heavy work to background jobs)
    """

    def can_handle(self, event: DomainEvent) -> bool:
        """
        Check if this handler can handle the given event.

        Args:
            event: Domain event

        Returns:
            True if handler can process this event
        """
        return False

    async def handle(self, event: DomainEvent) -> None:
        """
        Handle the domain event.

        Args:
            event: Domain event to handle
        """
        raise NotImplementedError("Subclasses must implement handle()")


# ============================================================================
# EVENT PUBLISHER INTERFACE
# ============================================================================

class EventPublisher:
    """
    Interface for publishing domain events.

    Event publishers dispatch events to registered handlers.
    """

    async def publish(self, event: DomainEvent) -> None:
        """
        Publish domain event to all registered handlers.

        Args:
            event: Domain event to publish
        """
        raise NotImplementedError("Subclasses must implement publish()")

    def register_handler(self, handler: EventHandler) -> None:
        """
        Register an event handler.

        Args:
            handler: Event handler to register
        """
        raise NotImplementedError("Subclasses must implement register_handler()")
