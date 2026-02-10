"""Communication Agent - Email and Calendar Specialist 💬"""

from typing import Optional
from ..config import COMMUNICATION_AGENT_CONFIG
from ..tools.communication_tools import SendEmailTool, ReadEmailTool, CalendarListTool, CalendarCreateTool
from .factory import create_agent


def create_communication_agent(llm: Optional[object] = None, verbose: bool = True):
    return create_agent(
        config=COMMUNICATION_AGENT_CONFIG,
        tools=[SendEmailTool(), ReadEmailTool(), CalendarListTool(), CalendarCreateTool()],
        llm=llm, verbose=verbose,
    )
