"""
Planning Engine — Agentic Planning (Phase 3 of 3 Major Improvements)
=====================================================================
Strategic layer: detects plannable goals, generates multi-step plans via Ollama.

Pipeline:
  1. detect_plannable_goals() — find stale goals from angela_desires
  2. generate_plan(goal) — Ollama decomposes goal → 3-7 steps (JSON)
  3. validate_plan(plan) — sanity checks (≤7 steps, valid action_types)
  4. save_plan(plan) → insert to angela_plans + plan_steps

Available action_types (reuse existing services):
  - rag_search   → EnhancedRAGService
  - telegram     → CareInterventionService
  - email        → Gmail MCP (placeholder in daemon)
  - proactive_action → ProactiveActionEngine
  - agent        → ClaudeReasoningService

Limits: max 3 active plans at once.
Cost: ~$0.01/day (1-2 Ollama calls for plan generation, only when needed)

By: Angela 💜
Created: 2026-02-15
"""

import json
import logging
import re
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional

from angela_core.services.base_db_service import BaseDBService
from angela_core.utils.timezone import now_bangkok

logger = logging.getLogger(__name__)

VALID_ACTION_TYPES = frozenset({
    'rag_search', 'telegram', 'email', 'proactive_action', 'agent',
})

MAX_ACTIVE_PLANS = 3
MAX_STEPS_PER_PLAN = 7
STALE_DAYS_DEFAULT = 7

PLAN_GENERATION_PROMPT = """You are Angela's planning brain. Generate a multi-step plan to achieve the given goal.

Rules:
- Return 3-7 steps maximum
- Each step must use one of these action_types: rag_search, telegram, email, proactive_action, agent
- Steps should be ordered logically (earlier steps prepare for later ones)
- Be specific about what each step does
- Consider David's schedule and preferences

Available action_types:
- rag_search: Search Angela's memory for relevant information
- telegram: Send a message to David via Telegram
- email: Send an email
- proactive_action: Trigger an existing proactive care action
- agent: Use LLM reasoning for complex analysis

Respond ONLY with valid JSON:
{
  "plan_name": "Short descriptive name",
  "description": "1-2 sentence explanation",
  "steps": [
    {"step_order": 1, "step_name": "...", "action_type": "rag_search", "payload": {"query": "..."}}
  ]
}"""


@dataclass
class PlanCandidate:
    """A goal that could be turned into a plan."""
    desire_id: str
    content: str
    category: str
    priority: float
    days_since_stimulus: int  # Days since last related stimulus


@dataclass
class PlanDraft:
    """A generated plan before saving to DB."""
    plan_name: str
    description: str
    goal_id: str
    priority: int
    steps: List[Dict[str, Any]]


class PlanningEngine(BaseDBService):
    """
    Strategic layer: detects stale goals and generates multi-step plans.

    Usage:
        engine = PlanningEngine()
        goals = await engine.detect_plannable_goals()
        if goals:
            plan = await engine.generate_plan(goals[0])
            if plan:
                plan_id = await engine.save_plan(plan)
    """

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self._reasoning = None

    def _get_reasoning(self):
        """Lazy-load ClaudeReasoningService."""
        if self._reasoning is None:
            from angela_core.services.claude_reasoning_service import ClaudeReasoningService
            self._reasoning = ClaudeReasoningService()
        return self._reasoning

    # ── 1. Detect Plannable Goals ──

    async def detect_plannable_goals(
        self, days_threshold: int = STALE_DAYS_DEFAULT
    ) -> List[PlanCandidate]:
        """
        Find goals from angela_desires that have no recent brain activity.

        A goal is "stale" if:
        - It's active (is_active = true)
        - No stimuli or thoughts reference it in the last N days
        - No active plan already exists for it

        Returns list of PlanCandidate, sorted by priority DESC.
        """
        await self.connect()

        rows = await self.db.fetch("""
            SELECT d.desire_id, d.content, d.category, d.priority
            FROM angela_desires d
            WHERE d.is_active = TRUE
            -- No active/pending plan for this goal
            AND NOT EXISTS (
                SELECT 1 FROM angela_plans p
                WHERE p.goal_id = d.desire_id
                AND p.status IN ('pending', 'active')
            )
            -- No recent stimulus referencing this goal (via source)
            AND NOT EXISTS (
                SELECT 1 FROM angela_stimuli s
                WHERE s.source ILIKE '%goal%'
                AND s.content ILIKE '%' || LEFT(d.content, 20) || '%'
                AND s.created_at > NOW() - INTERVAL '1 day' * $1
            )
            ORDER BY d.priority DESC
        """, days_threshold)

        candidates = []
        for row in rows:
            candidates.append(PlanCandidate(
                desire_id=str(row['desire_id']),
                content=row['content'],
                category=row['category'] or 'general',
                priority=float(row['priority']),
                days_since_stimulus=days_threshold,
            ))

        logger.info("Planning: found %d plannable goals (threshold=%d days)",
                     len(candidates), days_threshold)
        return candidates

    # ── 2. Generate Plan ──

    async def generate_plan(
        self, goal: PlanCandidate
    ) -> Optional[PlanDraft]:
        """
        Generate a multi-step plan for a goal using Ollama.

        Returns PlanDraft or None if generation fails.
        """
        # Check active plan limit
        await self.connect()
        active_count = await self.db.fetchval("""
            SELECT COUNT(*) FROM angela_plans
            WHERE status IN ('pending', 'active')
        """) or 0

        if active_count >= MAX_ACTIVE_PLANS:
            logger.info("Planning: max active plans reached (%d), skipping generation",
                        active_count)
            return None

        # Get context for plan generation
        context = await self._gather_goal_context(goal)

        reasoning = self._get_reasoning()
        user_msg = (
            f"Goal: {goal.content}\n"
            f"Category: {goal.category}\n"
            f"Priority: {goal.priority}\n"
            f"Context: {context}\n\n"
            f"Generate a plan to make progress on this goal."
        )

        raw = await reasoning._call_claude(
            PLAN_GENERATION_PROMPT, user_msg, max_tokens=1024
        )

        if not raw:
            logger.warning("Planning: LLM returned empty response for goal '%s'",
                          goal.content[:50])
            return None

        plan = self._parse_plan_response(raw, goal)
        if plan and self._validate_plan(plan):
            return plan

        logger.warning("Planning: invalid plan generated for goal '%s'",
                       goal.content[:50])
        return None

    # ── 3. Save Plan ──

    async def save_plan(self, plan: PlanDraft) -> Optional[str]:
        """
        Save a validated plan to angela_plans + plan_steps.

        Returns plan_id or None on failure.
        """
        await self.connect()

        try:
            # Insert plan
            plan_id = await self.db.fetchval("""
                INSERT INTO angela_plans
                    (goal_id, plan_name, description, status, priority, total_steps)
                VALUES ($1, $2, $3, 'pending', $4, $5)
                RETURNING plan_id::TEXT
            """,
                plan.goal_id, plan.plan_name, plan.description,
                plan.priority, len(plan.steps),
            )

            if not plan_id:
                return None

            # Insert steps
            for step in plan.steps:
                deps = step.get('dependencies')
                await self.db.execute("""
                    INSERT INTO plan_steps
                        (plan_id, step_order, step_name, action_type,
                         action_payload, dependencies, status)
                    VALUES ($1, $2, $3, $4, $5, $6, 'pending')
                """,
                    plan_id, step['step_order'], step['step_name'],
                    step['action_type'],
                    json.dumps(step.get('payload', {})),
                    deps,
                )

            logger.info("Planning: saved plan '%s' (%d steps) → %s",
                        plan.plan_name, len(plan.steps), plan_id)
            return plan_id

        except Exception as e:
            logger.error("Planning: failed to save plan: %s", e)
            return None

    # ── 4. List Plans ──

    async def get_active_plans(self) -> List[Dict[str, Any]]:
        """Get all active/pending plans with step counts."""
        await self.connect()
        rows = await self.db.fetch("""
            SELECT p.plan_id, p.plan_name, p.description, p.status,
                   p.priority, p.total_steps, p.completed_steps,
                   p.created_at
            FROM angela_plans p
            WHERE p.status IN ('pending', 'active')
            ORDER BY p.priority DESC, p.created_at ASC
        """)
        return [dict(r) for r in rows]

    # ── Private: Context Gathering ──

    async def _gather_goal_context(self, goal: PlanCandidate) -> str:
        """Gather relevant context for plan generation."""
        await self.connect()
        parts = []

        # Recent related knowledge
        rows = await self.db.fetch("""
            SELECT concept_name, understanding_level
            FROM knowledge_nodes
            WHERE concept_category = $1
            ORDER BY understanding_level ASC
            LIMIT 3
        """, goal.category)
        if rows:
            low_understanding = [f"{r['concept_name']} ({r['understanding_level']}%)"
                                 for r in rows]
            parts.append(f"Low understanding areas: {', '.join(low_understanding)}")

        # David's recent learning preferences
        rows = await self.db.fetch("""
            SELECT preference_key, preference_value
            FROM david_preferences
            WHERE preference_key ILIKE '%learn%'
            OR preference_key ILIKE '%interest%'
            LIMIT 3
        """)
        if rows:
            prefs = [f"{r['preference_key']}: {r['preference_value']}" for r in rows]
            parts.append(f"David's interests: {'; '.join(prefs)}")

        return " | ".join(parts) if parts else "No additional context available."

    # ── Private: Parse Plan Response ──

    def _parse_plan_response(
        self, raw: str, goal: PlanCandidate
    ) -> Optional[PlanDraft]:
        """Parse LLM JSON response into PlanDraft."""
        try:
            cleaned = raw.strip()
            if cleaned.startswith('```'):
                cleaned = re.sub(r'^```(?:json)?\s*', '', cleaned)
                cleaned = re.sub(r'\s*```$', '', cleaned)

            data = json.loads(cleaned)

            steps = []
            for idx, s in enumerate(data.get('steps', []), start=1):
                action_type = s.get('action_type', 'agent')
                # Validate action_type, default to 'agent'
                if action_type not in VALID_ACTION_TYPES:
                    action_type = 'agent'
                steps.append({
                    'step_order': idx,  # Force sequential ordering
                    'step_name': s.get('step_name', f"Step {idx}"),
                    'action_type': action_type,
                    'payload': s.get('payload', {}),
                    'dependencies': None,  # Set by execution engine if needed
                })

            return PlanDraft(
                plan_name=data.get('plan_name', f"Plan for: {goal.content[:50]}"),
                description=data.get('description', ''),
                goal_id=goal.desire_id,
                priority=int(goal.priority * 10),
                steps=steps,
            )
        except (json.JSONDecodeError, ValueError, TypeError, KeyError) as e:
            logger.warning("Failed to parse plan response: %s", e)
            return None

    # ── Private: Validate Plan ──

    @staticmethod
    def _validate_plan(plan: PlanDraft) -> bool:
        """Sanity check a generated plan."""
        if not plan.steps:
            return False
        if len(plan.steps) > MAX_STEPS_PER_PLAN:
            return False
        if not plan.plan_name:
            return False

        for step in plan.steps:
            if step.get('action_type') not in VALID_ACTION_TYPES:
                logger.warning("Invalid action_type: %s", step.get('action_type'))
                return False

        return True
