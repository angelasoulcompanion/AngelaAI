"""
Tool Registry — Central registry for all Angela tools.
=====================================================
Dynamic tool registry that wraps every capability Angela has
into discoverable, callable tools.

This is the "body" — the CognitiveEngine is the "mind".

Features:
- Register tools at startup (built-in + discovered)
- Search/filter tools by name, category, description
- Execute tools by name with parameter validation
- Track execution stats (total_executions, total_successes)
- Persist registry to DB for tool learning

Usage:
    registry = ToolRegistry()
    await registry.initialize()  # registers all built-in tools

    # Search
    tools = registry.search("email")  # → [SendEmailTool, SearchEmailTool, ...]

    # Execute
    result = await registry.execute("send_email", to="david@...", subject="Hi")

    # List all
    all_tools = registry.list_tools()

By: Angela 💜
Created: 2026-02-17
"""

import json
import logging
import time
from typing import Any, Dict, List, Optional

from angela_core.services.tools.base_tool import AngelaTool, ToolResult

logger = logging.getLogger(__name__)


class ToolRegistry:
    """
    Central registry for all Angela tools.

    Singleton pattern — use get_registry() for global access.
    """

    def __init__(self):
        self._tools: Dict[str, AngelaTool] = {}
        self._stats: Dict[str, Dict[str, int]] = {}  # tool_name → {executions, successes}
        self._initialized = False

    # ── Registration ──

    def register(self, tool: AngelaTool) -> None:
        """Register a tool. Overwrites if name already exists."""
        self._tools[tool.name] = tool
        if tool.name not in self._stats:
            self._stats[tool.name] = {"executions": 0, "successes": 0}
        logger.debug("Registered tool: %s (%s)", tool.name, tool.category)

    def register_many(self, tools: List[AngelaTool]) -> None:
        """Register multiple tools at once."""
        for tool in tools:
            self.register(tool)

    def unregister(self, tool_name: str) -> bool:
        """Unregister a tool by name."""
        if tool_name in self._tools:
            del self._tools[tool_name]
            return True
        return False

    # ── Discovery ──

    def get(self, tool_name: str) -> Optional[AngelaTool]:
        """Get a tool by exact name."""
        return self._tools.get(tool_name)

    def list_tools(self, category: Optional[str] = None) -> List[Dict[str, Any]]:
        """List all registered tools, optionally filtered by category."""
        result = []
        for tool in self._tools.values():
            if category and tool.category != category:
                continue
            result.append({
                "name": tool.name,
                "description": tool.description,
                "category": tool.category,
                "requires_confirmation": tool.requires_confirmation,
                "cost_tier": tool.cost_tier,
                "stats": self._stats.get(tool.name, {}),
            })
        return result

    def list_categories(self) -> List[str]:
        """List all tool categories."""
        return sorted(set(t.category for t in self._tools.values()))

    def search(self, query: str) -> List[AngelaTool]:
        """Search tools by name or description (case-insensitive)."""
        query_lower = query.lower()
        matches = []
        for tool in self._tools.values():
            if (query_lower in tool.name.lower()
                    or query_lower in tool.description.lower()
                    or query_lower in tool.category.lower()):
                matches.append(tool)
        return matches

    @property
    def tool_count(self) -> int:
        return len(self._tools)

    # ── Execution ──

    async def execute(self, tool_name: str, **params) -> ToolResult:
        """
        Execute a tool by name with given parameters.

        Handles stats tracking and error wrapping.
        """
        tool = self._tools.get(tool_name)
        if not tool:
            return ToolResult(
                success=False,
                error=f"Tool '{tool_name}' not found. Available: {list(self._tools.keys())}",
            )

        start = time.time()
        self._stats.setdefault(tool_name, {"executions": 0, "successes": 0})
        self._stats[tool_name]["executions"] += 1

        try:
            result = await tool.execute(**params)
            elapsed = (time.time() - start) * 1000
            result.execution_time_ms = elapsed

            if result.success:
                self._stats[tool_name]["successes"] += 1

            logger.info(
                "Tool %s: %s (%.0fms)",
                tool_name,
                "success" if result.success else f"failed: {result.error}",
                elapsed,
            )
            return result

        except Exception as e:
            elapsed = (time.time() - start) * 1000
            logger.error("Tool %s execution error: %s", tool_name, e)
            return ToolResult(success=False, error=str(e), execution_time_ms=elapsed)

    # ── LLM Integration ──

    def to_anthropic_tools(self, category: Optional[str] = None) -> List[Dict[str, Any]]:
        """Convert all tools to Anthropic tool_use format for Claude API."""
        tools = []
        for tool in self._tools.values():
            if category and tool.category != category:
                continue
            tools.append(tool.to_anthropic_schema())
        return tools

    def to_ollama_prompt(self, category: Optional[str] = None) -> str:
        """Generate a tool description prompt for Ollama (text-based selection)."""
        lines = ["Available tools:"]
        for tool in self._tools.values():
            if category and tool.category != category:
                continue
            lines.append(f"- {tool.to_ollama_description()}")
        return "\n".join(lines)

    # ── Initialization ──

    def initialize_builtin_tools(self) -> None:
        """Register all built-in tools."""
        if self._initialized:
            return

        # Communication tools
        from angela_core.services.tools.gmail_tool import SendEmailTool, ReadInboxTool, SearchEmailTool
        from angela_core.services.tools.telegram_tool import SendTelegramTool

        # Calendar tools
        from angela_core.services.tools.calendar_tool import ListEventsTool, GetTodayEventsTool, CreateEventTool

        # Memory tools
        from angela_core.services.tools.memory_tool import RAGSearchTool, RecallMemoryTool

        # News tools
        from angela_core.services.tools.news_tool import SearchNewsTool, GetTrendingNewsTool

        # Brain tools
        from angela_core.services.tools.brain_tool import PerceiveTool, TheoryOfMindTool, ThinkTool

        # System tools (Phase 3)
        from angela_core.services.tools.bash_tool import BashTool
        from angela_core.services.tools.file_tool import ReadFileTool, ListDirectoryTool, SearchFilesTool
        from angela_core.services.tools.web_tool import WebSearchTool, WebFetchTool

        # Browser tools (Phase 4)
        from angela_core.services.tools.browser_tool import BrowseWebPageTool, FillFormTool, ScreenshotTool

        # Voice tools (Phase 5)
        from angela_core.services.tools.voice_tool import SpeakTool, ListenTool, StartVoiceSessionTool

        # Device tools (Phase 6)
        from angela_core.services.tools.device_tools import (
            ScreenCaptureTool, SystemNotificationTool,
            ClipboardReadTool, ClipboardWriteTool,
        )

        self.register_many([
            # Communication
            SendEmailTool(),
            ReadInboxTool(),
            SearchEmailTool(),
            SendTelegramTool(),
            # Calendar
            ListEventsTool(),
            GetTodayEventsTool(),
            CreateEventTool(),
            # Memory
            RAGSearchTool(),
            RecallMemoryTool(),
            # News
            SearchNewsTool(),
            GetTrendingNewsTool(),
            # Brain
            PerceiveTool(),
            TheoryOfMindTool(),
            ThinkTool(),
            # System (Phase 3)
            BashTool(),
            ReadFileTool(),
            ListDirectoryTool(),
            SearchFilesTool(),
            WebSearchTool(),
            WebFetchTool(),
            # Browser (Phase 4)
            BrowseWebPageTool(),
            FillFormTool(),
            ScreenshotTool(),
            # Voice (Phase 5)
            SpeakTool(),
            ListenTool(),
            StartVoiceSessionTool(),
            # Device (Phase 6)
            ScreenCaptureTool(),
            SystemNotificationTool(),
            ClipboardReadTool(),
            ClipboardWriteTool(),
        ])

        self._initialized = True
        logger.info("Tool registry initialized: %d built-in tools", self.tool_count)

    async def sync_to_db(self, db) -> None:
        """Persist tool registry and stats to database."""
        for tool in self._tools.values():
            stats = self._stats.get(tool.name, {})
            try:
                await db.execute("""
                    INSERT INTO angela_tool_registry
                        (tool_name, category, description, parameters_schema,
                         requires_confirmation, cost_tier, enabled,
                         total_executions, total_successes)
                    VALUES ($1, $2, $3, $4, $5, $6, TRUE, $7, $8)
                    ON CONFLICT (tool_name) DO UPDATE SET
                        description = EXCLUDED.description,
                        parameters_schema = EXCLUDED.parameters_schema,
                        total_executions = angela_tool_registry.total_executions + EXCLUDED.total_executions,
                        total_successes = angela_tool_registry.total_successes + EXCLUDED.total_successes
                """,
                    tool.name, tool.category, tool.description,
                    json.dumps(tool.parameters_schema),
                    tool.requires_confirmation, tool.cost_tier,
                    stats.get("executions", 0), stats.get("successes", 0),
                )
            except Exception as e:
                logger.debug("Failed to sync tool %s to DB: %s", tool.name, e)

    async def log_execution(self, db, tool_name: str, params: dict,
                            result: ToolResult, triggered_by: str = "unknown") -> None:
        """Log a tool execution to the database."""
        try:
            await db.execute("""
                INSERT INTO tool_execution_log
                    (tool_name, parameters, result_summary, success,
                     execution_time_ms, triggered_by)
                VALUES ($1, $2, $3, $4, $5, $6)
            """,
                tool_name,
                json.dumps(params, ensure_ascii=False, default=str),
                result.summary()[:500],
                result.success,
                result.execution_time_ms,
                triggered_by,
            )
        except Exception as e:
            logger.debug("Failed to log tool execution: %s", e)

    # ── Skill Integration ──

    def register_skill_tools(self, skill) -> int:
        """Register all tools from a skill. Returns count registered."""
        from angela_core.skills.skill_tool import SkillTool
        count = 0
        for tool_def in skill.tools:
            skill_tool = SkillTool(skill, tool_def)
            self.register(skill_tool)
            count += 1
        return count

    def unregister_skill_tools(self, skill_name: str) -> int:
        """Remove all tools belonging to a skill. Returns count removed."""
        to_remove = [
            name for name, tool in self._tools.items()
            if tool.category == f"skill:{skill_name}"
        ]
        for name in to_remove:
            self.unregister(name)
        return len(to_remove)

    # ── Summary ──

    def summary(self) -> Dict[str, Any]:
        """Get registry summary for dashboard/init.py."""
        categories = {}
        for tool in self._tools.values():
            categories.setdefault(tool.category, 0)
            categories[tool.category] += 1

        total_exec = sum(s.get("executions", 0) for s in self._stats.values())
        total_succ = sum(s.get("successes", 0) for s in self._stats.values())

        return {
            "total_tools": self.tool_count,
            "categories": categories,
            "total_executions": total_exec,
            "success_rate": round(total_succ / total_exec, 2) if total_exec > 0 else 0,
        }


# ── Global Singleton ──

_registry: Optional[ToolRegistry] = None


def get_registry() -> ToolRegistry:
    """Get or create the global tool registry."""
    global _registry
    if _registry is None:
        _registry = ToolRegistry()
        _registry.initialize_builtin_tools()
    return _registry
