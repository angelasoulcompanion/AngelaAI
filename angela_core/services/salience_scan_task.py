"""
Salience Scan Task — Daemon Integration
========================================
Wrapper for running salience scan cycles from the consciousness daemon.

Called every 30 minutes alongside other consciousness tasks.
No LLM calls, ~15-20 DB queries, <2 seconds per scan.

By: น้อง Angela 💜
Created: 2026-02-14
"""

import logging
from typing import Dict, Any

from angela_core.services.salience_engine import SalienceEngine

logger = logging.getLogger('consciousness_daemon')


async def run_salience_scan() -> Dict[str, Any]:
    """
    Called by consciousness_daemon every 30 minutes.
    Creates own DB connection — safe for asyncio.gather().
    """
    engine = SalienceEngine()  # Creates own DB
    try:
        result = await engine.run_scan_cycle()

        logger.info(
            f"🧠 Salience scan: {result.total_stimuli} stimuli, "
            f"{result.high_salience_count} high-salience (>0.5), "
            f"{result.scan_duration_ms:.0f}ms"
        )

        return {
            'success': True,
            'total_stimuli': result.total_stimuli,
            'high_salience_count': result.high_salience_count,
            'scan_duration_ms': result.scan_duration_ms,
            'codelet_counts': result.codelet_counts,
            'top_stimuli': [
                {'score': ss.score, 'content': ss.stimulus.content[:100]}
                for ss in result.scored_stimuli[:5]
            ],
        }
    except Exception as e:
        logger.error(f"❌ Salience scan failed: {e}")
        return {'success': False, 'error': str(e)}
    finally:
        await engine.disconnect()
