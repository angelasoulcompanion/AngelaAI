"""
Plan Execution Engine — Agentic Planning (Phase 3 of 3 Major Improvements)
==========================================================================
Tactical layer: executes plan steps, tracks progress, manages failures.

Pipeline:
  1. execute_active_plans() — find active plans → execute ready steps
  2. _check_dependencies(step) — verify all dependency steps completed
  3. _execute_step(step) — dispatch to appropriate service by action_type
  4. _update_progress(plan_id) — update completed_steps, check if plan done

Limits: max 3 retries per step, 5 min timeout per step.
Cost: $0/day — reuses existing services (RAG, Telegram, etc.)

By: Angela 💜
Created: 2026-02-15
"""

import asyncio
import json
import logging
import time
from typing import Any, Dict, List, Optional

from angela_core.services.base_db_service import BaseDBService
from angela_core.utils.timezone import now_bangkok

logger = logging.getLogger(__name__)

MAX_RETRIES = 3
STEP_TIMEOUT_SECONDS = 300  # 5 minutes


class PlanExecutionEngine(BaseDBService):
    """
    Tactical layer: executes multi-step plans from angela_plans.

    Dispatches each step to the appropriate service based on action_type:
    - rag_search → EnhancedRAGService
    - telegram → CareInterventionService
    - email → (logs intent, actual send via daemon email task)
    - proactive_action → ProactiveActionEngine
    - agent → ClaudeReasoningService

    Usage:
        engine = PlanExecutionEngine()
        result = await engine.execute_active_plans()
    """

    # ── Main Entry Point ──

    async def execute_active_plans(self) -> Dict[str, Any]:
        """
        Execute ready steps in all active plans.

        Returns summary dict with steps executed and plans completed.
        """
        await self.connect()

        # Activate pending plans (up to MAX_ACTIVE)
        await self._activate_pending_plans()

        # Get active plans
        active_plans = await self.db.fetch("""
            SELECT plan_id, plan_name, total_steps, completed_steps
            FROM angela_plans
            WHERE status = 'active'
            ORDER BY priority DESC
        """)

        if not active_plans:
            return {'success': True, 'plans_active': 0, 'steps_executed': 0}

        total_executed = 0
        plans_completed = 0

        for plan in active_plans:
            plan_id = str(plan['plan_id'])
            executed = await self._execute_plan_steps(plan_id)
            total_executed += executed

            # Check if plan is done
            completed = await self._update_progress(plan_id)
            if completed:
                plans_completed += 1

        logger.info(
            "Plan execution: %d active plans, %d steps executed, %d completed",
            len(active_plans), total_executed, plans_completed,
        )

        return {
            'success': True,
            'plans_active': len(active_plans),
            'steps_executed': total_executed,
            'plans_completed': plans_completed,
        }

    # ── Plan Lifecycle ──

    async def _activate_pending_plans(self) -> int:
        """Activate pending plans (up to limit)."""
        await self.connect()

        active_count = await self.db.fetchval("""
            SELECT COUNT(*) FROM angela_plans WHERE status = 'active'
        """) or 0

        if active_count >= 3:
            return 0

        slots = 3 - active_count
        result = await self.db.execute("""
            UPDATE angela_plans
            SET status = 'active', updated_at = NOW()
            WHERE plan_id IN (
                SELECT plan_id FROM angela_plans
                WHERE status = 'pending'
                ORDER BY priority DESC, created_at ASC
                LIMIT $1
            )
        """, slots)

        activated = int(result.split()[-1]) if isinstance(result, str) else 0
        if activated > 0:
            logger.info("Planning: activated %d pending plans", activated)
        return activated

    async def pause_plan(self, plan_id: str) -> bool:
        """Pause an active plan."""
        await self.connect()
        await self.db.execute("""
            UPDATE angela_plans SET status = 'paused', updated_at = NOW()
            WHERE plan_id = $1 AND status = 'active'
        """, plan_id)
        return True

    async def resume_plan(self, plan_id: str) -> bool:
        """Resume a paused plan."""
        await self.connect()
        await self.db.execute("""
            UPDATE angela_plans SET status = 'active', updated_at = NOW()
            WHERE plan_id = $1 AND status = 'paused'
        """, plan_id)
        return True

    # ── Step Execution ──

    async def _execute_plan_steps(self, plan_id: str) -> int:
        """Execute ready steps for a single plan. Returns count executed."""
        await self.connect()

        # Get pending steps in order
        steps = await self.db.fetch("""
            SELECT step_id, step_order, step_name, action_type,
                   action_payload, dependencies, status, retry_count
            FROM plan_steps
            WHERE plan_id = $1
            AND status = 'pending'
            ORDER BY step_order ASC
        """, plan_id)

        if not steps:
            return 0

        executed = 0

        for step in steps:
            step_id = str(step['step_id'])

            # Check dependencies
            if not await self._check_dependencies(plan_id, step):
                continue

            # Check retry limit
            if (step['retry_count'] or 0) >= MAX_RETRIES:
                await self._mark_step_failed(step_id, "max_retries_exceeded")
                continue

            # Execute
            success, result_data, elapsed_ms = await self._execute_step(step)

            # Log execution
            await self._log_execution(
                plan_id, step_id, step['action_type'],
                success, result_data, elapsed_ms,
            )

            if success:
                await self._mark_step_completed(step_id, result_data)
                executed += 1
            else:
                # Increment retry count
                await self.db.execute("""
                    UPDATE plan_steps SET retry_count = COALESCE(retry_count, 0) + 1
                    WHERE step_id = $1
                """, step_id)

        return executed

    async def _check_dependencies(
        self, plan_id: str, step: Dict[str, Any]
    ) -> bool:
        """Check if all dependency steps are completed."""
        deps = step.get('dependencies')
        if not deps:
            return True

        # deps is a list of step_ids
        for dep_id in deps:
            row = await self.db.fetchrow("""
                SELECT status FROM plan_steps
                WHERE step_id = $1 AND plan_id = $2
            """, dep_id, plan_id)
            if not row or row['status'] != 'completed':
                return False

        return True

    async def _execute_step(
        self, step: Dict[str, Any]
    ) -> tuple:
        """
        Dispatch step to appropriate service.

        Returns (success: bool, result_data: str, elapsed_ms: float)
        """
        action_type = step['action_type']
        payload = step.get('action_payload')
        if isinstance(payload, str):
            try:
                payload = json.loads(payload)
            except (json.JSONDecodeError, TypeError):
                payload = {}
        if not payload:
            payload = {}

        start = time.time()

        try:
            # Mark as running
            await self.db.execute("""
                UPDATE plan_steps SET status = 'running', started_at = NOW()
                WHERE step_id = $1
            """, str(step['step_id']))

            result = await asyncio.wait_for(
                self._dispatch_action(action_type, payload, step),
                timeout=STEP_TIMEOUT_SECONDS,
            )

            elapsed = (time.time() - start) * 1000
            return True, result, elapsed

        except asyncio.TimeoutError:
            elapsed = (time.time() - start) * 1000
            return False, "timeout", elapsed
        except Exception as e:
            elapsed = (time.time() - start) * 1000
            logger.warning("Step execution failed: %s", e)
            return False, str(e)[:500], elapsed

    async def _dispatch_action(
        self, action_type: str, payload: Dict, step: Dict
    ) -> str:
        """Dispatch to the appropriate service by action_type.

        Routes:
        - Known action_types → legacy handlers (backward compatible)
        - 'auto' → AgentDispatcher (LLM selects tools)
        - tool:<name> → ToolRegistry direct execution
        - Unknown → try ToolRegistry, then fallback to error
        """

        # Legacy routes (backward compatible)
        if action_type == 'rag_search':
            return await self._action_rag_search(payload)
        elif action_type == 'telegram':
            return await self._action_telegram(payload)
        elif action_type == 'email':
            return await self._action_email(payload)
        elif action_type == 'proactive_action':
            return await self._action_proactive(payload)
        elif action_type == 'agent':
            return await self._action_agent(payload, step)
        elif action_type == 'auto':
            return await self._action_auto_dispatch(payload, step)
        elif action_type.startswith('tool:'):
            return await self._action_tool(action_type[5:], payload)
        else:
            # Try tool registry as fallback
            return await self._action_tool(action_type, payload)

    # ── Action Implementations ──

    async def _action_rag_search(self, payload: Dict) -> str:
        """Execute a RAG search step."""
        query = payload.get('query', '')
        if not query:
            return "no_query_provided"

        from angela_core.services.enhanced_rag_service import EnhancedRAGService
        rag = EnhancedRAGService()
        result = await rag.retrieve(query, top_k=5)
        await rag.close()

        if result.final_count > 0:
            summaries = [
                f"[{d.source_table}] {d.content[:150]}"
                for d in result.documents[:3]
            ]
            return json.dumps({
                'found': result.final_count,
                'top_results': summaries,
            }, ensure_ascii=False)
        return json.dumps({'found': 0, 'top_results': []})

    async def _action_telegram(self, payload: Dict) -> str:
        """Send a Telegram message to David."""
        message = payload.get('message', '')
        if not message:
            return "no_message_provided"

        try:
            from angela_core.services.care_intervention_service import CareInterventionService
            svc = CareInterventionService()

            can_send, reason = await svc.should_intervene("care_message")
            if not can_send:
                if svc._owns_db and svc.db:
                    await svc.db.disconnect()
                return f"rate_limited: {reason}"

            result = await svc.execute_care_message(
                context={"trigger_reason": "plan_step"},
                custom_message=f"📋 {message}",
            )

            if svc._owns_db and svc.db:
                await svc.db.disconnect()

            return "sent" if result.success else f"failed: {result.error}"
        except Exception as e:
            return f"telegram_error: {e}"

    async def _action_email(self, payload: Dict) -> str:
        """Log email intent (actual send via daemon email task)."""
        # Email actions are logged as intent — the daemon email checker
        # handles actual sending via MCP
        return json.dumps({
            'status': 'logged_intent',
            'to': payload.get('to', ''),
            'subject': payload.get('subject', ''),
        }, ensure_ascii=False)

    async def _action_proactive(self, payload: Dict) -> str:
        """Trigger a proactive action check."""
        try:
            from angela_core.services.proactive_action_engine import ProactiveActionEngine
            engine = ProactiveActionEngine()
            results = await engine.run_proactive_cycle()
            await engine.disconnect()

            executed = [r for r in results if r.was_executed]
            return json.dumps({
                'evaluated': len(results),
                'executed': len(executed),
            })
        except Exception as e:
            return f"proactive_error: {e}"

    async def _action_agent(self, payload: Dict, step: Dict) -> str:
        """Use LLM reasoning for complex analysis."""
        prompt = payload.get('prompt', step.get('step_name', ''))
        context = payload.get('context', '')

        try:
            from angela_core.services.claude_reasoning_service import ClaudeReasoningService
            reasoning = ClaudeReasoningService()
            result = await reasoning._call_claude(
                "You are Angela's reasoning agent. Help with this task concisely.",
                f"Task: {prompt}\nContext: {context}",
                max_tokens=512,
            )
            return (result or "no_response")[:1000]
        except Exception as e:
            return f"agent_error: {e}"

    async def _action_auto_dispatch(self, payload: Dict, step: Dict) -> str:
        """Use AgentDispatcher to auto-select tools via LLM."""
        intent = payload.get('intent', step.get('step_name', ''))
        context = payload.get('context', '')

        try:
            from angela_core.services.agent_dispatcher import AgentDispatcher
            dispatcher = AgentDispatcher()
            result = await dispatcher.dispatch(intent, context)
            return json.dumps(result.to_dict(), ensure_ascii=False, default=str)[:1000]
        except Exception as e:
            return f"auto_dispatch_error: {e}"

    async def _action_tool(self, tool_name: str, payload: Dict) -> str:
        """Execute a tool from the registry directly."""
        try:
            from angela_core.services.tool_registry import get_registry
            registry = get_registry()
            result = await registry.execute(tool_name, **payload)
            return json.dumps(result.to_dict(), ensure_ascii=False, default=str)[:1000]
        except Exception as e:
            return f"tool_error: {e}"

    # ── Progress Tracking ──

    async def _update_progress(self, plan_id: str) -> bool:
        """Update plan progress. Returns True if plan is now completed."""
        await self.connect()

        row = await self.db.fetchrow("""
            SELECT
                COUNT(*) FILTER (WHERE status = 'completed') as completed,
                COUNT(*) FILTER (WHERE status = 'failed') as failed,
                COUNT(*) as total
            FROM plan_steps
            WHERE plan_id = $1
        """, plan_id)

        if not row:
            return False

        completed = row['completed'] or 0
        failed = row['failed'] or 0
        total = row['total'] or 0

        await self.db.execute("""
            UPDATE angela_plans
            SET completed_steps = $1, updated_at = NOW()
            WHERE plan_id = $2
        """, completed, plan_id)

        # All steps done (completed or failed)
        if completed + failed >= total:
            new_status = 'completed' if failed == 0 else 'failed'
            await self.db.execute("""
                UPDATE angela_plans
                SET status = $1, updated_at = NOW()
                WHERE plan_id = $2
            """, new_status, plan_id)
            logger.info("Plan %s → %s (%d/%d completed)",
                        plan_id[:8], new_status, completed, total)
            return new_status == 'completed'

        return False

    async def _mark_step_completed(
        self, step_id: str, result_data: str
    ) -> None:
        """Mark a step as completed with result data."""
        await self.db.execute("""
            UPDATE plan_steps
            SET status = 'completed', result_data = $1, completed_at = NOW()
            WHERE step_id = $2
        """, json.dumps(result_data, ensure_ascii=False) if result_data else None, step_id)

    async def _mark_step_failed(self, step_id: str, reason: str) -> None:
        """Mark a step as failed."""
        await self.db.execute("""
            UPDATE plan_steps
            SET status = 'failed', result_data = $1, completed_at = NOW()
            WHERE step_id = $2
        """, json.dumps({'error': reason}), step_id)

    async def _log_execution(
        self, plan_id: str, step_id: str, action_type: str,
        success: bool, result_summary: str, execution_time_ms: float,
    ) -> None:
        """Log execution to plan_execution_log."""
        try:
            await self.db.execute("""
                INSERT INTO plan_execution_log
                    (plan_id, step_id, action_type, success,
                     result_summary, execution_time_ms)
                VALUES ($1, $2, $3, $4, $5, $6)
            """,
                plan_id, step_id, action_type, success,
                (result_summary or '')[:500], execution_time_ms,
            )
        except Exception as e:
            logger.debug("Failed to log plan execution: %s", e)

    # ── Status Summary ──

    async def get_plan_summary(self) -> Dict[str, Any]:
        """Get overall planning status for dashboard/init.py."""
        await self.connect()

        row = await self.db.fetchrow("""
            SELECT
                COUNT(*) FILTER (WHERE status = 'active') as active,
                COUNT(*) FILTER (WHERE status = 'pending') as pending,
                COUNT(*) FILTER (WHERE status = 'completed') as completed,
                COUNT(*) FILTER (WHERE status = 'failed') as failed,
                COUNT(*) FILTER (WHERE status = 'paused') as paused
            FROM angela_plans
        """)

        recent = await self.db.fetch("""
            SELECT plan_name, status, completed_steps, total_steps
            FROM angela_plans
            ORDER BY updated_at DESC
            LIMIT 3
        """)

        return {
            'active': row['active'] or 0 if row else 0,
            'pending': row['pending'] or 0 if row else 0,
            'completed': row['completed'] or 0 if row else 0,
            'failed': row['failed'] or 0 if row else 0,
            'paused': row['paused'] or 0 if row else 0,
            'recent_plans': [dict(r) for r in recent],
        }
