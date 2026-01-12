#!/usr/bin/env python3
"""
Domain Entities for Angela AI

Rich domain entities with business logic, not just data containers.
"""

from .conversation import Conversation, Speaker, MessageType, SentimentLabel
from .emotion import Emotion, EmotionType, EmotionalQuality, SharingLevel
from .memory import Memory, MemoryPhase
from .knowledge import KnowledgeNode, KnowledgeRelationship, KnowledgeCategory, UnderstandingLevel
from .document import Document, DocumentChunk, ProcessingStatus, FileType, DocumentCategory
from .goal import Goal, GoalType, GoalStatus, GoalPriority, GoalCategory
from .learning import Learning, LearningCategory, ConfidenceLevel
from .task import Task, TaskType, TaskPriority, SyncStatus
from .note import Note, NoteCategory
from .pattern import Pattern, ResponseType, SituationType
from .journal import Journal
from .angela_message import AngelaMessage
from .project_memory import (
    Project, ProjectSchema, ProjectFlow, ProjectPattern,
    ProjectEntityRelation, ProjectTechnicalDecision, ProjectContext,
    FlowType, SchemaType, PatternType, RelationType,
    DecisionCategory, DecisionStatus
)

__all__ = [
    # Conversation
    "Conversation",
    "Speaker",
    "MessageType",
    "SentimentLabel",

    # Emotion
    "Emotion",
    "EmotionType",
    "EmotionalQuality",
    "SharingLevel",

    # Memory
    "Memory",
    "MemoryPhase",

    # Knowledge
    "KnowledgeNode",
    "KnowledgeRelationship",
    "KnowledgeCategory",
    "UnderstandingLevel",

    # Document
    "Document",
    "DocumentChunk",
    "ProcessingStatus",
    "FileType",
    "DocumentCategory",

    # Goal
    "Goal",
    "GoalType",
    "GoalStatus",
    "GoalPriority",
    "GoalCategory",

    # Learning
    "Learning",
    "LearningCategory",
    "ConfidenceLevel",

    # Task
    "Task",
    "TaskType",
    "TaskPriority",
    "SyncStatus",

    # Note
    "Note",
    "NoteCategory",

    # Pattern
    "Pattern",
    "ResponseType",
    "SituationType",

    # Journal
    "Journal",

    # Angela Message (Batch-24)
    "AngelaMessage",

    # Project Memory
    "Project",
    "ProjectSchema",
    "ProjectFlow",
    "ProjectPattern",
    "ProjectEntityRelation",
    "ProjectTechnicalDecision",
    "ProjectContext",
    "FlowType",
    "SchemaType",
    "PatternType",
    "RelationType",
    "DecisionCategory",
    "DecisionStatus",
]
