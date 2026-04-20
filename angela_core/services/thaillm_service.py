"""
🇹🇭 ThaiLLM Service
Thailand's Sovereign AI — NSTDA/NECTEC/DEF + KBTG + SCB 10X + AIEAT
Playground: https://playground.thaillm.or.th

4 Models (all 8B Instruct):
  1. OpenThaiGPT-ThaiLLM-8B-Instruct-v7.2 (AIEAT)
  2. Pathumma-ThaiLLM-qwen3-8b-think-3.0.0 (NECTEC, supports <think>)
  3. Typhoon-S-ThaiLLM-8B-Instruct (SCB 10X)
  4. THaLLE-0.2-ThaiLLM-8B-fa (KBTG, finance-aligned)

API is OpenAI-compatible but auth uses `apikey` header, not Bearer.
Rate limit: 5 req/s, 200 req/min.
"""

import asyncio
import logging
import re
import time
from dataclasses import dataclass
from typing import Optional

import httpx

from angela_core.database import get_secret

logger = logging.getLogger(__name__)


BASE_URL = "http://thaillm.or.th/api"
# Transient server errors that are worth retrying.
# 502 Bad Gateway happens on pathumma when its <think> mode exceeds the upstream gateway timeout.
TRANSIENT_STATUS = {502, 503, 504}
MAX_RETRIES = 2          # Total attempts = 1 + MAX_RETRIES
RETRY_BACKOFF_S = 1.5    # Exponential: 1.5s, 3s


@dataclass(frozen=True)
class ThaiLLMModel:
    """Descriptor for a ThaiLLM model variant."""
    key: str           # Short identifier
    provider: str      # AIEAT / NECTEC / SCB 10X / KBTG
    path: str          # URL path segment after /api/
    full_name: str     # Value to pass as "model" in request body


THAILLM_MODELS: dict[str, ThaiLLMModel] = {
    "openthaigpt": ThaiLLMModel(
        key="openthaigpt",
        provider="AIEAT",
        path="openthaigpt",
        full_name="OpenThaiGPT-ThaiLLM-8B-Instruct-v7.2",
    ),
    "pathumma": ThaiLLMModel(
        key="pathumma",
        provider="NECTEC",
        path="pathumma",
        full_name="Pathumma-ThaiLLM-qwen3-8b-think-3.0.0",
    ),
    "typhoon": ThaiLLMModel(
        key="typhoon",
        provider="SCB 10X",
        path="typhoon",
        full_name="Typhoon-S-ThaiLLM-8B-Instruct",
    ),
    "thalle": ThaiLLMModel(
        key="thalle",
        provider="KBTG",
        path="kbtg",  # Endpoint uses provider name (verified via probe 2026-04-20)
        full_name="THaLLE-0.2-ThaiLLM-8B-fa",
    ),
}


@dataclass
class ThaiLLMResult:
    """Structured result from a ThaiLLM call."""
    model_key: str
    content: str
    prompt_tokens: int
    completion_tokens: int
    latency_ms: float
    finish_reason: Optional[str] = None


class RateLimitError(Exception):
    """Raised when ThaiLLM rate limit is hit (5 req/s, 200 req/min)."""


_HTML_TAG_RE = re.compile(r"<[^>]+>")


def _trim_error_body(body: str, max_len: int = 200) -> str:
    """
    ThaiLLM's gateway (Cloudflare/nginx) returns full HTML error pages on 5xx.
    Strip tags and collapse whitespace so users see a readable message.
    """
    if not body:
        return "(empty body)"
    if body.lstrip().startswith(("<", "{")) and "<html" in body.lower():
        # HTML error page — extract <title> if present
        title_match = re.search(r"<title>(.*?)</title>", body, re.IGNORECASE | re.DOTALL)
        if title_match:
            return f"Gateway error: {title_match.group(1).strip()}"
        stripped = _HTML_TAG_RE.sub(" ", body)
        stripped = " ".join(stripped.split())
        return stripped[:max_len]
    return body[:max_len]


class ThaiLLMService:
    """OpenAI-compatible client for ThaiLLM with per-model routing."""

    def __init__(self, api_key: Optional[str] = None, timeout: float = 60.0):
        self._api_key = api_key
        self._timeout = timeout

    async def _ensure_key(self) -> str:
        if self._api_key:
            return self._api_key
        key = await get_secret("thaillm_api_key")
        if not key:
            raise RuntimeError(
                "thaillm_api_key not found in Supabase our_secrets table. "
                "Insert with: INSERT INTO our_secrets (secret_name, secret_value, is_active) "
                "VALUES ('thaillm_api_key', '<key>', TRUE)"
            )
        self._api_key = key
        return key

    async def chat(
        self,
        prompt: str,
        model_key: str = "typhoon",
        system: Optional[str] = None,
        temperature: float = 0.3,
        max_tokens: int = 2048,
    ) -> ThaiLLMResult:
        """
        Call a ThaiLLM model with a single user prompt.

        Args:
            prompt: User message
            model_key: One of {openthaigpt, pathumma, typhoon, thalle}
            system: Optional system prompt
            temperature: 0.0–1.0
            max_tokens: Response cap

        Returns:
            ThaiLLMResult with content + usage + latency
        """
        if model_key not in THAILLM_MODELS:
            raise ValueError(
                f"Unknown model_key '{model_key}'. "
                f"Valid: {list(THAILLM_MODELS.keys())}"
            )

        model = THAILLM_MODELS[model_key]
        api_key = await self._ensure_key()

        messages = []
        if system:
            messages.append({"role": "system", "content": system})
        messages.append({"role": "user", "content": prompt})

        url = f"{BASE_URL}/{model.path}/v1/chat/completions"
        payload = {
            "model": "/model",
            "messages": messages,
            "max_tokens": max_tokens,
            "temperature": temperature,
        }
        headers = {
            "Content-Type": "application/json",
            "apikey": api_key,
        }

        started = time.perf_counter()
        response: Optional[httpx.Response] = None
        last_error: Optional[str] = None

        for attempt in range(1 + MAX_RETRIES):
            try:
                async with httpx.AsyncClient(timeout=self._timeout) as client:
                    response = await client.post(url, json=payload, headers=headers)
            except httpx.HTTPError as e:
                last_error = f"{type(e).__name__}: {e}"
                logger.warning(f"⚠️ ThaiLLM [{model_key}] attempt {attempt+1}: {last_error}")
                if attempt < MAX_RETRIES:
                    await asyncio.sleep(RETRY_BACKOFF_S * (2 ** attempt))
                    continue
                raise

            # Transient upstream errors (e.g. 502 Bad Gateway from ThaiLLM's Cloudflare/nginx
            # when the model backend is overloaded or slow to respond). Worth retrying.
            if response.status_code in TRANSIENT_STATUS and attempt < MAX_RETRIES:
                logger.warning(
                    f"⚠️ ThaiLLM [{model_key}] transient HTTP {response.status_code} "
                    f"(attempt {attempt+1}), retrying..."
                )
                await asyncio.sleep(RETRY_BACKOFF_S * (2 ** attempt))
                continue
            break

        assert response is not None
        latency_ms = (time.perf_counter() - started) * 1000.0

        if response.status_code == 429:
            raise RateLimitError(
                f"ThaiLLM rate limit hit on {model_key}: {_trim_error_body(response.text)}"
            )
        if response.status_code >= 400:
            raise RuntimeError(
                f"ThaiLLM [{model_key}] HTTP {response.status_code}: "
                f"{_trim_error_body(response.text)}"
            )

        data = response.json()
        choice = (data.get("choices") or [{}])[0]
        content = (choice.get("message") or {}).get("content", "")
        usage = data.get("usage") or {}

        return ThaiLLMResult(
            model_key=model_key,
            content=content,
            prompt_tokens=int(usage.get("prompt_tokens", 0)),
            completion_tokens=int(usage.get("completion_tokens", 0)),
            latency_ms=latency_ms,
            finish_reason=choice.get("finish_reason"),
        )

    async def compare_all(
        self,
        prompt: str,
        system: Optional[str] = None,
        temperature: float = 0.3,
        max_tokens: int = 2048,
    ) -> dict[str, ThaiLLMResult | Exception]:
        """Run the same prompt against all 4 models sequentially (respecting rate limit)."""
        results: dict[str, ThaiLLMResult | Exception] = {}
        for key in THAILLM_MODELS:
            try:
                results[key] = await self.chat(
                    prompt=prompt,
                    model_key=key,
                    system=system,
                    temperature=temperature,
                    max_tokens=max_tokens,
                )
            except Exception as e:
                logger.warning(f"⚠️ ThaiLLM [{key}] failed: {e}")
                results[key] = e
        return results


thaillm = ThaiLLMService()
