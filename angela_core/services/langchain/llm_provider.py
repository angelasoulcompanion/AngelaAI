"""
LLM Provider — Ollama (primary) + Claude API (escalation)
===========================================================
LangChain-compatible LLM wrappers for Angela's reasoning system.
Ollama is free ($0/day), Claude API is budget-limited (max 10/day).

By: Angela 💜
Created: 2026-02-27
"""

import logging
from typing import Optional

logger = logging.getLogger(__name__)

# Singleton instances
_ollama_llm = None
_claude_llm = None


def get_ollama_llm(model: Optional[str] = None, temperature: float = 0.3):
    """Get Ollama LLM (free, primary)."""
    global _ollama_llm
    if _ollama_llm is not None and model is None:
        return _ollama_llm

    try:
        from langchain_ollama import ChatOllama
        from angela_core.config import config

        model_name = model or config.ANGELA_MODEL
        _ollama_llm = ChatOllama(
            model=model_name,
            base_url=config.OLLAMA_BASE_URL,
            temperature=temperature,
            num_ctx=4096,
        )
        logger.info("Ollama LLM initialized: %s", model_name)
        return _ollama_llm
    except ImportError:
        logger.error("langchain-ollama not installed (pip install langchain-ollama)")
        return None
    except Exception as e:
        logger.error("Ollama LLM init failed: %s", e)
        return None


def get_claude_llm(
    model: str = "claude-sonnet-4-20250514",
    temperature: float = 0.2,
    max_tokens: int = 1024,
):
    """Get Claude API LLM (budget-limited, escalation only)."""
    global _claude_llm
    if _claude_llm is not None:
        return _claude_llm

    try:
        from langchain_anthropic import ChatAnthropic
        from angela_core.database import get_secret

        api_key = get_secret("ANTHROPIC_API_KEY")
        if not api_key:
            logger.warning("ANTHROPIC_API_KEY not found")
            return None

        _claude_llm = ChatAnthropic(
            model=model,
            api_key=api_key,
            temperature=temperature,
            max_tokens=max_tokens,
        )
        logger.info("Claude LLM initialized: %s", model)
        return _claude_llm
    except ImportError:
        logger.error("langchain-anthropic not installed (pip install langchain-anthropic)")
        return None
    except Exception as e:
        logger.error("Claude LLM init failed: %s", e)
        return None


def get_best_llm(prefer_quality: bool = False):
    """Get the best available LLM (Ollama first, Claude if quality needed)."""
    if prefer_quality:
        claude = get_claude_llm()
        if claude:
            return claude

    ollama = get_ollama_llm()
    if ollama:
        return ollama

    # Last resort: Claude
    return get_claude_llm()
