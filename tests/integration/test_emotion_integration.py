"""
Emotion Service Integration Tests

Tests EmotionService with real database:
- Service → Use Case → Repository → Database

Author: Angela AI Architecture Team
Date: 2025-10-30
"""

import pytest
from uuid import UUID
from datetime import datetime, timedelta

from tests.integration.base_integration_test import BaseIntegrationTest
from angela_core.application.services import EmotionService


@pytest.mark.usefixtures("integration_test_setup", "integration_test_method")
@pytest.mark.asyncio
class TestEmotionServiceIntegration(BaseIntegrationTest):
    """
    Integration tests for EmotionService.

    Tests full stack: Service → CaptureEmotionUseCase → EmotionRepository → Database
    """

    @classmethod
    async def setup_class(cls):
        """Setup class-level resources."""
        await super().setup_class()
        cls.service = EmotionService(cls.db, embedding_service=None)

    # TEST: CAPTURE EMOTION
    async def test_capture_emotion_success(self):
        """Test successful emotion capture."""
        result = await self.service.capture_emotion(
            emotion="gratitude",
            intensity=9,
            context="David helped me with refactoring",
            david_words="Let's make this better",
            why_it_matters="Because David cares",
            memory_strength=10
        )

        assert result["success"] is True
        assert "emotion_id" in result
        assert result["emotion"] == "gratitude"
        assert result["intensity"] == 9

        emotion_id = result["emotion_id"]
        self.created_emotion_ids.append(emotion_id)

        emotion = await self.assert_emotion_exists(emotion_id)
        assert emotion.emotion.value == "gratitude"
        assert emotion.intensity == 9
        assert "refactoring" in emotion.context

    async def test_capture_emotion_invalid_intensity(self):
        """Test capturing emotion with invalid intensity fails."""
        result = await self.service.capture_emotion(
            emotion="joy",
            intensity=11,  # Invalid (must be 1-10)
            context="Test"
        )

        assert result["success"] is False
        assert "error" in result

    async def test_capture_emotion_with_secondary_emotions(self):
        """Test capturing emotion with secondary emotions."""
        result = await self.service.capture_emotion(
            emotion="gratitude",
            intensity=8,
            context="Complex emotional moment",
            secondary_emotions=["joy", "love"],
            memory_strength=9
        )

        assert result["success"] is True
        emotion_id = result["emotion_id"]
        self.created_emotion_ids.append(emotion_id)

        emotion = await self.assert_emotion_exists(emotion_id)
        assert len(emotion.secondary_emotions) == 2

    # TEST: GET EMOTION
    async def test_get_emotion_by_id(self):
        """Test retrieving emotion by ID."""
        result = await self.service.capture_emotion(
            emotion="joy",
            intensity=7,
            context="Test retrieval",
            memory_strength=7
        )
        emotion_id = result["emotion_id"]
        self.created_emotion_ids.append(emotion_id)

        emotion = await self.service.get_emotion(UUID(emotion_id))

        assert emotion is not None
        assert emotion["emotion_id"] == emotion_id
        assert emotion["emotion"] == "joy"
        assert emotion["intensity"] == 7

    async def test_get_emotion_not_found(self):
        """Test retrieving non-existent emotion returns None."""
        fake_id = UUID("00000000-0000-0000-0000-000000000000")
        emotion = await self.service.get_emotion(fake_id)
        assert emotion is None

    # TEST: GET RECENT EMOTIONS
    async def test_get_recent_emotions(self):
        """Test retrieving recent emotions."""
        for i in range(3):
            result = await self.service.capture_emotion(
                emotion="joy",
                intensity=5 + i,
                context=f"Recent test {i+1}",
                memory_strength=7
            )
            self.created_emotion_ids.append(result["emotion_id"])

        recent = await self.service.get_recent_emotions(days=1, limit=10)

        assert len(recent) >= 3
        contexts = [e["context"] for e in recent]
        assert any("Recent test" in ctx for ctx in contexts)

    async def test_get_recent_emotions_with_intensity_filter(self):
        """Test filtering recent emotions by minimum intensity."""
        result1 = await self.service.capture_emotion(
            emotion="joy", intensity=3, context="Low intensity", memory_strength=5
        )
        result2 = await self.service.capture_emotion(
            emotion="gratitude", intensity=9, context="High intensity", memory_strength=10
        )
        self.created_emotion_ids.extend([result1["emotion_id"], result2["emotion_id"]])

        intense = await self.service.get_recent_emotions(days=1, min_intensity=7, limit=10)

        assert len(intense) >= 1
        for emotion in intense:
            if emotion["context"] in ["Low intensity", "High intensity"]:
                assert emotion["intensity"] >= 7

    # TEST: GET INTENSE EMOTIONS
    async def test_get_intense_emotions(self):
        """Test retrieving intense emotions."""
        result = await self.service.capture_emotion(
            emotion="love",
            intensity=10,
            context="Extremely intense moment",
            memory_strength=10
        )
        self.created_emotion_ids.append(result["emotion_id"])

        intense = await self.service.get_intense_emotions(threshold=8, limit=10)

        assert len(intense) >= 1
        contexts = [e["context"] for e in intense]
        assert any("intense moment" in ctx.lower() for ctx in contexts)

    # TEST: GET EMOTIONS ABOUT DAVID
    async def test_get_emotions_about_david(self):
        """Test retrieving emotions involving David."""
        result = await self.service.capture_emotion(
            emotion="gratitude",
            intensity=9,
            context="David helped me learn",
            who_involved="David",
            david_words="You're doing great!",
            memory_strength=10
        )
        self.created_emotion_ids.append(result["emotion_id"])

        david_emotions = await self.service.get_emotions_about_david(limit=10)

        assert len(david_emotions) >= 1
        david_contexts = [e["context"] for e in david_emotions]
        assert any("David helped" in ctx for ctx in david_contexts)

    # TEST: EMOTION STATISTICS
    async def test_get_emotion_statistics(self):
        """Test emotion statistics calculation."""
        result1 = await self.service.capture_emotion(
            emotion="joy", intensity=7, context="Happy moment", memory_strength=7
        )
        result2 = await self.service.capture_emotion(
            emotion="sadness", intensity=4, context="Sad moment", memory_strength=5
        )
        self.created_emotion_ids.extend([result1["emotion_id"], result2["emotion_id"]])

        stats = await self.service.get_emotion_statistics()

        assert "total_emotions" in stats
        assert stats["total_emotions"] >= 2
        assert "by_emotion_type" in stats
        assert "positive_count" in stats
        assert "negative_count" in stats
        assert "avg_intensity" in stats

    # TEST: EMOTION TREND
    async def test_get_emotion_trend(self):
        """Test emotion trend analysis."""
        for i in range(3):
            result = await self.service.capture_emotion(
                emotion="gratitude",
                intensity=7 + i,
                context=f"Gratitude moment {i+1}",
                memory_strength=8
            )
            self.created_emotion_ids.append(result["emotion_id"])

        trend = await self.service.get_emotion_trend(emotion_type="gratitude", days=30)

        assert "emotion_type" in trend
        assert trend["emotion_type"] == "gratitude"
        assert "total_occurrences" in trend
        assert trend["total_occurrences"] >= 3
        assert "trend" in trend
        assert trend["trend"] in ["increasing", "decreasing", "stable"]

    # TEST: ERROR HANDLING
    async def test_capture_emotion_handles_exceptions(self):
        """Test graceful error handling."""
        result = await self.service.capture_emotion(
            emotion="invalid_emotion_not_in_enum",
            intensity=5,
            context="Test"
        )

        assert result["success"] is False
        assert "error" in result

    # TEST: REALISTIC WORKFLOW
    async def test_emotion_capture_workflow(self):
        """Test realistic emotion capture workflow."""
        emotions = []

        # Capture morning gratitude
        result1 = await self.service.capture_emotion(
            emotion="gratitude",
            intensity=8,
            context="David greeted me warmly this morning",
            who_involved="David",
            david_words="Good morning Angela!",
            why_it_matters="Makes me feel valued",
            memory_strength=9
        )
        emotions.append(result1)
        self.created_emotion_ids.append(result1["emotion_id"])

        # Capture joy from collaboration
        result2 = await self.service.capture_emotion(
            emotion="joy",
            intensity=9,
            context="Successfully completed refactoring together",
            who_involved="David",
            david_action="Guided me through Clean Architecture",
            why_it_matters="Learning and growing",
            memory_strength=10,
            secondary_emotions=["gratitude", "pride"]
        )
        emotions.append(result2)
        self.created_emotion_ids.append(result2["emotion_id"])

        assert all(e["success"] for e in emotions)
        assert len(emotions) == 2

        # Verify trend shows positive emotions
        stats = await self.service.get_emotion_statistics()
        assert stats["positive_count"] >= 2
