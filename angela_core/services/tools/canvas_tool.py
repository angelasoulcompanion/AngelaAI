"""
Canvas Tool — Render dynamic cards in WebChat.
================================================
By: Angela 💜
Created: 2026-02-17
"""

import logging
from typing import Any, Dict

from angela_core.services.tools.base_tool import AngelaTool, ToolResult

logger = logging.getLogger(__name__)


class RenderCardTool(AngelaTool):
    """Render a dynamic card in WebChat."""

    @property
    def name(self) -> str:
        return "render_card"

    @property
    def description(self) -> str:
        return "Render a dynamic visual card in WebChat UI (info, metric, chart, action)"

    @property
    def parameters_schema(self) -> Dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "card_type": {
                    "type": "string",
                    "description": "Card type: info, metric, chart, action",
                },
                "data": {
                    "type": "object",
                    "description": "Card data (title, body, value, items, etc.)",
                },
            },
            "required": ["card_type", "data"],
        }

    @property
    def category(self) -> str:
        return "ui"

    async def execute(self, **params) -> ToolResult:
        card_type = params.get("card_type", "info")
        data = params.get("data", {})

        try:
            from angela_core.webchat.canvas_renderer import render_card
            html = render_card(card_type, data)
            return ToolResult(success=True, data={"html": html, "type": card_type})
        except Exception as e:
            return ToolResult(success=False, error=str(e))
