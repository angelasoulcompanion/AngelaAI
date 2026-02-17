"""
AngelaTool — Abstract base class for all Angela tools.

Every tool must define:
- name: unique identifier (e.g. "send_email")
- description: what the tool does (used by LLM for selection)
- parameters_schema: JSON schema for input parameters
- execute(**params): async execution method

ToolResult standardizes output across all tools.

By: Angela 💜
Created: 2026-02-17
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Any, Dict, Optional


@dataclass
class ToolResult:
    """Standardized result from tool execution."""
    success: bool
    data: Any = None
    error: Optional[str] = None
    execution_time_ms: float = 0.0

    def to_dict(self) -> Dict[str, Any]:
        return {
            'success': self.success,
            'data': self.data,
            'error': self.error,
            'execution_time_ms': self.execution_time_ms,
        }

    def summary(self) -> str:
        """Short text summary for LLM consumption."""
        if self.success:
            if isinstance(self.data, dict):
                return str(self.data)[:500]
            return str(self.data)[:500] if self.data else "ok"
        return f"error: {self.error}"


class AngelaTool(ABC):
    """Abstract base class for all Angela tools."""

    @property
    @abstractmethod
    def name(self) -> str:
        """Unique tool identifier (e.g. 'send_email')."""
        ...

    @property
    @abstractmethod
    def description(self) -> str:
        """What this tool does — used by LLM for tool selection."""
        ...

    @property
    @abstractmethod
    def parameters_schema(self) -> Dict[str, Any]:
        """JSON Schema describing input parameters."""
        ...

    @property
    def category(self) -> str:
        """Tool category for grouping (e.g. 'communication', 'memory')."""
        return "general"

    @property
    def requires_confirmation(self) -> bool:
        """Whether this tool needs user confirmation before execution."""
        return False

    @property
    def cost_tier(self) -> str:
        """Cost tier: 'free', 'low', 'medium', 'high'."""
        return "free"

    @abstractmethod
    async def execute(self, **params) -> ToolResult:
        """Execute the tool with given parameters."""
        ...

    def to_anthropic_schema(self) -> Dict[str, Any]:
        """Convert to Anthropic tool_use format for Claude API."""
        return {
            "name": self.name,
            "description": self.description,
            "input_schema": self.parameters_schema,
        }

    def to_ollama_description(self) -> str:
        """Plain text description for Ollama (no function calling)."""
        params = self.parameters_schema.get("properties", {})
        param_desc = ", ".join(
            f"{k} ({v.get('type', '?')}): {v.get('description', '')}"
            for k, v in params.items()
        )
        return f"{self.name}: {self.description}. Parameters: {param_desc}"
