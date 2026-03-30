"""
Pythia — Unified LLM Service (Claude API Primary + Ollama Fallback)

Routing:
  Claude API (primary) → all AI features
  Ollama (fallback) → only when Claude is unavailable
  DB-backed response caching for cost optimization

Cost: ~$0.63/day (~$19/month) with caching
"""
import hashlib
import json
import os
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from typing import Optional

import asyncpg
import httpx

from config import PythiaConfig


@dataclass
class LLMResponse:
    text: str
    provider: str  # "claude", "ollama", or "cache"
    model: str
    tokens_used: int = 0
    cost_estimate: float = 0.0
    success: bool = True
    error: str = ""
    cached: bool = False


class LLMService:
    """Unified LLM with Claude API primary, DB-backed caching, Ollama fallback."""

    # Cost per token (claude-sonnet-4)
    COST_INPUT_PER_TOKEN = 3.0 / 1_000_000   # $3/MTok
    COST_OUTPUT_PER_TOKEN = 15.0 / 1_000_000  # $15/MTok

    def __init__(self) -> None:
        self._anthropic_client = None

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

    @staticmethod
    def _cache_key(prompt: str, system: str, model: str) -> str:
        """Generate SHA256 cache key from prompt + system + model."""
        raw = f"{model}::{system}::{prompt}"
        return hashlib.sha256(raw.encode()).hexdigest()

    async def _check_cache(
        self, conn: Optional[asyncpg.Connection], prompt: str, system: str, model: str
    ) -> Optional[LLMResponse]:
        """Check DB cache for a cached response."""
        if conn is None:
            return None
        try:
            key = self._cache_key(prompt, system, model)
            row = await conn.fetchrow(
                "SELECT response, provider, tokens_used FROM llm_cache "
                "WHERE cache_key = $1 AND expires_at > NOW()",
                key,
            )
            if row:
                return LLMResponse(
                    text=row["response"],
                    provider=row["provider"] or "cache",
                    model=model,
                    tokens_used=row["tokens_used"] or 0,
                    cached=True,
                )
        except Exception:
            pass
        return None

    async def _store_cache(
        self,
        conn: Optional[asyncpg.Connection],
        prompt: str,
        system: str,
        model: str,
        response: LLMResponse,
        ttl_seconds: int = 3600,
        feature: str = "",
    ) -> None:
        """Store response in DB cache."""
        if conn is None:
            return
        try:
            key = self._cache_key(prompt, system, model)
            expires = datetime.now(timezone.utc) + timedelta(seconds=ttl_seconds)
            await conn.execute(
                """INSERT INTO llm_cache (cache_key, response, provider, model, tokens_used, feature, expires_at)
                   VALUES ($1, $2, $3, $4, $5, $6, $7)
                   ON CONFLICT (cache_key) DO UPDATE
                   SET response = $2, provider = $3, tokens_used = $5, expires_at = $7""",
                key, response.text, response.provider, model,
                response.tokens_used, feature, expires,
            )
        except Exception:
            pass

    async def _log_usage(
        self, conn: Optional[asyncpg.Connection], response: LLMResponse, feature: str
    ) -> None:
        """Log LLM usage for cost tracking."""
        if conn is None or response.cached:
            return
        try:
            await conn.execute(
                """INSERT INTO llm_usage_log (provider, model, feature, tokens_used, cost_estimate)
                   VALUES ($1, $2, $3, $4, $5)""",
                response.provider, response.model, feature,
                response.tokens_used, response.cost_estimate,
            )
        except Exception:
            pass

    async def complete(
        self,
        prompt: str,
        system: str = "You are a quantitative finance analyst. Be precise and data-driven.",
        max_tokens: int = 1024,
        temperature: float = 0.3,
        conn: Optional[asyncpg.Connection] = None,
        cache_ttl: int = 3600,
        feature: str = "general",
    ) -> LLMResponse:
        """Call Claude API (primary) with DB caching, Ollama fallback.

        Args:
            prompt: User prompt
            system: System message
            max_tokens: Max response tokens
            temperature: Generation temperature
            conn: DB connection for caching (optional)
            cache_ttl: Cache TTL in seconds (0 to disable)
            feature: Feature name for usage tracking
        """
        # Check cache first
        if cache_ttl > 0:
            cached = await self._check_cache(conn, prompt, system, PythiaConfig.CLAUDE_MODEL)
            if cached:
                return cached

        # Try Claude API (primary)
        result = await self._call_claude(prompt, system, max_tokens, temperature)
        if result.success:
            await self._log_usage(conn, result, feature)
            if cache_ttl > 0:
                await self._store_cache(
                    conn, prompt, system, PythiaConfig.CLAUDE_MODEL,
                    result, cache_ttl, feature,
                )
            return result

        # Fallback to Ollama
        result = await self._call_ollama(prompt, system, max_tokens, temperature)
        if result.success:
            await self._log_usage(conn, result, feature)
            if cache_ttl > 0:
                await self._store_cache(
                    conn, prompt, system, PythiaConfig.CLAUDE_MODEL,
                    result, cache_ttl, feature,
                )
            return result

        return LLMResponse(
            text="", provider="none", model="none",
            success=False, error="All LLM providers unavailable",
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
                success=False, error="Anthropic client not available",
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
            input_tokens = message.usage.input_tokens or 0
            output_tokens = message.usage.output_tokens or 0
            total_tokens = input_tokens + output_tokens
            cost = (input_tokens * self.COST_INPUT_PER_TOKEN
                    + output_tokens * self.COST_OUTPUT_PER_TOKEN)
            return LLMResponse(
                text=text.strip(),
                provider="claude",
                model=PythiaConfig.CLAUDE_MODEL,
                tokens_used=total_tokens,
                cost_estimate=round(cost, 6),
            )
        except Exception as e:
            return LLMResponse(
                text="", provider="claude", model=PythiaConfig.CLAUDE_MODEL,
                success=False, error=str(e),
            )

    async def _call_ollama(
        self,
        prompt: str,
        system: str,
        max_tokens: int,
        temperature: float,
    ) -> LLMResponse:
        """Call Ollama local API (fallback)."""
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
                        success=False, error=f"Ollama HTTP {resp.status_code}",
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
                success=False, error=str(e),
            )

    async def complete_json(
        self,
        prompt: str,
        system: str = "You are a quantitative finance analyst. Respond ONLY with valid JSON.",
        max_tokens: int = 1024,
        temperature: float = 0.2,
        conn: Optional[asyncpg.Connection] = None,
        cache_ttl: int = 3600,
        feature: str = "general",
    ) -> tuple[Optional[dict], LLMResponse]:
        """Complete and parse as JSON. Returns (parsed_dict, raw_response)."""
        resp = await self.complete(
            prompt, system, max_tokens, temperature,
            conn=conn, cache_ttl=cache_ttl, feature=feature,
        )
        if not resp.success:
            return None, resp
        try:
            text = resp.text.strip()
            if text.startswith("```"):
                lines = text.split("\n")
                text = "\n".join(lines[1:-1] if lines[-1].strip() == "```" else lines[1:])
            parsed = json.loads(text)
            return parsed, resp
        except json.JSONDecodeError:
            return None, resp


# Singleton
llm_service = LLMService()
