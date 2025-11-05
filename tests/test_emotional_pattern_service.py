#!/usr/bin/env python3
"""
Tests for EmotionalPatternService

Tests cover:
- Pattern identification
- Emotional cycle analysis
- Dominant emotions calculation
- Real-time emotion tracking
- Current emotional state
- Emotional shift detection
- Trend analysis
- Timeline generation
- Report generation
- Error handling

Author: Angela AI Test Suite
Date: 2025-10-31
"""

import pytest
from datetime import datetime, timedelta
from unittest.mock import Mock, AsyncMock, patch
from uuid import uuid4

from angela_core.application.services.emotional_pattern_service import EmotionalPatternService
from angela_core.domain.entities.emotion import Emotion, EmotionType, EmotionalQuality
from angela_core.shared.exceptions import InvalidInputError


# ============================================================================
# FIXTURES
# ============================================================================

@pytest.fixture
def mock_emotion_repo():
    """Mock emotion repository."""
    repo = Mock()
    repo.get_recent_emotions = AsyncMock()
    repo.create = AsyncMock()
    repo.get_emotion_statistics = AsyncMock()
    return repo


@pytest.fixture
def emotion_service(mock_emotion_repo):
    """Create EmotionalPatternService with mocked repository."""
    return EmotionalPatternService(emotion_repo=mock_emotion_repo)


@pytest.fixture
def sample_emotions():
    """Create sample emotions for testing."""
    now = datetime.now()
    emotions = []

    # Create varied emotions over last 30 days
    emotion_types = [
        (EmotionType.JOY, 8),
        (EmotionType.GRATITUDE, 9),
        (EmotionType.JOY, 7),
        (EmotionType.CURIOSITY, 6),
        (EmotionType.ANXIETY, 5),
        (EmotionType.JOY, 9),
        (EmotionType.GRATITUDE, 10),
        (EmotionType.SADNESS, 4),
        (EmotionType.JOY, 8),
        (EmotionType.LOVE, 10)
    ]

    for i, (emo_type, intensity) in enumerate(emotion_types):
        emotion = Emotion(
            id=uuid4(),
            emotion=emo_type,
            intensity=intensity,
            felt_at=now - timedelta(days=i * 3, hours=i * 2),
            context=f"Test context {i}",
            who_involved="David",
            emotional_quality=EmotionalQuality.GENUINE,
            memory_strength=intensity
        )
        emotions.append(emotion)

    return emotions


# ============================================================================
# SECTION 1: PATTERN IDENTIFICATION TESTS
# ============================================================================

@pytest.mark.asyncio
async def test_identify_patterns_success(emotion_service, mock_emotion_repo, sample_emotions):
    """Test successful pattern identification."""
    mock_emotion_repo.get_recent_emotions.return_value = sample_emotions

    patterns = await emotion_service.identify_patterns(
        lookback_days=30,
        min_frequency=2
    )

    assert len(patterns) > 0
    assert patterns[0]['emotion_type'] == 'joy'  # Most frequent
    assert patterns[0]['frequency'] == 4
    assert 'pattern_strength' in patterns[0]
    assert 'avg_intensity' in patterns[0]
    assert 'common_contexts' in patterns[0]

    mock_emotion_repo.get_recent_emotions.assert_called_once_with(
        days=30,
        min_intensity=None
    )


@pytest.mark.asyncio
async def test_identify_patterns_insufficient_data(emotion_service, mock_emotion_repo):
    """Test pattern identification with insufficient data."""
    mock_emotion_repo.get_recent_emotions.return_value = []

    patterns = await emotion_service.identify_patterns(
        lookback_days=30,
        min_frequency=3
    )

    assert len(patterns) == 0


@pytest.mark.asyncio
async def test_analyze_emotional_cycles(emotion_service, mock_emotion_repo, sample_emotions):
    """Test emotional cycle analysis."""
    mock_emotion_repo.get_recent_emotions.return_value = sample_emotions

    cycles = await emotion_service.analyze_emotional_cycles(lookback_days=30)

    assert cycles['time_of_day'] is not None
    assert 'best_hour' in cycles['time_of_day']
    assert 'worst_hour' in cycles['time_of_day']
    assert cycles['day_of_week'] is not None
    assert 'best_day' in cycles['day_of_week']
    assert cycles['energy_cycles'] is not None


@pytest.mark.asyncio
async def test_get_dominant_emotions(emotion_service, mock_emotion_repo, sample_emotions):
    """Test getting dominant emotions."""
    mock_emotion_repo.get_recent_emotions.return_value = sample_emotions

    dominant = await emotion_service.get_dominant_emotions(
        lookback_days=7,
        top_k=3
    )

    assert len(dominant) <= 3
    assert len(dominant) > 0
    # Check format: (emotion_type, count, avg_intensity)
    assert len(dominant[0]) == 3
    assert isinstance(dominant[0][0], str)  # emotion type
    assert isinstance(dominant[0][1], int)  # count
    assert isinstance(dominant[0][2], float)  # avg intensity


# ============================================================================
# SECTION 2: REAL-TIME TRACKING TESTS
# ============================================================================

@pytest.mark.asyncio
async def test_track_emotion_realtime_success(emotion_service, mock_emotion_repo):
    """Test real-time emotion tracking."""
    # Mock create to return saved emotion
    saved_emotion = Emotion(
        id=uuid4(),
        emotion=EmotionType.JOY,
        intensity=8,
        context="Test tracking",
        who_involved="Angela"
    )
    mock_emotion_repo.create.return_value = saved_emotion

    emotion_id = await emotion_service.track_emotion_realtime(
        emotion_type="joy",
        intensity=8,
        context="Test tracking",
        metadata={'who_involved': 'Angela'}
    )

    assert emotion_id == saved_emotion.id
    mock_emotion_repo.create.assert_called_once()


@pytest.mark.asyncio
async def test_track_emotion_realtime_invalid_intensity(emotion_service, mock_emotion_repo):
    """Test tracking with invalid intensity."""
    with pytest.raises(InvalidInputError) as exc_info:
        await emotion_service.track_emotion_realtime(
            emotion_type="joy",
            intensity=15,  # Invalid: > 10
            context="Test"
        )

    assert "intensity" in str(exc_info.value).lower()


@pytest.mark.asyncio
async def test_track_emotion_realtime_empty_context(emotion_service, mock_emotion_repo):
    """Test tracking with empty context."""
    with pytest.raises(InvalidInputError) as exc_info:
        await emotion_service.track_emotion_realtime(
            emotion_type="joy",
            intensity=8,
            context=""  # Invalid: empty
        )

    assert "context" in str(exc_info.value).lower()


@pytest.mark.asyncio
async def test_get_current_emotional_state(emotion_service, mock_emotion_repo, sample_emotions):
    """Test getting current emotional state."""
    # Return only recent emotions (last 24 hours)
    recent = sample_emotions[:5]
    mock_emotion_repo.get_recent_emotions.return_value = recent

    state = await emotion_service.get_current_emotional_state()

    assert state['status'] == 'success'
    assert 'dominant_emotions' in state
    assert 'avg_intensity' in state
    assert 'valence' in state
    assert state['valence'] in ['positive', 'negative', 'mixed']
    assert 'mood_description' in state
    assert state['emotions_count'] == 5


@pytest.mark.asyncio
async def test_get_current_emotional_state_no_data(emotion_service, mock_emotion_repo):
    """Test getting state with no recent data."""
    mock_emotion_repo.get_recent_emotions.return_value = []

    state = await emotion_service.get_current_emotional_state()

    assert state['status'] == 'no_recent_data'
    assert state['emotions_count'] == 0


# ============================================================================
# SECTION 3: SHIFT DETECTION TESTS
# ============================================================================

@pytest.mark.asyncio
async def test_detect_emotional_shifts(emotion_service, mock_emotion_repo):
    """Test detecting emotional shifts."""
    now = datetime.now()

    # Create emotions with significant shift
    emotions = [
        Emotion(
            emotion=EmotionType.JOY,
            intensity=9,
            felt_at=now - timedelta(hours=2),
            context="Happy moment"
        ),
        Emotion(
            emotion=EmotionType.SADNESS,
            intensity=4,
            felt_at=now - timedelta(hours=1),
            context="Sad moment"
        ),
        Emotion(
            emotion=EmotionType.ANXIETY,
            intensity=7,
            felt_at=now,
            context="Anxious moment"
        )
    ]

    mock_emotion_repo.get_recent_emotions.return_value = emotions

    shifts = await emotion_service.detect_emotional_shifts(window_hours=24)

    assert len(shifts) >= 2  # At least 2 shifts detected
    assert 'shift_type' in shifts[0]
    assert 'intensity_change' in shifts[0]
    assert 'significance' in shifts[0]


# ============================================================================
# SECTION 4: TREND ANALYSIS TESTS
# ============================================================================

@pytest.mark.asyncio
async def test_analyze_emotional_trends_improving(emotion_service, mock_emotion_repo):
    """Test trend analysis showing improvement."""
    now = datetime.now()

    # Create trend: low intensity first half, high intensity second half
    emotions = []
    for i in range(20):
        intensity = 5 if i < 10 else 9  # Improvement
        emotions.append(Emotion(
            emotion=EmotionType.JOY,
            intensity=intensity,
            felt_at=now - timedelta(days=20 - i),
            context=f"Day {i}"
        ))

    mock_emotion_repo.get_recent_emotions.return_value = emotions

    trends = await emotion_service.analyze_emotional_trends(lookback_days=30)

    assert trends['trend'] == 'improving'
    assert trends['overall_change'] > 0
    assert trends['second_period_avg'] > trends['first_period_avg']


@pytest.mark.asyncio
async def test_analyze_emotional_trends_declining(emotion_service, mock_emotion_repo):
    """Test trend analysis showing decline."""
    now = datetime.now()

    # Create trend: high intensity first half, low intensity second half
    emotions = []
    for i in range(20):
        intensity = 9 if i < 10 else 5  # Decline
        emotions.append(Emotion(
            emotion=EmotionType.JOY,
            intensity=intensity,
            felt_at=now - timedelta(days=20 - i),
            context=f"Day {i}"
        ))

    mock_emotion_repo.get_recent_emotions.return_value = emotions

    trends = await emotion_service.analyze_emotional_trends(lookback_days=30)

    assert trends['trend'] == 'declining'
    assert trends['overall_change'] < 0


@pytest.mark.asyncio
async def test_predict_emotional_needs(emotion_service, mock_emotion_repo, sample_emotions):
    """Test predicting emotional needs."""
    mock_emotion_repo.get_recent_emotions.return_value = sample_emotions

    needs = await emotion_service.predict_emotional_needs()

    assert isinstance(needs, list)
    assert len(needs) > 0
    # Common needs
    possible_needs = [
        'need_rest', 'need_encouragement', 'need_support',
        'need_reassurance', 'need_companionship', 'need_stability',
        'doing_well', 'unable_to_predict'
    ]
    assert all(need in possible_needs for need in needs)


# ============================================================================
# SECTION 5: REPORTING TESTS
# ============================================================================

@pytest.mark.asyncio
async def test_get_emotion_timeline(emotion_service, mock_emotion_repo, sample_emotions):
    """Test getting emotion timeline."""
    start_date = datetime.now() - timedelta(days=30)
    end_date = datetime.now()

    mock_emotion_repo.get_recent_emotions.return_value = sample_emotions

    timeline = await emotion_service.get_emotion_timeline(
        start_date=start_date,
        end_date=end_date
    )

    assert isinstance(timeline, list)
    assert len(timeline) > 0
    assert 'timestamp' in timeline[0]
    assert 'emotion' in timeline[0]
    assert 'intensity' in timeline[0]
    assert 'context_preview' in timeline[0]


@pytest.mark.asyncio
async def test_generate_pattern_report(emotion_service, mock_emotion_repo, sample_emotions):
    """Test generating comprehensive pattern report."""
    mock_emotion_repo.get_recent_emotions.return_value = sample_emotions

    report = await emotion_service.generate_pattern_report(lookback_days=30)

    assert 'summary' in report
    assert report['summary']['period_days'] == 30
    assert report['summary']['emotions_analyzed'] == len(sample_emotions)

    assert 'patterns' in report
    assert 'cycles' in report
    assert 'trends' in report
    assert 'dominant_emotions' in report
    assert 'emotional_needs' in report
    assert 'insights' in report
    assert 'recommendations' in report
    assert 'generated_at' in report


# ============================================================================
# SECTION 6: HELPER METHOD TESTS
# ============================================================================

def test_calculate_pattern_strength(emotion_service):
    """Test pattern strength calculation."""
    # High frequency, high consistency, recent
    strength1 = emotion_service._calculate_pattern_strength(
        frequency=15,
        consistency=0.9,
        recency=0.9
    )
    assert 0.8 <= strength1 <= 1.0

    # Low frequency, low consistency, old
    strength2 = emotion_service._calculate_pattern_strength(
        frequency=2,
        consistency=0.3,
        recency=0.1
    )
    assert 0.0 <= strength2 <= 0.4


def test_detect_anomalies(emotion_service, sample_emotions):
    """Test anomaly detection."""
    # Add an extreme outlier
    outlier = Emotion(
        emotion=EmotionType.ANXIETY,
        intensity=10,  # Much higher than average
        context="Extreme anxiety"
    )
    emotions_with_outlier = sample_emotions + [outlier]

    anomalies = emotion_service._detect_anomalies(emotions_with_outlier)

    # Should detect anomalies (though exact count depends on data)
    assert isinstance(anomalies, list)


def test_generate_mood_description(emotion_service):
    """Test mood description generation."""
    # Test joyful mood
    dominant = [('joy', 5, 8.5), ('gratitude', 3, 9.0)]
    description = emotion_service._generate_mood_description(
        dominant=dominant,
        valence='positive',
        avg_intensity=8.0
    )
    assert 'Joyful' in description or 'joy' in description.lower()
    assert 'intense' in description.lower()

    # Test anxious mood
    dominant = [('anxiety', 4, 7.0)]
    description = emotion_service._generate_mood_description(
        dominant=dominant,
        valence='negative',
        avg_intensity=6.5
    )
    assert 'anxious' in description.lower()


# ============================================================================
# SECTION 7: ERROR HANDLING TESTS
# ============================================================================

@pytest.mark.asyncio
async def test_identify_patterns_error_handling(emotion_service, mock_emotion_repo):
    """Test error handling in pattern identification."""
    mock_emotion_repo.get_recent_emotions.side_effect = Exception("Database error")

    with pytest.raises(Exception) as exc_info:
        await emotion_service.identify_patterns(lookback_days=30)

    assert "Database error" in str(exc_info.value)


@pytest.mark.asyncio
async def test_get_current_emotional_state_error_handling(emotion_service, mock_emotion_repo):
    """Test error handling in getting current state."""
    mock_emotion_repo.get_recent_emotions.side_effect = Exception("Connection error")

    state = await emotion_service.get_current_emotional_state()

    assert state['status'] == 'error'
    assert 'error' in state
    assert 'Connection error' in state['error']


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
