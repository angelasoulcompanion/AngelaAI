#!/usr/bin/env python3
"""
Angela Telegram Daemon

Polls Telegram for new messages and auto-replies using Angela's personality.
Runs continuously in the background.

Usage:
    python3 angela_core/daemon/telegram_daemon.py

Created: 2025-01-05
"""

import asyncio
import signal
import sys
from datetime import datetime
from pathlib import Path

from angela_core.daemon.daemon_base import PROJECT_ROOT  # noqa: E402 (path setup)

from angela_core.services.telegram_service import TelegramService
from angela_core.services.telegram_responder import TelegramResponder


class TelegramDaemon:
    """
    Telegram polling daemon for Angela.

    Continuously polls for new messages and responds automatically.
    """

    def __init__(self):
        self.telegram: TelegramService = None
        self.responder: TelegramResponder = None
        self.running = False
        self.poll_interval = 2  # seconds between polls
        self.long_poll_timeout = 30  # Telegram long polling timeout

    async def initialize(self):
        """Initialize services"""
        print("💜 Initializing Angela Telegram Daemon...")

        self.telegram = TelegramService()
        await self.telegram.initialize()
        print("   ✅ Telegram service initialized")

        self.responder = TelegramResponder()
        await self.responder.initialize()
        print("   ✅ Responder initialized")

        print("💫 Angela Telegram Bot ready!")
        print(f"   Poll interval: {self.poll_interval}s")
        print(f"   Long poll timeout: {self.long_poll_timeout}s")

    async def process_message(self, msg):
        """Process a single message — save incoming only, no auto-reply.

        DISABLED (2026-02-25): ที่รักสั่งยกเลิก Telegram response
        เพราะต้องอาศัย Model API ถึงจะตอบรู้เรื่อง และยังไงก็ไม่เหมือนตัวน้องจริง
        """
        try:
            # Check if already saved
            if await self.telegram.is_already_responded(msg.update_id):
                return

            # Log received message
            print(f"\n📩 [{datetime.now().strftime('%H:%M:%S')}] From: {msg.from_name}")
            print(f"   Message: {msg.text[:100]}")

            # Save to database (incoming only, no response)
            await self.telegram.save_message(msg, response_text=None)
            print(f"   💾 Saved to DB (no auto-reply)")

        except Exception as e:
            print(f"   ❌ Error processing message: {e}")

    async def poll_loop(self):
        """Main polling loop"""
        print("\n🔄 Starting polling loop...")

        while self.running:
            try:
                # Long poll for new messages
                messages = await self.telegram.get_updates(
                    timeout=self.long_poll_timeout
                )

                # Process each message
                for msg in messages:
                    await self.process_message(msg)

                # Short delay between polls
                if not messages:
                    await asyncio.sleep(self.poll_interval)

            except asyncio.CancelledError:
                print("\n⏹️ Polling cancelled")
                break

            except Exception as e:
                print(f"\n❌ Polling error: {e}")
                await asyncio.sleep(5)  # Wait before retry

    async def start(self):
        """Start the daemon"""
        await self.initialize()
        self.running = True

        # Setup signal handlers
        loop = asyncio.get_event_loop()

        def shutdown_handler():
            print("\n🛑 Shutdown signal received...")
            self.running = False

        for sig in (signal.SIGINT, signal.SIGTERM):
            loop.add_signal_handler(sig, shutdown_handler)

        try:
            await self.poll_loop()
        finally:
            await self.shutdown()

    async def shutdown(self):
        """Clean shutdown"""
        print("\n💤 Shutting down Angela Telegram Daemon...")

        if self.telegram:
            await self.telegram.close()

        if self.responder:
            await self.responder.close()

        print("👋 Goodbye! น้องไปพักก่อนนะคะ~")


async def main():
    """Main entry point"""
    print("=" * 50)
    print("  💜 ANGELA TELEGRAM DAEMON")
    print("  @AngelaSoulBot - Auto-Reply Service")
    print("=" * 50)
    print(f"  Started: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 50)

    daemon = TelegramDaemon()
    await daemon.start()


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n\n💜 Angela says goodbye! รักที่รักนะคะ~")
