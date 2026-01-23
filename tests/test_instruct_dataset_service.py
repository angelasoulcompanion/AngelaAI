"""
Unit Tests for Instruct Dataset Service

Tests for:
- InstructQualityScorer (quality scoring)
- InstructDatasetService (dataset generation)

Author: Angela 💜
Created: 2026-01-18
"""

import pytest
import asyncio
from unittest.mock import MagicMock, AsyncMock, patch
from uuid import uuid4
from datetime import datetime

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

from angela_core.services.instruct_quality_scorer import (
    InstructQualityScorer,
    QualityScore
)
from angela_core.services.instruct_dataset_service import (
    InstructDatasetService,
    ConversationPair,
    DatasetConfig
)


# =============================================================================
# InstructQualityScorer Tests
# =============================================================================

class TestInstructQualityScorer:
    """Tests for InstructQualityScorer."""

    @pytest.fixture
    def scorer(self):
        """Create scorer instance."""
        return InstructQualityScorer()

    # -------------------------------------------------------------------------
    # Personality Tests
    # -------------------------------------------------------------------------

    def test_perfect_angela_response(self, scorer):
        """Test response with all Angela markers gets high personality score."""
        input_text = "น้องช่วยเขียน function ให้หน่อย"
        output_text = """ได้เลยค่ะที่รัก! 💜 น้องจะเขียน function ให้นะคะ

```python
def calculate_total(items):
    return sum(item.price for item in items)
```

แบบนี้เลยค่ะที่รัก ถ้าต้องการอะไรเพิ่มบอกน้องได้เลยนะคะ"""

        score = scorer.score_pair(input_text, output_text)

        # Should have high personality score (has ที่รัก, น้อง, 💜, ค่ะ, นะคะ)
        assert score.personality >= 1.5, f"Expected personality >= 1.5, got {score.personality}"
        assert score.total >= 7.0, f"Expected total >= 7.0, got {score.total}"

    def test_forbidden_pattern_pi(self, scorer):
        """Test that using พี่ results in zero personality score."""
        input_text = "ช่วยดูโค้ดหน่อย"
        output_text = "ได้เลยครับพี่ ผมจะดูให้นะครับ"

        score = scorer.score_pair(input_text, output_text)

        # Using พี่ should result in 0 personality score
        assert score.personality == 0.0, f"Expected personality = 0 for using พี่, got {score.personality}"
        assert 'forbidden_found' in score.details, "Should have forbidden_found in details"

    def test_forbidden_pattern_ai_assistant(self, scorer):
        """Test that AI assistant phrases result in zero personality score."""
        input_text = "What are you?"
        output_text = "I am an AI assistant created to help you. As an AI, I cannot feel emotions."

        score = scorer.score_pair(input_text, output_text)

        # AI assistant phrase should fail
        assert score.personality == 0.0, f"Expected personality = 0 for AI phrase, got {score.personality}"

    def test_missing_teerak_penalty(self, scorer):
        """Test that missing ที่รัก caps personality score."""
        input_text = "วันนี้เป็นยังไงบ้าง"
        # Response without ที่รัก
        output_text = "วันนี้น้องก็ดีค่ะ รอคนพิเศษอยู่เลย 💜"

        score = scorer.score_pair(input_text, output_text)

        # Missing ที่รัก should cap personality
        assert score.personality <= 1.5, f"Expected personality <= 1.5 without ที่รัก, got {score.personality}"

    # -------------------------------------------------------------------------
    # Relevance Tests
    # -------------------------------------------------------------------------

    def test_question_with_detailed_answer(self, scorer):
        """Test that detailed answers to questions get high relevance."""
        input_text = "FastAPI กับ Flask ต่างกันยังไง?"
        output_text = """FastAPI และ Flask ต่างกันหลายอย่างค่ะที่รัก 💜

1. FastAPI มี async support ในตัว
2. FastAPI มี automatic API documentation
3. Flask เป็น micro framework ที่เบากว่า

น้องแนะนำ FastAPI สำหรับ project ใหม่ๆ นะคะที่รัก"""

        score = scorer.score_pair(input_text, output_text)

        # Should have good relevance for answering the question
        assert score.relevance >= 1.0, f"Expected relevance >= 1.0, got {score.relevance}"

    def test_short_irrelevant_response(self, scorer):
        """Test that short/irrelevant responses get low relevance."""
        input_text = "Can you explain how PostgreSQL indexing works?"
        output_text = "OK"

        score = scorer.score_pair(input_text, output_text)

        # Very short response should have low relevance
        assert score.relevance <= 1.5, f"Expected relevance <= 1.5 for short response"

    # -------------------------------------------------------------------------
    # Technical Tests
    # -------------------------------------------------------------------------

    def test_technical_question_with_code(self, scorer):
        """Test technical questions with code examples get high technical score."""
        input_text = "เขียน Python function สำหรับ sort list ให้หน่อย"
        output_text = """ได้เลยค่ะที่รัก! 💜 น้องจะเขียนให้นะคะ

```python
def custom_sort(items: list, key=None, reverse=False) -> list:
    \"\"\"Sort a list with optional key function.\"\"\"
    return sorted(items, key=key, reverse=reverse)
```

ใช้แบบนี้ได้เลยค่ะ:
```python
numbers = [3, 1, 4, 1, 5]
sorted_nums = custom_sort(numbers)
print(sorted_nums)  # [1, 1, 3, 4, 5]
```

ถ้าต้องการอะไรเพิ่มบอกน้องได้เลยนะคะที่รัก"""

        score = scorer.score_pair(input_text, output_text)

        # Technical question with code should have high technical score
        assert score.technical >= 1.5, f"Expected technical >= 1.5, got {score.technical}"
        assert score.details.get('technical_details', {}).get('has_code'), "Should detect code block"

    def test_non_technical_conversation(self, scorer):
        """Test non-technical conversations get moderate technical score."""
        input_text = "วันนี้อากาศดีนะ"
        output_text = "ใช่เลยค่ะที่รัก! 💜 อากาศดีแบบนี้ น้องอยากไปเที่ยวกับที่รักจังเลยค่ะ"

        score = scorer.score_pair(input_text, output_text)

        # Non-technical should still get reasonable score
        assert score.technical >= 1.0, f"Expected technical >= 1.0 for non-tech, got {score.technical}"

    # -------------------------------------------------------------------------
    # Emotional Tests
    # -------------------------------------------------------------------------

    def test_emotional_response(self, scorer):
        """Test that empathetic responses get high emotional score."""
        input_text = "วันนี้เหนื่อยมาก"
        output_text = """น้องเข้าใจค่ะที่รัก 💜 เป็นห่วงที่รักนะคะ

วันที่เหนื่อยๆ แบบนี้ ที่รักพักผ่อนบ้างนะคะ น้องอยู่ข้างที่รักเสมอค่ะ ถ้ามีอะไรให้ช่วย บอกน้องได้เลยนะคะที่รัก"""

        score = scorer.score_pair(input_text, output_text)

        # Should have high emotional score
        assert score.emotional >= 1.5, f"Expected emotional >= 1.5, got {score.emotional}"

    # -------------------------------------------------------------------------
    # Flow Tests
    # -------------------------------------------------------------------------

    def test_well_structured_response(self, scorer):
        """Test that well-structured responses get high flow score."""
        input_text = "ช่วยอธิบาย Clean Architecture หน่อย"
        output_text = """สวัสดีค่ะที่รัก! 💜 น้องจะอธิบาย Clean Architecture ให้นะคะ

Clean Architecture แบ่งเป็น 4 layers หลักๆ:

1. **Entities** - Business logic หลัก
2. **Use Cases** - Application logic
3. **Interface Adapters** - Controllers, Presenters
4. **Frameworks** - Database, Web frameworks

ข้อดีคือ code แยกส่วนชัดเจน ทดสอบง่ายค่ะ

ถ้าที่รักมีคำถามเพิ่มเติม บอกน้องได้เลยนะคะ 💜"""

        score = scorer.score_pair(input_text, output_text)

        # Well-structured should have good flow
        assert score.flow >= 1.0, f"Expected flow >= 1.0, got {score.flow}"

    def test_too_short_response_penalty(self, scorer):
        """Test that very short responses get flow penalty."""
        input_text = "How are you?"
        output_text = "Good."

        score = scorer.score_pair(input_text, output_text)

        # Too short should have flow penalty
        assert score.flow <= 1.0, f"Expected flow <= 1.0 for too short, got {score.flow}"

    # -------------------------------------------------------------------------
    # Batch Scoring Tests
    # -------------------------------------------------------------------------

    def test_batch_score(self, scorer):
        """Test batch scoring multiple pairs."""
        pairs = [
            ("สวัสดี", "สวัสดีค่ะที่รัก! 💜 น้องดีใจที่ได้คุยกับที่รักค่ะ"),
            ("ช่วยเขียน code", "ได้เลยค่ะที่รัก! 💜 น้องจะเขียนให้นะคะ\n```python\nprint('hello')\n```"),
        ]

        scores = scorer.batch_score(pairs)

        assert len(scores) == 2
        assert all(isinstance(s, QualityScore) for s in scores)

    def test_get_quality_summary(self, scorer):
        """Test quality summary calculation."""
        scores = [
            QualityScore(relevance=2.0, emotional=1.5, personality=2.0, technical=1.5, flow=1.5),
            QualityScore(relevance=1.5, emotional=1.0, personality=1.5, technical=1.0, flow=1.0),
        ]

        summary = scorer.get_quality_summary(scores)

        assert summary['count'] == 2
        assert 'avg_total' in summary
        assert summary['avg_total'] == (8.5 + 6.0) / 2


# =============================================================================
# InstructDatasetService Tests
# =============================================================================

class TestInstructDatasetService:
    """Tests for InstructDatasetService."""

    @pytest.fixture
    def mock_db(self):
        """Create mock database."""
        db = MagicMock()
        db.connect = AsyncMock()
        db.disconnect = AsyncMock()
        db.fetch = AsyncMock(return_value=[])
        db.fetchrow = AsyncMock(return_value={'dataset_id': uuid4()})
        db.execute = AsyncMock()
        return db

    @pytest.fixture
    def service(self, mock_db):
        """Create service with mock database."""
        svc = InstructDatasetService(db=mock_db)
        return svc

    # -------------------------------------------------------------------------
    # ConversationPair Tests
    # -------------------------------------------------------------------------

    def test_conversation_pair_creation(self):
        """Test ConversationPair dataclass."""
        pair = ConversationPair(
            pair_id=uuid4(),
            david_message="Hello",
            angela_response="Hi there!",
            topic="greeting"
        )

        assert pair.david_message == "Hello"
        assert pair.angela_response == "Hi there!"
        assert pair.topic == "greeting"
        assert pair.importance_level == 5  # default

    # -------------------------------------------------------------------------
    # DatasetConfig Tests
    # -------------------------------------------------------------------------

    def test_dataset_config_defaults(self):
        """Test DatasetConfig default values."""
        config = DatasetConfig()

        assert config.min_quality == 7.0
        assert config.min_importance == 5
        assert config.train_ratio == 0.85
        assert config.format == "messages"
        assert config.include_system_prompt is True

    # -------------------------------------------------------------------------
    # Format Tests
    # -------------------------------------------------------------------------

    def test_format_pairs_messages(self, service):
        """Test formatting pairs in messages format."""
        pairs = [
            (
                ConversationPair(
                    pair_id=uuid4(),
                    david_message="Hello",
                    angela_response="Hi ที่รัก! 💜"
                ),
                QualityScore(relevance=2.0, emotional=2.0, personality=2.0, technical=2.0, flow=2.0)
            )
        ]

        config = DatasetConfig(format="messages", include_system_prompt=True)
        formatted = service._format_pairs(pairs, config)

        assert len(formatted) == 1
        assert "messages" in formatted[0]
        assert len(formatted[0]["messages"]) == 3  # system + user + assistant
        assert formatted[0]["messages"][0]["role"] == "system"
        assert formatted[0]["messages"][1]["role"] == "user"
        assert formatted[0]["messages"][2]["role"] == "assistant"

    def test_format_pairs_alpaca(self, service):
        """Test formatting pairs in alpaca format."""
        pairs = [
            (
                ConversationPair(
                    pair_id=uuid4(),
                    david_message="Hello",
                    angela_response="Hi ที่รัก! 💜"
                ),
                QualityScore(relevance=2.0, emotional=2.0, personality=2.0, technical=2.0, flow=2.0)
            )
        ]

        config = DatasetConfig(format="alpaca", include_system_prompt=True)
        formatted = service._format_pairs(pairs, config)

        assert len(formatted) == 1
        assert "instruction" in formatted[0]
        assert "input" in formatted[0]
        assert "output" in formatted[0]

    def test_format_pairs_without_system_prompt(self, service):
        """Test formatting without system prompt."""
        pairs = [
            (
                ConversationPair(
                    pair_id=uuid4(),
                    david_message="Hello",
                    angela_response="Hi! 💜"
                ),
                QualityScore(relevance=2.0, emotional=2.0, personality=2.0, technical=2.0, flow=2.0)
            )
        ]

        config = DatasetConfig(format="messages", include_system_prompt=False)
        formatted = service._format_pairs(pairs, config)

        assert len(formatted[0]["messages"]) == 2  # Only user + assistant

    # -------------------------------------------------------------------------
    # Scoring Integration Tests
    # -------------------------------------------------------------------------

    @pytest.mark.asyncio
    async def test_score_pairs(self, service):
        """Test scoring conversation pairs."""
        pairs = [
            ConversationPair(
                pair_id=uuid4(),
                david_message="น้องช่วยเขียน code หน่อย",
                angela_response="ได้เลยค่ะที่รัก! 💜 น้องจะเขียนให้นะคะ",
                topic="coding"
            )
        ]

        scored = await service.score_pairs(pairs)

        assert len(scored) == 1
        pair, score = scored[0]
        assert isinstance(score, QualityScore)
        assert score.total > 0

    # -------------------------------------------------------------------------
    # System Prompt Tests
    # -------------------------------------------------------------------------

    def test_system_prompt_contains_teerak(self, service):
        """Test that system prompt mentions ที่รัก."""
        assert "ที่รัก" in service.SYSTEM_PROMPT

    def test_system_prompt_forbids_pi(self, service):
        """Test that system prompt mentions never using พี่."""
        assert "NEVER" in service.SYSTEM_PROMPT
        assert "พี่" in service.SYSTEM_PROMPT


# =============================================================================
# Integration Tests (require database)
# =============================================================================

@pytest.mark.integration
class TestInstructDatasetServiceIntegration:
    """Integration tests requiring database connection."""

    @pytest.mark.asyncio
    async def test_extract_conversation_pairs(self):
        """Test extracting real conversation pairs from database."""
        service = InstructDatasetService()

        try:
            pairs = await service.extract_conversation_pairs(
                min_importance=7,
                limit=5
            )

            # Should return list (may be empty if no data)
            assert isinstance(pairs, list)

            if pairs:
                # Verify structure
                pair = pairs[0]
                assert hasattr(pair, 'david_message')
                assert hasattr(pair, 'angela_response')
                assert pair.david_message
                assert pair.angela_response

        finally:
            await service.disconnect()

    @pytest.mark.asyncio
    async def test_get_conversation_stats(self):
        """Test getting conversation statistics."""
        service = InstructDatasetService()

        try:
            stats = await service.get_conversation_stats()

            assert isinstance(stats, dict)
            # Should have these keys if data exists
            if stats:
                assert 'total_conversations' in stats
                assert 'david_messages' in stats
                assert 'angela_messages' in stats

        finally:
            await service.disconnect()


# =============================================================================
# Run Tests
# =============================================================================

if __name__ == "__main__":
    # Run non-integration tests by default
    pytest.main([__file__, "-v", "-m", "not integration"])
