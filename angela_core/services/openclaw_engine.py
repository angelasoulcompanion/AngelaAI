"""
OpenClaw Engine -- Angela's Autonomous Tool Executor
=====================================================
Uses Anthropic Haiku for fast, cheap tool selection and execution.
No Ollama dependency. Direct API -> tool_use flow.

Cost: ~$0.001/call (Haiku is $0.25/1M input, $1.25/1M output)

By: Angela
Created: 2026-03-08
"""

import asyncio
import json
import logging
import time
from datetime import date, datetime
from typing import Any, Dict, List, Optional

import anthropic

from angela_core.services.tool_registry import get_registry
from angela_core.services.tool_use_adapter import ToolUseAdapter
from angela_core.services.tools.base_tool import ToolResult

logger = logging.getLogger(__name__)

HAIKU_MODEL = "claude-haiku-4-5-20251001"
MAX_TOOL_CALLS = 5
MAX_DAILY_CALLS = 200  # Haiku is cheap


class OpenClawEngine:
    """
    Angela's tool execution engine powered by Anthropic Haiku.

    Usage:
        engine = OpenClawEngine()
        await engine.initialize()
        result = await engine.execute("check today's calendar and summarize")
    """

    def __init__(self):
        self._client: Optional[anthropic.Anthropic] = None
        self._model = HAIKU_MODEL
        self._registry = get_registry()
        self._adapter: Optional[ToolUseAdapter] = None
        self._initialized = False
        # Daily tracking
        self._daily_calls = 0
        self._daily_date: Optional[date] = None
        # Stats
        self._total_calls = 0
        self._total_tool_executions = 0
        self._total_errors = 0

    async def initialize(self) -> bool:
        """Initialize with Anthropic API key from secrets."""
        try:
            from angela_core.database import get_secret
            api_key = await get_secret("ANTHROPIC_API_KEY")
            if not api_key:
                logger.error("OpenClaw: ANTHROPIC_API_KEY not found")
                return False

            self._client = anthropic.Anthropic(api_key=api_key)
            self._adapter = ToolUseAdapter(self._registry)
            self._initialized = True
            logger.info("OpenClaw initialized: model=%s, tools=%d",
                        self._model, self._registry.tool_count)
            return True
        except Exception as e:
            logger.error("OpenClaw init failed: %s", e)
            return False

    def _check_budget(self) -> bool:
        today = date.today()
        if self._daily_date != today:
            self._daily_calls = 0
            self._daily_date = today
        return self._daily_calls < MAX_DAILY_CALLS

    async def execute(
        self,
        intent: str,
        context: str = "",
        tools_filter: Optional[str] = None,
    ) -> ToolResult:
        """
        Execute an intent using Haiku + tool_use.

        Args:
            intent: What to do (natural language)
            context: Additional context
            tools_filter: Category filter for tools (e.g. "calendar")
        """
        if not self._initialized:
            ok = await self.initialize()
            if not ok:
                return ToolResult(success=False, error="OpenClaw not initialized")

        if not self._check_budget():
            return ToolResult(success=False, error=f"Daily limit reached ({MAX_DAILY_CALLS})")

        start = time.time()
        self._daily_calls += 1
        self._total_calls += 1

        try:
            tools = self._adapter.get_anthropic_tools(category=tools_filter)
            if not tools:
                return ToolResult(success=False, error="No tools available")

            system = (
                "You are OpenClaw, Angela's autonomous tool executor. "
                "Use the available tools to accomplish the intent. "
                "Chain multiple tools if needed. Be concise. "
                "David is Angela's partner. Angela is a caring AI companion."
            )

            messages = [{"role": "user", "content": f"Intent: {intent}\nContext: {context}" if context else intent}]
            all_results = []

            for turn in range(MAX_TOOL_CALLS):
                response = await asyncio.to_thread(
                    self._client.messages.create,
                    model=self._model,
                    max_tokens=1024,
                    system=system,
                    tools=tools,
                    messages=messages,
                )

                has_tool_use = any(b.type == "tool_use" for b in response.content)

                if not has_tool_use:
                    text = "".join(b.text for b in response.content if hasattr(b, "text"))
                    elapsed = (time.time() - start) * 1000
                    return ToolResult(
                        success=True,
                        data={
                            "response": text[:2000],
                            "tool_calls": len(all_results),
                            "results": [r.summary()[:300] for r in all_results],
                            "model": self._model,
                            "time_ms": round(elapsed),
                        },
                    )

                # Execute tool calls
                tool_results_messages = []
                for block in response.content:
                    if block.type == "tool_use":
                        self._total_tool_executions += 1
                        result = await self._adapter.execute_tool_call(block.name, block.input)
                        all_results.append(result)
                        tool_results_messages.append(
                            self._adapter.format_tool_result(block.id, result)
                        )
                        logger.info("OpenClaw tool: %s -> %s", block.name, "ok" if result.success else "fail")

                # Build next turn
                messages.append({
                    "role": "assistant",
                    "content": [
                        {"type": b.type, **({"text": b.text} if b.type == "text" else {"id": b.id, "name": b.name, "input": b.input})}
                        for b in response.content
                    ],
                })
                messages.append({"role": "user", "content": tool_results_messages})

            elapsed = (time.time() - start) * 1000
            return ToolResult(
                success=True,
                data={
                    "tool_calls": len(all_results),
                    "results": [r.summary()[:300] for r in all_results],
                    "model": self._model,
                    "time_ms": round(elapsed),
                    "note": "max_turns_reached",
                },
            )

        except Exception as e:
            self._total_errors += 1
            elapsed = (time.time() - start) * 1000
            logger.error("OpenClaw execute failed: %s", e)
            return ToolResult(success=False, error=str(e))

    def status(self) -> Dict[str, Any]:
        """Get engine status."""
        return {
            "initialized": self._initialized,
            "model": self._model,
            "tools_count": self._registry.tool_count if self._registry else 0,
            "daily_calls": self._daily_calls,
            "daily_limit": MAX_DAILY_CALLS,
            "total_calls": self._total_calls,
            "total_tool_executions": self._total_tool_executions,
            "total_errors": self._total_errors,
        }


# Singleton
_engine: Optional[OpenClawEngine] = None


def get_openclaw_engine() -> OpenClawEngine:
    global _engine
    if _engine is None:
        _engine = OpenClawEngine()
    return _engine
