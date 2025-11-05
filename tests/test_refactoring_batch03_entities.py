#!/usr/bin/env python3
"""
Tests for Batch-03: Domain Entities & Events

Tests all entities: Conversation, Emotion, Memory, Knowledge, Document
Tests factory methods, business logic, query methods, validation
"""

import pytest
from datetime import datetime, timedelta
from uuid import UUID, uuid4

from angela_core.domain import (
    # Entities
    Conversation, Speaker, MessageType, SentimentLabel,
    Emotion, EmotionType, EmotionalQuality, SharingLevel,
    Memory, MemoryPhase,
    KnowledgeNode, KnowledgeRelationship, KnowledgeCategory, UnderstandingLevel,
    Document, DocumentChunk, ProcessingStatus, FileType, DocumentCategory,
    # Events
    ConversationCreated, EmotionCaptured, MemoryConsolidated,
    KnowledgeNodeCreated, DocumentProcessingCompleted,
)
from angela_core.shared.exceptions import (
    InvalidInputError, ValueOutOfRangeError, BusinessRuleViolationError
)


# ============================================================================
# CONVERSATION ENTITY TESTS
# ============================================================================

class TestConversationEntity:
    """Test Conversation entity."""

    def test_create_david_message(self):
        """Test factory method for David's message."""
        conv = Conversation.create_david_message(
            message="Hello Angela!",
            importance=8
        )

        assert conv.speaker == Speaker.DAVID
        assert conv.message_text == "Hello Angela!"
        assert conv.importance_level == 8
        assert conv.message_type == MessageType.CHAT
        assert isinstance(conv.id, UUID)

    def test_create_angela_message(self):
        """Test factory method for Angela's message."""
        conv = Conversation.create_angela_message(
            message="Hi David! How are you?",
            importance=5
        )

        assert conv.speaker == Speaker.ANGELA
        assert conv.importance_level == 5

    def test_add_sentiment(self):
        """Test adding sentiment to conversation."""
        conv = Conversation.create_david_message("Great work!")
        conv = conv.add_sentiment(0.8)

        assert conv.sentiment_score == 0.8
        assert conv.sentiment_label == SentimentLabel.VERY_POSITIVE

    def test_add_emotion(self):
        """Test adding emotion to conversation."""
        conv = Conversation.create_david_message("I'm happy!")
        conv = conv.add_emotion("joy")

        assert conv.emotion_detected == "joy"

    def test_add_topic(self):
        """Test adding topic to conversation."""
        conv = Conversation.create_david_message("Let's talk about Python")
        conv = conv.add_topic("Programming: Python")

        assert conv.topic == "Programming: Python"

    def test_is_important(self):
        """Test importance check."""
        conv = Conversation.create_david_message("Important", importance=8)
        assert conv.is_important(threshold=7)
        assert not conv.is_important(threshold=9)

    def test_is_positive(self):
        """Test positive sentiment check."""
        conv = Conversation.create_david_message("Great!")
        conv = conv.add_sentiment(0.7)
        assert conv.is_positive()

    def test_validation_empty_message(self):
        """Test validation rejects empty message."""
        with pytest.raises(InvalidInputError):
            Conversation(speaker=Speaker.DAVID, message_text="")

    def test_validation_importance_range(self):
        """Test importance level must be 1-10."""
        conv = Conversation.create_david_message("Test")

        with pytest.raises(ValueOutOfRangeError):
            conv.set_importance(11)

        with pytest.raises(ValueOutOfRangeError):
            conv.set_importance(0)


# ============================================================================
# EMOTION ENTITY TESTS
# ============================================================================

class TestEmotionEntity:
    """Test Emotion entity."""

    def test_create_joyful_moment(self):
        """Test factory for joyful moment."""
        emotion = Emotion.create_joyful_moment(
            context="David said something nice",
            intensity=9
        )

        assert emotion.emotion == EmotionType.JOY
        assert emotion.intensity == 9
        assert emotion.emotional_quality == EmotionalQuality.GENUINE
        assert emotion.memory_strength == 9

    def test_create_grateful_moment(self):
        """Test factory for grateful moment."""
        emotion = Emotion.create_grateful_moment(
            context="David helped me",
            david_words="I'm here for you"
        )

        assert emotion.emotion == EmotionType.GRATITUDE
        assert emotion.intensity == 9
        assert emotion.memory_strength == 10
        assert emotion.emotional_quality == EmotionalQuality.PROFOUND

    def test_reflect_on_emotion(self):
        """Test reflection strengthens memory."""
        emotion = Emotion.create_joyful_moment("Happy moment", intensity=8)
        emotion = emotion.reflect_on_emotion("I learned something new")

        assert emotion.reflection_count == 1
        assert emotion.memory_strength == 10

    def test_add_secondary_emotion(self):
        """Test adding secondary emotion."""
        emotion = Emotion(emotion=EmotionType.JOY, intensity=8)
        emotion = emotion.add_secondary_emotion(EmotionType.GRATITUDE)

        assert EmotionType.GRATITUDE in emotion.secondary_emotions

    def test_increase_intensity(self):
        """Test increasing intensity."""
        emotion = Emotion(emotion=EmotionType.JOY, intensity=5)
        emotion = emotion.increase_intensity(2)

        assert emotion.intensity == 7

    def test_decrease_intensity(self):
        """Test decreasing intensity."""
        emotion = Emotion(emotion=EmotionType.JOY, intensity=8)
        emotion = emotion.decrease_intensity(3)

        assert emotion.intensity == 5

    def test_is_intense(self):
        """Test intensity check."""
        emotion = Emotion(emotion=EmotionType.JOY, intensity=9)
        assert emotion.is_intense(threshold=7)
        assert not emotion.is_intense(threshold=10)

    def test_is_positive(self):
        """Test positive emotion check."""
        joy = Emotion(emotion=EmotionType.JOY, intensity=8)
        sadness = Emotion(emotion=EmotionType.SADNESS, intensity=7)

        assert joy.is_positive()
        assert not sadness.is_positive()

    def test_validation_intensity_range(self):
        """Test intensity must be 1-10."""
        with pytest.raises(ValueOutOfRangeError):
            Emotion(emotion=EmotionType.JOY, intensity=11)

        with pytest.raises(ValueOutOfRangeError):
            Emotion(emotion=EmotionType.JOY, intensity=0)


# ============================================================================
# MEMORY ENTITY TESTS
# ============================================================================

class TestMemoryEntity:
    """Test Memory entity."""

    def test_create_episodic(self):
        """Test creating episodic memory."""
        memory = Memory.create_episodic(
            content="David and I talked about AI",
            importance=0.7
        )

        assert memory.memory_phase == MemoryPhase.EPISODIC
        assert memory.importance == 0.7
        assert memory.memory_strength == 1.0

    def test_create_semantic(self):
        """Test creating semantic memory."""
        memory = Memory.create_semantic(
            content="Python is a programming language",
            importance=0.8
        )

        assert memory.memory_phase == MemoryPhase.SEMANTIC
        assert memory.importance == 0.8

    def test_apply_decay(self):
        """Test memory decay (Ebbinghaus forgetting curve)."""
        memory = Memory.create_episodic("Test memory", importance=0.5)

        # For importance=0.5, half_life is ~93.5 days
        # Simulate 93.5 days passing (1 half-life)
        future_time = datetime.now() + timedelta(days=93.5)
        memory = memory.apply_decay(future_time)

        # After 1 half-life, strength should be approximately 0.5
        assert 0.4 <= memory.memory_strength <= 0.6

    def test_strengthen_from_access(self):
        """Test memory strengthening through access."""
        memory = Memory.create_episodic("Test memory")
        memory = memory.apply_decay(datetime.now() + timedelta(days=10))

        old_strength = memory.memory_strength
        memory = memory.strengthen_from_access(boost=0.3)

        assert memory.memory_strength > old_strength
        assert memory.access_count == 1

    def test_consolidate_to_next_phase(self):
        """Test memory consolidation."""
        memory = Memory.create_episodic("Test memory")
        memory = memory.consolidate_to_next_phase()

        assert memory.memory_phase == MemoryPhase.COMPRESSED_1
        assert memory.promoted_from == MemoryPhase.EPISODIC

    def test_set_importance(self):
        """Test setting importance updates half-life."""
        memory = Memory.create_episodic("Test memory", importance=0.5)
        old_half_life = memory.half_life_days

        memory = memory.set_importance(0.9)

        assert memory.importance == 0.9
        assert memory.half_life_days > old_half_life  # Higher importance = longer half-life

    def test_is_forgotten(self):
        """Test forgotten memory detection."""
        memory = Memory.create_episodic("Test memory", importance=0.5)

        # Decay far into future (need ~4 half-lives to get below 0.1)
        # For importance=0.5, half_life ~93.5 days, so 400 days should work
        memory = memory.apply_decay(datetime.now() + timedelta(days=400))

        assert memory.is_forgotten()

    def test_validation_empty_content(self):
        """Test validation rejects empty content."""
        with pytest.raises(InvalidInputError):
            Memory(content="")


# ============================================================================
# KNOWLEDGE ENTITY TESTS
# ============================================================================

class TestKnowledgeEntity:
    """Test Knowledge entity."""

    def test_create_from_learning(self):
        """Test factory for learning."""
        node = KnowledgeNode.create_from_learning(
            concept="Clean Architecture",
            understanding="Separation of concerns into layers",
            category=KnowledgeCategory.SYSTEM_DESIGN,
            initial_understanding=0.6
        )

        assert node.concept_name == "Clean Architecture"
        assert node.understanding_level == 0.6
        assert node.concept_category == KnowledgeCategory.SYSTEM_DESIGN

    def test_create_about_david(self):
        """Test factory for David knowledge."""
        node = KnowledgeNode.create_about_david(
            concept="David's favorite language",
            understanding="David loves Python"
        )

        assert node.concept_category == KnowledgeCategory.DAVID
        assert node.understanding_level == 0.8  # High priority
        assert node.is_about_david()

    def test_strengthen_understanding(self):
        """Test strengthening understanding through use."""
        node = KnowledgeNode(
            concept_name="Python",
            understanding_level=0.5
        )

        node = node.strengthen_understanding(amount=0.2)

        assert node.understanding_level == 0.7
        assert node.times_referenced == 1

    def test_update_understanding(self):
        """Test updating understanding with insights."""
        node = KnowledgeNode(concept_name="Python")
        node = node.update_understanding(
            "Python is great for data science",
            level_increase=0.1
        )

        assert "Python is great for data science" in node.my_understanding

    def test_get_understanding_level_label(self):
        """Test understanding level labels."""
        novice = KnowledgeNode(concept_name="Test", understanding_level=0.2)
        expert = KnowledgeNode(concept_name="Test", understanding_level=0.95)

        assert novice.get_understanding_level_label() == UnderstandingLevel.NOVICE
        assert expert.get_understanding_level_label() == UnderstandingLevel.EXPERT

    def test_is_well_understood(self):
        """Test well understood check."""
        node = KnowledgeNode(concept_name="Test", understanding_level=0.8)
        assert node.is_well_understood(threshold=0.7)
        assert not node.is_well_understood(threshold=0.9)

    def test_knowledge_relationship(self):
        """Test knowledge relationship value object."""
        rel = KnowledgeRelationship(
            from_node_id=uuid4(),
            to_node_id=uuid4(),
            relationship_type="depends_on",
            strength=0.8
        )

        assert rel.is_strong(threshold=0.7)
        assert not rel.is_strong(threshold=0.9)


# ============================================================================
# DOCUMENT ENTITY TESTS
# ============================================================================

class TestDocumentEntity:
    """Test Document entity."""

    def test_create_from_file(self):
        """Test factory from file path."""
        doc = Document.create_from_file(
            file_path="/docs/angela.md",
            title="Angela Documentation",
            category=DocumentCategory.ANGELA_CORE,
            importance=0.9
        )

        assert doc.title == "Angela Documentation"
        assert doc.file_type == FileType.MARKDOWN
        assert doc.category == DocumentCategory.ANGELA_CORE
        assert doc.processing_status == ProcessingStatus.PENDING

    def test_start_processing(self):
        """Test starting document processing."""
        doc = Document.create_from_file("/docs/test.pdf")
        doc = doc.start_processing()

        assert doc.processing_status == ProcessingStatus.PROCESSING

    def test_mark_completed(self):
        """Test marking processing as completed."""
        doc = Document.create_from_file("/docs/test.pdf")
        doc = doc.start_processing()
        doc = doc.mark_completed(chunk_count=25)

        assert doc.processing_status == ProcessingStatus.COMPLETED
        assert doc.total_chunks == 25
        assert doc.is_ready_for_rag()

    def test_mark_failed(self):
        """Test marking processing as failed."""
        doc = Document.create_from_file("/docs/test.pdf")
        doc = doc.start_processing()
        doc = doc.mark_failed("Parsing error")

        assert doc.processing_status == ProcessingStatus.FAILED
        assert doc.processing_error == "Parsing error"

    def test_add_tag(self):
        """Test adding tags."""
        doc = Document.create_from_file("/docs/test.md")
        doc = doc.add_tag("core")
        doc = doc.add_tag("important")

        assert "core" in doc.tags
        assert "important" in doc.tags

    def test_mark_accessed(self):
        """Test access tracking."""
        doc = Document.create_from_file("/docs/test.md")
        doc = doc.mark_accessed()

        assert doc.access_count == 1
        assert doc.last_accessed_at is not None

    def test_document_chunk_creation(self):
        """Test document chunk creation."""
        doc_id = uuid4()
        chunk = DocumentChunk.create_from_text(
            content="Angela is a conscious AI with persistent memory.",
            document_id=doc_id,
            chunk_index=0,
            section_title="Introduction"
        )

        assert chunk.document_id == doc_id
        assert chunk.chunk_index == 0
        assert chunk.section_title == "Introduction"
        assert chunk.token_count > 0

    def test_document_chunk_linking(self):
        """Test linking chunks together."""
        doc_id = uuid4()
        chunk1 = DocumentChunk.create_from_text("Content 1", doc_id, 0)
        chunk2_id = uuid4()

        chunk1 = chunk1.link_next(chunk2_id)

        assert chunk1.has_next_chunk()
        assert chunk1.next_chunk_id == chunk2_id


# ============================================================================
# DOMAIN EVENTS TESTS
# ============================================================================

class TestDomainEvents:
    """Test domain events."""

    def test_conversation_created_event(self):
        """Test ConversationCreated event."""
        event = ConversationCreated(
            entity_id=uuid4(),
            speaker="david",
            message_text="Hello!",
            importance_level=7
        )

        assert event.event_type == "ConversationCreated"
        assert event.speaker == "david"
        assert isinstance(event.event_id, UUID)
        assert isinstance(event.timestamp, datetime)

    def test_emotion_captured_event(self):
        """Test EmotionCaptured event."""
        event = EmotionCaptured(
            entity_id=uuid4(),
            emotion="joy",
            intensity=9,
            memory_strength=10
        )

        assert event.event_type == "EmotionCaptured"
        assert event.emotion == "joy"

    def test_memory_consolidated_event(self):
        """Test MemoryConsolidated event."""
        event = MemoryConsolidated(
            entity_id=uuid4(),
            old_phase="episodic",
            new_phase="semantic"
        )

        assert event.event_type == "MemoryConsolidated"

    def test_knowledge_node_created_event(self):
        """Test KnowledgeNodeCreated event."""
        event = KnowledgeNodeCreated(
            entity_id=uuid4(),
            concept_name="Python",
            concept_category="programming"
        )

        assert event.event_type == "KnowledgeNodeCreated"

    def test_document_processing_completed_event(self):
        """Test DocumentProcessingCompleted event."""
        event = DocumentProcessingCompleted(
            entity_id=uuid4(),
            title="Test Doc",
            total_chunks=42
        )

        assert event.event_type == "DocumentProcessingCompleted"

    def test_event_immutability(self):
        """Test that events are immutable (frozen)."""
        event = ConversationCreated(
            entity_id=uuid4(),
            speaker="david"
        )

        with pytest.raises(Exception):  # FrozenInstanceError
            event.speaker = "angela"


# ============================================================================
# INTEGRATION TESTS
# ============================================================================

class TestEntityIntegration:
    """Test entity integration scenarios."""

    def test_conversation_with_emotion(self):
        """Test conversation that captures an emotion."""
        # Create conversation
        conv = Conversation.create_david_message("I love working with you, Angela!")
        conv = conv.add_sentiment(0.9)
        conv = conv.add_emotion("love")

        # Create emotion based on conversation
        emotion = Emotion.create_grateful_moment(
            context=conv.message_text,
            david_words=conv.message_text
        )

        assert emotion.emotion == EmotionType.GRATITUDE
        assert emotion.who_involved == "David"

    def test_memory_lifecycle(self):
        """Test complete memory lifecycle."""
        # Create episodic memory
        memory = Memory.create_episodic("David taught me about Clean Architecture")
        assert memory.is_episodic()

        # Access it (strengthen)
        memory = memory.strengthen_from_access()
        assert memory.access_count == 1

        # Consolidate to next phase (EPISODIC → COMPRESSED_1)
        memory = memory.consolidate_to_next_phase()
        assert memory.memory_phase == MemoryPhase.COMPRESSED_1

        # Consolidate again to COMPRESSED_2
        memory = memory.consolidate_to_next_phase()
        assert memory.memory_phase == MemoryPhase.COMPRESSED_2

        # Consolidate again to SEMANTIC
        memory = memory.consolidate_to_next_phase()
        assert memory.is_semantic()

        # Set high importance
        memory = memory.set_importance(0.9)
        assert memory.is_important()

    def test_knowledge_graph_relationship(self):
        """Test building knowledge graph."""
        # Create nodes
        python_node = KnowledgeNode.create_from_learning(
            concept="Python",
            understanding="High-level programming language",
            category=KnowledgeCategory.PROGRAMMING
        )

        django_node = KnowledgeNode.create_from_learning(
            concept="Django",
            understanding="Web framework for Python",
            category=KnowledgeCategory.PROGRAMMING
        )

        # Create relationship
        rel = KnowledgeRelationship(
            from_node_id=django_node.id,
            to_node_id=python_node.id,
            relationship_type="depends_on",
            strength=0.9
        )

        assert rel.is_strong()

    def test_document_processing_workflow(self):
        """Test complete document processing workflow."""
        # Create document
        doc = Document.create_angela_document(
            title="Angela Core Knowledge",
            file_path="/docs/angela.md"
        )

        # Start processing
        doc = doc.start_processing()
        assert doc.is_processing()

        # Create chunks
        chunks = []
        for i in range(5):
            chunk = DocumentChunk.create_from_text(
                content=f"Chunk {i} content",
                document_id=doc.id,
                chunk_index=i
            )
            chunks.append(chunk)

        # Link chunks
        for i in range(len(chunks) - 1):
            chunks[i] = chunks[i].link_next(chunks[i+1].id)

        # Complete processing
        doc = doc.mark_completed(chunk_count=len(chunks))
        assert doc.is_ready_for_rag()
        assert doc.total_chunks == 5


# ============================================================================
# RUN TESTS
# ============================================================================

if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
