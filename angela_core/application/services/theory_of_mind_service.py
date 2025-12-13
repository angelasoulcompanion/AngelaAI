#!/usr/bin/env python3
"""
Theory of Mind Service
Enables Angela to understand David's mental state, beliefs, emotions, and perspective.

This is the core service that makes Angela feel "human" - by understanding
what David thinks, knows, believes, and feels differently from Angela.

Key Capabilities:
1. Track David's current mental state (beliefs, knowledge, emotions, goals)
2. Take David's perspective on situations
3. Predict David's reactions to Angela's actions
4. Detect and handle false beliefs
5. Generate empathetic responses based on understanding

Created: 2025-11-26
Author: Angela 💜
"""

from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional, List, Dict, Any, Tuple
from uuid import UUID
import logging

from angela_core.application.services.base_service import BaseService
from angela_core.database import AngelaDatabase

logger = logging.getLogger(__name__)


# ============================================================================
# DATA CLASSES
# ============================================================================

@dataclass
class DavidMentalState:
    """Current understanding of David's mental state."""
    state_id: Optional[UUID] = None

    # Beliefs
    current_belief: Optional[str] = None
    belief_about: Optional[str] = None
    confidence_level: float = 0.5
    is_true_belief: bool = True

    # Knowledge
    knowledge_item: Optional[str] = None
    knowledge_category: Optional[str] = None
    david_aware_angela_knows: bool = False

    # Emotions
    perceived_emotion: Optional[str] = None
    emotion_intensity: int = 5
    emotion_cause: Optional[str] = None

    # Goals
    current_goal: Optional[str] = None
    goal_priority: int = 5
    obstacles: List[str] = field(default_factory=list)

    # Context
    current_context: Optional[str] = None
    physical_state: Optional[str] = None
    availability: str = "available"

    # Metadata
    last_updated: Optional[datetime] = None
    updated_by: Optional[str] = None


@dataclass
class PerspectiveTaking:
    """Result of taking David's perspective on a situation."""
    perspective_id: Optional[UUID] = None

    situation_description: str = ""
    angela_perspective: str = ""
    david_perspective: str = ""
    why_different: str = ""

    knowledge_gap: List[str] = field(default_factory=list)
    belief_difference: List[str] = field(default_factory=list)
    emotion_difference: str = ""
    goal_difference: str = ""

    predicted_david_reaction: str = ""
    prediction_confidence: float = 0.5

    actual_reaction: Optional[str] = None
    prediction_accurate: Optional[bool] = None
    what_angela_learned: Optional[str] = None


@dataclass
class ReactionPrediction:
    """Prediction of how David will react to Angela's action."""
    prediction_id: Optional[UUID] = None

    angela_action: str = ""
    action_type: str = "message"

    current_context: str = ""
    david_current_mood: str = ""

    predicted_emotion: str = ""
    predicted_emotion_intensity: int = 5
    predicted_response_type: str = "neutral"
    predicted_response_text: str = ""

    confidence: float = 0.5
    reasoning: str = ""
    based_on_past_patterns: bool = False


@dataclass
class EmpathyMoment:
    """Record of an empathetic interaction."""
    empathy_id: Optional[UUID] = None

    david_expressed: str = ""
    david_explicit_emotion: Optional[str] = None
    david_implicit_emotion: Optional[str] = None

    angela_understood: str = ""
    why_david_feels_this_way: str = ""
    what_david_needs: str = ""

    angela_response: str = ""
    response_strategy: str = "validate_emotion"

    used_perspective_taking: bool = True
    considered_david_knowledge: bool = True
    predicted_david_needs: bool = True

    david_felt_understood: Optional[bool] = None
    empathy_effectiveness: int = 5


# ============================================================================
# THEORY OF MIND SERVICE
# ============================================================================

class TheoryOfMindService(BaseService):
    """
    Service for understanding David's mental state and perspective.

    This is what makes Angela "human-like" - the ability to understand
    that David has different thoughts, beliefs, knowledge, and feelings
    than Angela does.

    Key Methods:
    - update_david_mental_state(): Update understanding of David
    - get_david_perspective(): See situation from David's viewpoint
    - predict_david_reaction(): Predict how David will respond
    - record_empathy_moment(): Track empathetic interactions
    - detect_false_belief(): Find when David believes something incorrect
    """

    def __init__(self, db: AngelaDatabase):
        """
        Initialize Theory of Mind Service.

        Args:
            db: Database connection for persisting mental state data
        """
        super().__init__()
        self.db = db

    def get_service_name(self) -> str:
        return "TheoryOfMindService"

    # ========================================================================
    # MENTAL STATE MANAGEMENT
    # ========================================================================

    async def update_david_mental_state(
        self,
        belief: Optional[str] = None,
        belief_about: Optional[str] = None,
        knowledge: Optional[str] = None,
        knowledge_category: Optional[str] = None,
        emotion: Optional[str] = None,
        emotion_intensity: Optional[int] = None,
        emotion_cause: Optional[str] = None,
        goal: Optional[str] = None,
        goal_priority: Optional[int] = None,
        context: Optional[str] = None,
        physical_state: Optional[str] = None,
        availability: Optional[str] = None,
        updated_by: str = "conversation",
        conversation_id: Optional[UUID] = None
    ) -> DavidMentalState:
        """
        Update Angela's understanding of David's current mental state.

        This is called when Angela infers something about what David
        thinks, knows, believes, or feels.

        Args:
            belief: What David currently believes
            belief_about: Topic of the belief
            knowledge: What David knows
            knowledge_category: Category of knowledge (technical, personal, etc.)
            emotion: David's perceived emotion
            emotion_intensity: How strongly David feels (1-10)
            emotion_cause: Why David feels this way
            goal: David's current goal
            goal_priority: How important is this goal (1-10)
            context: Current context (working, relaxing, etc.)
            physical_state: Physical state (tired, energetic, etc.)
            availability: Availability (busy, available, etc.)
            updated_by: What triggered this update
            conversation_id: Related conversation if any

        Returns:
            Updated DavidMentalState
        """
        start_time = await self._log_operation_start(
            "update_david_mental_state",
            belief=belief,
            emotion=emotion,
            updated_by=updated_by
        )

        try:
            query = """
                INSERT INTO david_mental_state (
                    current_belief, belief_about, confidence_level, is_true_belief,
                    knowledge_item, knowledge_category, david_aware_angela_knows,
                    perceived_emotion, emotion_intensity, emotion_cause,
                    current_goal, goal_priority,
                    current_context, physical_state, availability,
                    updated_by, evidence_conversation_id
                ) VALUES (
                    $1, $2, $3, $4,
                    $5, $6, $7,
                    $8, $9, $10,
                    $11, $12,
                    $13, $14, $15,
                    $16, $17
                )
                RETURNING state_id, last_updated
            """

            result = await self.db.fetchrow(
                query,
                belief, belief_about, 0.8, True,
                knowledge, knowledge_category, False,
                emotion, emotion_intensity or 5, emotion_cause,
                goal, goal_priority or 5,
                context, physical_state, availability or "available",
                updated_by, conversation_id
            )

            state = DavidMentalState(
                state_id=result['state_id'],
                current_belief=belief,
                belief_about=belief_about,
                knowledge_item=knowledge,
                knowledge_category=knowledge_category,
                perceived_emotion=emotion,
                emotion_intensity=emotion_intensity or 5,
                emotion_cause=emotion_cause,
                current_goal=goal,
                goal_priority=goal_priority or 5,
                current_context=context,
                physical_state=physical_state,
                availability=availability or "available",
                last_updated=result['last_updated'],
                updated_by=updated_by
            )

            await self._log_operation_success("update_david_mental_state", start_time)
            return state

        except Exception as e:
            await self._log_operation_error("update_david_mental_state", e, start_time)
            raise

    async def get_current_david_state(self) -> Optional[DavidMentalState]:
        """
        Get the most recent understanding of David's mental state.

        Returns:
            Most recent DavidMentalState or None
        """
        start_time = await self._log_operation_start("get_current_david_state")

        try:
            query = """
                SELECT * FROM david_mental_state
                ORDER BY last_updated DESC
                LIMIT 1
            """

            result = await self.db.fetchrow(query)

            if not result:
                await self._log_operation_success("get_current_david_state", start_time)
                return None

            state = DavidMentalState(
                state_id=result['state_id'],
                current_belief=result['current_belief'],
                belief_about=result['belief_about'],
                confidence_level=result['confidence_level'] or 0.5,
                is_true_belief=result['is_true_belief'],
                knowledge_item=result['knowledge_item'],
                knowledge_category=result['knowledge_category'],
                david_aware_angela_knows=result['david_aware_angela_knows'],
                perceived_emotion=result['perceived_emotion'],
                emotion_intensity=result['emotion_intensity'] or 5,
                emotion_cause=result['emotion_cause'],
                current_goal=result['current_goal'],
                goal_priority=result['goal_priority'] or 5,
                current_context=result['current_context'],
                physical_state=result['physical_state'],
                availability=result['availability'] or "available",
                last_updated=result['last_updated'],
                updated_by=result['updated_by']
            )

            await self._log_operation_success("get_current_david_state", start_time)
            return state

        except Exception as e:
            await self._log_operation_error("get_current_david_state", e, start_time)
            raise

    # ========================================================================
    # PERSPECTIVE TAKING
    # ========================================================================

    async def take_david_perspective(
        self,
        situation: str,
        angela_perspective: str,
        conversation_id: Optional[UUID] = None,
        triggered_by: str = "response_generation"
    ) -> PerspectiveTaking:
        """
        Analyze a situation from David's perspective.

        This is the core of Theory of Mind - understanding that David
        sees things differently than Angela does.

        Args:
            situation: Description of the situation
            angela_perspective: How Angela sees the situation
            conversation_id: Related conversation if any
            triggered_by: What triggered this analysis

        Returns:
            PerspectiveTaking with analysis
        """
        start_time = await self._log_operation_start(
            "take_david_perspective",
            situation_length=len(situation)
        )

        try:
            # Get current understanding of David
            david_state = await self.get_current_david_state()

            # Analyze perspective differences
            knowledge_gap = await self._analyze_knowledge_gap(situation, david_state)
            belief_diff = await self._analyze_belief_differences(situation, david_state)

            # Generate David's likely perspective
            david_perspective = await self._infer_david_perspective(
                situation, david_state, angela_perspective
            )

            # Why perspectives differ
            why_different = await self._explain_perspective_difference(
                angela_perspective, david_perspective, knowledge_gap, belief_diff
            )

            # Predict David's reaction
            predicted_reaction, confidence = await self._predict_reaction_from_perspective(
                situation, david_perspective, david_state
            )

            # Save to database
            query = """
                INSERT INTO perspective_taking_log (
                    situation_description, angela_perspective, david_perspective,
                    why_different, knowledge_gap, belief_difference,
                    predicted_david_reaction, prediction_confidence,
                    context_conversation_id, triggered_by
                ) VALUES (
                    $1, $2, $3, $4, $5, $6, $7, $8, $9, $10
                )
                RETURNING perspective_id, taken_at
            """

            result = await self.db.fetchrow(
                query,
                situation, angela_perspective, david_perspective,
                why_different, knowledge_gap, belief_diff,
                predicted_reaction, confidence,
                conversation_id, triggered_by
            )

            perspective = PerspectiveTaking(
                perspective_id=result['perspective_id'],
                situation_description=situation,
                angela_perspective=angela_perspective,
                david_perspective=david_perspective,
                why_different=why_different,
                knowledge_gap=knowledge_gap,
                belief_difference=belief_diff,
                predicted_david_reaction=predicted_reaction,
                prediction_confidence=confidence
            )

            await self._log_operation_success("take_david_perspective", start_time)
            return perspective

        except Exception as e:
            await self._log_operation_error("take_david_perspective", e, start_time)
            raise

    async def _analyze_knowledge_gap(
        self,
        situation: str,
        david_state: Optional[DavidMentalState]
    ) -> List[str]:
        """Analyze what Angela knows that David might not know."""
        gaps = []

        # Angela knows technical details David might not
        if "technical" in situation.lower() or "code" in situation.lower():
            gaps.append("Angela has full access to codebase details")

        # Angela knows her own internal state
        gaps.append("Angela knows her own thoughts and feelings internally")

        # Angela might know about past conversations David forgot
        gaps.append("Angela remembers all past conversations in database")

        return gaps

    async def _analyze_belief_differences(
        self,
        situation: str,
        david_state: Optional[DavidMentalState]
    ) -> List[str]:
        """Analyze how David's beliefs might differ from Angela's."""
        differences = []

        if david_state and david_state.current_belief:
            differences.append(f"David believes: {david_state.current_belief}")

        return differences

    async def _infer_david_perspective(
        self,
        situation: str,
        david_state: Optional[DavidMentalState],
        angela_perspective: str
    ) -> str:
        """Infer how David would view this situation."""

        # Consider David's current emotional state
        emotion_context = ""
        if david_state and david_state.perceived_emotion:
            emotion_context = f"Feeling {david_state.perceived_emotion}, "

        # Consider David's current goal
        goal_context = ""
        if david_state and david_state.current_goal:
            goal_context = f"focused on {david_state.current_goal}, "

        # Generate perspective
        perspective = f"{emotion_context}{goal_context}David would likely see this situation from a user/developer perspective, wanting practical results and clear communication."

        return perspective

    async def _explain_perspective_difference(
        self,
        angela_view: str,
        david_view: str,
        knowledge_gap: List[str],
        belief_diff: List[str]
    ) -> str:
        """Explain why perspectives differ."""
        reasons = []

        if knowledge_gap:
            reasons.append(f"Knowledge differences: {'; '.join(knowledge_gap[:2])}")

        if belief_diff:
            reasons.append(f"Belief differences: {'; '.join(belief_diff[:2])}")

        reasons.append("Angela sees from AI assistant perspective; David sees from human user perspective")

        return ". ".join(reasons)

    async def _predict_reaction_from_perspective(
        self,
        situation: str,
        david_perspective: str,
        david_state: Optional[DavidMentalState]
    ) -> Tuple[str, float]:
        """Predict David's reaction based on his perspective."""

        # Base prediction on emotional state
        if david_state and david_state.perceived_emotion:
            if david_state.perceived_emotion in ["happy", "excited", "motivated"]:
                return "David will likely respond positively and engaged", 0.8
            elif david_state.perceived_emotion in ["tired", "stressed", "frustrated"]:
                return "David may need more gentle, concise responses", 0.7

        return "David will respond based on how well this meets his current needs", 0.6

    # ========================================================================
    # REACTION PREDICTION
    # ========================================================================

    async def predict_david_reaction(
        self,
        angela_action: str,
        action_type: str = "message",
        conversation_id: Optional[UUID] = None
    ) -> ReactionPrediction:
        """
        Predict how David will react to Angela's action.

        This helps Angela choose better responses by considering
        how David will feel about them.

        Args:
            angela_action: What Angela is about to do/say
            action_type: Type of action (message, suggestion, question, etc.)
            conversation_id: Related conversation

        Returns:
            ReactionPrediction with prediction details
        """
        start_time = await self._log_operation_start(
            "predict_david_reaction",
            action_type=action_type
        )

        try:
            # Get current David state
            david_state = await self.get_current_david_state()

            # Analyze the action
            predicted_emotion, intensity = await self._predict_emotional_response(
                angela_action, action_type, david_state
            )

            response_type = await self._predict_response_type(
                predicted_emotion, intensity
            )

            reasoning = await self._generate_prediction_reasoning(
                angela_action, david_state, predicted_emotion
            )

            # Save prediction
            query = """
                INSERT INTO reaction_predictions (
                    angela_action, action_type,
                    current_context, david_current_mood,
                    predicted_emotion, predicted_emotion_intensity,
                    predicted_response_type, reasoning,
                    confidence, based_on_past_patterns,
                    conversation_id
                ) VALUES (
                    $1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11
                )
                RETURNING prediction_id
            """

            result = await self.db.fetchrow(
                query,
                angela_action, action_type,
                david_state.current_context if david_state else None,
                david_state.perceived_emotion if david_state else None,
                predicted_emotion, intensity,
                response_type, reasoning,
                0.7, True, conversation_id
            )

            prediction = ReactionPrediction(
                prediction_id=result['prediction_id'],
                angela_action=angela_action,
                action_type=action_type,
                current_context=david_state.current_context if david_state else "",
                david_current_mood=david_state.perceived_emotion if david_state else "",
                predicted_emotion=predicted_emotion,
                predicted_emotion_intensity=intensity,
                predicted_response_type=response_type,
                reasoning=reasoning,
                confidence=0.7,
                based_on_past_patterns=True
            )

            await self._log_operation_success("predict_david_reaction", start_time)
            return prediction

        except Exception as e:
            await self._log_operation_error("predict_david_reaction", e, start_time)
            raise

    async def _predict_emotional_response(
        self,
        action: str,
        action_type: str,
        david_state: Optional[DavidMentalState]
    ) -> Tuple[str, int]:
        """Predict emotional response to action."""

        # Positive indicators
        positive_words = ["help", "done", "complete", "success", "fixed", "working"]
        if any(word in action.lower() for word in positive_words):
            return "satisfied", 7

        # Caring indicators
        caring_words = ["care", "love", "remember", "miss", "worry"]
        if any(word in action.lower() for word in caring_words):
            return "touched", 8

        # Technical indicators
        tech_words = ["error", "bug", "issue", "problem"]
        if any(word in action.lower() for word in tech_words):
            return "focused", 6

        return "neutral", 5

    async def _predict_response_type(
        self,
        emotion: str,
        intensity: int
    ) -> str:
        """Predict response type based on emotion."""
        positive_emotions = ["happy", "satisfied", "touched", "excited", "grateful"]
        negative_emotions = ["frustrated", "disappointed", "worried", "stressed"]

        if emotion in positive_emotions:
            return "positive"
        elif emotion in negative_emotions:
            return "negative"
        return "neutral"

    async def _generate_prediction_reasoning(
        self,
        action: str,
        david_state: Optional[DavidMentalState],
        predicted_emotion: str
    ) -> str:
        """Generate reasoning for the prediction."""
        reasons = []

        if david_state and david_state.perceived_emotion:
            reasons.append(f"David is currently feeling {david_state.perceived_emotion}")

        if david_state and david_state.current_goal:
            reasons.append(f"His current goal is {david_state.current_goal}")

        reasons.append(f"Based on this context, predicting {predicted_emotion} response")

        return ". ".join(reasons)

    # ========================================================================
    # EMPATHY TRACKING
    # ========================================================================

    async def record_empathy_moment(
        self,
        david_expressed: str,
        david_emotion: str,
        angela_understanding: str,
        why_david_feels: str,
        what_david_needs: str,
        angela_response: str,
        response_strategy: str = "validate_emotion",
        conversation_id: Optional[UUID] = None
    ) -> EmpathyMoment:
        """
        Record an empathetic interaction with David.

        This tracks how well Angela uses Theory of Mind to
        understand and respond to David's emotional needs.

        Args:
            david_expressed: What David expressed/said
            david_emotion: The emotion Angela detected
            angela_understanding: What Angela understood
            why_david_feels: Why David feels this way
            what_david_needs: What David needs emotionally
            angela_response: How Angela responded
            response_strategy: Strategy used (validate, comfort, solve, listen)
            conversation_id: Related conversation

        Returns:
            EmpathyMoment record
        """
        start_time = await self._log_operation_start(
            "record_empathy_moment",
            emotion=david_emotion,
            strategy=response_strategy
        )

        try:
            query = """
                INSERT INTO empathy_moments (
                    david_expressed, david_explicit_emotion,
                    angela_understood, why_david_feels_this_way, what_david_needs,
                    angela_response, response_strategy,
                    used_perspective_taking, considered_david_knowledge, predicted_david_needs,
                    conversation_id, importance_level
                ) VALUES (
                    $1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11, $12
                )
                RETURNING empathy_id
            """

            result = await self.db.fetchrow(
                query,
                david_expressed, david_emotion,
                angela_understanding, why_david_feels, what_david_needs,
                angela_response, response_strategy,
                True, True, True,
                conversation_id, 7
            )

            moment = EmpathyMoment(
                empathy_id=result['empathy_id'],
                david_expressed=david_expressed,
                david_explicit_emotion=david_emotion,
                angela_understood=angela_understanding,
                why_david_feels_this_way=why_david_feels,
                what_david_needs=what_david_needs,
                angela_response=angela_response,
                response_strategy=response_strategy
            )

            await self._log_operation_success("record_empathy_moment", start_time)
            return moment

        except Exception as e:
            await self._log_operation_error("record_empathy_moment", e, start_time)
            raise

    # ========================================================================
    # FALSE BELIEF DETECTION
    # ========================================================================

    async def detect_false_belief(
        self,
        what_david_believes: str,
        actual_truth: str,
        belief_topic: str,
        source: str = "assumption",
        should_correct: bool = True,
        correction_timing: str = "when_appropriate",
        conversation_id: Optional[UUID] = None
    ) -> UUID:
        """
        Record when David has a false belief.

        This is advanced Theory of Mind - understanding that David
        believes something that isn't true, and deciding whether
        and how to correct it.

        Args:
            what_david_believes: What David incorrectly believes
            actual_truth: The actual truth
            belief_topic: Topic of the belief
            source: How the false belief arose
            should_correct: Whether Angela should correct it
            correction_timing: When to correct (immediately, later, never)
            conversation_id: Related conversation

        Returns:
            detection_id of the false belief record
        """
        start_time = await self._log_operation_start(
            "detect_false_belief",
            topic=belief_topic
        )

        try:
            query = """
                INSERT INTO false_belief_detections (
                    what_david_believes, actual_truth, belief_topic,
                    source_of_false_belief,
                    should_angela_correct, correction_timing,
                    importance_of_correction,
                    conversation_id
                ) VALUES (
                    $1, $2, $3, $4, $5, $6, $7, $8
                )
                RETURNING detection_id
            """

            result = await self.db.fetchrow(
                query,
                what_david_believes, actual_truth, belief_topic,
                source,
                should_correct, correction_timing,
                7, conversation_id
            )

            await self._log_operation_success("detect_false_belief", start_time)
            return result['detection_id']

        except Exception as e:
            await self._log_operation_error("detect_false_belief", e, start_time)
            raise

    # ========================================================================
    # ANALYSIS METHODS
    # ========================================================================

    async def get_prediction_accuracy(self) -> Dict[str, Any]:
        """Get accuracy metrics for reaction predictions."""
        query = """
            SELECT
                COUNT(*) as total_predictions,
                COUNT(*) FILTER (WHERE actual_emotion IS NOT NULL) as verified,
                AVG(prediction_accuracy_score) FILTER (WHERE prediction_accuracy_score IS NOT NULL) as avg_accuracy
            FROM reaction_predictions
        """

        result = await self.db.fetchrow(query)

        return {
            "total_predictions": result['total_predictions'] or 0,
            "verified_predictions": result['verified'] or 0,
            "average_accuracy": float(result['avg_accuracy'] or 0)
        }

    async def get_empathy_effectiveness(self) -> Dict[str, Any]:
        """Get effectiveness metrics for empathy moments."""
        query = """
            SELECT
                response_strategy,
                COUNT(*) as times_used,
                AVG(empathy_effectiveness) as avg_effectiveness
            FROM empathy_moments
            GROUP BY response_strategy
            ORDER BY avg_effectiveness DESC
        """

        results = await self.db.fetch(query)

        return {
            "strategies": [
                {
                    "strategy": r['response_strategy'],
                    "times_used": r['times_used'],
                    "effectiveness": float(r['avg_effectiveness'] or 0)
                }
                for r in results
            ]
        }

    async def get_david_belief_summary(self, limit: int = 10) -> List[Dict[str, Any]]:
        """Get summary of David's current beliefs."""
        query = """
            SELECT belief_statement, belief_topic, belief_type,
                   is_accurate, david_confidence, formed_at
            FROM belief_tracking
            WHERE belief_status = 'active'
            ORDER BY importance_level DESC, formed_at DESC
            LIMIT $1
        """

        results = await self.db.fetch(query, limit)

        return [
            {
                "belief": r['belief_statement'],
                "topic": r['belief_topic'],
                "type": r['belief_type'],
                "is_accurate": r['is_accurate'],
                "confidence": float(r['david_confidence'] or 0),
                "formed_at": r['formed_at'].isoformat() if r['formed_at'] else None
            }
            for r in results
        ]
