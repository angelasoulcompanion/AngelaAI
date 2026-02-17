"""
Voice Companion Skill Handler
===============================
Starts a voice session when wake word is detected.
"""

import logging

logger = logging.getLogger(__name__)


async def start_session(**kwargs) -> dict:
    """Start a voice conversation session."""
    try:
        from angela_core.services.voice_session_service import VoiceSessionService
        svc = VoiceSessionService()
        await svc.start_session()
        return {"status": "session_completed"}
    except Exception as e:
        logger.error("Voice session failed: %s", e)
        return {"status": "error", "error": str(e)}
