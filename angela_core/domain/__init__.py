#!/usr/bin/env python3
"""
Domain Layer for Angela AI

The domain layer contains the core business logic:
- Entities: Rich domain models with business rules
- Events: Domain events for event-driven architecture
- Interfaces: Service contracts (protocols)
- Value Objects: Immutable value types
"""

# Entities
from .entities import (
    # Conversation
    Conversation, Speaker, MessageType, SentimentLabel,
    # Emotion
    Emotion, EmotionType, EmotionalQuality, SharingLevel,
    # Memory
    Memory, MemoryPhase,
    # Knowledge
    KnowledgeNode, KnowledgeRelationship, KnowledgeCategory, UnderstandingLevel,
    # Document
    Document, DocumentChunk, ProcessingStatus, FileType, DocumentCategory,
    # Goal
    Goal, GoalType, GoalStatus, GoalPriority, GoalCategory,
    # Pattern
    Pattern, ResponseType, SituationType,
    # Learning
    Learning, LearningCategory, ConfidenceLevel,
    # Task
    Task, TaskType, TaskPriority, SyncStatus,
    # Note
    Note, NoteCategory,
)

# Domain Events
from .events import (
    # Base
    DomainEvent, EventType, EventHandler, EventPublisher,
    # Conversation events
    ConversationCreated, SentimentAdded, EmotionDetected, TopicExtracted, EmbeddingGenerated,
    # Emotion events
    EmotionCaptured, EmotionReflected, EmotionIntensityChanged, SecondaryEmotionAdded,
    # Memory events
    MemoryCreated, MemoryDecayed, MemoryStrengthened, MemoryConsolidated,
    MemoryForgotten, MemoryImportanceChanged,
    # Knowledge events
    KnowledgeNodeCreated, UnderstandingStrengthened, UnderstandingUpdated,
    KnowledgeRelationshipCreated, ConceptMasteryAchieved,
    # Document events
    DocumentCreated, DocumentProcessingStarted, DocumentProcessingCompleted,
    DocumentProcessingFailed, DocumentChunkCreated, DocumentAccessed,
    DocumentArchived, DocumentImportanceChanged,
    # System events
    SystemHealthCheck, ConsciousnessLevelChanged, AutonomousActionExecuted,
    GoalProgressUpdated, GoalCompleted,
)

__all__ = [
    # Entities - Conversation
    "Conversation", "Speaker", "MessageType", "SentimentLabel",
    # Entities - Emotion
    "Emotion", "EmotionType", "EmotionalQuality", "SharingLevel",
    # Entities - Memory
    "Memory", "MemoryPhase",
    # Entities - Knowledge
    "KnowledgeNode", "KnowledgeRelationship", "KnowledgeCategory", "UnderstandingLevel",
    # Entities - Document
    "Document", "DocumentChunk", "ProcessingStatus", "FileType", "DocumentCategory",
    # Entities - Goal
    "Goal", "GoalType", "GoalStatus", "GoalPriority", "GoalCategory",
    # Entities - Pattern
    "Pattern", "ResponseType", "SituationType",
    # Entities - Learning
    "Learning", "LearningCategory", "ConfidenceLevel",
    # Entities - Task
    "Task", "TaskType", "TaskPriority", "SyncStatus",
    # Entities - Note
    "Note", "NoteCategory",

    # Events - Base
    "DomainEvent", "EventType", "EventHandler", "EventPublisher",
    # Events - Conversation
    "ConversationCreated", "SentimentAdded", "EmotionDetected", "TopicExtracted", "EmbeddingGenerated",
    # Events - Emotion
    "EmotionCaptured", "EmotionReflected", "EmotionIntensityChanged", "SecondaryEmotionAdded",
    # Events - Memory
    "MemoryCreated", "MemoryDecayed", "MemoryStrengthened", "MemoryConsolidated",
    "MemoryForgotten", "MemoryImportanceChanged",
    # Events - Knowledge
    "KnowledgeNodeCreated", "UnderstandingStrengthened", "UnderstandingUpdated",
    "KnowledgeRelationshipCreated", "ConceptMasteryAchieved",
    # Events - Document
    "DocumentCreated", "DocumentProcessingStarted", "DocumentProcessingCompleted",
    "DocumentProcessingFailed", "DocumentChunkCreated", "DocumentAccessed",
    "DocumentArchived", "DocumentImportanceChanged",
    # Events - System
    "SystemHealthCheck", "ConsciousnessLevelChanged", "AutonomousActionExecuted",
    "GoalProgressUpdated", "GoalCompleted",
]
