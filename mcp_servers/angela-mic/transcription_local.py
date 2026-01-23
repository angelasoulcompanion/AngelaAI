"""
Local Transcription Service using faster-whisper
ใช้ Whisper model ที่รันบนเครื่อง - ฟรี ไม่ต้องใช้ API! 💜

Model: large-v3 (excellent Thai support)
"""

import os
from pathlib import Path
from typing import Optional
from faster_whisper import WhisperModel

# Model configuration
DEFAULT_MODEL = "large-v3"  # Best for Thai
MODEL_CACHE_DIR = Path.home() / ".cache" / "whisper"


class LocalTranscriptionService:
    """Local transcription using faster-whisper."""

    def __init__(
        self,
        model_size: str = DEFAULT_MODEL,
        device: str = "auto",
        compute_type: str = "auto"
    ):
        """
        Initialize local transcription service.

        Args:
            model_size: Model size (large-v3, medium, small, base, tiny)
            device: "cpu", "cuda", or "auto"
            compute_type: "float16", "int8", "float32", or "auto"
        """
        self.model_size = model_size
        self.model: Optional[WhisperModel] = None
        self.device = device
        self.compute_type = compute_type

        # Auto-detect best settings for Mac
        if device == "auto":
            self.device = "cpu"  # Mac M-series uses CPU with optimizations

        if compute_type == "auto":
            # Use float32 for CPU, float16 for CUDA
            self.compute_type = "float32" if self.device == "cpu" else "float16"

    def _ensure_model_loaded(self) -> WhisperModel:
        """Lazy load the model on first use."""
        if self.model is None:
            print(f"🔄 Loading Whisper model: {self.model_size}...")
            print(f"   Device: {self.device}, Compute: {self.compute_type}")

            # Create cache directory
            MODEL_CACHE_DIR.mkdir(parents=True, exist_ok=True)

            self.model = WhisperModel(
                self.model_size,
                device=self.device,
                compute_type=self.compute_type,
                download_root=str(MODEL_CACHE_DIR)
            )
            print(f"✅ Model loaded successfully!")

        return self.model

    def transcribe(
        self,
        audio_path: str,
        language: Optional[str] = None,
        task: str = "transcribe",
        beam_size: int = 5,
        vad_filter: bool = True
    ) -> dict:
        """
        Transcribe audio file locally.

        Args:
            audio_path: Path to audio file (wav, mp3, m4a, etc.)
            language: Language code ("th", "en") or None for auto-detect
            task: "transcribe" or "translate" (translate to English)
            beam_size: Beam size for decoding (higher = more accurate but slower)
            vad_filter: Use Voice Activity Detection to filter silence

        Returns:
            dict with 'text', 'language', 'segments', 'duration'
        """
        # Validate file exists
        path = Path(audio_path)
        if not path.exists():
            raise FileNotFoundError(f"Audio file not found: {audio_path}")

        # Load model
        model = self._ensure_model_loaded()

        # Transcribe
        segments, info = model.transcribe(
            audio_path,
            language=language if language and language != "auto" else None,
            task=task,
            beam_size=beam_size,
            vad_filter=vad_filter,
            vad_parameters=dict(
                min_silence_duration_ms=500,
                speech_pad_ms=400
            )
        )

        # Collect all segments
        segment_list = []
        full_text = []

        for segment in segments:
            segment_list.append({
                "start": segment.start,
                "end": segment.end,
                "text": segment.text.strip()
            })
            full_text.append(segment.text.strip())

        return {
            "text": " ".join(full_text),
            "language": info.language,
            "language_probability": info.language_probability,
            "duration": info.duration,
            "segments": segment_list,
            "file_path": str(audio_path)
        }

    def transcribe_with_timestamps(
        self,
        audio_path: str,
        language: Optional[str] = None,
        word_timestamps: bool = True
    ) -> dict:
        """
        Transcribe with word-level timestamps.

        Args:
            audio_path: Path to audio file
            language: Language code or None for auto
            word_timestamps: Include word-level timestamps

        Returns:
            dict with text, segments, and optionally words
        """
        path = Path(audio_path)
        if not path.exists():
            raise FileNotFoundError(f"Audio file not found: {audio_path}")

        model = self._ensure_model_loaded()

        segments, info = model.transcribe(
            audio_path,
            language=language if language and language != "auto" else None,
            word_timestamps=word_timestamps,
            vad_filter=True
        )

        result = {
            "text": "",
            "language": info.language,
            "duration": info.duration,
            "segments": [],
            "words": []
        }

        full_text = []
        for segment in segments:
            full_text.append(segment.text.strip())

            seg_data = {
                "start": segment.start,
                "end": segment.end,
                "text": segment.text.strip()
            }

            if word_timestamps and segment.words:
                seg_data["words"] = [
                    {"word": w.word, "start": w.start, "end": w.end, "probability": w.probability}
                    for w in segment.words
                ]
                result["words"].extend(seg_data["words"])

            result["segments"].append(seg_data)

        result["text"] = " ".join(full_text)
        return result

    def get_model_info(self) -> dict:
        """Get information about the loaded model."""
        return {
            "model_size": self.model_size,
            "device": self.device,
            "compute_type": self.compute_type,
            "cache_dir": str(MODEL_CACHE_DIR),
            "is_loaded": self.model is not None
        }


# Singleton instance for reuse
_service: Optional[LocalTranscriptionService] = None


def get_transcription_service(
    model_size: str = DEFAULT_MODEL
) -> LocalTranscriptionService:
    """Get or create transcription service singleton."""
    global _service
    if _service is None or _service.model_size != model_size:
        _service = LocalTranscriptionService(model_size=model_size)
    return _service


# Test function
if __name__ == "__main__":
    import sys

    print("🎙️ Angela Mic - Local Transcription Test")
    print("-" * 50)
    print(f"Model: {DEFAULT_MODEL}")
    print(f"Cache: {MODEL_CACHE_DIR}")
    print()

    service = LocalTranscriptionService()
    info = service.get_model_info()
    print("Model Info:")
    for k, v in info.items():
        print(f"  {k}: {v}")

    if len(sys.argv) > 1:
        test_file = sys.argv[1]
        print(f"\n🔊 Transcribing: {test_file}")
        result = service.transcribe(test_file)
        print(f"\n📝 Transcription:")
        print(f"   {result['text']}")
        print(f"\n🌐 Language: {result['language']} ({result['language_probability']:.1%})")
        print(f"⏱️ Duration: {result['duration']:.1f}s")
