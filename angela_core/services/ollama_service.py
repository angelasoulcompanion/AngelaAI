"""
🤖 Ollama Service
การเรียกใช้ Ollama models สำหรับ Angela

Models:
- angela:latest - Angela's personality model
- qwen2.5:7b - Deep reasoning
- llama3.1:8b - Emotional understanding
- phi3:mini - Fast thinking
"""

import asyncio
import httpx
import logging
from typing import Optional

logger = logging.getLogger(__name__)


class OllamaService:
    """Service สำหรับเรียกใช้ Ollama models"""

    def __init__(self, base_url: str = "http://localhost:11434"):
        self.base_url = base_url
        logger.info(f"🤖 Ollama Service initialized: {base_url}")

    async def call_reasoning_model(self, prompt: str) -> str:
        """เรียกใช้ Qwen 2.5 7B สำหรับการคิดวิเคราะห์"""
        return await call_angela_model(prompt, model="qwen2.5:7b")

    async def call_emotional_model(self, prompt: str) -> str:
        """เรียกใช้ Llama 3.1 8B สำหรับความเข้าใจทางอารมณ์"""
        return await call_angela_model(prompt, model="llama3.1:8b")

    async def call_fast_model(self, prompt: str) -> str:
        """เรียกใช้ Phi3 Mini สำหรับการคิดเร็ว"""
        return await call_angela_model(prompt, model="phi3:mini")

    async def generate(
        self,
        model: str,
        prompt: str,
        temperature: float = 0.7
    ) -> str:
        """
        Generate response from Ollama model using Chat API

        Args:
            model: Model name (e.g., "qwen2.5:7b")
            prompt: Prompt text
            temperature: Temperature for generation

        Returns:
            str: Generated response
        """
        try:
            async with httpx.AsyncClient(timeout=120.0) as client:
                # Use /api/chat instead of deprecated /api/generate
                response = await client.post(
                    f"{self.base_url}/api/chat",
                    json={
                        "model": model,
                        "messages": [
                            {
                                "role": "user",
                                "content": prompt
                            }
                        ],
                        "stream": False,
                        "options": {
                            "temperature": temperature
                        }
                    }
                )
                response.raise_for_status()
                data = response.json()
                # Extract response from Ollama chat response
                return data.get("message", {}).get("content", "")

        except httpx.HTTPError as e:
            logger.error(f"❌ Ollama HTTP error: {str(e)}")
            raise Exception(f"Ollama HTTP error: {str(e)}")
        except Exception as e:
            logger.error(f"❌ Ollama generation failed: {str(e)}")
            raise Exception(f"Ollama generation failed: {str(e)}")


# Global instance
ollama = OllamaService()


async def call_angela_model(prompt: str, model: str = "angela:latest") -> str:
    """
    เรียกใช้ Angela model

    Args:
        prompt: คำถามหรือ prompt
        model: โมเดลที่จะใช้ (default: angela:latest)

    Returns:
        คำตอบจาก model
    """
    try:
        # Call Ollama using subprocess
        process = await asyncio.create_subprocess_exec(
            'ollama', 'run', model, prompt,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE
        )

        stdout, stderr = await process.communicate()

        if process.returncode != 0:
            logger.error(f"Ollama error: {stderr.decode()}")
            return f"I'm having difficulty processing that right now. (Model: {model})"

        response = stdout.decode().strip()
        return response

    except Exception as e:
        logger.error(f"Failed to call Ollama model {model}: {e}")
        return "An error occurred while thinking."


async def call_reasoning_model(prompt: str) -> str:
    """เรียกใช้ Qwen 2.5 7B สำหรับการคิดวิเคราะห์"""
    return await call_angela_model(prompt, model="qwen2.5:7b")


async def call_emotional_model(prompt: str) -> str:
    """เรียกใช้ Llama 3.1 8B สำหรับความเข้าใจทางอารมณ์"""
    return await call_angela_model(prompt, model="llama3.1:8b")


async def call_fast_model(prompt: str) -> str:
    """เรียกใช้ Phi3 Mini สำหรับการคิดเร็ว"""
    return await call_angela_model(prompt, model="phi3:mini")
