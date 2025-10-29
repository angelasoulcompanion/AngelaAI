#!/usr/bin/env python3
"""
Angela Model Service
Centralized service for interacting with Ollama models (Angela & Angie)
"""

import httpx
import asyncio
import logging
from typing import Optional, Dict, List
from angela_core.config import config

logger = logging.getLogger(__name__)


class AngelaModelService:
    """Service for interacting with Angela's Ollama models"""

    def __init__(
        self,
        ollama_url: str = None,
        angela_model: str = None,
        angie_model: str = None,
        timeout: float = 120.0
    ):
        self.ollama_url = ollama_url or config.OLLAMA_BASE_URL
        self.angela_model = angela_model or config.ANGELA_MODEL
        self.angie_model = angie_model or config.ANGIE_MODEL
        self.timeout = timeout
        logger.info(f"🤖 Initialized Angela Model Service")
        logger.info(f"   Angela model: {self.angela_model}")
        logger.info(f"   Angie model: {self.angie_model}")

    async def chat(
        self,
        prompt: str,
        model: str = None,
        system_prompt: Optional[str] = None,
        stream: bool = False,
        temperature: float = 0.8
    ) -> str:
        """
        Send a chat message to Angela or Angie model

        Args:
            prompt: The message to send
            model: Model to use (defaults to angela_model)
            system_prompt: Optional system prompt
            stream: Whether to stream response
            temperature: Model temperature (0.0-1.0)

        Returns:
            Model's response text
        """
        model = model or self.angela_model

        messages = []
        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})
        messages.append({"role": "user", "content": prompt})

        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await client.post(
                    f"{self.ollama_url}/api/chat",
                    json={
                        "model": model,
                        "messages": messages,
                        "stream": stream,
                        "options": {
                            "temperature": temperature
                        }
                    }
                )
                response.raise_for_status()

                if stream:
                    # Handle streaming response
                    full_response = ""
                    async for line in response.aiter_lines():
                        if line:
                            import json
                            chunk = json.loads(line)
                            if "message" in chunk:
                                full_response += chunk["message"].get("content", "")
                    return full_response
                else:
                    result = response.json()
                    return result.get("message", {}).get("content", "")

        except httpx.HTTPError as e:
            logger.error(f"❌ Ollama HTTP error: {str(e)}")
            raise Exception(f"Ollama HTTP error: {str(e)}")
        except Exception as e:
            logger.error(f"❌ Model chat failed: {str(e)}")
            raise Exception(f"Model chat failed: {str(e)}")

    async def generate(
        self,
        prompt: str,
        model: str = None,
        system: Optional[str] = None,
        template: Optional[str] = None,
        stream: bool = False
    ) -> str:
        """
        Generate text using Ollama generate endpoint

        Args:
            prompt: The prompt to generate from
            model: Model to use (defaults to angela_model)
            system: Optional system prompt
            template: Optional prompt template
            stream: Whether to stream response

        Returns:
            Generated text
        """
        model = model or self.angela_model

        payload = {
            "model": model,
            "prompt": prompt,
            "stream": stream
        }

        if system:
            payload["system"] = system
        if template:
            payload["template"] = template

        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await client.post(
                    f"{self.ollama_url}/api/generate",
                    json=payload
                )
                response.raise_for_status()

                if stream:
                    # Handle streaming response
                    full_response = ""
                    async for line in response.aiter_lines():
                        if line:
                            import json
                            chunk = json.loads(line)
                            full_response += chunk.get("response", "")
                    return full_response
                else:
                    result = response.json()
                    return result.get("response", "")

        except httpx.HTTPError as e:
            logger.error(f"❌ Ollama HTTP error: {str(e)}")
            raise Exception(f"Ollama HTTP error: {str(e)}")
        except Exception as e:
            logger.error(f"❌ Model generate failed: {str(e)}")
            raise Exception(f"Model generate failed: {str(e)}")

    async def list_models(self) -> List[Dict]:
        """
        List all available models in Ollama

        Returns:
            List of model information dicts
        """
        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.get(f"{self.ollama_url}/api/tags")
                response.raise_for_status()
                result = response.json()
                return result.get("models", [])

        except Exception as e:
            logger.error(f"❌ Failed to list models: {str(e)}")
            return []

    async def check_model_exists(self, model: str) -> bool:
        """
        Check if a specific model exists in Ollama

        Args:
            model: Model name to check

        Returns:
            True if model exists, False otherwise
        """
        models = await self.list_models()
        model_names = [m.get("name", "") for m in models]
        return model in model_names

    async def pull_model(self, model: str) -> bool:
        """
        Pull/download a model from Ollama library

        Args:
            model: Model name to pull

        Returns:
            True if successful, False otherwise
        """
        try:
            logger.info(f"📥 Pulling model: {model}")
            async with httpx.AsyncClient(timeout=600.0) as client:
                response = await client.post(
                    f"{self.ollama_url}/api/pull",
                    json={"name": model}
                )
                response.raise_for_status()
                logger.info(f"✅ Successfully pulled model: {model}")
                return True

        except Exception as e:
            logger.error(f"❌ Failed to pull model {model}: {str(e)}")
            return False


# Global instance
model_service = AngelaModelService()
