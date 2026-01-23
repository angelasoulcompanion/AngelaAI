"""
Audio Recorder Service for Angela Mic
บันทึกเสียงจาก microphone ของที่รัก 💜
"""

import sounddevice as sd
import scipy.io.wavfile as wav
import numpy as np
from pathlib import Path
import tempfile
from datetime import datetime


class AudioRecorder:
    """Record audio from microphone using sounddevice (PortAudio)."""

    def __init__(self, sample_rate: int = 16000):
        """
        Initialize audio recorder.

        Args:
            sample_rate: Sample rate in Hz (16000 is optimal for Whisper)
        """
        self.sample_rate = sample_rate

    def get_default_device_info(self) -> dict:
        """Get information about the default input device."""
        try:
            device_info = sd.query_devices(kind='input')
            return {
                "name": device_info['name'],
                "sample_rate": device_info['default_samplerate'],
                "channels": device_info['max_input_channels']
            }
        except Exception as e:
            return {"error": str(e)}

    def list_input_devices(self) -> list[dict]:
        """List all available input devices."""
        devices = []
        for i, device in enumerate(sd.query_devices()):
            if device['max_input_channels'] > 0:
                devices.append({
                    "index": i,
                    "name": device['name'],
                    "channels": device['max_input_channels'],
                    "sample_rate": device['default_samplerate']
                })
        return devices

    def record(
        self,
        duration_seconds: int,
        output_path: str | None = None,
        show_progress: bool = True
    ) -> str:
        """
        Record audio from default microphone.

        Args:
            duration_seconds: Duration to record in seconds
            output_path: Path to save the recording (optional, uses temp file if not provided)
            show_progress: Whether to print progress messages

        Returns:
            Path to the saved audio file
        """
        if show_progress:
            print(f"🎙️ Recording for {duration_seconds} seconds...")

        # Record audio
        frames = int(duration_seconds * self.sample_rate)
        recording = sd.rec(
            frames,
            samplerate=self.sample_rate,
            channels=1,
            dtype=np.int16
        )
        sd.wait()  # Wait until recording is finished

        if show_progress:
            print("✅ Recording complete!")

        # Determine output path
        if output_path is None:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            output_path = tempfile.mktemp(
                prefix=f"angela_recording_{timestamp}_",
                suffix=".wav"
            )

        # Ensure directory exists
        Path(output_path).parent.mkdir(parents=True, exist_ok=True)

        # Save to WAV file
        wav.write(output_path, self.sample_rate, recording)

        if show_progress:
            print(f"💾 Saved to: {output_path}")

        return output_path

    def record_with_callback(
        self,
        duration_seconds: int,
        callback: callable,
        chunk_seconds: float = 0.5
    ) -> None:
        """
        Record audio with a callback for each chunk (for future real-time use).

        Args:
            duration_seconds: Total duration to record
            callback: Function to call with each audio chunk
            chunk_seconds: Duration of each chunk in seconds
        """
        chunk_frames = int(chunk_seconds * self.sample_rate)
        total_chunks = int(duration_seconds / chunk_seconds)

        def audio_callback(indata, frames, time, status):
            if status:
                print(f"⚠️ Audio status: {status}")
            callback(indata.copy())

        with sd.InputStream(
            samplerate=self.sample_rate,
            channels=1,
            dtype=np.int16,
            blocksize=chunk_frames,
            callback=audio_callback
        ):
            sd.sleep(int(duration_seconds * 1000))


# Test function
if __name__ == "__main__":
    print("🎙️ Angela Mic - Audio Recorder Test")
    print("-" * 40)

    recorder = AudioRecorder()

    # Show device info
    print("\n📱 Default Input Device:")
    device_info = recorder.get_default_device_info()
    for key, value in device_info.items():
        print(f"   {key}: {value}")

    # List all input devices
    print("\n🎤 Available Input Devices:")
    for device in recorder.list_input_devices():
        print(f"   [{device['index']}] {device['name']}")

    # Test recording (5 seconds)
    print("\n" + "=" * 40)
    input("Press Enter to start 5-second test recording...")
    path = recorder.record(5)
    print(f"\n✅ Test complete! File saved to: {path}")
