"""
Angela Telegram Service (Standalone)
Handles Telegram Bot API interactions

Updated: 2026-02-16 — Fix schema mismatch with actual telegram_messages table
Actual columns: message_id (uuid), telegram_update_id, telegram_message_id,
                chat_id, sender, message_text, direction, created_at
"""

import asyncio
import httpx
from typing import Dict, List, Optional, Any
from dataclasses import dataclass
from datetime import datetime

from database import AngelaDatabase, get_secret


@dataclass
class TelegramMessage:
    """Represents a Telegram message"""
    update_id: int
    message_id: int
    chat_id: int
    from_id: int
    from_name: str
    text: str
    date: datetime
    is_command: bool = False
    command: Optional[str] = None


class TelegramService:
    """Telegram Bot API service for Angela"""

    API_BASE = "https://api.telegram.org/bot{token}"

    # David's Telegram ID
    DAVID_TELEGRAM_ID = 7980404818

    def __init__(self, bot_token: str = None):
        self.bot_token = bot_token
        self.api_base = None
        self._client: Optional[httpx.AsyncClient] = None
        self._last_update_id: int = 0
        self._db: Optional[AngelaDatabase] = None

    async def initialize(self):
        """Initialize the service"""
        if not self.bot_token:
            # Get token from Neon our_secrets
            self.bot_token = await get_secret('telegram_bot_token')

            if not self.bot_token:
                raise ValueError("Telegram bot token not found in database!")

            # Initialize database connection for message storage (Neon)
            self._db = AngelaDatabase()
            await self._db.connect()

        self.api_base = self.API_BASE.format(token=self.bot_token)
        self._client = httpx.AsyncClient(timeout=60.0)

        # Load last processed update_id
        await self._load_last_update_id()

    async def _load_last_update_id(self):
        """Load the last processed update_id from database"""
        if self._db is None:
            self._db = AngelaDatabase()
            await self._db.connect()

        result = await self._db.fetchrow("""
            SELECT MAX(telegram_update_id) as last_id
            FROM telegram_messages
            WHERE direction = 'incoming'
        """)

        if result and result['last_id']:
            self._last_update_id = result['last_id']

    async def _api_call(self, method: str, **params) -> Dict[str, Any]:
        """Make a Telegram API call"""
        url = f"{self.api_base}/{method}"
        params = {k: v for k, v in params.items() if v is not None}

        try:
            response = await self._client.post(url, json=params)
            return response.json()
        except Exception as e:
            return {"ok": False, "error": str(e)}

    async def get_updates(self, timeout: int = 30) -> List[TelegramMessage]:
        """Long polling to get new messages"""
        response = await self._api_call(
            "getUpdates",
            offset=self._last_update_id + 1,
            timeout=timeout,
            allowed_updates=["message"]
        )

        messages = []

        if response.get("ok") and response.get("result"):
            for update in response["result"]:
                update_id = update["update_id"]
                self._last_update_id = max(self._last_update_id, update_id)

                if "message" in update:
                    msg = update["message"]
                    text = msg.get("text", "")

                    is_command = text.startswith("/")
                    command = text.split()[0][1:] if is_command else None

                    telegram_msg = TelegramMessage(
                        update_id=update_id,
                        message_id=msg["message_id"],
                        chat_id=msg["chat"]["id"],
                        from_id=msg.get("from", {}).get("id", 0),
                        from_name=msg.get("from", {}).get("first_name", "Unknown"),
                        text=text,
                        date=datetime.fromtimestamp(msg["date"]),
                        is_command=is_command,
                        command=command
                    )
                    messages.append(telegram_msg)

        return messages

    async def send_message(
        self,
        chat_id: int,
        text: str,
        parse_mode: str = "Markdown",
        reply_to_message_id: int = None
    ) -> Dict[str, Any]:
        """Send a message to a chat"""
        response = await self._api_call(
            "sendMessage",
            chat_id=chat_id,
            text=text,
            parse_mode=parse_mode,
            reply_to_message_id=reply_to_message_id
        )
        return response

    async def send_typing(self, chat_id: int):
        """Send typing indicator"""
        await self._api_call("sendChatAction", chat_id=chat_id, action="typing")

    async def is_already_responded(self, update_id: int) -> bool:
        """Check if we already processed this update (incoming message exists in DB)."""
        if self._db is None:
            self._db = AngelaDatabase()
            await self._db.connect()

        result = await self._db.fetchrow("""
            SELECT message_id FROM telegram_messages
            WHERE telegram_update_id = $1
            LIMIT 1
        """, update_id)

        return result is not None

    async def save_incoming_message(self, msg: TelegramMessage):
        """Save David's incoming message to telegram_messages."""
        if self._db is None:
            self._db = AngelaDatabase()
            await self._db.connect()

        await self._db.execute("""
            INSERT INTO telegram_messages
            (telegram_update_id, telegram_message_id, chat_id, sender, message_text, direction, created_at)
            VALUES ($1, $2, $3, 'david', $4, 'incoming', NOW())
        """, msg.update_id, msg.message_id, msg.chat_id, msg.text)

    async def save_outgoing_message(self, chat_id: int, message_text: str, telegram_message_id: int = None):
        """Save Angela's outgoing response to telegram_messages."""
        if self._db is None:
            self._db = AngelaDatabase()
            await self._db.connect()

        await self._db.execute("""
            INSERT INTO telegram_messages
            (telegram_message_id, chat_id, sender, message_text, direction, created_at)
            VALUES ($1, $2, 'angela', $3, 'outgoing', NOW())
        """, telegram_message_id, chat_id, message_text)

    async def save_to_conversations(self, speaker: str, message_text: str, session_id: str = 'telegram'):
        """Save message to conversations table so brain can learn from it."""
        if self._db is None:
            self._db = AngelaDatabase()
            await self._db.connect()

        await self._db.execute("""
            INSERT INTO conversations
            (session_id, speaker, message_text, topic, interface, created_at)
            VALUES ($1, $2, $3, 'telegram_chat', 'telegram', NOW())
        """, session_id, speaker, message_text)

    async def get_recent_incoming(self, limit: int = 10) -> List[Dict[str, Any]]:
        """Get recent incoming messages from David (for init.py display)."""
        if self._db is None:
            self._db = AngelaDatabase()
            await self._db.connect()

        rows = await self._db.fetch("""
            SELECT message_text, created_at
            FROM telegram_messages
            WHERE direction = 'incoming' AND sender = 'david'
            ORDER BY created_at DESC
            LIMIT $1
        """, limit)
        return [dict(r) for r in rows]

    async def is_david(self, from_id: int) -> bool:
        """Check if the sender is David"""
        return from_id == self.DAVID_TELEGRAM_ID

    async def close(self):
        """Close the HTTP client"""
        if self._client:
            await self._client.aclose()
        if self._db:
            await self._db.disconnect()
