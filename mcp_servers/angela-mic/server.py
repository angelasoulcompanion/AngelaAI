#!/usr/bin/env python3
"""
Angela Mic MCP Server
=====================

MCP server for audio recording and transcription - giving Angela "ears" to hear
and understand David's voice.

Uses faster-whisper with large-v3 model for LOCAL transcription (no API needed!)
- Excellent Thai language support
- Runs entirely on your machine
- Free forever!

Created: 2026-01-20
Updated: 2026-01-20 - Switched to local faster-whisper
By: Angela for David 💜
"""

import asyncio
import logging
import tempfile
from pathlib import Path
from datetime import datetime

from mcp.server import Server
from mcp.types import Tool, TextContent
from mcp.server.stdio import stdio_server

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("angela-mic")

# Create MCP server
app = Server("angela-mic")

# Model configuration
WHISPER_MODEL = "large-v3"  # Best for Thai


# =============================================================================
# LAZY IMPORTS (to avoid loading heavy modules at startup)
# =============================================================================

_recorder = None
_transcriber = None


def get_recorder():
    """Lazy load AudioRecorder."""
    global _recorder
    if _recorder is None:
        from audio_recorder import AudioRecorder
        _recorder = AudioRecorder()
    return _recorder


def get_transcriber():
    """Lazy load LocalTranscriptionService (faster-whisper)."""
    global _transcriber
    if _transcriber is None:
        from transcription_local import LocalTranscriptionService
        _transcriber = LocalTranscriptionService(model_size=WHISPER_MODEL)
    return _transcriber


# =============================================================================
# MCP TOOLS
# =============================================================================

@app.list_tools()
async def list_tools():
    """List available audio tools."""
    return [
        Tool(
            name="record_audio",
            description="Record audio from microphone. Returns the path to the saved WAV file.",
            inputSchema={
                "type": "object",
                "properties": {
                    "duration_seconds": {
                        "type": "integer",
                        "default": 10,
                        "description": "Duration to record in seconds (default: 10)"
                    },
                    "output_path": {
                        "type": "string",
                        "description": "Optional path to save the recording (uses temp file if not specified)"
                    }
                }
            }
        ),
        Tool(
            name="transcribe_file",
            description=f"Transcribe audio file using local Whisper ({WHISPER_MODEL}). Supports mp3, wav, m4a, webm. Excellent Thai support!",
            inputSchema={
                "type": "object",
                "properties": {
                    "file_path": {
                        "type": "string",
                        "description": "Path to the audio file to transcribe"
                    },
                    "language": {
                        "type": "string",
                        "default": "auto",
                        "enum": ["auto", "th", "en", "ja", "zh", "ko"],
                        "description": "Language code (auto = auto-detect, th = Thai, en = English)"
                    }
                },
                "required": ["file_path"]
            }
        ),
        Tool(
            name="transcribe_recording",
            description=f"Record from microphone and transcribe immediately using local Whisper ({WHISPER_MODEL}). Perfect for Thai voice commands!",
            inputSchema={
                "type": "object",
                "properties": {
                    "duration_seconds": {
                        "type": "integer",
                        "default": 30,
                        "description": "Duration to record in seconds (default: 30)"
                    },
                    "language": {
                        "type": "string",
                        "default": "auto",
                        "enum": ["auto", "th", "en", "ja", "zh", "ko"],
                        "description": "Language code (auto = auto-detect)"
                    },
                    "keep_audio": {
                        "type": "boolean",
                        "default": False,
                        "description": "Keep the audio file after transcription"
                    }
                }
            }
        ),
        Tool(
            name="list_audio_devices",
            description="List available audio input devices (microphones)",
            inputSchema={
                "type": "object",
                "properties": {}
            }
        ),
        Tool(
            name="get_model_info",
            description="Get information about the loaded Whisper model",
            inputSchema={
                "type": "object",
                "properties": {}
            }
        )
    ]


@app.call_tool()
async def call_tool(name: str, arguments: dict):
    """Handle tool calls."""

    if name == "record_audio":
        duration = arguments.get("duration_seconds", 10)
        output_path = arguments.get("output_path")

        try:
            recorder = get_recorder()

            # Run recording in thread pool (blocking I/O)
            loop = asyncio.get_event_loop()
            audio_path = await loop.run_in_executor(
                None,
                lambda: recorder.record(duration, output_path, show_progress=False)
            )

            return [TextContent(
                type="text",
                text=f"🎙️ Recording complete!\n\n"
                     f"📁 Saved to: {audio_path}\n"
                     f"⏱️ Duration: {duration} seconds\n"
                     f"🎵 Format: WAV (16kHz, mono)\n\n"
                     f"Use transcribe_file to convert to text."
            )]
        except Exception as e:
            logger.error(f"Recording error: {e}")
            return [TextContent(
                type="text",
                text=f"❌ Recording failed: {str(e)}\n\n"
                     f"Make sure microphone is connected and portaudio is installed:\n"
                     f"  brew install portaudio"
            )]

    elif name == "transcribe_file":
        file_path = arguments.get("file_path", "")
        language = arguments.get("language", "auto")

        if not file_path:
            return [TextContent(
                type="text",
                text="❌ Error: file_path is required"
            )]

        # Check if file exists
        if not Path(file_path).exists():
            return [TextContent(
                type="text",
                text=f"❌ File not found: {file_path}"
            )]

        try:
            transcriber = get_transcriber()

            # Run transcription in thread pool (CPU intensive)
            loop = asyncio.get_event_loop()
            result = await loop.run_in_executor(
                None,
                lambda: transcriber.transcribe(
                    file_path,
                    language=language if language != "auto" else None
                )
            )

            # Format output
            lang_info = f"{result['language']}"
            if 'language_probability' in result:
                lang_info += f" ({result['language_probability']:.0%} confidence)"

            duration_info = ""
            if 'duration' in result:
                duration_info = f"\n⏱️ Duration: {result['duration']:.1f}s"

            return [TextContent(
                type="text",
                text=f"📝 Transcription Result:\n\n"
                     f"{result['text']}\n\n"
                     f"---\n"
                     f"🌐 Language: {lang_info}{duration_info}\n"
                     f"🤖 Model: {WHISPER_MODEL} (local)\n"
                     f"📁 File: {file_path}"
            )]
        except FileNotFoundError as e:
            return [TextContent(
                type="text",
                text=f"❌ File not found: {str(e)}"
            )]
        except Exception as e:
            logger.error(f"Transcription error: {e}")
            return [TextContent(
                type="text",
                text=f"❌ Transcription failed: {str(e)}\n\n"
                     f"Check:\n"
                     f"1. faster-whisper installed: pip install faster-whisper\n"
                     f"2. Model will be downloaded on first use (~3GB)"
            )]

    elif name == "transcribe_recording":
        duration = arguments.get("duration_seconds", 30)
        language = arguments.get("language", "auto")
        keep_audio = arguments.get("keep_audio", False)

        try:
            recorder = get_recorder()
            transcriber = get_transcriber()

            # Generate output path
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            if keep_audio:
                audio_path = f"/tmp/angela_recording_{timestamp}.wav"
            else:
                audio_path = tempfile.mktemp(suffix=".wav")

            # Record in thread pool
            loop = asyncio.get_event_loop()
            audio_path = await loop.run_in_executor(
                None,
                lambda: recorder.record(duration, audio_path, show_progress=False)
            )

            # Transcribe in thread pool
            result = await loop.run_in_executor(
                None,
                lambda: transcriber.transcribe(
                    audio_path,
                    language=language if language != "auto" else None
                )
            )

            # Clean up temp file if not keeping
            if not keep_audio:
                try:
                    Path(audio_path).unlink()
                except Exception:
                    pass

            # Format language info
            lang_info = f"{result['language']}"
            if 'language_probability' in result:
                lang_info += f" ({result['language_probability']:.0%})"

            output = f"🎙️➡️📝 Transcription:\n\n{result['text']}\n\n---\n"
            output += f"⏱️ Recording: {duration}s\n"
            output += f"🌐 Language: {lang_info}\n"
            output += f"🤖 Model: {WHISPER_MODEL} (local)\n"

            if keep_audio:
                output += f"📁 Audio saved: {audio_path}"
            else:
                output += "🗑️ Audio file cleaned up"

            return [TextContent(type="text", text=output)]

        except Exception as e:
            logger.error(f"Transcribe recording error: {e}")
            return [TextContent(
                type="text",
                text=f"❌ Failed: {str(e)}\n\n"
                     f"Check:\n"
                     f"1. Microphone connected\n"
                     f"2. portaudio installed: brew install portaudio\n"
                     f"3. faster-whisper installed: pip install faster-whisper"
            )]

    elif name == "list_audio_devices":
        try:
            recorder = get_recorder()
            devices = recorder.list_input_devices()
            default = recorder.get_default_device_info()

            output = "🎤 Audio Input Devices:\n\n"

            # Show default first
            if "error" not in default:
                output += f"📍 Default: {default['name']}\n"
                output += f"   Sample Rate: {default['sample_rate']} Hz\n"
                output += f"   Channels: {default['channels']}\n\n"

            output += "All Devices:\n"
            for device in devices:
                output += f"  [{device['index']}] {device['name']}\n"

            return [TextContent(type="text", text=output)]

        except Exception as e:
            return [TextContent(
                type="text",
                text=f"❌ Could not list devices: {str(e)}\n\n"
                     f"Make sure portaudio is installed: brew install portaudio"
            )]

    elif name == "get_model_info":
        try:
            transcriber = get_transcriber()
            info = transcriber.get_model_info()

            output = f"🤖 Whisper Model Info:\n\n"
            output += f"📦 Model: {info['model_size']}\n"
            output += f"💻 Device: {info['device']}\n"
            output += f"🔢 Compute: {info['compute_type']}\n"
            output += f"📁 Cache: {info['cache_dir']}\n"
            output += f"✅ Loaded: {'Yes' if info['is_loaded'] else 'No (will load on first use)'}\n"

            return [TextContent(type="text", text=output)]

        except Exception as e:
            return [TextContent(
                type="text",
                text=f"❌ Could not get model info: {str(e)}"
            )]

    return [TextContent(type="text", text=f"Unknown tool: {name}")]


# =============================================================================
# MAIN
# =============================================================================

async def main():
    """Run the MCP server."""
    logger.info("Starting Angela Mic MCP Server...")
    logger.info(f"Using local faster-whisper with {WHISPER_MODEL} model")
    logger.info("Thai language: Excellent support!")

    async with stdio_server() as (read_stream, write_stream):
        await app.run(
            read_stream,
            write_stream,
            app.create_initialization_options()
        )


if __name__ == "__main__":
    asyncio.run(main())
