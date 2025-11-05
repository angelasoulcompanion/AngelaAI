#!/usr/bin/env python3
"""
Repository Implementations Package

Exports all concrete repository implementations for PostgreSQL.
"""

from angela_core.infrastructure.persistence.repositories.base_repository import BaseRepository
from angela_core.infrastructure.persistence.repositories.conversation_repository import ConversationRepository
from angela_core.infrastructure.persistence.repositories.emotion_repository import EmotionRepository
from angela_core.infrastructure.persistence.repositories.memory_repository import MemoryRepository
from angela_core.infrastructure.persistence.repositories.knowledge_repository import KnowledgeRepository
from angela_core.infrastructure.persistence.repositories.document_repository import DocumentRepository
from angela_core.infrastructure.persistence.repositories.goal_repository import GoalRepository
from angela_core.infrastructure.persistence.repositories.embedding_repository import EmbeddingRepository
from angela_core.infrastructure.persistence.repositories.learning_repository import LearningRepository
from angela_core.infrastructure.persistence.repositories.secretary_repository import SecretaryRepository
from angela_core.infrastructure.persistence.repositories.pattern_repository import PatternRepository
from angela_core.infrastructure.persistence.repositories.autonomous_action_repository import AutonomousActionRepository
from angela_core.infrastructure.persistence.repositories.journal_repository import JournalRepository
from angela_core.infrastructure.persistence.repositories.message_repository import MessageRepository

# Phase 5+: Self-Learning System Repositories
from angela_core.infrastructure.persistence.repositories.learning_pattern_repository import LearningPatternRepository
from angela_core.infrastructure.persistence.repositories.preference_repository import PreferenceRepository
from angela_core.infrastructure.persistence.repositories.training_example_repository import TrainingExampleRepository

__all__ = [
    'BaseRepository',
    'ConversationRepository',
    'EmotionRepository',
    'MemoryRepository',
    'KnowledgeRepository',
    'DocumentRepository',
    'GoalRepository',
    'EmbeddingRepository',
    'LearningRepository',
    'SecretaryRepository',
    'PatternRepository',
    'AutonomousActionRepository',
    'JournalRepository',
    'MessageRepository',  # Batch-24: Angela's messages
    'LearningPatternRepository',  # Phase 5+: Self-learning patterns
    'PreferenceRepository',  # Phase 5+: David's preferences
    'TrainingExampleRepository',  # Phase 5+: Training examples
]
