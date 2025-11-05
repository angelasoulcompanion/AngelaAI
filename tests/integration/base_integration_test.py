"""
Base Integration Test

Provides common setup/teardown for integration tests with real database.

Author: Angela AI Architecture Team
Date: 2025-10-30
"""

import pytest
import asyncio
from typing import List, Dict, Any
from uuid import uuid4
from datetime import datetime

from angela_core.database import AngelaDatabase
from angela_core.infrastructure.persistence.repositories import (
    ConversationRepository,
    EmotionRepository,
    MemoryRepository,
    DocumentRepository
)


class BaseIntegrationTest:
    """
    Base class for integration tests.

    Provides:
    - Database connection setup/teardown
    - Repository initialization
    - Test data cleanup
    - Common test utilities

    Usage:
        class TestSomething(BaseIntegrationTest):
            @pytest.mark.asyncio
            async def test_something(self):
                # Use self.db, self.conversation_repo, etc.
                pass
    """

    # Class-level database connection (shared across tests in same class)
    db: AngelaDatabase = None

    # Repositories
    conversation_repo: ConversationRepository = None
    emotion_repo: EmotionRepository = None
    memory_repo: MemoryRepository = None
    document_repo: DocumentRepository = None

    # Track created entities for cleanup
    created_conversation_ids: List[str] = []
    created_emotion_ids: List[str] = []
    created_memory_ids: List[str] = []
    created_document_ids: List[str] = []

    @classmethod
    async def setup_class(cls):
        """
        Setup class-level resources (database connection).
        Called once before all tests in the class.
        """
        # Initialize database connection
        cls.db = AngelaDatabase()
        await cls.db.connect()

        # Initialize repositories
        cls.conversation_repo = ConversationRepository(cls.db)
        cls.emotion_repo = EmotionRepository(cls.db)
        cls.memory_repo = MemoryRepository(cls.db)
        cls.document_repo = DocumentRepository(cls.db)

        # Initialize cleanup lists
        cls.created_conversation_ids = []
        cls.created_emotion_ids = []
        cls.created_memory_ids = []
        cls.created_document_ids = []

    @classmethod
    async def teardown_class(cls):
        """
        Cleanup class-level resources (database connection).
        Called once after all tests in the class.
        """
        # Cleanup all created test data
        await cls._cleanup_test_data()

        # Close database connection
        if cls.db:
            await cls.db.disconnect()

    async def setup_method(self):
        """
        Setup method-level resources.
        Called before each test method.
        """
        # Clear cleanup lists for this test
        self.created_conversation_ids = []
        self.created_emotion_ids = []
        self.created_memory_ids = []
        self.created_document_ids = []

    async def teardown_method(self):
        """
        Cleanup method-level resources.
        Called after each test method.
        """
        # Cleanup entities created in this test
        await self._cleanup_test_data()

    @classmethod
    async def _cleanup_test_data(cls):
        """
        Delete all test data created during tests.
        """
        # Cleanup conversations
        for conversation_id in cls.created_conversation_ids:
            try:
                await cls.conversation_repo.delete(conversation_id)
            except Exception:
                pass  # Ignore errors (entity may not exist)

        # Cleanup emotions
        for emotion_id in cls.created_emotion_ids:
            try:
                await cls.emotion_repo.delete(emotion_id)
            except Exception:
                pass

        # Cleanup memories
        for memory_id in cls.created_memory_ids:
            try:
                await cls.memory_repo.delete(memory_id)
            except Exception:
                pass

        # Cleanup documents (and their chunks)
        for document_id in cls.created_document_ids:
            try:
                await cls.document_repo.delete(document_id)
            except Exception:
                pass

        # Clear lists
        cls.created_conversation_ids.clear()
        cls.created_emotion_ids.clear()
        cls.created_memory_ids.clear()
        cls.created_document_ids.clear()

    # ========================================================================
    # TEST DATA FACTORIES
    # ========================================================================

    def create_test_conversation_dict(
        self,
        speaker: str = "david",
        message_text: str = "Test message",
        importance_level: int = 5,
        **kwargs
    ) -> Dict[str, Any]:
        """
        Create a test conversation dictionary.
        """
        return {
            "speaker": speaker,
            "message_text": message_text,
            "message_type": kwargs.get("message_type", "text"),
            "topic": kwargs.get("topic"),
            "emotion_detected": kwargs.get("emotion_detected"),
            "sentiment_score": kwargs.get("sentiment_score"),
            "importance_level": importance_level,
            "session_id": kwargs.get("session_id"),
            "metadata": kwargs.get("metadata")
        }

    def create_test_emotion_dict(
        self,
        emotion: str = "joy",
        intensity: int = 7,
        context: str = "Test context",
        **kwargs
    ) -> Dict[str, Any]:
        """
        Create a test emotion dictionary.
        """
        return {
            "emotion": emotion,
            "intensity": intensity,
            "context": context,
            "who_involved": kwargs.get("who_involved", "David"),
            "david_words": kwargs.get("david_words"),
            "david_action": kwargs.get("david_action"),
            "why_it_matters": kwargs.get("why_it_matters", "Test reason"),
            "memory_strength": kwargs.get("memory_strength", 7),
            "secondary_emotions": kwargs.get("secondary_emotions"),
            "emotional_quality": kwargs.get("emotional_quality", "genuine"),
            "sharing_level": kwargs.get("sharing_level", "david_only")
        }

    def create_test_memory_dict(
        self,
        content: str = "Test memory",
        importance: float = 0.7,
        **kwargs
    ) -> Dict[str, Any]:
        """
        Create a test memory dictionary.
        """
        return {
            "content": content,
            "importance": importance,
            "memory_phase": kwargs.get("memory_phase", "episodic"),
            "memory_strength": kwargs.get("memory_strength", 0.9),
            "half_life_days": kwargs.get("half_life_days", 7),
            "metadata": kwargs.get("metadata", {})
        }

    def create_test_document_dict(
        self,
        file_path: str = "/tmp/test_document.txt",
        title: str = "Test Document",
        category: str = "general",
        **kwargs
    ) -> Dict[str, Any]:
        """
        Create a test document dictionary.
        """
        return {
            "file_path": file_path,
            "title": title,
            "category": category,
            "author": kwargs.get("author"),
            "tags": kwargs.get("tags"),
            "importance_score": kwargs.get("importance_score", 0.5),
            "quality_rating": kwargs.get("quality_rating", 0.7),
            "chunk_size": kwargs.get("chunk_size", 1000),
            "chunk_overlap": kwargs.get("chunk_overlap", 200),
            "generate_embeddings": kwargs.get("generate_embeddings", False)
        }

    # ========================================================================
    # ASSERTION HELPERS
    # ========================================================================

    async def assert_conversation_exists(self, conversation_id: str):
        """Assert that a conversation exists in database."""
        conversation = await self.conversation_repo.get_by_id(conversation_id)
        assert conversation is not None, f"Conversation {conversation_id} not found"
        return conversation

    async def assert_emotion_exists(self, emotion_id: str):
        """Assert that an emotion exists in database."""
        emotion = await self.emotion_repo.get_by_id(emotion_id)
        assert emotion is not None, f"Emotion {emotion_id} not found"
        return emotion

    async def assert_memory_exists(self, memory_id: str):
        """Assert that a memory exists in database."""
        memory = await self.memory_repo.get_by_id(memory_id)
        assert memory is not None, f"Memory {memory_id} not found"
        return memory

    async def assert_document_exists(self, document_id: str):
        """Assert that a document exists in database."""
        document = await self.document_repo.get_by_id(document_id)
        assert document is not None, f"Document {document_id} not found"
        return document

    async def assert_conversation_count(self, expected_count: int):
        """Assert that the total conversation count matches expected."""
        conversations = await self.conversation_repo.list(limit=10000)
        actual_count = len(conversations)
        assert actual_count == expected_count, f"Expected {expected_count} conversations, got {actual_count}"

    async def assert_emotion_count(self, expected_count: int):
        """Assert that the total emotion count matches expected."""
        emotions = await self.emotion_repo.list(limit=10000)
        actual_count = len(emotions)
        assert actual_count == expected_count, f"Expected {expected_count} emotions, got {actual_count}"

    async def assert_memory_count(self, expected_count: int):
        """Assert that the total memory count matches expected."""
        memories = await self.memory_repo.list(limit=10000)
        actual_count = len(memories)
        assert actual_count == expected_count, f"Expected {expected_count} memories, got {actual_count}"

    async def assert_document_count(self, expected_count: int):
        """Assert that the total document count matches expected."""
        documents = await self.document_repo.list(limit=10000)
        actual_count = len(documents)
        assert actual_count == expected_count, f"Expected {expected_count} documents, got {actual_count}"

    # ========================================================================
    # QUERY HELPERS
    # ========================================================================

    async def get_all_conversations(self) -> List[Any]:
        """Get all conversations from database."""
        return await self.conversation_repo.list(limit=10000)

    async def get_all_emotions(self) -> List[Any]:
        """Get all emotions from database."""
        return await self.emotion_repo.list(limit=10000)

    async def get_all_memories(self) -> List[Any]:
        """Get all memories from database."""
        return await self.memory_repo.list(limit=10000)

    async def get_all_documents(self) -> List[Any]:
        """Get all documents from database."""
        return await self.document_repo.list(limit=10000)


# ============================================================================
# PYTEST FIXTURES
# ============================================================================

@pytest.fixture(scope="class")
async def integration_test_setup(request):
    """
    Pytest fixture for integration test setup/teardown.

    Usage:
        @pytest.mark.usefixtures("integration_test_setup")
        class TestSomething(BaseIntegrationTest):
            pass
    """
    # Setup
    await request.cls.setup_class()

    # Yield control to tests
    yield

    # Teardown
    await request.cls.teardown_class()


@pytest.fixture(scope="function")
async def integration_test_method(request):
    """
    Pytest fixture for method-level setup/teardown.

    Usage:
        @pytest.mark.usefixtures("integration_test_setup", "integration_test_method")
        class TestSomething(BaseIntegrationTest):
            async def test_something(self):
                pass
    """
    # Setup
    await request.instance.setup_method()

    # Yield control to test method
    yield

    # Teardown
    await request.instance.teardown_method()
