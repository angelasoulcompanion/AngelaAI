"""
Research Agent - Information Gathering Specialist
🔍 ค้นหาข้อมูลจาก web, news, และ knowledge base

Author: Angela AI 💜
Created: 2025-01-25
"""

from crewai import Agent
from typing import Optional

from ..config import RESEARCH_AGENT_CONFIG
from ..tools.research_tools import (
    WebResearchTool,
    NewsSearchTool,
    KnowledgeSearchTool,
)


def create_research_agent(
    llm: Optional[object] = None,
    verbose: bool = True
) -> Agent:
    """
    Create Research Agent instance.

    Args:
        llm: Language model to use (optional, uses default if not provided)
        verbose: Whether to show detailed output

    Returns:
        Configured Research Agent
    """
    config = RESEARCH_AGENT_CONFIG

    # Initialize tools
    tools = [
        WebResearchTool(),
        NewsSearchTool(),
        KnowledgeSearchTool(),
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
