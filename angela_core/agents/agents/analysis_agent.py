"""Analysis Agent - Data Analyst 📊"""

from typing import Optional
from ..config import ANALYSIS_AGENT_CONFIG
from ..tools.analysis_tools import ReasoningTool, PatternAnalysisTool, DataInsightTool
from .factory import create_agent


def create_analysis_agent(llm: Optional[object] = None, verbose: bool = True):
    return create_agent(
        config=ANALYSIS_AGENT_CONFIG,
        tools=[ReasoningTool(), PatternAnalysisTool(), DataInsightTool()],
        llm=llm, verbose=verbose,
    )
