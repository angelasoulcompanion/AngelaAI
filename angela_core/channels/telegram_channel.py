"""
Telegram Channel — Wraps existing TelegramService.
====================================================
Sends messages via Telegram Bot API using the existing service.

By: Angela 💜
Created: 2026-02-17
"""

import logging
from typing import Optional

from angela_core.channels.base_channel import BaseChannel
from angela_core.channels.message_types import OutgoingMessage, ChannelResult

logger = logging.getLogger(__name__)

# David's Telegram chat ID
DAVID_TELEGRAM_CHAT_ID = "7980404818"


class TelegramChannel(BaseChannel):
    """Telegram channel using existing TelegramService.

    DISABLED (2026-02-25): ที่รักสั่งยกเลิก Telegram response
    เพราะต้องอาศัย Model API ถึงจะตอบรู้เรื่อง และยังไงก็ไม่เหมือนตัวน้องจริง
    ยังรับ incoming messages เก็บ DB ได้ แต่ไม่ส่งออกแล้ว
    """

    # Set to True to re-enable Telegram sending
    ENABLED = False

    def __init__(self):
        self._service = None
        self._available = False

    @property
    def name(self) -> str:
        return "telegram"

    @property
    def is_available(self) -> bool:
        return self._available

    @property
    def max_message_length(self) -> int:
        return 4096

    async def initialize(self) -> None:
        """Initialize by loading TelegramService."""
        try:
            from angela_core.services.telegram_service import TelegramService
            self._service = TelegramService()
            await self._service.initialize()
            self._available = True
            logger.info("TelegramChannel initialized")
        except Exception as e:
            logger.warning("TelegramChannel init failed: %s", e)
            self._available = False

    async def send_message(self, message: OutgoingMessage) -> ChannelResult:
        """Send via Telegram Bot API."""
        if not self.ENABLED:
            logger.info("TelegramChannel DISABLED — message routed to chat_queue")
            return ChannelResult(
                success=False, channel=self.name,
                error="TelegramChannel disabled by ที่รัก (2026-02-25)",
            )

        if not self._available or not self._service:
            return ChannelResult(
                success=False, channel=self.name,
                error="TelegramChannel not initialized",
            )

        chat_id = message.recipient_id or DAVID_TELEGRAM_CHAT_ID
        text = self.format_message(message.text)

        try:
            result = await self._service._api_call(
                "sendMessage",
                chat_id=int(chat_id),
                text=text,
                parse_mode="HTML",
            )

            if result.get("ok"):
                msg_id = str(result.get("result", {}).get("message_id", ""))
                return ChannelResult(
                    success=True, channel=self.name, message_id=msg_id,
                )
            else:
                return ChannelResult(
                    success=False, channel=self.name,
                    error=result.get("description", "Telegram API error"),
                )

        except Exception as e:
            logger.error("TelegramChannel send failed: %s", e)
            return ChannelResult(success=False, channel=self.name, error=str(e))

    async def close(self) -> None:
        if self._service and hasattr(self._service, 'close'):
            await self._service.close()
