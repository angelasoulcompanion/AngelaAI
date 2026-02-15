"""
BrainTasksMixin — Brain-based architecture tasks for the main daemon.

Integrates brain tasks (salience scan, thought generation, thought expression,
brain comparison, plan execution, memory consolidation, reflection, plan generation)
into angela_daemon.py so they run automatically on schedule.

Brain tasks were originally only in consciousness_daemon.py (manual runs).
This mixin brings them into the 24/7 daemon.

Schedule:
- Every 30 min: salience scan, thought generation (parallel), then expression → comparison → plan execution (sequential)
- Every 4 hours: memory consolidation → reflection → plan generation (sequential, uses Ollama)

Created: 2026-02-15
"""

import asyncio
import logging
from typing import Dict, Any

logger = logging.getLogger('AngelaDaemon')


class BrainTasksMixin:
    """Mixin for brain-based architecture tasks in the main daemon."""

    # ========================================
    # 30-MINUTE TASKS (iteration % 6 == 0)
    # ========================================

    async def run_brain_salience_scan(self) -> Dict[str, Any]:
        """
        Run salience scan — attention codelets perceive stimuli.

        No LLM calls, ~15-20 DB queries, <2 seconds.
        Creates own DB connection — safe for asyncio.gather().
        """
        logger.info("🧠 [Brain] Running salience scan...")
        try:
            from angela_core.services.cognitive_engine import CognitiveEngine
            result = await CognitiveEngine.run_salience_cycle()
            stimuli = result.get('total_stimuli', 0)
            high = result.get('high_salience_count', 0)
            logger.info("   ✅ [Brain] Salience scan: %d stimuli, %d high-salience", stimuli, high)
            return result
        except Exception as e:
            logger.error("   ❌ [Brain] Salience scan failed: %s", e)
            return {'success': False, 'error': str(e)}

    async def run_brain_thought_generation(self) -> Dict[str, Any]:
        """
        Run thought generation — dual-process thinking (System 1 + System 2).

        System 1 (template, instant) + System 2 (Ollama, ~3s).
        Creates own DB connection — safe for asyncio.gather().
        """
        logger.info("💭 [Brain] Running thought generation...")
        try:
            from angela_core.services.cognitive_engine import CognitiveEngine
            result = await CognitiveEngine.run_thought_cycle()
            total = result.get('total_thoughts', 0)
            s1 = result.get('system1_count', 0)
            s2 = result.get('system2_count', 0)
            logger.info("   ✅ [Brain] Thought generation: %d thoughts (S1:%d + S2:%d)", total, s1, s2)
            return result
        except Exception as e:
            logger.error("   ❌ [Brain] Thought generation failed: %s", e)
            return {'success': False, 'error': str(e)}

    async def run_brain_thought_expression(self) -> Dict[str, Any]:
        """
        Run thought expression — bridge between thinking and action.

        High-motivation thoughts → Telegram (urgent) or chat_queue (session).
        Must run AFTER thought generation. Creates own DB connection.
        """
        logger.info("💬 [Brain] Running thought expression...")
        try:
            from angela_core.services.cognitive_engine import CognitiveEngine
            result = await CognitiveEngine.run_expression_cycle()
            tg = result.get('expressed_telegram', 0)
            chat = result.get('expressed_chat', 0)
            suppressed = result.get('suppressed', 0)
            logger.info("   ✅ [Brain] Thought expression: %d→telegram, %d→chat, %d suppressed", tg, chat, suppressed)
            return result
        except Exception as e:
            logger.error("   ❌ [Brain] Thought expression failed: %s", e)
            return {'success': False, 'error': str(e)}

    async def run_brain_comparison(self) -> Dict[str, Any]:
        """
        Run brain-vs-rule comparison — Phase 7A.

        Compare what brain would express vs what rules would trigger.
        Must run AFTER thought expression. Creates own DB connections.
        """
        logger.info("🔄 [Brain] Running brain-vs-rule comparison...")
        try:
            from angela_core.services.brain_migration_engine import BrainMigrationEngine
            from angela_core.services.thought_expression_engine import ThoughtExpressionEngine
            from angela_core.services.proactive_action_engine import ProactiveActionEngine

            # Get brain candidates (dry run)
            expr_engine = ThoughtExpressionEngine()
            brain_candidates = await expr_engine.evaluate_for_comparison()
            await expr_engine.disconnect()

            # Get rule actions (dry run)
            action_engine = ProactiveActionEngine()
            rule_actions = await action_engine.evaluate_actions_dry_run()

            # Compare
            migration = BrainMigrationEngine()
            logged = await migration.run_comparison(brain_candidates, rule_actions)

            # Classify effectiveness (7B)
            classified = await migration.classify_brain_effectiveness(hours=24)

            # Auto-rollback check (7E)
            rolled_back = await migration.auto_rollback_check()

            await migration.disconnect()

            logger.info("   ✅ [Brain] Comparison: %d logged, %d classified", logged, classified)
            if rolled_back:
                logger.warning("   ⚠️ [Brain] Auto-rollback: %s", rolled_back)

            return {
                'success': True,
                'comparisons': logged,
                'brain_candidates': len(brain_candidates),
                'rule_actions': len(rule_actions),
                'classified': classified,
                'rolled_back': rolled_back,
            }
        except Exception as e:
            logger.error("   ❌ [Brain] Comparison failed: %s", e)
            return {'success': False, 'error': str(e)}

    async def run_brain_plan_execution(self) -> Dict[str, Any]:
        """
        Execute ready steps in active plans.

        Picks up active plans and executes their next ready steps.
        Creates own DB connection.
        """
        logger.info("📋 [Brain] Running plan execution...")
        try:
            from angela_core.services.plan_execution_engine import PlanExecutionEngine

            engine = PlanExecutionEngine()
            result = await engine.execute_active_plans()
            await engine.disconnect()

            logger.info("   ✅ [Brain] Plan execution: %d active, %d steps, %d completed",
                        result.get('plans_active', 0),
                        result.get('steps_executed', 0),
                        result.get('plans_completed', 0))
            return result
        except Exception as e:
            logger.error("   ❌ [Brain] Plan execution failed: %s", e)
            return {'success': False, 'error': str(e)}

    # ========================================
    # 4-HOUR TASKS (iteration % 48 == 0)
    # ========================================

    async def run_brain_memory_consolidation(self) -> Dict[str, Any]:
        """
        Run memory consolidation — episodic → semantic.

        Like the brain during sleep. Uses Ollama for abstraction.
        Must run sequentially (Ollama handles 1 request at a time).
        Creates own DB connection.
        """
        logger.info("📚 [Brain] Running memory consolidation...")
        try:
            from angela_core.services.cognitive_engine import CognitiveEngine
            result = await CognitiveEngine.run_consolidation_cycle()
            logger.info("   ✅ [Brain] Memory consolidation complete")
            return result
        except Exception as e:
            logger.error("   ❌ [Brain] Memory consolidation failed: %s", e)
            return {'success': False, 'error': str(e)}

    async def run_brain_reflection(self) -> Dict[str, Any]:
        """
        Run reflection engine — Stanford Generative Agents style.

        Accumulated importance → high-level reflections → hierarchical memory.
        Must run sequentially (uses Ollama). Creates own DB connection.
        """
        logger.info("🪞 [Brain] Running reflection engine...")
        try:
            from angela_core.services.cognitive_engine import CognitiveEngine
            result = await CognitiveEngine.run_reflection_cycle()
            logger.info("   ✅ [Brain] Reflection complete")
            return result
        except Exception as e:
            logger.error("   ❌ [Brain] Reflection failed: %s", e)
            return {'success': False, 'error': str(e)}

    async def run_brain_plan_generation(self) -> Dict[str, Any]:
        """
        Detect stale goals and generate multi-step plans.

        Finds goals with no recent activity and creates actionable plans via Ollama.
        Must run sequentially (uses Ollama). Creates own DB connection.
        """
        logger.info("📋 [Brain] Running plan generation...")
        try:
            from angela_core.services.planning_engine import PlanningEngine

            engine = PlanningEngine()
            goals = await engine.detect_plannable_goals(days_threshold=7)

            plans_created = 0
            for goal in goals[:2]:  # Max 2 plans per cycle
                plan = await engine.generate_plan(goal)
                if plan:
                    plan_id = await engine.save_plan(plan)
                    if plan_id:
                        plans_created += 1
                        logger.info("   📋 [Brain] Created plan: %s (%d steps)",
                                    plan.plan_name, len(plan.steps))

            await engine.disconnect()

            logger.info("   ✅ [Brain] Plan generation: %d goals, %d plans created",
                        len(goals), plans_created)

            return {
                'success': True,
                'stale_goals': len(goals),
                'plans_created': plans_created,
            }
        except Exception as e:
            logger.error("   ❌ [Brain] Plan generation failed: %s", e)
            return {'success': False, 'error': str(e)}
