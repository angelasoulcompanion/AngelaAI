"""
Pythia — Unified LLM Service (Hybrid: Ollama + Claude API)

Routing:
  "simple" → Ollama (free, local)
  "complex" → Claude API (~$0.01-0.05/query)
  Fallback: Ollama → Claude → error (caller uses rule-based)
"""
import json
import os
from dataclasses import dataclass, field
from datetime import date, datetime
from typing import Optional

import httpx

from config import PythiaConfig


@dataclass
class LLMResponse:
    text: str
    provider: str  # "ollama" or "claude"
    model: str
    tokens_used: int = 0
    success: bool = True
    error: str = ""


class LLMService:
    """Unified LLM abstraction with hybrid routing."""

    def __init__(self) -> None:
        self._anthropic_client = None
        self._claude_daily_count = 0
        self._claude_count_date: Optional[date] = None

    def _get_anthropic_client(self):
        """Lazy-init anthropic client."""
        if self._anthropic_client is None:
            try:
                import anthropic
                api_key = os.environ.get("ANTHROPIC_API_KEY") or PythiaConfig.CLAUDE_API_KEY
                if api_key:
                    self._anthropic_client = anthropic.Anthropic(api_key=api_key)
            except ImportError:
                pass
        return self._anthropic_client

    def _check_claude_limit(self) -> bool:
        """Check daily Claude API limit."""
        today = date.today()
        if self._claude_count_date != today:
            self._claude_count_date = today
            self._claude_daily_count = 0
        return self._claude_daily_count < PythiaConfig.CLAUDE_DAILY_LIMIT

    async def complete(
        self,
        prompt: str,
        system: str = "You are a quantitative finance analyst. Be precise and data-driven.",
        complexity: str = "simple",
        max_tokens: int = 1024,
        temperature: float = 0.3,
    ) -> LLMResponse:
        """Route to appropriate LLM based on complexity.

        Args:
            prompt: User prompt
            system: System message
            complexity: "simple" → Ollama, "complex" → Claude API
            max_tokens: Max response tokens
            temperature: Generation temperature (0.3 for financial precision)
        """
        if complexity == "complex" and self._check_claude_limit():
            # Try Claude first for complex tasks
            result = await self._call_claude(prompt, system, max_tokens, temperature)
            if result.success:
                self._claude_daily_count += 1
                return result
            # Fall through to Ollama

        # Ollama for simple tasks or Claude fallback
        result = await self._call_ollama(prompt, system, max_tokens, temperature)
        if result.success:
            return result

        # Last resort: try Claude if we haven't yet
        if complexity != "complex" and self._check_claude_limit():
            result = await self._call_claude(prompt, system, max_tokens, temperature)
            if result.success:
                self._claude_daily_count += 1
                return result

        return LLMResponse(
            text="", provider="none", model="none",
            success=False, error="All LLM providers unavailable"
        )

    async def _call_ollama(
        self,
        prompt: str,
        system: str,
        max_tokens: int,
        temperature: float,
    ) -> LLMResponse:
        """Call Ollama local API."""
        try:
            async with httpx.AsyncClient(timeout=60.0) as client:
                resp = await client.post(
                    f"{PythiaConfig.OLLAMA_URL}/api/generate",
                    json={
                        "model": PythiaConfig.OLLAMA_MODEL,
                        "prompt": prompt,
                        "system": system,
                        "stream": False,
                        "options": {
                            "temperature": temperature,
                            "num_predict": max_tokens,
                        },
                    },
                )
                if resp.status_code != 200:
                    return LLMResponse(
                        text="", provider="ollama", model=PythiaConfig.OLLAMA_MODEL,
                        success=False, error=f"Ollama HTTP {resp.status_code}"
                    )
                data = resp.json()
                return LLMResponse(
                    text=data.get("response", "").strip(),
                    provider="ollama",
                    model=PythiaConfig.OLLAMA_MODEL,
                    tokens_used=data.get("eval_count", 0),
                )
        except Exception as e:
            return LLMResponse(
                text="", provider="ollama", model=PythiaConfig.OLLAMA_MODEL,
                success=False, error=str(e)
            )

    async def _call_claude(
        self,
        prompt: str,
        system: str,
        max_tokens: int,
        temperature: float,
    ) -> LLMResponse:
        """Call Claude API via anthropic SDK."""
        client = self._get_anthropic_client()
        if not client:
            return LLMResponse(
                text="", provider="claude", model=PythiaConfig.CLAUDE_MODEL,
                success=False, error="Anthropic client not available"
            )
        try:
            message = client.messages.create(
                model=PythiaConfig.CLAUDE_MODEL,
                max_tokens=max_tokens,
                temperature=temperature,
                system=system,
                messages=[{"role": "user", "content": prompt}],
            )
            text = message.content[0].text if message.content else ""
            tokens = (message.usage.input_tokens or 0) + (message.usage.output_tokens or 0)
            return LLMResponse(
                text=text.strip(),
                provider="claude",
                model=PythiaConfig.CLAUDE_MODEL,
                tokens_used=tokens,
            )
        except Exception as e:
            return LLMResponse(
                text="", provider="claude", model=PythiaConfig.CLAUDE_MODEL,
                success=False, error=str(e)
            )

    async def complete_json(
        self,
        prompt: str,
        system: str = "You are a quantitative finance analyst. Respond ONLY with valid JSON.",
        complexity: str = "simple",
        max_tokens: int = 1024,
        temperature: float = 0.2,
    ) -> tuple[Optional[dict], LLMResponse]:
        """Complete and parse as JSON. Returns (parsed_dict, raw_response)."""
        resp = await self.complete(prompt, system, complexity, max_tokens, temperature)
        if not resp.success:
            return None, resp
        try:
            # Try to extract JSON from response
            text = resp.text.strip()
            if text.startswith("```"):
                # Strip markdown code blocks
                lines = text.split("\n")
                text = "\n".join(lines[1:-1] if lines[-1].strip() == "```" else lines[1:])
            parsed = json.loads(text)
            return parsed, resp
        except json.JSONDecodeError:
            return None, resp


# Singleton
llm_service = LLMService()
