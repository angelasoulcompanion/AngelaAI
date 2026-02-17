"""
Skill Registry — Central registry for all loaded skills.
=========================================================
Singleton that manages skill lifecycle: load, register, unregister, list.
Connects skills to ToolRegistry (for tool execution) and EventBus (for events).

Usage:
    registry = get_skill_registry()
    await registry.load_all_skills()
    skill = registry.get("weather_checker")

By: Angela 💜
Created: 2026-02-17
"""

import json
import logging
import time
from pathlib import Path
from typing import Any, Dict, List, Optional

from angela_core.skills.skill_loader import AngelaSkill, SkillLoader
from angela_core.skills.skill_tool import SkillTool
from angela_core.skills.skill_scheduler import SkillScheduler

logger = logging.getLogger(__name__)

# Default skills directory (project root / skills)
DEFAULT_SKILLS_DIR = Path(__file__).parent.parent.parent / "skills"


class SkillRegistry:
    """
    Central registry for Angela's skills.

    Manages:
    - Loading skills from directory
    - Registering skill tools with ToolRegistry
    - Connecting skill event triggers to EventBus
    - Scheduling skill execution
    """

    def __init__(self):
        self._skills: Dict[str, AngelaSkill] = {}
        self._loader = SkillLoader()
        self._scheduler = SkillScheduler()
        self._initialized = False

    async def load_all_skills(self, skills_dir: Optional[Path] = None) -> int:
        """
        Load all skills from the skills directory.
        Returns count of skills loaded.
        """
        skills_dir = skills_dir or DEFAULT_SKILLS_DIR

        if not skills_dir.exists():
            logger.info("Skills directory not found: %s", skills_dir)
            return 0

        skills = self._loader.load_all_from_dir(skills_dir)

        for skill in skills:
            if skill.enabled:
                self._register_skill(skill)

        self._initialized = True
        logger.info("Skill registry loaded: %d skills from %s",
                     len(self._skills), skills_dir)
        return len(self._skills)

    def _register_skill(self, skill: AngelaSkill) -> None:
        """Register a skill and connect it to ToolRegistry + EventBus."""
        self._skills[skill.name] = skill

        # Register skill tools with ToolRegistry
        self._register_skill_tools(skill)

        # Register schedule triggers with SkillScheduler
        sched_count = self._scheduler.register_skill(skill)

        # Register event triggers with EventBus
        event_count = self._register_event_triggers(skill)

        logger.info("Registered skill '%s': %d tools, %d schedules, %d events",
                     skill.name, len(skill.tools), sched_count, event_count)

    def _register_skill_tools(self, skill: AngelaSkill) -> None:
        """Register skill's tools with the global ToolRegistry."""
        try:
            from angela_core.services.tool_registry import get_registry
            registry = get_registry()

            for tool_def in skill.tools:
                skill_tool = SkillTool(skill, tool_def)
                registry.register(skill_tool)
                logger.debug("Registered skill tool: %s", skill_tool.name)

        except Exception as e:
            logger.error("Failed to register tools for skill %s: %s", skill.name, e)

    def _unregister_skill_tools(self, skill_name: str) -> None:
        """Remove a skill's tools from the global ToolRegistry."""
        try:
            from angela_core.services.tool_registry import get_registry
            registry = get_registry()

            # Find and remove tools with this skill's category
            to_remove = [
                name for name, tool in registry._tools.items()
                if tool.category == f"skill:{skill_name}"
            ]
            for name in to_remove:
                registry.unregister(name)

        except Exception as e:
            logger.error("Failed to unregister tools for skill %s: %s", skill_name, e)

    def _register_event_triggers(self, skill: AngelaSkill) -> int:
        """Subscribe skill event triggers to the EventBus. Returns count."""
        count = 0
        try:
            from angela_core.services.event_bus import get_event_bus
            bus = get_event_bus()

            for trigger in skill.event_triggers:
                # Create a closure that captures skill and trigger
                def _make_handler(s=skill, t=trigger):
                    async def handler(event):
                        await self._execute_skill_event(s, t, event.data)
                    return handler

                bus.subscribe(trigger.value, _make_handler())
                count += 1

        except Exception as e:
            # EventBus may not be running (e.g. during tests)
            logger.debug("Could not register event triggers for %s: %s", skill.name, e)

        return count

    async def _execute_skill_event(self, skill: AngelaSkill, trigger, data: dict) -> None:
        """Execute a skill in response to an event."""
        logger.info("Skill '%s' triggered by event: %s", skill.name, trigger.value)

        # Find and execute the first tool, or call a default handler
        if skill.tools:
            tool_def = skill.tools[0]
            func_name = tool_def.handler_ref.split('::')[-1] if '::' in tool_def.handler_ref else None
            if func_name:
                handler = skill.get_handler_func(func_name)
                if handler:
                    try:
                        import asyncio
                        if asyncio.iscoroutinefunction(handler):
                            await handler(**data)
                        else:
                            handler(**data)
                    except Exception as e:
                        logger.error("Skill event handler error: %s", e)

    # ── CRUD ──

    def get(self, skill_name: str) -> Optional[AngelaSkill]:
        """Get a skill by name."""
        return self._skills.get(skill_name)

    def list_skills(self) -> List[Dict[str, Any]]:
        """List all registered skills."""
        return [
            {
                "name": s.name,
                "description": s.description,
                "version": s.version,
                "enabled": s.enabled,
                "triggers": len(s.triggers),
                "tools": len(s.tools),
                "source": str(s.source_path) if s.source_path else None,
            }
            for s in self._skills.values()
        ]

    def unregister(self, skill_name: str) -> bool:
        """Unregister a skill and remove its tools."""
        if skill_name not in self._skills:
            return False

        self._unregister_skill_tools(skill_name)
        self._scheduler.unregister_skill(skill_name)
        del self._skills[skill_name]
        return True

    @property
    def scheduler(self) -> SkillScheduler:
        return self._scheduler

    @property
    def skill_count(self) -> int:
        return len(self._skills)

    def summary(self) -> Dict[str, Any]:
        """Get registry summary."""
        return {
            "total_skills": self.skill_count,
            "skills": [s.name for s in self._skills.values()],
            "scheduler": self._scheduler.summary(),
        }

    async def check_and_run_scheduled(self) -> List[Dict]:
        """Check for due scheduled skills and run them. Called by daemon."""
        due = self._scheduler.get_due_skills()
        results = []

        for skill_name, trigger in due:
            skill = self._skills.get(skill_name)
            if not skill:
                continue

            start = time.time()
            try:
                await self._execute_skill_event(skill, trigger, {})
                elapsed = (time.time() - start) * 1000
                self._scheduler.mark_completed(skill_name, trigger)
                results.append({
                    "skill": skill_name,
                    "trigger": trigger.value,
                    "success": True,
                    "time_ms": elapsed,
                })
            except Exception as e:
                elapsed = (time.time() - start) * 1000
                logger.error("Scheduled skill %s failed: %s", skill_name, e)
                self._scheduler.mark_completed(skill_name, trigger)
                results.append({
                    "skill": skill_name,
                    "trigger": trigger.value,
                    "success": False,
                    "error": str(e),
                    "time_ms": elapsed,
                })

        return results

    async def sync_to_db(self, db) -> None:
        """Persist skills to database."""
        for skill in self._skills.values():
            try:
                await db.execute("""
                    INSERT INTO angela_skills
                        (skill_name, description, version, enabled, source, config)
                    VALUES ($1, $2, $3, $4, $5, $6)
                    ON CONFLICT (skill_name) DO UPDATE SET
                        description = EXCLUDED.description,
                        version = EXCLUDED.version,
                        enabled = EXCLUDED.enabled,
                        config = EXCLUDED.config
                """,
                    skill.name, skill.description, skill.version,
                    skill.enabled, str(skill.source_path) if skill.source_path else 'local',
                    json.dumps(skill.config, ensure_ascii=False),
                )
            except Exception as e:
                logger.debug("Failed to sync skill %s to DB: %s", skill.name, e)

    async def log_execution(self, db, skill_name: str, trigger_type: str,
                            trigger_data: dict, result_summary: str,
                            success: bool, time_ms: float) -> None:
        """Log skill execution to database."""
        try:
            await db.execute("""
                INSERT INTO skill_execution_log
                    (skill_name, trigger_type, trigger_data, result_summary,
                     success, execution_time_ms)
                VALUES ($1, $2, $3, $4, $5, $6)
            """,
                skill_name, trigger_type,
                json.dumps(trigger_data, ensure_ascii=False, default=str),
                result_summary[:500] if result_summary else '',
                success, time_ms,
            )
        except Exception as e:
            logger.debug("Failed to log skill execution: %s", e)


# ── Global Singleton ──

_skill_registry: Optional[SkillRegistry] = None


def get_skill_registry() -> SkillRegistry:
    """Get or create the global skill registry."""
    global _skill_registry
    if _skill_registry is None:
        _skill_registry = SkillRegistry()
    return _skill_registry
