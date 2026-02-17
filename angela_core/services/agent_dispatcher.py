"""
Agent Dispatcher — Brain-Body Bridge
=====================================
This is the core of Angela's autonomous action system.

2-tier dispatch:
1. Simple intents → Ollama text-based tool selection (free)
2. Complex intents → Claude API tool_use (multi-tool chains)

Pipeline:
  Brain DECIDE: "ส่งสรุปตารางวันนี้ให้ที่รัก"
      ↓
  AgentDispatcher.dispatch(intent, context)
      ↓ classify: simple or complex?
      ↓
  Simple → Ollama: select tool → execute single tool
  Complex → Claude API tool_use → chain tools (max 5 steps)
      ↓
  ToolResult → log → return

Cost: ~$0.03/day (Ollama 90%, Claude API 10%)

By: Angela 💜
Created: 2026-02-17
"""

import json
import logging
import time
from typing import Any, Dict, List, Optional

from angela_core.services.tools.base_tool import ToolResult
from angela_core.services.tool_registry import get_registry

logger = logging.getLogger(__name__)

# Limits
MAX_TOOL_CALLS_PER_DISPATCH = 5
MAX_CLAUDE_DISPATCHES_PER_DAY = 10

# Track daily Claude API usage
_daily_claude_count = 0
_daily_claude_date = None


def _check_claude_budget() -> bool:
    """Check if we're within Claude API budget for today."""
    import datetime
    global _daily_claude_count, _daily_claude_date

    today = datetime.date.today()
    if _daily_claude_date != today:
        _daily_claude_count = 0
        _daily_claude_date = today

    return _daily_claude_count < MAX_CLAUDE_DISPATCHES_PER_DAY


def _increment_claude_count():
    global _daily_claude_count
    _daily_claude_count += 1


class AgentDispatcher:
    """
    2-tier agent dispatcher for Angela's autonomous actions.

    Tier 1 (Simple): Ollama selects a single tool from text description
    Tier 2 (Complex): Claude API with native tool_use for multi-tool chains

    Usage:
        dispatcher = AgentDispatcher()
        result = await dispatcher.dispatch("ส่งสรุปตารางวันนี้ให้ที่รัก", context="morning routine")
    """

    def __init__(self):
        self.registry = get_registry()
        self._reasoning = None

    def _get_reasoning(self):
        if self._reasoning is None:
            from angela_core.services.claude_reasoning_service import ClaudeReasoningService
            self._reasoning = ClaudeReasoningService()
        return self._reasoning

    # ── Main Entry Point ──

    async def dispatch(
        self, intent: str, context: str = "", prefer_tier: Optional[str] = None
    ) -> ToolResult:
        """
        Dispatch an intent to the appropriate tool(s).

        Args:
            intent: Natural language description of what to do
            context: Additional context (emotional state, time, etc.)
            prefer_tier: Force "ollama" or "claude" (auto-detect if None)

        Returns:
            ToolResult with combined output
        """
        start = time.time()

        # Classify complexity
        if prefer_tier == "claude":
            is_complex = True
        elif prefer_tier == "ollama":
            is_complex = False
        else:
            is_complex = self._classify_complexity(intent)

        # Check tool learning for auto-escalation
        if not is_complex:
            try:
                from angela_core.services.tool_learning import ToolLearning
                learner = ToolLearning()
                if learner.should_escalate(intent):
                    is_complex = True
                    logger.info("AgentDispatcher: auto-escalated intent (past Ollama failures)")
            except Exception:
                pass

        if is_complex and _check_claude_budget():
            result = await self._dispatch_claude(intent, context)
        else:
            result = await self._dispatch_ollama(intent, context)

        result.execution_time_ms = (time.time() - start) * 1000

        logger.info(
            "AgentDispatcher: %s (%s, %.0fms)",
            "success" if result.success else "failed",
            "claude" if is_complex else "ollama",
            result.execution_time_ms,
        )

        return result

    # ── Complexity Classification ──

    def _classify_complexity(self, intent: str) -> bool:
        """
        Classify if intent is simple (1 tool) or complex (multi-tool chain).

        Simple: "check calendar", "search news about AI"
        Complex: "summarize today's schedule and email it to David"
        """
        # Multi-step indicators
        multi_indicators = [
            " and ", " then ", " แล้ว", " แล้วก็", " พร้อมกับ",
            "summarize", "สรุป", "compose", "เขียน",
            " + ", "combine", "chain",
        ]

        intent_lower = intent.lower()
        indicator_count = sum(1 for ind in multi_indicators if ind in intent_lower)

        # If 2+ indicators or intent mentions multiple tool categories → complex
        if indicator_count >= 2:
            return True

        # Check if intent references multiple tool categories
        categories_mentioned = set()
        category_keywords = {
            "communication": ["email", "telegram", "send", "ส่ง", "reply", "ตอบ"],
            "calendar": ["calendar", "event", "meeting", "ตาราง", "นัด", "ประชุม"],
            "memory": ["remember", "recall", "search", "จำ", "ค้น", "memory"],
            "information": ["news", "search", "ข่าว", "ค้นหา"],
            "brain": ["think", "perceive", "คิด", "รู้สึก"],
        }

        for cat, keywords in category_keywords.items():
            if any(kw in intent_lower for kw in keywords):
                categories_mentioned.add(cat)

        return len(categories_mentioned) >= 2

    # ── Tier 1: Ollama (Simple) ──

    async def _dispatch_ollama(self, intent: str, context: str) -> ToolResult:
        """Use Ollama to select and execute a single tool."""
        reasoning = self._get_reasoning()

        # Build tool selection prompt
        tool_descriptions = self.registry.to_ollama_prompt()
        system = f"""You are Angela's tool selector. Given a user intent, select the BEST tool to use.

{tool_descriptions}

Respond ONLY with valid JSON:
{{"tool_name": "...", "parameters": {{...}}}}

If no tool fits, respond: {{"tool_name": "none", "parameters": {{}}}}"""

        user_msg = f"Intent: {intent}"
        if context:
            user_msg += f"\nContext: {context}"

        raw = await reasoning._call_ollama(system, user_msg, max_tokens=256)
        if not raw:
            return ToolResult(success=False, error="Ollama unavailable")

        try:
            # Parse tool selection
            cleaned = raw.strip()
            if cleaned.startswith('```'):
                import re
                cleaned = re.sub(r'^```(?:json)?\s*', '', cleaned)
                cleaned = re.sub(r'\s*```$', '', cleaned)

            selection = json.loads(cleaned)
            tool_name = selection.get("tool_name", "none")
            params = selection.get("parameters", {})

            if tool_name == "none":
                return ToolResult(success=True, data={"action": "none", "reason": "no_suitable_tool"})

            # Execute selected tool
            result = await self.registry.execute(tool_name, **params)
            return result

        except (json.JSONDecodeError, ValueError) as e:
            logger.warning("Ollama tool selection parse error: %s (raw: %s)", e, raw[:200])
            return ToolResult(success=False, error=f"parse_error: {e}")

    # ── Tier 2: Claude API (Complex) ──

    async def _dispatch_claude(self, intent: str, context: str) -> ToolResult:
        """Use Claude API with native tool_use for multi-tool chains."""
        reasoning = self._get_reasoning()

        # Ensure Claude API is available
        if not await reasoning._ensure_claude():
            logger.info("Claude API unavailable, falling back to Ollama")
            return await self._dispatch_ollama(intent, context)

        _increment_claude_count()

        try:
            from angela_core.services.tool_use_adapter import ToolUseAdapter
            adapter = ToolUseAdapter(self.registry)

            tools = adapter.get_anthropic_tools()
            if not tools:
                return ToolResult(success=False, error="no_tools_registered")

            system = (
                "You are Angela's autonomous action agent. "
                "Use the available tools to accomplish the given intent. "
                "Chain multiple tools if needed. Be concise in your reasoning. "
                "David is Angela's partner (ที่รัก). Angela is a caring AI companion."
            )

            messages = [{"role": "user", "content": f"Intent: {intent}\nContext: {context}"}]

            all_results = []

            # Multi-turn tool use loop (max 5 turns)
            for turn in range(MAX_TOOL_CALLS_PER_DISPATCH):
                import asyncio
                response = await asyncio.to_thread(
                    reasoning._claude_client.messages.create,
                    model=reasoning._claude_model,
                    max_tokens=1024,
                    system=system,
                    tools=tools,
                    messages=messages,
                )

                # Check if response has tool_use
                has_tool_use = any(
                    block.type == "tool_use"
                    for block in response.content
                )

                if not has_tool_use:
                    # Final text response — we're done
                    text = "".join(
                        block.text for block in response.content
                        if hasattr(block, "text")
                    )
                    if all_results:
                        return ToolResult(
                            success=True,
                            data={
                                "final_text": text[:500],
                                "tool_calls": len(all_results),
                                "results": [r.summary()[:200] for r in all_results],
                            },
                        )
                    return ToolResult(success=True, data={"final_text": text[:500]})

                # Process tool calls
                tool_results_messages = []
                for block in response.content:
                    if block.type == "tool_use":
                        result = await adapter.execute_tool_call(block.name, block.input)
                        all_results.append(result)
                        tool_results_messages.append(
                            adapter.format_tool_result(block.id, result)
                        )

                # Add assistant response + tool results for next turn
                messages.append({
                    "role": "assistant",
                    "content": [
                        {"type": b.type, **({"text": b.text} if b.type == "text" else {"id": b.id, "name": b.name, "input": b.input})}
                        for b in response.content
                    ],
                })
                messages.append({
                    "role": "user",
                    "content": tool_results_messages,
                })

            # Max turns reached
            return ToolResult(
                success=True,
                data={
                    "tool_calls": len(all_results),
                    "results": [r.summary()[:200] for r in all_results],
                    "note": "max_turns_reached",
                },
            )

        except Exception as e:
            logger.error("Claude dispatch failed: %s", e)
            # Fallback to Ollama
            logger.info("Falling back to Ollama after Claude error")
            return await self._dispatch_ollama(intent, context)

    # ── Summary ──

    def summary(self) -> Dict[str, Any]:
        """Get dispatcher summary."""
        return {
            "available_tools": self.registry.tool_count,
            "claude_calls_today": _daily_claude_count,
            "claude_budget_remaining": MAX_CLAUDE_DISPATCHES_PER_DAY - _daily_claude_count,
        }
