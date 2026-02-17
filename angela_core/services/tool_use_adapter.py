"""
Tool Use Adapter — Convert ToolRegistry → Anthropic tool_use format.
==================================================================
Bridges Angela's tool system with Claude API's native tool_use.

Handles:
- Converting tool schemas → Anthropic format
- Parsing tool_use responses → execute via registry
- Multi-turn tool chains (up to max_steps)

By: Angela 💜
Created: 2026-02-17
"""

import json
import logging
from typing import Any, Dict, List, Optional, Tuple

from angela_core.services.tools.base_tool import ToolResult

logger = logging.getLogger(__name__)


class ToolUseAdapter:
    """Adapter between ToolRegistry and Anthropic tool_use API."""

    def __init__(self, registry):
        """
        Args:
            registry: ToolRegistry instance
        """
        self.registry = registry

    def get_anthropic_tools(self, category: Optional[str] = None) -> List[Dict[str, Any]]:
        """Get tools in Anthropic API format."""
        return self.registry.to_anthropic_tools(category)

    async def execute_tool_call(
        self, tool_name: str, tool_input: Dict[str, Any]
    ) -> ToolResult:
        """Execute a single tool call from Claude's response."""
        return await self.registry.execute(tool_name, **tool_input)

    def format_tool_result(self, tool_use_id: str, result: ToolResult) -> Dict[str, Any]:
        """Format ToolResult back into Anthropic tool_result message format."""
        return {
            "type": "tool_result",
            "tool_use_id": tool_use_id,
            "content": result.summary(),
            "is_error": not result.success,
        }

    async def process_response_tool_calls(
        self, response_content: List[Dict[str, Any]]
    ) -> Tuple[List[Dict[str, Any]], List[ToolResult]]:
        """
        Process all tool_use blocks in a Claude response.

        Returns (tool_result_messages, tool_results) for multi-turn.
        """
        tool_results_messages = []
        tool_results = []

        for block in response_content:
            if block.get("type") == "tool_use":
                tool_name = block["name"]
                tool_input = block.get("input", {})
                tool_use_id = block["id"]

                logger.info("Executing tool call: %s(%s)", tool_name, json.dumps(tool_input, ensure_ascii=False)[:200])

                result = await self.execute_tool_call(tool_name, tool_input)
                tool_results.append(result)
                tool_results_messages.append(
                    self.format_tool_result(tool_use_id, result)
                )

        return tool_results_messages, tool_results
