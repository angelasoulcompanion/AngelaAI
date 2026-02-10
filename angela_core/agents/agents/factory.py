"""
Shared agent factory — eliminates boilerplate across all 6 agent files.

Each agent file only needs to define its config + tool list,
then call create_agent() to get a configured CrewAI Agent.
"""

from crewai import Agent
from typing import List, Optional


def create_agent(
    config,
    tools: List,
    llm: Optional[object] = None,
    verbose: bool = True,
) -> Agent:
    """
    Create a CrewAI Agent from config and tools.

    Args:
        config: AgentConfig with role, goal, backstory, etc.
        tools: List of tool instances
        llm: Language model (optional)
        verbose: Show detailed output

    Returns:
        Configured Agent
    """
    return Agent(
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
