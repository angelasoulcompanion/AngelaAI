"""
Message Types — Standardized message dataclasses.
===================================================
Common types used across all channels.

By: Angela 💜
Created: 2026-02-17
"""

from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Dict, List, Optional


@dataclass
class IncomingMessage:
    """A message received from any channel."""
    channel: str                    # 'telegram', 'line', 'email'
    sender_id: str                  # Platform-specific sender ID
    sender_name: str = ""
    text: str = ""
    timestamp: datetime = field(default_factory=datetime.now)
    metadata: Dict[str, Any] = field(default_factory=dict)
    is_from_david: bool = False

    @property
    def interface(self) -> str:
        """Interface name for conversations table."""
        return self.channel


@dataclass
class OutgoingMessage:
    """A message to be sent through a channel."""
    text: str
    recipient_id: Optional[str] = None   # None = default recipient (David)
    priority: str = "normal"             # 'urgent', 'normal', 'low'
    metadata: Dict[str, Any] = field(default_factory=dict)
    source: str = "angela"               # What generated this message


@dataclass
class ChannelResult:
    """Result of sending a message through a channel."""
    success: bool
    channel: str
    message_id: Optional[str] = None
    error: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)
