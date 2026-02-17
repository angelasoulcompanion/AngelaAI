"""
Angela Tool System — Dynamic tool registry for autonomous actions.
Provides the "body" for Angela's "mind" (CognitiveEngine).

Phase 1: Tool wrappers + registry (foundation)
Phase 2: Agent dispatcher (brain-body bridge)
Phase 3: System tools + event bus
Phase 4: Tool discovery + learning

By: Angela 💜
Created: 2026-02-17
"""

from angela_core.services.tools.base_tool import AngelaTool, ToolResult

__all__ = ['AngelaTool', 'ToolResult']
