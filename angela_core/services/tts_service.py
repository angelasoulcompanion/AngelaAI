"""
TTS Service — Text-to-Speech using macOS `say` command.
=========================================================
Auto-detects Thai vs English text and selects appropriate voice.

Voices:
  - Thai: Kanya (macOS built-in)
  - English: Samantha (macOS built-in)

Features:
  - Async execution (non-blocking)
  - Queue-based (messages play in order)
  - Interrupt current speech

Usage:
    tts = TTSService()
    await tts.speak("สวัสดีค่ะที่รัก")  # Thai voice
    await tts.speak("Hello David!")      # English voice

By: Angela 💜
Created: 2026-02-17
"""

import asyncio
import logging
import re
from typing import Optional

logger = logging.getLogger(__name__)

THAI_VOICE = "Kanya"
ENGLISH_VOICE = "Samantha"
SPEECH_RATE = 180  # Words per minute


class TTSService:
    """macOS Text-to-Speech service."""

    def __init__(self):
        self._queue: asyncio.Queue = asyncio.Queue()
        self._current_process: Optional[asyncio.subprocess.Process] = None
        self._running = False
        self._processor_task: Optional[asyncio.Task] = None

    async def speak(self, text: str, voice: Optional[str] = None,
                    rate: int = SPEECH_RATE) -> None:
        """
        Speak text using macOS say command.

        Args:
            text: Text to speak
            voice: Override voice (default: auto-detect language)
            rate: Speech rate in words per minute
        """
        if not text.strip():
            return

        voice = voice or self._detect_voice(text)
        await self._queue.put((text, voice, rate))

        # Start processor if not running
        if not self._running:
            self._running = True
            self._processor_task = asyncio.create_task(self._process_queue())

    async def speak_immediate(self, text: str, voice: Optional[str] = None) -> None:
        """Speak immediately, interrupting current speech."""
        await self.stop()
        voice = voice or self._detect_voice(text)
        await self._execute_say(text, voice)

    async def stop(self) -> None:
        """Stop current speech."""
        if self._current_process:
            try:
                self._current_process.terminate()
                await self._current_process.wait()
            except ProcessLookupError:
                pass
            self._current_process = None

    async def _process_queue(self) -> None:
        """Process queued speech in order."""
        while self._running:
            try:
                text, voice, rate = await asyncio.wait_for(
                    self._queue.get(), timeout=1.0
                )
                await self._execute_say(text, voice, rate)
            except asyncio.TimeoutError:
                if self._queue.empty():
                    self._running = False
                    break
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error("TTS queue error: %s", e)

    async def _execute_say(self, text: str, voice: str,
                           rate: int = SPEECH_RATE) -> None:
        """Execute macOS say command."""
        # Sanitize text for shell
        clean_text = text.replace('"', '\\"').replace("'", "\\'")
        clean_text = clean_text[:1000]  # Cap length

        try:
            self._current_process = await asyncio.create_subprocess_exec(
                "say", "-v", voice, "-r", str(rate), clean_text,
                stdout=asyncio.subprocess.DEVNULL,
                stderr=asyncio.subprocess.DEVNULL,
            )
            await self._current_process.wait()
            self._current_process = None
        except Exception as e:
            logger.error("TTS say failed: %s", e)

    def _detect_voice(self, text: str) -> str:
        """Detect if text is Thai or English and return appropriate voice."""
        # Count Thai characters
        thai_chars = len(re.findall(r'[\u0E00-\u0E7F]', text))
        total_alpha = len(re.findall(r'[a-zA-Z\u0E00-\u0E7F]', text))

        if total_alpha == 0:
            return ENGLISH_VOICE

        thai_ratio = thai_chars / total_alpha
        return THAI_VOICE if thai_ratio > 0.3 else ENGLISH_VOICE

    @property
    def is_speaking(self) -> bool:
        return self._current_process is not None
