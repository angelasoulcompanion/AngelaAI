"""
Voice Tools — AngelaTool wrappers for voice services.
=======================================================
Tools:
  - speak: Speak text using TTS
  - listen: Listen and transcribe speech
  - start_voice_session: Start a voice conversation loop

By: Angela 💜
Created: 2026-02-17
"""

import logging
from typing import Any, Dict

from angela_core.services.tools.base_tool import AngelaTool, ToolResult

logger = logging.getLogger(__name__)


class SpeakTool(AngelaTool):
    """Speak text using macOS TTS."""

    @property
    def name(self) -> str:
        return "speak"

    @property
    def description(self) -> str:
        return "Speak text aloud using macOS text-to-speech (auto-detects Thai/English)"

    @property
    def parameters_schema(self) -> Dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "text": {"type": "string", "description": "Text to speak"},
                "voice": {"type": "string", "description": "Voice name (default: auto-detect)"},
            },
            "required": ["text"],
        }

    @property
    def category(self) -> str:
        return "voice"

    async def execute(self, **params) -> ToolResult:
        text = params.get("text", "")
        voice = params.get("voice")

        if not text:
            return ToolResult(success=False, error="Missing 'text'")

        try:
            from angela_core.services.tts_service import TTSService
            tts = TTSService()
            await tts.speak(text, voice=voice)
            return ToolResult(success=True, data={"spoken": text[:100]})
        except Exception as e:
            return ToolResult(success=False, error=str(e))


class ListenTool(AngelaTool):
    """Listen and transcribe speech."""

    @property
    def name(self) -> str:
        return "listen"

    @property
    def description(self) -> str:
        return "Listen through microphone and transcribe speech to text"

    @property
    def parameters_schema(self) -> Dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "duration_seconds": {"type": "integer", "description": "How long to listen (default: 5)"},
            },
            "required": [],
        }

    @property
    def category(self) -> str:
        return "voice"

    async def execute(self, **params) -> ToolResult:
        duration = params.get("duration_seconds", 5)

        try:
            from angela_core.services.voice_session_service import VoiceSessionService
            svc = VoiceSessionService()
            text = await svc._listen(timeout=float(duration))
            if text:
                return ToolResult(success=True, data={"transcription": text})
            return ToolResult(success=True, data={"transcription": "", "note": "No speech detected"})
        except Exception as e:
            return ToolResult(success=False, error=str(e))


class StartVoiceSessionTool(AngelaTool):
    """Start a voice conversation session."""

    @property
    def name(self) -> str:
        return "start_voice_session"

    @property
    def description(self) -> str:
        return "Start a voice conversation session with David (listen → think → speak loop)"

    @property
    def parameters_schema(self) -> Dict[str, Any]:
        return {
            "type": "object",
            "properties": {},
            "required": [],
        }

    @property
    def category(self) -> str:
        return "voice"

    @property
    def requires_confirmation(self) -> bool:
        return True

    async def execute(self, **params) -> ToolResult:
        try:
            from angela_core.services.voice_session_service import VoiceSessionService
            svc = VoiceSessionService()
            await svc.start_session()
            return ToolResult(success=True, data={"session": "completed"})
        except Exception as e:
            return ToolResult(success=False, error=str(e))
