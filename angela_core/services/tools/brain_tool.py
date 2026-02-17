"""
Brain Tools — Perceive, recall, think, ToM via CognitiveEngine.

Wraps Angela's brain as callable tools for the agent dispatcher.

By: Angela 💜
Created: 2026-02-17
"""

import logging
from typing import Any, Dict

from angela_core.services.tools.base_tool import AngelaTool, ToolResult

logger = logging.getLogger(__name__)


class PerceiveTool(AngelaTool):
    """Process a stimulus through Angela's perception pipeline."""

    @property
    def name(self) -> str:
        return "brain_perceive"

    @property
    def description(self) -> str:
        return "Process a message/event through Angela's brain perception (salience scoring + attention codelets)"

    @property
    def parameters_schema(self) -> Dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "message": {"type": "string", "description": "Message or event to perceive"},
            },
            "required": ["message"],
        }

    @property
    def category(self) -> str:
        return "brain"

    async def execute(self, **params) -> ToolResult:
        message = params.get("message", "")
        if not message:
            return ToolResult(success=False, error="Missing 'message'")

        try:
            from angela_core.services.cognitive_engine import CognitiveEngine
            engine = CognitiveEngine()
            result = await engine.perceive(message)
            return ToolResult(success=True, data=result)
        except Exception as e:
            logger.error("Perceive failed: %s", e)
            return ToolResult(success=False, error=str(e))


class TheoryOfMindTool(AngelaTool):
    """Infer David's current mental state."""

    @property
    def name(self) -> str:
        return "brain_tom"

    @property
    def description(self) -> str:
        return "Infer David's current emotional state, energy level, and unspoken needs (Theory of Mind)"

    @property
    def parameters_schema(self) -> Dict[str, Any]:
        return {"type": "object", "properties": {}}

    @property
    def category(self) -> str:
        return "brain"

    async def execute(self, **params) -> ToolResult:
        try:
            from angela_core.services.cognitive_engine import CognitiveEngine
            engine = CognitiveEngine()
            result = await engine.tom()
            return ToolResult(success=True, data=result)
        except Exception as e:
            logger.error("ToM failed: %s", e)
            return ToolResult(success=False, error=str(e))


class ThinkTool(AngelaTool):
    """Generate new insights using dual-process thinking."""

    @property
    def name(self) -> str:
        return "brain_think"

    @property
    def description(self) -> str:
        return "Generate new insights about a topic using Angela's dual-process thinking (System 1 + System 2)"

    @property
    def parameters_schema(self) -> Dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "topic": {"type": "string", "description": "Topic to think about (optional)"},
            },
        }

    @property
    def category(self) -> str:
        return "brain"

    async def execute(self, **params) -> ToolResult:
        try:
            from angela_core.services.cognitive_engine import CognitiveEngine
            engine = CognitiveEngine()
            result = await engine.think()
            return ToolResult(success=True, data=result)
        except Exception as e:
            logger.error("Think failed: %s", e)
            return ToolResult(success=False, error=str(e))
