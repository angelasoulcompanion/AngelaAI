"""
LLM Router
===========
Smart routing between Claude Code (interactive), Claude API (daemon),
and Ollama (fallback).

Created: 2026-02-06
By: Angela 💜 (Opus 4.6 Upgrade)
"""

import os
import logging
from enum import Enum
from typing import Optional

logger = logging.getLogger(__name__)


class ExecutionContext(str, Enum):
    """Where the code is running."""
    CLAUDE_CODE = "claude_code"      # Interactive session with David
    DAEMON = "daemon"                # Background daemon process
    API_SERVER = "api_server"        # FastAPI backend
    UNKNOWN = "unknown"


class LLMRoute(str, Enum):
    """Which LLM to use."""
    CLAUDE_CODE_TASK = "claude_code_task"  # Use Task tool natively (best quality)
    CLAUDE_API_OPUS = "claude-opus-4-6"    # Opus 4.6 via API (high complexity)
    CLAUDE_API_SONNET = "claude-sonnet-4-5-20250929"  # Sonnet via API (good balance)
    OLLAMA = "ollama"                      # Local Ollama (fallback)


class LLMRouter:
    """
    Smart LLM routing for Angela's services.

    Decision hierarchy:
    1. Claude Code session → Use Task tool (native parallel subagents)
    2. Daemon/API + API key available → Claude Sonnet API (or Opus for complex)
    3. Fallback → Ollama local

    Usage:
        router = LLMRouter()
        route = router.route("Analyze emotional patterns", complexity="high")
        if route == LLMRoute.CLAUDE_CODE_TASK:
            # Use Task tool
        elif route in (LLMRoute.CLAUDE_API_OPUS, LLMRoute.CLAUDE_API_SONNET):
            # Use Anthropic SDK
        else:
            # Use Ollama
    """

    def __init__(self):
        self._context: Optional[ExecutionContext] = None

    @property
    def context(self) -> ExecutionContext:
        """Detect current execution context."""
        if self._context:
            return self._context
        return self.detect_context()

    @context.setter
    def context(self, value: ExecutionContext):
        self._context = value

    def detect_context(self) -> ExecutionContext:
        """Auto-detect execution context from environment."""
        # Claude Code sets specific environment variables
        if os.environ.get("CLAUDE_CODE") or os.environ.get("CLAUDE_CODE_ENTRYPOINT"):
            return ExecutionContext.CLAUDE_CODE

        # Check if running as daemon
        if os.environ.get("ANGELA_DAEMON") or os.environ.get("LAUNCHD_SOCKET"):
            return ExecutionContext.DAEMON

        # Check if running as API server
        if os.environ.get("ANGELA_API_SERVER"):
            return ExecutionContext.API_SERVER

        return ExecutionContext.UNKNOWN

    def is_claude_code_session(self) -> bool:
        """Check if running inside Claude Code."""
        return self.context == ExecutionContext.CLAUDE_CODE

    def claude_api_available(self) -> bool:
        """Check if Claude API is available (has API key)."""
        try:
            from angela_core.database import get_secret_sync
            key = get_secret_sync('ANTHROPIC_API_KEY')
            return bool(key)
        except Exception:
            return bool(os.environ.get('ANTHROPIC_API_KEY'))

    def ollama_available(self) -> bool:
        """Check if Ollama is running locally."""
        try:
            import urllib.request
            req = urllib.request.Request("http://localhost:11434/api/tags", method="GET")
            with urllib.request.urlopen(req, timeout=2):
                return True
        except Exception:
            return False

    def route(self, task: str = "", complexity: str = "medium") -> LLMRoute:
        """
        Determine which LLM to use for a task.

        Args:
            task: Task description (for context)
            complexity: "low", "medium", or "high"

        Returns:
            LLMRoute indicating which LLM to use
        """
        # Priority 1: Claude Code session → native Task tool
        if self.is_claude_code_session():
            logger.info("Route: Claude Code Task tool (interactive session)")
            return LLMRoute.CLAUDE_CODE_TASK

        # Priority 2: Claude API
        if self.claude_api_available():
            if complexity == "high":
                logger.info("Route: Claude Opus API (high complexity)")
                return LLMRoute.CLAUDE_API_OPUS
            logger.info("Route: Claude Sonnet API")
            return LLMRoute.CLAUDE_API_SONNET

        # Priority 3: Ollama fallback
        if self.ollama_available():
            logger.info("Route: Ollama fallback")
            return LLMRoute.OLLAMA

        # Last resort: try Sonnet anyway (might work)
        logger.warning("Route: Claude Sonnet API (no fallback available)")
        return LLMRoute.CLAUDE_API_SONNET

    def get_model_id(self, route: Optional[LLMRoute] = None) -> str:
        """Get the model ID string for a route."""
        route = route or self.route()
        model_map = {
            LLMRoute.CLAUDE_CODE_TASK: "claude-opus-4-6",  # Claude Code model
            LLMRoute.CLAUDE_API_OPUS: "claude-opus-4-6",
            LLMRoute.CLAUDE_API_SONNET: "claude-sonnet-4-5-20250929",
            LLMRoute.OLLAMA: "llama3.2:latest",
        }
        return model_map.get(route, "claude-sonnet-4-5-20250929")


# Global singleton
_router: Optional[LLMRouter] = None


def get_router() -> LLMRouter:
    """Get or create the global LLM router."""
    global _router
    if _router is None:
        _router = LLMRouter()
    return _router
