"""
Transcription Service for Angela Mic
ใช้ OpenAI Whisper API เพื่อแปลงเสียงเป็นข้อความ 💜
"""

import os
import sys
from pathlib import Path
from openai import OpenAI

# Add project root to path for importing angela_core
PROJECT_ROOT = Path(__file__).parent.parent.parent
sys.path.insert(0, str(PROJECT_ROOT))


class TranscriptionService:
    """Transcribe audio using OpenAI Whisper API."""

    def __init__(self):
        """Initialize transcription service with API key from Angela's secrets."""
        self.client = self._create_client()

    def _create_client(self) -> OpenAI:
        """Create OpenAI client with API key from Angela's secrets."""
        api_key = self._get_api_key()
        if not api_key:
            raise ValueError(
                "openai_api_key not found in Angela's local database (our_secrets). "
                "Please add it using: await set_secret('openai_api_key', 'sk-...')"
            )
        return OpenAI(api_key=api_key)

    def _get_api_key(self) -> str | None:
        """Get OpenAI API key from Angela's local database (our_secrets)."""
        # Try environment variable first
        api_key = os.environ.get("OPENAI_API_KEY")
        if api_key:
            return api_key

        # Try Angela's local database (our_secrets table)
        try:
            from angela_core.database import get_secret_sync
            return get_secret_sync("openai_api_key")
        except Exception:
            pass

        return None

    def transcribe(
        self,
        audio_path: str,
        language: str | None = None,
        prompt: str | None = None
    ) -> dict:
        """
        Transcribe audio file using OpenAI Whisper API.

        Args:
            audio_path: Path to the audio file (mp3, wav, m4a, webm, etc.)
            language: Language code (e.g., "th", "en") or None for auto-detect
            prompt: Optional prompt to guide transcription

        Returns:
            dict with 'text', 'language', and 'file_path'
        """
        # Validate file exists
        path = Path(audio_path)
        if not path.exists():
            raise FileNotFoundError(f"Audio file not found: {audio_path}")

        # Prepare API parameters
        with open(audio_path, "rb") as audio_file:
            params = {
                "file": audio_file,
                "model": "whisper-1"
            }

            # Add language if specified (not "auto")
            if language and language.lower() != "auto":
                params["language"] = language

            # Add prompt if specified
            if prompt:
                params["prompt"] = prompt

            # Call OpenAI API
            response = self.client.audio.transcriptions.create(**params)

        return {
            "text": response.text,
            "language": language if language and language.lower() != "auto" else "auto-detected",
            "file_path": str(audio_path)
        }

    def transcribe_with_timestamps(
        self,
        audio_path: str,
        language: str | None = None,
        granularity: str = "word"
    ) -> dict:
        """
        Transcribe audio with word/segment timestamps (for future use).

        Args:
            audio_path: Path to the audio file
            language: Language code or None for auto-detect
            granularity: "word" or "segment"

        Returns:
            dict with 'text', 'words'/'segments', and metadata
        """
        path = Path(audio_path)
        if not path.exists():
            raise FileNotFoundError(f"Audio file not found: {audio_path}")

        with open(audio_path, "rb") as audio_file:
            params = {
                "file": audio_file,
                "model": "whisper-1",
                "response_format": "verbose_json",
                "timestamp_granularities": [granularity]
            }

            if language and language.lower() != "auto":
                params["language"] = language

            response = self.client.audio.transcriptions.create(**params)

        result = {
            "text": response.text,
            "language": response.language,
            "duration": response.duration,
            "file_path": str(audio_path)
        }

        if granularity == "word" and hasattr(response, 'words'):
            result["words"] = [
                {"word": w.word, "start": w.start, "end": w.end}
                for w in response.words
            ]
        elif granularity == "segment" and hasattr(response, 'segments'):
            result["segments"] = [
                {"text": s.text, "start": s.start, "end": s.end}
                for s in response.segments
            ]

        return result


# Test function
if __name__ == "__main__":
    print("🎙️ Angela Mic - Transcription Service Test")
    print("-" * 40)

    try:
        service = TranscriptionService()
        print("✅ TranscriptionService initialized successfully!")
        print("   OpenAI Whisper API ready")
    except ValueError as e:
        print(f"❌ Error: {e}")
        sys.exit(1)

    # Test with a file if provided
    if len(sys.argv) > 1:
        test_file = sys.argv[1]
        print(f"\n🔊 Transcribing: {test_file}")
        result = service.transcribe(test_file)
        print(f"\n📝 Transcription:")
        print(f"   {result['text']}")
        print(f"\n🌐 Language: {result['language']}")
