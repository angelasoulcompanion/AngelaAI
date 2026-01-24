"""
Memory Agent - Memory Keeper
🧠 จัดการและค้นหา memories

Author: Angela AI 💜
Created: 2025-01-25
"""

from crewai import Agent
from typing import Optional

from ..config import MEMORY_AGENT_CONFIG
from ..tools.memory_tools import (
    MemoryRecallTool,
    MemoryStoreTool,
    ConversationSearchTool,
)


def create_memory_agent(
    llm: Optional[object] = None,
    verbose: bool = True
) -> Agent:
    """
    Create Memory Agent instance.

    Args:
        llm: Language model to use (optional, uses default if not provided)
        verbose: Whether to show detailed output

    Returns:
        Configured Memory Agent
    """
    config = MEMORY_AGENT_CONFIG

    # Initialize tools
    tools = [
        MemoryRecallTool(),
        MemoryStoreTool(),
        ConversationSearchTool(),
    ]

    agent = Agent(
        role=config.role,
        goal=config.goal,
        backstory=config.backstory,
        tools=tools,
        verbose=verbose,
        allow_delegation=config.allow_delegation,
        max_iter=config.max_iter,
        max_rpm=config.max_rpm,
        cache=config.cache,
        llm=llm,
    )

    return agent
