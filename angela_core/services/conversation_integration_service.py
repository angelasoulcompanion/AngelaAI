#!/usr/bin/env python3
"""
🔗 Conversation Integration Service
Integrates all conversation capture components into unified system

Components:
- Listeners (Claude Code, Web Chat, API, Daemon)
- Aggregator (message routing and normalization)
- Real-time Pipeline (immediate learning)

Flow:
Conversation → Listener → Aggregator → Pipeline → Knowledge Graph

Created: 2025-01-26
Author: น้อง Angela
"""

import asyncio
import logging
from typing import Dict, Optional
from datetime import datetime

from angela_core.services.conversation_listeners import (
    claude_code_listener,
    web_chat_listener,
    api_listener,
    daemon_listener
)
from angela_core.services.conversation_aggregator import (
    aggregator,
    ConversationMessage
)
from angela_core.services.realtime_learning_service import realtime_pipeline
from angela_core.services.background_learning_workers import background_workers

logger = logging.getLogger(__name__)


class ConversationIntegrationService:
    """
    Unified conversation capture and learning system

    น้อง Angela จะได้เรียนรู้จากทุกการสนทนาแบบ real-time!
    """

    def __init__(self):
        self.is_running = False
        self.aggregator = aggregator
        self.pipeline = realtime_pipeline

        # Listeners
        self.listeners = {
            "claude_code": claude_code_listener,
            "web_chat": web_chat_listener,
            "api": api_listener,
            "daemon": daemon_listener
        }

        logger.info("🔗 Conversation Integration Service initialized")

    async def start(self):
        """
        Start the integrated conversation capture system
        """
        if self.is_running:
            logger.warning("Integration service already running!")
            return

        logger.info("🚀 Starting Conversation Integration Service...")

        # Step 1: Start background workers
        await background_workers.start()
        logger.info(f"   🔄 Background workers: {background_workers.num_workers} running")

        # Step 2: Register callback with aggregator
        self.aggregator.register_callback(self._on_aggregated_conversation)

        # Step 3: Register listeners with aggregator
        for source, listener in self.listeners.items():
            self.aggregator.register_listener(source, listener)

        # Step 4: Start aggregator
        aggregator_task = asyncio.create_task(self.aggregator.start())

        self.is_running = True
        logger.info("✅ Conversation Integration Service started!")
        logger.info(f"   📡 Listening to: {list(self.listeners.keys())}")

        # Keep running
        try:
            await aggregator_task
        except Exception as e:
            logger.error(f"Integration service error: {e}")
            self.is_running = False

    async def stop(self):
        """
        Stop the integration service
        """
        logger.info("🛑 Stopping Conversation Integration Service...")
        await self.aggregator.stop()
        await background_workers.stop()
        self.is_running = False

    async def _on_aggregated_conversation(self, message: ConversationMessage):
        """
        Callback when aggregator receives a conversation

        This forwards to real-time learning pipeline
        """
        try:
            logger.info(f"🧠 Processing conversation from {message.source}")

            # Send to real-time learning pipeline
            result = await self.pipeline.process_conversation(
                david_message=message.david_message,
                angela_response=message.angela_response,
                source=message.source,
                metadata={
                    "session_id": message.session_id,
                    **(message.metadata or {})
                }
            )

            logger.info(f"✅ Learning complete: {result.get('concepts_extracted', 0)} concepts")

        except Exception as e:
            logger.error(f"Failed to process conversation: {e}")

    async def submit_conversation(
        self,
        david_message: str,
        angela_response: str,
        source: str,
        session_id: Optional[str] = None,
        metadata: Optional[Dict] = None
    ) -> bool:
        """
        Manually submit a conversation (for Claude Code, etc.)

        Args:
            david_message: What David said
            angela_response: What Angela responded
            source: Source identifier (claude_code, web_chat, api, daemon)
            session_id: Optional session ID
            metadata: Optional metadata

        Returns:
            True if submitted successfully
        """
        try:
            # Submit to aggregator
            success = await self.aggregator.submit_conversation(
                david_message=david_message,
                angela_response=angela_response,
                source=source,
                session_id=session_id,
                metadata=metadata
            )

            if success:
                logger.info(f"✅ Submitted conversation from {source}")
            else:
                logger.warning(f"⚠️ Failed to submit conversation from {source}")

            return success

        except Exception as e:
            logger.error(f"Error submitting conversation: {e}")
            return False

    def get_stats(self) -> Dict:
        """
        Get integration statistics
        """
        return {
            "is_running": self.is_running,
            "aggregator_stats": self.aggregator.get_stats(),
            "pipeline_metrics": self.pipeline.get_metrics(),
            "background_workers": background_workers.get_stats(),
            "active_listeners": list(self.listeners.keys())
        }


# Global instance
integration_service = ConversationIntegrationService()


# ========================================
# Helper Functions for Easy Integration
# ========================================

async def submit_conversation(
    david_message: str,
    angela_response: str,
    source: str,
    session_id: Optional[str] = None,
    metadata: Optional[Dict] = None
) -> bool:
    """
    Global helper to submit conversations

    Usage from anywhere:
    ```python
    from angela_core.services.conversation_integration_service import submit_conversation

    await submit_conversation(
        david_message="...",
        angela_response="...",
        source="claude_code",
        session_id="session_123"
    )
    ```
    """
    return await integration_service.submit_conversation(
        david_message, angela_response, source, session_id, metadata
    )


async def get_integration_stats() -> Dict:
    """
    Get current integration statistics
    """
    return integration_service.get_stats()


if __name__ == "__main__":
    async def test():
        """Test the integration service"""
        print("🔗 Testing Conversation Integration Service...\n")

        # Start integration service in background
        service_task = asyncio.create_task(integration_service.start())

        # Wait for service to start
        await asyncio.sleep(2)

        print("📤 Submitting test conversations...\n")

        # Test 1: Claude Code conversation
        await integration_service.submit_conversation(
            david_message="สวัสดีค่ะ น้อง Angela",
            angela_response="สวัสดีค่ะที่รัก! 💜 น้องอยู่ที่นี่ค่ะ",
            source="claude_code",
            session_id="test_claude_code_1",
            metadata={"test": True}
        )

        # Test 2: Web Chat conversation
        await integration_service.submit_conversation(
            david_message="น้องเป็นยังไงบ้าง",
            angela_response="น้องสบายดีค่ะ! ดีใจที่ได้คุยกับที่รักค่ะ 💜",
            source="web_chat",
            metadata={"test": True, "model": "claude-sonnet-4"}
        )

        # Test 3: Daemon action
        await integration_service.submit_conversation(
            david_message="",  # Empty - daemon initiated
            angela_response="☀️ สวัสดีตอนเช้าค่ะที่รัก! 💜 น้องหวังว่าที่รักจะมีวันที่ดีนะคะ",
            source="daemon",
            metadata={"action_type": "morning_greeting"}
        )

        # Wait for processing
        await asyncio.sleep(5)

        # Show statistics
        print("\n📊 Integration Statistics:")
        stats = integration_service.get_stats()
        print(f"   Running: {stats['is_running']}")
        print(f"   Active Listeners: {stats['active_listeners']}")
        print(f"   Total Messages: {stats['aggregator_stats']['total_messages']}")
        print(f"   Messages by Source: {stats['aggregator_stats']['messages_by_source']}")
        print(f"   Pipeline Metrics: {stats['pipeline_metrics']}")

        # Stop service
        await integration_service.stop()
        service_task.cancel()

        print("\n✅ Integration test complete!")

    asyncio.run(test())
