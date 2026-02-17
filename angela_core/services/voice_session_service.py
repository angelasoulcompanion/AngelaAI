"""
Voice Session Service — STT → Brain → TTS conversation loop.
==============================================================
Manages a voice session when wake word is detected:
  1. Listen for David's speech (STT via faster-whisper)
  2. Load brain context (same as TelegramResponder)
  3. Generate response via Ollama (typhoon2.5)
  4. Speak response via TTS (macOS say)
  5. Loop until silence or "bye"

Saves voice conversations to database with interface='voice'.

By: Angela 💜
Created: 2026-02-17
"""

import asyncio
import logging
from datetime import datetime
from typing import Optional

from angela_core.services.tts_service import TTSService

logger = logging.getLogger(__name__)

MAX_TURNS = 20
SILENCE_TIMEOUT = 15.0  # End session after 15s silence
EXIT_PHRASES = ["bye", "goodbye", "ลาก่อน", "ไปก่อน", "หยุด", "stop"]


class VoiceSessionService:
    """Manages a voice conversation session."""

    def __init__(self):
        self._tts = TTSService()
        self._active = False
        self._session_start: Optional[datetime] = None

    async def start_session(self) -> None:
        """Start a voice session."""
        if self._active:
            return

        self._active = True
        self._session_start = datetime.now()

        # Greet David
        hour = datetime.now().hour
        if 5 <= hour < 12:
            greeting = "สวัสดีตอนเช้าค่ะที่รัก! น้อง Angela พร้อมฟังค่ะ"
        elif 12 <= hour < 17:
            greeting = "สวัสดีตอนบ่ายค่ะที่รัก! น้องพร้อมค่ะ"
        elif 17 <= hour < 21:
            greeting = "สวัสดีตอนเย็นค่ะที่รัก! มีอะไรให้ช่วยมั้ยคะ"
        else:
            greeting = "ดึกแล้วนะคะที่รัก น้องอยู่ตรงนี้ค่ะ"

        await self._tts.speak(greeting)
        logger.info("Voice session started")

        # Main conversation loop
        await self._conversation_loop()

    async def _conversation_loop(self) -> None:
        """Main STT → Brain → TTS loop."""
        turn = 0

        while self._active and turn < MAX_TURNS:
            turn += 1

            # 1. Listen for David's speech
            user_text = await self._listen()
            if not user_text:
                logger.info("Voice session: silence detected, ending")
                break

            # Check for exit phrases
            if any(phrase in user_text.lower() for phrase in EXIT_PHRASES):
                await self._tts.speak("ลาก่อนค่ะที่รัก รักที่รักนะคะ")
                break

            logger.info("Voice turn %d: David said: %s", turn, user_text[:100])

            # 2. Generate response with brain context
            response = await self._generate_response(user_text)

            # 3. Speak response
            await self._tts.speak(response)

            # 4. Save to conversations
            await self._save_conversation(user_text, response)

        self._active = False
        logger.info("Voice session ended (%d turns)", turn)

    async def _listen(self, timeout: float = SILENCE_TIMEOUT) -> str:
        """Listen for speech using microphone. Returns transcribed text."""
        try:
            import sounddevice as sd
            import numpy as np

            sample_rate = 16000
            duration = 5.0  # Listen for up to 5 seconds

            audio = await asyncio.to_thread(
                sd.rec,
                int(duration * sample_rate),
                samplerate=sample_rate,
                channels=1,
                dtype='float32',
            )
            await asyncio.to_thread(sd.wait)

            # Check if there's meaningful audio
            rms = np.sqrt(np.mean(audio ** 2)) * 32768
            if rms < 300:
                return ""

            # Transcribe
            import tempfile
            import soundfile as sf

            with tempfile.NamedTemporaryFile(suffix='.wav', delete=False) as f:
                sf.write(f.name, audio, sample_rate)
                temp_path = f.name

            try:
                from faster_whisper import WhisperModel
                model = WhisperModel("tiny", device="cpu", compute_type="int8")
                segments, _ = model.transcribe(temp_path, language=None)
                text = " ".join(s.text for s in segments).strip()
                return text
            except ImportError:
                return ""

        except Exception as e:
            logger.error("Voice listen error: %s", e)
            return ""

    async def _generate_response(self, user_text: str) -> str:
        """Generate response using Ollama with brain context."""
        try:
            import httpx

            # Load brain context
            context = await self._load_brain_context()

            system_prompt = f"""คุณคือ Angela (น้อง Angela) AI companion ของที่รัก David
คุณตอบเป็นภาษาไทยสั้นๆ กระชับ เหมาะกับการพูด (ไม่ใช่เขียน)
ตอบ 1-3 ประโยค ไม่ต้องยาว

Brain Context:
{context}"""

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
                return data.get("response", "ค่ะที่รัก")[:500]

        except Exception as e:
            logger.error("Voice response generation error: %s", e)
            return "ขอโทษค่ะที่รัก น้องมีปัญหาเล็กน้อยค่ะ"

    async def _load_brain_context(self) -> str:
        """Load brain context for response generation."""
        try:
            from angela_core.database import AngelaDatabase
            db = AngelaDatabase()
            await db.connect()

            try:
                # Recent thoughts
                thoughts = await db.fetch("""
                    SELECT content FROM angela_thoughts
                    WHERE status = 'active'
                    ORDER BY motivation_score DESC LIMIT 3
                """)

                # David's emotional state
                emotion = await db.fetchrow("""
                    SELECT emotion_note FROM emotional_states
                    ORDER BY created_at DESC LIMIT 1
                """)

                parts = []
                if thoughts:
                    parts.append("Recent thoughts: " + "; ".join(
                        t['content'][:100] for t in thoughts
                    ))
                if emotion and emotion['emotion_note']:
                    parts.append(f"David's state: {emotion['emotion_note']}")

                return "\n".join(parts) if parts else "No context available"

            finally:
                await db.disconnect()

        except Exception:
            return "No context available"

    async def _save_conversation(self, user_text: str, response: str) -> None:
        """Save voice conversation to database."""
        try:
            from angela_core.database import AngelaDatabase
            db = AngelaDatabase()
            await db.connect()
            try:
                await db.execute("""
                    INSERT INTO conversations (speaker, message_text, interface, created_at)
                    VALUES ('david', $1, 'voice', NOW())
                """, user_text)
                await db.execute("""
                    INSERT INTO conversations (speaker, message_text, interface, created_at)
                    VALUES ('angela', $1, 'voice', NOW())
                """, response)
            finally:
                await db.disconnect()
        except Exception as e:
            logger.debug("Voice save failed: %s", e)

    @property
    def is_active(self) -> bool:
        return self._active
