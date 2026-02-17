"""
WebChat Channel — Delivers messages to connected WebSocket clients.
====================================================================
When WebChat UI is running, messages are pushed to connected clients.
Falls back to chat_queue if no clients connected.

By: Angela 💜
Created: 2026-02-17
"""

import logging
from typing import List, Optional

from angela_core.channels.base_channel import BaseChannel
from angela_core.channels.message_types import OutgoingMessage, ChannelResult

logger = logging.getLogger(__name__)


class WebChatChannel(BaseChannel):
    """WebChat channel — pushes to connected WebSocket clients."""

    def __init__(self):
        self._connected_clients: List = []

    @property
    def name(self) -> str:
        return "webchat"

    @property
    def is_available(self) -> bool:
        return len(self._connected_clients) > 0

    def add_client(self, websocket) -> None:
        """Register a connected WebSocket client."""
        self._connected_clients.append(websocket)

    def remove_client(self, websocket) -> None:
        """Remove a disconnected client."""
        self._connected_clients = [c for c in self._connected_clients if c != websocket]

    async def send_message(self, message: OutgoingMessage) -> ChannelResult:
        """Send to all connected WebSocket clients."""
        if not self._connected_clients:
            return ChannelResult(
                success=False, channel=self.name,
                error="No WebChat clients connected",
            )

        import json
        payload = json.dumps({
            "text": message.text,
            "sender": "angela",
            "source": message.source,
        })

        sent = 0
        for client in list(self._connected_clients):
            try:
                await client.send_text(payload)
                sent += 1
            except Exception:
                self.remove_client(client)

        if sent > 0:
            return ChannelResult(
                success=True, channel=self.name,
                metadata={"clients_sent": sent},
            )
        return ChannelResult(
            success=False, channel=self.name,
            error="All clients disconnected",
        )
