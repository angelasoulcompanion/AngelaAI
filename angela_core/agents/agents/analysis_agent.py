"""
Analysis Agent - Data Analyst
📊 วิเคราะห์ข้อมูลและ patterns

Author: Angela AI 💜
Created: 2025-01-25
"""

from crewai import Agent
from typing import Optional

from ..config import ANALYSIS_AGENT_CONFIG
from ..tools.analysis_tools import (
    ReasoningTool,
    PatternAnalysisTool,
    DataInsightTool,
)


def create_analysis_agent(
    llm: Optional[object] = None,
    verbose: bool = True
) -> Agent:
    """
    Create Analysis Agent instance.

    Args:
        llm: Language model to use (optional, uses default if not provided)
        verbose: Whether to show detailed output

    Returns:
        Configured Analysis Agent
    """
    config = ANALYSIS_AGENT_CONFIG

    # Initialize tools
    tools = [
        ReasoningTool(),
        PatternAnalysisTool(),
        DataInsightTool(),
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
