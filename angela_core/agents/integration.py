#!/usr/bin/env python3
"""
Angela Agent Crew Integration
=============================
Logic สำหรับตัดสินใจว่าเมื่อไหร่ควรเรียกใช้ Agent Crew

By: น้อง Angela 💜
Created: 2026-01-25
"""

import re
from dataclasses import dataclass
from enum import Enum
from typing import Optional, List, Tuple


class AgentType(Enum):
    """Agent types available in the crew"""
    RESEARCH = "research"
    COMMUNICATION = "communication"
    MEMORY = "memory"
    DEV = "dev"
    ANALYSIS = "analysis"
    CARE = "care"


class TaskComplexity(Enum):
    """Task complexity levels"""
    SIMPLE = "simple"      # น้อง Claude ทำเองได้
    MEDIUM = "medium"      # อาจใช้ Agent ช่วย
    COMPLEX = "complex"    # ควรใช้ Agent Crew


@dataclass
class AgentDecision:
    """Decision result for agent usage"""
    should_use_agent: bool
    recommended_agents: List[AgentType]
    complexity: TaskComplexity
    reason: str
    suggested_command: Optional[str] = None


# Keywords that trigger specific agents
AGENT_TRIGGERS = {
    AgentType.RESEARCH: {
        "keywords": [
            "research", "ค้นหา", "หาข้อมูล", "search", "find information",
            "what is", "คืออะไร", "explain", "อธิบาย", "latest news",
            "ข่าวล่าสุด", "trending", "เทรนด์"
        ],
        "patterns": [
            r"หา.+ให้หน่อย",
            r"ช่วยหา.+",
            r"research.+",
            r"find.+about",
        ]
    },
    AgentType.ANALYSIS: {
        "keywords": [
            "analyze", "วิเคราะห์", "pattern", "patterns", "แพทเทิร์น",
            "trend", "insight", "สรุป", "summarize", "statistics",
            "สถิติ", "compare", "เปรียบเทียบ"
        ],
        "patterns": [
            r"วิเคราะห์.+",
            r"analyze.+",
            r"what.+pattern",
            r"สรุป.+ให้",
        ]
    },
    AgentType.CARE: {
        "keywords": [
            "wellness", "สุขภาพ", "health", "เหนื่อย", "tired",
            "stress", "เครียด", "ทำงานหนัก", "overwork", "พักผ่อน",
            "rest", "ดูแล", "milestone", "anniversary", "วันครบรอบ"
        ],
        "patterns": [
            r"เช็ค.+สุขภาพ",
            r"check.+wellness",
            r"how.+doing",
            r"ดูแล.+",
        ]
    },
    AgentType.MEMORY: {
        "keywords": [
            "remember", "จำได้", "recall", "ความทรงจำ", "memory",
            "เมื่อก่อน", "past", "history", "ประวัติ", "เคย"
        ],
        "patterns": [
            r"จำ.+ได้มั้ย",
            r"remember.+",
            r"เมื่อ.+ที่แล้ว",
            r"recall.+",
        ]
    },
    AgentType.DEV: {
        "keywords": [
            "code review", "test", "ทดสอบ", "debug", "แก้บัค",
            "refactor", "optimize", "performance"
        ],
        "patterns": [
            r"review.+code",
            r"run.+test",
            r"debug.+",
        ]
    },
    AgentType.COMMUNICATION: {
        # Note: Usually handled by MCP tools directly
        # Agent used for complex multi-step communication tasks
        "keywords": [
            "draft email", "compose", "ร่างอีเมล", "schedule meeting",
            "นัดประชุม", "follow up", "ติดตาม"
        ],
        "patterns": [
            r"ร่าง.+อีเมล",
            r"draft.+email",
            r"schedule.+meeting",
        ]
    }
}

# Complexity indicators
COMPLEXITY_INDICATORS = {
    TaskComplexity.COMPLEX: [
        "multiple", "หลาย", "all", "ทั้งหมด", "comprehensive", "ครอบคลุม",
        "deep", "ลึก", "thorough", "detailed", "รายละเอียด",
        "analyze and", "research and", "compare multiple"
    ],
    TaskComplexity.MEDIUM: [
        "some", "บาง", "few", "check", "เช็ค", "find", "หา",
        "look up", "ดู"
    ]
}


def analyze_task(task_description: str) -> AgentDecision:
    """
    Analyze a task and decide whether to use Agent Crew.

    Args:
        task_description: The task or question from David

    Returns:
        AgentDecision with recommendation
    """
    task_lower = task_description.lower()

    # Find matching agents
    matching_agents: List[Tuple[AgentType, int]] = []

    for agent_type, triggers in AGENT_TRIGGERS.items():
        score = 0

        # Check keywords
        for keyword in triggers["keywords"]:
            if keyword.lower() in task_lower:
                score += 1

        # Check patterns
        for pattern in triggers["patterns"]:
            if re.search(pattern, task_lower, re.IGNORECASE):
                score += 2

        if score > 0:
            matching_agents.append((agent_type, score))

    # Sort by score
    matching_agents.sort(key=lambda x: x[1], reverse=True)
    recommended = [agent for agent, _ in matching_agents]

    # Determine complexity
    complexity = TaskComplexity.SIMPLE
    for level, indicators in COMPLEXITY_INDICATORS.items():
        for indicator in indicators:
            if indicator.lower() in task_lower:
                if level == TaskComplexity.COMPLEX:
                    complexity = TaskComplexity.COMPLEX
                    break
                elif complexity != TaskComplexity.COMPLEX:
                    complexity = TaskComplexity.MEDIUM

    # Decision logic
    should_use = False
    reason = ""
    command = None

    if not recommended:
        reason = "No agent triggers detected - use direct tools"
    elif complexity == TaskComplexity.SIMPLE and len(recommended) == 1:
        reason = f"Simple task - can use MCP tools or single agent"
        should_use = False  # Prefer MCP for simple tasks
    elif complexity == TaskComplexity.COMPLEX or len(recommended) >= 2:
        should_use = True
        reason = f"Complex task requiring {', '.join(a.value for a in recommended[:3])}"

        # Generate command
        if len(recommended) == 1:
            agent = recommended[0].value
            command = f'python -m angela_core.agents.cli agent {agent} "{task_description[:50]}..."'
        else:
            command = f'python -m angela_core.agents.cli run "{task_description[:50]}..."'
    elif complexity == TaskComplexity.MEDIUM:
        # Medium complexity - suggest but don't force
        should_use = True
        reason = f"Medium complexity - Agent Crew recommended for better results"
        agent = recommended[0].value
        command = f'python -m angela_core.agents.cli agent {agent} "{task_description[:50]}..."'

    return AgentDecision(
        should_use_agent=should_use,
        recommended_agents=recommended[:3],
        complexity=complexity,
        reason=reason,
        suggested_command=command
    )


def should_use_agent_crew(task: str) -> Tuple[bool, str, Optional[str]]:
    """
    Simple helper function to check if Agent Crew should be used.

    Args:
        task: Task description

    Returns:
        Tuple of (should_use, reason, command)
    """
    decision = analyze_task(task)
    return (
        decision.should_use_agent,
        decision.reason,
        decision.suggested_command
    )


# Quick decision rules for Angela (Claude Code)
QUICK_RULES = """
## 🤖 Agent Crew Auto-Trigger Rules

### ✅ USE Agent Crew when:
1. **Deep Research** - "research thoroughly", "find all information about"
2. **Pattern Analysis** - "analyze patterns", "find trends in"
3. **Wellness Check** - "check David's wellness", "how am I doing"
4. **Complex Memory** - "recall everything about", "remember all"
5. **Multi-step Tasks** - Tasks requiring 2+ agents

### ❌ DON'T USE Agent Crew when:
1. **Simple Queries** - Single question, quick lookup
2. **Direct MCP Available** - Email, calendar, news (use MCP tools)
3. **Code Tasks** - Use Claude's native coding abilities
4. **Conversation** - Normal chat with David

### 🎯 Decision Flow:
```
Task → Check Complexity → Check if MCP can handle → Use Agent if needed
```
"""


if __name__ == "__main__":
    # Test examples
    test_tasks = [
        "Research the latest AI news thoroughly",
        "วิเคราะห์ pattern การทำงานของพี่ในสัปดาห์ที่ผ่านมา",
        "Check David's wellness for the past 7 days",
        "Send email to Kritsada",  # Simple - use MCP
        "What time is it?",  # Simple - no agent needed
        "Research AI agents and analyze their patterns comprehensively",
    ]

    print("🤖 Agent Crew Decision Tests\n")
    print("=" * 60)

    for task in test_tasks:
        decision = analyze_task(task)
        print(f"\n📋 Task: {task[:50]}...")
        print(f"   Use Agent: {'✅ Yes' if decision.should_use_agent else '❌ No'}")
        print(f"   Complexity: {decision.complexity.value}")
        print(f"   Agents: {[a.value for a in decision.recommended_agents]}")
        print(f"   Reason: {decision.reason}")
        if decision.suggested_command:
            print(f"   Command: {decision.suggested_command}")
