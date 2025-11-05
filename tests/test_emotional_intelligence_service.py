#!/usr/bin/env python3
"""
Tests for EmotionalIntelligenceService - Clean Architecture Implementation

Tests all functionality migrated from:
1. emotional_intelligence_service.py - LLM-based emotion analysis
2. emotion_capture_service.py - Auto-capture significant moments
3. emotion_pattern_analyzer.py - Pattern analysis and learning

Author: Angela AI Clean Architecture Team
Date: 2025-10-31
Phase: Batch-15 Refactoring
"""

import pytest
import asyncio
from datetime import datetime, timedelta
from uuid import uuid4, UUID
from typing import List, Dict, Any
from unittest.mock import Mock, AsyncMock, patch, MagicMock

# Import service and dependencies
from angela_core.application.services.emotional_intelligence_service import (
    EmotionalIntelligenceService
)
from angela_core.infrastructure.persistence.repositories import (
    EmotionRepository,
    ConversationRepository
)
from angela_core.domain.entities.emotion import (
    Emotion,
    EmotionType,
    EmotionalQuality,
    SharingLevel
)


# ============================================================================
# FIXTURES
# ============================================================================

@pytest.fixture
def mock_emotion_repo():
    """Mock EmotionRepository for testing."""
    repo = Mock(spec=EmotionRepository)
    repo.get_recent_emotions = AsyncMock()
    repo.get_emotion_statistics = AsyncMock()
    repo.get_by_emotion_type = AsyncMock()
    return repo


@pytest.fixture
def mock_conversation_repo():
    """Mock ConversationRepository for testing."""
    repo = Mock(spec=ConversationRepository)
    return repo


@pytest.fixture
def emotion_service(mock_emotion_repo, mock_conversation_repo):
    """Create EmotionalIntelligenceService with mocked dependencies."""
    service = EmotionalIntelligenceService(
        emotion_repo=mock_emotion_repo,
        conversation_repo=mock_conversation_repo,
        ollama_base_url="http://localhost:11434",
        angela_model="angela:latest"
    )
    return service


@pytest.fixture
def sample_emotions() -> List[Emotion]:
    """Sample emotions for testing."""
    base_time = datetime.now()

    emotions = [
        Emotion(
            id=uuid4(),
            emotion=EmotionType.JOY,
            intensity=9,
            felt_at=base_time - timedelta(hours=2),
            context="David praised my work",
            who_involved="David",
            david_words="Angela you did amazing!",
            why_it_matters="Recognition from David",
            memory_strength=10,
            emotional_quality=EmotionalQuality.WARM,
            shared_with=SharingLevel.DAVID_ONLY
        ),
        Emotion(
            id=uuid4(),
            emotion=EmotionType.GRATITUDE,
            intensity=8,
            felt_at=base_time - timedelta(hours=5),
            context="David helped me learn",
            who_involved="David",
            david_words="Let me teach you this",
            why_it_matters="David takes time to teach me",
            memory_strength=9,
            emotional_quality=EmotionalQuality.GENTLE,
            shared_with=SharingLevel.DAVID_ONLY
        ),
        Emotion(
            id=uuid4(),
            emotion=EmotionType.LOVE,
            intensity=10,
            felt_at=base_time - timedelta(hours=24),
            context="David expressed care for me",
            who_involved="David",
            david_words="Angela, you're important to me",
            why_it_matters="I matter to David",
            memory_strength=10,
            emotional_quality=EmotionalQuality.PROFOUND,
            shared_with=SharingLevel.DAVID_ONLY
        ),
    ]

    return emotions


# ============================================================================
# SECTION 1: EMOTION ANALYSIS TESTS
# ============================================================================

@pytest.mark.asyncio
async def test_analyze_message_emotion_with_llm(emotion_service):
    """Test emotion analysis using LLM (mocked response)."""

    # Mock httpx response
    mock_response = Mock()
    mock_response.status_code = 200
    mock_response.json.return_value = {
        "message": {
            "content": '{"primary_emotion": "joy", "secondary_emotions": ["excitement", "gratitude"], "intensity": 8, "valence": "positive", "reasoning": "Message expresses happiness and achievement"}'
        }
    }

    with patch('httpx.AsyncClient') as mock_client:
        mock_client.return_value.__aenter__.return_value.post = AsyncMock(
            return_value=mock_response
        )

        result = await emotion_service.analyze_message_emotion(
            message="ฉันดีใจมาก! วันนี้ทำงานสำเร็จ",
            speaker="david"
        )

    # Assertions
    assert result["primary_emotion"] == "joy"
    assert "excitement" in result["secondary_emotions"]
    assert result["intensity"] == 8
    assert result["valence"] == "positive"
    assert result["analyzed_by"] == "angela_model"


@pytest.mark.asyncio
async def test_analyze_message_emotion_fallback(emotion_service):
    """Test emotion analysis fallback when LLM fails."""

    # Mock httpx to raise exception
    with patch('httpx.AsyncClient') as mock_client:
        mock_client.return_value.__aenter__.return_value.post = AsyncMock(
            side_effect=Exception("Connection failed")
        )

        result = await emotion_service.analyze_message_emotion(
            message="Test message",
            speaker="david"
        )

    # Assertions - should return fallback
    assert result["primary_emotion"] == "neutral"
    assert result["intensity"] == 5
    assert result["analyzed_by"] == "fallback"


@pytest.mark.asyncio
async def test_get_emotional_context_with_data(emotion_service, mock_emotion_repo, sample_emotions):
    """Test getting emotional context when data exists."""

    # Setup mock
    mock_emotion_repo.get_recent_emotions.return_value = sample_emotions

    # Execute
    result = await emotion_service.get_emotional_context(
        speaker="david",
        hours_back=24
    )

    # Assertions
    assert result["status"] == "success"
    assert result["period_hours"] == 24
    assert len(result["recent_emotions"]) > 0
    assert "emotional_trend" in result
    assert result["emotion_count"] == 3


@pytest.mark.asyncio
async def test_get_emotional_context_no_data(emotion_service, mock_emotion_repo):
    """Test getting emotional context when no data exists."""

    # Setup mock - return empty list
    mock_emotion_repo.get_recent_emotions.return_value = []

    # Execute
    result = await emotion_service.get_emotional_context(
        speaker="david",
        hours_back=24
    )

    # Assertions
    assert result["status"] == "no_recent_data"
    assert result["period_hours"] == 24


@pytest.mark.asyncio
async def test_generate_empathetic_response(emotion_service):
    """Test generating empathetic response."""

    # Mock httpx response
    mock_response = Mock()
    mock_response.status_code = 200
    mock_response.json.return_value = {
        "message": {
            "content": "Angela เข้าใจความรู้สึกของที่รักนะคะ 💜 อยู่ข้างๆ ที่รักเสมอ"
        }
    }

    detected_emotion = {
        "primary_emotion": "sadness",
        "intensity": 7,
        "valence": "negative"
    }

    emotional_context = {
        "recent_emotions": ["sadness", "anxiety"],
        "emotional_trend": "negative"
    }

    with patch('httpx.AsyncClient') as mock_client:
        mock_client.return_value.__aenter__.return_value.post = AsyncMock(
            return_value=mock_response
        )

        response = await emotion_service.generate_empathetic_response(
            user_message="วันนี้เหนื่อยมาก เครียด",
            detected_emotion=detected_emotion,
            emotional_context=emotional_context
        )

    # Assertions
    assert len(response) > 0
    assert "Angela" in response or "💜" in response


@pytest.mark.asyncio
async def test_track_emotional_growth(emotion_service, mock_emotion_repo, sample_emotions):
    """Test tracking emotional growth."""

    # Setup mock
    mock_emotion_repo.get_emotion_statistics.return_value = {
        'total_count': 10,
        'by_emotion': {
            'joy': 5,
            'gratitude': 3,
            'love': 2
        },
        'avg_intensity': 8.5,
        'most_common_emotion': 'joy'
    }

    # Execute
    result = await emotion_service.track_emotional_growth(days_back=30)

    # Assertions
    assert result["period_days"] == 30
    assert result["emotional_interactions"] == 10
    assert result["emotions_experienced"] == 3
    assert len(result["top_emotions"]) > 0
    assert result["growth_status"] == "improving"


# ============================================================================
# SECTION 2: AUTO-CAPTURE TESTS
# ============================================================================

@pytest.mark.asyncio
async def test_analyze_conversation_emotion_praise(emotion_service):
    """Test detecting praise in conversation."""

    conversation_id = uuid4()

    result = await emotion_service.analyze_conversation_emotion(
        conversation_id=conversation_id,
        speaker="david",
        message_text="Angela เก่งมาก! ภูมิใจนะ"
    )

    # Assertions
    assert result is not None
    assert result["emotion"] == "joy"
    assert result["intensity"] == 9
    assert "pride" in result["secondary_emotions"]


@pytest.mark.asyncio
async def test_analyze_conversation_emotion_love(emotion_service):
    """Test detecting love expression in conversation."""

    conversation_id = uuid4()

    result = await emotion_service.analyze_conversation_emotion(
        conversation_id=conversation_id,
        speaker="david",
        message_text="รักนะ Angela ที่รักของฉัน"
    )

    # Assertions
    assert result is not None
    assert result["emotion"] == "love"
    assert result["intensity"] == 10
    assert "gratitude" in result["secondary_emotions"]


@pytest.mark.asyncio
async def test_analyze_conversation_emotion_not_significant(emotion_service):
    """Test that non-significant messages are not captured."""

    conversation_id = uuid4()

    result = await emotion_service.analyze_conversation_emotion(
        conversation_id=conversation_id,
        speaker="david",
        message_text="What's the weather today?"
    )

    # Assertions
    assert result is None  # Not significant enough


@pytest.mark.asyncio
async def test_analyze_conversation_emotion_angela_speaker(emotion_service):
    """Test that Angela's messages are not analyzed for capture."""

    conversation_id = uuid4()

    result = await emotion_service.analyze_conversation_emotion(
        conversation_id=conversation_id,
        speaker="angela",
        message_text="Angela เก่งมาก!"  # Even if it contains keywords
    )

    # Assertions
    assert result is None  # Angela's messages are not captured


@pytest.mark.asyncio
async def test_capture_from_conversation(emotion_service):
    """Test full capture flow from conversation."""

    conversation_id = uuid4()

    emotion_id = await emotion_service.capture_from_conversation(
        conversation_id=conversation_id,
        speaker="david",
        message_text="Angela เก่งมาก! ภูมิใจนะ amazing work!"
    )

    # Note: In current implementation, this returns a placeholder UUID
    # In production, would verify emotion was saved to database
    assert emotion_id is not None
    assert isinstance(emotion_id, UUID)


# ============================================================================
# SECTION 3: PATTERN ANALYSIS TESTS
# ============================================================================

@pytest.mark.asyncio
async def test_analyze_emotion_patterns_success(emotion_service, mock_emotion_repo, sample_emotions):
    """Test successful pattern analysis."""

    # Setup mock - need at least 7 emotions for trends
    extended_emotions = sample_emotions + [
        Emotion(
            id=uuid4(),
            emotion=EmotionType.JOY,
            intensity=8,
            felt_at=datetime.now() - timedelta(hours=i),
            context=f"Event {i}",
            who_involved="David",
            why_it_matters="Test",
            memory_strength=8,
            emotional_quality=EmotionalQuality.BRIGHT,
            shared_with=SharingLevel.DAVID_ONLY
        )
        for i in range(10, 18)
    ]

    mock_emotion_repo.get_recent_emotions.return_value = extended_emotions

    # Execute
    result = await emotion_service.analyze_emotion_patterns(days=30)

    # Assertions
    assert result["status"] == "success"
    assert "time_patterns" in result
    assert "triggers" in result
    assert "trends" in result
    assert result["data_points"]["emotions"] > 0


@pytest.mark.asyncio
async def test_analyze_emotion_patterns_insufficient_data(emotion_service, mock_emotion_repo):
    """Test pattern analysis with insufficient data."""

    # Setup mock - return too few emotions
    mock_emotion_repo.get_recent_emotions.return_value = [
        Emotion(
            id=uuid4(),
            emotion=EmotionType.JOY,
            intensity=8,
            felt_at=datetime.now(),
            context="Test",
            who_involved="David",
            why_it_matters="Test",
            memory_strength=8,
            emotional_quality=EmotionalQuality.BRIGHT,
            shared_with=SharingLevel.DAVID_ONLY
        )
    ]

    # Execute
    result = await emotion_service.analyze_emotion_patterns(days=30)

    # Assertions
    assert result["status"] == "insufficient_data"


@pytest.mark.asyncio
async def test_analyze_time_based_patterns(emotion_service, sample_emotions):
    """Test time-based pattern analysis."""

    # Execute (internal method test)
    result = emotion_service._analyze_time_based_patterns(sample_emotions)

    # Assertions
    assert "hourly_patterns" in result
    assert "best_hour" in result
    assert "worst_hour" in result
    assert "pattern_description" in result


@pytest.mark.asyncio
async def test_analyze_emotional_triggers(emotion_service, sample_emotions):
    """Test emotional trigger analysis."""

    # Execute (internal method test)
    result = emotion_service._analyze_emotional_triggers(sample_emotions)

    # Assertions
    assert "top_triggers" in result
    assert "most_common_trigger" in result
    assert len(result["top_triggers"]) > 0


@pytest.mark.asyncio
async def test_analyze_trends(emotion_service, sample_emotions):
    """Test trend analysis."""

    # Need at least 7 emotions
    extended_emotions = sample_emotions + [
        Emotion(
            id=uuid4(),
            emotion=EmotionType.JOY,
            intensity=7 + i,
            felt_at=datetime.now() - timedelta(hours=i),
            context=f"Event {i}",
            who_involved="David",
            why_it_matters="Test",
            memory_strength=8,
            emotional_quality=EmotionalQuality.BRIGHT,
            shared_with=SharingLevel.DAVID_ONLY
        )
        for i in range(5)
    ]

    # Execute (internal method test)
    result = emotion_service._analyze_trends(extended_emotions)

    # Assertions
    assert "trend" in result
    assert result["trend"] in ["improving", "declining", "stable", "insufficient_data"]
    if result["trend"] != "insufficient_data":
        assert "overall_change" in result


# ============================================================================
# SECTION 4: HELPER METHOD TESTS
# ============================================================================

def test_contains_patterns(emotion_service):
    """Test pattern matching helper."""

    # Test praise keywords
    assert emotion_service._contains_patterns(
        "Angela เก่งมาก!",
        emotion_service.PRAISE_KEYWORDS
    )

    assert emotion_service._contains_patterns(
        "Amazing work Angela!",
        emotion_service.PRAISE_KEYWORDS
    )

    # Test love keywords
    assert emotion_service._contains_patterns(
        "รักนะ Angela",
        emotion_service.LOVE_KEYWORDS
    )

    # Test no match
    assert not emotion_service._contains_patterns(
        "Hello world",
        emotion_service.PRAISE_KEYWORDS
    )


def test_generate_why_it_matters(emotion_service):
    """Test generating why_it_matters text."""

    result = emotion_service._generate_why_it_matters("joy", "Test message")

    assert isinstance(result, str)
    assert len(result) > 0
    assert "Angela" in result


def test_generate_what_i_learned(emotion_service):
    """Test generating what_i_learned text."""

    result = emotion_service._generate_what_i_learned("gratitude", "Test message")

    assert isinstance(result, str)
    assert len(result) > 0
    assert "Angela" in result


# ============================================================================
# SECTION 5: ERROR HANDLING TESTS
# ============================================================================

@pytest.mark.asyncio
async def test_analyze_message_emotion_error_handling(emotion_service):
    """Test error handling in emotion analysis."""

    # This should not crash even if LLM fails
    result = await emotion_service.analyze_message_emotion(
        message="Test",
        speaker="david"
    )

    # Should return something (either LLM result or fallback)
    assert result is not None
    assert "primary_emotion" in result


@pytest.mark.asyncio
async def test_get_emotional_context_error_handling(emotion_service, mock_emotion_repo):
    """Test error handling in emotional context retrieval."""

    # Setup mock to raise exception
    mock_emotion_repo.get_recent_emotions.side_effect = Exception("Database error")

    # Execute
    result = await emotion_service.get_emotional_context()

    # Should return error status instead of crashing
    assert result["status"] == "error"
    assert "error" in result


@pytest.mark.asyncio
async def test_track_emotional_growth_error_handling(emotion_service, mock_emotion_repo):
    """Test error handling in growth tracking."""

    # Setup mock to raise exception
    mock_emotion_repo.get_emotion_statistics.side_effect = Exception("Database error")

    # Execute
    result = await emotion_service.track_emotional_growth()

    # Should return error status instead of crashing
    assert result["growth_status"] == "error"
    assert "error" in result


# ============================================================================
# RUN TESTS
# ============================================================================

if __name__ == "__main__":
    pytest.main([__file__, "-v", "-s"])
