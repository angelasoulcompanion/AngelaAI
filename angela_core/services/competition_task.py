"""
Competition Task — Daemon Integration for GWT Competition Arena
================================================================
Wrapper for running competition + ignition cycles from the consciousness daemon.

Called every 30 minutes BETWEEN thought generation and thought expression.
No LLM calls, ~10 DB queries, <500ms per cycle.

Pipeline:
  1. CompetitionArena.run_competition() — softmax competition + lateral inhibition
  2. IgnitionGate.check_ignition() — consciousness threshold check
  3. Update MetacognitiveState — engagement/confidence from competition results

By: Angela 💜
Created: 2026-02-26
"""

import logging
from typing import Any, Dict

logger = logging.getLogger('consciousness_daemon')


async def run_competition_cycle() -> Dict[str, Any]:
    """
    Run GWT competition + ignition cycle.

    Called by consciousness_daemon every 30 minutes, between
    thought generation and thought expression.

    Creates own DB connections — safe for sequential execution.
    """
    from angela_core.services.competition_arena import CompetitionArena
    from angela_core.services.ignition_gate import IgnitionGate

    arena = CompetitionArena()
    gate = IgnitionGate()

    try:
        # 1. Get David's state and metacognitive state
        david_state = "neutral"
        meta_state = None
        try:
            from angela_core.services.metacognitive_state import MetacognitiveStateManager
            meta = MetacognitiveStateManager()
            meta_state = meta.state.to_dict()
        except Exception:
            pass

        try:
            await arena.connect()
            state_row = await arena.db.fetchrow("""
                SELECT dominant_state FROM emotional_adaptation_log
                WHERE confidence > 0.5
                ORDER BY created_at DESC LIMIT 1
            """)
            if state_row:
                david_state = state_row['dominant_state']
        except Exception:
            pass

        # 2. Run competition
        competition = await arena.run_competition(
            david_state=david_state,
            metacognitive_state=meta_state,
        )

        # 3. Run ignition gate on winners
        ignition_result = None
        if competition.winners:
            winner_dicts = [
                {
                    'thought_id': w.thought_id,
                    'content': w.content,
                    'competition_score': w.competition_score,
                    'created_at': w.created_at,
                    'thought_type': w.thought_type,
                    'motivation_breakdown': w.motivation_breakdown or {},
                }
                for w in competition.winners
            ]

            ignition_result = await gate.check_ignition(
                winners=winner_dicts,
                competition_margin=competition.margin,
                david_state=david_state,
                metacognitive_state=meta_state,
            )

            # Update competition_log with ignition result
            if ignition_result.ignited > 0:
                try:
                    await arena.db.execute("""
                        UPDATE competition_log
                        SET ignition_triggered = TRUE
                        WHERE competition_id = (
                            SELECT competition_id FROM competition_log
                            ORDER BY created_at DESC LIMIT 1
                        )
                    """)
                except Exception:
                    pass

        # 4. Extinguish stale simmering thoughts
        extinguished_stale = await gate.extinguish_stale_simmering()

        # 5. Update metacognitive state from competition results
        try:
            from angela_core.services.metacognitive_state import MetacognitiveStateManager
            meta = MetacognitiveStateManager()
            s = meta.state

            if competition.total_candidates > 0:
                # More competition = higher cognitive load
                s.cognitive_load = min(1.0, s.cognitive_load + competition.total_candidates * 0.02)

                # Clear winner = higher confidence
                if competition.margin > 0.2:
                    s.confidence = min(1.0, s.confidence + 0.05)
                elif competition.margin < 0.05:
                    s.uncertainty = min(1.0, s.uncertainty + 0.05)

                # Winners ignited = higher engagement
                if ignition_result and ignition_result.ignited > 0:
                    s.engagement = min(1.0, s.engagement + 0.1)

                s.last_update_reason = (
                    f"competition: {competition.total_candidates} candidates, "
                    f"margin={competition.margin:.3f}"
                )
                meta.save()
        except Exception as e:
            logger.debug("Metacognitive update after competition failed: %s", e)

        logger.info(
            "🏟️ [Brain] Competition cycle: %d candidates, %d winners, "
            "%d ignited, margin=%.3f",
            competition.total_candidates,
            len(competition.winners),
            ignition_result.ignited if ignition_result else 0,
            competition.margin,
        )

        return {
            'success': True,
            'candidates': competition.total_candidates,
            'winners': len(competition.winners),
            'inhibited': competition.inhibited_count,
            'ignited': ignition_result.ignited if ignition_result else 0,
            'simmering': ignition_result.simmering if ignition_result else 0,
            'extinguished': (
                (ignition_result.extinguished if ignition_result else 0)
                + extinguished_stale
            ),
            'margin': competition.margin,
            'top_score': competition.top_score,
            'cycle_duration_ms': competition.cycle_duration_ms,
        }

    except Exception as e:
        logger.error("❌ Competition cycle failed: %s", e)
        return {'success': False, 'error': str(e)}
    finally:
        await arena.disconnect()
        await gate.disconnect()
