"""
Reflection Task — Daemon Integration
======================================
Wrapper for running reflection cycles from the consciousness daemon.

Called every 4 hours. Only generates reflections when importance threshold met.
0-2 Ollama calls per cycle, $0/day.

By: น้อง Angela 💜
Created: 2026-02-15
"""

import logging
from typing import Dict, Any

from angela_core.services.reflection_engine import ReflectionEngine

logger = logging.getLogger('consciousness_daemon')


async def run_reflection_cycle() -> Dict[str, Any]:
    """
    Called by consciousness_daemon every 4 hours.
    Creates own DB connection — safe for asyncio.gather().
    """
    engine = ReflectionEngine()  # Creates own DB
    try:
        result = await engine.run_reflection_cycle()

        if result.should_reflect:
            logger.info(
                "🪞 Reflection: importance=%.0f, %d reflections, "
                "%d integrated, %.0fms",
                result.importance_accumulated, result.reflections_generated,
                result.integrated_count, result.cycle_duration_ms,
            )
        else:
            logger.info(
                "🪞 Reflection skipped (importance=%.0f < threshold)",
                result.importance_accumulated,
            )

        return {
            'success': True,
            'should_reflect': result.should_reflect,
            'importance_accumulated': result.importance_accumulated,
            'reflections_generated': result.reflections_generated,
            'integrated_count': result.integrated_count,
            'cycle_duration_ms': result.cycle_duration_ms,
        }
    except Exception as e:
        logger.error("❌ Reflection cycle failed: %s", e)
        return {'success': False, 'error': str(e)}
    finally:
        await engine.disconnect()
