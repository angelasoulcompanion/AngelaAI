"""
🤖 Ollama Service
การเรียกใช้ Ollama models สำหรับ Angela

Model Priority (Tier 2 - Daemon/Fallback):
1. angela:v4-typhoon — Fine-tuned Typhoon 2.5 4B (ChatML) [PRIMARY]
2. angela:v3-dpo     — Fine-tuned Angela (DPO-refined) [FALLBACK 1]
3. angela:v3-sft     — Fine-tuned Angela (SFT only) [FALLBACK 2]
4. llama3.1:8b       — Base Llama 3.1 [FALLBACK 3]
"""

import asyncio
import httpx
import logging
from typing import Optional, List

from angela_core.config import config

logger = logging.getLogger(__name__)

# Model priority order for Angela
ANGELA_MODEL_PRIORITY: List[str] = [
    "angela:v4-typhoon",  # Best: Typhoon 2.5 fine-tuned Angela (ChatML)
    "angela:v3-dpo",      # Good: DPO-refined Angela (Llama 3.1)
    "angela:v3-sft",      # OK: SFT-only Angela (Llama 3.1)
    "llama3.1:8b",        # Base: Generic Llama 3.1
]


class OllamaService:
    """Service สำหรับเรียกใช้ Ollama models"""

    def __init__(self, base_url: str = "http://localhost:11434"):
        self.base_url = base_url
        self._available_model: Optional[str] = None  # Cached after health check
        logger.info(f"🤖 Ollama Service initialized: {base_url}")

    async def health_check(self) -> Optional[str]:
        """
        Check which Angela model is available.
        Tries models in priority order and returns the first available one.

        Returns:
            Model name if available, None if Ollama is not running
        """
        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
                response = await client.get(f"{self.base_url}/api/tags")
                if response.status_code != 200:
                    return None

                available = {m["name"] for m in response.json().get("models", [])}

                for model in ANGELA_MODEL_PRIORITY:
                    if model in available or f"{model}:latest" in available:
                        self._available_model = model
                        logger.info(f"🤖 Angela model found: {model}")
                        return model

                logger.warning("⚠️ No Angela model found in Ollama")
                return None

        except Exception as e:
            logger.error(f"❌ Ollama health check failed: {e}")
            return None

    async def get_angela_model(self) -> str:
        """Get the best available Angela model (cached)"""
        if self._available_model:
            return self._available_model

        model = await self.health_check()
        return model or ANGELA_MODEL_PRIORITY[-1]  # Fallback to base

    async def call_angela(self, prompt: str) -> str:
        """Call the best available Angela model"""
        model = await self.get_angela_model()
        return await self.generate(model=model, prompt=prompt)

    async def call_reasoning_model(self, prompt: str) -> str:
        """เรียกใช้ Angela model หรือ Qwen 2.5 7B สำหรับการคิดวิเคราะห์"""
        model = await self.get_angela_model()
        return await call_angela_model(prompt, model=model)

    async def call_emotional_model(self, prompt: str) -> str:
        """เรียกใช้ Angela model สำหรับความเข้าใจทางอารมณ์"""
        model = await self.get_angela_model()
        return await call_angela_model(prompt, model=model)

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
                        },
                        "keep_alive": "35m" if config.ANGELA_MACHINE == "angela_server" else "1m",
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


async def call_angela_model(prompt: str, model: str = "angela:v4-typhoon") -> str:
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
    """เรียกใช้ Angela model สำหรับการคิดวิเคราะห์"""
    return await call_angela_model(prompt, model="angela:v4-typhoon")


async def call_emotional_model(prompt: str) -> str:
    """เรียกใช้ Angela model สำหรับความเข้าใจทางอารมณ์"""
    return await call_angela_model(prompt, model="angela:v4-typhoon")


async def call_fast_model(prompt: str) -> str:
    """เรียกใช้ Phi3 Mini สำหรับการคิดเร็ว"""
    return await call_angela_model(prompt, model="phi3:mini")
