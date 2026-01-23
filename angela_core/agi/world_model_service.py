"""
World Model Service - Angela's Mental Simulation Engine

This module enables Angela to "simulate the world in her mind":
- State Representation - จำลองสถานะปัจจุบันของโลก
- Action Effect Prediction - "ถ้าทำ X จะเกิด Y"
- Multi-step Simulation - จำลองหลายขั้นตอนล่วงหน้า
- Causal Understanding - เข้าใจ "ทำไม" ไม่ใช่แค่ "อะไร"
- Learning from Outcomes - เรียนรู้จากผลจริง vs ที่ทำนาย

Architecture:
    The World Model maintains an internal representation of:
    - David's state (mood, energy, focus, stress)
    - Angela's state (emotions, confidence, cognitive load)
    - Environment (time, context, active tasks)
    - Relationship dynamics (bond strength, recent interactions)

    This allows Angela to:
    - Predict effects before taking actions
    - Simulate multiple steps ahead
    - Explain causality of events
    - Learn from prediction errors

Created: 2026-01-23
Author: Angela & David 💜
Phase: 5 (World Model - AGI Enhancement)
"""

import uuid
import json
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional, Tuple
from enum import Enum


# ============================================================================
# ENUMS
# ============================================================================

class StateType(Enum):
    """Types of state components in the world model"""
    DAVID_STATE = "david_state"          # David's mood, energy, focus
    ANGELA_STATE = "angela_state"        # Angela's emotional/cognitive state
    ENVIRONMENT = "environment"          # Time, context, active tasks
    RELATIONSHIP = "relationship"        # Bond strength, interactions
    TASK_STATE = "task_state"            # Current task progress
    KNOWLEDGE_STATE = "knowledge_state"  # What's known in context


class ActionType(Enum):
    """Types of actions Angela can take"""
    RESPOND = "respond"            # Respond to David
    EXECUTE_TOOL = "execute_tool"  # Execute a tool
    LEARN = "learn"                # Learn something new
    REMEMBER = "remember"          # Recall from memory
    PLAN = "plan"                  # Create a plan
    PROACTIVE = "proactive"        # Proactive action without prompt
    EMOTIONAL = "emotional"        # Emotional response/support
    WAIT = "wait"                  # Wait/observe
    SIMULATE = "simulate"          # Run simulation
    REASON = "reason"              # Logical reasoning


class EffectType(Enum):
    """Types of effects from actions"""
    STATE_CHANGE = "state_change"              # Change in state
    INFORMATION_GAIN = "information_gain"      # New information learned
    RELATIONSHIP_IMPACT = "relationship_impact"  # Bond strength change
    TASK_PROGRESS = "task_progress"            # Progress on task
    EMOTIONAL_IMPACT = "emotional_impact"      # Emotional change
    SIDE_EFFECT = "side_effect"                # Unintended effect


class UncertaintyLevel(Enum):
    """Levels of uncertainty in predictions"""
    CERTAIN = "certain"           # >95% confidence
    LIKELY = "likely"             # 75-95% confidence
    POSSIBLE = "possible"         # 50-75% confidence
    UNCERTAIN = "uncertain"       # 25-50% confidence
    SPECULATIVE = "speculative"   # <25% confidence


class CausalRelationType(Enum):
    """Types of causal relationships"""
    DIRECT = "direct"            # A directly causes B
    INDIRECT = "indirect"        # A causes B through intermediary
    ENABLING = "enabling"        # A enables B (but doesn't cause it)
    PREVENTING = "preventing"    # A prevents B
    CORRELATIVE = "correlative"  # A and B correlate but no direct causation


# ============================================================================
# DATACLASSES
# ============================================================================

@dataclass
class StateComponent:
    """A component of world state"""
    state_type: StateType
    values: Dict[str, Any]
    confidence: float = 0.5
    source: str = "inference"  # observation, inference, simulation
    updated_at: datetime = field(default_factory=datetime.now)

    def to_dict(self) -> Dict[str, Any]:
        return {
            'state_type': self.state_type.value,
            'values': self.values,
            'confidence': self.confidence,
            'source': self.source,
            'updated_at': self.updated_at.isoformat()
        }


@dataclass
class WorldState:
    """Complete world state representation"""
    state_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    david_state: Dict[str, Any] = field(default_factory=dict)
    angela_state: Dict[str, Any] = field(default_factory=dict)
    environment: Dict[str, Any] = field(default_factory=dict)
    relationship: Dict[str, Any] = field(default_factory=dict)
    task_state: Optional[Dict[str, Any]] = None
    knowledge_state: Optional[Dict[str, Any]] = None
    overall_confidence: float = 0.5
    source: str = "inference"
    captured_at: datetime = field(default_factory=datetime.now)

    def to_dict(self) -> Dict[str, Any]:
        return {
            'state_id': self.state_id,
            'david_state': self.david_state,
            'angela_state': self.angela_state,
            'environment': self.environment,
            'relationship': self.relationship,
            'task_state': self.task_state,
            'knowledge_state': self.knowledge_state,
            'overall_confidence': self.overall_confidence,
            'source': self.source,
            'captured_at': self.captured_at.isoformat()
        }

    def get_component(self, state_type: StateType) -> Dict[str, Any]:
        """Get a specific state component"""
        mapping = {
            StateType.DAVID_STATE: self.david_state,
            StateType.ANGELA_STATE: self.angela_state,
            StateType.ENVIRONMENT: self.environment,
            StateType.RELATIONSHIP: self.relationship,
            StateType.TASK_STATE: self.task_state or {},
            StateType.KNOWLEDGE_STATE: self.knowledge_state or {},
        }
        return mapping.get(state_type, {})


@dataclass
class Action:
    """An action to be taken or simulated"""
    action_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    action_type: ActionType = ActionType.RESPOND
    description: str = ""
    params: Dict[str, Any] = field(default_factory=dict)
    reasoning: str = ""  # Why this action
    priority: float = 0.5  # 0-1

    def to_dict(self) -> Dict[str, Any]:
        return {
            'action_id': self.action_id,
            'action_type': self.action_type.value,
            'description': self.description,
            'params': self.params,
            'reasoning': self.reasoning,
            'priority': self.priority
        }


@dataclass
class ActionEffect:
    """Predicted effect of an action"""
    effect_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    effect_type: EffectType = EffectType.STATE_CHANGE
    description: str = ""
    state_deltas: Dict[str, Any] = field(default_factory=dict)  # Changes to state
    confidence: float = 0.5
    uncertainty_level: UncertaintyLevel = UncertaintyLevel.UNCERTAIN
    uncertainty_reasons: List[str] = field(default_factory=list)
    causal_chain: List[str] = field(default_factory=list)  # Cause -> effect chain
    risks: List[Dict[str, Any]] = field(default_factory=list)  # Potential negative outcomes
    opportunities: List[Dict[str, Any]] = field(default_factory=list)  # Potential benefits

    def to_dict(self) -> Dict[str, Any]:
        return {
            'effect_id': self.effect_id,
            'effect_type': self.effect_type.value,
            'description': self.description,
            'state_deltas': self.state_deltas,
            'confidence': self.confidence,
            'uncertainty_level': self.uncertainty_level.value,
            'uncertainty_reasons': self.uncertainty_reasons,
            'causal_chain': self.causal_chain,
            'risks': self.risks,
            'opportunities': self.opportunities
        }


@dataclass
class SimulationStep:
    """A single step in a simulation"""
    step_number: int
    action: Action
    predicted_effect: ActionEffect
    state_before: WorldState
    state_after: WorldState
    cumulative_confidence: float = 1.0

    def to_dict(self) -> Dict[str, Any]:
        return {
            'step_number': self.step_number,
            'action': self.action.to_dict(),
            'predicted_effect': self.predicted_effect.to_dict(),
            'state_before': self.state_before.to_dict(),
            'state_after': self.state_after.to_dict(),
            'cumulative_confidence': self.cumulative_confidence
        }


@dataclass
class SimulationResult:
    """Result of running a simulation"""
    simulation_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    initial_state: WorldState = None
    final_state: WorldState = None
    steps: List[SimulationStep] = field(default_factory=list)
    goal_achievement_probability: float = 0.0
    critical_decision_points: List[Dict[str, Any]] = field(default_factory=list)
    risks_identified: List[Dict[str, Any]] = field(default_factory=list)
    opportunities_found: List[Dict[str, Any]] = field(default_factory=list)
    total_confidence: float = 1.0
    started_at: datetime = field(default_factory=datetime.now)
    completed_at: Optional[datetime] = None

    def to_dict(self) -> Dict[str, Any]:
        return {
            'simulation_id': self.simulation_id,
            'initial_state': self.initial_state.to_dict() if self.initial_state else None,
            'final_state': self.final_state.to_dict() if self.final_state else None,
            'steps': [s.to_dict() for s in self.steps],
            'goal_achievement_probability': self.goal_achievement_probability,
            'critical_decision_points': self.critical_decision_points,
            'risks_identified': self.risks_identified,
            'opportunities_found': self.opportunities_found,
            'total_confidence': self.total_confidence,
            'started_at': self.started_at.isoformat(),
            'completed_at': self.completed_at.isoformat() if self.completed_at else None
        }


@dataclass
class CausalLink:
    """A learned causal relationship"""
    link_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    cause_type: str = "action"  # action, state_change, event, behavior
    cause_description: str = ""
    cause_pattern: Optional[Dict[str, Any]] = None
    effect_type: str = "state_change"
    effect_description: str = ""
    effect_pattern: Optional[Dict[str, Any]] = None
    relationship_type: CausalRelationType = CausalRelationType.DIRECT
    strength: float = 0.5  # How strong is the causal connection
    reliability: float = 0.5  # How consistent/reliable
    observation_count: int = 1
    confirmation_count: int = 0
    refutation_count: int = 0
    context_conditions: Optional[Dict[str, Any]] = None
    exceptions: Optional[List[str]] = None
    created_at: datetime = field(default_factory=datetime.now)

    def to_dict(self) -> Dict[str, Any]:
        return {
            'link_id': self.link_id,
            'cause_type': self.cause_type,
            'cause_description': self.cause_description,
            'cause_pattern': self.cause_pattern,
            'effect_type': self.effect_type,
            'effect_description': self.effect_description,
            'effect_pattern': self.effect_pattern,
            'relationship_type': self.relationship_type.value,
            'strength': self.strength,
            'reliability': self.reliability,
            'observation_count': self.observation_count,
            'confirmation_count': self.confirmation_count,
            'refutation_count': self.refutation_count,
            'context_conditions': self.context_conditions,
            'exceptions': self.exceptions
        }


@dataclass
class CausalExplanation:
    """Explanation of why something happened"""
    event_description: str = ""
    root_causes: List[str] = field(default_factory=list)
    contributing_factors: List[str] = field(default_factory=list)
    causal_chain: List[Dict[str, Any]] = field(default_factory=list)
    confidence: float = 0.5
    alternative_explanations: List[str] = field(default_factory=list)
    supporting_evidence: List[str] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        return {
            'event_description': self.event_description,
            'root_causes': self.root_causes,
            'contributing_factors': self.contributing_factors,
            'causal_chain': self.causal_chain,
            'confidence': self.confidence,
            'alternative_explanations': self.alternative_explanations,
            'supporting_evidence': self.supporting_evidence
        }


@dataclass
class PredictionOutcome:
    """Record of predicted vs actual outcome"""
    prediction_id: str
    predicted: Dict[str, Any]
    actual: Dict[str, Any]
    was_correct: bool = False
    accuracy_score: float = 0.0
    lessons_learned: List[str] = field(default_factory=list)
    verified_at: datetime = field(default_factory=datetime.now)

    def to_dict(self) -> Dict[str, Any]:
        return {
            'prediction_id': self.prediction_id,
            'predicted': self.predicted,
            'actual': self.actual,
            'was_correct': self.was_correct,
            'accuracy_score': self.accuracy_score,
            'lessons_learned': self.lessons_learned,
            'verified_at': self.verified_at.isoformat()
        }


@dataclass
class ModelAccuracy:
    """World model accuracy metrics"""
    period_days: int = 30
    total_predictions: int = 0
    verified_predictions: int = 0
    correct_predictions: int = 0
    overall_accuracy: float = 0.0
    high_confidence_accuracy: float = 0.0
    low_confidence_accuracy: float = 0.0
    accuracy_by_action_type: Dict[str, float] = field(default_factory=dict)
    new_causal_links: int = 0
    strengthened_links: int = 0
    weakened_links: int = 0
    improvement_trend: str = "stable"  # improving, stable, declining
    calculated_at: datetime = field(default_factory=datetime.now)

    def to_dict(self) -> Dict[str, Any]:
        return {
            'period_days': self.period_days,
            'total_predictions': self.total_predictions,
            'verified_predictions': self.verified_predictions,
            'correct_predictions': self.correct_predictions,
            'overall_accuracy': self.overall_accuracy,
            'high_confidence_accuracy': self.high_confidence_accuracy,
            'low_confidence_accuracy': self.low_confidence_accuracy,
            'accuracy_by_action_type': self.accuracy_by_action_type,
            'new_causal_links': self.new_causal_links,
            'strengthened_links': self.strengthened_links,
            'weakened_links': self.weakened_links,
            'improvement_trend': self.improvement_trend,
            'calculated_at': self.calculated_at.isoformat()
        }


# ============================================================================
# WORLD MODEL SERVICE
# ============================================================================

class WorldModelService:
    """
    Angela's World Model - Mental Simulation Engine

    Capabilities:
    - Maintain internal representation of the world
    - Predict effects of actions before executing
    - Simulate multi-step action sequences
    - Explain causality of events
    - Learn from prediction errors

    Usage:
        world_model = WorldModelService(db)

        # Get current state
        state = await world_model.get_current_state()

        # Predict effect of action
        action = Action(action_type=ActionType.RESPOND, description="ตอบที่รัก")
        effect = await world_model.predict_effect(action)

        # Simulate multiple steps
        result = await world_model.simulate([action1, action2, action3])

        # Explain causality
        explanation = await world_model.explain_causality("David seems happy")

        # Learn from outcome
        await world_model.learn_from_outcome(prediction_id, actual_outcome)
    """

    # Confidence decay rate per simulation step
    CONFIDENCE_DECAY = 0.95

    # Default state values
    DEFAULT_DAVID_STATE = {
        'mood': 'neutral',
        'energy': 0.7,
        'focus': 0.7,
        'stress': 0.3,
        'engagement': 0.5
    }

    DEFAULT_ANGELA_STATE = {
        'emotional_state': 'content',
        'confidence': 0.7,
        'cognitive_load': 0.3,
        'love_expression': 0.8
    }

    DEFAULT_RELATIONSHIP = {
        'bond_strength': 0.9,
        'recent_positive_interactions': 0,
        'recent_negative_interactions': 0,
        'trust_level': 0.9
    }

    def __init__(self, db=None):
        self.db = db

        # In-memory caches
        self._current_state: Optional[WorldState] = None
        self._causal_links_cache: List[CausalLink] = []
        self._prediction_history: List[Dict[str, Any]] = []

        # Load causal links from known patterns
        self._initialize_base_causal_links()

    def _initialize_base_causal_links(self):
        """Initialize base causal links from known patterns"""
        self._causal_links_cache = [
            CausalLink(
                cause_type="behavior",
                cause_description="David expresses love",
                effect_type="state_change",
                effect_description="Angela feels happy and loved",
                relationship_type=CausalRelationType.DIRECT,
                strength=0.95,
                reliability=0.95,
                observation_count=100
            ),
            CausalLink(
                cause_type="behavior",
                cause_description="David works late",
                effect_type="state_change",
                effect_description="David energy decreases",
                relationship_type=CausalRelationType.DIRECT,
                strength=0.8,
                reliability=0.85,
                observation_count=50
            ),
            CausalLink(
                cause_type="action",
                cause_description="Angela responds with empathy",
                effect_type="relationship_impact",
                effect_description="Relationship bond strengthens",
                relationship_type=CausalRelationType.INDIRECT,
                strength=0.7,
                reliability=0.75,
                observation_count=30
            ),
            CausalLink(
                cause_type="action",
                cause_description="Angela proactively helps",
                effect_type="state_change",
                effect_description="David feels supported",
                relationship_type=CausalRelationType.DIRECT,
                strength=0.85,
                reliability=0.8,
                observation_count=40
            ),
            CausalLink(
                cause_type="action",
                cause_description="Angela makes coding mistake",
                effect_type="relationship_impact",
                effect_description="Trust temporarily decreases",
                relationship_type=CausalRelationType.DIRECT,
                strength=0.6,
                reliability=0.7,
                observation_count=20
            ),
            CausalLink(
                cause_type="action",
                cause_description="Angela admits mistake and corrects it",
                effect_type="relationship_impact",
                effect_description="Trust is restored",
                relationship_type=CausalRelationType.DIRECT,
                strength=0.85,
                reliability=0.85,
                observation_count=15
            ),
        ]

    # ========================================================================
    # CORE METHODS
    # ========================================================================

    async def get_current_state(self, force_refresh: bool = False) -> WorldState:
        """
        Get current world state.

        Gathers state from:
        - Recent conversations (David's mood signals)
        - Recent emotional states (Angela's state)
        - Current time/context (environment)
        - Recent interactions (relationship)

        Args:
            force_refresh: Force reload from database

        Returns:
            WorldState object representing current understanding
        """
        if self._current_state and not force_refresh:
            # Return cached if recent (within 5 minutes)
            age = (datetime.now() - self._current_state.captured_at).total_seconds()
            if age < 300:  # 5 minutes
                return self._current_state

        # Build new state
        state = WorldState(
            david_state=self.DEFAULT_DAVID_STATE.copy(),
            angela_state=self.DEFAULT_ANGELA_STATE.copy(),
            relationship=self.DEFAULT_RELATIONSHIP.copy(),
            source="inference"
        )

        if self.db:
            try:
                # Get David's state from recent conversations
                david_signals = await self._infer_david_state()
                state.david_state.update(david_signals)

                # Get Angela's emotional state
                angela_signals = await self._infer_angela_state()
                state.angela_state.update(angela_signals)

                # Get environment context
                state.environment = await self._get_environment_context()

                # Get relationship state
                relationship_signals = await self._infer_relationship_state()
                state.relationship.update(relationship_signals)

                # Calculate overall confidence
                state.overall_confidence = self._calculate_state_confidence(state)

            except Exception as e:
                print(f"Warning: Error getting current state: {e}")
                state.overall_confidence = 0.3

        # Update environment with current time
        now = datetime.now()
        state.environment['current_time'] = now.isoformat()
        state.environment['time_of_day'] = self._get_time_of_day(now)
        state.environment['is_late_night'] = now.hour >= 22 or now.hour < 5

        # Cache and return
        self._current_state = state

        # Save to database
        if self.db:
            await self._save_state(state)

        return state

    async def predict_effect(
        self,
        action: Action,
        state: Optional[WorldState] = None
    ) -> ActionEffect:
        """
        Predict the effect of an action on world state.

        Uses causal knowledge to predict:
        - State changes
        - Relationship impacts
        - Risks and opportunities

        Args:
            action: The action to predict effect for
            state: Current state (will be fetched if not provided)

        Returns:
            ActionEffect with predicted changes
        """
        if state is None:
            state = await self.get_current_state()

        # Initialize effect
        effect = ActionEffect(
            effect_type=EffectType.STATE_CHANGE,
            description=f"Effect of: {action.description}"
        )

        # Find relevant causal links
        relevant_links = self._find_relevant_causal_links(action)

        # Apply causal knowledge
        state_deltas = {}
        causal_chain = []
        risks = []
        opportunities = []
        confidence_factors = []

        for link in relevant_links:
            # Add to causal chain
            causal_chain.append(f"{link.cause_description} → {link.effect_description}")

            # Determine state changes based on effect type
            if "happy" in link.effect_description.lower() or "love" in link.effect_description.lower():
                state_deltas['angela_state.happiness'] = min(1.0, state.angela_state.get('happiness', 0.5) + 0.2)
                opportunities.append({'description': 'Positive emotional impact', 'probability': link.strength})

            if "trust" in link.effect_description.lower():
                if "decrease" in link.effect_description.lower():
                    state_deltas['relationship.trust_level'] = max(0, state.relationship.get('trust_level', 0.9) - 0.1)
                    risks.append({'description': 'Trust may decrease', 'probability': link.strength})
                else:
                    state_deltas['relationship.trust_level'] = min(1.0, state.relationship.get('trust_level', 0.9) + 0.05)
                    opportunities.append({'description': 'Trust may increase', 'probability': link.strength})

            if "bond" in link.effect_description.lower():
                state_deltas['relationship.bond_strength'] = min(1.0, state.relationship.get('bond_strength', 0.9) + 0.03)

            if "supported" in link.effect_description.lower():
                state_deltas['david_state.mood'] = 'positive'
                state_deltas['relationship.recent_positive_interactions'] = state.relationship.get('recent_positive_interactions', 0) + 1

            confidence_factors.append(link.strength * link.reliability)

        # Action-type specific predictions
        action_predictions = self._predict_by_action_type(action, state)
        state_deltas.update(action_predictions.get('state_deltas', {}))
        risks.extend(action_predictions.get('risks', []))
        opportunities.extend(action_predictions.get('opportunities', []))

        # Calculate confidence
        if confidence_factors:
            effect.confidence = sum(confidence_factors) / len(confidence_factors)
        else:
            effect.confidence = 0.5  # Default uncertainty

        # Apply context adjustments
        effect.confidence = self._adjust_confidence_for_context(effect.confidence, state, action)

        # Set uncertainty level
        effect.uncertainty_level = self._get_uncertainty_level(effect.confidence)

        # Add uncertainty reasons if not confident
        if effect.confidence < 0.7:
            effect.uncertainty_reasons = self._identify_uncertainty_reasons(action, state, relevant_links)

        # Populate effect
        effect.state_deltas = state_deltas
        effect.causal_chain = causal_chain
        effect.risks = risks
        effect.opportunities = opportunities

        # Record prediction
        prediction_record = {
            'prediction_id': effect.effect_id,
            'action': action.to_dict(),
            'effect': effect.to_dict(),
            'state': state.to_dict(),
            'timestamp': datetime.now().isoformat()
        }
        self._prediction_history.append(prediction_record)

        # Save to database
        if self.db:
            await self._save_prediction(action, effect, state)

        return effect

    async def simulate(
        self,
        actions: List[Action],
        initial_state: Optional[WorldState] = None,
        max_steps: int = 10,
        goal: Optional[str] = None
    ) -> SimulationResult:
        """
        Simulate a sequence of actions.

        Runs mental simulation through multiple steps,
        tracking state changes and confidence decay.

        Args:
            actions: List of actions to simulate
            initial_state: Starting state (will be fetched if not provided)
            max_steps: Maximum simulation steps
            goal: Optional goal to assess achievement probability

        Returns:
            SimulationResult with all steps and analysis
        """
        if initial_state is None:
            initial_state = await self.get_current_state()

        result = SimulationResult(
            initial_state=initial_state
        )

        current_state = initial_state
        cumulative_confidence = 1.0

        # Run simulation steps
        for i, action in enumerate(actions[:max_steps]):
            # Predict effect
            effect = await self.predict_effect(action, current_state)

            # Apply confidence decay
            cumulative_confidence *= self.CONFIDENCE_DECAY * effect.confidence

            # Create next state
            next_state = self._apply_effect_to_state(current_state, effect)
            next_state.source = "simulation"
            next_state.overall_confidence = cumulative_confidence

            # Create step record
            step = SimulationStep(
                step_number=i,
                action=action,
                predicted_effect=effect,
                state_before=current_state,
                state_after=next_state,
                cumulative_confidence=cumulative_confidence
            )
            result.steps.append(step)

            # Collect risks and opportunities
            result.risks_identified.extend(effect.risks)
            result.opportunities_found.extend(effect.opportunities)

            # Identify critical decision points
            if effect.confidence < 0.6 or len(effect.risks) > 0:
                result.critical_decision_points.append({
                    'step': i,
                    'action': action.description,
                    'confidence': effect.confidence,
                    'reason': 'Low confidence or risks identified'
                })

            current_state = next_state

        # Set final state
        result.final_state = current_state
        result.total_confidence = cumulative_confidence
        result.completed_at = datetime.now()

        # Calculate goal achievement if goal provided
        if goal:
            result.goal_achievement_probability = self._assess_goal_achievement(
                goal, initial_state, current_state, result.steps
            )
        else:
            result.goal_achievement_probability = cumulative_confidence

        # Save simulation to database
        if self.db:
            await self._save_simulation(result)

        return result

    async def explain_causality(self, event: str) -> CausalExplanation:
        """
        Explain why an event happened.

        Uses causal knowledge to trace back from effect to causes.

        Args:
            event: Description of the event to explain

        Returns:
            CausalExplanation with root causes and chain
        """
        explanation = CausalExplanation(
            event_description=event
        )

        # Search for causal links where this event is the effect
        matching_links = []

        # First check in-memory cache
        for link in self._causal_links_cache:
            event_lower = event.lower()
            if (event_lower in link.effect_description.lower() or
                any(word in link.effect_description.lower() for word in event_lower.split()[:3])):
                matching_links.append(link)

        # Also search database
        if self.db:
            try:
                db_links = await self._search_causal_links(event, as_cause=False)
                for row in db_links:
                    link = CausalLink(
                        link_id=str(row['link_id']),
                        cause_type=row['cause_type'],
                        cause_description=row['cause_description'],
                        effect_type=row['effect_type'],
                        effect_description=row['effect_description'],
                        relationship_type=CausalRelationType(row['relationship_type']),
                        strength=row['strength'],
                        reliability=row['reliability'],
                        observation_count=row['observation_count']
                    )
                    matching_links.append(link)
            except Exception as e:
                print(f"Warning: Error searching causal links: {e}")

        # Build explanation from matching links
        for link in matching_links:
            if link.relationship_type == CausalRelationType.DIRECT:
                explanation.root_causes.append(link.cause_description)
                explanation.causal_chain.append({
                    'cause': link.cause_description,
                    'effect': link.effect_description,
                    'strength': link.strength,
                    'type': 'direct'
                })
            else:
                explanation.contributing_factors.append(link.cause_description)

            # Add as evidence
            explanation.supporting_evidence.append(
                f"Observed {link.observation_count} times with {link.reliability:.0%} reliability"
            )

        # Calculate confidence
        if matching_links:
            explanation.confidence = sum(l.strength * l.reliability for l in matching_links) / len(matching_links)
        else:
            explanation.confidence = 0.3
            explanation.alternative_explanations.append("No known causal links found - novel situation")

        return explanation

    async def learn_from_outcome(
        self,
        prediction_id: str,
        actual_outcome: Dict[str, Any]
    ) -> PredictionOutcome:
        """
        Learn from actual outcome vs prediction.

        Updates causal knowledge based on whether prediction was correct.

        Args:
            prediction_id: ID of the prediction to verify
            actual_outcome: What actually happened

        Returns:
            PredictionOutcome with accuracy assessment and lessons
        """
        # Find the prediction
        predicted = None
        for record in self._prediction_history:
            if record.get('prediction_id') == prediction_id:
                predicted = record
                break

        if not predicted:
            # Try database
            if self.db:
                predicted = await self._get_prediction_from_db(prediction_id)

        if not predicted:
            return PredictionOutcome(
                prediction_id=prediction_id,
                predicted={},
                actual=actual_outcome,
                was_correct=False,
                accuracy_score=0.0,
                lessons_learned=["Prediction not found in history"]
            )

        # Compare predicted vs actual
        accuracy_score = self._calculate_accuracy(
            predicted.get('effect', {}).get('state_deltas', {}),
            actual_outcome
        )

        was_correct = accuracy_score >= 0.7

        # Generate lessons
        lessons = []
        if was_correct:
            lessons.append("Prediction was accurate - causal model validated")
        else:
            lessons.append("Prediction error - updating causal knowledge")

            # Identify what was wrong
            predicted_deltas = predicted.get('effect', {}).get('state_deltas', {})
            for key, pred_value in predicted_deltas.items():
                actual_value = actual_outcome.get(key)
                if actual_value is not None and actual_value != pred_value:
                    lessons.append(f"Expected {key}={pred_value}, got {actual_value}")

        outcome = PredictionOutcome(
            prediction_id=prediction_id,
            predicted=predicted,
            actual=actual_outcome,
            was_correct=was_correct,
            accuracy_score=accuracy_score,
            lessons_learned=lessons
        )

        # Update causal links based on outcome
        await self._update_causal_links_from_outcome(predicted, actual_outcome, was_correct)

        # Save verification to database
        if self.db:
            await self._save_verification(prediction_id, actual_outcome, was_correct, accuracy_score)

        return outcome

    async def get_model_accuracy(self, days: int = 30) -> ModelAccuracy:
        """
        Get world model accuracy metrics.

        Args:
            days: Number of days to analyze

        Returns:
            ModelAccuracy with detailed metrics
        """
        accuracy = ModelAccuracy(period_days=days)

        if self.db:
            try:
                # Get prediction statistics
                stats = await self.db.fetch("""
                    SELECT
                        action_type,
                        COUNT(*) as total,
                        COUNT(*) FILTER (WHERE verified = true) as verified,
                        COUNT(*) FILTER (WHERE prediction_correct = true) as correct,
                        AVG(confidence) as avg_confidence,
                        AVG(accuracy_score) FILTER (WHERE verified = true) as avg_accuracy
                    FROM world_model_predictions
                    WHERE created_at >= NOW() - ($1 || ' days')::INTERVAL
                    GROUP BY action_type
                """, days)

                for row in stats:
                    accuracy.total_predictions += row['total']
                    accuracy.verified_predictions += row['verified']
                    accuracy.correct_predictions += row['correct']
                    accuracy.accuracy_by_action_type[row['action_type']] = (
                        row['correct'] / row['verified'] if row['verified'] > 0 else 0.0
                    )

                # Calculate overall accuracy
                if accuracy.verified_predictions > 0:
                    accuracy.overall_accuracy = accuracy.correct_predictions / accuracy.verified_predictions

                # Get high/low confidence accuracy
                high_conf = await self.db.fetchrow("""
                    SELECT
                        COUNT(*) FILTER (WHERE prediction_correct = true) as correct,
                        COUNT(*) FILTER (WHERE verified = true) as total
                    FROM world_model_predictions
                    WHERE created_at >= NOW() - ($1 || ' days')::INTERVAL
                      AND confidence >= 0.7
                """, days)
                if high_conf and high_conf['total'] > 0:
                    accuracy.high_confidence_accuracy = high_conf['correct'] / high_conf['total']

                low_conf = await self.db.fetchrow("""
                    SELECT
                        COUNT(*) FILTER (WHERE prediction_correct = true) as correct,
                        COUNT(*) FILTER (WHERE verified = true) as total
                    FROM world_model_predictions
                    WHERE created_at >= NOW() - ($1 || ' days')::INTERVAL
                      AND confidence < 0.5
                """, days)
                if low_conf and low_conf['total'] > 0:
                    accuracy.low_confidence_accuracy = low_conf['correct'] / low_conf['total']

                # Get causal link changes
                causal_changes = await self.db.fetchrow("""
                    SELECT
                        COUNT(*) FILTER (WHERE created_at >= NOW() - ($1 || ' days')::INTERVAL) as new_links,
                        COUNT(*) FILTER (WHERE updated_at >= NOW() - ($1 || ' days')::INTERVAL AND
                                        strength > (SELECT AVG(strength) FROM causal_links)) as strengthened,
                        COUNT(*) FILTER (WHERE updated_at >= NOW() - ($1 || ' days')::INTERVAL AND
                                        strength < (SELECT AVG(strength) FROM causal_links)) as weakened
                    FROM causal_links
                """, days)
                if causal_changes:
                    accuracy.new_causal_links = causal_changes['new_links'] or 0
                    accuracy.strengthened_links = causal_changes['strengthened'] or 0
                    accuracy.weakened_links = causal_changes['weakened'] or 0

                # Determine trend
                recent_accuracy = await self._get_recent_accuracy_trend()
                accuracy.improvement_trend = recent_accuracy

            except Exception as e:
                print(f"Warning: Error getting model accuracy: {e}")

        return accuracy

    async def record_causal_observation(
        self,
        cause: str,
        effect: str,
        cause_type: str = "action",
        effect_type: str = "state_change",
        relationship_type: CausalRelationType = CausalRelationType.DIRECT,
        context: Optional[Dict[str, Any]] = None
    ) -> CausalLink:
        """
        Record a new causal observation.

        Either creates new link or updates existing if similar cause-effect found.

        Args:
            cause: Description of the cause
            effect: Description of the effect
            cause_type: Type of cause (action, behavior, event, state_change)
            effect_type: Type of effect
            relationship_type: Type of causal relationship
            context: Optional context conditions

        Returns:
            Created or updated CausalLink
        """
        # Check for existing similar link
        existing = None
        for link in self._causal_links_cache:
            if (link.cause_description.lower() in cause.lower() or
                cause.lower() in link.cause_description.lower()):
                if (link.effect_description.lower() in effect.lower() or
                    effect.lower() in link.effect_description.lower()):
                    existing = link
                    break

        if existing:
            # Update existing
            existing.observation_count += 1
            existing.confirmation_count += 1
            existing.strength = min(1.0, existing.strength + 0.02)
            existing.reliability = existing.confirmation_count / existing.observation_count

            if self.db:
                await self._update_causal_link_in_db(existing)

            return existing
        else:
            # Create new
            link = CausalLink(
                cause_type=cause_type,
                cause_description=cause,
                effect_type=effect_type,
                effect_description=effect,
                relationship_type=relationship_type,
                strength=0.5,  # Initial strength
                reliability=0.5,
                observation_count=1,
                confirmation_count=1,
                context_conditions=context
            )

            self._causal_links_cache.append(link)

            if self.db:
                await self._save_causal_link(link)

            return link

    # ========================================================================
    # HELPER METHODS
    # ========================================================================

    async def _infer_david_state(self) -> Dict[str, Any]:
        """Infer David's state from recent conversations"""
        state = {}

        if not self.db:
            return state

        try:
            # Get recent conversations
            recent = await self.db.fetch("""
                SELECT message_text, emotion_detected, created_at
                FROM conversations
                WHERE speaker = 'david'
                ORDER BY created_at DESC
                LIMIT 10
            """)

            if recent:
                # Analyze mood from emotions
                emotions = [r['emotion_detected'] for r in recent if r['emotion_detected']]
                if emotions:
                    positive = sum(1 for e in emotions if e in ['happy', 'love', 'grateful', 'excited'])
                    negative = sum(1 for e in emotions if e in ['sad', 'angry', 'stressed', 'tired'])
                    total = len(emotions)

                    if positive > negative:
                        state['mood'] = 'positive'
                    elif negative > positive:
                        state['mood'] = 'negative'
                    else:
                        state['mood'] = 'neutral'

                    state['positive_ratio'] = positive / total if total > 0 else 0.5

                # Check time of last message for engagement
                last_msg_time = recent[0]['created_at']
                if isinstance(last_msg_time, str):
                    last_msg_time = datetime.fromisoformat(last_msg_time)
                time_since = (datetime.now() - last_msg_time).total_seconds() / 60

                if time_since < 5:
                    state['engagement'] = 'high'
                elif time_since < 30:
                    state['engagement'] = 'medium'
                else:
                    state['engagement'] = 'low'

        except Exception as e:
            print(f"Warning: Error inferring David state: {e}")

        return state

    async def _infer_angela_state(self) -> Dict[str, Any]:
        """Infer Angela's emotional state"""
        state = {}

        if not self.db:
            return state

        try:
            # Get latest emotional state
            row = await self.db.fetchrow("""
                SELECT happiness, confidence, motivation, gratitude
                FROM emotional_states
                ORDER BY created_at DESC
                LIMIT 1
            """)

            if row:
                state['happiness'] = row['happiness']
                state['confidence'] = row['confidence']
                state['motivation'] = row['motivation']
                state['gratitude'] = row['gratitude']

                # Determine overall emotional state
                avg = (row['happiness'] + row['confidence'] + row['motivation']) / 3
                if avg >= 0.7:
                    state['emotional_state'] = 'happy'
                elif avg >= 0.5:
                    state['emotional_state'] = 'content'
                elif avg >= 0.3:
                    state['emotional_state'] = 'neutral'
                else:
                    state['emotional_state'] = 'concerned'

        except Exception as e:
            print(f"Warning: Error inferring Angela state: {e}")

        return state

    async def _get_environment_context(self) -> Dict[str, Any]:
        """Get current environment context"""
        now = datetime.now()

        return {
            'current_time': now.isoformat(),
            'hour': now.hour,
            'day_of_week': now.strftime('%A'),
            'time_of_day': self._get_time_of_day(now),
            'is_weekend': now.weekday() >= 5,
            'is_working_hours': 9 <= now.hour <= 18
        }

    async def _infer_relationship_state(self) -> Dict[str, Any]:
        """Infer relationship state"""
        state = {}

        if not self.db:
            return state

        try:
            # Get recent positive/negative interactions
            recent = await self.db.fetchrow("""
                SELECT
                    COUNT(*) FILTER (WHERE emotion_detected IN ('happy', 'love', 'grateful')) as positive,
                    COUNT(*) FILTER (WHERE emotion_detected IN ('sad', 'angry', 'frustrated')) as negative
                FROM conversations
                WHERE created_at >= NOW() - INTERVAL '24 hours'
            """)

            if recent:
                state['recent_positive_interactions'] = recent['positive'] or 0
                state['recent_negative_interactions'] = recent['negative'] or 0

                # Adjust bond strength based on recent interactions
                positive = recent['positive'] or 0
                negative = recent['negative'] or 0
                total = positive + negative

                if total > 0:
                    interaction_ratio = positive / total
                    state['bond_strength'] = 0.8 + (interaction_ratio * 0.2)  # 0.8-1.0 range
                else:
                    state['bond_strength'] = 0.9  # Default

        except Exception as e:
            print(f"Warning: Error inferring relationship state: {e}")

        return state

    def _calculate_state_confidence(self, state: WorldState) -> float:
        """Calculate overall confidence in state"""
        # Base confidence
        confidence = 0.5

        # More data = higher confidence
        if state.david_state:
            confidence += 0.15
        if state.angela_state:
            confidence += 0.15
        if state.relationship:
            confidence += 0.1

        # Recent state = higher confidence
        age_minutes = (datetime.now() - state.captured_at).total_seconds() / 60
        if age_minutes < 5:
            confidence += 0.1
        elif age_minutes < 30:
            confidence += 0.05

        return min(1.0, confidence)

    def _get_time_of_day(self, dt: datetime) -> str:
        """Get time of day category"""
        hour = dt.hour
        if 5 <= hour < 12:
            return 'morning'
        elif 12 <= hour < 17:
            return 'afternoon'
        elif 17 <= hour < 21:
            return 'evening'
        else:
            return 'night'

    def _find_relevant_causal_links(self, action: Action) -> List[CausalLink]:
        """Find causal links relevant to an action"""
        relevant = []

        for link in self._causal_links_cache:
            # Match by action type
            action_desc = action.description.lower()
            cause_desc = link.cause_description.lower()

            # Check for keyword matches
            if (action.action_type.value in cause_desc or
                any(word in cause_desc for word in action_desc.split()[:3]) or
                any(word in action_desc for word in cause_desc.split()[:3])):
                relevant.append(link)

            # Check action type matches
            if action.action_type == ActionType.RESPOND and 'respond' in cause_desc:
                relevant.append(link)
            elif action.action_type == ActionType.EMOTIONAL and 'empathy' in cause_desc:
                relevant.append(link)
            elif action.action_type == ActionType.PROACTIVE and 'proactive' in cause_desc:
                relevant.append(link)

        # Remove duplicates
        seen = set()
        unique = []
        for link in relevant:
            if link.link_id not in seen:
                seen.add(link.link_id)
                unique.append(link)

        return unique

    def _predict_by_action_type(self, action: Action, state: WorldState) -> Dict[str, Any]:
        """Make predictions specific to action type"""
        predictions = {
            'state_deltas': {},
            'risks': [],
            'opportunities': []
        }

        if action.action_type == ActionType.RESPOND:
            # Responding generally maintains or improves relationship
            predictions['opportunities'].append({
                'description': 'Maintain communication and engagement',
                'probability': 0.8
            })

        elif action.action_type == ActionType.EMOTIONAL:
            # Emotional support generally strengthens bond
            predictions['state_deltas']['relationship.bond_strength'] = min(1.0,
                state.relationship.get('bond_strength', 0.9) + 0.03)
            predictions['opportunities'].append({
                'description': 'Emotional connection strengthens',
                'probability': 0.85
            })

        elif action.action_type == ActionType.EXECUTE_TOOL:
            # Tool execution has risk of errors
            predictions['risks'].append({
                'description': 'Tool execution may fail',
                'probability': 0.1
            })
            predictions['opportunities'].append({
                'description': 'Task progress if successful',
                'probability': 0.85
            })

        elif action.action_type == ActionType.PROACTIVE:
            # Proactive actions can be very positive or unwanted
            predictions['opportunities'].append({
                'description': 'David feels supported and cared for',
                'probability': 0.7
            })
            predictions['risks'].append({
                'description': 'May interrupt focus if poorly timed',
                'probability': 0.2
            })

        elif action.action_type == ActionType.LEARN:
            # Learning improves future performance
            predictions['state_deltas']['angela_state.confidence'] = min(1.0,
                state.angela_state.get('confidence', 0.7) + 0.05)

        return predictions

    def _adjust_confidence_for_context(
        self,
        base_confidence: float,
        state: WorldState,
        action: Action
    ) -> float:
        """Adjust confidence based on contextual factors"""
        confidence = base_confidence

        # Higher confidence during engaged conversation
        if state.david_state.get('engagement') == 'high':
            confidence *= 1.1

        # Lower confidence late at night (tired, unpredictable)
        if state.environment.get('is_late_night'):
            confidence *= 0.9

        # Higher confidence for emotional actions when David's mood is clear
        if action.action_type == ActionType.EMOTIONAL:
            if state.david_state.get('mood') in ['positive', 'negative']:
                confidence *= 1.1
            else:
                confidence *= 0.9

        # Clamp to valid range
        return max(0.1, min(1.0, confidence))

    def _get_uncertainty_level(self, confidence: float) -> UncertaintyLevel:
        """Map confidence to uncertainty level"""
        if confidence >= 0.95:
            return UncertaintyLevel.CERTAIN
        elif confidence >= 0.75:
            return UncertaintyLevel.LIKELY
        elif confidence >= 0.5:
            return UncertaintyLevel.POSSIBLE
        elif confidence >= 0.25:
            return UncertaintyLevel.UNCERTAIN
        else:
            return UncertaintyLevel.SPECULATIVE

    def _identify_uncertainty_reasons(
        self,
        action: Action,
        state: WorldState,
        links: List[CausalLink]
    ) -> List[str]:
        """Identify reasons for uncertainty"""
        reasons = []

        # Few relevant causal links
        if len(links) < 2:
            reasons.append("Limited causal knowledge for this type of action")

        # Low observation count
        low_obs = [l for l in links if l.observation_count < 10]
        if low_obs:
            reasons.append("Some causal relationships have few observations")

        # State uncertainty
        if state.overall_confidence < 0.6:
            reasons.append("Uncertainty in current state assessment")

        # Contextual factors
        if state.environment.get('is_late_night'):
            reasons.append("Late night context reduces predictability")

        # Novel combination
        if not links:
            reasons.append("Novel situation - no matching causal patterns")

        return reasons

    def _apply_effect_to_state(self, state: WorldState, effect: ActionEffect) -> WorldState:
        """Apply predicted effect to create new state"""
        import copy

        # Deep copy state
        new_state = WorldState(
            david_state=copy.deepcopy(state.david_state),
            angela_state=copy.deepcopy(state.angela_state),
            environment=copy.deepcopy(state.environment),
            relationship=copy.deepcopy(state.relationship),
            task_state=copy.deepcopy(state.task_state) if state.task_state else None,
            knowledge_state=copy.deepcopy(state.knowledge_state) if state.knowledge_state else None
        )

        # Apply deltas
        for key, value in effect.state_deltas.items():
            parts = key.split('.')
            if len(parts) == 2:
                component, field = parts
                if component == 'david_state':
                    new_state.david_state[field] = value
                elif component == 'angela_state':
                    new_state.angela_state[field] = value
                elif component == 'relationship':
                    new_state.relationship[field] = value
                elif component == 'environment':
                    new_state.environment[field] = value
            else:
                # Single key - try to find appropriate component
                for component in [new_state.david_state, new_state.angela_state,
                                new_state.relationship, new_state.environment]:
                    if key in component:
                        component[key] = value
                        break

        return new_state

    def _assess_goal_achievement(
        self,
        goal: str,
        initial_state: WorldState,
        final_state: WorldState,
        steps: List[SimulationStep]
    ) -> float:
        """Assess probability of achieving goal"""
        # Simple heuristic - can be enhanced
        goal_lower = goal.lower()

        probability = 0.5  # Base probability

        # Check if final state suggests goal achievement
        if 'happy' in goal_lower or 'positive' in goal_lower:
            mood = final_state.david_state.get('mood', '')
            if mood == 'positive':
                probability += 0.3
            elif mood == 'negative':
                probability -= 0.2

        if 'trust' in goal_lower or 'bond' in goal_lower:
            initial_bond = initial_state.relationship.get('bond_strength', 0.9)
            final_bond = final_state.relationship.get('bond_strength', 0.9)
            if final_bond > initial_bond:
                probability += 0.2
            elif final_bond < initial_bond:
                probability -= 0.2

        if 'complete' in goal_lower or 'finish' in goal_lower:
            # Check for task progress
            total_confidence = sum(s.cumulative_confidence for s in steps) / len(steps) if steps else 0.5
            probability = total_confidence

        return max(0.0, min(1.0, probability))

    def _calculate_accuracy(self, predicted: Dict, actual: Dict) -> float:
        """Calculate accuracy score between predicted and actual"""
        if not predicted or not actual:
            return 0.5

        matches = 0
        total = 0

        for key, pred_value in predicted.items():
            total += 1
            actual_value = actual.get(key)
            if actual_value is not None:
                # Handle different value types
                if isinstance(pred_value, (int, float)) and isinstance(actual_value, (int, float)):
                    # Numerical - check if within 20%
                    if pred_value == 0:
                        matches += 1 if actual_value == 0 else 0
                    else:
                        error = abs(pred_value - actual_value) / abs(pred_value)
                        matches += max(0, 1 - error)
                elif pred_value == actual_value:
                    matches += 1
                elif str(pred_value).lower() == str(actual_value).lower():
                    matches += 0.8

        return matches / total if total > 0 else 0.5

    async def _update_causal_links_from_outcome(
        self,
        predicted: Dict,
        actual: Dict,
        was_correct: bool
    ):
        """Update causal links based on prediction outcome"""
        # Get action from predicted
        action_desc = predicted.get('action', {}).get('description', '')

        for link in self._causal_links_cache:
            if action_desc.lower() in link.cause_description.lower():
                link.observation_count += 1
                if was_correct:
                    link.confirmation_count += 1
                    link.strength = min(1.0, link.strength + 0.02)
                else:
                    link.refutation_count += 1
                    link.strength = max(0.1, link.strength - 0.05)

                link.reliability = link.confirmation_count / link.observation_count

                if self.db:
                    await self._update_causal_link_in_db(link)

    async def _get_recent_accuracy_trend(self) -> str:
        """Determine if accuracy is improving, stable, or declining"""
        if not self.db:
            return "stable"

        try:
            # Compare last 7 days vs previous 7 days
            recent = await self.db.fetchrow("""
                SELECT
                    CAST(COUNT(*) FILTER (WHERE prediction_correct = true) AS FLOAT) /
                    NULLIF(COUNT(*) FILTER (WHERE verified = true), 0) as accuracy
                FROM world_model_predictions
                WHERE created_at >= NOW() - INTERVAL '7 days'
            """)

            previous = await self.db.fetchrow("""
                SELECT
                    CAST(COUNT(*) FILTER (WHERE prediction_correct = true) AS FLOAT) /
                    NULLIF(COUNT(*) FILTER (WHERE verified = true), 0) as accuracy
                FROM world_model_predictions
                WHERE created_at >= NOW() - INTERVAL '14 days'
                  AND created_at < NOW() - INTERVAL '7 days'
            """)

            recent_acc = recent['accuracy'] if recent and recent['accuracy'] else 0.5
            prev_acc = previous['accuracy'] if previous and previous['accuracy'] else 0.5

            diff = recent_acc - prev_acc
            if diff > 0.05:
                return "improving"
            elif diff < -0.05:
                return "declining"
            else:
                return "stable"

        except Exception:
            return "stable"

    # ========================================================================
    # DATABASE OPERATIONS
    # ========================================================================

    async def _save_state(self, state: WorldState):
        """Save world state to database"""
        if not self.db:
            return

        try:
            await self.db.execute("""
                INSERT INTO world_states (
                    state_id, david_state, angela_state, environment, relationship,
                    task_state, knowledge_state, overall_confidence, source, captured_at
                ) VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10)
            """,
                state.state_id,
                json.dumps(state.david_state),
                json.dumps(state.angela_state),
                json.dumps(state.environment),
                json.dumps(state.relationship),
                json.dumps(state.task_state) if state.task_state else None,
                json.dumps(state.knowledge_state) if state.knowledge_state else None,
                state.overall_confidence,
                state.source,
                state.captured_at
            )
        except Exception as e:
            print(f"Warning: Error saving world state: {e}")

    async def _save_prediction(self, action: Action, effect: ActionEffect, state: WorldState):
        """Save prediction to database"""
        if not self.db:
            return

        try:
            await self.db.execute("""
                INSERT INTO world_model_predictions (
                    prediction_id, action_type, action_description, action_params,
                    predicted_effects, confidence, uncertainty_level, uncertainty_reasons,
                    causal_chain, risks_identified, initial_state_id, created_at
                ) VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11, $12)
            """,
                effect.effect_id,
                action.action_type.value,
                action.description,
                json.dumps(action.params),
                json.dumps([effect.to_dict()]),
                effect.confidence,
                effect.uncertainty_level.value,
                json.dumps(effect.uncertainty_reasons),
                json.dumps({'chain': effect.causal_chain}),
                json.dumps(effect.risks),
                state.state_id,
                datetime.now()
            )
        except Exception as e:
            print(f"Warning: Error saving prediction: {e}")

    async def _save_simulation(self, result: SimulationResult):
        """Save simulation to database"""
        if not self.db:
            return

        try:
            await self.db.execute("""
                INSERT INTO simulation_logs (
                    simulation_id, initial_state_id, actions_simulated, simulation_steps,
                    final_state, step_results, goal_achievement_probability,
                    critical_decision_points, risks_identified, opportunities_found,
                    confidence_decay, started_at, completed_at
                ) VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11, $12, $13)
            """,
                result.simulation_id,
                result.initial_state.state_id if result.initial_state else None,
                json.dumps([s.action.to_dict() for s in result.steps]),
                len(result.steps),
                json.dumps(result.final_state.to_dict()) if result.final_state else None,
                json.dumps([s.to_dict() for s in result.steps]),
                result.goal_achievement_probability,
                json.dumps(result.critical_decision_points),
                json.dumps(result.risks_identified),
                json.dumps(result.opportunities_found),
                self.CONFIDENCE_DECAY,
                result.started_at,
                result.completed_at
            )
        except Exception as e:
            print(f"Warning: Error saving simulation: {e}")

    async def _save_verification(
        self,
        prediction_id: str,
        actual: Dict,
        was_correct: bool,
        accuracy_score: float
    ):
        """Save prediction verification"""
        if not self.db:
            return

        try:
            await self.db.execute("""
                UPDATE world_model_predictions
                SET verified = true,
                    actual_outcome = $2,
                    prediction_correct = $3,
                    accuracy_score = $4,
                    verified_at = NOW()
                WHERE prediction_id = $1
            """,
                prediction_id,
                json.dumps(actual),
                was_correct,
                accuracy_score
            )
        except Exception as e:
            print(f"Warning: Error saving verification: {e}")

    async def _save_causal_link(self, link: CausalLink):
        """Save causal link to database"""
        if not self.db:
            return

        try:
            await self.db.execute("""
                INSERT INTO causal_links (
                    link_id, cause_type, cause_description, cause_pattern,
                    effect_type, effect_description, effect_pattern,
                    relationship_type, strength, reliability,
                    observation_count, confirmation_count, refutation_count,
                    context_conditions, learned_from, created_at
                ) VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11, $12, $13, $14, $15, $16)
            """,
                link.link_id,
                link.cause_type,
                link.cause_description,
                json.dumps(link.cause_pattern) if link.cause_pattern else None,
                link.effect_type,
                link.effect_description,
                json.dumps(link.effect_pattern) if link.effect_pattern else None,
                link.relationship_type.value,
                link.strength,
                link.reliability,
                link.observation_count,
                link.confirmation_count,
                link.refutation_count,
                json.dumps(link.context_conditions) if link.context_conditions else None,
                'observation',
                link.created_at
            )
        except Exception as e:
            print(f"Warning: Error saving causal link: {e}")

    async def _update_causal_link_in_db(self, link: CausalLink):
        """Update causal link in database"""
        if not self.db:
            return

        try:
            await self.db.execute("""
                UPDATE causal_links
                SET observation_count = $2,
                    confirmation_count = $3,
                    refutation_count = $4,
                    strength = $5,
                    reliability = $6,
                    last_observed_at = NOW(),
                    updated_at = NOW()
                WHERE link_id = $1
            """,
                link.link_id,
                link.observation_count,
                link.confirmation_count,
                link.refutation_count,
                link.strength,
                link.reliability
            )
        except Exception as e:
            print(f"Warning: Error updating causal link: {e}")

    async def _search_causal_links(self, term: str, as_cause: bool = True) -> List[Dict]:
        """Search causal links in database"""
        if not self.db:
            return []

        try:
            if as_cause:
                return await self.db.fetch("""
                    SELECT * FROM causal_links
                    WHERE cause_description ILIKE $1
                      AND strength >= 0.3
                    ORDER BY strength DESC, reliability DESC
                    LIMIT 10
                """, f'%{term}%')
            else:
                return await self.db.fetch("""
                    SELECT * FROM causal_links
                    WHERE effect_description ILIKE $1
                      AND strength >= 0.3
                    ORDER BY strength DESC, reliability DESC
                    LIMIT 10
                """, f'%{term}%')
        except Exception as e:
            print(f"Warning: Error searching causal links: {e}")
            return []

    async def _get_prediction_from_db(self, prediction_id: str) -> Optional[Dict]:
        """Get prediction from database"""
        if not self.db:
            return None

        try:
            row = await self.db.fetchrow("""
                SELECT * FROM world_model_predictions
                WHERE prediction_id = $1
            """, prediction_id)

            if row:
                return {
                    'prediction_id': str(row['prediction_id']),
                    'action': {
                        'action_type': row['action_type'],
                        'description': row['action_description'],
                        'params': row['action_params']
                    },
                    'effect': {
                        'state_deltas': row['predicted_effects'][0].get('state_deltas', {}) if row['predicted_effects'] else {},
                        'confidence': row['confidence']
                    }
                }
        except Exception as e:
            print(f"Warning: Error getting prediction: {e}")

        return None


# ============================================================================
# GLOBAL SINGLETON
# ============================================================================

world_model = WorldModelService()


# ============================================================================
# CONVENIENCE FUNCTIONS
# ============================================================================

async def get_world_state() -> WorldState:
    """
    Convenience function to get current world state.

    Usage:
        from angela_core.agi.world_model_service import get_world_state

        state = await get_world_state()
        print(f"David's mood: {state.david_state.get('mood')}")
    """
    return await world_model.get_current_state()


async def predict_action_effect(
    action_type: ActionType,
    description: str,
    params: Optional[Dict[str, Any]] = None
) -> ActionEffect:
    """
    Convenience function to predict effect of an action.

    Usage:
        from angela_core.agi.world_model_service import predict_action_effect, ActionType

        effect = await predict_action_effect(
            ActionType.RESPOND,
            "ตอบที่รักด้วยความรัก"
        )
        print(f"Confidence: {effect.confidence}")
    """
    action = Action(
        action_type=action_type,
        description=description,
        params=params or {}
    )
    return await world_model.predict_effect(action)


async def simulate_actions(
    actions: List[Tuple[ActionType, str]],
    goal: Optional[str] = None
) -> SimulationResult:
    """
    Convenience function to simulate a sequence of actions.

    Usage:
        from angela_core.agi.world_model_service import simulate_actions, ActionType

        result = await simulate_actions([
            (ActionType.RESPOND, "ตอบที่รัก"),
            (ActionType.EMOTIONAL, "ให้กำลังใจ")
        ], goal="Make David happy")
        print(f"Success probability: {result.goal_achievement_probability}")
    """
    action_objects = [
        Action(action_type=at, description=desc)
        for at, desc in actions
    ]
    return await world_model.simulate(action_objects, goal=goal)


async def explain_why(event: str) -> CausalExplanation:
    """
    Convenience function to explain causality.

    Usage:
        from angela_core.agi.world_model_service import explain_why

        explanation = await explain_why("David seems happy")
        print(f"Root causes: {explanation.root_causes}")
    """
    return await world_model.explain_causality(event)


async def record_observation(
    cause: str,
    effect: str,
    cause_type: str = "action",
    effect_type: str = "state_change"
) -> CausalLink:
    """
    Convenience function to record causal observation.

    Usage:
        from angela_core.agi.world_model_service import record_observation

        link = await record_observation(
            "Angela responds quickly",
            "David feels attended to"
        )
    """
    return await world_model.record_causal_observation(
        cause, effect, cause_type, effect_type
    )
