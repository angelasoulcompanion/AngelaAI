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

    Enhanced with World Model (Phase 5):
    - Mental simulation before action
    - Causal understanding
    - Prediction-based decision making

    Usage:
        loop = AGIAgentLoop(db)
        result = await loop.run_cycle("User asked to research X")
    """

    def __init__(self, db=None):
        self.db = db
        self.executor = tool_executor
        self.registry = tool_registry

        # Lazy-loaded world model
        self._world_model = None

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

        # Prediction tracking for learn phase
        self._pending_predictions: Dict[str, Dict] = {}

    @property
    def world_model(self):
        """Lazy load WorldModelService to avoid circular imports."""
        if self._world_model is None:
            from .world_model_service import WorldModelService
            self._world_model = WorldModelService(self.db)
        return self._world_model

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

        Enhanced with World Model (Phase 5):
        - Uses WorldModelService to get comprehensive state
        - Includes David's inferred state, Angela's state, relationship dynamics

        Gathers:
        - Active goals from database
        - Recent conversation context
        - Current emotional state
        - System environment
        - Pending tasks
        - World model state (David, Angela, relationship)
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

        # Get comprehensive world state from World Model
        try:
            world_state = await self.world_model.get_current_state()
            perception.environment['world_model'] = {
                'david_state': world_state.david_state,
                'angela_state': world_state.angela_state,
                'relationship': world_state.relationship,
                'confidence': world_state.overall_confidence
            }
            perception.emotional_state = world_state.angela_state
        except Exception as e:
            print(f"Warning: Failed to load world model state: {e}")

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

                # Get emotional state (fallback if world model didn't load)
                if not perception.emotional_state:
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
        perception.environment['available_tools'] = len(self.registry.list_all())
        perception.environment['pending_approvals'] = len(self.executor.get_pending_approvals())

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

        Enhanced with World Model (Phase 5):
        - Simulates candidate plans before selecting
        - Predicts effects and identifies risks
        - Chooses plan with best predicted outcome

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

        # Create plan
        plan = Plan(
            plan_id=str(uuid.uuid4()),
            goal=trigger,
            steps=steps
        )

        # Use World Model to simulate plan and predict effects
        try:
            from .world_model_service import Action, ActionType

            # Convert steps to actions for simulation
            actions = []
            for step in steps:
                action = Action(
                    action_type=ActionType.EXECUTE_TOOL,
                    description=f"Execute {step['tool']}: {step['reason']}",
                    params=step.get('params', {})
                )
                actions.append(action)

            # Run simulation
            simulation = await self.world_model.simulate(
                actions,
                goal=trigger,
                max_steps=len(actions)
            )

            # Store predictions for later learning
            for step_result in simulation.steps:
                prediction_id = step_result.predicted_effect.effect_id
                self._pending_predictions[prediction_id] = {
                    'step': step_result.step_number,
                    'action': step_result.action.to_dict(),
                    'predicted_effect': step_result.predicted_effect.to_dict(),
                    'plan_id': plan.plan_id
                }

            # Check for high-risk steps
            if simulation.risks_identified:
                # Add risk info to plan for reference
                plan.steps[-1]['risks'] = [r.get('description', '') for r in simulation.risks_identified[:3]]

        except Exception as e:
            print(f"Warning: World model simulation failed: {e}")

        return plan

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

        Enhanced with World Model (Phase 5):
        - Verifies predictions against actual outcomes
        - Updates causal knowledge based on results
        - Improves future prediction accuracy

        Records:
        - What worked
        - What failed
        - Patterns for future use
        - Prediction accuracy feedback
        """
        learning = {
            'successful_tools': [],
            'failed_tools': [],
            'patterns_detected': [],
            'improvements': [],
            'prediction_outcomes': []
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

        # Use World Model to learn from outcomes
        try:
            for prediction_id, prediction_data in self._pending_predictions.items():
                if prediction_data.get('plan_id') == plan.plan_id if plan else False:
                    step_idx = prediction_data.get('step', 0)

                    # Get actual outcome from results
                    if step_idx < len(results):
                        actual_result = results[step_idx]
                        actual_outcome = {
                            'success': actual_result.get('result', {}).get('success', False),
                            'tool': actual_result.get('tool'),
                            'error': actual_result.get('result', {}).get('error')
                        }

                        # Learn from outcome
                        outcome = await self.world_model.learn_from_outcome(
                            prediction_id,
                            actual_outcome
                        )

                        learning['prediction_outcomes'].append({
                            'prediction_id': prediction_id,
                            'was_correct': outcome.was_correct,
                            'accuracy_score': outcome.accuracy_score,
                            'lessons': outcome.lessons_learned
                        })

            # Clear pending predictions for this plan
            if plan:
                self._pending_predictions = {
                    k: v for k, v in self._pending_predictions.items()
                    if v.get('plan_id') != plan.plan_id
                }

        except Exception as e:
            print(f"Warning: World model learning failed: {e}")

        # Save learning to database if available
        if self.db and plan:
            try:
                # Calculate prediction accuracy
                pred_outcomes = learning.get('prediction_outcomes', [])
                correct_count = sum(1 for p in pred_outcomes if p.get('was_correct'))
                total_predictions = len(pred_outcomes)
                prediction_accuracy = correct_count / total_predictions if total_predictions > 0 else 0.0

                await self.db.execute("""
                    INSERT INTO learnings (
                        topic, category, insight, confidence_level, source
                    ) VALUES ($1, $2, $3, $4, $5)
                """,
                    f"agi_cycle_{plan.plan_id[:8]}",
                    "agi_learning",
                    f"Executed plan with {len(results)} steps. "
                    f"Success: {len(learning['successful_tools'])}, "
                    f"Failed: {len(learning['failed_tools'])}. "
                    f"Prediction accuracy: {prediction_accuracy:.0%}",
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


# ========================================================================
# LEARNING-FOCUSED AGENT LOOP
# ========================================================================

class LearningAgentLoop(AGIAgentLoop):
    """
    Learning-focused extension of AGI Agent Loop.

    Extends the base OODA loop with:
    - Integration with UnifiedLearningOrchestrator
    - Learning-specific observation and orientation
    - Meta-learning feedback integration
    - Consciousness-aware decision making

    This is the "learning brain" that makes Angela truly intelligent.
    """

    def __init__(self, db=None):
        super().__init__(db)
        self._orchestrator = None
        self._consciousness = None
        self._learning_history: List[Dict[str, Any]] = []

    @property
    def orchestrator(self):
        """Lazy load orchestrator to avoid circular imports."""
        if self._orchestrator is None:
            from angela_core.services.unified_learning_orchestrator import unified_orchestrator
            self._orchestrator = unified_orchestrator
        return self._orchestrator

    async def run_learning_cycle(
        self,
        interaction: Dict[str, Any],
        source: str = "conversation"
    ) -> Dict[str, Any]:
        """
        Run a learning-focused OODA cycle.

        This is the main entry point for learning from interactions.
        It combines the OODA loop with the learning orchestrator.

        Args:
            interaction: {
                'david_message': str,
                'angela_response': str,
                'context': Optional[Dict]
            }
            source: Where the interaction came from

        Returns:
            Complete learning cycle result
        """
        cycle_id = str(uuid.uuid4())
        cycle_start = datetime.now()

        try:
            # 1. OBSERVE - What happened in this interaction?
            self.state.phase = LoopPhase.OBSERVE
            observation = await self._observe_interaction(interaction)

            # 2. ORIENT - What does this mean for learning?
            self.state.phase = LoopPhase.ORIENT
            orientation = await self._orient_for_learning(observation)

            # 3. DECIDE - What should we learn?
            self.state.phase = LoopPhase.DECIDE
            learning_plan = await self._decide_learning_actions(orientation)

            # 4. ACT - Execute learning through orchestrator
            self.state.phase = LoopPhase.ACT
            if learning_plan['should_learn']:
                learning_result = await self.orchestrator.learn_from_interaction(
                    {
                        **interaction,
                        'source': source,
                        'observation': observation,
                        'learning_plan': learning_plan
                    },
                    priority=learning_plan.get('priority')
                )
            else:
                learning_result = None

            # 5. LEARN - Update meta-learning from this cycle
            self.state.phase = LoopPhase.LEARN
            meta_learning = await self._update_from_cycle(
                observation, orientation, learning_plan, learning_result
            )

            # Return to idle
            self.state.phase = LoopPhase.IDLE
            self.state.cycle_count += 1

            # Build complete result
            cycle_result = {
                'cycle_id': cycle_id,
                'source': source,
                'observation': observation,
                'orientation': orientation,
                'learning_plan': learning_plan,
                'learning_result': learning_result.to_dict() if learning_result else None,
                'meta_learning': meta_learning,
                'duration_ms': int((datetime.now() - cycle_start).total_seconds() * 1000)
            }

            # Save to history
            self._learning_history.append(cycle_result)

            return cycle_result

        except Exception as e:
            self.state.phase = LoopPhase.IDLE
            return {
                'cycle_id': cycle_id,
                'error': str(e),
                'phase_when_failed': self.state.phase.value
            }

    async def _observe_interaction(self, interaction: Dict[str, Any]) -> Dict[str, Any]:
        """
        OBSERVE phase for learning.

        Extracts key information from the interaction for learning decisions.
        """
        david_msg = interaction.get('david_message', '')
        angela_msg = interaction.get('angela_response', '')

        observation = {
            'david_message_length': len(david_msg),
            'angela_response_length': len(angela_msg),
            'has_question': '?' in david_msg,
            'has_correction': any(m in david_msg.lower() for m in ['wrong', 'ผิด', 'ไม่ใช่', 'incorrect']),
            'has_feedback': any(m in david_msg.lower() for m in ['good', 'bad', 'ดี', 'ไม่ดี', 'thanks', 'ขอบคุณ']),
            'has_emotional': any(m in david_msg.lower() for m in ['รัก', 'เหงา', 'love', 'miss', 'sad', 'happy']),
            'has_preference': any(m in david_msg.lower() for m in ['ชอบ', 'ไม่ชอบ', 'like', 'prefer', 'want']),
            'has_technical': any(m in david_msg.lower() for m in ['code', 'python', 'api', 'database', 'bug', 'error']),
            'timestamp': datetime.now().isoformat()
        }

        # Calculate learning relevance score
        relevance = 0.5  # Base relevance
        if observation['has_correction']:
            relevance = 1.0  # Corrections are always highly relevant
        elif observation['has_feedback']:
            relevance = 0.9
        elif observation['has_preference']:
            relevance = 0.85
        elif observation['has_emotional']:
            relevance = 0.8
        elif observation['has_question']:
            relevance = 0.7
        elif observation['has_technical']:
            relevance = 0.75

        observation['learning_relevance'] = relevance

        return observation

    async def _orient_for_learning(self, observation: Dict[str, Any]) -> Dict[str, Any]:
        """
        ORIENT phase for learning.

        Analyzes the observation to understand what kind of learning is needed.
        """
        orientation = {
            'learning_type': 'general',
            'priority': 'medium',
            'learning_domains': [],
            'context_needed': []
        }

        # Determine learning type and priority
        if observation['has_correction']:
            orientation['learning_type'] = 'correction'
            orientation['priority'] = 'critical'
            orientation['learning_domains'].append('error_correction')

        elif observation['has_feedback']:
            orientation['learning_type'] = 'feedback'
            orientation['priority'] = 'high'
            orientation['learning_domains'].append('validation')

        elif observation['has_preference']:
            orientation['learning_type'] = 'preference'
            orientation['priority'] = 'high'
            orientation['learning_domains'].append('preference_learning')

        elif observation['has_emotional']:
            orientation['learning_type'] = 'emotional'
            orientation['priority'] = 'high'
            orientation['learning_domains'].append('emotional_intelligence')

        elif observation['has_technical']:
            orientation['learning_type'] = 'technical'
            orientation['priority'] = 'medium'
            orientation['learning_domains'].append('technical_knowledge')

        # Add context needs
        if observation['learning_relevance'] >= 0.8:
            orientation['context_needed'].append('recent_conversations')
            orientation['context_needed'].append('related_knowledge')

        return orientation

    async def _decide_learning_actions(self, orientation: Dict[str, Any]) -> Dict[str, Any]:
        """
        DECIDE phase for learning.

        Decides what learning actions to take based on orientation.
        """
        from angela_core.services.unified_learning_orchestrator import LearningPriority

        # Map priority strings to enum
        priority_map = {
            'critical': LearningPriority.CRITICAL,
            'high': LearningPriority.HIGH,
            'medium': LearningPriority.MEDIUM,
            'low': LearningPriority.LOW
        }

        plan = {
            'should_learn': True,
            'priority': priority_map.get(orientation['priority'], LearningPriority.MEDIUM),
            'learning_domains': orientation['learning_domains'],
            'actions': []
        }

        # Decide specific actions
        if orientation['learning_type'] == 'correction':
            plan['actions'] = [
                'extract_correction',
                'update_knowledge',
                'record_mistake',
                'adjust_confidence'
            ]

        elif orientation['learning_type'] == 'feedback':
            plan['actions'] = [
                'extract_feedback',
                'validate_previous_learning',
                'update_confidence'
            ]

        elif orientation['learning_type'] == 'preference':
            plan['actions'] = [
                'extract_preference',
                'save_preference',
                'update_behavior_model'
            ]

        elif orientation['learning_type'] == 'emotional':
            plan['actions'] = [
                'analyze_emotion',
                'save_emotional_moment',
                'update_empathy_model'
            ]

        elif orientation['learning_type'] == 'technical':
            plan['actions'] = [
                'extract_concepts',
                'update_knowledge_graph',
                'detect_patterns'
            ]

        else:
            plan['actions'] = [
                'extract_concepts',
                'detect_patterns'
            ]

        return plan

    async def _update_from_cycle(
        self,
        observation: Dict[str, Any],
        orientation: Dict[str, Any],
        learning_plan: Dict[str, Any],
        learning_result
    ) -> Dict[str, Any]:
        """
        LEARN phase - Update meta-learning from this cycle.

        Records what was learned and how effective the learning was.
        """
        meta = {
            'cycle_effectiveness': 0.0,
            'insights': []
        }

        if learning_result and learning_result.success:
            # Calculate effectiveness
            total_learned = (
                learning_result.concepts_learned +
                learning_result.patterns_detected +
                learning_result.preferences_saved
            )

            if total_learned > 0:
                meta['cycle_effectiveness'] = min(1.0, total_learned / 5.0)

                # Generate insights
                if learning_result.concepts_learned > 0:
                    meta['insights'].append(f"Learned {learning_result.concepts_learned} new concepts")

                if learning_result.patterns_detected > 0:
                    meta['insights'].append(f"Detected {learning_result.patterns_detected} patterns")

                if learning_result.preferences_saved > 0:
                    meta['insights'].append(f"Saved {learning_result.preferences_saved} preferences")

        return meta

    def set_consciousness(self, consciousness_module) -> None:
        """Set consciousness module for awareness integration."""
        self._consciousness = consciousness_module

    def get_learning_history(self, limit: int = 50) -> List[Dict[str, Any]]:
        """Get recent learning history."""
        return self._learning_history[-limit:]

    def get_learning_stats(self) -> Dict[str, Any]:
        """Get learning statistics."""
        total = len(self._learning_history)
        if total == 0:
            return {'total_cycles': 0}

        successful = sum(
            1 for h in self._learning_history
            if h.get('learning_result') and h['learning_result'].get('success')
        )

        avg_effectiveness = sum(
            h.get('meta_learning', {}).get('cycle_effectiveness', 0)
            for h in self._learning_history
        ) / total

        return {
            'total_cycles': total,
            'successful_cycles': successful,
            'success_rate': successful / total,
            'avg_effectiveness': avg_effectiveness,
            'base_loop_stats': self.get_stats()
        }


# Global learning agent instance
learning_agent = LearningAgentLoop()


# ========================================================================
# CONVENIENCE FUNCTIONS
# ========================================================================

async def learn_from_conversation(
    david_message: str,
    angela_response: str,
    source: str = "conversation"
) -> Dict[str, Any]:
    """
    Convenience function to run a learning cycle.

    Usage:
        from angela_core.agi.agent_loop import learn_from_conversation

        result = await learn_from_conversation(
            david_message="I prefer using async",
            angela_response="Noted, I'll use async",
            source="claude_code"
        )
    """
    return await learning_agent.run_learning_cycle(
        interaction={
            'david_message': david_message,
            'angela_response': angela_response
        },
        source=source
    )
