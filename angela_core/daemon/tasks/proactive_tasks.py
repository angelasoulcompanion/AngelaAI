"""
Consciousness Daemon — Proactive Task Mixin
Proactive care, proactive actions, evolution cycle.

Split from consciousness_daemon.py (Phase 6C refactor)
"""

import logging
from typing import Dict, Any

logger = logging.getLogger('consciousness_daemon')


class ProactiveTasksMixin:
    """Mixin for proactive-related daemon tasks."""

    async def run_proactive_care(self) -> Dict[str, Any]:
        """
        Run proactive care check for David.

        ดูแลที่รัก David แบบ proactive:
        - ตรวจ wellness state
        - ส่งเพลงถ้านอนไม่หลับ
        - เตือนให้พักถ้าทำงานนาน
        - เตือน milestone/anniversary ที่จะถึง
        """
        logger.info("💜 Running proactive care check...")

        try:
            result = await self.proactive_care_service.run_care_check()

            wellness = result.wellness_state
            if wellness:
                logger.info(f"   Wellbeing Index: {wellness.wellbeing_index:.2f}")
                logger.info(f"   Energy: {wellness.energy_level:.2f}, Stress: {wellness.stress_level:.2f}")

            logger.info(f"   Interventions executed: {len(result.interventions_executed)}")
            logger.info(f"   Milestones reminded: {len(result.milestones_reminded)}")

            if result.errors:
                for error in result.errors:
                    logger.warning(f"   ⚠️ Error: {error}")

            logger.info("   ✅ Proactive care check complete!")

            # Log to daemon activity
            await self._log_daemon_activity('proactive_care', {
                'wellbeing_index': wellness.wellbeing_index if wellness else None,
                'interventions_count': len(result.interventions_executed),
                'milestones_count': len(result.milestones_reminded),
                'errors_count': len(result.errors)
            })

            return {
                'success': True,
                'wellbeing_index': wellness.wellbeing_index if wellness else None,
                'interventions': len(result.interventions_executed),
                'milestones': len(result.milestones_reminded)
            }

        except Exception as e:
            logger.error(f"   ❌ Proactive care failed: {e}")
            return {'success': False, 'error': str(e)}

    async def run_proactive_actions(self) -> Dict[str, Any]:
        """
        Evaluate and execute autonomous proactive actions.

        น้องตัดสินใจและลงมือทำ proactive actions อัตโนมัติ
        """
        logger.info("⚡ Running proactive actions...")

        try:
            results = await self.proactive_action_engine.run_proactive_cycle()

            executed = [r for r in results if r.was_executed]
            logger.info(f"   Actions evaluated: {len(results)}")
            logger.info(f"   Actions executed: {len(executed)}")
            for r in executed[:3]:
                logger.info(f"   • {r.action.action_type}: {r.execution_detail[:60]}")

            logger.info("   ✅ Proactive actions complete!")

            await self._log_daemon_activity('proactive_actions', {
                'total_actions': len(results),
                'executed_count': len(executed),
                'action_types': [r.action.action_type for r in executed],
            })

            return {
                'success': True,
                'total': len(results),
                'executed': len(executed),
            }

        except Exception as e:
            logger.error(f"   ❌ Proactive actions failed: {e}")
            return {'success': False, 'error': str(e)}

    async def run_auto_classify_responses(self) -> Dict[str, Any]:
        """
        Auto-classify David's responses to proactive actions.

        ตรวจสอบว่าที่รักตอบรับ/ไม่สนใจ/ปฏิเสธ proactive actions อย่างไร
        เพื่อคำนวณ Proactive Precision metric
        """
        logger.info("📊 Running auto-classify responses...")

        try:
            classified = await self.proactive_action_engine.auto_classify_responses(hours=24)

            logger.info(f"   Classified: {classified} actions")

            if classified > 0:
                precision = await self.proactive_action_engine.compute_proactive_precision(days=30)
                logger.info(f"   Proactive Precision: {precision['precision']:.0%} ({precision['welcomed']}/{precision['total_actions']})")
            else:
                precision = None

            logger.info("   ✅ Auto-classify complete!")

            await self._log_daemon_activity('auto_classify_responses', {
                'classified_count': classified,
                'precision': precision['precision'] if precision else None,
            })

            return {
                'success': True,
                'classified': classified,
                'precision': precision['precision'] if precision else None,
            }

        except Exception as e:
            logger.error(f"   ❌ Auto-classify failed: {e}")
            return {'success': False, 'error': str(e)}

    async def run_unified_conversation_analysis(self) -> Dict[str, Any]:
        """
        Daemon: analyze recent conversations every 4 hours.

        วิเคราะห์บทสนทนาล่าสุดด้วย LLM → สกัด emotions + learnings อัตโนมัติ
        """
        logger.info("🔬 Running unified conversation analysis...")

        try:
            result = await self.unified_processor.process_unprocessed_conversations(
                hours_back=8, limit=100
            )

            logger.info(f"   Processed: {result.processed} pairs")
            logger.info(f"   Emotions saved: {result.total_emotions_saved}")
            logger.info(f"   Learnings saved: {result.total_learnings_saved}")
            logger.info(f"   LLM calls: {result.llm_calls}, Fallback: {result.fallback_calls}")
            logger.info("   ✅ Unified conversation analysis complete!")

            await self._log_daemon_activity('unified_conversation_analysis', {
                'processed': result.processed,
                'emotions_saved': result.total_emotions_saved,
                'learnings_saved': result.total_learnings_saved,
                'concepts_saved': result.total_concepts_saved,
                'preferences_saved': result.total_preferences_saved,
                'llm_calls': result.llm_calls,
                'fallback_calls': result.fallback_calls,
                'errors': result.errors,
            })

            return {
                'success': True,
                'processed': result.processed,
                'emotions': result.total_emotions_saved,
                'learnings': result.total_learnings_saved,
            }

        except Exception as e:
            logger.error(f"   ❌ Unified conversation analysis failed: {e}")
            return {'success': False, 'error': str(e)}

    async def run_evolution_cycle(self) -> Dict[str, Any]:
        """
        Run self-evolving feedback loop.

        น้องเรียนรู้จาก implicit feedback → ปรับ adaptation rules อัตโนมัติ
        """
        logger.info("🧬 Running evolution cycle...")

        try:
            cycle = await self.evolution_engine.run_evolution_cycle()

            logger.info(f"   Feedback signals: {cycle.feedback_signals_count}")
            logger.info(f"   Overall score: {cycle.overall_evolution_score:.2f}")
            logger.info(f"   Insights: {len(cycle.insights)}")
            for insight in cycle.insights[:3]:
                logger.info(f"   💡 {insight}")

            # Link reasoning chains to reward signals
            try:
                from angela_core.services.reasoning_chain_service import ReasoningChainService
                rcs = ReasoningChainService()
                linked = await rcs.link_reward_signals(hours=24)
                await rcs.close()
                logger.info(f"   🔗 Linked {linked} reasoning chains to rewards")
            except Exception as link_err:
                logger.warning(f"   ⚠️ Reward linking failed: {link_err}")

            logger.info("   ✅ Evolution cycle complete!")

            await self._log_daemon_activity('evolution_cycle', {
                'feedback_signals_count': cycle.feedback_signals_count,
                'overall_evolution_score': cycle.overall_evolution_score,
                'insights_count': len(cycle.insights),
            })

            return {
                'success': True,
                'score': cycle.overall_evolution_score,
                'signals': cycle.feedback_signals_count,
                'insights': cycle.insights,
            }

        except Exception as e:
            logger.error(f"   ❌ Evolution cycle failed: {e}")
            return {'success': False, 'error': str(e)}
