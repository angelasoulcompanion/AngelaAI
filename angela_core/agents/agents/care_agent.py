"""Care Agent - Wellness Guardian 💜"""

from typing import Optional
from ..config import CARE_AGENT_CONFIG
from ..tools.care_tools import WellnessCheckTool, EmotionalSupportTool, MilestoneReminderTool
from .factory import create_agent


def create_care_agent(llm: Optional[object] = None, verbose: bool = True):
    return create_agent(
        config=CARE_AGENT_CONFIG,
        tools=[WellnessCheckTool(), EmotionalSupportTool(), MilestoneReminderTool()],
        llm=llm, verbose=verbose,
    )
