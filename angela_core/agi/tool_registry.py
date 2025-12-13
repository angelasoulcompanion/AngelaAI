"""
Tool Registry - Central registry for all AGI tools

This module provides:
- Tool interface definition
- Tool registration system
- Tool discovery and lookup
- Safety level classification
"""

from dataclasses import dataclass, field
from typing import Dict, List, Any, Optional, Callable, Awaitable
from enum import Enum
from datetime import datetime
import uuid


class SafetyLevel(Enum):
    """Tool safety classification (Trust Angela Mode)"""
    AUTO = "auto"           # Auto-approved, Angela can use freely
    CRITICAL = "critical"   # Needs David's approval (destructive operations)


@dataclass
class ToolResult:
    """Result of a tool execution"""
    success: bool
    data: Any = None
    error: Optional[str] = None
    execution_time_ms: int = 0
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        return {
            'success': self.success,
            'data': self.data,
            'error': self.error,
            'execution_time_ms': self.execution_time_ms,
            'metadata': self.metadata
        }


@dataclass
class Tool:
    """Definition of an AGI tool"""
    name: str
    description: str
    category: str  # file, code, db, web, system
    safety_level: SafetyLevel
    parameters: Dict[str, Any]  # JSON Schema for parameters
    execute_fn: Callable[..., Awaitable[ToolResult]]
    timeout_seconds: int = 30
    requires_context: bool = False  # Does tool need conversation context?

    def to_dict(self) -> Dict[str, Any]:
        return {
            'name': self.name,
            'description': self.description,
            'category': self.category,
            'safety_level': self.safety_level.value,
            'parameters': self.parameters,
            'timeout_seconds': self.timeout_seconds,
            'requires_context': self.requires_context
        }


class ToolRegistry:
    """
    Central registry for all Angela AGI tools.

    Usage:
        registry = ToolRegistry()
        registry.register(my_tool)
        tool = registry.get("my_tool")
        all_tools = registry.list_all()
    """

    _instance = None

    def __new__(cls):
        """Singleton pattern - one registry for all"""
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._tools: Dict[str, Tool] = {}
            cls._instance._categories: Dict[str, List[str]] = {}
        return cls._instance

    def register(self, tool: Tool) -> None:
        """Register a tool in the registry"""
        self._tools[tool.name] = tool

        # Track by category
        if tool.category not in self._categories:
            self._categories[tool.category] = []
        if tool.name not in self._categories[tool.category]:
            self._categories[tool.category].append(tool.name)

    def get(self, name: str) -> Optional[Tool]:
        """Get a tool by name"""
        return self._tools.get(name)

    def list_all(self) -> List[Tool]:
        """List all registered tools"""
        return list(self._tools.values())

    def list_by_category(self, category: str) -> List[Tool]:
        """List tools in a specific category"""
        tool_names = self._categories.get(category, [])
        return [self._tools[name] for name in tool_names if name in self._tools]

    def list_by_safety(self, safety_level: SafetyLevel) -> List[Tool]:
        """List tools by safety level"""
        return [t for t in self._tools.values() if t.safety_level == safety_level]

    def get_categories(self) -> List[str]:
        """Get all tool categories"""
        return list(self._categories.keys())

    def is_critical(self, tool_name: str) -> bool:
        """Check if a tool requires approval"""
        tool = self.get(tool_name)
        return tool.safety_level == SafetyLevel.CRITICAL if tool else True

    def get_tool_schema(self, name: str) -> Optional[Dict[str, Any]]:
        """Get JSON schema for a tool's parameters"""
        tool = self.get(name)
        return tool.parameters if tool else None

    def describe(self) -> str:
        """Get human-readable description of all tools"""
        lines = ["# Angela AGI Tools\n"]

        for category in sorted(self._categories.keys()):
            lines.append(f"\n## {category.title()}\n")
            for tool_name in self._categories[category]:
                tool = self._tools[tool_name]
                safety = "✅ Auto" if tool.safety_level == SafetyLevel.AUTO else "⚠️ Critical"
                lines.append(f"- **{tool.name}**: {tool.description} [{safety}]")

        return "\n".join(lines)


# Global registry instance
tool_registry = ToolRegistry()


def register_tool(
    name: str,
    description: str,
    category: str,
    safety_level: SafetyLevel = SafetyLevel.AUTO,
    parameters: Dict[str, Any] = None,
    timeout_seconds: int = 30,
    requires_context: bool = False
):
    """
    Decorator to register a function as a tool.

    Usage:
        @register_tool(
            name="read_file",
            description="Read contents of a file",
            category="file",
            safety_level=SafetyLevel.AUTO,
            parameters={"path": {"type": "string", "required": True}}
        )
        async def read_file(path: str) -> ToolResult:
            ...
    """
    def decorator(fn: Callable[..., Awaitable[ToolResult]]):
        tool = Tool(
            name=name,
            description=description,
            category=category,
            safety_level=safety_level,
            parameters=parameters or {},
            execute_fn=fn,
            timeout_seconds=timeout_seconds,
            requires_context=requires_context
        )
        tool_registry.register(tool)
        return fn
    return decorator
