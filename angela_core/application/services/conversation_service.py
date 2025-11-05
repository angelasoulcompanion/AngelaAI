"""
Conversation Service

High-level application service for conversation management.
Coordinates use cases, repositories, and services for conversation operations.

Author: Angela AI Architecture Team
Date: 2025-10-30
"""

import logging
from typing import Optional, List, Dict, Any
from datetime import datetime, timedelta
from uuid import UUID

from angela_core.database import AngelaDatabase
from angela_core.domain.entities.conversation import Speaker, MessageType, SentimentLabel
from angela_core.infrastructure.persistence.repositories import ConversationRepository
from angela_core.application.use_cases.conversation import (
    LogConversationUseCase,
    LogConversationInput
)


class ConversationService:
    """
    High-level service for conversation management.

    This service provides a simplified API for:
    - Logging conversations
    - Retrieving conversations
    - Searching conversations
    - Analyzing conversation history

    Coordinates:
    - LogConversationUseCase
    - ConversationRepository
    - EmbeddingService (optional)

    Example:
        >>> service = ConversationService(db)
        >>> result = await service.log_conversation(
        ...     speaker="david",
        ...     message_text="Good morning Angela!",
        ...     emotion_detected="happy"
        ... )
        >>> if result["success"]:
        ...     print(f"Logged: {result['conversation_id']}")
    """

    def __init__(
        self,
        db: AngelaDatabase,
        embedding_service: Optional[Any] = None
    ):
        """
        Initialize conversation service with dependencies.

        Args:
            db: Database connection
            embedding_service: Optional embedding service
        """
        self.db = db
        self.logger = logging.getLogger(__name__)

        # Initialize repository
        self.conversation_repo = ConversationRepository(db)

        # Initialize use cases
        self.log_conversation_use_case = LogConversationUseCase(
            conversation_repo=self.conversation_repo,
            embedding_service=embedding_service
        )

    # ========================================================================
    # HIGH-LEVEL API - CONVERSATION LOGGING
    # ========================================================================

    async def log_conversation(
        self,
        speaker: str,
        message_text: str,
        message_type: str = "text",
        topic: Optional[str] = None,
        emotion_detected: Optional[str] = None,
        sentiment_score: Optional[float] = None,
        importance_level: int = 5,
        session_id: Optional[str] = None,
        metadata: Optional[Dict] = None
    ) -> Dict[str, Any]:
        """
        Log a conversation between David and Angela.

        Args:
            speaker: Who spoke ('david', 'angela', or 'system')
            message_text: The message content
            message_type: Type of message ('text', 'command', etc.)
            topic: Optional topic
            emotion_detected: Optional detected emotion
            sentiment_score: Optional sentiment (-1.0 to 1.0)
            importance_level: Importance (1-10)
            session_id: Optional session identifier
            metadata: Additional metadata

        Returns:
            {
                "success": bool,
                "conversation_id": UUID (if success),
                "embedding_generated": bool (if success),
                "error": str (if failure)
            }
        """
        try:
            # Convert string speaker to enum
            speaker_enum = Speaker(speaker.lower())

            # Convert string message_type to enum
            message_type_enum = MessageType(message_type.lower())

            # Convert sentiment score to label
            sentiment_label = None
            if sentiment_score is not None:
                sentiment_label = SentimentLabel.from_score(sentiment_score)

            # Create input
            input_data = LogConversationInput(
                speaker=speaker_enum,
                message_text=message_text,
                message_type=message_type_enum,
                topic=topic,
                emotion_detected=emotion_detected,
                sentiment=sentiment_label,
                importance_level=importance_level,
                session_id=session_id,
                metadata=metadata
            )

            # Execute use case
            result = await self.log_conversation_use_case.execute(input_data)

            # Return simplified result
            if result.success:
                return {
                    "success": True,
                    "conversation_id": str(result.data.conversation.conversation_id),
                    "embedding_generated": result.data.embedding_generated,
                    "speaker": speaker,
                    "importance_level": importance_level
                }
            else:
                return {
                    "success": False,
                    "error": result.error
                }

        except Exception as e:
            self.logger.error(f"Error logging conversation: {e}")
            return {
                "success": False,
                "error": str(e)
            }

    # ========================================================================
    # HIGH-LEVEL API - CONVERSATION RETRIEVAL
    # ========================================================================

    async def get_conversation(self, conversation_id: UUID) -> Optional[Dict[str, Any]]:
        """
        Get a single conversation by ID.

        Args:
            conversation_id: Conversation UUID

        Returns:
            Conversation dict or None if not found
        """
        try:
            conversation = await self.conversation_repo.get_by_id(conversation_id)

            if conversation:
                return self._conversation_to_dict(conversation)
            return None

        except Exception as e:
            self.logger.error(f"Error getting conversation: {e}")
            return None

    async def get_recent_conversations(
        self,
        days: int = 7,
        speaker: Optional[str] = None,
        min_importance: Optional[int] = None,
        limit: int = 100
    ) -> List[Dict[str, Any]]:
        """
        Get recent conversations.

        Args:
            days: Number of days to look back
            speaker: Optional filter by speaker
            min_importance: Optional minimum importance level
            limit: Maximum results

        Returns:
            List of conversation dicts
        """
        try:
            conversations = await self.conversation_repo.get_recent_conversations(
                days=days,
                speaker=speaker,
                min_importance=min_importance,
                limit=limit
            )

            return [self._conversation_to_dict(c) for c in conversations]

        except Exception as e:
            self.logger.error(f"Error getting recent conversations: {e}")
            return []

    async def search_conversations(
        self,
        query: str,
        limit: int = 50
    ) -> List[Dict[str, Any]]:
        """
        Full-text search in conversations.

        Args:
            query: Search query
            limit: Maximum results

        Returns:
            List of matching conversation dicts
        """
        try:
            conversations = await self.conversation_repo.search_by_text(
                query=query,
                limit=limit
            )

            return [self._conversation_to_dict(c) for c in conversations]

        except Exception as e:
            self.logger.error(f"Error searching conversations: {e}")
            return []

    # ========================================================================
    # HIGH-LEVEL API - CONVERSATION ANALYTICS
    # ========================================================================

    async def get_conversation_statistics(
        self,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None
    ) -> Dict[str, Any]:
        """
        Get conversation statistics.

        Args:
            start_date: Optional start date
            end_date: Optional end date

        Returns:
            {
                "total_conversations": int,
                "by_speaker": {"david": int, "angela": int, "system": int},
                "by_importance": {1: int, 2: int, ...},
                "avg_importance": float,
                "with_embeddings": int
            }
        """
        try:
            # Default to last 30 days if not specified
            if start_date is None:
                start_date = datetime.now() - timedelta(days=30)
            if end_date is None:
                end_date = datetime.now()

            # Get conversations in date range
            all_conversations = await self.conversation_repo.get_by_date_range(
                start=start_date,
                end=end_date
            )

            # Calculate statistics
            total = len(all_conversations)
            by_speaker = {"david": 0, "angela": 0, "system": 0}
            by_importance = {i: 0 for i in range(1, 11)}
            total_importance = 0
            with_embeddings = 0

            for conv in all_conversations:
                by_speaker[conv.speaker.value] += 1
                by_importance[conv.importance_level] += 1
                total_importance += conv.importance_level
                if conv.has_embedding():
                    with_embeddings += 1

            return {
                "total_conversations": total,
                "by_speaker": by_speaker,
                "by_importance": by_importance,
                "avg_importance": total_importance / total if total > 0 else 0,
                "with_embeddings": with_embeddings,
                "embedding_percentage": (with_embeddings / total * 100) if total > 0 else 0,
                "start_date": start_date.isoformat(),
                "end_date": end_date.isoformat()
            }

        except Exception as e:
            self.logger.error(f"Error getting conversation statistics: {e}")
            return {
                "total_conversations": 0,
                "error": str(e)
            }

    # ========================================================================
    # HELPER METHODS
    # ========================================================================

    def _conversation_to_dict(self, conversation) -> Dict[str, Any]:
        """
        Convert conversation entity to dictionary.

        Args:
            conversation: Conversation entity

        Returns:
            Dictionary representation
        """
        return {
            "conversation_id": str(conversation.conversation_id),
            "speaker": conversation.speaker.value,
            "message_text": conversation.message_text,
            "message_type": conversation.message_type.value,
            "topic": conversation.topic,
            "emotion_detected": conversation.emotion_detected,
            "sentiment_label": conversation.sentiment_label.value if conversation.sentiment_label else None,
            "sentiment_score": conversation.sentiment_score,
            "importance_level": conversation.importance_level,
            "session_id": conversation.session_id,
            "has_embedding": conversation.has_embedding(),
            "created_at": conversation.created_at.isoformat(),
            "metadata": conversation.metadata
        }
