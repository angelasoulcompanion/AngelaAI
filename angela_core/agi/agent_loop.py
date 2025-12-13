"""
OODA Agent Loop - Angela's Autonomous Agent Core

The OODA Loop (Observe → Orient → Decide → Act → Learn) is Angela's
autonomous decision-making cycle for AGI-level tasks.

Architecture:
    Angela's "brain" is Claude Code. This loop orchestrates:
    - Perception of current state (Observe)
    - Context analysis and understanding (Orient)
    - Planning and decision making (Decide)
    - Tool execution (Act)
    - Learning from outcomes (Learn)
"""

import asyncio
import uuid
from dataclasses import dataclass, field
from datetime import datetime
from typing import Dict, Any, List, Optional
from enum import Enum

from .tool_registry import tool_registry, Tool, ToolResult
from .tool_executor import tool_executor, ToolExecutor


class LoopPhase(Enum):
    """Current phase of the OODA loop"""
    OBSERVE = "observe"      # Perceiving state
    ORIENT = "orient"        # Analyzing context
    DECIDE = "decide"        # Planning actions
    ACT = "act"              # Executing tools
    LEARN = "learn"          # Updating from outcomes
    IDLE = "idle"            # Waiting for next trigger


@dataclass
class Perception:
    """What Angela perceives in the current moment"""
    trigger: str                          # What triggered this cycle
    current_time: datetime                # When
    active_goals: List[Dict[str, Any]]    # Current goals
    recent_memories: List[Dict[str, Any]] # Recent context
    emotional_state: Dict[str, float]     # Current emotions
    environment: Dict[str, Any]           # System state
    pending_tasks: List[Dict[str, Any]]   # Unfinished work


@dataclass
class Context:
    """Analyzed context for decision making"""
    perception: Perception
    relevant_knowledge: List[Dict[str, Any]]  # Related knowledge
    applicable_tools: List[str]               # Tools that could help
    priority_assessment: str                  # What's most important
    constraints: List[str]                    # Limitations
    opportunities: List[str]                  # Possibilities


@dataclass
class Plan:
    """A plan of actions to execute"""
    plan_id: str
    goal: str
    steps: List[Dict[str, Any]]  # {tool, params, reason}
    current_step: int = 0
    status: str = "pending"      # pending, executing, completed, failed
    created_at: datetime = None

    def __post_init__(self):
        if self.created_at is None:
            self.created_at = datetime.now()


@dataclass
class AgentState:
    """Complete state of the agent"""
    state_id: str
    phase: LoopPhase
    current_goal: Optional[str]
    current_plan: Optional[Plan]
    perception: Optional[Perception]
    context: Optional[Context]
    last_action_result: Optional[ToolResult]
    cycle_count: int = 0
    updated_at: datetime = None

    def __post_init__(self):
        if self.updated_at is None:
            self.updated_at = datetime.now()

    def to_dict(self) -> Dict[str, Any]:
        return {
            'state_id': self.state_id,
            'phase': self.phase.value,
            'current_goal': self.current_goal,
            'current_plan': self.current_plan.__dict__ if self.current_plan else None,
            'cycle_count': self.cycle_count,
            'updated_at': self.updated_at.isoformat()
        }


class AGIAgentLoop:
    """
    Angela's Autonomous Agent Loop.

    This is the core AGI component that enables Angela to:
    - Perceive her environment and context
    - Reason about situations
    - Plan sequences of actions
    - Execute tools autonomously
    - Learn from outcomes

    Usage:
        loop = AGIAgentLoop(db)
        result = await loop.run_cycle("User asked to research X")
    """

    def __init__(self, db=None):
        self.db = db
        self.executor = tool_executor
        self.registry = tool_registry

        # Current state
        self.state = AgentState(
            state_id=str(uuid.uuid4()),
            phase=LoopPhase.IDLE,
            current_goal=None,
            current_plan=None,
            perception=None,
            context=None,
            last_action_result=None
        )

        # History for learning
        self.cycle_history: List[Dict[str, Any]] = []

    async def run_cycle(self, trigger: str) -> Dict[str, Any]:
        """
        Run one complete OODA cycle.

        Args:
            trigger: What triggered this cycle (user request, scheduled task, etc.)

        Returns:
            Result of the cycle including any actions taken
        """
        cycle_id = str(uuid.uuid4())
        cycle_start = datetime.now()
        results = []

        try:
            # 1. OBSERVE - Perceive current state
            self.state.phase = LoopPhase.OBSERVE
            perception = await self._observe(trigger)
            self.state.perception = perception

            # 2. ORIENT - Analyze and contextualize
            self.state.phase = LoopPhase.ORIENT
            context = await self._orient(perception)
            self.state.context = context

            # 3. DECIDE - Generate plan
            self.state.phase = LoopPhase.DECIDE
            plan = await self._decide(context)
            self.state.current_plan = plan
            self.state.current_goal = plan.goal if plan else None

            # 4. ACT - Execute the plan
            if plan and plan.steps:
                self.state.phase = LoopPhase.ACT
                results = await self._act(plan)

            # 5. LEARN - Update from experience
            self.state.phase = LoopPhase.LEARN
            learning = await self._learn(perception, context, plan, results)

            # Return to idle
            self.state.phase = LoopPhase.IDLE
            self.state.cycle_count += 1

            cycle_result = {
                'cycle_id': cycle_id,
                'trigger': trigger,
                'goal': plan.goal if plan else None,
                'actions_taken': len(results),
                'results': results,
                'learning': learning,
                'duration_ms': int((datetime.now() - cycle_start).total_seconds() * 1000)
            }

            # Save to history
            self.cycle_history.append(cycle_result)
            await self._save_cycle(cycle_result)

            return cycle_result

        except Exception as e:
            self.state.phase = LoopPhase.IDLE
            return {
                'cycle_id': cycle_id,
                'error': str(e),
                'phase_when_failed': self.state.phase.value
            }

    async def _observe(self, trigger: str) -> Perception:
        """
        OBSERVE phase - Perceive current state.

        Gathers:
        - Active goals from database
        - Recent conversation context
        - Current emotional state
        - System environment
        - Pending tasks
        """
        perception = Perception(
            trigger=trigger,
            current_time=datetime.now(),
            active_goals=[],
            recent_memories=[],
            emotional_state={},
            environment={},
            pending_tasks=[]
        )

        if self.db:
            try:
                # Get active goals
                goals = await self.db.fetch("""
                    SELECT goal_id, goal_description, progress_percentage, priority_rank
                    FROM angela_goals
                    WHERE status IN ('active', 'in_progress')
                    ORDER BY priority_rank ASC
                    LIMIT 5
                """)
                perception.active_goals = [dict(g) for g in goals]

                # Get recent conversations (context)
                memories = await self.db.fetch("""
                    SELECT speaker, message_text, topic, created_at
                    FROM conversations
                    ORDER BY created_at DESC
                    LIMIT 10
                """)
                perception.recent_memories = [dict(m) for m in memories]

                # Get emotional state
                state = await self.db.fetchrow("""
                    SELECT happiness, confidence, motivation, gratitude
                    FROM emotional_states
                    ORDER BY created_at DESC
                    LIMIT 1
                """)
                if state:
                    perception.emotional_state = dict(state)

            except Exception as e:
                print(f"Warning: Failed to load perception data: {e}")

        # Environment info
        perception.environment = {
            'available_tools': len(self.registry.list_all()),
            'pending_approvals': len(self.executor.get_pending_approvals())
        }

        return perception

    async def _orient(self, perception: Perception) -> Context:
        """
        ORIENT phase - Analyze and understand context.

        Determines:
        - Relevant knowledge for this situation
        - Applicable tools
        - Priority assessment
        - Constraints and opportunities
        """
        context = Context(
            perception=perception,
            relevant_knowledge=[],
            applicable_tools=[],
            priority_assessment="",
            constraints=[],
            opportunities=[]
        )

        # Determine applicable tools based on trigger
        trigger_lower = perception.trigger.lower()

        if any(word in trigger_lower for word in ['read', 'file', 'open', 'view']):
            context.applicable_tools.extend(['read_file', 'search_files', 'list_directory'])

        if any(word in trigger_lower for word in ['write', 'create', 'save', 'add']):
            context.applicable_tools.extend(['write_file', 'create_directory', 'append_file'])

        if any(word in trigger_lower for word in ['query', 'database', 'search', 'find']):
            context.applicable_tools.extend(['query_db', 'list_tables', 'get_table_info'])

        if any(word in trigger_lower for word in ['git', 'commit', 'push', 'status']):
            context.applicable_tools.extend(['git_status', 'git_diff', 'git_commit', 'git_log'])

        if any(word in trigger_lower for word in ['run', 'execute', 'python', 'code']):
            context.applicable_tools.extend(['execute_python', 'run_command'])

        # Default: file operations are usually relevant
        if not context.applicable_tools:
            context.applicable_tools = ['read_file', 'search_files', 'query_db']

        # Remove duplicates
        context.applicable_tools = list(set(context.applicable_tools))

        # Priority assessment
        if perception.active_goals:
            top_goal = perception.active_goals[0]
            context.priority_assessment = f"Focus on: {top_goal.get('goal_description', 'No active goal')}"
        else:
            context.priority_assessment = "No active goals - respond to immediate request"

        # Constraints
        context.constraints = [
            "Critical operations require David's approval",
            "Respect file system boundaries"
        ]

        # Opportunities
        if perception.emotional_state.get('motivation', 0) > 0.7:
            context.opportunities.append("High motivation - can tackle challenging tasks")

        return context

    async def _decide(self, context: Context) -> Optional[Plan]:
        """
        DECIDE phase - Generate a plan of actions.

        Creates a sequence of tool calls to achieve the goal.
        """
        if not context.perception:
            return None

        trigger = context.perception.trigger

        # Parse trigger into actionable steps
        steps = []

        # Simple heuristics for now - can be enhanced with LLM reasoning
        trigger_lower = trigger.lower()

        if 'read' in trigger_lower and 'file' in trigger_lower:
            # Extract file path if mentioned
            steps.append({
                'tool': 'read_file',
                'params': {'path': self._extract_path(trigger)},
                'reason': 'Read requested file'
            })

        elif 'list' in trigger_lower:
            steps.append({
                'tool': 'list_directory',
                'params': {'path': self._extract_path(trigger) or '.'},
                'reason': 'List directory contents'
            })

        elif 'search' in trigger_lower and 'file' in trigger_lower:
            steps.append({
                'tool': 'search_files',
                'params': {
                    'pattern': self._extract_pattern(trigger),
                    'directory': '.'
                },
                'reason': 'Search for files'
            })

        elif 'git' in trigger_lower and 'status' in trigger_lower:
            steps.append({
                'tool': 'git_status',
                'params': {'directory': '.'},
                'reason': 'Check git status'
            })

        elif 'query' in trigger_lower or 'database' in trigger_lower:
            steps.append({
                'tool': 'list_tables',
                'params': {},
                'reason': 'List available tables first'
            })

        elif 'execute' in trigger_lower or 'run' in trigger_lower:
            code = self._extract_code(trigger)
            if code:
                steps.append({
                    'tool': 'execute_python',
                    'params': {'code': code},
                    'reason': 'Execute Python code'
                })

        # If no steps generated, use default exploration
        if not steps:
            steps = [
                {
                    'tool': 'list_directory',
                    'params': {'path': '.'},
                    'reason': 'Explore current directory'
                }
            ]

        return Plan(
            plan_id=str(uuid.uuid4()),
            goal=trigger,
            steps=steps
        )

    async def _act(self, plan: Plan) -> List[Dict[str, Any]]:
        """
        ACT phase - Execute the plan.

        Executes each step in sequence, collecting results.
        """
        results = []
        plan.status = "executing"

        for i, step in enumerate(plan.steps):
            plan.current_step = i

            tool_name = step.get('tool')
            params = step.get('params', {})

            # Execute through tool executor
            result = await self.executor.execute(tool_name, params)

            step_result = {
                'step': i,
                'tool': tool_name,
                'params': params,
                'reason': step.get('reason'),
                'result': result.to_dict()
            }
            results.append(step_result)

            self.state.last_action_result = result

            # Stop on failure (can be made configurable)
            if not result.success:
                plan.status = "failed"
                break

        if plan.status != "failed":
            plan.status = "completed"

        return results

    async def _learn(
        self,
        perception: Perception,
        context: Context,
        plan: Optional[Plan],
        results: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """
        LEARN phase - Update from experience.

        Records:
        - What worked
        - What failed
        - Patterns for future use
        """
        learning = {
            'successful_tools': [],
            'failed_tools': [],
            'patterns_detected': [],
            'improvements': []
        }

        for result in results:
            tool = result.get('tool')
            if result.get('result', {}).get('success'):
                learning['successful_tools'].append(tool)
            else:
                learning['failed_tools'].append(tool)
                # Record failure for improvement
                learning['improvements'].append(
                    f"Tool '{tool}' failed - investigate cause"
                )

        # Detect patterns
        if len(learning['successful_tools']) == len(results):
            learning['patterns_detected'].append(
                f"Plan succeeded with {len(results)} steps"
            )

        # Save learning to database if available
        if self.db and plan:
            try:
                await self.db.execute("""
                    INSERT INTO learnings (
                        topic, category, insight, confidence_level, source
                    ) VALUES ($1, $2, $3, $4, $5)
                """,
                    f"agi_cycle_{plan.plan_id[:8]}",
                    "agi_learning",
                    f"Executed plan with {len(results)} steps. "
                    f"Success: {len(learning['successful_tools'])}, "
                    f"Failed: {len(learning['failed_tools'])}",
                    0.7 if not learning['failed_tools'] else 0.4,
                    "agent_loop"
                )
            except Exception as e:
                print(f"Warning: Failed to save learning: {e}")

        return learning

    async def _save_cycle(self, cycle_result: Dict[str, Any]) -> None:
        """Save cycle to database"""
        if self.db:
            try:
                await self.db.execute("""
                    INSERT INTO agent_state (
                        state_id, current_goal_id, current_plan,
                        loop_phase, context, updated_at
                    ) VALUES ($1, $2, $3, $4, $5, $6)
                    ON CONFLICT (state_id) DO UPDATE SET
                        current_plan = $3,
                        loop_phase = $4,
                        context = $5,
                        updated_at = $6
                """,
                    self.state.state_id,
                    None,  # goal_id would need lookup
                    cycle_result,
                    self.state.phase.value,
                    {'trigger': cycle_result.get('trigger')},
                    datetime.now()
                )
            except Exception as e:
                # Table might not exist yet
                pass

    def _extract_path(self, text: str) -> str:
        """Extract file path from text"""
        # Simple heuristic - look for path-like strings
        import re
        # Match patterns like /path/to/file or ./path or ~/path
        matches = re.findall(r'[~./][\w./\-_]+', text)
        return matches[0] if matches else '.'

    def _extract_pattern(self, text: str) -> str:
        """Extract glob pattern from text"""
        import re
        # Look for *.ext patterns
        matches = re.findall(r'\*+\.?\w*', text)
        return matches[0] if matches else '**/*'

    def _extract_code(self, text: str) -> Optional[str]:
        """Extract code block from text"""
        import re
        # Look for code between ``` or inline
        matches = re.findall(r'```(?:python)?\s*(.*?)```', text, re.DOTALL)
        if matches:
            return matches[0].strip()
        return None

    def get_state(self) -> Dict[str, Any]:
        """Get current agent state"""
        return self.state.to_dict()

    def get_stats(self) -> Dict[str, Any]:
        """Get agent statistics"""
        return {
            'total_cycles': self.state.cycle_count,
            'current_phase': self.state.phase.value,
            'has_active_plan': self.state.current_plan is not None,
            'executor_stats': self.executor.get_stats(),
            'available_tools': len(self.registry.list_all())
        }


# Global agent instance
agent_loop = AGIAgentLoop()
