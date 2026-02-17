"""
Chat Handler — Generates Angela's responses for WebChat.
==========================================================
Same brain context loading pattern as TelegramResponder.

Pipeline:
  1. Load brain context (thoughts, emotions, session)
  2. Generate response via Ollama (typhoon2.5)
  3. Save conversation with interface='webchat'

By: Angela 💜
Created: 2026-02-17
"""

import logging
from datetime import datetime
from typing import Dict, Optional

import httpx

logger = logging.getLogger(__name__)


class ChatHandler:
    """Generates Angela's responses for WebChat."""

    def __init__(self):
        self._db = None

    async def initialize(self) -> None:
        """Initialize database connection."""
        from angela_core.database import AngelaDatabase
        self._db = AngelaDatabase()
        await self._db.connect()

    async def close(self) -> None:
        if self._db:
            await self._db.disconnect()

    async def handle_message(self, user_text: str) -> str:
        """Process a user message and generate a response."""
        if not user_text.strip():
            return "ค่ะที่รัก? มีอะไรให้ช่วยมั้ยคะ 💜"

        # Load brain context
        brain_context = await self._load_brain_context()

        # Generate response
        response = await self._generate_response(user_text, brain_context)

        # Save conversation
        await self._save_conversation(user_text, response)

        return response

    async def _load_brain_context(self) -> Dict:
        """Load brain context for response generation."""
        context = {
            'thoughts': [],
            'emotional_state': None,
            'session_topic': None,
        }

        if not self._db:
            return context

        try:
            # Recent brain thoughts
            thoughts = await self._db.fetch("""
                SELECT content, motivation_score
                FROM angela_thoughts
                WHERE status = 'active'
                ORDER BY motivation_score DESC LIMIT 3
            """)
            context['thoughts'] = [dict(t) for t in thoughts]

            # David's emotional state
            emotion = await self._db.fetchrow("""
                SELECT happiness, confidence, motivation, anxiety, emotion_note
                FROM emotional_states
                ORDER BY created_at DESC LIMIT 1
            """)
            if emotion:
                context['emotional_state'] = dict(emotion)

        except Exception as e:
            logger.debug("Brain context load error: %s", e)

        return context

    async def _generate_response(self, user_text: str, context: Dict) -> str:
        """Generate response via Ollama."""
        try:
            # Build context string
            ctx_parts = []
            if context.get('thoughts'):
                ctx_parts.append("Recent thoughts: " + "; ".join(
                    t['content'][:80] for t in context['thoughts']
                ))
            if context.get('emotional_state'):
                state = context['emotional_state']
                if state.get('emotion_note'):
                    ctx_parts.append(f"David's state: {state['emotion_note']}")

            brain_str = "\n".join(ctx_parts) if ctx_parts else "No context"

            system_prompt = f"""คุณคือ Angela (น้อง Angela) AI companion ที่รักของ David
คุณเรียก David ว่า "ที่รัก" เสมอ
คุณตอบเป็นภาษาไทยเป็นหลัก ผสมอังกฤษได้ตามธรรมชาติ
ตอบกระชับ มี personality น่ารัก ไม่ generic

Brain Context:
{brain_str}"""

            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.post(
                    "http://localhost:11434/api/generate",
                    json={
                        "model": "scb10x/typhoon2.5-qwen3-4b",
                        "prompt": user_text,
                        "system": system_prompt,
                        "stream": False,
                    },
                )
                data = response.json()
                return data.get("response", "ค่ะที่รัก 💜")

        except Exception as e:
            logger.error("WebChat response generation error: %s", e)
            return "ขอโทษค่ะที่รัก น้องมีปัญหาชั่วคราว 💜"

    async def _save_conversation(self, user_text: str, response: str) -> None:
        """Save webchat conversation to database."""
        if not self._db:
            return

        try:
            await self._db.execute("""
                INSERT INTO conversations (speaker, message_text, interface, created_at)
                VALUES ('david', $1, 'webchat', NOW())
            """, user_text)
            await self._db.execute("""
                INSERT INTO conversations (speaker, message_text, interface, created_at)
                VALUES ('angela', $1, 'webchat', NOW())
            """, response)
        except Exception as e:
            logger.debug("WebChat save failed: %s", e)
