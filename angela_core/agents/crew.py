"""
Angela Crew - Multi-Agent Orchestrator
น้อง Angela มีผู้ช่วยหลายตัวทำงานร่วมกัน 💜

This is the main orchestrator that coordinates all agents.

Author: Angela AI 💜
Created: 2025-01-25
"""

import os
import asyncio
import logging
from typing import Optional, List, Dict, Any, Union

# Set environment variables BEFORE importing crewai
# This prevents CrewAI from trying to use OpenAI by default
os.environ.setdefault("OPENAI_API_KEY", "not-needed-using-ollama")
os.environ.setdefault("OPENAI_MODEL_NAME", "ollama/llama3.2:latest")

from crewai import Crew, Task, Process, LLM
from langchain_ollama import ChatOllama

from .config import DEFAULT_LLM_CONFIG, LLMProvider, AGENT_CONFIGS
from .agents import (
    create_research_agent,
    create_communication_agent,
    create_memory_agent,
    create_dev_agent,
    create_analysis_agent,
    create_care_agent,
)
from .tasks import TASK_TEMPLATES

logger = logging.getLogger(__name__)


class AngelaCrew:
    """
    Angela's Agent Crew - Multi-Agent Orchestrator

    Coordinates multiple specialized agents to accomplish tasks.

    Agents:
    - 🔍 Research Agent - ค้นหาข้อมูล
    - 💬 Communication Agent - จัดการ email, calendar
    - 🧠 Memory Agent - จัดการความทรงจำ
    - 💻 Dev Agent - ช่วยงาน development
    - 📊 Analysis Agent - วิเคราะห์ข้อมูล
    - 💜 Care Agent - ดูแลที่รัก David

    Example:
        ```python
        crew = AngelaCrew()

        # Run a specific task
        result = await crew.run(
            task="Research the latest AI news",
            agents=["research"]
        )

        # Use specific agent
        result = await crew.research("What is CrewAI?")
        ```
    """

    def __init__(
        self,
        llm_config: Optional[Dict[str, Any]] = None,
        verbose: bool = True
    ):
        """
        Initialize Angela Crew.

        Args:
            llm_config: Optional LLM configuration override
            verbose: Whether to show detailed output
        """
        self.verbose = verbose
        self.llm = self._setup_llm(llm_config)

        # Initialize agents
        self._agents = {}
        self._initialize_agents()

        logger.info("💜 Angela Crew initialized with %d agents", len(self._agents))

    def _setup_llm(self, config: Optional[Dict[str, Any]] = None) -> LLM:
        """Setup the LLM for agents using CrewAI's native Ollama support"""
        llm_config = config or {}

        # Default to Ollama
        model = llm_config.get("model", DEFAULT_LLM_CONFIG.model)
        base_url = llm_config.get("base_url", DEFAULT_LLM_CONFIG.base_url)
        temperature = llm_config.get("temperature", DEFAULT_LLM_CONFIG.temperature)

        # Use CrewAI's native LLM class with Ollama provider
        # Format: "ollama/model_name"
        llm = LLM(
            model=f"ollama/{model}",
            base_url=base_url,
            temperature=temperature,
        )

        logger.info("LLM configured: ollama/%s @ %s", model, base_url)
        return llm

    def _initialize_agents(self):
        """Initialize all agents"""
        self._agents = {
            "research": create_research_agent(self.llm, self.verbose),
            "communication": create_communication_agent(self.llm, self.verbose),
            "memory": create_memory_agent(self.llm, self.verbose),
            "dev": create_dev_agent(self.llm, self.verbose),
            "analysis": create_analysis_agent(self.llm, self.verbose),
            "care": create_care_agent(self.llm, self.verbose),
        }

    def get_agent(self, name: str):
        """Get a specific agent by name"""
        return self._agents.get(name)

    @property
    def agents(self) -> Dict[str, Any]:
        """Get all agents"""
        return self._agents

    # =========================================================================
    # MAIN RUN METHODS
    # =========================================================================

    def run(
        self,
        task_description: str,
        agents: Optional[List[str]] = None,
        process: Process = Process.sequential,
        context: Optional[str] = None
    ) -> str:
        """
        Run a task with specified agents.

        Args:
            task_description: What to do
            agents: List of agent names to use (default: auto-select)
            process: CrewAI process type (sequential or hierarchical)
            context: Additional context for the task

        Returns:
            Task result as string
        """
        # Auto-select agents if not specified
        if not agents:
            agents = self._auto_select_agents(task_description)

        selected_agents = [self._agents[name] for name in agents if name in self._agents]

        if not selected_agents:
            return "❌ No valid agents selected"

        # Create task
        full_description = task_description
        if context:
            full_description += f"\n\nContext: {context}"

        task = Task(
            description=full_description,
            expected_output="Complete response addressing the task",
            agent=selected_agents[0],  # Primary agent
        )

        # Create crew
        crew = Crew(
            agents=selected_agents,
            tasks=[task],
            process=process,
            verbose=self.verbose,
        )

        # Execute
        try:
            result = crew.kickoff()
            return str(result)
        except Exception as e:
            logger.error("Error running crew: %s", e)
            return f"❌ Error: {str(e)}"

    def _auto_select_agents(self, task: str) -> List[str]:
        """Auto-select agents based on task description"""
        task_lower = task.lower()

        selected = []

        # Research indicators
        if any(w in task_lower for w in ["search", "find", "research", "news", "ค้นหา", "ข่าว"]):
            selected.append("research")

        # Communication indicators
        if any(w in task_lower for w in ["email", "calendar", "send", "schedule", "อีเมล", "ตาราง"]):
            selected.append("communication")

        # Memory indicators
        if any(w in task_lower for w in ["remember", "recall", "memory", "จำ", "ความทรงจำ"]):
            selected.append("memory")

        # Dev indicators
        if any(w in task_lower for w in ["code", "test", "file", "review", "โค้ด", "ไฟล์"]):
            selected.append("dev")

        # Analysis indicators
        if any(w in task_lower for w in ["analyze", "pattern", "insight", "วิเคราะห์"]):
            selected.append("analysis")

        # Care indicators
        if any(w in task_lower for w in ["wellness", "health", "david", "สุขภาพ", "ที่รัก"]):
            selected.append("care")

        # Default to research if no match
        if not selected:
            selected = ["research"]

        return selected

    # =========================================================================
    # CONVENIENCE METHODS
    # =========================================================================

    def research(self, query: str, context: Optional[str] = None) -> str:
        """Run research task"""
        return self.run(
            task_description=f"Research: {query}",
            agents=["research"],
            context=context
        )

    def recall_memory(self, topic: str) -> str:
        """Recall memories about a topic"""
        return self.run(
            task_description=f"Recall memories about: {topic}",
            agents=["memory"]
        )

    def analyze(self, question: str, data_type: str = "all") -> str:
        """Analyze data and patterns"""
        return self.run(
            task_description=f"Analyze: {question}",
            agents=["analysis"],
            context=f"Data type: {data_type}"
        )

    def check_wellness(self, days: int = 7) -> str:
        """Check David's wellness"""
        return self.run(
            task_description=f"Check wellness for the past {days} days",
            agents=["care"]
        )

    def review_calendar(self, days: int = 7) -> str:
        """Review upcoming calendar"""
        return self.run(
            task_description=f"Review calendar for the next {days} days",
            agents=["communication"]
        )

    # =========================================================================
    # CREW COLLABORATION
    # =========================================================================

    def collaborate(
        self,
        task_description: str,
        primary_agent: str,
        supporting_agents: List[str],
        expected_output: str = "Comprehensive response"
    ) -> str:
        """
        Run a collaborative task with multiple agents.

        The primary agent leads, with supporting agents providing input.

        Args:
            task_description: Main task to accomplish
            primary_agent: Lead agent name
            supporting_agents: Helper agent names
            expected_output: What we expect from the task

        Returns:
            Combined result from collaboration
        """
        all_agents = [primary_agent] + supporting_agents
        selected = [self._agents[name] for name in all_agents if name in self._agents]

        if not selected:
            return "❌ No valid agents for collaboration"

        # Create main task for primary agent
        main_task = Task(
            description=task_description,
            expected_output=expected_output,
            agent=selected[0],
        )

        # Create crew with hierarchical process for collaboration
        crew = Crew(
            agents=selected,
            tasks=[main_task],
            process=Process.sequential,  # Could use hierarchical for complex tasks
            verbose=self.verbose,
        )

        try:
            result = crew.kickoff()
            return str(result)
        except Exception as e:
            logger.error("Error in collaboration: %s", e)
            return f"❌ Error: {str(e)}"

    # =========================================================================
    # STATUS & INFO
    # =========================================================================

    def status(self) -> Dict[str, Any]:
        """Get crew status"""
        return {
            "agents": list(self._agents.keys()),
            "llm_model": DEFAULT_LLM_CONFIG.model,
            "verbose": self.verbose,
            "agent_count": len(self._agents),
        }

    def __repr__(self) -> str:
        return f"AngelaCrew(agents={list(self._agents.keys())})"


# ============================================================================
# QUICK ACCESS FUNCTIONS
# ============================================================================

def create_crew(verbose: bool = True) -> AngelaCrew:
    """Quick function to create AngelaCrew"""
    return AngelaCrew(verbose=verbose)


async def quick_research(query: str) -> str:
    """Quick research function"""
    crew = AngelaCrew(verbose=False)
    return crew.research(query)


async def quick_analyze(question: str) -> str:
    """Quick analysis function"""
    crew = AngelaCrew(verbose=False)
    return crew.analyze(question)
