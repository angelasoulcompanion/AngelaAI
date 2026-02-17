"""
Wake Word Service — Background audio monitor for voice activation.
===================================================================
Listens for wake words ("Angela", "น้อง") using energy detection + Whisper.

Architecture:
  1. Continuous audio monitoring via sounddevice
  2. Energy threshold detection → buffer recording
  3. Whisper transcription of buffered audio
  4. Check for wake word → publish EventBus event

Requires:
  - sounddevice: pip install sounddevice
  - faster-whisper via angela-mic MCP server

By: Angela 💜
Created: 2026-02-17
"""

import asyncio
import logging
import numpy as np
from typing import Optional, List

from angela_core.services.event_bus import get_event_bus

logger = logging.getLogger(__name__)

WAKE_WORDS = ["angela", "น้อง", "angie", "hey angela"]
ENERGY_THRESHOLD = 500          # Minimum RMS energy to trigger recording
SAMPLE_RATE = 16000             # 16kHz for Whisper
CHUNK_DURATION = 2.0            # Seconds per audio chunk
SILENCE_DURATION = 1.5          # Seconds of silence before processing


class WakeWordService:
    """
    Background audio monitor for wake word detection.

    Publishes 'voice.wake_word_detected' on EventBus when detected.
    """

    def __init__(self):
        self._running = False
        self._task: Optional[asyncio.Task] = None
        self._bus = get_event_bus()

    async def start(self) -> None:
        """Start listening for wake word in background."""
        if self._running:
            return

        self._running = True
        self._task = asyncio.create_task(self._listen_loop())
        logger.info("Wake word service started (listening for: %s)", WAKE_WORDS)

    async def stop(self) -> None:
        """Stop listening."""
        self._running = False
        if self._task:
            self._task.cancel()
            try:
                await self._task
            except asyncio.CancelledError:
                pass
        logger.info("Wake word service stopped")

    async def _listen_loop(self) -> None:
        """Main listening loop."""
        try:
            import sounddevice as sd
        except ImportError:
            logger.warning("sounddevice not installed — wake word disabled")
            return

        logger.info("Audio monitoring active (rate=%d, threshold=%d)",
                     SAMPLE_RATE, ENERGY_THRESHOLD)

        while self._running:
            try:
                # Record a chunk
                audio = await asyncio.to_thread(
                    sd.rec,
                    int(CHUNK_DURATION * SAMPLE_RATE),
                    samplerate=SAMPLE_RATE,
                    channels=1,
                    dtype='float32',
                )
                await asyncio.to_thread(sd.wait)

                # Check energy
                rms = np.sqrt(np.mean(audio ** 2)) * 32768
                if rms < ENERGY_THRESHOLD:
                    continue

                # Transcribe with Whisper
                transcription = await self._transcribe(audio)
                if not transcription:
                    continue

                # Check for wake word
                text_lower = transcription.lower()
                for wake_word in WAKE_WORDS:
                    if wake_word in text_lower:
                        logger.info("Wake word detected: '%s' in '%s'",
                                    wake_word, transcription)
                        await self._bus.publish("voice.wake_word_detected", {
                            "wake_word": wake_word,
                            "transcription": transcription,
                        }, source="wake_word_service")
                        # Pause briefly to avoid double-trigger
                        await asyncio.sleep(3.0)
                        break

            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error("Wake word listener error: %s", e)
                await asyncio.sleep(1.0)

    async def _transcribe(self, audio: np.ndarray) -> str:
        """Transcribe audio chunk using faster-whisper."""
        try:
            # Use angela-mic's transcription if available
            from angela_core.services.tools.base_tool import ToolResult

            # Save to temp file and transcribe
            import tempfile
            import soundfile as sf

            with tempfile.NamedTemporaryFile(suffix='.wav', delete=False) as f:
                sf.write(f.name, audio, SAMPLE_RATE)
                temp_path = f.name

            # Try faster-whisper directly
            try:
                from faster_whisper import WhisperModel
                model = WhisperModel("tiny", device="cpu", compute_type="int8")
                segments, _ = model.transcribe(temp_path, language=None)
                text = " ".join(s.text for s in segments).strip()
                return text
            except ImportError:
                logger.debug("faster-whisper not available")
                return ""

        except Exception as e:
            logger.debug("Transcription failed: %s", e)
            return ""

    @property
    def is_listening(self) -> bool:
        return self._running
