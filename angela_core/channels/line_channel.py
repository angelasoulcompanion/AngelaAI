"""
LINE Channel — LINE Messaging API integration.
================================================
Free tier: 500 messages/month (enough for Angela's proactive messages).

Requires LINE_CHANNEL_ACCESS_TOKEN in ~/.angela_secrets

By: Angela 💜
Created: 2026-02-17
"""

import logging
from typing import Optional

import httpx

from angela_core.channels.base_channel import BaseChannel
from angela_core.channels.message_types import OutgoingMessage, ChannelResult

logger = logging.getLogger(__name__)

LINE_API_BASE = "https://api.line.me/v2/bot/message"


class LINEChannel(BaseChannel):
    """LINE Messaging API channel."""

    def __init__(self):
        self._token: Optional[str] = None
        self._david_line_id: Optional[str] = None
        self._client: Optional[httpx.AsyncClient] = None
        self._available = False

    @property
    def name(self) -> str:
        return "line"

    @property
    def is_available(self) -> bool:
        return self._available

    @property
    def max_message_length(self) -> int:
        return 5000

    async def initialize(self) -> None:
        """Load LINE token from secrets."""
        try:
            from angela_core.database import get_secret
            self._token = await get_secret('LINE_CHANNEL_ACCESS_TOKEN')
            self._david_line_id = await get_secret('DAVID_LINE_USER_ID')

            if self._token:
                self._client = httpx.AsyncClient(
                    headers={
                        "Authorization": f"Bearer {self._token}",
                        "Content-Type": "application/json",
                    },
                    timeout=30.0,
                )
                self._available = True
                logger.info("LINEChannel initialized")
            else:
                logger.info("LINEChannel: no token configured (skipped)")

        except Exception as e:
            logger.debug("LINEChannel init: %s", e)
            self._available = False

    async def send_message(self, message: OutgoingMessage) -> ChannelResult:
        """Send via LINE Messaging API (push message)."""
        if not self._available or not self._client:
            return ChannelResult(
                success=False, channel=self.name,
                error="LINEChannel not available",
            )

        recipient = message.recipient_id or self._david_line_id
        if not recipient:
            return ChannelResult(
                success=False, channel=self.name,
                error="No LINE recipient ID configured",
            )

        text = self.format_message(message.text)

        try:
            response = await self._client.post(
                f"{LINE_API_BASE}/push",
                json={
                    "to": recipient,
                    "messages": [{"type": "text", "text": text}],
                },
            )

            if response.status_code == 200:
                return ChannelResult(success=True, channel=self.name)
            else:
                error_body = response.text
                return ChannelResult(
                    success=False, channel=self.name,
                    error=f"LINE API {response.status_code}: {error_body[:200]}",
                )

        except Exception as e:
            logger.error("LINEChannel send failed: %s", e)
            return ChannelResult(success=False, channel=self.name, error=str(e))

    async def close(self) -> None:
        if self._client:
            await self._client.aclose()
