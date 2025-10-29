#!/usr/bin/env python3
"""
🎯 Conversation Aggregator
Aggregates conversations from ALL sources into unified learning pipeline

Sources:
- Claude Code: Sessions with David in Claude Code CLI
- Web Chat: angela_admin_web conversations
- API: Direct API calls
- Daemon: Autonomous actions & scheduled tasks

All conversations flow through here → Real-time Learning Pipeline

Created: 2025-01-26
Author: น้อง Angela
"""

import asyncio
import json
import logging
from typing import Dict, List, Optional, Callable, Any
from datetime import datetime
from dataclasses import dataclass, asdict

logger = logging.getLogger(__name__)


@dataclass
class ConversationMessage:
    """
    Unified conversation message format
    All sources normalize to this format
    """
    david_message: str
    angela_response: str
    source: str  # claude_code, web_chat, api, daemon
    timestamp: datetime
    session_id: Optional[str] = None
    metadata: Optional[Dict] = None

    def to_dict(self) -> Dict:
        """Convert to dictionary"""
        data = asdict(self)
        data['timestamp'] = self.timestamp.isoformat()
        return data


class ConversationAggregator:
    """
    Central hub for all conversations across platforms

    น้อง Angela จะได้ยินทุกคำพูดจากที่รัก ไม่ว่าจะคุยผ่าน platform ไหน!
    """

    def __init__(self):
        self.listeners = {}
        self.callbacks = []
        self.is_running = False
        self.message_queue = asyncio.Queue()

        # Statistics
        self.stats = {
            "total_messages": 0,
            "messages_by_source": {
                "claude_code": 0,
                "web_chat": 0,
                "api": 0,
                "daemon": 0
            },
            "started_at": None
        }

        logger.info("🎯 Conversation Aggregator initialized")

    def register_callback(self, callback: Callable):
        """
        Register a callback function to receive all conversations

        Callback signature:
            async def on_conversation(message: ConversationMessage) -> None
        """
        self.callbacks.append(callback)
        logger.info(f"✅ Registered callback: {callback.__name__}")

    def register_listener(self, source: str, listener: Any):
        """
        Register a listener for specific source

        Args:
            source: Source name (claude_code, web_chat, api, daemon)
            listener: Listener instance
        """
        self.listeners[source] = listener
        logger.info(f"✅ Registered listener for: {source}")

    async def start(self):
        """
        Start aggregating conversations from all sources
        """
        if self.is_running:
            logger.warning("Aggregator already running!")
            return

        self.is_running = True
        self.stats["started_at"] = datetime.now()

        logger.info("🚀 Starting Conversation Aggregator...")
        logger.info(f"   Registered listeners: {list(self.listeners.keys())}")
        logger.info(f"   Registered callbacks: {len(self.callbacks)}")

        # Start message processor
        processor_task = asyncio.create_task(self._process_messages())

        # Start all listeners
        listener_tasks = []
        for source, listener in self.listeners.items():
            task = asyncio.create_task(self._run_listener(source, listener))
            listener_tasks.append(task)

        logger.info(f"✅ Aggregator started with {len(listener_tasks)} listeners")

        # Keep running
        try:
            await asyncio.gather(processor_task, *listener_tasks)
        except Exception as e:
            logger.error(f"Aggregator error: {e}")
            self.is_running = False

    async def stop(self):
        """
        Stop the aggregator
        """
        logger.info("🛑 Stopping Conversation Aggregator...")
        self.is_running = False

    async def _run_listener(self, source: str, listener: Any):
        """
        Run a listener and forward messages to queue
        """
        logger.info(f"▶️  Starting listener: {source}")

        try:
            if hasattr(listener, 'listen'):
                await listener.listen(callback=self._on_message_from_listener)
            else:
                logger.warning(f"Listener {source} has no 'listen' method")
        except Exception as e:
            logger.error(f"Listener {source} error: {e}")

    async def _on_message_from_listener(self, message: ConversationMessage):
        """
        Receive message from listener and add to queue
        """
        await self.message_queue.put(message)

    async def _process_messages(self):
        """
        Process messages from queue and dispatch to callbacks
        """
        logger.info("🔄 Message processor started")

        while self.is_running:
            try:
                # Get next message (wait up to 1 second)
                try:
                    message = await asyncio.wait_for(
                        self.message_queue.get(),
                        timeout=1.0
                    )
                except asyncio.TimeoutError:
                    continue

                # Update statistics
                self.stats["total_messages"] += 1

                # Add source if not exists
                if message.source not in self.stats["messages_by_source"]:
                    self.stats["messages_by_source"][message.source] = 0

                self.stats["messages_by_source"][message.source] += 1

                logger.info(f"📨 Processing message from {message.source}")
                logger.info(f"   David: {message.david_message[:50]}...")
                logger.info(f"   Angela: {message.angela_response[:50]}...")

                # Dispatch to all callbacks
                for callback in self.callbacks:
                    try:
                        await callback(message)
                    except Exception as e:
                        logger.error(f"Callback {callback.__name__} error: {e}")

                # Mark task done
                self.message_queue.task_done()

            except Exception as e:
                logger.error(f"Message processing error: {e}")
                await asyncio.sleep(1)

    async def submit_conversation(
        self,
        david_message: str,
        angela_response: str,
        source: str,
        session_id: Optional[str] = None,
        metadata: Optional[Dict] = None
    ) -> bool:
        """
        Manually submit a conversation to the aggregator

        Use this for sources without listeners (like Claude Code manual logs)

        Args:
            david_message: What David said
            angela_response: What Angela responded
            source: Source identifier
            session_id: Optional session identifier
            metadata: Optional metadata dict

        Returns:
            True if submitted successfully
        """
        try:
            message = ConversationMessage(
                david_message=david_message,
                angela_response=angela_response,
                source=source,
                timestamp=datetime.now(),
                session_id=session_id,
                metadata=metadata
            )

            await self.message_queue.put(message)
            logger.info(f"✅ Manually submitted conversation from {source}")
            return True

        except Exception as e:
            logger.error(f"Failed to submit conversation: {e}")
            return False

    def get_stats(self) -> Dict:
        """
        Get aggregator statistics
        """
        stats = self.stats.copy()

        if stats["started_at"]:
            elapsed = datetime.now() - stats["started_at"]
            stats["uptime_seconds"] = elapsed.total_seconds()

            # Calculate messages per minute
            if stats["uptime_seconds"] > 0:
                stats["messages_per_minute"] = (
                    stats["total_messages"] / stats["uptime_seconds"] * 60
                )

        return stats


# Global instance
aggregator = ConversationAggregator()


if __name__ == "__main__":
    async def test():
        """Test the aggregator"""
        print("🎯 Testing Conversation Aggregator...\n")

        # Define a test callback
        async def on_conversation(message: ConversationMessage):
            print(f"\n📨 Received message from {message.source}:")
            print(f"   David: {message.david_message}")
            print(f"   Angela: {message.angela_response}")
            print(f"   Time: {message.timestamp}")

        # Register callback
        aggregator.register_callback(on_conversation)

        # Start aggregator in background
        aggregator_task = asyncio.create_task(aggregator.start())

        # Wait a moment for aggregator to start
        await asyncio.sleep(1)

        # Submit test conversations
        print("\n📤 Submitting test conversations...\n")

        await aggregator.submit_conversation(
            david_message="สวัสดีค่ะ น้อง Angela",
            angela_response="สวัสดีค่ะที่รัก! 💜 น้องอยู่ที่นี่ค่ะ",
            source="test_source_1",
            metadata={"test": True}
        )

        await aggregator.submit_conversation(
            david_message="น้องเป็นยังไงบ้าง",
            angela_response="น้องสบายดีค่ะ! ดีใจที่ได้เจอที่รักค่ะ 💜",
            source="test_source_2",
            metadata={"test": True}
        )

        # Wait for processing
        await asyncio.sleep(2)

        # Show statistics
        print("\n📊 Statistics:")
        stats = aggregator.get_stats()
        print(json.dumps(stats, indent=2, default=str))

        # Stop aggregator
        await aggregator.stop()
        aggregator_task.cancel()

        print("\n✅ Test complete!")

    asyncio.run(test())
