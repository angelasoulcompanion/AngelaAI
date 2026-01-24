"""
Communication Agent - Email and Calendar Specialist
💬 จัดการ email, calendar, และ messaging

Author: Angela AI 💜
Created: 2025-01-25
"""

from crewai import Agent
from typing import Optional

from ..config import COMMUNICATION_AGENT_CONFIG
from ..tools.communication_tools import (
    SendEmailTool,
    ReadEmailTool,
    CalendarListTool,
    CalendarCreateTool,
)


def create_communication_agent(
    llm: Optional[object] = None,
    verbose: bool = True
) -> Agent:
    """
    Create Communication Agent instance.

    Args:
        llm: Language model to use (optional, uses default if not provided)
        verbose: Whether to show detailed output

    Returns:
        Configured Communication Agent
    """
    config = COMMUNICATION_AGENT_CONFIG

    # Initialize tools
    tools = [
        SendEmailTool(),
        ReadEmailTool(),
        CalendarListTool(),
        CalendarCreateTool(),
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
