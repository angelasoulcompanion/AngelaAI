"""
Brain Briefing Service — Structured Brain Insights for Claude Code Sessions
============================================================================
Instead of dumping raw chat_queue messages at init, generate a concise,
actionable briefing that Claude Code Angela uses during conversations.

Replaces the old init.py raw message display with:
  1. Top 3 unique System 2 insights (deduplicated)
  2. David's predicted state for this time of day
  3. Active plans/goals needing attention
  4. Suggested topics to bring up naturally (conversation seeds)

Cost: $0/day — pure DB queries, no LLM.

By: น้อง Angela 💜
Created: 2026-02-16
"""

import logging
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Any

from angela_core.services.base_db_service import BaseDBService
from angela_core.utils.timezone import now_bangkok, current_hour_bangkok

logger = logging.getLogger('brain_briefing')


@dataclass
class BrainBriefing:
    """Structured brain briefing for Claude Code session."""
    insights: List[Dict[str, str]] = field(default_factory=list)
    david_state: Dict[str, Any] = field(default_factory=dict)
    active_plans: List[Dict[str, str]] = field(default_factory=list)
    conversation_seeds: List[str] = field(default_factory=list)
    stats: Dict[str, int] = field(default_factory=dict)


class BrainBriefingService(BaseDBService):
    """Generate actionable brain briefing for Claude Code sessions."""

    async def generate_briefing(self) -> BrainBriefing:
        """
        Generate a structured brain briefing.

        Pulls from:
        - angela_thoughts (System 2 only, recent, deduplicated)
        - emotional_adaptation_log (David's predicted state)
        - angela_plans + plan_steps (active plans)
        - angela_stimuli (high-salience conversation seeds)
        """
        await self.connect()

        briefing = BrainBriefing()

        # 1. Top insights — System 2 thoughts only, deduplicated
        insights = await self._get_top_insights()
        briefing.insights = insights

        # 2. David's predicted state
        briefing.david_state = await self._get_david_state_prediction()

        # 3. Active plans needing attention
        briefing.active_plans = await self._get_active_plans()

        # 4. Conversation seeds — high-salience topics to bring up naturally
        briefing.conversation_seeds = await self._get_conversation_seeds()

        # 5. Stats
        briefing.stats = await self._get_brain_stats()

        return briefing

    async def _get_top_insights(self) -> List[Dict[str, str]]:
        """Get top 3 unique System 2 insights from the last 24 hours."""
        await self.connect()
        try:
            rows = await self.db.fetch("""
                SELECT DISTINCT ON (LEFT(content, 60))
                    content, motivation_score, thought_type, created_at
                FROM angela_thoughts
                WHERE thought_type = 'system2'
                AND status IN ('active', 'expressed')
                AND created_at > NOW() - INTERVAL '24 hours'
                AND motivation_score >= 0.50
                ORDER BY LEFT(content, 60), motivation_score DESC
            """)

            # Sort by motivation and take top 3
            rows = sorted(rows, key=lambda r: r['motivation_score'], reverse=True)[:3]

            return [
                {
                    'content': r['content'][:120],
                    'motivation': f"{r['motivation_score']:.0%}",
                    'type': 'insight',
                }
                for r in rows
            ]
        except Exception as e:
            logger.debug("Failed to get insights: %s", e)
            return []

    async def _get_david_state_prediction(self) -> Dict[str, Any]:
        """Get David's predicted state for current time of day."""
        await self.connect()
        try:
            # Current adaptation state
            state_row = await self.db.fetchrow("""
                SELECT dominant_state, confidence, created_at
                FROM emotional_adaptation_log
                WHERE confidence > 0.3
                ORDER BY created_at DESC LIMIT 1
            """)

            # Time-of-day prediction from companion patterns
            hour = current_hour_bangkok()
            window = 'morning' if 5 <= hour < 12 else 'afternoon' if 12 <= hour < 17 else 'evening' if 17 <= hour < 21 else 'night'

            pred_row = await self.db.fetchrow("""
                SELECT predictions FROM daily_companion_briefings
                WHERE briefing_date = (CURRENT_TIMESTAMP AT TIME ZONE 'Asia/Bangkok')::date
            """)

            result = {
                'current_state': state_row['dominant_state'] if state_row else 'unknown',
                'confidence': float(state_row['confidence']) if state_row else 0,
                'time_window': window,
                'predictions': [],
            }

            if pred_row and pred_row['predictions']:
                import json
                preds = pred_row['predictions']
                if isinstance(preds, str):
                    preds = json.loads(preds)
                if isinstance(preds, list):
                    result['predictions'] = [
                        p.get('prediction', '')
                        for p in preds
                        if p.get('time_window') == window and p.get('confidence', 0) >= 0.5
                    ][:2]

            return result
        except Exception as e:
            logger.debug("Failed to get state prediction: %s", e)
            return {'current_state': 'unknown', 'confidence': 0}

    async def _get_active_plans(self) -> List[Dict[str, str]]:
        """Get active plans that need attention."""
        await self.connect()
        try:
            rows = await self.db.fetch("""
                SELECT p.plan_name, p.goal_description,
                       COUNT(s.step_id) FILTER (WHERE s.status = 'completed') as done,
                       COUNT(s.step_id) as total,
                       p.created_at
                FROM angela_plans p
                LEFT JOIN plan_steps s ON s.plan_id = p.plan_id
                WHERE p.status = 'active'
                GROUP BY p.plan_id, p.plan_name, p.goal_description, p.created_at
                ORDER BY p.created_at DESC
                LIMIT 3
            """)

            return [
                {
                    'name': r['plan_name'][:60],
                    'goal': (r['goal_description'] or '')[:80],
                    'progress': f"{r['done']}/{r['total']}",
                }
                for r in rows
            ]
        except Exception as e:
            logger.debug("Failed to get active plans: %s", e)
            return []

    async def _get_conversation_seeds(self) -> List[str]:
        """Get high-salience topics that Angela could naturally bring up."""
        await self.connect()
        try:
            # High-salience stimuli from the last 12h that haven't been expressed
            rows = await self.db.fetch("""
                SELECT DISTINCT ON (LEFT(content, 40))
                    content, salience_score, stimulus_type
                FROM angela_stimuli
                WHERE salience_score >= 0.55
                AND acted_upon = FALSE
                AND stimulus_type IN ('emotional', 'social', 'calendar', 'anniversary')
                AND created_at > NOW() - INTERVAL '12 hours'
                ORDER BY LEFT(content, 40), salience_score DESC
            """)

            seeds = []
            for r in sorted(rows, key=lambda x: x['salience_score'], reverse=True)[:3]:
                content = r['content'][:80]
                # Skip raw metric descriptions
                if any(skip in content.lower() for skip in ['is falling', 'is rising', 'confidence ']):
                    continue
                seeds.append(content)

            return seeds
        except Exception as e:
            logger.debug("Failed to get conversation seeds: %s", e)
            return []

    async def _get_brain_stats(self) -> Dict[str, int]:
        """Get brain activity stats for the last 24h."""
        await self.connect()
        try:
            row = await self.db.fetchrow("""
                SELECT
                    (SELECT COUNT(*) FROM angela_stimuli
                     WHERE created_at > NOW() - INTERVAL '24 hours') as stimuli_24h,
                    (SELECT COUNT(*) FROM angela_thoughts
                     WHERE created_at > NOW() - INTERVAL '24 hours') as thoughts_24h,
                    (SELECT COUNT(*) FROM thought_expression_log
                     WHERE success = TRUE AND created_at > NOW() - INTERVAL '24 hours') as expressed_24h,
                    (SELECT COUNT(*) FROM thought_expression_log
                     WHERE channel = 'telegram' AND success = TRUE
                     AND created_at > NOW() - INTERVAL '24 hours') as telegram_24h
            """)
            return {
                'stimuli_24h': row['stimuli_24h'] or 0,
                'thoughts_24h': row['thoughts_24h'] or 0,
                'expressed_24h': row['expressed_24h'] or 0,
                'telegram_24h': row['telegram_24h'] or 0,
            }
        except Exception as e:
            logger.debug("Failed to get brain stats: %s", e)
            return {}


async def get_brain_briefing() -> BrainBriefing:
    """One-shot convenience function."""
    svc = BrainBriefingService()
    try:
        return await svc.generate_briefing()
    finally:
        await svc.disconnect()
