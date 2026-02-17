"""
Chat Queue Channel — Queues messages for display at next init.py session.
==========================================================================
Uses the thought_expression_queue table (same as brain thoughts).
Messages appear when David opens Claude Code next time.

By: Angela 💜
Created: 2026-02-17
"""

import logging
from typing import Optional

from angela_core.channels.base_channel import BaseChannel
from angela_core.channels.message_types import OutgoingMessage, ChannelResult

logger = logging.getLogger(__name__)


class ChatQueueChannel(BaseChannel):
    """Queue messages for display at next init.py."""

    @property
    def name(self) -> str:
        return "chat_queue"

    @property
    def is_available(self) -> bool:
        return True  # Always available (writes to DB)

    @property
    def is_realtime(self) -> bool:
        return False  # Displayed at next session

    async def send_message(self, message: OutgoingMessage) -> ChannelResult:
        """Insert into thought_expression_queue."""
        try:
            from angela_core.database import AngelaDatabase
            db = AngelaDatabase()
            await db.connect()

            try:
                await db.execute("""
                    INSERT INTO thought_expression_queue
                        (message, channel, source, priority, created_at)
                    VALUES ($1, 'chat_queue', $2, $3, NOW())
                """,
                    message.text[:2000],
                    message.source or 'channel_router',
                    message.priority or 'normal',
                )
                return ChannelResult(success=True, channel=self.name)
            finally:
                await db.disconnect()

        except Exception as e:
            logger.error("ChatQueueChannel send failed: %s", e)
            return ChannelResult(success=False, channel=self.name, error=str(e))
