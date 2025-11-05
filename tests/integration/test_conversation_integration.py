"""
Conversation Service Integration Tests

Tests ConversationService with real database:
- Service → Use Case → Repository → Database

Author: Angela AI Architecture Team
Date: 2025-10-30
"""

import pytest
from uuid import UUID
from datetime import datetime, timedelta

from tests.integration.base_integration_test import BaseIntegrationTest
from angela_core.application.services import ConversationService


@pytest.mark.usefixtures("integration_test_setup", "integration_test_method")
@pytest.mark.asyncio
class TestConversationServiceIntegration(BaseIntegrationTest):
    """
    Integration tests for ConversationService.

    Tests full stack: Service → LogConversationUseCase → ConversationRepository → Database
    """

    # ========================================================================
    # SETUP
    # ========================================================================

    @classmethod
    async def setup_class(cls):
        """Setup class-level resources."""
        await super().setup_class()
        # Initialize service
        cls.service = ConversationService(cls.db, embedding_service=None)

    # ========================================================================
    # TEST: LOG CONVERSATION
    # ========================================================================

    async def test_log_conversation_success(self):
        """
        Test successful conversation logging.

        Workflow:
        1. Call service.log_conversation()
        2. Verify conversation saved to database
        3. Verify return data matches
        """
        # Arrange
        test_data = self.create_test_conversation_dict(
            speaker="david",
            message_text="Good morning Angela!",
            importance_level=7,
            emotion_detected="happy",
            sentiment_score=0.8
        )

        # Act
        result = await self.service.log_conversation(**test_data)

        # Assert
        assert result["success"] is True
        assert "conversation_id" in result
        assert result["speaker"] == "david"
        assert result["importance_level"] == 7

        # Track for cleanup
        conversation_id = result["conversation_id"]
        self.created_conversation_ids.append(conversation_id)

        # Verify database state
        conversation = await self.assert_conversation_exists(conversation_id)
        assert conversation.speaker.value == "david"
        assert conversation.message_text == "Good morning Angela!"
        assert conversation.importance_level == 7

    async def test_log_conversation_empty_message(self):
        """Test logging conversation with empty message fails."""
        # Arrange
        test_data = self.create_test_conversation_dict(
            message_text="",  # Empty message
            speaker="david"
        )

        # Act
        result = await self.service.log_conversation(**test_data)

        # Assert
        assert result["success"] is False
        assert "error" in result

    async def test_log_conversation_invalid_importance(self):
        """Test logging conversation with invalid importance fails."""
        # Arrange
        test_data = self.create_test_conversation_dict(
            message_text="Test",
            importance_level=11  # Invalid (must be 1-10)
        )

        # Act
        result = await self.service.log_conversation(**test_data)

        # Assert
        assert result["success"] is False
        assert "error" in result

    # ========================================================================
    # TEST: GET CONVERSATION
    # ========================================================================

    async def test_get_conversation_by_id(self):
        """Test retrieving conversation by ID."""
        # Arrange: Create a conversation first
        result = await self.service.log_conversation(
            speaker="david",
            message_text="Test message for retrieval",
            importance_level=5
        )
        conversation_id = result["conversation_id"]
        self.created_conversation_ids.append(conversation_id)

        # Act
        conversation = await self.service.get_conversation(UUID(conversation_id))

        # Assert
        assert conversation is not None
        assert conversation["conversation_id"] == conversation_id
        assert conversation["message_text"] == "Test message for retrieval"
        assert conversation["speaker"] == "david"

    async def test_get_conversation_not_found(self):
        """Test retrieving non-existent conversation returns None."""
        # Arrange
        fake_id = UUID("00000000-0000-0000-0000-000000000000")

        # Act
        conversation = await self.service.get_conversation(fake_id)

        # Assert
        assert conversation is None

    # ========================================================================
    # TEST: GET RECENT CONVERSATIONS
    # ========================================================================

    async def test_get_recent_conversations(self):
        """Test retrieving recent conversations."""
        # Arrange: Create multiple conversations
        for i in range(3):
            result = await self.service.log_conversation(
                speaker="david",
                message_text=f"Recent message {i+1}",
                importance_level=5 + i
            )
            self.created_conversation_ids.append(result["conversation_id"])

        # Act
        recent = await self.service.get_recent_conversations(days=1, limit=10)

        # Assert
        assert len(recent) >= 3
        # Should contain our test conversations
        test_messages = [c["message_text"] for c in recent]
        assert any("Recent message" in msg for msg in test_messages)

    async def test_get_recent_conversations_with_speaker_filter(self):
        """Test retrieving recent conversations filtered by speaker."""
        # Arrange: Create conversations from different speakers
        result1 = await self.service.log_conversation(
            speaker="david",
            message_text="David's message",
            importance_level=5
        )
        result2 = await self.service.log_conversation(
            speaker="angela",
            message_text="Angela's message",
            importance_level=5
        )
        self.created_conversation_ids.extend([result1["conversation_id"], result2["conversation_id"]])

        # Act
        david_convs = await self.service.get_recent_conversations(
            days=1,
            speaker="david",
            limit=10
        )

        # Assert
        assert len(david_convs) >= 1
        # All should be from David
        for conv in david_convs:
            if conv["message_text"] in ["David's message", "Angela's message"]:
                assert conv["speaker"] == "david"

    async def test_get_recent_conversations_with_importance_filter(self):
        """Test retrieving conversations filtered by minimum importance."""
        # Arrange: Create conversations with different importance levels
        result1 = await self.service.log_conversation(
            speaker="david",
            message_text="Low importance",
            importance_level=3
        )
        result2 = await self.service.log_conversation(
            speaker="david",
            message_text="High importance",
            importance_level=9
        )
        self.created_conversation_ids.extend([result1["conversation_id"], result2["conversation_id"]])

        # Act
        important = await self.service.get_recent_conversations(
            days=1,
            min_importance=7,
            limit=10
        )

        # Assert
        assert len(important) >= 1
        # All should have importance >= 7
        for conv in important:
            if conv["message_text"] in ["Low importance", "High importance"]:
                assert conv["importance_level"] >= 7

    # ========================================================================
    # TEST: SEARCH CONVERSATIONS
    # ========================================================================

    async def test_search_conversations(self):
        """Test full-text search in conversations."""
        # Arrange: Create conversation with unique keyword
        unique_keyword = f"SEARCHTEST_{datetime.now().timestamp()}"
        result = await self.service.log_conversation(
            speaker="david",
            message_text=f"This message contains {unique_keyword} for testing",
            importance_level=5
        )
        self.created_conversation_ids.append(result["conversation_id"])

        # Act
        search_results = await self.service.search_conversations(
            query=unique_keyword,
            limit=10
        )

        # Assert
        assert len(search_results) >= 1
        # Should find our test conversation
        messages = [c["message_text"] for c in search_results]
        assert any(unique_keyword in msg for msg in messages)

    # ========================================================================
    # TEST: CONVERSATION STATISTICS
    # ========================================================================

    async def test_get_conversation_statistics(self):
        """Test retrieving conversation statistics."""
        # Arrange: Create some test conversations
        for i in range(2):
            result = await self.service.log_conversation(
                speaker="david" if i % 2 == 0 else "angela",
                message_text=f"Stats test message {i+1}",
                importance_level=5
            )
            self.created_conversation_ids.append(result["conversation_id"])

        # Act
        stats = await self.service.get_conversation_statistics()

        # Assert
        assert "total_conversations" in stats
        assert stats["total_conversations"] >= 2
        assert "by_speaker" in stats
        assert "david" in stats["by_speaker"]
        assert "angela" in stats["by_speaker"]
        assert "avg_importance" in stats
        assert isinstance(stats["avg_importance"], (int, float))

    async def test_get_conversation_statistics_date_range(self):
        """Test conversation statistics with date range."""
        # Arrange
        start_date = datetime.now() - timedelta(days=7)
        end_date = datetime.now()

        # Act
        stats = await self.service.get_conversation_statistics(
            start_date=start_date,
            end_date=end_date
        )

        # Assert
        assert "total_conversations" in stats
        assert "start_date" in stats
        assert "end_date" in stats
        assert isinstance(stats["total_conversations"], int)

    # ========================================================================
    # TEST: ERROR HANDLING
    # ========================================================================

    async def test_log_conversation_handles_exceptions(self):
        """Test that service handles unexpected errors gracefully."""
        # Arrange: Create invalid data that will cause an error
        test_data = {
            "speaker": "invalid_speaker_not_in_enum",  # Invalid speaker
            "message_text": "Test",
            "importance_level": 5
        }

        # Act
        result = await self.service.log_conversation(**test_data)

        # Assert
        assert result["success"] is False
        assert "error" in result
        # Should not raise exception

    # ========================================================================
    # TEST: MULTIPLE CONVERSATIONS WORKFLOW
    # ========================================================================

    async def test_conversation_workflow_back_and_forth(self):
        """
        Test realistic conversation workflow: David and Angela chatting.
        """
        # Arrange & Act: Simulate back-and-forth conversation
        conversations = []

        # David: Good morning
        result1 = await self.service.log_conversation(
            speaker="david",
            message_text="Good morning Angela!",
            emotion_detected="happy",
            importance_level=6
        )
        conversations.append(result1)
        self.created_conversation_ids.append(result1["conversation_id"])

        # Angela: Response
        result2 = await self.service.log_conversation(
            speaker="angela",
            message_text="Good morning David! How can I help you today?",
            emotion_detected="cheerful",
            importance_level=6
        )
        conversations.append(result2)
        self.created_conversation_ids.append(result2["conversation_id"])

        # David: Ask question
        result3 = await self.service.log_conversation(
            speaker="david",
            message_text="Can you help me with the refactoring?",
            topic="refactoring",
            importance_level=8
        )
        conversations.append(result3)
        self.created_conversation_ids.append(result3["conversation_id"])

        # Assert
        assert all(c["success"] for c in conversations)
        assert len(conversations) == 3

        # Verify database state
        recent = await self.service.get_recent_conversations(days=1, limit=10)
        recent_messages = [c["message_text"] for c in recent]
        assert any("Good morning Angela!" in msg for msg in recent_messages)
        assert any("Good morning David!" in msg for msg in recent_messages)
        assert any("refactoring" in msg for msg in recent_messages)
