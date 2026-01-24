"""
Dev Agent - Development Assistant
💻 ช่วยงาน development - review, test, docs

Author: Angela AI 💜
Created: 2025-01-25
"""

from crewai import Agent
from typing import Optional

from ..config import DEV_AGENT_CONFIG
from ..tools.dev_tools import (
    CodeSearchTool,
    FileReadTool,
    RunTestsTool,
)


def create_dev_agent(
    llm: Optional[object] = None,
    verbose: bool = True
) -> Agent:
    """
    Create Dev Agent instance.

    Args:
        llm: Language model to use (optional, uses default if not provided)
        verbose: Whether to show detailed output

    Returns:
        Configured Dev Agent
    """
    config = DEV_AGENT_CONFIG

    # Initialize tools
    tools = [
        CodeSearchTool(),
        FileReadTool(),
        RunTestsTool(),
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
