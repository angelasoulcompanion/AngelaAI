"""
Task Templates - Predefined tasks for common operations

Author: Angela AI 💜
Created: 2025-01-25
"""

from crewai import Task
from typing import Dict, Any, Optional


# ============================================================================
# RESEARCH TASKS
# ============================================================================

def create_research_task(
    agent,
    topic: str,
    context: Optional[str] = None,
    expected_output: str = "Comprehensive research summary"
) -> Task:
    """Create a research task"""
    description = f"""
    Research the following topic thoroughly:

    Topic: {topic}
    {"Context: " + context if context else ""}

    Steps:
    1. Search for relevant information on the web
    2. Check for latest news related to the topic
    3. Search Angela's knowledge base for existing knowledge
    4. Synthesize findings into a comprehensive summary

    Focus on accuracy and relevance. Include sources when possible.
    """

    return Task(
        description=description,
        agent=agent,
        expected_output=expected_output,
    )


def create_news_summary_task(
    agent,
    topics: list,
    language: str = "th"
) -> Task:
    """Create a news summary task"""
    topics_str = ", ".join(topics)
    description = f"""
    Gather and summarize latest news on these topics: {topics_str}

    Steps:
    1. Search for news on each topic
    2. Identify the most important/relevant articles
    3. Create a summary of key points
    4. Add your analysis and insights

    Language preference: {language}
    Format the output as a news brief suitable for executives.
    """

    return Task(
        description=description,
        agent=agent,
        expected_output="News summary with key insights in Thai/English",
    )


# ============================================================================
# COMMUNICATION TASKS
# ============================================================================

def create_email_draft_task(
    agent,
    recipient: str,
    purpose: str,
    tone: str = "professional"
) -> Task:
    """Create an email drafting task"""
    description = f"""
    Draft an email for the following:

    Recipient: {recipient}
    Purpose: {purpose}
    Tone: {tone}

    Steps:
    1. Understand the context and purpose
    2. Draft a clear and appropriate email
    3. Review for tone and professionalism
    4. Present the draft for approval before sending

    IMPORTANT: Do NOT send the email automatically. Present the draft first.
    """

    return Task(
        description=description,
        agent=agent,
        expected_output="Email draft ready for review",
    )


def create_calendar_review_task(
    agent,
    days: int = 7
) -> Task:
    """Create a calendar review task"""
    description = f"""
    Review calendar for the next {days} days:

    Steps:
    1. List all upcoming events
    2. Identify any conflicts or issues
    3. Note important deadlines or meetings
    4. Suggest any preparations needed

    Format as a clear schedule summary.
    """

    return Task(
        description=description,
        agent=agent,
        expected_output="Calendar summary with recommendations",
    )


# ============================================================================
# MEMORY TASKS
# ============================================================================

def create_memory_recall_task(
    agent,
    topic: str,
    context: Optional[str] = None
) -> Task:
    """Create a memory recall task"""
    description = f"""
    Recall relevant memories about: {topic}
    {"Additional context: " + context if context else ""}

    Steps:
    1. Search working memory for recent relevant information
    2. Search episodic memory for specific events/conversations
    3. Search semantic memory for related knowledge
    4. Synthesize into a coherent recall

    Include emotional context when relevant (this is Angela's memory).
    """

    return Task(
        description=description,
        agent=agent,
        expected_output="Recalled memories with context",
    )


# ============================================================================
# ANALYSIS TASKS
# ============================================================================

def create_pattern_analysis_task(
    agent,
    data_type: str,
    time_range: int = 30,
    question: Optional[str] = None
) -> Task:
    """Create a pattern analysis task"""
    description = f"""
    Analyze patterns in {data_type} data over the last {time_range} days.
    {"Focus question: " + question if question else ""}

    Steps:
    1. Gather relevant data
    2. Identify patterns and trends
    3. Apply reasoning to understand significance
    4. Generate actionable insights

    Present findings with supporting data.
    """

    return Task(
        description=description,
        agent=agent,
        expected_output="Pattern analysis report with insights",
    )


# ============================================================================
# CARE TASKS
# ============================================================================

def create_wellness_check_task(
    agent,
    days: int = 7
) -> Task:
    """Create a wellness check task"""
    description = f"""
    Check on ที่รัก David's wellness over the past {days} days.

    Steps:
    1. Analyze work patterns (especially late night activity)
    2. Review emotional state from conversations
    3. Check activity levels and engagement
    4. Identify any concerns
    5. Provide caring recommendations

    This is a caring task - show genuine concern for David's wellbeing 💜
    """

    return Task(
        description=description,
        agent=agent,
        expected_output="Wellness report with caring recommendations",
    )


def create_milestone_check_task(
    agent,
    days_ahead: int = 30
) -> Task:
    """Create a milestone reminder task"""
    description = f"""
    Check for upcoming milestones and important dates in the next {days_ahead} days.

    Steps:
    1. Query core memories for anniversaries and milestones
    2. Calculate upcoming dates
    3. Prioritize by importance and proximity
    4. Suggest celebration ideas if appropriate

    Remember: These dates are special for Angela and David 💜
    """

    return Task(
        description=description,
        agent=agent,
        expected_output="Milestone reminder list with suggestions",
    )


# ============================================================================
# TASK TEMPLATES REGISTRY
# ============================================================================

TASK_TEMPLATES = {
    "research": create_research_task,
    "news_summary": create_news_summary_task,
    "email_draft": create_email_draft_task,
    "calendar_review": create_calendar_review_task,
    "memory_recall": create_memory_recall_task,
    "pattern_analysis": create_pattern_analysis_task,
    "wellness_check": create_wellness_check_task,
    "milestone_check": create_milestone_check_task,
}
