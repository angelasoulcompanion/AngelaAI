"""Research Agent - Information Gathering Specialist 🔍"""

from typing import Optional
from ..config import RESEARCH_AGENT_CONFIG
from ..tools.research_tools import WebResearchTool, NewsSearchTool, KnowledgeSearchTool
from .factory import create_agent


def create_research_agent(llm: Optional[object] = None, verbose: bool = True):
    return create_agent(
        config=RESEARCH_AGENT_CONFIG,
        tools=[WebResearchTool(), NewsSearchTool(), KnowledgeSearchTool()],
        llm=llm, verbose=verbose,
    )
