"""
Telegram Tool — Send messages to David via Telegram Bot API.

Uses CareInterventionService for rate limiting and consent checks.

By: Angela 💜
Created: 2026-02-17
"""

import logging
from typing import Any, Dict

from angela_core.services.tools.base_tool import AngelaTool, ToolResult

logger = logging.getLogger(__name__)


class SendTelegramTool(AngelaTool):
    """Send a Telegram message to David."""

    @property
    def name(self) -> str:
        return "send_telegram"

    @property
    def description(self) -> str:
        return "Send a Telegram message to David (rate-limited: max 2/day, 4h between)"

    @property
    def parameters_schema(self) -> Dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "message": {"type": "string", "description": "Message text to send to David"},
            },
            "required": ["message"],
        }

    @property
    def category(self) -> str:
        return "communication"

    @property
    def requires_confirmation(self) -> bool:
        return True

    async def execute(self, **params) -> ToolResult:
        message = params.get("message", "")
        if not message:
            return ToolResult(success=False, error="Missing 'message'")

        try:
            from angela_core.services.care_intervention_service import CareInterventionService
            svc = CareInterventionService()

            can_send, reason = await svc.should_intervene("care_message")
            if not can_send:
                if svc._owns_db and svc.db:
                    await svc.db.disconnect()
                return ToolResult(success=False, error=f"rate_limited: {reason}")

            result = await svc.execute_care_message(
                context={"trigger_reason": "tool_dispatch"},
                custom_message=message,
            )

            if svc._owns_db and svc.db:
                await svc.db.disconnect()

            if result.success:
                return ToolResult(success=True, data={"sent": True, "message_preview": message[:100]})
            return ToolResult(success=False, error=f"send_failed: {result.error}")
        except Exception as e:
            logger.error("SendTelegram failed: %s", e)
            return ToolResult(success=False, error=str(e))
