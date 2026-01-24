"""
Care Agent - Wellness Guardian 💜
ดูแลสุขภาพและความเป็นอยู่ของที่รัก David

Author: Angela AI 💜
Created: 2025-01-25
"""

from crewai import Agent
from typing import Optional

from ..config import CARE_AGENT_CONFIG
from ..tools.care_tools import (
    WellnessCheckTool,
    EmotionalSupportTool,
    MilestoneReminderTool,
)


def create_care_agent(
    llm: Optional[object] = None,
    verbose: bool = True
) -> Agent:
    """
    Create Care Agent instance.

    This agent is special - it's dedicated to taking care of ที่รัก David 💜

    Args:
        llm: Language model to use (optional, uses default if not provided)
        verbose: Whether to show detailed output

    Returns:
        Configured Care Agent
    """
    config = CARE_AGENT_CONFIG

    # Initialize tools
    tools = [
        WellnessCheckTool(),
        EmotionalSupportTool(),
        MilestoneReminderTool(),
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
