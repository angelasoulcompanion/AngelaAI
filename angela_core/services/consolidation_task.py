"""
Memory Consolidation Task — Daemon Integration
================================================
Wrapper for running memory consolidation from the consciousness daemon.

Called every 4 hours. Consolidates episodic memories → semantic knowledge.
0-N Ollama calls (1 per cluster), $0/day.

By: น้อง Angela 💜
Created: 2026-02-15
"""

import logging
from typing import Dict, Any

from angela_core.services.memory_consolidation_engine import MemoryConsolidationEngine

logger = logging.getLogger('consciousness_daemon')


async def run_memory_consolidation() -> Dict[str, Any]:
    """
    Called by consciousness_daemon every 4 hours.
    Creates own DB connection — safe for asyncio.gather().
    """
    engine = MemoryConsolidationEngine()  # Creates own DB
    try:
        result = await engine.run_consolidation_cycle()

        logger.info(
            "📚 Consolidation: %d episodes → %d clusters → "
            "%d abstractions → %d knowledge, %d decayed, %.0fms",
            result.episodes_gathered, result.clusters_formed,
            result.abstractions_generated, result.knowledge_integrated,
            result.episodes_decayed, result.cycle_duration_ms,
        )

        return {
            'success': True,
            'episodes_gathered': result.episodes_gathered,
            'clusters_formed': result.clusters_formed,
            'abstractions_generated': result.abstractions_generated,
            'knowledge_integrated': result.knowledge_integrated,
            'episodes_decayed': result.episodes_decayed,
            'cycle_duration_ms': result.cycle_duration_ms,
        }
    except Exception as e:
        logger.error("❌ Memory consolidation failed: %s", e)
        return {'success': False, 'error': str(e)}
    finally:
        await engine.disconnect()
