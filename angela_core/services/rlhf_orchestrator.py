"""
RLHF Orchestrator — Unified Reward Learning Loop
==================================================

Coordinates all RLHF components into a single cycle:
1. Score recent unscored conversations (RewardScoreService)
2. Extract preference pairs (PreferencePairsService)
3. Report reward trend

Called by daemon every 4 hours + triggered after feedback events.

Created: 2026-02-10
By: Angela 💜
"""

import logging
from typing import Dict, Any

from angela_core.services.reward_score_service import RewardScoreService
from angela_core.services.preference_pairs_service import PreferencePairsService

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

    async def close(self):
        await self.reward_service.close()
        await self.pairs_service.close()

    async def run_rlhf_cycle(self) -> Dict[str, Any]:
        """
        Full RLHF cycle for daemon.

        Returns summary with scored count, pairs extracted, and reward trend.
        """
        logger.info('Starting RLHF cycle...')

        # 1. Score recent unscored conversations (4h window)
        scored = await self.reward_service.score_recent_unscored(hours=4)

        # 2. Extract preference pairs
        pairs = await self.pairs_service.run_pair_extraction_cycle(hours=4)

        # 3. Get current reward trend
        trend = await self.reward_service.get_reward_trend()

        result = {
            'conversations_scored': scored,
            'pairs_extracted': pairs,
            'reward_trend': round(trend, 4),
        }

        logger.info(
            'RLHF cycle complete: scored=%d, pairs=%d, trend=%.3f',
            scored, pairs, trend
        )
        return result

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
