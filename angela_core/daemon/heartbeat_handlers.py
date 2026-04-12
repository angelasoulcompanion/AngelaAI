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
        # ── Every 4 hours ──
        'rlhf_cycle': getattr(daemon, 'run_rlhf_cycle', _noop),
        'unified_conversation_analysis': getattr(daemon, 'run_unified_conversation_analysis', _noop),

        # ── Daily ──
        'keep_sync': getattr(daemon, 'run_keep_sync', _noop),
        'session_coverage_audit': getattr(daemon, 'run_session_coverage_audit', _noop),
    }


async def _noop() -> Dict[str, Any]:
    """No-op handler for tasks not yet implemented."""
    return {'success': True, 'skipped': True, 'reason': 'not_implemented'}
