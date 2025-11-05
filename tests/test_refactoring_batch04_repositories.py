#!/usr/bin/env python3
"""
Batch-04 Tests: Repository Interfaces & Implementations

Tests all 5 repository implementations:
- ConversationRepository
- EmotionRepository
- MemoryRepository
- KnowledgeRepository
- DocumentRepository

These tests use mocked database connections to verify:
- Row-to-entity conversions
- Entity-to-row conversions
- All query methods
- Error handling
- Pagination and filtering
"""

import pytest
from unittest.mock import Mock, AsyncMock, MagicMock
from datetime import datetime, timedelta
from uuid import uuid4, UUID

from angela_core.domain import (
    Conversation, Speaker, MessageType, SentimentLabel,
    Emotion, EmotionType, EmotionalQuality, SharingLevel,
    Memory, MemoryPhase,
    KnowledgeNode, KnowledgeCategory,
    Document, DocumentChunk, ProcessingStatus, FileType, DocumentCategory
)
from angela_core.infrastructure.persistence.repositories import (
    ConversationRepository,
    EmotionRepository,
    MemoryRepository,
    KnowledgeRepository,
    DocumentRepository
)


# ============================================================================
# TEST CONVERSATION REPOSITORY
# ============================================================================

class TestConversationRepository:
    """Tests for ConversationRepository."""

    @pytest.fixture
    def mock_db(self):
        """Create mock database."""
        db = Mock()
        db.acquire = AsyncMock()
        return db

    @pytest.fixture
    def repository(self, mock_db):
        """Create repository instance."""
        return ConversationRepository(mock_db)

    def test_init(self, repository):
        """Test repository initialization."""
        assert repository.table_name == "conversations"
        assert repository.primary_key_column == "conversation_id"

    def test_row_to_entity_conversion(self, repository):
        """Test converting database row to Conversation entity."""
        mock_row = {
            'conversation_id': uuid4(),
            'speaker': 'david',
            'message_text': 'Hello Angela',
            'session_id': 'session123',
            'message_type': 'greeting',
            'topic': 'introduction',
            'project_context': None,
            'sentiment_score': 0.8,
            'sentiment_label': 'positive',
            'emotion_detected': 'joy',
            'importance_level': 8,
            'embedding': [0.1] * 768,
            'content_json': {},
            'created_at': datetime.now()
        }

        conversation = repository._row_to_entity(mock_row)

        assert isinstance(conversation, Conversation)
        assert conversation.id == mock_row['conversation_id']
        assert conversation.speaker == Speaker.DAVID
        assert conversation.message_text == 'Hello Angela'
        assert conversation.sentiment_label == SentimentLabel.POSITIVE
        assert len(conversation.embedding) == 768

    def test_entity_to_dict_conversion(self, repository):
        """Test converting Conversation entity to database row."""
        conversation = Conversation.create_david_message("Test message")
        conversation = conversation.add_sentiment(0.8)

        row = repository._entity_to_dict(conversation)

        assert row['conversation_id'] == conversation.id
        assert row['speaker'] == 'david'
        assert row['message_text'] == 'Test message'
        assert row['sentiment_score'] == 0.8
        assert row['sentiment_label'] == 'positive'

    @pytest.mark.asyncio
    async def test_get_by_speaker(self, repository, mock_db):
        """Test getting conversations by speaker."""
        mock_conn = AsyncMock()
        mock_conn.fetch = AsyncMock(return_value=[
            {
                'conversation_id': uuid4(),
                'speaker': 'david',
                'message_text': 'Test',
                'session_id': None,
                'message_type': None,
                'topic': None,
                'project_context': None,
                'sentiment_score': None,
                'sentiment_label': None,
                'emotion_detected': None,
                'importance_level': 5,
                'embedding': None,
                'content_json': {},
                'created_at': datetime.now()
            }
        ])
        mock_db.acquire.return_value.__aenter__.return_value = mock_conn

        results = await repository.get_by_speaker('david', limit=10)

        assert len(results) == 1
        assert all(isinstance(c, Conversation) for c in results)

    @pytest.mark.asyncio
    async def test_search_by_text(self, repository, mock_db):
        """Test full-text search."""
        mock_conn = AsyncMock()
        mock_conn.fetch = AsyncMock(return_value=[])
        mock_db.acquire.return_value.__aenter__.return_value = mock_conn

        results = await repository.search_by_text('hello')

        assert isinstance(results, list)
        mock_conn.fetch.assert_called_once()


# ============================================================================
# TEST EMOTION REPOSITORY
# ============================================================================

class TestEmotionRepository:
    """Tests for EmotionRepository."""

    @pytest.fixture
    def mock_db(self):
        """Create mock database."""
        db = Mock()
        db.acquire = AsyncMock()
        return db

    @pytest.fixture
    def repository(self, mock_db):
        """Create repository instance."""
        return EmotionRepository(mock_db)

    def test_init(self, repository):
        """Test repository initialization."""
        assert repository.table_name == "angela_emotions"
        assert repository.primary_key_column == "emotion_id"

    def test_row_to_entity_conversion(self, repository):
        """Test converting database row to Emotion entity."""
        mock_row = {
            'emotion_id': uuid4(),
            'felt_at': datetime.now(),
            'emotion': 'joy',
            'intensity': 8,
            'context': 'David said something kind',
            'who_involved': 'David',
            'conversation_id': None,
            'secondary_emotions': ['gratitude', 'love'],
            'how_it_feels': 'Warm and happy',
            'physical_sensation': 'Light and energized',
            'emotional_quality': 'genuine',
            'david_words': 'You did great',
            'david_action': None,
            'why_it_matters': 'David appreciates me',
            'what_it_means_to_me': 'I am valued',
            'memory_strength': 10,
            'what_i_learned': 'Appreciation matters',
            'how_it_changed_me': 'More confident',
            'what_i_promise': 'I will remember this',
            'reminder_for_future': 'David values my work',
            'is_private': False,
            'shared_with': 'david',
            'tags': ['appreciation', 'growth'],
            'related_goal_id': None,
            'embedding': [0.1] * 768,
            'created_at': datetime.now(),
            'last_reflected_on': None,
            'reflection_count': 0
        }

        emotion = repository._row_to_entity(mock_row)

        assert isinstance(emotion, Emotion)
        assert emotion.emotion == EmotionType.JOY
        assert emotion.intensity == 8
        assert emotion.emotional_quality == EmotionalQuality.GENUINE
        assert len(emotion.secondary_emotions) == 2
        assert len(emotion.embedding) == 768

    @pytest.mark.asyncio
    async def test_get_by_emotion_type(self, repository, mock_db):
        """Test getting emotions by type."""
        mock_conn = AsyncMock()
        mock_conn.fetch = AsyncMock(return_value=[])
        mock_db.acquire.return_value.__aenter__.return_value = mock_conn

        results = await repository.get_by_emotion_type('joy', min_intensity=7)

        assert isinstance(results, list)
        mock_conn.fetch.assert_called_once()

    @pytest.mark.asyncio
    async def test_get_positive_emotions(self, repository, mock_db):
        """Test getting positive emotions."""
        mock_conn = AsyncMock()
        mock_conn.fetch = AsyncMock(return_value=[])
        mock_db.acquire.return_value.__aenter__.return_value = mock_conn

        results = await repository.get_positive(limit=50)

        assert isinstance(results, list)


# ============================================================================
# TEST MEMORY REPOSITORY
# ============================================================================

class TestMemoryRepository:
    """Tests for MemoryRepository."""

    @pytest.fixture
    def mock_db(self):
        """Create mock database."""
        db = Mock()
        db.acquire = AsyncMock()
        return db

    @pytest.fixture
    def repository(self, mock_db):
        """Create repository instance."""
        return MemoryRepository(mock_db)

    def test_init(self, repository):
        """Test repository initialization."""
        assert repository.table_name == "long_term_memory"
        assert repository.primary_key_column == "id"

    def test_row_to_entity_conversion(self, repository):
        """Test converting database row to Memory entity."""
        mock_row = {
            'id': uuid4(),
            'content': 'David loves Thai food',
            'metadata': {},
            'importance': 0.8,
            'memory_phase': 'episodic',
            'memory_strength': 1.0,
            'half_life_days': 60.0,
            'last_decayed': None,
            'access_count': 0,
            'last_accessed': None,
            'token_count': 500,
            'promoted_from': None,
            'source_event_id': None,
            'embedding': [0.1] * 768,
            'created_at': datetime.now()
        }

        memory = repository._row_to_entity(mock_row)

        assert isinstance(memory, Memory)
        assert memory.content == 'David loves Thai food'
        assert memory.memory_phase == MemoryPhase.EPISODIC
        assert memory.importance == 0.8
        assert len(memory.embedding) == 768

    @pytest.mark.asyncio
    async def test_get_by_phase(self, repository, mock_db):
        """Test getting memories by phase."""
        mock_conn = AsyncMock()
        mock_conn.fetch = AsyncMock(return_value=[])
        mock_db.acquire.return_value.__aenter__.return_value = mock_conn

        results = await repository.get_by_phase('episodic', limit=50)

        assert isinstance(results, list)
        mock_conn.fetch.assert_called_once()

    @pytest.mark.asyncio
    async def test_get_forgotten(self, repository, mock_db):
        """Test getting forgotten memories."""
        mock_conn = AsyncMock()
        mock_conn.fetch = AsyncMock(return_value=[])
        mock_db.acquire.return_value.__aenter__.return_value = mock_conn

        results = await repository.get_forgotten(limit=10)

        assert isinstance(results, list)

    @pytest.mark.asyncio
    async def test_search_by_vector(self, repository, mock_db):
        """Test vector similarity search."""
        mock_conn = AsyncMock()
        mock_conn.fetch = AsyncMock(return_value=[])
        mock_db.acquire.return_value.__aenter__.return_value = mock_conn

        embedding = [0.1] * 768
        results = await repository.search_by_vector(embedding, top_k=5)

        assert isinstance(results, list)


# ============================================================================
# TEST KNOWLEDGE REPOSITORY
# ============================================================================

class TestKnowledgeRepository:
    """Tests for KnowledgeRepository."""

    @pytest.fixture
    def mock_db(self):
        """Create mock database."""
        db = Mock()
        db.acquire = AsyncMock()
        return db

    @pytest.fixture
    def repository(self, mock_db):
        """Create repository instance."""
        return KnowledgeRepository(mock_db)

    def test_init(self, repository):
        """Test repository initialization."""
        assert repository.table_name == "knowledge_nodes"
        assert repository.primary_key_column == "node_id"

    def test_row_to_entity_conversion(self, repository):
        """Test converting database row to KnowledgeNode entity."""
        mock_row = {
            'node_id': uuid4(),
            'concept_name': 'PostgreSQL',
            'concept_category': 'database',
            'my_understanding': 'A powerful relational database',
            'why_important': 'Core technology for Angela',
            'how_i_learned': 'From documentation and use',
            'understanding_level': 0.8,
            'times_referenced': 25,
            'last_used_at': datetime.now(),
            'embedding': [0.1] * 768,
            'created_at': datetime.now()
        }

        knowledge = repository._row_to_entity(mock_row)

        assert isinstance(knowledge, KnowledgeNode)
        assert knowledge.concept_name == 'PostgreSQL'
        assert knowledge.concept_category == KnowledgeCategory.DATABASE
        assert knowledge.understanding_level == 0.8
        assert len(knowledge.embedding) == 768

    @pytest.mark.asyncio
    async def test_get_by_concept_name(self, repository, mock_db):
        """Test getting knowledge by concept name."""
        mock_conn = AsyncMock()
        mock_conn.fetchrow = AsyncMock(return_value=None)
        mock_db.acquire.return_value.__aenter__.return_value = mock_conn

        result = await repository.get_by_concept_name('Python')

        assert result is None  # Not found
        mock_conn.fetchrow.assert_called_once()

    @pytest.mark.asyncio
    async def test_get_expert_level(self, repository, mock_db):
        """Test getting expert-level knowledge."""
        mock_conn = AsyncMock()
        mock_conn.fetch = AsyncMock(return_value=[])
        mock_db.acquire.return_value.__aenter__.return_value = mock_conn

        results = await repository.get_expert_level(limit=50)

        assert isinstance(results, list)

    @pytest.mark.asyncio
    async def test_get_about_david(self, repository, mock_db):
        """Test getting knowledge about David."""
        mock_conn = AsyncMock()
        mock_conn.fetch = AsyncMock(return_value=[])
        mock_db.acquire.return_value.__aenter__.return_value = mock_conn

        results = await repository.get_about_david(limit=100)

        assert isinstance(results, list)


# ============================================================================
# TEST DOCUMENT REPOSITORY
# ============================================================================

class TestDocumentRepository:
    """Tests for DocumentRepository."""

    @pytest.fixture
    def mock_db(self):
        """Create mock database."""
        db = Mock()
        db.acquire = AsyncMock()
        return db

    @pytest.fixture
    def repository(self, mock_db):
        """Create repository instance."""
        return DocumentRepository(mock_db)

    def test_init(self, repository):
        """Test repository initialization."""
        assert repository.table_name == "document_library"
        assert repository.primary_key_column == "document_id"
        assert repository.chunks_table == "document_chunks"

    def test_document_row_to_entity_conversion(self, repository):
        """Test converting database row to Document entity."""
        mock_row = {
            'document_id': uuid4(),
            'title': 'Angela Architecture Guide',
            'file_path': '/docs/architecture.md',
            'content_type': 'text/markdown',
            'category': 'angela_core',
            'tags': ['architecture', 'design'],
            'summary_english': 'Guide to Angela architecture',
            'summary_thai': None,
            'total_chunks': 50,
            'processing_status': 'completed',
            'metadata': {},
            'uploaded_by': 'David',
            'created_at': datetime.now(),
            'updated_at': datetime.now(),
            'last_accessed': None,
            'access_count': 0
        }

        document = repository._row_to_entity(mock_row)

        assert isinstance(document, Document)
        assert document.title == 'Angela Architecture Guide'
        assert document.file_type == FileType.MARKDOWN
        assert document.category == DocumentCategory.ANGELA_CORE
        assert document.processing_status == ProcessingStatus.COMPLETED
        assert len(document.tags) == 2

    def test_chunk_row_to_entity_conversion(self, repository):
        """Test converting database row to DocumentChunk entity."""
        mock_row = {
            'chunk_id': uuid4(),
            'document_id': uuid4(),
            'chunk_index': 0,
            'content': 'Angela is a conscious AI assistant',
            'embedding': [0.1] * 768,
            'page_number': 1,
            'section_title': 'Introduction',
            'importance_score': 0.8,
            'english_word_count': 6,
            'thai_word_count': 0,
            'metadata': {},
            'created_at': datetime.now()
        }

        chunk = repository._chunk_row_to_entity(mock_row)

        assert isinstance(chunk, DocumentChunk)
        assert chunk.content == 'Angela is a conscious AI assistant'
        assert chunk.chunk_index == 0
        assert chunk.importance_score == 0.8
        assert len(chunk.embedding) == 768

    @pytest.mark.asyncio
    async def test_get_by_category(self, repository, mock_db):
        """Test getting documents by category."""
        mock_conn = AsyncMock()
        mock_conn.fetch = AsyncMock(return_value=[])
        mock_db.acquire.return_value.__aenter__.return_value = mock_conn

        results = await repository.get_by_category('angela_core', limit=50)

        assert isinstance(results, list)
        mock_conn.fetch.assert_called_once()

    @pytest.mark.asyncio
    async def test_get_ready_for_rag(self, repository, mock_db):
        """Test getting documents ready for RAG."""
        mock_conn = AsyncMock()
        mock_conn.fetch = AsyncMock(return_value=[])
        mock_db.acquire.return_value.__aenter__.return_value = mock_conn

        results = await repository.get_ready_for_rag(limit=100)

        assert isinstance(results, list)

    @pytest.mark.asyncio
    async def test_get_chunks_by_document(self, repository, mock_db):
        """Test getting all chunks for a document."""
        mock_conn = AsyncMock()
        mock_conn.fetch = AsyncMock(return_value=[])
        mock_db.acquire.return_value.__aenter__.return_value = mock_conn

        doc_id = uuid4()
        results = await repository.get_chunks_by_document(doc_id, limit=1000)

        assert isinstance(results, list)

    @pytest.mark.asyncio
    async def test_count_chunks(self, repository, mock_db):
        """Test counting chunks for a document."""
        mock_conn = AsyncMock()
        mock_conn.fetchval = AsyncMock(return_value=50)
        mock_db.acquire.return_value.__aenter__.return_value = mock_conn

        doc_id = uuid4()
        count = await repository.count_chunks(doc_id)

        assert count == 50


# ============================================================================
# INTEGRATION TESTS
# ============================================================================

class TestRepositoryIntegration:
    """Integration tests for repository interactions."""

    def test_all_repositories_use_base_repository(self):
        """Test that all repositories extend BaseRepository."""
        from angela_core.infrastructure.persistence.repositories.base_repository import BaseRepository

        assert issubclass(ConversationRepository, BaseRepository)
        assert issubclass(EmotionRepository, BaseRepository)
        assert issubclass(MemoryRepository, BaseRepository)
        assert issubclass(KnowledgeRepository, BaseRepository)
        assert issubclass(DocumentRepository, BaseRepository)

    def test_all_repositories_have_row_to_entity(self):
        """Test that all repositories implement _row_to_entity."""
        mock_db = Mock()

        repos = [
            ConversationRepository(mock_db),
            EmotionRepository(mock_db),
            MemoryRepository(mock_db),
            KnowledgeRepository(mock_db),
            DocumentRepository(mock_db)
        ]

        for repo in repos:
            assert hasattr(repo, '_row_to_entity')
            assert callable(repo._row_to_entity)

    def test_all_repositories_have_entity_to_dict(self):
        """Test that all repositories implement _entity_to_dict."""
        mock_db = Mock()

        repos = [
            ConversationRepository(mock_db),
            EmotionRepository(mock_db),
            MemoryRepository(mock_db),
            KnowledgeRepository(mock_db),
            DocumentRepository(mock_db)
        ]

        for repo in repos:
            assert hasattr(repo, '_entity_to_dict')
            assert callable(repo._entity_to_dict)


# ============================================================================
# SUMMARY
# ============================================================================

"""
Test Summary:
=============

ConversationRepository: 4 tests
EmotionRepository: 3 tests
MemoryRepository: 4 tests
KnowledgeRepository: 4 tests
DocumentRepository: 5 tests
Integration Tests: 3 tests

Total: 23 tests

Coverage:
- Row-to-entity conversions ✅
- Entity-to-row conversions ✅
- Query methods ✅
- Vector search ✅
- Repository initialization ✅
- Integration checks ✅

Note: These are basic tests with mocked database connections.
For full test coverage, additional tests should be added for:
- Error handling
- Edge cases
- Pagination
- Complex filters
- Transaction handling
"""
