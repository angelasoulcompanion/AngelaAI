"""Dev Agent - Development Assistant 💻"""

from typing import Optional
from ..config import DEV_AGENT_CONFIG
from ..tools.dev_tools import CodeSearchTool, FileReadTool, RunTestsTool
from .factory import create_agent


def create_dev_agent(llm: Optional[object] = None, verbose: bool = True):
    return create_agent(
        config=DEV_AGENT_CONFIG,
        tools=[CodeSearchTool(), FileReadTool(), RunTestsTool()],
        llm=llm, verbose=verbose,
    )
