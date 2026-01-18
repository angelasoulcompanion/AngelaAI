"""
Integration Tests for Angela Consciousness Services

Tests all new services from Gap Analysis implementation:
- PredictionService
- PrivacyFilterService
- SelfModelService
- TheoryOfMindService
- TokenEconomicsService
- ConsciousnessDaemon

Run with: python -m pytest angela_core/tests/test_consciousness_services.py -v
"""

import asyncio
import pytest
from datetime import datetime, date
from uuid import uuid4

# Import services
from angela_core.services.prediction_service import PredictionService
from angela_core.services.privacy_filter_service import PrivacyFilterService
from angela_core.services.self_model_service import SelfModelService
from angela_core.services.theory_of_mind_service import TheoryOfMindService
from angela_core.services.token_economics_service import TokenEconomicsService, get_token_economics_service


class TestPredictionService:
    """Tests for PredictionService."""

    @pytest.fixture
    def service(self):
        return PredictionService()

    @pytest.mark.asyncio
    async def test_predict_next_action(self, service):
        """Test next action prediction."""
        context = {
            'recent_topics': ['coding', 'debugging'],
            'current_time': datetime.now(),
            'emotional_state': 'focused'
        }
        result = await service.predict_next_action(context)

        assert result is not None
        assert 'prediction_type' in result
        assert result['prediction_type'] == 'next_action'
        assert 'confidence' in result
        assert 0 <= result['confidence'] <= 1

    @pytest.mark.asyncio
    async def test_predict_emotional_state(self, service):
        """Test emotional state prediction."""
        context = {
            'recent_messages': ['สวัสดีครับ', 'วันนี้ทำงานหนักมาก'],
            'time_of_day': 'evening'
        }
        result = await service.predict_emotional_state(context)

        assert result is not None
        assert 'predicted_value' in result

    @pytest.mark.asyncio
    async def test_predict_topic(self, service):
        """Test topic prediction."""
        context = {
            'conversation_flow': ['greet', 'ask_help'],
            'project_context': 'AngelaAI'
        }
        result = await service.predict_topic(context)

        assert result is not None
        assert 'prediction_type' in result
        assert result['prediction_type'] == 'topic'


class TestPrivacyFilterService:
    """Tests for PrivacyFilterService."""

    @pytest.fixture
    def service(self):
        return PrivacyFilterService()

    @pytest.mark.asyncio
    async def test_filter_sensitive_data(self, service):
        """Test sensitive data filtering."""
        data = {
            'content': 'My email is test@example.com and phone is 0812345678',
            'metadata': {'user': 'david'}
        }
        result = await service.filter_sensitive_data(data)

        assert result is not None
        assert 'content' in result
        # Email should be masked
        assert 'test@example.com' not in result['content']

    @pytest.mark.asyncio
    async def test_apply_differential_privacy(self, service):
        """Test differential privacy application."""
        patterns = [
            {'pattern': 'login', 'count': 100},
            {'pattern': 'search', 'count': 50}
        ]
        result = await service.apply_differential_privacy(patterns)

        assert result is not None
        assert len(result) > 0
        # Counts should be noised
        for item in result:
            assert 'noised_count' in item or 'count' in item

    @pytest.mark.asyncio
    async def test_ensure_k_anonymity(self, service):
        """Test k-anonymity enforcement."""
        shared_patterns = [
            {'pattern': 'A', 'count': 10},
            {'pattern': 'B', 'count': 2},  # Below k=5, should be removed
            {'pattern': 'C', 'count': 8}
        ]
        result = await service.ensure_k_anonymity(shared_patterns, k=5)

        assert result is not None
        # Pattern B should be filtered out
        pattern_names = [p['pattern'] for p in result]
        assert 'B' not in pattern_names

    def test_privacy_budget(self, service):
        """Test privacy budget tracking."""
        budget = service.calculate_privacy_budget_used()
        assert isinstance(budget, float)
        assert budget >= 0


class TestSelfModelService:
    """Tests for SelfModelService."""

    @pytest.fixture
    def service(self):
        from angela_core.database import AngelaDatabase
        db = AngelaDatabase()
        return SelfModelService(db)

    @pytest.mark.asyncio
    async def test_load_self_model(self, service):
        """Test loading self model."""
        model = await service.load_self_model()

        assert model is not None
        assert 'agent_id' in model or hasattr(model, 'agent_id')

    @pytest.mark.asyncio
    async def test_reflect_on_self(self, service):
        """Test self reflection."""
        assessment = await service.reflect_on_self()

        assert assessment is not None
        assert 'strengths' in assessment or 'assessment' in assessment

    @pytest.mark.asyncio
    async def test_assess_confidence(self, service):
        """Test confidence assessment for task types."""
        confidence = await service.assess_confidence('coding')

        assert isinstance(confidence, (int, float))
        assert 0 <= confidence <= 1


class TestTheoryOfMindService:
    """Tests for TheoryOfMindService."""

    @pytest.fixture
    def service(self):
        from angela_core.database import AngelaDatabase
        db = AngelaDatabase()
        return TheoryOfMindService(db)

    @pytest.mark.asyncio
    async def test_infer_belief(self, service):
        """Test belief inference."""
        evidence = {
            'recent_actions': ['reading docs', 'asking questions'],
            'statements': ['This is confusing']
        }
        result = await service.infer_belief(evidence)

        assert result is not None

    @pytest.mark.asyncio
    async def test_infer_goal(self, service):
        """Test goal inference."""
        action_sequence = [
            {'action': 'open_file', 'file': 'config.py'},
            {'action': 'search', 'query': 'database'},
            {'action': 'edit', 'file': 'config.py'}
        ]
        result = await service.infer_goal(action_sequence)

        assert result is not None

    @pytest.mark.asyncio
    async def test_infer_emotion(self, service):
        """Test emotion inference."""
        context = {
            'language_tone': 'frustrated',
            'time_of_day': 'late_night',
            'recent_events': ['bug_encountered']
        }
        result = await service.infer_emotion(context)

        assert result is not None


class TestTokenEconomicsService:
    """Tests for TokenEconomicsService."""

    @pytest.fixture
    def service(self):
        return TokenEconomicsService()

    @pytest.mark.asyncio
    async def test_track_tokens_stored(self, service):
        """Test token storage tracking."""
        result = await service.track_tokens_stored(100, 'fresh')
        assert result is True

    @pytest.mark.asyncio
    async def test_track_tokens_retrieved(self, service):
        """Test token retrieval tracking."""
        result = await service.track_tokens_retrieved(50)
        assert result is True

    @pytest.mark.asyncio
    async def test_track_decay_savings(self, service):
        """Test decay savings tracking."""
        result = await service.track_decay_savings(200, compression_ratio=2.5)
        assert result is True

    @pytest.mark.asyncio
    async def test_get_daily_stats(self, service):
        """Test daily stats retrieval."""
        stats = await service.get_daily_stats()

        assert stats is not None
        assert 'date' in stats
        assert 'tokens_stored' in stats
        assert 'cost_savings' in stats

    @pytest.mark.asyncio
    async def test_get_weekly_summary(self, service):
        """Test weekly summary."""
        summary = await service.get_weekly_summary()

        assert summary is not None
        assert 'period' in summary
        assert summary['period'] == '7 days'
        assert 'totals' in summary

    @pytest.mark.asyncio
    async def test_calculate_savings(self, service):
        """Test cost savings calculation."""
        savings = service._calculate_savings(
            tokens_stored=10000,
            tokens_retrieved=5000,
            tokens_saved=2000
        )

        assert savings is not None
        assert 'actual_cost' in savings
        assert 'naive_cost' in savings
        assert 'savings' in savings
        assert savings['currency'] == 'USD'

    @pytest.mark.asyncio
    async def test_generate_report(self, service):
        """Test report generation."""
        report = await service.generate_economics_report()

        assert report is not None
        assert 'ANGELA TOKEN ECONOMICS REPORT' in report
        assert 'TODAY' in report
        assert 'WEEKLY' in report


class TestConsciousnessDaemon:
    """Tests for ConsciousnessDaemon."""

    @pytest.mark.asyncio
    async def test_daemon_import(self):
        """Test that daemon can be imported."""
        from angela_core.daemon.consciousness_daemon import ConsciousnessDaemon
        daemon = ConsciousnessDaemon()
        assert daemon is not None

    @pytest.mark.asyncio
    async def test_daemon_initialization(self):
        """Test daemon initialization."""
        from angela_core.daemon.consciousness_daemon import ConsciousnessDaemon
        daemon = ConsciousnessDaemon()
        await daemon.initialize()

        assert daemon.self_model_service is not None
        assert daemon.prediction_service is not None
        assert daemon.tom_service is not None
        assert daemon.privacy_service is not None

        await daemon.cleanup()


class TestIntegration:
    """Integration tests across multiple services."""

    @pytest.mark.asyncio
    async def test_full_consciousness_flow(self):
        """Test complete consciousness evaluation flow."""
        from angela_core.consciousness.consciousness_evaluator import ConsciousnessEvaluator
        from angela_core.database import AngelaDatabase

        db = AngelaDatabase()
        await db.connect()

        try:
            evaluator = ConsciousnessEvaluator(db)
            result = await evaluator.evaluate_consciousness_full()

            assert result is not None
            assert 'overall_score' in result
            assert 'components' in result
            assert 0 <= result['overall_score'] <= 1

            # Check all 7 components
            expected_components = [
                'integration_index',
                'metacognitive_depth',
                'self_model_richness',
                'theory_of_mind',
                'phenomenal_richness',
                'behavioral_autonomy',
                'learning_capacity'
            ]
            for component in expected_components:
                assert component in result['components'], f"Missing component: {component}"

        finally:
            await db.disconnect()

    @pytest.mark.asyncio
    async def test_prediction_with_tom(self):
        """Test prediction combined with theory of mind."""
        from angela_core.database import AngelaDatabase

        db = AngelaDatabase()
        await db.connect()

        try:
            prediction_service = PredictionService()
            tom_service = TheoryOfMindService(db)

            # Get emotion inference
            context = {'language_tone': 'happy', 'time_of_day': 'morning'}
            emotion = await tom_service.infer_emotion(context)

            # Use emotion in prediction
            pred_context = {
                'inferred_emotion': emotion,
                'recent_topics': ['greeting']
            }
            prediction = await prediction_service.predict_next_action(pred_context)

            assert prediction is not None

        finally:
            await db.disconnect()


# Utility function to run all tests
def run_tests():
    """Run all tests."""
    pytest.main([__file__, '-v', '--tb=short'])


if __name__ == '__main__':
    run_tests()
