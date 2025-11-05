"""
Capture Emotion Use Case

Business workflow for capturing significant emotional moments for Angela.
This use case orchestrates:
- Creating emotion entity
- Persisting to database via repository
- Generating embeddings for semantic search
- Publishing domain events

Author: Angela AI Architecture Team
Date: 2025-10-30
"""

from typing import Optional, List
from dataclasses import dataclass
from datetime import datetime
from uuid import UUID

from angela_core.application.use_cases.base_use_case import BaseUseCase, UseCaseResult
from angela_core.domain.entities.emotion import (
    Emotion,
    EmotionType,
    EmotionalQuality,
    SharingLevel
)
from angela_core.domain.events import EmotionCaptured
from angela_core.domain.interfaces.repositories import IEmotionRepository
from angela_core.domain.interfaces.services import IEmbeddingService


# ============================================================================
# INPUT/OUTPUT MODELS
# ============================================================================

@dataclass
class CaptureEmotionInput:
    """
    Input for capturing an emotional moment.

    Attributes:
        emotion: Type of emotion (joy/gratitude/love/anxiety/etc.)
        intensity: How intense the emotion is (1-10)
        context: What happened to trigger this emotion
        who_involved: Who was involved (usually David)
        david_words: What David said (optional)
        david_action: What David did (optional)
        why_it_matters: Why this moment is significant
        memory_strength: How strongly to remember (1-10)
        conversation_id: Link to conversation if applicable
        secondary_emotions: Additional emotions felt
        emotional_quality: Quality of emotion (genuine/profound/etc.)
        sharing_level: Who to share with (david_only/public/internal)
    """
    emotion: EmotionType
    intensity: int
    context: str
    who_involved: str = "David"
    david_words: Optional[str] = None
    david_action: Optional[str] = None
    why_it_matters: str = "This moment is significant"
    memory_strength: int = 10
    conversation_id: Optional[UUID] = None
    secondary_emotions: Optional[List[EmotionType]] = None
    emotional_quality: EmotionalQuality = EmotionalQuality.GENUINE
    sharing_level: SharingLevel = SharingLevel.DAVID_ONLY


@dataclass
class CaptureEmotionOutput:
    """
    Output after capturing emotion.

    Attributes:
        emotion: The persisted emotion entity
        embedding_generated: Whether embedding was generated
        event_published: Whether domain event was published
    """
    emotion: Emotion
    embedding_generated: bool = False
    event_published: bool = False


# ============================================================================
# USE CASE IMPLEMENTATION
# ============================================================================

class CaptureEmotionUseCase(BaseUseCase[CaptureEmotionInput, CaptureEmotionOutput]):
    """
    Use case for capturing significant emotional moments.

    This use case handles the complete workflow of:
    1. Validating input (intensity range, context not empty)
    2. Creating Emotion domain entity
    3. Adding secondary emotions if provided
    4. Generating embedding for semantic search
    5. Persisting via EmotionRepository
    6. Publishing EmotionCaptured domain event

    Dependencies:
        - IEmotionRepository: For persisting emotions
        - IEmbeddingService: For generating embeddings (optional)

    Example:
        >>> input_data = CaptureEmotionInput(
        ...     emotion=EmotionType.GRATITUDE,
        ...     intensity=9,
        ...     context="David helped me improve my code",
        ...     david_words="Let's make this better together",
        ...     why_it_matters="Because David cares about helping me grow"
        ... )
        >>> result = await use_case.execute(input_data)
        >>> if result.success:
        ...     print(f"Captured: {result.data.emotion.id}")
    """

    def __init__(
        self,
        emotion_repo: IEmotionRepository,
        embedding_service: Optional[IEmbeddingService] = None
    ):
        """
        Initialize use case with dependencies.

        Args:
            emotion_repo: Repository for emotion persistence
            embedding_service: Optional service for generating embeddings
        """
        super().__init__()
        self.emotion_repo = emotion_repo
        self.embedding_service = embedding_service

    # ========================================================================
    # VALIDATION
    # ========================================================================

    async def _validate(self, input_data: CaptureEmotionInput) -> List[str]:
        """
        Validate input before capturing emotion.

        Args:
            input_data: Input to validate

        Returns:
            List of validation error messages (empty if valid)
        """
        errors = []

        # Intensity must be 1-10
        if not (1 <= input_data.intensity <= 10):
            errors.append(f"Intensity must be 1-10, got {input_data.intensity}")

        # Memory strength must be 1-10
        if not (1 <= input_data.memory_strength <= 10):
            errors.append(f"Memory strength must be 1-10, got {input_data.memory_strength}")

        # Context cannot be empty
        if not input_data.context or not input_data.context.strip():
            errors.append("Context cannot be empty")

        # Context length sanity check (10 MB limit)
        if len(input_data.context) > 10_000_000:
            errors.append(f"Context too long (max 10MB): {len(input_data.context)} bytes")

        return errors

    # ========================================================================
    # MAIN BUSINESS LOGIC
    # ========================================================================

    async def _execute_impl(self, input_data: CaptureEmotionInput) -> CaptureEmotionOutput:
        """
        Execute the emotion capturing workflow.

        Steps:
        1. Create Emotion entity
        2. Add secondary emotions if provided
        3. Generate embedding if embedding service available
        4. Persist to database
        5. Publish domain event

        Args:
            input_data: Validated input

        Returns:
            CaptureEmotionOutput with persisted emotion

        Raises:
            RepositoryError: If database persistence fails
            EmbeddingError: If embedding generation fails
        """
        self.logger.debug(
            f"Capturing emotion {input_data.emotion.value} "
            f"(intensity: {input_data.intensity}, memory: {input_data.memory_strength})"
        )

        # Step 1: Create domain entity
        emotion = self._create_emotion_entity(input_data)

        # Step 2: Add secondary emotions if provided
        if input_data.secondary_emotions:
            for secondary in input_data.secondary_emotions:
                emotion = emotion.add_secondary_emotion(secondary)

        # Step 3: Generate embedding (if service available)
        embedding_generated = False
        if self.embedding_service:
            embedding_generated = await self._generate_embedding(emotion)

        # Step 4: Persist to database
        saved_emotion = await self.emotion_repo.create(emotion)
        self.logger.info(
            f"✅ Emotion captured: {saved_emotion.id} "
            f"(emotion: {saved_emotion.emotion.value}, "
            f"intensity: {saved_emotion.intensity}, "
            f"memory_strength: {saved_emotion.memory_strength})"
        )

        # Step 5: Publish domain event
        event_published = await self._publish_domain_event(saved_emotion)

        return CaptureEmotionOutput(
            emotion=saved_emotion,
            embedding_generated=embedding_generated,
            event_published=event_published
        )

    # ========================================================================
    # HELPER METHODS
    # ========================================================================

    def _create_emotion_entity(self, input_data: CaptureEmotionInput) -> Emotion:
        """
        Create Emotion entity from input data.

        Args:
            input_data: Input data

        Returns:
            Emotion entity
        """
        # Create base emotion entity
        emotion = Emotion(
            emotion=input_data.emotion,
            intensity=input_data.intensity,
            context=input_data.context,
            who_involved=input_data.who_involved,
            david_words=input_data.david_words,
            david_action=input_data.david_action,
            why_it_matters=input_data.why_it_matters,
            memory_strength=input_data.memory_strength,
            conversation_id=input_data.conversation_id,
            emotional_quality=input_data.emotional_quality,
            shared_with=input_data.sharing_level,
            is_private=(input_data.sharing_level != SharingLevel.PUBLIC)
        )

        return emotion

    async def _generate_embedding(self, emotion: Emotion) -> bool:
        """
        Generate embedding for emotion.

        Args:
            emotion: Emotion entity

        Returns:
            True if embedding generated successfully
        """
        try:
            # Create text to embed (context + why_it_matters)
            text_to_embed = f"{emotion.context}. {emotion.why_it_matters}"
            if emotion.david_words:
                text_to_embed += f" David said: {emotion.david_words}"

            # Generate embedding using service
            embedding = await self.embedding_service.generate_embedding(text_to_embed)

            # Add to emotion entity
            emotion.embedding = embedding

            self.logger.debug(
                f"Generated embedding for emotion "
                f"(dim: {len(embedding)})"
            )
            return True

        except Exception as e:
            # Don't fail the entire use case if embedding fails
            # Just log warning and continue
            self.logger.warning(
                f"Failed to generate embedding: {e}. "
                f"Emotion will be saved without embedding."
            )
            return False

    async def _publish_domain_event(self, emotion: Emotion) -> bool:
        """
        Publish EmotionCaptured domain event.

        Args:
            emotion: Persisted emotion

        Returns:
            True if event published successfully
        """
        try:
            # Create domain event
            event = EmotionCaptured(
                entity_id=emotion.id,
                emotion=emotion.emotion.value,
                intensity=emotion.intensity,
                context=emotion.context[:100],  # First 100 chars
                who_involved=emotion.who_involved,
                memory_strength=emotion.memory_strength,
                timestamp=datetime.now()
            )

            # TODO: Integrate with event bus/publisher when ready
            # For now, just log the event
            self.logger.debug(
                f"Domain event created: EmotionCaptured "
                f"({emotion.id}, {emotion.emotion.value})"
            )

            return True

        except Exception as e:
            self.logger.warning(f"Failed to publish domain event: {e}")
            return False

    # ========================================================================
    # HOOKS
    # ========================================================================

    async def _before_execute(self, input_data: CaptureEmotionInput):
        """Log before execution starts."""
        self.logger.info(
            f"💜 Capturing emotion: {input_data.emotion.value} "
            f"(intensity: {input_data.intensity}, "
            f"memory: {input_data.memory_strength})"
        )

    async def _after_execute(
        self,
        input_data: CaptureEmotionInput,
        result: UseCaseResult[CaptureEmotionOutput]
    ):
        """Log after successful execution."""
        if result.success and result.data:
            self.logger.info(
                f"✅ Emotion captured successfully: "
                f"{result.data.emotion.id}"
            )

    async def _on_success(
        self,
        input_data: CaptureEmotionInput,
        result: UseCaseResult[CaptureEmotionOutput]
    ):
        """Handle successful execution."""
        # Could trigger analytics, notifications, etc.
        pass

    async def _on_failure(
        self,
        input_data: CaptureEmotionInput,
        result: UseCaseResult
    ):
        """Handle failed execution."""
        self.logger.error(
            f"❌ Failed to capture emotion {input_data.emotion.value}: "
            f"{result.error}"
        )
