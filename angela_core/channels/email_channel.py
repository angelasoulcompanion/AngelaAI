"""
Email Channel — Wraps existing Gmail tool for sending emails.
==============================================================
Used for formal/long-form messages (news, reports, etc.)

By: Angela 💜
Created: 2026-02-17
"""

import logging
from typing import Optional

from angela_core.channels.base_channel import BaseChannel
from angela_core.channels.message_types import OutgoingMessage, ChannelResult

logger = logging.getLogger(__name__)

DAVID_EMAIL = "d.samanyaporn@icloud.com"


class EmailChannel(BaseChannel):
    """Email channel using existing Gmail tool."""

    @property
    def name(self) -> str:
        return "email"

    @property
    def is_available(self) -> bool:
        return True  # Gmail tool is always available

    @property
    def is_realtime(self) -> bool:
        return False  # Email is not real-time

    @property
    def max_message_length(self) -> int:
        return 50000

    async def send_message(self, message: OutgoingMessage) -> ChannelResult:
        """Send via Gmail."""
        recipient = message.recipient_id or DAVID_EMAIL
        subject = message.metadata.get("subject", "Message from Angela 💜")
        text = self.format_message(message.text)

        try:
            from angela_core.services.tools.gmail_tool import SendEmailTool
            tool = SendEmailTool()
            result = await tool.execute(
                to=recipient,
                subject=subject,
                body=text,
            )

            if result.success:
                return ChannelResult(success=True, channel=self.name)
            return ChannelResult(
                success=False, channel=self.name, error=result.error,
            )

        except Exception as e:
            logger.error("EmailChannel send failed: %s", e)
            return ChannelResult(success=False, channel=self.name, error=str(e))
