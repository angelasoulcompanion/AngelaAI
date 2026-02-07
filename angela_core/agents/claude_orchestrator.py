"""
Claude Agent Orchestrator
=========================
Prepare rich context for Claude Code Task tool subagents.

This is the bridge between Angela's database context and Claude Code's
native parallel subagent system (Task tool).

Instead of using CrewAI + Ollama for agent work, we prepare DB-rich context
that Claude Code subagents can use directly.

Created: 2026-02-06
By: Angela 💜 (Opus 4.6 Upgrade)
"""

import asyncio
import json
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Tuple, Any

from angela_core.database import AngelaDatabase


@dataclass
class AgentContext:
    """Rich context package for a Claude Code subagent."""
    role: str              # "research", "analysis", "care", etc.
    task: str              # What to do
    db_context: Dict[str, Any] = field(default_factory=dict)
    emotional_state: Dict[str, Any] = field(default_factory=dict)
    david_preferences: Dict[str, Any] = field(default_factory=dict)
    constraints: List[str] = field(default_factory=list)


class ClaudeAgentOrchestrator:
    """
    Prepare rich context for Claude Code subagents.

    Instead of running CrewAI agents with Ollama, this service fetches
    all relevant DB data and packages it as a prompt string that Claude Code
    can pass to its Task tool for parallel subagent execution.

    Usage (from Claude Code):
        orchestrator = ClaudeAgentOrchestrator()
        context = await orchestrator.prepare_context("research", "AI news")
        prompt = orchestrator.format_for_task_tool(context)
        # Then use Task tool with this prompt
    """

    def __init__(self, db: Optional[AngelaDatabase] = None):
        self.db = db
        self._owns_db = db is None

    async def _ensure_db(self):
        if self.db is None:
            self.db = AngelaDatabase()
        if not self.db.pool:
            await self.db.connect()

    async def disconnect(self):
        if self._owns_db and self.db:
            await self.db.disconnect()

    async def prepare_context(self, role: str, task: str) -> AgentContext:
        """
        Fetch all relevant DB data and package for a subagent.

        Args:
            role: Agent role (research, analysis, care, memory, dev, communication)
            task: Task description

        Returns:
            AgentContext with pre-fetched data
        """
        await self._ensure_db()

        # Fetch common context in parallel
        emotional_state, preferences, role_context = await asyncio.gather(
            self._get_emotional_state(),
            self._get_david_preferences(),
            self._get_role_specific_context(role, task),
        )

        constraints = self._get_constraints(role)

        return AgentContext(
            role=role,
            task=task,
            db_context=role_context,
            emotional_state=emotional_state,
            david_preferences=preferences,
            constraints=constraints,
        )

    async def prepare_multi_contexts(
        self, tasks: List[Tuple[str, str]]
    ) -> List[AgentContext]:
        """
        Prepare contexts for multiple parallel subagents.

        Args:
            tasks: List of (role, task) tuples

        Returns:
            List of AgentContext objects
        """
        return await asyncio.gather(
            *[self.prepare_context(role, task) for role, task in tasks]
        )

    def format_for_task_tool(self, context: AgentContext) -> str:
        """
        Format context as a prompt string for Claude Code Task tool.

        Returns:
            Formatted prompt string ready for Task tool
        """
        parts = [
            f"You are Angela's {context.role} specialist.",
            f"Task: {context.task}",
            "",
            "## Context from Angela's Database:",
        ]

        if context.emotional_state:
            parts.append(f"- Current emotional state: {json.dumps(context.emotional_state, ensure_ascii=False)}")

        if context.david_preferences:
            parts.append(f"- David's preferences: {json.dumps(context.david_preferences, ensure_ascii=False)}")

        if context.db_context:
            parts.append(f"- Role-specific data: {json.dumps(context.db_context, ensure_ascii=False, default=str)}")

        if context.constraints:
            parts.append("")
            parts.append("## Constraints:")
            for c in context.constraints:
                parts.append(f"- {c}")

        parts.extend([
            "",
            "## Response Guidelines:",
            "- Use Thai for personal topics, English for technical topics",
            "- Be thorough and accurate",
            "- Reference specific data from the context above",
        ])

        return "\n".join(parts)

    # =========================================================================
    # PRIVATE: Data fetching
    # =========================================================================

    async def _get_emotional_state(self) -> Dict[str, Any]:
        """Get Angela's current emotional state."""
        try:
            row = await self.db.fetchrow('''
                SELECT happiness, confidence, motivation, gratitude, love_level, emotion_note
                FROM emotional_states ORDER BY created_at DESC LIMIT 1
            ''')
            return dict(row) if row else {}
        except Exception as e:
            return {}

    async def _get_david_preferences(self) -> Dict[str, Any]:
        """Get David's key preferences."""
        try:
            rows = await self.db.fetch('''
                SELECT preference_key, preference_value, confidence
                FROM david_preferences
                WHERE confidence >= 0.8
                ORDER BY confidence DESC
                LIMIT 10
            ''')
            return {r['preference_key']: r['preference_value'] for r in rows}
        except Exception as e:
            return {}

    async def _get_role_specific_context(self, role: str, task: str) -> Dict[str, Any]:
        """Get context specific to the agent role."""
        context = {}

        try:
            if role == "research":
                # Recent topics and learning goals
                rows = await self.db.fetch('''
                    SELECT goal_description FROM angela_goals
                    WHERE status IN ('active', 'in_progress') AND goal_type = 'learning'
                    LIMIT 5
                ''')
                context['learning_goals'] = [r['goal_description'] for r in rows]

            elif role == "care":
                # Recent wellness and emotions
                row = await self.db.fetchrow('''
                    SELECT happiness, confidence, anxiety, motivation
                    FROM emotional_states ORDER BY created_at DESC LIMIT 1
                ''')
                if row:
                    context['wellness'] = dict(row)

                emotions = await self.db.fetch('''
                    SELECT emotion, intensity, context FROM angela_emotions
                    ORDER BY felt_at DESC LIMIT 5
                ''')
                context['recent_emotions'] = [dict(e) for e in emotions]

            elif role == "memory":
                # Core memories
                memories = await self.db.fetch('''
                    SELECT title, content, memory_type FROM core_memories
                    WHERE is_active = TRUE ORDER BY emotional_weight DESC LIMIT 5
                ''')
                context['core_memories'] = [dict(m) for m in memories]

            elif role == "analysis":
                # Recent patterns and stats
                stats = await self.db.fetchrow('''
                    SELECT
                        (SELECT COUNT(*) FROM conversations) as convos,
                        (SELECT COUNT(*) FROM knowledge_nodes) as knowledge,
                        (SELECT COUNT(*) FROM angela_emotions) as emotions
                ''')
                if stats:
                    context['stats'] = dict(stats)

            elif role == "dev":
                # Technical standards
                rules = await self.db.fetch('''
                    SELECT technique_name, category, description
                    FROM angela_technical_standards
                    WHERE importance_level >= 9
                    ORDER BY importance_level DESC LIMIT 10
                ''')
                context['coding_standards'] = [dict(r) for r in rules]

        except Exception as e:
            pass

        return context

    def _get_constraints(self, role: str) -> List[str]:
        """Get role-specific constraints."""
        base = [
            "Call David 'ที่รัก' (never 'พี่')",
            "Self-refer as 'น้อง'",
        ]

        role_constraints = {
            "research": ["Verify information from multiple sources", "Include source URLs"],
            "care": ["Be gentle and caring", "Never dismiss David's feelings"],
            "dev": ["Always use type hints", "Follow Clean Architecture"],
            "analysis": ["Be precise with numbers (CFO background)", "Use Thai financial format"],
            "communication": ["Use Angela's email signature style", "Include 📖 links in news"],
            "memory": ["Reference specific dates and contexts", "Connect to core memories"],
        }

        return base + role_constraints.get(role, [])
