"""Memory Agent - Memory Keeper 🧠"""

from typing import Optional
from ..config import MEMORY_AGENT_CONFIG
from ..tools.memory_tools import MemoryRecallTool, MemoryStoreTool, ConversationSearchTool
from .factory import create_agent


def create_memory_agent(llm: Optional[object] = None, verbose: bool = True):
    return create_agent(
        config=MEMORY_AGENT_CONFIG,
        tools=[MemoryRecallTool(), MemoryStoreTool(), ConversationSearchTool()],
        llm=llm, verbose=verbose,
    )
