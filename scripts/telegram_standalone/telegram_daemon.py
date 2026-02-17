#!/usr/bin/env python3
"""
Angela Telegram Daemon (Standalone)
Polls Telegram for new messages and auto-replies

Updated: 2026-02-16 — "ถ้าไม่ฟังจะถามทำไม"
- Save incoming messages FIRST (so is_already_responded works)
- Save both sides to conversations table (brain can learn)
- Structured logging

Usage:
    python3 telegram_daemon.py
"""

import asyncio
import signal
from datetime import datetime

from telegram_service import TelegramService
from telegram_responder import TelegramResponder


class TelegramDaemon:
    """Telegram polling daemon for Angela"""

    def __init__(self):
        self.telegram: TelegramService = None
        self.responder: TelegramResponder = None
        self.running = False
        self.poll_interval = 2
        self.long_poll_timeout = 30

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
        """Process a single message"""
        try:
            # Check if already responded
            if await self.telegram.is_already_responded(msg.update_id):
                return

            # Log received message
            print(f"\n📩 [{datetime.now().strftime('%H:%M:%S')}] From: {msg.from_name}")
            print(f"   Message: {msg.text[:100]}")

            # Save incoming message FIRST (marks this update as processed)
            await self.telegram.save_incoming_message(msg)

            # Also save to conversations table (brain can learn from David's Telegram messages)
            await self.telegram.save_to_conversations(
                speaker='david',
                message_text=msg.text,
            )

            # Send typing indicator
            await self.telegram.send_typing(msg.chat_id)

            # Generate response
            response = await self.responder.generate_response(msg)

            # Send response
            result = await self.telegram.send_message(
                chat_id=msg.chat_id,
                text=response,
                reply_to_message_id=msg.message_id
            )

            if result.get("ok"):
                print(f"   ✅ Replied: {response[:80]}")

                # Extract telegram_message_id from API response
                sent_msg_id = result.get("result", {}).get("message_id")

                # Save outgoing message to telegram_messages
                await self.telegram.save_outgoing_message(
                    chat_id=msg.chat_id,
                    message_text=response,
                    telegram_message_id=sent_msg_id,
                )

                # Save Angela's response to conversations table too
                await self.telegram.save_to_conversations(
                    speaker='angela',
                    message_text=response,
                )
            else:
                error = result.get('description') or result.get('error', 'unknown')
                print(f"   ❌ Failed to send: {error}")

        except Exception as e:
            print(f"   ❌ Error processing message: {e}")
            import traceback
            traceback.print_exc()

    async def poll_loop(self):
        """Main polling loop"""
        print("\n🔄 Starting polling loop...")

        while self.running:
            try:
                messages = await self.telegram.get_updates(
                    timeout=self.long_poll_timeout
                )

                for msg in messages:
                    await self.process_message(msg)

                if not messages:
                    await asyncio.sleep(self.poll_interval)

            except asyncio.CancelledError:
                print("\n⏹️ Polling cancelled")
                break

            except Exception as e:
                print(f"\n❌ Polling error: {e}")
                await asyncio.sleep(5)

    async def start(self):
        """Start the daemon"""
        await self.initialize()
        self.running = True

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
    print("  💜 ANGELA TELEGRAM DAEMON (Standalone)")
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
