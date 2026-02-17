"""
Base Channel — Abstract base class for all messaging channels.
================================================================
Every channel (Telegram, LINE, Email, WebChat, etc.) implements this.

By: Angela 💜
Created: 2026-02-17
"""

from abc import ABC, abstractmethod
from typing import Optional

from angela_core.channels.message_types import OutgoingMessage, ChannelResult


class BaseChannel(ABC):
    """Abstract base class for messaging channels."""

    @property
    @abstractmethod
    def name(self) -> str:
        """Channel name (e.g. 'telegram', 'line', 'email')."""
        ...

    @property
    @abstractmethod
    def is_available(self) -> bool:
        """Whether this channel is currently available (configured, connected)."""
        ...

    @property
    def is_realtime(self) -> bool:
        """Whether this channel delivers messages in real-time."""
        return True

    @property
    def max_message_length(self) -> int:
        """Maximum message length for this channel."""
        return 4096

    @abstractmethod
    async def send_message(self, message: OutgoingMessage) -> ChannelResult:
        """Send a message through this channel."""
        ...

    def format_message(self, text: str) -> str:
        """Format message for this channel (truncate, escape, etc.)."""
        if len(text) > self.max_message_length:
            return text[:self.max_message_length - 3] + "..."
        return text

    async def initialize(self) -> None:
        """Initialize the channel (load tokens, connect, etc.)."""
        pass

    async def close(self) -> None:
        """Clean up channel resources."""
        pass
