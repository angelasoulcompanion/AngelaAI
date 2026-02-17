"""
Heartbeat Handlers — Maps task names to handler functions.
===========================================================
Bridges HEARTBEAT.md task names to the actual daemon mixin methods.

This mapping allows HeartbeatScheduler to dispatch tasks by name
without knowing the implementation details.

By: Angela 💜
Created: 2026-02-17
"""

import logging
from typing import Any, Callable, Coroutine, Dict, Optional

logger = logging.getLogger(__name__)


def build_handler_map(daemon) -> Dict[str, Callable]:
    """
    Build a mapping from task names (as in HEARTBEAT.md) to daemon methods.

    Args:
        daemon: ConsciousnessDaemon instance (has all mixin methods)

    Returns:
        Dict mapping task_name → async handler function
    """
    return {
        # ── Every 30 minutes ──
        'proactive_care': daemon.run_proactive_care,
        'salience_scan': daemon.run_salience_scan,
        'thought_generation': daemon.run_thought_generation,
        'plan_execution': daemon.run_plan_execution,

        # ── Every 2 hours ──
        'theory_of_mind': daemon.run_theory_of_mind,
        'meta_awareness': daemon.run_meta_awareness,

        # ── Every 4 hours ──
        'predictions': daemon.run_predictions,
        'companion_predictions': daemon.run_companion_predictions,
        'evolution_cycle': daemon.run_evolution_cycle,
        'memory_consolidation': daemon.run_memory_consolidation,
        'brain_reflection': daemon.run_brain_reflection,
        'plan_generation': daemon.run_plan_generation,
        'rlhf_cycle': daemon.run_rlhf_cycle,
        'unified_conversation_analysis': daemon.run_unified_conversation_analysis,

        # ── Sequential (every cycle) ──
        'thought_expression': daemon.run_thought_expression,
        'brain_comparison': daemon.run_brain_comparison,
        'telegram_effectiveness': daemon.run_telegram_effectiveness,
        'proactive_actions': daemon.run_proactive_actions,
        'auto_classify_responses': daemon.run_auto_classify_responses,

        # ── Daily ──
        'self_validation': getattr(daemon, 'run_self_validation', _noop),
        'self_reflection': daemon.run_self_reflection,
        'daily_news': getattr(daemon, 'run_daily_news', _noop),
        'keep_sync': daemon.run_keep_sync,
        'session_coverage_audit': daemon.run_session_coverage_audit,
        'identity_check': daemon.run_identity_check,

        # ── Weekly ──
        'privacy_audit': getattr(daemon, 'run_privacy_audit', _noop),
    }


async def _noop() -> Dict[str, Any]:
    """No-op handler for tasks not yet implemented."""
    return {'success': True, 'skipped': True, 'reason': 'not_implemented'}
