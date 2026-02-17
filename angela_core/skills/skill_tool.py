"""
Skill Tool — Wraps skill handler functions into AngelaTool ABC.
================================================================
Bridges the gap between SKILL.md tool definitions and the ToolRegistry.

Each SkillToolDef from a parsed SKILL.md becomes a SkillTool(AngelaTool)
that can be registered in the ToolRegistry and executed by the AgentDispatcher.

By: Angela 💜
Created: 2026-02-17
"""

import logging
from typing import Any, Callable, Dict, Optional

from angela_core.services.tools.base_tool import AngelaTool, ToolResult
from angela_core.skills.skill_loader import AngelaSkill, SkillToolDef

logger = logging.getLogger(__name__)


class SkillTool(AngelaTool):
    """
    Wraps a skill handler function as an AngelaTool.

    Created dynamically from SkillToolDef + handler module.
    """

    def __init__(self, skill: AngelaSkill, tool_def: SkillToolDef):
        self._skill = skill
        self._tool_def = tool_def
        self._handler_func: Optional[Callable] = None

        # Resolve handler function
        if tool_def.handler_ref and '::' in tool_def.handler_ref:
            _, func_name = tool_def.handler_ref.split('::', 1)
            self._handler_func = skill.get_handler_func(func_name)

    @property
    def name(self) -> str:
        return f"{self._skill.name}.{self._tool_def.name}"

    @property
    def description(self) -> str:
        return self._tool_def.description

    @property
    def parameters_schema(self) -> Dict[str, Any]:
        properties = {}
        for param_name, param_type in self._tool_def.parameters.items():
            json_type = {
                'string': 'string', 'str': 'string',
                'int': 'integer', 'integer': 'integer',
                'float': 'number', 'number': 'number',
                'bool': 'boolean', 'boolean': 'boolean',
            }.get(param_type.lower(), 'string')

            properties[param_name] = {
                "type": json_type,
                "description": f"{param_name} parameter",
            }

        return {
            "type": "object",
            "properties": properties,
            "required": list(self._tool_def.parameters.keys()),
        }

    @property
    def category(self) -> str:
        return f"skill:{self._skill.name}"

    async def execute(self, **params) -> ToolResult:
        """Execute the skill handler function."""
        if self._handler_func is None:
            return ToolResult(
                success=False,
                error=f"No handler function for {self.name}",
            )

        try:
            import asyncio
            if asyncio.iscoroutinefunction(self._handler_func):
                result = await self._handler_func(**params)
            else:
                result = self._handler_func(**params)

            # Normalize result
            if isinstance(result, ToolResult):
                return result
            if isinstance(result, dict):
                return ToolResult(success=True, data=result)
            return ToolResult(success=True, data=str(result))

        except Exception as e:
            logger.error("Skill tool %s execution error: %s", self.name, e)
            return ToolResult(success=False, error=str(e))
