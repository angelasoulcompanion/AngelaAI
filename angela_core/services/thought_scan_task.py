"""
Thought Scan Task — Daemon Integration
========================================
Wrapper for running thought cycles from the consciousness daemon.

Called every 30 minutes after salience scan.
0-1 Ollama calls, ~3-5 seconds per cycle.

By: น้อง Angela 💜
Created: 2026-02-15
"""

import logging
from typing import Dict, Any

from angela_core.services.thought_engine import ThoughtEngine

logger = logging.getLogger('consciousness_daemon')


async def run_thought_cycle() -> Dict[str, Any]:
    """
    Called by consciousness_daemon every 30 minutes.
    Creates own DB connection — safe for asyncio.gather().

    Bug fix (2026-02-26): Now updates MetacognitiveStateManager after cycle.
    Previously metacognitive state stayed at defaults because only
    CognitiveEngine (CLI) called update methods, not the daemon.
    """
    engine = ThoughtEngine()  # Creates own DB
    try:
        result = await engine.run_thought_cycle()

        logger.info(
            "💭 Thought cycle: %d thoughts (S1:%d + S2:%d), "
            "%d high-motivation, %d decayed, %.0fms",
            result.total_thoughts, result.system1_count, result.system2_count,
            result.high_motivation_count, result.decayed_count,
            result.cycle_duration_ms,
        )

        # Bug fix: Update metacognitive state from thought results
        try:
            from angela_core.services.metacognitive_state import MetacognitiveStateManager
            meta = MetacognitiveStateManager()
            meta.update_from_thought_cycle(
                system1_count=result.system1_count,
                system2_count=result.system2_count,
                high_motivation_count=result.high_motivation_count,
            )
        except Exception as e:
            logger.debug("Metacognitive update after thought cycle failed: %s", e)

        return {
            'success': True,
            'total_thoughts': result.total_thoughts,
            'system1_count': result.system1_count,
            'system2_count': result.system2_count,
            'high_motivation_count': result.high_motivation_count,
            'stimuli_processed': result.stimuli_processed,
            'decayed_count': result.decayed_count,
            'cycle_duration_ms': result.cycle_duration_ms,
        }
    except Exception as e:
        logger.error("❌ Thought cycle failed: %s", e)
        return {'success': False, 'error': str(e)}
    finally:
        await engine.disconnect()
