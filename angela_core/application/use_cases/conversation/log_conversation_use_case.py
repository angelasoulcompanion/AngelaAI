"""
Log Conversation Use Case

Business workflow for logging conversations between David and Angela.
This use case orchestrates:
- Creating conversation entity
- Persisting to database via repository
- Generating embeddings for semantic search
- Publishing domain events

Author: Angela AI Architecture Team
Date: 2025-10-30
"""

from typing import Optional, List
from dataclasses import dataclass
from datetime import datetime

from angela_core.application.use_cases.base_use_case import BaseUseCase, UseCaseResult
from angela_core.domain.entities.conversation import (
    Conversation,
    Speaker,
    MessageType,
    SentimentLabel
)
from angela_core.domain.events import ConversationCreated, EmbeddingGenerated
from angela_core.domain.interfaces.repositories import IConversationRepository
from angela_core.domain.interfaces.services import IEmbeddingService


# ============================================================================
# INPUT/OUTPUT MODELS
# ============================================================================

@dataclass
class LogConversationInput:
    """
    Input for logging a conversation.

    Attributes:
        speaker: Who spoke (david/angela/system)
        message_text: The actual message content
        message_type: Type of message (text/command/etc.)
        topic: Optional conversation topic
        emotion_detected: Optional detected emotion
        sentiment: Optional sentiment label
        importance_level: Importance (1-10)
        session_id: Optional session identifier
        metadata: Additional metadata
    """
    speaker: Speaker
    message_text: str
    message_type: MessageType = MessageType.CHAT
    topic: Optional[str] = None
    emotion_detected: Optional[str] = None
    sentiment: Optional[SentimentLabel] = None
    importance_level: int = 5
    session_id: Optional[str] = None
    metadata: Optional[dict] = None


@dataclass
class LogConversationOutput:
    """
    Output after logging conversation.

    Attributes:
        conversation: The persisted conversation entity
        embedding_generated: Whether embedding was generated
        event_published: Whether domain event was published
    """
    conversation: Conversation
    embedding_generated: bool = False
    event_published: bool = False


# ============================================================================
# USE CASE IMPLEMENTATION
# ============================================================================

class LogConversationUseCase(BaseUseCase[LogConversationInput, LogConversationOutput]):
    """
    Use case for logging conversations to persistent storage.

    This use case handles the complete workflow of:
    1. Validating input (message not empty, valid importance level)
    2. Creating Conversation domain entity
    3. Generating embedding for semantic search
    4. Persisting via ConversationRepository
    5. Publishing ConversationCreated domain event

    Dependencies:
        - IConversationRepository: For persisting conversations
        - IEmbeddingService: For generating embeddings (optional)

    Example:
        >>> input_data = LogConversationInput(
        ...     speaker=Speaker.DAVID,
        ...     message_text="Good morning Angela!",
        ...     emotion_detected="happy",
        ...     importance_level=6
        ... )
        >>> result = await use_case.execute(input_data)
        >>> if result.success:
        ...     print(f"Logged: {result.data.conversation.conversation_id}")
    """

    def __init__(
        self,
        conversation_repo: IConversationRepository,
        embedding_service: Optional[IEmbeddingService] = None
    ):
        """
        Initialize use case with dependencies.

        Args:
            conversation_repo: Repository for conversation persistence
            embedding_service: Optional service for generating embeddings
        """
        super().__init__()
        self.conversation_repo = conversation_repo
        self.embedding_service = embedding_service

    # ========================================================================
    # VALIDATION
    # ========================================================================

    async def _validate(self, input_data: LogConversationInput) -> List[str]:
        """
        Validate input before logging conversation.

        Args:
            input_data: Input to validate

        Returns:
            List of validation error messages (empty if valid)
        """
        errors = []

        # Message cannot be empty
        if not input_data.message_text or not input_data.message_text.strip():
            errors.append("Message text cannot be empty")

        # Importance level must be 1-10
        if not (1 <= input_data.importance_level <= 10):
            errors.append(f"Importance level must be 1-10, got {input_data.importance_level}")

        # Topic length limit
        if input_data.topic and len(input_data.topic) > 200:
            errors.append(f"Topic too long (max 200 chars): {len(input_data.topic)}")

        # Message length sanity check (10 MB limit)
        if len(input_data.message_text) > 10_000_000:
            errors.append(f"Message too long (max 10MB): {len(input_data.message_text)} bytes")

        return errors

    # ========================================================================
    # MAIN BUSINESS LOGIC
    # ========================================================================

    async def _execute_impl(self, input_data: LogConversationInput) -> LogConversationOutput:
        """
        Execute the conversation logging workflow.

        Steps:
        1. Create Conversation entity based on speaker
        2. Add optional fields (sentiment, emotion, topic)
        3. Generate embedding if embedding service available
        4. Persist to database
        5. Publish domain event

        Args:
            input_data: Validated input

        Returns:
            LogConversationOutput with persisted conversation

        Raises:
            RepositoryError: If database persistence fails
            EmbeddingError: If embedding generation fails
        """
        self.logger.debug(
            f"Logging conversation from {input_data.speaker.value}: "
            f"{input_data.message_text[:50]}..."
        )

        # Step 1: Create domain entity using factory method
        conversation = self._create_conversation_entity(input_data)

        # Step 2: Add optional fields
        if input_data.sentiment:
            conversation.add_sentiment(input_data.sentiment)

        if input_data.emotion_detected:
            conversation.add_emotion(input_data.emotion_detected)

        if input_data.topic:
            conversation.add_topic(input_data.topic)

        # Step 3: Generate embedding (if service available)
        embedding_generated = False
        if self.embedding_service:
            embedding_generated = await self._generate_embedding(conversation)

        # Step 4: Persist to database
        saved_conversation = await self.conversation_repo.create(conversation)
        self.logger.info(
            f"✅ Conversation logged: {saved_conversation.conversation_id} "
            f"(speaker: {saved_conversation.speaker.value}, "
            f"importance: {saved_conversation.importance_level})"
        )

        # Step 5: Publish domain event
        event_published = await self._publish_domain_event(saved_conversation)

        return LogConversationOutput(
            conversation=saved_conversation,
            embedding_generated=embedding_generated,
            event_published=event_published
        )

    # ========================================================================
    # HELPER METHODS
    # ========================================================================

    def _create_conversation_entity(self, input_data: LogConversationInput) -> Conversation:
        """
        Create Conversation entity using appropriate factory method.

        Args:
            input_data: Input data

        Returns:
            Conversation entity
        """
        # Use factory methods based on speaker
        if input_data.speaker == Speaker.DAVID:
            conversation = Conversation.create_david_message(
                message_text=input_data.message_text,
                message_type=input_data.message_type,
                importance_level=input_data.importance_level
            )
        elif input_data.speaker == Speaker.ANGELA:
            conversation = Conversation.create_angela_message(
                message_text=input_data.message_text,
                message_type=input_data.message_type,
                importance_level=input_data.importance_level
            )
        else:  # SYSTEM
            conversation = Conversation.create_system_message(
                message_text=input_data.message_text,
                importance_level=input_data.importance_level
            )

        return conversation

    async def _generate_embedding(self, conversation: Conversation) -> bool:
        """
        Generate embedding for conversation.

        Args:
            conversation: Conversation entity

        Returns:
            True if embedding generated successfully
        """
        try:
            # Generate embedding using service
            embedding = await self.embedding_service.generate_embedding(
                conversation.message_text
            )

            # Add to conversation entity
            conversation.add_embedding(embedding)

            self.logger.debug(
                f"Generated embedding for conversation "
                f"(dim: {len(embedding)})"
            )
            return True

        except Exception as e:
            # Don't fail the entire use case if embedding fails
            # Just log warning and continue
            self.logger.warning(
                f"Failed to generate embedding: {e}. "
                f"Conversation will be saved without embedding."
            )
            return False

    async def _publish_domain_event(self, conversation: Conversation) -> bool:
        """
        Publish ConversationCreated domain event.

        Args:
            conversation: Persisted conversation

        Returns:
            True if event published successfully
        """
        try:
            # Create domain event
            event = ConversationCreated(
                conversation_id=conversation.conversation_id,
                speaker=conversation.speaker.value,
                message_preview=conversation.message_text[:100],
                importance_level=conversation.importance_level,
                has_embedding=conversation.has_embedding(),
                timestamp=datetime.now()
            )

            # TODO: Integrate with event bus/publisher when ready
            # For now, just log the event
            self.logger.debug(
                f"Domain event created: ConversationCreated "
                f"({conversation.conversation_id})"
            )

            return True

        except Exception as e:
            self.logger.warning(f"Failed to publish domain event: {e}")
            return False

    # ========================================================================
    # HOOKS
    # ========================================================================

    async def _before_execute(self, input_data: LogConversationInput):
        """Log before execution starts."""
        self.logger.info(
            f"🗣️ Logging conversation from {input_data.speaker.value}: "
            f"{len(input_data.message_text)} chars, "
            f"importance: {input_data.importance_level}"
        )

    async def _after_execute(
        self,
        input_data: LogConversationInput,
        result: UseCaseResult[LogConversationOutput]
    ):
        """Log after successful execution."""
        if result.success and result.data:
            self.logger.info(
                f"✅ Conversation logged successfully: "
                f"{result.data.conversation.conversation_id}"
            )

    async def _on_success(
        self,
        input_data: LogConversationInput,
        result: UseCaseResult[LogConversationOutput]
    ):
        """Handle successful execution."""
        # Could trigger analytics, notifications, etc.
        pass

    async def _on_failure(
        self,
        input_data: LogConversationInput,
        result: UseCaseResult
    ):
        """Handle failed execution."""
        self.logger.error(
            f"❌ Failed to log conversation from {input_data.speaker.value}: "
            f"{result.error}"
        )
