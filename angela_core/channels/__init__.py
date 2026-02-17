"""
Angela Channels — Multi-channel messaging gateway.
====================================================
All messaging goes through BaseChannel → ChannelRouter.
No more hardcoding TelegramService everywhere.

Channels:
  - TelegramChannel: Wrap existing TelegramService
  - LINEChannel: LINE Messaging API
  - EmailChannel: Wrap gmail tool
  - ChatQueueChannel: Wrap thought_expression_queue

Usage:
    from angela_core.channels import get_channel_router
    router = get_channel_router()
    result = await router.route(message, preference="auto")

By: Angela 💜
Created: 2026-02-17
"""

from angela_core.channels.base_channel import BaseChannel
from angela_core.channels.message_types import IncomingMessage, OutgoingMessage, ChannelResult
from angela_core.channels.channel_router import ChannelRouter, get_channel_router

__all__ = [
    'BaseChannel', 'IncomingMessage', 'OutgoingMessage', 'ChannelResult',
    'ChannelRouter', 'get_channel_router',
]
