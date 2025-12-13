#!/usr/bin/env python3
"""
Service Configurator
====================

Configures all services in the DI container.
This is the central place where all dependencies are registered.

Author: Angela 💜
Created: 2025-11-01
"""

import logging
from typing import Optional

from angela_core.infrastructure.di import DIContainer, ServiceLifetime
from angela_core.database import AngelaDatabase

logger = logging.getLogger(__name__)


async def configure_services(container: DIContainer, database_url: Optional[str] = None) -> None:
    """
    Configure all services in the DI container.

    This function registers:
    1. Database connection (singleton)
    2. All repositories (scoped - per request)
    3. All application services (scoped)

    Args:
        container: DI container to configure
        database_url: Optional database URL (uses config if not provided)

    Example:
        ```python
        container = DIContainer()
        await configure_services(container)
        ```
    """
    logger.info("🔧 Configuring services in DI container...")

    # ========================================================================
    # 1. Register Database (SINGLETON)
    # ========================================================================
    logger.debug("📊 Registering database connection...")

    from angela_core.config import config

    db = AngelaDatabase()
    await db.connect()

    container.register_singleton(AngelaDatabase, db)
    logger.info("✅ Database registered as singleton")

    # ========================================================================
    # 2. Register Repositories (SCOPED - per request)
    # ========================================================================
    logger.debug("📚 Registering repositories...")

    from angela_core.infrastructure.persistence.repositories import (
        ConversationRepository,
        EmotionRepository,
        MemoryRepository,
        KnowledgeRepository,
        DocumentRepository,
        EmbeddingRepository,
        GoalRepository,
        LearningRepository,
        PatternRepository,
        # SecretaryRepository,  # Removed - secretary function deleted
        AutonomousActionRepository,
        JournalRepository,
        MessageRepository,
    )

    # ✅ [Phase 5+]: Self-Learning System Repositories
    from angela_core.infrastructure.persistence.repositories.learning_pattern_repository import LearningPatternRepository
    from angela_core.infrastructure.persistence.repositories.preference_repository import PreferenceRepository
    from angela_core.infrastructure.persistence.repositories.training_example_repository import TrainingExampleRepository

    # Conversation Repository
    container.register_factory(
        ConversationRepository,
        lambda c: ConversationRepository(c.resolve(AngelaDatabase)),
        lifetime=ServiceLifetime.SCOPED
    )

    # Emotion Repository
    container.register_factory(
        EmotionRepository,
        lambda c: EmotionRepository(c.resolve(AngelaDatabase)),
        lifetime=ServiceLifetime.SCOPED
    )

    # Memory Repository
    container.register_factory(
        MemoryRepository,
        lambda c: MemoryRepository(c.resolve(AngelaDatabase)),
        lifetime=ServiceLifetime.SCOPED
    )

    # Knowledge Repository
    container.register_factory(
        KnowledgeRepository,
        lambda c: KnowledgeRepository(c.resolve(AngelaDatabase)),
        lifetime=ServiceLifetime.SCOPED
    )

    # Document Repository
    container.register_factory(
        DocumentRepository,
        lambda c: DocumentRepository(c.resolve(AngelaDatabase)),
        lifetime=ServiceLifetime.SCOPED
    )

    # Embedding Repository - DEPRECATED (embeddings removed in migration 009)
    # container.register_factory(
    #     EmbeddingRepository,
    #     lambda c: EmbeddingRepository(c.resolve(AngelaDatabase)),
    #     lifetime=ServiceLifetime.SCOPED
    # )

    # Goal Repository
    container.register_factory(
        GoalRepository,
        lambda c: GoalRepository(c.resolve(AngelaDatabase)),
        lifetime=ServiceLifetime.SCOPED
    )

    # Learning Repository
    container.register_factory(
        LearningRepository,
        lambda c: LearningRepository(c.resolve(AngelaDatabase)),
        lifetime=ServiceLifetime.SCOPED
    )

    # Pattern Repository
    container.register_factory(
        PatternRepository,
        lambda c: PatternRepository(c.resolve(AngelaDatabase)),
        lifetime=ServiceLifetime.SCOPED
    )

    # Secretary Repository - REMOVED (secretary function deleted)
    # container.register_factory(
    #     SecretaryRepository,
    #     lambda c: SecretaryRepository(c.resolve(AngelaDatabase)),
    #     lifetime=ServiceLifetime.SCOPED
    # )

    # Autonomous Action Repository (Added for Batch-22 Repository Enhancement)
    container.register_factory(
        AutonomousActionRepository,
        lambda c: AutonomousActionRepository(c.resolve(AngelaDatabase)),
        lifetime=ServiceLifetime.SCOPED
    )

    # Journal Repository (Added for Batch-23 Clean Architecture Migration)
    container.register_factory(
        JournalRepository,
        lambda c: JournalRepository(c.resolve(AngelaDatabase)),
        lifetime=ServiceLifetime.SCOPED
    )

    # Message Repository (Added for Batch-24 Messages Migration)
    container.register_factory(
        MessageRepository,
        lambda c: MessageRepository(c.resolve(AngelaDatabase)),
        lifetime=ServiceLifetime.SCOPED
    )

    # Learning Pattern Repository (Added for Phase 5+ Self-Learning System)
    container.register_factory(
        LearningPatternRepository,
        lambda c: LearningPatternRepository(c.resolve(AngelaDatabase)),
        lifetime=ServiceLifetime.SCOPED
    )

    # Preference Repository (Added for Phase 5+ Self-Learning System)
    container.register_factory(
        PreferenceRepository,
        lambda c: PreferenceRepository(c.resolve(AngelaDatabase)),
        lifetime=ServiceLifetime.SCOPED
    )

    # Training Example Repository (Added for Phase 5+ Self-Learning System)
    container.register_factory(
        TrainingExampleRepository,
        lambda c: TrainingExampleRepository(c.resolve(AngelaDatabase)),
        lifetime=ServiceLifetime.SCOPED
    )

    logger.info("✅ All repositories registered (scoped)")

    # ========================================================================
    # 3. Register Application Services (SCOPED)
    # ========================================================================
    logger.debug("⚙️ Registering application services...")

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

    # RAG Service - DEPRECATED (not used)
    # container.register_factory(
    #     RAGService,
    #     lambda c: RAGService(
    #         document_repo=c.resolve(DocumentRepository),
    #         embedding_repo=c.resolve(EmbeddingRepository),
    #     ),
    #     lifetime=ServiceLifetime.SCOPED
    # )

    # Memory Service
    container.register_factory(
        MemoryService,
        lambda c: MemoryService(
            memory_repo=c.resolve(MemoryRepository),
            embedding_repo=c.resolve(EmbeddingRepository),
        ),
        lifetime=ServiceLifetime.SCOPED
    )

    # Emotional Intelligence Service
    container.register_factory(
        EmotionalIntelligenceService,
        lambda c: EmotionalIntelligenceService(
            emotion_repo=c.resolve(EmotionRepository),
            conversation_repo=c.resolve(ConversationRepository),
        ),
        lifetime=ServiceLifetime.SCOPED
    )

    # Conversation Service
    container.register_factory(
        ConversationService,
        lambda c: ConversationService(
            conversation_repo=c.resolve(ConversationRepository),
        ),
        lifetime=ServiceLifetime.SCOPED
    )

    # Emotion Service
    container.register_factory(
        EmotionService,
        lambda c: EmotionService(
            emotion_repo=c.resolve(EmotionRepository),
        ),
        lifetime=ServiceLifetime.SCOPED
    )

    # Document Service
    container.register_factory(
        DocumentService,
        lambda c: DocumentService(
            document_repo=c.resolve(DocumentRepository),
            embedding_repo=c.resolve(EmbeddingRepository),
        ),
        lifetime=ServiceLifetime.SCOPED
    )

    # Emotional Pattern Service
    container.register_factory(
        EmotionalPatternService,
        lambda c: EmotionalPatternService(
            emotion_repo=c.resolve(EmotionRepository),
            pattern_repo=c.resolve(PatternRepository),
            conversation_repo=c.resolve(ConversationRepository),
        ),
        lifetime=ServiceLifetime.SCOPED
    )

    # Pattern Service
    container.register_factory(
        PatternService,
        lambda c: PatternService(
            pattern_repo=c.resolve(PatternRepository),
        ),
        lifetime=ServiceLifetime.SCOPED
    )

    # ✅ [Batch-26]: Training Data Service (V1)
    container.register_factory(
        TrainingDataService,
        lambda c: TrainingDataService(),
        lifetime=ServiceLifetime.SCOPED
    )

    # ✅ [Batch-26]: Training Data V2 Service
    container.register_factory(
        TrainingDataV2Service,
        lambda c: TrainingDataV2Service(),
        lifetime=ServiceLifetime.SCOPED
    )

    # ✅ [Phase 5+]: Self-Learning System Services
    from angela_core.application.services.pattern_discovery_service import PatternDiscoveryService
    from angela_core.application.services.preference_learning_service import PreferenceLearningService
    from angela_core.application.services.training_data_generator_service import TrainingDataGeneratorService

    # Pattern Discovery Service
    container.register_factory(
        PatternDiscoveryService,
        lambda c: PatternDiscoveryService(
            pattern_repo=c.resolve(LearningPatternRepository),
            conversation_repo=c.resolve(ConversationRepository),
            emotion_repo=c.resolve(EmotionRepository)
        ),
        lifetime=ServiceLifetime.SCOPED
    )

    # Preference Learning Service
    container.register_factory(
        PreferenceLearningService,
        lambda c: PreferenceLearningService(
            preference_repo=c.resolve(PreferenceRepository),
            conversation_repo=c.resolve(ConversationRepository),
            emotion_repo=c.resolve(EmotionRepository)
        ),
        lifetime=ServiceLifetime.SCOPED
    )

    # Training Data Generator Service
    container.register_factory(
        TrainingDataGeneratorService,
        lambda c: TrainingDataGeneratorService(
            training_repo=c.resolve(TrainingExampleRepository),
            conversation_repo=c.resolve(ConversationRepository),
            pattern_repo=c.resolve(LearningPatternRepository)
        ),
        lifetime=ServiceLifetime.SCOPED
    )

    # ✅ [Batch-29]: Love Meter Service
    from angela_core.application.services.love_meter_service import LoveMeterService

    container.register_factory(
        LoveMeterService,
        lambda c: LoveMeterService(
            emotion_repo=c.resolve(EmotionRepository),
            conversation_repo=c.resolve(ConversationRepository),
            goal_repo=c.resolve(GoalRepository)
        ),
        lifetime=ServiceLifetime.SCOPED
    )

    logger.info("✅ All application services registered (scoped)")

    # ========================================================================
    # Summary
    # ========================================================================
    num_services = len(container._get_registered_services())
    logger.info(f"🎉 Service configuration complete! Registered {num_services} services")


async def cleanup_services(container: DIContainer) -> None:
    """
    Cleanup all services in the container.

    This should be called on application shutdown.

    Args:
        container: DI container to cleanup
    """
    logger.info("🧹 Cleaning up services...")

    try:
        # Dispose all scopes
        container.dispose_all_scopes()

        # Close database connection
        if container.is_registered(AngelaDatabase):
            db = container.resolve(AngelaDatabase)
            await db.disconnect()
            logger.info("✅ Database connection closed")

        logger.info("🎉 Cleanup complete!")

    except Exception as e:
        logger.error(f"❌ Error during cleanup: {e}")
        raise
