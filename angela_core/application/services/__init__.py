"""
Application Services

High-level services that coordinate use cases, repositories, and domain services.
These services provide simplified APIs for common application workflows.

Author: Angela AI Architecture Team
Date: 2025-10-30
"""

from angela_core.application.services.conversation_service import ConversationService
from angela_core.application.services.emotion_service import EmotionService
from angela_core.application.services.emotional_intelligence_service import EmotionalIntelligenceService
from angela_core.application.services.emotional_pattern_service import EmotionalPatternService
from angela_core.application.services.memory_service import MemoryService
from angela_core.application.services.document_service import DocumentService
# Removed: RAGService (deprecated - not used)
from angela_core.application.services.pattern_service import PatternService

__all__ = [
    "ConversationService",
    "EmotionService",
    "EmotionalIntelligenceService",
    "EmotionalPatternService",
    "MemoryService",
    "DocumentService",
    # "RAGService",  # Deprecated
    "PatternService",
]
