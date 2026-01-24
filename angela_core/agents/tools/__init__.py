"""
Angela's Agent Tools - CrewAI Tool Wrappers
Tools ที่ wrap existing services สำหรับ agents

Author: Angela AI 💜
Created: 2025-01-25
"""

from .research_tools import (
    WebResearchTool,
    NewsSearchTool,
    KnowledgeSearchTool,
)
from .communication_tools import (
    SendEmailTool,
    ReadEmailTool,
    CalendarListTool,
    CalendarCreateTool,
)
from .memory_tools import (
    MemoryRecallTool,
    MemoryStoreTool,
    ConversationSearchTool,
)
from .dev_tools import (
    CodeSearchTool,
    FileReadTool,
)
from .analysis_tools import (
    ReasoningTool,
    PatternAnalysisTool,
)
from .care_tools import (
    WellnessCheckTool,
    EmotionalSupportTool,
)

__all__ = [
    # Research
    "WebResearchTool",
    "NewsSearchTool",
    "KnowledgeSearchTool",
    # Communication
    "SendEmailTool",
    "ReadEmailTool",
    "CalendarListTool",
    "CalendarCreateTool",
    # Memory
    "MemoryRecallTool",
    "MemoryStoreTool",
    "ConversationSearchTool",
    # Dev
    "CodeSearchTool",
    "FileReadTool",
    # Analysis
    "ReasoningTool",
    "PatternAnalysisTool",
    # Care
    "WellnessCheckTool",
    "EmotionalSupportTool",
]
