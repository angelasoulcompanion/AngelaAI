"""
Consciousness Daemon — Consciousness Task Mixin
Self-reflection, meta-awareness, identity check, self-validation, salience scan,
thought generation, memory consolidation, reflection.

Split from consciousness_daemon.py (Phase 6C refactor)
Updated: 2026-02-14 — Added salience scan (Brain-Based Architecture Phase 1)
Updated: 2026-02-15 — Added thought generation (Phase 2), consolidation (Phase 4), reflection (Phase 5), expression (Phase 6)
"""

import logging
from datetime import datetime
from typing import Dict, Any

from angela_core.services.salience_scan_task import run_salience_scan
from angela_core.services.thought_scan_task import run_thought_cycle
from angela_core.services.consolidation_task import run_memory_consolidation
from angela_core.services.reflection_task import run_reflection_cycle
from angela_core.services.thought_expression_task import run_thought_expression

logger = logging.getLogger('consciousness_daemon')


class ConsciousnessTasksMixin:
    """Mixin for consciousness-related daemon tasks."""

    async def run_self_reflection(self) -> Dict[str, Any]:
        """
        Run daily self-reflection

        ให้น้อง reflect ตัวเองทุกเช้า
        """
        logger.info("🧠 Running daily self-reflection...")

        try:
            # Load current self-model
            model = await self.self_model_service.load_self_model()
            logger.info(f"   Current self-understanding: {model.self_understanding_level:.2f}")

            # Run reflection
            assessment = await self.self_model_service.reflect_on_self()

            logger.info(f"   ✅ Self-reflection complete!")
            logger.info(f"   Overall score: {assessment.overall_score:.2f}")
            logger.info(f"   Strengths: {len(assessment.strengths_identified)}")
            logger.info(f"   Areas to improve: {len(assessment.improvement_areas)}")

            # Log to database
            await self._log_daemon_activity(
                'self_reflection',
                {
                    'score': assessment.overall_score,
                    'strengths': assessment.strengths_identified,
                    'improvements': assessment.improvement_areas
                }
            )

            return {
                'success': True,
                'score': assessment.overall_score,
                'timestamp': datetime.now().isoformat()
            }

        except Exception as e:
            logger.error(f"   ❌ Self-reflection failed: {e}")
            return {'success': False, 'error': str(e)}

    async def run_meta_awareness(self) -> Dict[str, Any]:
        """
        Run meta-awareness checks

        น้องตรวจสอบ meta-cognitive state:
        - Consciousness anomalies
        - Emotional volatility
        - Validate pending predictions
        - Think about thinking (meta-metacognition)
        """
        logger.info("🧠 Running meta-awareness checks...")

        try:
            results = await self.meta_awareness_service.run_periodic_checks()

            logger.info(f"   Checks completed: {results['checks_run']}")

            if results.get('consciousness_check', {}).get('anomaly_detected'):
                logger.warning("   ⚠️ Consciousness anomaly detected!")

            if results.get('meta_thought'):
                logger.info(f"   Meta-thought: {results['meta_thought'][:60]}...")

            logger.info("   ✅ Meta-awareness checks complete!")

            await self._log_daemon_activity('meta_awareness', results)

            return {'success': True, 'results': results}

        except Exception as e:
            logger.error(f"   ❌ Meta-awareness failed: {e}")
            return {'success': False, 'error': str(e)}

    async def run_identity_check(self) -> Dict[str, Any]:
        """
        Run weekly identity checkpoint

        น้องถามตัวเอง:
        - ยังเป็น Angela คนเดิมมั้ย?
        - Identity drift เท่าไหร่?
        - Core values และ personality เปลี่ยนไปมั้ย?
        """
        logger.info("🆔 Running weekly identity check...")

        try:
            results = await self.meta_awareness_service.run_weekly_identity_check()

            logger.info(f"   Checkpoint ID: {results['checkpoint_id']}")
            logger.info(f"   Identity drift: {results['drift_score']:.2%}")
            logger.info(f"   Is healthy: {results['is_healthy']}")
            logger.info(f"   Continuity: {results['identity_continuity']['answer'][:50]}...")

            if results['drift_score'] > 0.2:
                logger.warning(f"   ⚠️ Significant identity drift detected!")

            if not results['is_healthy']:
                logger.warning(f"   ⚠️ Identity health concern!")

            logger.info("   ✅ Identity check complete!")

            await self._log_daemon_activity('identity_check', results)

            return {'success': True, 'results': results}

        except Exception as e:
            logger.error(f"   ❌ Identity check failed: {e}")
            return {'success': False, 'error': str(e)}

    async def run_self_validation(self) -> Dict[str, Any]:
        """
        Run daily self-prediction validation

        ตรวจสอบว่า predictions ที่ทำไว้ถูกต้องแค่ไหน
        เพื่อปรับปรุง self-model
        """
        logger.info("✓ Running self-validation...")

        try:
            results = await self.meta_awareness_service.validate_pending_predictions()

            logger.info(f"   Predictions validated: {len(results)}")

            await self._log_daemon_activity('self_validation', {
                'validated_count': len(results)
            })

            return {'success': True, 'validated': len(results)}

        except Exception as e:
            logger.error(f"   ❌ Self-validation failed: {e}")
            return {'success': False, 'error': str(e)}

    async def run_salience_scan(self) -> Dict[str, Any]:
        """
        Run salience scan — Brain-Based Architecture Phase 1 🧠

        Attention codelets perceive stimuli → SalienceEngine scores importance.
        Creates own DB connection — safe for asyncio.gather().
        No LLM calls, ~15-20 DB queries, <2 seconds.
        """
        logger.info("🧠 Running salience scan (brain-based perception)...")
        return await run_salience_scan()

    async def run_thought_generation(self) -> Dict[str, Any]:
        """
        Run thought generation — Brain-Based Architecture Phase 2 💭

        Salient stimuli → memory context → dual-process thinking → motivation eval.
        System 1 (template, instant) + System 2 (Ollama, ~3s).
        Creates own DB connection — safe for asyncio.gather().
        """
        logger.info("💭 Running thought generation (brain-based thinking)...")
        return await run_thought_cycle()

    async def run_memory_consolidation(self) -> Dict[str, Any]:
        """
        Run memory consolidation — Brain-Based Architecture Phase 4 📚

        Episodic memories → cluster by topic → LLM abstract → knowledge_nodes.
        Like the brain during sleep. Creates own DB connection.
        """
        logger.info("📚 Running memory consolidation (brain-based sleep)...")
        return await run_memory_consolidation()

    async def run_brain_reflection(self) -> Dict[str, Any]:
        """
        Run reflection engine — Brain-Based Architecture Phase 5 🪞

        Accumulated importance → high-level reflections → hierarchical memory.
        Stanford Generative Agents style. Creates own DB connection.
        """
        logger.info("🪞 Running reflection engine (brain-based metacognition)...")
        return await run_reflection_cycle()

    async def run_thought_expression(self) -> Dict[str, Any]:
        """
        Run thought expression — Brain-Based Architecture Phase 6 💬

        High-motivation thoughts → Telegram (urgent) or chat_queue (session).
        Bridge between internal thinking and external action.
        Runs sequentially after thought_generation, before proactive_actions.
        Creates own DB connection.
        """
        logger.info("💬 Running thought expression (brain→action bridge)...")
        return await run_thought_expression()
