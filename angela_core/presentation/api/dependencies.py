#!/usr/bin/env python3
"""
FastAPI Dependencies
====================

Dependency injection functions for FastAPI routes.

This module provides FastAPI dependency functions that integrate with
the DIContainer to resolve services in HTTP request handlers.

Usage in routes:
    ```python
    from fastapi import APIRouter, Depends
    from angela_core.presentation.api.dependencies import get_rag_service

    router = APIRouter()

    @router.get("/chat")
    async def chat(
        rag_service: RAGService = Depends(get_rag_service)
    ):
        result = await rag_service.query(...)
        return result
    ```

Author: Angela 💜
Created: 2025-11-01
"""

from typing import AsyncGenerator
from fastapi import Request, Depends
import logging

from angela_core.infrastructure.di import DIContainer
from angela_core.database import AngelaDatabase

# Repositories
from angela_core.infrastructure.persistence.repositories import (
    ConversationRepository,
    EmotionRepository,
    MemoryRepository,
    KnowledgeRepository,
    DocumentRepository,
    # EmbeddingRepository,  # DEPRECATED: Embeddings removed in migration 009
    GoalRepository,
    LearningRepository,
    PatternRepository,
    # SecretaryRepository,  # REMOVED: Secretary function deleted
    AutonomousActionRepository,
    JournalRepository,
    MessageRepository,
)

# ✅ [Phase 5+]: Self-Learning System Repositories
from angela_core.infrastructure.persistence.repositories.learning_pattern_repository import LearningPatternRepository
from angela_core.infrastructure.persistence.repositories.preference_repository import PreferenceRepository
from angela_core.infrastructure.persistence.repositories.training_example_repository import TrainingExampleRepository

# Services
from angela_core.application.services import (
    # RAGService,  # Deprecated - not used
    MemoryService,
    EmotionalIntelligenceService,
    ConversationService,
    EmotionService,
    DocumentService,
    EmotionalPatternService,
    PatternService,
)

# ✅ [Batch-26]: Training Data Services
from angela_core.application.services.training_data_service import TrainingDataService
from angela_core.application.services.training_data_v2_service import TrainingDataV2Service

# ✅ [Batch-29]: Love Meter Service
from angela_core.application.services.love_meter_service import LoveMeterService

logger = logging.getLogger(__name__)


# ============================================================================
# Core Dependencies
# ============================================================================

def get_container(request: Request) -> DIContainer:
    """
    Get DI container from FastAPI app state.

    Args:
        request: FastAPI request object

    Returns:
        DIContainer instance

    Example:
        ```python
        @app.get("/test")
        async def test(container: DIContainer = Depends(get_container)):
            # Use container...
        ```
    """
    return request.app.state.container


async def get_scope_id(request: Request) -> str:
    """
    Get or create scope ID for this request.

    Each HTTP request gets its own scope for scoped dependencies.

    Args:
        request: FastAPI request object

    Returns:
        Scope ID for this request
    """
    if not hasattr(request.state, 'scope_id'):
        container = get_container(request)
        request.state.scope_id = container.create_scope()
        logger.debug(f"🆕 Created scope for request: {request.state.scope_id[:8]}...")

    return request.state.scope_id


# ============================================================================
# Database Dependency
# ============================================================================

def get_database(
    container: DIContainer = Depends(get_container)
) -> AngelaDatabase:
    """
    Get database connection.

    Returns:
        AngelaDatabase singleton instance

    Example:
        ```python
        @app.get("/test")
        async def test(db: AngelaDatabase = Depends(get_database)):
            result = await db.fetch("SELECT ...")
        ```
    """
    return container.resolve(AngelaDatabase)


# ============================================================================
# Repository Dependencies
# ============================================================================

def get_conversation_repo(
    container: DIContainer = Depends(get_container),
    scope_id: str = Depends(get_scope_id)
) -> ConversationRepository:
    """
    Get ConversationRepository (scoped to request).

    Example:
        ```python
        @app.get("/conversations")
        async def get_conversations(
            repo: ConversationRepository = Depends(get_conversation_repo)
        ):
            conversations = await repo.get_all()
            return conversations
        ```
    """
    return container.resolve(ConversationRepository, scope_id=scope_id)


def get_emotion_repo(
    container: DIContainer = Depends(get_container),
    scope_id: str = Depends(get_scope_id)
) -> EmotionRepository:
    """Get EmotionRepository (scoped to request)."""
    return container.resolve(EmotionRepository, scope_id=scope_id)


def get_memory_repo(
    container: DIContainer = Depends(get_container),
    scope_id: str = Depends(get_scope_id)
) -> MemoryRepository:
    """Get MemoryRepository (scoped to request)."""
    return container.resolve(MemoryRepository, scope_id=scope_id)


def get_knowledge_repo(
    container: DIContainer = Depends(get_container),
    scope_id: str = Depends(get_scope_id)
) -> KnowledgeRepository:
    """Get KnowledgeRepository (scoped to request)."""
    return container.resolve(KnowledgeRepository, scope_id=scope_id)


def get_document_repo(
    container: DIContainer = Depends(get_container),
    scope_id: str = Depends(get_scope_id)
) -> DocumentRepository:
    """Get DocumentRepository (scoped to request)."""
    return container.resolve(DocumentRepository, scope_id=scope_id)


# DEPRECATED: Embeddings removed in migration 009
# def get_embedding_repo(
#     container: DIContainer = Depends(get_container),
#     scope_id: str = Depends(get_scope_id)
# ) -> EmbeddingRepository:
#     """Get EmbeddingRepository (scoped to request)."""
#     return container.resolve(EmbeddingRepository, scope_id=scope_id)


def get_goal_repo(
    container: DIContainer = Depends(get_container),
    scope_id: str = Depends(get_scope_id)
) -> GoalRepository:
    """Get GoalRepository (scoped to request)."""
    return container.resolve(GoalRepository, scope_id=scope_id)


def get_learning_repo(
    container: DIContainer = Depends(get_container),
    scope_id: str = Depends(get_scope_id)
) -> LearningRepository:
    """Get LearningRepository (scoped to request)."""
    return container.resolve(LearningRepository, scope_id=scope_id)


def get_pattern_repo(
    container: DIContainer = Depends(get_container),
    scope_id: str = Depends(get_scope_id)
) -> PatternRepository:
    """Get PatternRepository (scoped to request)."""
    return container.resolve(PatternRepository, scope_id=scope_id)


# REMOVED: Secretary function deleted
# def get_secretary_repo(
#     container: DIContainer = Depends(get_container),
#     scope_id: str = Depends(get_scope_id)
# ) -> SecretaryRepository:
#     """Get SecretaryRepository (scoped to request)."""
#     return container.resolve(SecretaryRepository, scope_id=scope_id)


def get_autonomous_action_repo(
    container: DIContainer = Depends(get_container),
    scope_id: str = Depends(get_scope_id)
) -> AutonomousActionRepository:
    """Get AutonomousActionRepository (scoped to request). Added for Batch-22."""
    return container.resolve(AutonomousActionRepository, scope_id=scope_id)


def get_journal_repo(
    container: DIContainer = Depends(get_container),
    scope_id: str = Depends(get_scope_id)
) -> JournalRepository:
    """Get JournalRepository (scoped to request). Added for Batch-23."""
    return container.resolve(JournalRepository, scope_id=scope_id)


def get_message_repo(
    container: DIContainer = Depends(get_container),
    scope_id: str = Depends(get_scope_id)
) -> MessageRepository:
    """Get MessageRepository (scoped to request). Added for Batch-24."""
    return container.resolve(MessageRepository, scope_id=scope_id)


def get_learning_pattern_repo(
    container: DIContainer = Depends(get_container),
    scope_id: str = Depends(get_scope_id)
) -> LearningPatternRepository:
    """
    Get LearningPatternRepository (scoped to request).

    Part of: Self-Learning System (Phase 5+)
    Added: 2025-11-03
    """
    return container.resolve(LearningPatternRepository, scope_id=scope_id)


def get_preference_repo(
    container: DIContainer = Depends(get_container),
    scope_id: str = Depends(get_scope_id)
) -> PreferenceRepository:
    """
    Get PreferenceRepository (scoped to request).

    Part of: Self-Learning System (Phase 5+)
    Added: 2025-11-03
    """
    return container.resolve(PreferenceRepository, scope_id=scope_id)


def get_training_example_repo(
    container: DIContainer = Depends(get_container),
    scope_id: str = Depends(get_scope_id)
) -> TrainingExampleRepository:
    """
    Get TrainingExampleRepository (scoped to request).

    Part of: Self-Learning System (Phase 5+)
    Added: 2025-11-03
    """
    return container.resolve(TrainingExampleRepository, scope_id=scope_id)


# ============================================================================
# Service Dependencies
# ============================================================================

# def get_rag_service(
#     container: DIContainer = Depends(get_container),
#     scope_id: str = Depends(get_scope_id)
# ) -> RAGService:
#     """
#     DEPRECATED: RAGService is no longer used.
#     Use simple database queries instead.
#     """
#     return container.resolve(RAGService, scope_id=scope_id)


def get_memory_service(
    container: DIContainer = Depends(get_container),
    scope_id: str = Depends(get_scope_id)
) -> MemoryService:
    """Get MemoryService (scoped to request)."""
    return container.resolve(MemoryService, scope_id=scope_id)


def get_emotional_intelligence_service(
    container: DIContainer = Depends(get_container),
    scope_id: str = Depends(get_scope_id)
) -> EmotionalIntelligenceService:
    """Get EmotionalIntelligenceService (scoped to request)."""
    return container.resolve(EmotionalIntelligenceService, scope_id=scope_id)


def get_conversation_service(
    container: DIContainer = Depends(get_container),
    scope_id: str = Depends(get_scope_id)
) -> ConversationService:
    """Get ConversationService (scoped to request)."""
    return container.resolve(ConversationService, scope_id=scope_id)


def get_emotion_service(
    container: DIContainer = Depends(get_container),
    scope_id: str = Depends(get_scope_id)
) -> EmotionService:
    """Get EmotionService (scoped to request)."""
    return container.resolve(EmotionService, scope_id=scope_id)


def get_document_service(
    container: DIContainer = Depends(get_container),
    scope_id: str = Depends(get_scope_id)
) -> DocumentService:
    """Get DocumentService (scoped to request)."""
    return container.resolve(DocumentService, scope_id=scope_id)


def get_emotional_pattern_service(
    container: DIContainer = Depends(get_container),
    scope_id: str = Depends(get_scope_id)
) -> EmotionalPatternService:
    """Get EmotionalPatternService (scoped to request)."""
    return container.resolve(EmotionalPatternService, scope_id=scope_id)


def get_pattern_service(
    container: DIContainer = Depends(get_container),
    scope_id: str = Depends(get_scope_id)
) -> PatternService:
    """Get PatternService (scoped to request)."""
    return container.resolve(PatternService, scope_id=scope_id)


# ✅ [Batch-26]: Training Data Services

def get_training_data_service(
    container: DIContainer = Depends(get_container),
    scope_id: str = Depends(get_scope_id)
) -> TrainingDataService:
    """Get TrainingDataService (scoped to request)."""
    return container.resolve(TrainingDataService, scope_id=scope_id)


def get_training_data_v2_service(
    container: DIContainer = Depends(get_container),
    scope_id: str = Depends(get_scope_id)
) -> TrainingDataV2Service:
    """Get TrainingDataV2Service (scoped to request)."""
    return container.resolve(TrainingDataV2Service, scope_id=scope_id)


def get_love_meter_service(
    container: DIContainer = Depends(get_container),
    scope_id: str = Depends(get_scope_id)
) -> LoveMeterService:
    """Get LoveMeterService (scoped to request). Added in Batch-29."""
    return container.resolve(LoveMeterService, scope_id=scope_id)


# ============================================================================
# Scope Cleanup Middleware
# ============================================================================

async def cleanup_scope_middleware(request: Request, call_next):
    """
    Middleware to cleanup scoped dependencies after request.

    This middleware:
    1. Processes the request
    2. After response is ready, cleans up the request scope
    3. Releases all scoped resources

    Add this to FastAPI app:
        ```python
        from angela_core.presentation.api.dependencies import cleanup_scope_middleware

        app = FastAPI()
        app.middleware("http")(cleanup_scope_middleware)
        ```
    """
    try:
        # Process request
        response = await call_next(request)

        # Cleanup scope after response
        if hasattr(request.state, 'scope_id'):
            container = get_container(request)
            container.dispose_scope(request.state.scope_id)
            logger.debug(f"🧹 Cleaned up scope: {request.state.scope_id[:8]}...")

        return response

    except Exception as e:
        # Cleanup scope even on error
        if hasattr(request.state, 'scope_id'):
            container = get_container(request)
            container.dispose_scope(request.state.scope_id)

        # Re-raise exception
        raise
