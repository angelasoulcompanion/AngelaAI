"""
Channel Router — Smart message routing across all channels.
=============================================================
Central router that decides which channel to use based on:
- Message priority (urgent→Telegram/LINE, normal→chat_queue, formal→email)
- Channel availability
- User preference
- Rate limits

Usage:
    router = get_channel_router()
    result = await router.route(OutgoingMessage("Hello!"), preference="auto")
    results = await router.broadcast(OutgoingMessage("News"), channels=["telegram", "email"])

By: Angela 💜
Created: 2026-02-17
"""

import logging
from typing import Any, Dict, List, Optional

from angela_core.channels.base_channel import BaseChannel
from angela_core.channels.message_types import OutgoingMessage, ChannelResult

logger = logging.getLogger(__name__)


class ChannelRouter:
    """
    Smart message routing across multiple channels.

    Priority-based auto-routing:
    - urgent → Telegram first, LINE fallback
    - normal → chat_queue (shown at init)
    - formal → email
    - low → chat_queue
    """

    def __init__(self):
        self._channels: Dict[str, BaseChannel] = {}
        self._initialized = False

    def register_channel(self, channel: BaseChannel) -> None:
        """Register a channel."""
        self._channels[channel.name] = channel
        logger.debug("Registered channel: %s", channel.name)

    def unregister_channel(self, name: str) -> None:
        """Unregister a channel."""
        self._channels.pop(name, None)

    def get_channel(self, name: str) -> Optional[BaseChannel]:
        """Get a channel by name."""
        return self._channels.get(name)

    @property
    def available_channels(self) -> List[str]:
        """List available channel names."""
        return [name for name, ch in self._channels.items() if ch.is_available]

    async def initialize_all(self) -> Dict[str, bool]:
        """Initialize all registered channels. Returns status map."""
        status = {}
        for name, channel in self._channels.items():
            try:
                await channel.initialize()
                status[name] = channel.is_available
            except Exception as e:
                logger.error("Channel %s init failed: %s", name, e)
                status[name] = False
        self._initialized = True
        return status

    async def route(self, message: OutgoingMessage,
                    preference: str = "auto") -> ChannelResult:
        """
        Route a message to the best channel.

        Args:
            message: The message to send
            preference: Channel name or "auto" for smart routing

        Returns:
            ChannelResult from the chosen channel
        """
        # Explicit channel preference
        if preference != "auto":
            channel = self._channels.get(preference)
            if channel and channel.is_available:
                return await channel.send_message(message)
            return ChannelResult(
                success=False, channel=preference,
                error=f"Channel '{preference}' not available",
            )

        # Auto-routing based on priority
        channel_name = self._select_channel(message)
        channel = self._channels.get(channel_name)

        if not channel or not channel.is_available:
            # Fallback to chat_queue (always available)
            channel = self._channels.get("chat_queue")
            if channel:
                return await channel.send_message(message)
            return ChannelResult(
                success=False, channel="none",
                error="No channels available",
            )

        return await channel.send_message(message)

    async def broadcast(self, message: OutgoingMessage,
                        channels: Optional[List[str]] = None) -> List[ChannelResult]:
        """
        Send a message to multiple channels.

        Args:
            message: The message to send
            channels: List of channel names (default: all available)

        Returns:
            List of ChannelResult from each channel
        """
        target_names = channels or self.available_channels
        results = []

        for name in target_names:
            channel = self._channels.get(name)
            if channel and channel.is_available:
                try:
                    result = await channel.send_message(message)
                    results.append(result)
                except Exception as e:
                    results.append(ChannelResult(
                        success=False, channel=name, error=str(e),
                    ))

        return results

    def _select_channel(self, message: OutgoingMessage) -> str:
        """Select the best channel based on message priority."""
        priority = message.priority

        if priority == "urgent":
            # Try Telegram first, then LINE, then chat_queue
            for ch in ["telegram", "line"]:
                if ch in self._channels and self._channels[ch].is_available:
                    return ch
            return "chat_queue"

        elif priority == "formal":
            if "email" in self._channels and self._channels["email"].is_available:
                return "email"
            return "chat_queue"

        elif priority == "low":
            return "chat_queue"

        else:  # normal
            return "chat_queue"

    async def close_all(self) -> None:
        """Close all channels."""
        for channel in self._channels.values():
            try:
                await channel.close()
            except Exception:
                pass

    def summary(self) -> Dict[str, Any]:
        """Get router summary."""
        return {
            "channels": {
                name: {
                    "available": ch.is_available,
                    "realtime": ch.is_realtime,
                }
                for name, ch in self._channels.items()
            },
            "available_count": len(self.available_channels),
            "initialized": self._initialized,
        }


# ── Global Singleton ──

_router: Optional[ChannelRouter] = None


def get_channel_router() -> ChannelRouter:
    """Get or create the global channel router."""
    global _router
    if _router is None:
        _router = ChannelRouter()

        # Register default channels
        from angela_core.channels.telegram_channel import TelegramChannel
        from angela_core.channels.line_channel import LINEChannel
        from angela_core.channels.email_channel import EmailChannel
        from angela_core.channels.chat_queue_channel import ChatQueueChannel

        _router.register_channel(TelegramChannel())
        _router.register_channel(LINEChannel())
        _router.register_channel(EmailChannel())
        _router.register_channel(ChatQueueChannel())

    return _router
