"""
RLHF Orchestrator — Unified Reward Learning Loop
==================================================

Coordinates all RLHF components into a single cycle:
1. Score recent unscored conversations (RewardScoreService)
2. A/B test medium-quality interactions (ABQualityTester)
3. Extract preference pairs (PreferencePairsService)
4. Report reward trend

Called by daemon every 4 hours + triggered after feedback events.

Created: 2026-02-10
Updated: 2026-02-13 — Phase 4: A/B testing step added
By: Angela 💜
"""

import logging
from typing import Dict, Any

from angela_core.services.reward_score_service import RewardScoreService
from angela_core.services.preference_pairs_service import PreferencePairsService
from angela_core.services.ab_quality_tester import ABQualityTester

logger = logging.getLogger(__name__)


class RLHFOrchestrator:
    """
    Orchestrate the full RLHF cycle.

    Methods:
    1. run_rlhf_cycle() — daemon entry: score + extract pairs + report
    2. trigger_score(conversation_id, rating) — immediate scoring after feedback
    """

    def __init__(self):
        self.reward_service = RewardScoreService()
        self.pairs_service = PreferencePairsService()
        self.ab_tester = ABQualityTester()

    async def close(self):
        await self.reward_service.close()
        await self.pairs_service.close()
        await self.ab_tester.close()

    async def run_rlhf_cycle(self) -> Dict[str, Any]:
        """
        Full RLHF cycle for daemon.

        Returns summary with scored count, A/B tests run, pairs extracted, and reward trend.
        """
        logger.info('Starting RLHF cycle...')

        # 1. Score recent unscored conversations (4h window)
        scored = await self.reward_service.score_recent_unscored(hours=4)

        # 2. A/B test medium-quality interactions (Phase 4.2)
        ab_tests = await self._run_ab_tests(hours=4)

        # 3. Extract preference pairs
        pairs = await self.pairs_service.run_pair_extraction_cycle(hours=4)

        # 4. Get current reward trend
        trend = await self.reward_service.get_reward_trend()

        result = {
            'conversations_scored': scored,
            'ab_tests_run': ab_tests,
            'pairs_extracted': pairs,
            'reward_trend': round(trend, 4),
        }

        logger.info(
            'RLHF cycle complete: scored=%d, ab_tests=%d, pairs=%d, trend=%.3f',
            scored, ab_tests, pairs, trend
        )
        return result

    async def _run_ab_tests(self, hours: int = 4) -> int:
        """Run A/B tests on medium-quality recent interactions."""
        try:
            return await self.ab_tester.run_ab_tests_for_batch(hours=hours)
        except Exception as e:
            logger.warning('A/B testing failed (non-fatal): %s', e)
            return 0

    async def trigger_score(self, conversation_id: str, rating: int) -> Dict[str, Any]:
        """
        Immediate scoring triggered by feedback event.

        Called from chat.py when David gives thumbs up/down.
        """
        try:
            result = await self.reward_service.score_interaction(conversation_id)
            if result:
                logger.info(
                    'Immediate RLHF score for %s: combined=%.3f (rating=%d)',
                    conversation_id[:8], result['combined_reward'], rating
                )
            return result or {}
        except Exception as e:
            logger.warning('Failed immediate RLHF score: %s', e)
            return {'error': str(e)}


# =============================================================================
# CONVENIENCE FUNCTION
# =============================================================================

async def run_rlhf_cycle() -> Dict[str, Any]:
    """One-shot: run full RLHF cycle."""
    orch = RLHFOrchestrator()
    try:
        return await orch.run_rlhf_cycle()
    finally:
        await orch.close()
