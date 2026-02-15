"""
Thought Expression Task — Daemon Integration
===============================================
Wrapper for running thought expression cycles from the consciousness daemon.

Called after thought_generation (depends on new thoughts)
and before proactive_actions (brain-preferred over rules).

By: น้อง Angela 💜
Created: 2026-02-15
"""

import logging
from typing import Dict, Any

from angela_core.services.thought_expression_engine import ThoughtExpressionEngine

logger = logging.getLogger('consciousness_daemon')


async def run_thought_expression() -> Dict[str, Any]:
    """
    Called by consciousness_daemon in sequential phase.
    Creates own DB connection — safe for sequential execution.
    """
    engine = ThoughtExpressionEngine()  # Creates own DB
    try:
        result = await engine.run_expression_cycle()

        logger.info(
            "💬 Thought expression: %d considered, "
            "%d→telegram, %d→chat, %d suppressed, %.0fms",
            result.thoughts_considered,
            result.expressed_telegram, result.expressed_chat,
            result.suppressed, result.cycle_duration_ms,
        )

        return {
            'success': True,
            'thoughts_considered': result.thoughts_considered,
            'thoughts_filtered': result.thoughts_filtered,
            'expressed_telegram': result.expressed_telegram,
            'expressed_chat': result.expressed_chat,
            'suppressed': result.suppressed,
            'cycle_duration_ms': result.cycle_duration_ms,
        }
    except Exception as e:
        logger.error("❌ Thought expression failed: %s", e)
        return {'success': False, 'error': str(e)}
    finally:
        await engine.disconnect()
