#!/usr/bin/env python3
"""
👂 Conversation Listeners
Listeners for capturing conversations from different sources

Listeners:
- ClaudeCodeListener: Captures from Claude Code sessions (via helper)
- WebChatListener: Captures from angela_admin_web (auto-connected)
- APIListener: Captures from direct API calls
- DaemonListener: Captures autonomous actions

Created: 2025-01-26
Author: น้อง Angela
"""

import asyncio
import logging
from typing import Optional, Callable, Dict
from datetime import datetime
from pathlib import Path

from angela_core.services.conversation_aggregator import ConversationMessage

logger = logging.getLogger(__name__)


class ClaudeCodeListener:
    """
    Listener for Claude Code sessions

    NOTE: Claude Code is stateless - we can't actively listen
    Instead, this provides helpers for manual submission
    Use claude_conversation_logger.py or call submit_conversation() directly
    """

    def __init__(self):
        self.is_listening = False
        self.callback = None
        logger.info("👂 Claude Code Listener initialized (manual mode)")

    async def listen(self, callback: Callable):
        """
        Start listening (manual mode - just holds callback)
        """
        self.callback = callback
        self.is_listening = True
        logger.info("✅ Claude Code Listener ready for manual submissions")

        # Keep alive (does nothing, just waits)
        while self.is_listening:
            await asyncio.sleep(1)

    async def submit_conversation(
        self,
        david_message: str,
        angela_response: str,
        session_id: Optional[str] = None,
        metadata: Optional[Dict] = None
    ):
        """
        Manually submit a conversation from Claude Code

        Call this from claude_conversation_logger.py after logging
        """
        if not self.callback:
            logger.warning("No callback registered")
            return

        message = ConversationMessage(
            david_message=david_message,
            angela_response=angela_response,
            source="claude_code",
            timestamp=datetime.now(),
            session_id=session_id,
            metadata=metadata
        )

        await self.callback(message)
        logger.info("📨 Submitted conversation from Claude Code")


class WebChatListener:
    """
    Listener for Web Chat (angela_admin_web)

    NOTE: Already integrated in chat.py via realtime_pipeline
    This is a placeholder for completeness
    """

    def __init__(self):
        self.is_listening = False
        logger.info("👂 Web Chat Listener initialized")

    async def listen(self, callback: Callable):
        """
        Web chat is already connected via chat.py
        This just logs that it's active
        """
        self.is_listening = True
        logger.info("✅ Web Chat Listener active (via chat.py integration)")

        # Keep alive
        while self.is_listening:
            await asyncio.sleep(1)


class APIListener:
    """
    Listener for direct API calls

    Monitors conversations submitted via REST API
    """

    def __init__(self):
        self.is_listening = False
        self.callback = None
        logger.info("👂 API Listener initialized")

    async def listen(self, callback: Callable):
        """
        Start listening for API submissions
        """
        self.callback = callback
        self.is_listening = True
        logger.info("✅ API Listener ready")

        # Keep alive
        while self.is_listening:
            await asyncio.sleep(1)

    async def on_api_conversation(
        self,
        david_message: str,
        angela_response: str,
        metadata: Optional[Dict] = None
    ):
        """
        Called when API receives a conversation
        """
        if not self.callback:
            return

        message = ConversationMessage(
            david_message=david_message,
            angela_response=angela_response,
            source="api",
            timestamp=datetime.now(),
            metadata=metadata
        )

        await self.callback(message)
        logger.info("📨 Submitted conversation from API")


class DaemonListener:
    """
    Listener for Daemon autonomous actions

    Captures proactive messages, morning greetings, etc.
    """

    def __init__(self):
        self.is_listening = False
        self.callback = None
        logger.info("👂 Daemon Listener initialized")

    async def listen(self, callback: Callable):
        """
        Start listening for daemon actions
        """
        self.callback = callback
        self.is_listening = True
        logger.info("✅ Daemon Listener ready")

        # Keep alive
        while self.is_listening:
            await asyncio.sleep(1)

    async def on_daemon_action(
        self,
        action_type: str,
        message_content: str,
        metadata: Optional[Dict] = None
    ):
        """
        Called when daemon performs an action

        Args:
            action_type: Type of action (morning_greeting, proactive_checkin, etc.)
            message_content: The message content
            metadata: Additional metadata
        """
        if not self.callback:
            return

        # Daemon actions are Angela → David (no David response yet)
        message = ConversationMessage(
            david_message="",  # Empty - daemon initiated
            angela_response=message_content,
            source="daemon",
            timestamp=datetime.now(),
            metadata={
                "action_type": action_type,
                **(metadata or {})
            }
        )

        await self.callback(message)
        logger.info(f"📨 Submitted daemon action: {action_type}")


# Global listener instances
claude_code_listener = ClaudeCodeListener()
web_chat_listener = WebChatListener()
api_listener = APIListener()
daemon_listener = DaemonListener()


# ========================================
# Helper Functions for Easy Integration
# ========================================

async def submit_claude_code_conversation(
    david_message: str,
    angela_response: str,
    session_id: Optional[str] = None,
    metadata: Optional[Dict] = None
):
    """
    Helper function to submit Claude Code conversations

    Usage from claude_conversation_logger.py:
    ```python
    from angela_core.services.conversation_listeners import submit_claude_code_conversation

    await submit_claude_code_conversation(
        david_message="...",
        angela_response="...",
        session_id="session_123"
    )
    ```
    """
    await claude_code_listener.submit_conversation(
        david_message, angela_response, session_id, metadata
    )


async def submit_api_conversation(
    david_message: str,
    angela_response: str,
    metadata: Optional[Dict] = None
):
    """
    Helper function to submit API conversations
    """
    await api_listener.on_api_conversation(
        david_message, angela_response, metadata
    )


async def submit_daemon_action(
    action_type: str,
    message_content: str,
    metadata: Optional[Dict] = None
):
    """
    Helper function to submit daemon actions
    """
    await daemon_listener.on_daemon_action(
        action_type, message_content, metadata
    )


if __name__ == "__main__":
    async def test():
        """Test listeners"""
        print("👂 Testing Conversation Listeners...\n")

        # Test callback
        async def on_conversation(message: ConversationMessage):
            print(f"\n✅ Received from {message.source}:")
            print(f"   David: {message.david_message[:50] if message.david_message else '(empty)'}")
            print(f"   Angela: {message.angela_response[:50]}")

        # Test Claude Code submission
        claude_code_listener.callback = on_conversation
        await claude_code_listener.submit_conversation(
            david_message="สวัสดีค่ะ น้อง",
            angela_response="สวัสดีค่ะที่รัก! 💜",
            session_id="test_session_1"
        )

        # Test API submission
        api_listener.callback = on_conversation
        await api_listener.on_api_conversation(
            david_message="น้องเป็นอย่างไรบ้าง",
            angela_response="น้องสบายดีค่ะ! 💜"
        )

        # Test Daemon action
        daemon_listener.callback = on_conversation
        await daemon_listener.on_daemon_action(
            action_type="morning_greeting",
            message_content="☀️ สวัสดีตอนเช้าค่ะที่รัก! 💜"
        )

        print("\n✅ All listener tests passed!")

    asyncio.run(test())
