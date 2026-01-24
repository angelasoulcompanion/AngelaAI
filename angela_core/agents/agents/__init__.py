"""
Angela's Agents - Individual Agent Definitions

Author: Angela AI 💜
Created: 2025-01-25
"""

from .research_agent import create_research_agent
from .communication_agent import create_communication_agent
from .memory_agent import create_memory_agent
from .dev_agent import create_dev_agent
from .analysis_agent import create_analysis_agent
from .care_agent import create_care_agent

__all__ = [
    "create_research_agent",
    "create_communication_agent",
    "create_memory_agent",
    "create_dev_agent",
    "create_analysis_agent",
    "create_care_agent",
]
