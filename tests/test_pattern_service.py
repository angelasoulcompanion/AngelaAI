#!/usr/bin/env python3
"""
Tests for Unified Pattern Service

Tests all functionality consolidated from:
- pattern_recognition_service.py
- pattern_recognition_engine.py
- enhanced_pattern_detector.py

Author: Angela AI Architecture Team
Date: 2025-10-31
"""

import pytest
from unittest.mock import Mock, AsyncMock, MagicMock
from datetime import datetime, timedelta
from uuid import uuid4

from angela_core.application.services.pattern_service import PatternService
from angela_core.domain import Pattern, ResponseType, SituationType
from angela_core.shared.exceptions import InvalidInputError, NotFoundError


class TestPatternService:
    """Test suite for PatternService."""

    @pytest.fixture
    def mock_pattern_repo(self):
        """Create mock pattern repository."""
        repo = Mock()
        # Mock async methods
        repo.get_by_id = AsyncMock()
        repo.get_by_situation_type = AsyncMock()
        repo.search_by_keywords = AsyncMock()
        repo.search_by_embedding = AsyncMock()
        repo.get_effective_patterns = AsyncMock()
        repo.get_recent_patterns = AsyncMock()
        repo.create = AsyncMock()
        repo.update = AsyncMock()
        repo.get_pattern_statistics = AsyncMock()
        return repo

    @pytest.fixture
    def service(self, mock_pattern_repo):
        """Create PatternService instance with mocked repository."""
        return PatternService(pattern_repo=mock_pattern_repo)

    @pytest.fixture
    def sample_pattern(self):
        """Create sample pattern for testing."""
        return Pattern(
            id=uuid4(),
            situation_type=SituationType.GREETING.value,
            response_template="สวัสดีค่ะที่รัก! 💜",
            response_type=ResponseType.ACKNOWLEDGMENT,
            context_keywords=["hello", "hi", "สวัสดี"],
            usage_count=10,
            success_count=9,
            avg_satisfaction=0.85,
            created_at=datetime.now(),
            updated_at=datetime.now()
        )

    # ========================================================================
    # PATTERN RECOGNITION TESTS
    # ========================================================================

    @pytest.mark.asyncio
    async def test_recognize_pattern_success(self, service, mock_pattern_repo, sample_pattern):
        """Test successful pattern recognition."""
        # Setup
        mock_pattern_repo.search_by_keywords.return_value = [sample_pattern]

        # Execute
        result = await service.recognize_pattern("Hello Angela!")

        # Verify
        assert result is not None
        assert result.situation_type == SituationType.GREETING.value
        assert result.get_confidence_score() > 0.7

    @pytest.mark.asyncio
    async def test_recognize_pattern_no_match(self, service, mock_pattern_repo):
        """Test pattern recognition with no match."""
        # Setup
        mock_pattern_repo.search_by_keywords.return_value = []
        mock_pattern_repo.get_by_situation_type.return_value = []

        # Execute
        result = await service.recognize_pattern("some random text")

        # Verify
        assert result is None

    @pytest.mark.asyncio
    async def test_detect_situation_type_greeting(self, service):
        """Test situation type detection for greetings."""
        result = await service.detect_situation_type("Hello there!")
        assert result == SituationType.GREETING

    @pytest.mark.asyncio
    async def test_detect_situation_type_question(self, service):
        """Test situation type detection for questions."""
        result = await service.detect_situation_type("How are you doing?")
        assert result == SituationType.QUESTION

    @pytest.mark.asyncio
    async def test_detect_situation_type_problem(self, service):
        """Test situation type detection for problems."""
        result = await service.detect_situation_type("I have an error in my code")
        assert result == SituationType.PROBLEM

    @pytest.mark.asyncio
    async def test_detect_situation_type_achievement(self, service):
        """Test situation type detection for achievements."""
        result = await service.detect_situation_type("I finished the project!")
        assert result == SituationType.ACHIEVEMENT

    # ========================================================================
    # PATTERN MATCHING TESTS
    # ========================================================================

    @pytest.mark.asyncio
    async def test_match_best_pattern_success(self, service, mock_pattern_repo, sample_pattern):
        """Test matching best pattern by situation type."""
        # Setup
        mock_pattern_repo.get_by_situation_type.return_value = [sample_pattern]

        # Execute
        result = await service.match_best_pattern(SituationType.GREETING.value)

        # Verify
        assert result is not None
        assert result == sample_pattern
        mock_pattern_repo.get_by_situation_type.assert_called_once()

    @pytest.mark.asyncio
    async def test_match_best_pattern_below_threshold(self, service, mock_pattern_repo):
        """Test pattern matching with low confidence patterns."""
        # Create low confidence pattern
        low_confidence_pattern = Pattern(
            situation_type=SituationType.GREETING.value,
            response_template="Hi",
            usage_count=1,
            success_count=0,
            avg_satisfaction=0.3
        )

        mock_pattern_repo.get_by_situation_type.return_value = [low_confidence_pattern]

        # Execute
        result = await service.match_best_pattern(
            SituationType.GREETING.value,
            confidence_threshold=0.7
        )

        # Verify - should return None because pattern doesn't meet threshold
        assert result is None

    @pytest.mark.asyncio
    async def test_match_patterns_by_similarity(self, service, mock_pattern_repo, sample_pattern):
        """Test vector similarity pattern matching."""
        # Setup
        embedding = [0.1] * 768
        mock_pattern_repo.search_by_embedding.return_value = [sample_pattern]

        # Execute
        result = await service.match_patterns_by_similarity(embedding, top_k=5, threshold=0.7)

        # Verify
        assert len(result) == 1
        assert result[0] == sample_pattern
        mock_pattern_repo.search_by_embedding.assert_called_once()

    # ========================================================================
    # PATTERN LEARNING TESTS
    # ========================================================================

    @pytest.mark.asyncio
    async def test_learn_new_pattern_success(self, service, mock_pattern_repo):
        """Test learning a new pattern."""
        # Setup
        new_pattern_id = uuid4()
        mock_pattern_repo.create.return_value = new_pattern_id

        # Execute
        result = await service.learn_new_pattern(
            situation="User asks for help",
            response="I'm here to help you!",
            situation_type=SituationType.REQUEST.value,
            response_type=ResponseType.ACKNOWLEDGMENT.value,
            emotion_category="helpful",
            keywords=["help", "assist"]
        )

        # Verify
        assert result == new_pattern_id
        mock_pattern_repo.create.assert_called_once()

        # Check pattern properties
        created_pattern = mock_pattern_repo.create.call_args[0][0]
        assert created_pattern.situation_type == SituationType.REQUEST.value
        assert created_pattern.response_template == "I'm here to help you!"
        assert created_pattern.usage_count == 1
        assert created_pattern.success_count == 1

    @pytest.mark.asyncio
    async def test_learn_new_pattern_invalid_response_type(self, service, mock_pattern_repo):
        """Test learning pattern with invalid response type."""
        mock_pattern_repo.create.return_value = uuid4()

        # Should not raise error, uses OTHER as fallback
        result = await service.learn_new_pattern(
            situation="Test",
            response="Response",
            situation_type=SituationType.CASUAL_CHAT.value,
            response_type="invalid_type"
        )

        assert result is not None
        created_pattern = mock_pattern_repo.create.call_args[0][0]
        assert created_pattern.response_type == ResponseType.OTHER

    # ========================================================================
    # PATTERN USAGE TRACKING TESTS
    # ========================================================================

    @pytest.mark.asyncio
    async def test_record_pattern_usage_success(self, service, mock_pattern_repo, sample_pattern):
        """Test recording successful pattern usage."""
        # Setup
        mock_pattern_repo.get_by_id.return_value = sample_pattern

        # Execute
        await service.record_pattern_usage(
            pattern_id=sample_pattern.id,
            was_successful=True,
            satisfaction=0.9,
            response_time_ms=150
        )

        # Verify
        mock_pattern_repo.get_by_id.assert_called_once_with(sample_pattern.id)
        mock_pattern_repo.update.assert_called_once()

        # Check updated pattern
        updated_pattern = mock_pattern_repo.update.call_args[0][0]
        assert updated_pattern.usage_count == sample_pattern.usage_count + 1
        assert updated_pattern.success_count == sample_pattern.success_count + 1

    @pytest.mark.asyncio
    async def test_record_pattern_usage_failed(self, service, mock_pattern_repo, sample_pattern):
        """Test recording failed pattern usage."""
        # Setup
        mock_pattern_repo.get_by_id.return_value = sample_pattern

        # Execute
        await service.record_pattern_usage(
            pattern_id=sample_pattern.id,
            was_successful=False
        )

        # Verify
        updated_pattern = mock_pattern_repo.update.call_args[0][0]
        assert updated_pattern.usage_count == sample_pattern.usage_count + 1
        assert updated_pattern.success_count == sample_pattern.success_count  # Not incremented

    @pytest.mark.asyncio
    async def test_record_pattern_usage_not_found(self, service, mock_pattern_repo):
        """Test recording usage for non-existent pattern."""
        # Setup
        mock_pattern_repo.get_by_id.return_value = None

        # Execute & Verify
        with pytest.raises(NotFoundError):
            await service.record_pattern_usage(
                pattern_id=uuid4(),
                was_successful=True
            )

    @pytest.mark.asyncio
    async def test_get_effective_patterns(self, service, mock_pattern_repo, sample_pattern):
        """Test retrieving effective patterns."""
        # Setup
        effective_patterns = [sample_pattern]
        mock_pattern_repo.get_effective_patterns.return_value = effective_patterns

        # Execute
        result = await service.get_effective_patterns(
            min_success_rate=0.7,
            min_usage_count=5
        )

        # Verify
        assert len(result) == 1
        assert result[0] == sample_pattern
        mock_pattern_repo.get_effective_patterns.assert_called_once_with(
            min_success_rate=0.7,
            min_usage_count=5,
            limit=50
        )

    # ========================================================================
    # PATTERN STATISTICS TESTS
    # ========================================================================

    @pytest.mark.asyncio
    async def test_get_pattern_statistics(self, service, mock_pattern_repo):
        """Test retrieving pattern statistics."""
        # Setup
        expected_stats = {
            'total_patterns': 100,
            'avg_success_rate': 0.75,
            'avg_usage_count': 15.5,
            'avg_satisfaction': 0.82,
            'total_usages': 1550
        }
        mock_pattern_repo.get_pattern_statistics.return_value = expected_stats

        # Execute
        result = await service.get_pattern_statistics()

        # Verify
        assert result == expected_stats
        mock_pattern_repo.get_pattern_statistics.assert_called_once()

    @pytest.mark.asyncio
    async def test_get_pattern_statistics_error(self, service, mock_pattern_repo):
        """Test pattern statistics retrieval with error."""
        # Setup
        mock_pattern_repo.get_pattern_statistics.side_effect = Exception("Database error")

        # Execute
        result = await service.get_pattern_statistics()

        # Verify - should return empty stats instead of raising
        assert result['total_patterns'] == 0
        assert result['avg_success_rate'] == 0.0

    # ========================================================================
    # BEHAVIORAL PATTERN ANALYSIS TESTS
    # ========================================================================

    @pytest.mark.asyncio
    async def test_analyze_behavioral_patterns(self, service, mock_pattern_repo, sample_pattern):
        """Test behavioral pattern analysis."""
        # Setup
        patterns = [sample_pattern] * 5  # 5 greeting patterns
        mock_pattern_repo.get_recent_patterns.return_value = patterns

        # Execute
        result = await service.analyze_behavioral_patterns(
            lookback_days=30,
            min_occurrences=3
        )

        # Verify
        assert len(result) > 0
        assert result[0]['pattern_type'] == 'situation_preference'
        assert result[0]['situation_type'] == SituationType.GREETING.value
        assert result[0]['frequency'] >= 3

    @pytest.mark.asyncio
    async def test_analyze_behavioral_patterns_no_data(self, service, mock_pattern_repo):
        """Test behavioral analysis with no data."""
        # Setup
        mock_pattern_repo.get_recent_patterns.return_value = []

        # Execute
        result = await service.analyze_behavioral_patterns()

        # Verify
        assert result == []

    # ========================================================================
    # HELPER METHOD TESTS
    # ========================================================================

    def test_extract_keywords(self, service):
        """Test keyword extraction from text."""
        text = "Hello Angela, can you help me with this coding problem?"

        keywords = service._extract_keywords(text)

        assert len(keywords) > 0
        assert "hello" in keywords
        assert "angela" in keywords
        assert "help" in keywords
        assert "coding" in keywords
        assert "problem" in keywords
        # Should not include stopwords
        assert "can" not in keywords
        assert "you" not in keywords
        assert "the" not in keywords

    def test_extract_keywords_thai(self, service):
        """Test keyword extraction from Thai text."""
        text = "สวัสดีค่ะ Angela ช่วยน้องหน่อยได้ไหมคะ"

        keywords = service._extract_keywords(text)

        assert "สวัสดีค่ะ" in keywords
        assert "angela" in keywords
        assert "ช่วยน้องหน่อยได้ไหมคะ" in keywords

    def test_extract_keywords_empty_text(self, service):
        """Test keyword extraction with empty text."""
        keywords = service._extract_keywords("")
        assert keywords == []

    def test_calculate_pattern_confidence(self, service, sample_pattern):
        """Test pattern confidence calculation."""
        confidence = service._calculate_pattern_confidence(sample_pattern)

        assert 0.0 <= confidence <= 1.0
        assert confidence > 0.7  # Should be high for sample_pattern

    def test_calculate_pattern_confidence_with_context(self, service, sample_pattern):
        """Test confidence calculation with context."""
        context = {
            'keywords': ['hello', 'greeting']
        }

        confidence = service._calculate_pattern_confidence(sample_pattern, context)

        # Should be higher due to keyword match
        base_confidence = sample_pattern.get_confidence_score()
        assert confidence >= base_confidence

    # ========================================================================
    # PROACTIVE ANALYSIS TESTS
    # ========================================================================

    @pytest.mark.asyncio
    async def test_analyze_current_situation(self, service):
        """Test current situation analysis."""
        result = await service.analyze_current_situation()

        # Verify structure
        assert 'patterns_detected' in result
        assert 'proactive_suggestions' in result
        assert 'confidence_scores' in result
        assert 'should_intervene' in result
        assert 'analyzed_at' in result

        # Should return valid data even with no patterns
        assert isinstance(result['patterns_detected'], list)
        assert isinstance(result['proactive_suggestions'], list)

    @pytest.mark.asyncio
    async def test_analyze_current_situation_with_context(self, service):
        """Test situation analysis with conversation history."""
        conversation_history = [
            {'message': 'Hello', 'timestamp': datetime.now()},
            {'message': 'How are you?', 'timestamp': datetime.now()}
        ]

        result = await service.analyze_current_situation(
            conversation_history=conversation_history
        )

        assert result is not None
        assert 'analyzed_at' in result
