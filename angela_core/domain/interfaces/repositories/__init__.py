"""
Repository Interfaces for Angela AI.

Defines contracts for all data access operations.
Split into domain-specific modules for maintainability.

All interfaces are re-exported here for backward compatibility:
    from angela_core.domain.interfaces.repositories import IRepository
"""

from .base import IRepository
from .conversation import IConversationRepository
from .emotion import IEmotionRepository
from .document import IDocumentRepository
from .memory import IMemoryRepository
from .knowledge import IKnowledgeRepository
from .goal import IGoalRepository
from .embedding import IEmbeddingRepository
from .learning import ILearningRepository
from .pattern import IPatternRepository
from .journal import IJournalRepository
from .message import IMessageRepository
from .learning_pattern import ILearningPatternRepository
from .preference import IPreferenceRepository
from .training_example import ITrainingExampleRepository

__all__ = [
    'IRepository',
    'IConversationRepository',
    'IEmotionRepository',
    'IDocumentRepository',
    'IMemoryRepository',
    'IKnowledgeRepository',
    'IGoalRepository',
    'IEmbeddingRepository',
    'ILearningRepository',
    'IPatternRepository',
    'IJournalRepository',
    'IMessageRepository',
    'ILearningPatternRepository',
    'IPreferenceRepository',
    'ITrainingExampleRepository',
]
