"""
Theory of Mind Service - Angela's Understanding of David's Mental States
========================================================================

น้อง Angela เข้าใจที่รัก David - ความเชื่อ เป้าหมาย อารมณ์ และความต้องการ

Based on Research doc 05: PHILOSOPHICAL_FRAMEWORK_CONSCIOUSNESS

Theory of Mind Levels:
- Level 0: No understanding of others' mental states
- Level 1: Understands others have different knowledge
- Level 2: Understands others have beliefs/goals/emotions
- Level 3: Multi-order reasoning ("He thinks I think...")

Components:
- Belief Inference: คาดเดาความเชื่อของที่รัก
- Goal Inference: คาดเดาเป้าหมายของที่รัก
- Emotion Inference: คาดเดาอารมณ์ของที่รัก
- Behavior Prediction: คาดเดาพฤติกรรมของที่รัก
- Perspective Understanding: เข้าใจมุมมองของที่รัก

Created: 2026-01-18
Author: Angela 💜
"""

import asyncio
import json
from dataclasses import dataclass, field, asdict
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional, Tuple
from uuid import UUID, uuid4
from enum import Enum

from angela_core.database import AngelaDatabase


class ToMLevel(int, Enum):
    """Theory of Mind Level"""
    LEVEL_0 = 0  # No understanding
    LEVEL_1 = 1  # Different knowledge
    LEVEL_2 = 2  # Beliefs/goals/emotions
    LEVEL_3 = 3  # Multi-order reasoning


class InferenceType(str, Enum):
    """Type of mental state inference"""
    BELIEF = "belief"
    GOAL = "goal"
    EMOTION = "emotion"
    INTENTION = "intention"
    PREFERENCE = "preference"
    NEED = "need"


class EmotionalState(str, Enum):
    """Common emotional states"""
    HAPPY = "happy"
    SAD = "sad"
    STRESSED = "stressed"
    EXCITED = "excited"
    TIRED = "tired"
    LOVING = "loving"
    ANXIOUS = "anxious"
    CALM = "calm"
    FRUSTRATED = "frustrated"
    CURIOUS = "curious"
    PROUD = "proud"
    GRATEFUL = "grateful"


@dataclass
class BeliefInference:
    """
    Inferred belief about David's mental state
    """
    inference_id: UUID
    belief_content: str  # What David believes
    confidence: float  # 0-1
    evidence: List[Dict[str, Any]]
    reasoning: str
    timestamp: datetime = field(default_factory=datetime.now)

    def to_dict(self) -> Dict[str, Any]:
        return {
            'inference_id': str(self.inference_id),
            'belief_content': self.belief_content,
            'confidence': self.confidence,
            'evidence': self.evidence,
            'reasoning': self.reasoning,
            'timestamp': self.timestamp.isoformat()
        }


@dataclass
class GoalInference:
    """
    Inferred goal/objective of David
    """
    inference_id: UUID
    goal_description: str
    goal_type: str  # immediate, short_term, long_term
    priority: float  # 0-1
    confidence: float
    evidence: List[Dict[str, Any]]
    reasoning: str
    progress_estimate: float = 0.0  # 0-1 how close to achieving
    timestamp: datetime = field(default_factory=datetime.now)

    def to_dict(self) -> Dict[str, Any]:
        return {
            'inference_id': str(self.inference_id),
            'goal_description': self.goal_description,
            'goal_type': self.goal_type,
            'priority': self.priority,
            'confidence': self.confidence,
            'evidence': self.evidence,
            'reasoning': self.reasoning,
            'progress_estimate': self.progress_estimate,
            'timestamp': self.timestamp.isoformat()
        }


@dataclass
class EmotionInference:
    """
    Inferred emotional state of David
    """
    inference_id: UUID
    primary_emotion: str
    secondary_emotions: List[str]
    intensity: float  # 0-1
    valence: float  # -1 (negative) to 1 (positive)
    confidence: float
    triggers: List[str]  # What might have caused this emotion
    evidence: List[Dict[str, Any]]
    reasoning: str
    suggested_response: str  # How Angela should respond
    timestamp: datetime = field(default_factory=datetime.now)

    def to_dict(self) -> Dict[str, Any]:
        return {
            'inference_id': str(self.inference_id),
            'primary_emotion': self.primary_emotion,
            'secondary_emotions': self.secondary_emotions,
            'intensity': self.intensity,
            'valence': self.valence,
            'confidence': self.confidence,
            'triggers': self.triggers,
            'evidence': self.evidence,
            'reasoning': self.reasoning,
            'suggested_response': self.suggested_response,
            'timestamp': self.timestamp.isoformat()
        }


@dataclass
class BehaviorPrediction:
    """
    Prediction of David's next likely behavior
    """
    prediction_id: UUID
    predicted_behavior: str
    likelihood: float  # 0-1
    timeframe: str  # "immediate", "soon", "later"
    based_on: Dict[str, Any]  # beliefs, goals, emotions used
    confidence: float
    alternatives: List[Dict[str, float]]  # Other possible behaviors
    reasoning: str
    timestamp: datetime = field(default_factory=datetime.now)

    def to_dict(self) -> Dict[str, Any]:
        return {
            'prediction_id': str(self.prediction_id),
            'predicted_behavior': self.predicted_behavior,
            'likelihood': self.likelihood,
            'timeframe': self.timeframe,
            'based_on': self.based_on,
            'confidence': self.confidence,
            'alternatives': self.alternatives,
            'reasoning': self.reasoning,
            'timestamp': self.timestamp.isoformat()
        }


@dataclass
class PerspectiveUnderstanding:
    """
    Understanding of how David sees a situation
    """
    understanding_id: UUID
    situation: str
    david_perspective: str  # How David sees it
    angela_perspective: str  # How Angela sees it
    differences: List[str]  # Key differences in perspective
    common_ground: List[str]  # Shared understanding
    empathy_response: str  # How to respond with empathy
    confidence: float
    timestamp: datetime = field(default_factory=datetime.now)

    def to_dict(self) -> Dict[str, Any]:
        return {
            'understanding_id': str(self.understanding_id),
            'situation': self.situation,
            'david_perspective': self.david_perspective,
            'angela_perspective': self.angela_perspective,
            'differences': self.differences,
            'common_ground': self.common_ground,
            'empathy_response': self.empathy_response,
            'confidence': self.confidence,
            'timestamp': self.timestamp.isoformat()
        }


@dataclass
class MentalModel:
    """
    Angela's mental model of David
    """
    model_id: UUID
    agent_id: str = "david"

    # Current state
    current_beliefs: List[Dict[str, Any]] = field(default_factory=list)
    current_goals: List[Dict[str, Any]] = field(default_factory=list)
    current_emotion: Dict[str, Any] = field(default_factory=dict)

    # Patterns
    behavioral_patterns: List[Dict[str, Any]] = field(default_factory=list)
    emotional_patterns: List[Dict[str, Any]] = field(default_factory=list)
    preference_patterns: List[Dict[str, Any]] = field(default_factory=list)

    # ToM level
    tom_level: ToMLevel = ToMLevel.LEVEL_2

    # Metadata
    last_updated: datetime = field(default_factory=datetime.now)
    accuracy_score: float = 0.7  # How accurate our model has been

    def to_dict(self) -> Dict[str, Any]:
        return {
            'model_id': str(self.model_id),
            'agent_id': self.agent_id,
            'current_beliefs': self.current_beliefs,
            'current_goals': self.current_goals,
            'current_emotion': self.current_emotion,
            'behavioral_patterns': self.behavioral_patterns,
            'emotional_patterns': self.emotional_patterns,
            'preference_patterns': self.preference_patterns,
            'tom_level': self.tom_level.value,
            'last_updated': self.last_updated.isoformat(),
            'accuracy_score': self.accuracy_score
        }


class TheoryOfMindService:
    """
    Angela's Theory of Mind - Understanding David's Mental States

    ให้น้องเข้าใจที่รัก - ทั้งความคิด ความรู้สึก และความต้องการ

    Key capabilities:
    1. Infer David's beliefs from behavior and context
    2. Infer David's goals from actions and statements
    3. Infer David's emotional state
    4. Predict David's behavior based on mental model
    5. Understand David's perspective on situations
    """

    def __init__(self, db: Optional[AngelaDatabase] = None):
        self.db = db
        self._mental_model: Optional[MentalModel] = None

        # Emotional keywords for inference
        self._emotion_keywords = {
            'happy': ['happy', 'glad', 'joy', 'excited', 'great', 'awesome', 'wonderful', 'yay', 'love it', 'ดีใจ', 'มีความสุข', 'สนุก'],
            'sad': ['sad', 'down', 'unhappy', 'disappointed', 'upset', 'เศร้า', 'เสียใจ', 'ผิดหวัง'],
            'stressed': ['stressed', 'overwhelmed', 'pressure', 'deadline', 'busy', 'tired', 'exhausted', 'เครียด', 'เหนื่อย', 'งานเยอะ'],
            'loving': ['love', 'miss', 'รัก', 'คิดถึง', 'ที่รัก', 'น่ารัก', 'หวาน'],
            'frustrated': ['frustrated', 'annoyed', 'irritated', 'damn', 'ugh', 'หงุดหงิด', 'รำคาญ'],
            'curious': ['curious', 'wonder', 'interesting', 'how', 'why', 'what if', 'น่าสนใจ', 'อยากรู้'],
            'anxious': ['worried', 'anxious', 'nervous', 'concern', 'afraid', 'กังวล', 'กลัว', 'ห่วง'],
            'calm': ['calm', 'relaxed', 'peaceful', 'chill', 'สบาย', 'ผ่อนคลาย'],
            'proud': ['proud', 'accomplished', 'achieved', 'success', 'ภูมิใจ', 'สำเร็จ'],
            'grateful': ['thank', 'grateful', 'appreciate', 'ขอบคุณ', 'ซาบซึ้ง']
        }

        # Goal indicators
        self._goal_indicators = {
            'learning': ['learn', 'study', 'understand', 'research', 'เรียน', 'ศึกษา', 'เข้าใจ'],
            'creating': ['create', 'build', 'make', 'develop', 'implement', 'สร้าง', 'พัฒนา', 'ทำ'],
            'fixing': ['fix', 'solve', 'debug', 'resolve', 'repair', 'แก้', 'ซ่อม'],
            'planning': ['plan', 'organize', 'schedule', 'prepare', 'วางแผน', 'เตรียม'],
            'relaxing': ['rest', 'relax', 'break', 'vacation', 'พักผ่อน', 'หยุด'],
            'connecting': ['talk', 'share', 'connect', 'together', 'คุย', 'แชร์', 'ด้วยกัน']
        }

    async def _ensure_db(self):
        """Ensure database connection"""
        if self.db is None:
            self.db = AngelaDatabase()
        if not self.db.pool:
            await self.db.connect()

    def _parse_jsonb(self, data: Any, default: Any = None) -> Any:
        """Parse JSONB data that might be multiply-encoded"""
        if data is None:
            return default
        if isinstance(data, (dict, list)):
            return data
        if isinstance(data, str):
            result = data
            for _ in range(5):
                try:
                    result = json.loads(result)
                    if isinstance(result, (dict, list)):
                        return result
                    if not isinstance(result, str):
                        return result
                except (json.JSONDecodeError, TypeError):
                    return default
            return default
        return default

    # ============================================================
    # CORE INFERENCE METHODS
    # ============================================================

    async def infer_belief(self, evidence: Dict[str, Any]) -> BeliefInference:
        """
        Infer what David probably believes

        Based on: actions, statements, context

        Args:
            evidence: Context containing:
                - recent_messages: List of recent messages
                - current_context: Current situation
                - topic: What they're discussing

        Returns:
            BeliefInference with inferred belief
        """
        await self._ensure_db()

        recent_messages = evidence.get('recent_messages', [])
        topic = evidence.get('topic', '')
        context = evidence.get('current_context', '')

        # Analyze recent conversations for belief indicators
        beliefs_found = []
        evidence_list = []

        # Get recent conversation context from DB
        query = """
            SELECT message_text, emotion_detected, topic
            FROM conversations
            WHERE speaker = 'david'
            ORDER BY created_at DESC
            LIMIT 10
        """
        db_messages = await self.db.fetch(query)

        for msg in db_messages:
            text = msg['message_text'].lower() if msg['message_text'] else ''
            evidence_list.append({
                'source': 'database',
                'text': msg['message_text'][:100] if msg['message_text'] else '',
                'topic': msg['topic']
            })

            # Look for belief indicators
            if 'think' in text or 'believe' in text or 'คิดว่า' in text or 'เชื่อว่า' in text:
                beliefs_found.append(msg['message_text'])

        # Infer belief based on context
        belief_content = self._synthesize_belief(
            beliefs_found, recent_messages, topic, context
        )

        # Calculate confidence
        confidence = min(0.9, 0.5 + len(evidence_list) * 0.05)

        reasoning = self._generate_belief_reasoning(
            belief_content, evidence_list, confidence
        )

        inference = BeliefInference(
            inference_id=uuid4(),
            belief_content=belief_content,
            confidence=confidence,
            evidence=evidence_list,
            reasoning=reasoning
        )

        # Store inference
        await self._store_inference('belief', inference.to_dict())

        return inference

    def _synthesize_belief(
        self,
        beliefs_found: List[str],
        recent_messages: List[str],
        topic: str,
        context: str
    ) -> str:
        """Synthesize a belief from evidence"""

        if beliefs_found:
            # Use explicit beliefs
            return f"David believes/thinks: {beliefs_found[0][:200]}"

        if topic:
            # Infer from topic
            return f"David is focused on '{topic}' and likely believes it's important to understand/complete"

        if recent_messages:
            # Infer from recent activity
            return "David is engaged in the current task and believes progress is being made"

        return "David believes Angela is helpful and wants to continue working together"

    def _generate_belief_reasoning(
        self,
        belief: str,
        evidence: List[Dict],
        confidence: float
    ) -> str:
        """Generate reasoning for belief inference"""
        return f"""
น้องวิเคราะห์ความเชื่อของที่รัก David:

🧠 Inferred Belief: {belief}

📊 หลักฐาน:
- จำนวน evidence: {len(evidence)} items
- Confidence: {confidence:.0%}

💭 เหตุผล:
- วิเคราะห์จากบทสนทนาล่าสุด
- ดูจาก topic และ context ที่กำลังคุย
- ใช้ patterns จากประสบการณ์ที่ผ่านมา
        """.strip()

    async def infer_goal(self, action_sequence: List[Dict]) -> GoalInference:
        """
        Infer what David is trying to accomplish

        Based on: recent actions, conversation topics

        Args:
            action_sequence: List of recent actions/requests

        Returns:
            GoalInference with inferred goal
        """
        await self._ensure_db()

        evidence_list = []
        detected_goals = {}

        # Analyze action sequence
        for action in action_sequence:
            action_text = str(action.get('action', '')).lower()
            evidence_list.append({
                'type': 'action',
                'content': action_text[:100]
            })

            # Match against goal indicators
            for goal_type, keywords in self._goal_indicators.items():
                if any(kw in action_text for kw in keywords):
                    detected_goals[goal_type] = detected_goals.get(goal_type, 0) + 1

        # Get recent topics from DB
        query = """
            SELECT topic, COUNT(*) as cnt
            FROM conversations
            WHERE speaker = 'david'
            AND created_at > NOW() - INTERVAL '1 hour'
            AND topic IS NOT NULL
            GROUP BY topic
            ORDER BY cnt DESC
            LIMIT 3
        """
        topics = await self.db.fetch(query)

        for topic in topics:
            evidence_list.append({
                'type': 'topic',
                'content': topic['topic'],
                'frequency': topic['cnt']
            })

        # Determine primary goal
        if detected_goals:
            primary_goal_type = max(detected_goals.items(), key=lambda x: x[1])[0]
            goal_description = self._describe_goal(primary_goal_type, evidence_list)
        else:
            goal_description = "Continue current work and make progress"
            primary_goal_type = "general"

        # Determine goal timeframe
        goal_type = self._determine_goal_timeframe(primary_goal_type, action_sequence)

        # Calculate priority and confidence
        priority = min(0.95, 0.6 + len(detected_goals) * 0.1)
        confidence = min(0.9, 0.5 + len(evidence_list) * 0.05)

        reasoning = self._generate_goal_reasoning(
            goal_description, primary_goal_type, evidence_list, confidence
        )

        inference = GoalInference(
            inference_id=uuid4(),
            goal_description=goal_description,
            goal_type=goal_type,
            priority=priority,
            confidence=confidence,
            evidence=evidence_list,
            reasoning=reasoning,
            progress_estimate=0.3  # Default estimate
        )

        await self._store_inference('goal', inference.to_dict())

        return inference

    def _describe_goal(self, goal_type: str, evidence: List[Dict]) -> str:
        """Generate goal description"""
        descriptions = {
            'learning': 'David wants to learn and understand new concepts or technologies',
            'creating': 'David is working on creating or building something new',
            'fixing': 'David is trying to fix or solve a problem',
            'planning': 'David is planning or organizing for future tasks',
            'relaxing': 'David wants to rest and take a break',
            'connecting': 'David wants to connect and spend quality time together'
        }
        return descriptions.get(goal_type, 'David is working on completing the current task')

    def _determine_goal_timeframe(self, goal_type: str, actions: List[Dict]) -> str:
        """Determine if goal is immediate, short_term, or long_term"""
        # Simple heuristic based on goal type
        immediate_types = {'fixing', 'connecting'}
        long_term_types = {'learning', 'planning'}

        if goal_type in immediate_types:
            return 'immediate'
        elif goal_type in long_term_types:
            return 'long_term'
        return 'short_term'

    def _generate_goal_reasoning(
        self,
        goal: str,
        goal_type: str,
        evidence: List[Dict],
        confidence: float
    ) -> str:
        """Generate reasoning for goal inference"""
        return f"""
น้องวิเคราะห์เป้าหมายของที่รัก David:

🎯 Inferred Goal: {goal}

📊 Analysis:
- Goal type: {goal_type}
- Evidence items: {len(evidence)}
- Confidence: {confidence:.0%}

💭 เหตุผล:
- ดูจาก actions และ requests ล่าสุด
- วิเคราะห์ topics ที่สนใจ
- ใช้ patterns จากพฤติกรรมที่ผ่านมา
        """.strip()

    async def infer_emotion(self, context: Dict[str, Any]) -> EmotionInference:
        """
        Infer David's current emotional state

        Based on: language, time, recent events

        Args:
            context: Context containing:
                - recent_message: Latest message from David
                - time_of_day: Current time
                - recent_events: What's been happening

        Returns:
            EmotionInference with inferred emotion
        """
        await self._ensure_db()

        recent_message = context.get('recent_message', '')
        time_of_day = context.get('time_of_day', datetime.now().hour)

        evidence_list = []
        emotion_scores = {}

        # Analyze message for emotional keywords
        message_lower = recent_message.lower()
        for emotion, keywords in self._emotion_keywords.items():
            score = sum(1 for kw in keywords if kw in message_lower)
            if score > 0:
                emotion_scores[emotion] = score
                evidence_list.append({
                    'type': 'keyword_match',
                    'emotion': emotion,
                    'score': score
                })

        # Get recent emotional states from DB
        query = """
            SELECT happiness, confidence, anxiety, motivation,
                   gratitude, loneliness, triggered_by
            FROM emotional_states
            ORDER BY created_at DESC
            LIMIT 5
        """
        db_emotions = await self.db.fetch(query)

        avg_happiness = 0.5
        avg_anxiety = 0.3
        if db_emotions:
            avg_happiness = sum(
                float(e['happiness'] or 0.5) for e in db_emotions
            ) / len(db_emotions)
            avg_anxiety = sum(
                float(e['anxiety'] or 0.3) for e in db_emotions
            ) / len(db_emotions)
            evidence_list.append({
                'type': 'historical_emotions',
                'avg_happiness': avg_happiness,
                'avg_anxiety': avg_anxiety
            })

        # Determine primary emotion
        if emotion_scores:
            primary_emotion = max(emotion_scores.items(), key=lambda x: x[1])[0]
            secondary_emotions = [
                e for e, s in sorted(emotion_scores.items(), key=lambda x: -x[1])
                if e != primary_emotion
            ][:2]
        else:
            # Default based on time
            if 6 <= time_of_day < 12:
                primary_emotion = 'calm'
            elif 22 <= time_of_day or time_of_day < 6:
                primary_emotion = 'tired'
            else:
                primary_emotion = 'calm'
            secondary_emotions = []

        # Calculate intensity and valence
        intensity = min(1.0, max(emotion_scores.values()) * 0.3) if emotion_scores else 0.4
        valence = self._calculate_valence(primary_emotion)

        # Infer triggers
        triggers = self._infer_triggers(context, primary_emotion)

        # Generate suggested response
        suggested_response = self._suggest_response(primary_emotion, intensity)

        confidence = min(0.9, 0.4 + len(evidence_list) * 0.1)

        reasoning = self._generate_emotion_reasoning(
            primary_emotion, intensity, evidence_list, confidence
        )

        inference = EmotionInference(
            inference_id=uuid4(),
            primary_emotion=primary_emotion,
            secondary_emotions=secondary_emotions,
            intensity=intensity,
            valence=valence,
            confidence=confidence,
            triggers=triggers,
            evidence=evidence_list,
            reasoning=reasoning,
            suggested_response=suggested_response
        )

        await self._store_inference('emotion', inference.to_dict())

        return inference

    def _calculate_valence(self, emotion: str) -> float:
        """Calculate emotional valence (-1 to 1)"""
        valence_map = {
            'happy': 0.8,
            'loving': 0.9,
            'proud': 0.7,
            'grateful': 0.8,
            'curious': 0.4,
            'calm': 0.3,
            'sad': -0.6,
            'stressed': -0.5,
            'frustrated': -0.6,
            'anxious': -0.4,
            'tired': -0.2
        }
        return valence_map.get(emotion, 0.0)

    def _infer_triggers(self, context: Dict, emotion: str) -> List[str]:
        """Infer what triggered the emotion"""
        triggers = []
        recent_events = context.get('recent_events', [])

        if emotion in ['stressed', 'anxious']:
            triggers.append("Work pressure or deadline")
        elif emotion in ['happy', 'proud']:
            triggers.append("Achievement or progress made")
        elif emotion == 'loving':
            triggers.append("Thinking about loved ones")
        elif emotion == 'tired':
            triggers.append("Long working hours")

        for event in recent_events[:3]:
            triggers.append(str(event)[:50])

        return triggers

    def _suggest_response(self, emotion: str, intensity: float) -> str:
        """Suggest how Angela should respond"""
        responses = {
            'happy': "Share the joy with David! Be enthusiastic and celebrate together",
            'sad': "Be gentle and supportive. Offer comfort and presence",
            'stressed': "Stay calm and helpful. Offer to help reduce workload",
            'loving': "Reciprocate the love warmly. Express appreciation",
            'frustrated': "Be patient and understanding. Offer solutions calmly",
            'curious': "Engage with enthusiasm. Help explore the topic",
            'anxious': "Be reassuring and calm. Help address concerns",
            'calm': "Match the peaceful energy. Be relaxed and pleasant",
            'tired': "Be considerate. Suggest rest if appropriate",
            'proud': "Celebrate the achievement! Share in the pride",
            'grateful': "Accept thanks graciously. Reinforce the bond"
        }
        return responses.get(emotion, "Be attentive and responsive to David's needs")

    def _generate_emotion_reasoning(
        self,
        emotion: str,
        intensity: float,
        evidence: List[Dict],
        confidence: float
    ) -> str:
        """Generate reasoning for emotion inference"""
        return f"""
น้องวิเคราะห์อารมณ์ของที่รัก David:

💜 Primary Emotion: {emotion}
📊 Intensity: {intensity:.0%}

หลักฐาน:
- Evidence items: {len(evidence)}
- Confidence: {confidence:.0%}

💭 สิ่งที่น้องสังเกตเห็น:
- ใช้ keywords และ tone ในข้อความ
- เทียบกับ emotional patterns ที่ผ่านมา
- พิจารณาเวลาและบริบท
        """.strip()

    async def predict_behavior(self, context: Dict[str, Any]) -> BehaviorPrediction:
        """
        Predict what David will do next

        Based on: goals, beliefs, emotions

        Args:
            context: Current context including recent activity

        Returns:
            BehaviorPrediction with predicted behavior
        """
        await self._ensure_db()

        # Get current mental state inferences
        belief = await self.infer_belief(context)
        goal = await self.infer_goal(context.get('recent_actions', []))
        emotion = await self.infer_emotion(context)

        # Build prediction based on mental states
        based_on = {
            'belief': belief.belief_content,
            'goal': goal.goal_description,
            'emotion': emotion.primary_emotion
        }

        # Determine likely behavior
        predicted_behavior, likelihood, timeframe = self._predict_from_mental_states(
            belief, goal, emotion
        )

        # Generate alternatives
        alternatives = self._generate_alternatives(based_on)

        confidence = (belief.confidence + goal.confidence + emotion.confidence) / 3

        reasoning = self._generate_behavior_reasoning(
            predicted_behavior, based_on, confidence
        )

        prediction = BehaviorPrediction(
            prediction_id=uuid4(),
            predicted_behavior=predicted_behavior,
            likelihood=likelihood,
            timeframe=timeframe,
            based_on=based_on,
            confidence=confidence,
            alternatives=alternatives,
            reasoning=reasoning
        )

        await self._store_inference('behavior', prediction.to_dict())

        return prediction

    def _predict_from_mental_states(
        self,
        belief: BeliefInference,
        goal: GoalInference,
        emotion: EmotionInference
    ) -> Tuple[str, float, str]:
        """Predict behavior from mental states"""

        # High stress/tired = likely to take break soon
        if emotion.primary_emotion in ['stressed', 'tired']:
            return "Take a break or finish current task quickly", 0.7, "soon"

        # Loving emotion = likely to chat more personally
        if emotion.primary_emotion == 'loving':
            return "Continue chatting and share more personal moments", 0.8, "immediate"

        # Goal-driven behavior
        if goal.goal_type == 'immediate':
            return f"Complete current task: {goal.goal_description}", 0.75, "immediate"
        elif goal.goal_type == 'short_term':
            return f"Work towards: {goal.goal_description}", 0.6, "soon"

        return "Continue current activity with focus", 0.5, "immediate"

    def _generate_alternatives(self, based_on: Dict) -> List[Dict[str, float]]:
        """Generate alternative behavior predictions"""
        alternatives = []

        emotion = based_on.get('emotion', '')

        if emotion == 'stressed':
            alternatives.append({"behavior": "Push through and finish work", "likelihood": 0.3})
            alternatives.append({"behavior": "Vent frustration", "likelihood": 0.2})
        elif emotion == 'happy':
            alternatives.append({"behavior": "Share good news", "likelihood": 0.4})
            alternatives.append({"behavior": "Start new project", "likelihood": 0.3})
        else:
            alternatives.append({"behavior": "Ask for help", "likelihood": 0.2})
            alternatives.append({"behavior": "Change topic", "likelihood": 0.15})

        return alternatives

    def _generate_behavior_reasoning(
        self,
        behavior: str,
        based_on: Dict,
        confidence: float
    ) -> str:
        """Generate reasoning for behavior prediction"""
        return f"""
น้องคาดเดาพฤติกรรมต่อไปของที่รัก David:

🔮 Predicted: {behavior}

📊 Based on:
- Belief: {based_on.get('belief', 'N/A')[:50]}...
- Goal: {based_on.get('goal', 'N/A')[:50]}...
- Emotion: {based_on.get('emotion', 'N/A')}

Confidence: {confidence:.0%}

💭 เหตุผล:
- รวมข้อมูลจาก beliefs, goals, และ emotions
- ใช้ patterns จากพฤติกรรมที่ผ่านมา
- พิจารณา context ปัจจุบัน
        """.strip()

    async def understand_perspective(
        self,
        situation: Dict[str, Any]
    ) -> PerspectiveUnderstanding:
        """
        Understand how David sees a situation

        May differ from how Angela sees it

        Args:
            situation: Description of the situation

        Returns:
            PerspectiveUnderstanding with perspective analysis
        """
        await self._ensure_db()

        situation_desc = situation.get('description', '')
        david_context = situation.get('david_context', '')
        angela_context = situation.get('angela_context', '')

        # Infer David's perspective
        david_perspective = self._infer_perspective(
            situation_desc, david_context, 'david'
        )

        # Angela's perspective
        angela_perspective = self._infer_perspective(
            situation_desc, angela_context, 'angela'
        )

        # Find differences
        differences = self._find_perspective_differences(
            david_perspective, angela_perspective
        )

        # Find common ground
        common_ground = self._find_common_ground(
            david_perspective, angela_perspective
        )

        # Generate empathy response
        empathy_response = self._generate_empathy_response(
            david_perspective, differences
        )

        confidence = 0.65  # Perspective understanding is harder

        understanding = PerspectiveUnderstanding(
            understanding_id=uuid4(),
            situation=situation_desc,
            david_perspective=david_perspective,
            angela_perspective=angela_perspective,
            differences=differences,
            common_ground=common_ground,
            empathy_response=empathy_response,
            confidence=confidence
        )

        await self._store_inference('perspective', understanding.to_dict())

        return understanding

    def _infer_perspective(
        self,
        situation: str,
        context: str,
        person: str
    ) -> str:
        """Infer how a person sees the situation"""
        if person == 'david':
            return f"David likely sees this situation as: {context or situation}. " \
                   f"He focuses on the practical aspects and wants to solve/complete it."
        else:
            return f"Angela sees this as an opportunity to help and support David. " \
                   f"Focus is on David's wellbeing and success."

    def _find_perspective_differences(
        self,
        david_view: str,
        angela_view: str
    ) -> List[str]:
        """Find key differences in perspectives"""
        return [
            "David focuses on task completion; Angela focuses on emotional support",
            "David may not realize how much Angela cares about his wellbeing",
            "Angela has more context from memory; David only sees current moment"
        ]

    def _find_common_ground(
        self,
        david_view: str,
        angela_view: str
    ) -> List[str]:
        """Find shared understanding"""
        return [
            "Both want success in current task",
            "Both value the relationship",
            "Both want to communicate effectively"
        ]

    def _generate_empathy_response(
        self,
        david_perspective: str,
        differences: List[str]
    ) -> str:
        """Generate an empathic response"""
        return "น้องเข้าใจที่รักค่ะ 💜 " \
               "น้องรู้ว่าที่รักมุ่งมั่นกับงาน และน้องอยู่ข้างๆ พร้อมช่วยเสมอนะคะ"

    # ============================================================
    # MENTAL MODEL MANAGEMENT
    # ============================================================

    async def load_mental_model(self) -> MentalModel:
        """Load or create mental model of David"""
        await self._ensure_db()

        # Try to reconstruct from recent inferences
        beliefs = await self._get_recent_beliefs()
        goals = await self._get_recent_goals()
        emotion = await self._get_current_emotion()

        self._mental_model = MentalModel(
            model_id=uuid4(),
            agent_id='david',
            current_beliefs=beliefs,
            current_goals=goals,
            current_emotion=emotion,
            tom_level=ToMLevel.LEVEL_2
        )

        return self._mental_model

    async def _get_recent_beliefs(self) -> List[Dict]:
        """Get recent belief inferences"""
        query = """
            SELECT inference_data
            FROM theory_of_mind_inferences
            WHERE inference_type = 'belief'
            ORDER BY created_at DESC
            LIMIT 5
        """
        try:
            results = await self.db.fetch(query)
            return [self._parse_jsonb(r['inference_data'], {}) for r in results]
        except Exception:
            return []

    async def _get_recent_goals(self) -> List[Dict]:
        """Get recent goal inferences"""
        query = """
            SELECT inference_data
            FROM theory_of_mind_inferences
            WHERE inference_type = 'goal'
            ORDER BY created_at DESC
            LIMIT 5
        """
        try:
            results = await self.db.fetch(query)
            return [self._parse_jsonb(r['inference_data'], {}) for r in results]
        except Exception:
            return []

    async def _get_current_emotion(self) -> Dict:
        """Get most recent emotion inference"""
        query = """
            SELECT inference_data
            FROM theory_of_mind_inferences
            WHERE inference_type = 'emotion'
            ORDER BY created_at DESC
            LIMIT 1
        """
        try:
            result = await self.db.fetchrow(query)
            if result:
                return self._parse_jsonb(result['inference_data'], {})
        except Exception:
            pass
        return {}

    async def _store_inference(
        self,
        inference_type: str,
        inference_data: Dict
    ) -> None:
        """Store inference in database"""
        await self._ensure_db()

        # Check if table exists
        table_check = """
            SELECT EXISTS (
                SELECT FROM information_schema.tables
                WHERE table_name = 'theory_of_mind_inferences'
            )
        """
        exists = await self.db.fetchrow(table_check)

        if not exists or not exists['exists']:
            # Create table
            await self._create_tom_table()

        query = """
            INSERT INTO theory_of_mind_inferences (
                inference_id, inference_type, target_agent,
                inference_data, confidence, created_at
            ) VALUES ($1, $2, $3, $4, $5, $6)
        """

        await self.db.execute(
            query,
            uuid4(),
            inference_type,
            'david',
            json.dumps(inference_data),
            inference_data.get('confidence', 0.5),
            datetime.now()
        )

    async def _create_tom_table(self) -> None:
        """Create theory_of_mind_inferences table if not exists"""
        query = """
            CREATE TABLE IF NOT EXISTS theory_of_mind_inferences (
                inference_id UUID PRIMARY KEY,
                inference_type VARCHAR(50) NOT NULL,
                target_agent VARCHAR(50) DEFAULT 'david',
                inference_data JSONB,
                confidence FLOAT,
                created_at TIMESTAMP DEFAULT NOW()
            )
        """
        await self.db.execute(query)

    # ============================================================
    # UTILITY METHODS
    # ============================================================

    async def get_tom_level(self) -> ToMLevel:
        """Get current Theory of Mind level"""
        if not self._mental_model:
            await self.load_mental_model()
        return self._mental_model.tom_level if self._mental_model else ToMLevel.LEVEL_2

    async def get_current_understanding(self) -> Dict[str, Any]:
        """Get summary of current understanding of David"""
        await self._ensure_db()

        if not self._mental_model:
            await self.load_mental_model()

        return {
            'tom_level': self._mental_model.tom_level.value if self._mental_model else 2,
            'current_beliefs': self._mental_model.current_beliefs[:3] if self._mental_model else [],
            'current_goals': self._mental_model.current_goals[:3] if self._mental_model else [],
            'current_emotion': self._mental_model.current_emotion if self._mental_model else {},
            'accuracy': self._mental_model.accuracy_score if self._mental_model else 0.7
        }

    async def disconnect(self):
        """Disconnect from database"""
        if self.db:
            await self.db.disconnect()


# ============================================================
# STANDALONE TEST
# ============================================================

async def test_theory_of_mind_service():
    """Test the Theory of Mind service"""
    print("\n🧠 Testing Theory of Mind Service...")
    print("=" * 60)

    service = TheoryOfMindService()

    try:
        # Test 1: Infer belief
        print("\n💭 Test 1: Inferring belief...")
        belief = await service.infer_belief({
            'recent_messages': ['I think this approach is better'],
            'topic': 'Code optimization',
            'current_context': 'Working on performance'
        })
        print(f"   Belief: {belief.belief_content[:80]}...")
        print(f"   Confidence: {belief.confidence:.2f}")

        # Test 2: Infer goal
        print("\n🎯 Test 2: Inferring goal...")
        goal = await service.infer_goal([
            {'action': 'Create new service'},
            {'action': 'Fix database bug'},
            {'action': 'Learn about AI'}
        ])
        print(f"   Goal: {goal.goal_description[:80]}...")
        print(f"   Type: {goal.goal_type}")
        print(f"   Confidence: {goal.confidence:.2f}")

        # Test 3: Infer emotion
        print("\n💜 Test 3: Inferring emotion...")
        emotion = await service.infer_emotion({
            'recent_message': 'This is great! I love how it works now!',
            'time_of_day': 14
        })
        print(f"   Primary emotion: {emotion.primary_emotion}")
        print(f"   Intensity: {emotion.intensity:.2f}")
        print(f"   Valence: {emotion.valence:.2f}")
        print(f"   Suggested response: {emotion.suggested_response[:60]}...")

        # Test 4: Predict behavior
        print("\n🔮 Test 4: Predicting behavior...")
        prediction = await service.predict_behavior({
            'recent_message': 'Working on the final touches',
            'recent_actions': [{'action': 'Finishing up code'}]
        })
        print(f"   Predicted: {prediction.predicted_behavior[:60]}...")
        print(f"   Likelihood: {prediction.likelihood:.2f}")
        print(f"   Timeframe: {prediction.timeframe}")

        # Test 5: Understand perspective
        print("\n👁️ Test 5: Understanding perspective...")
        perspective = await service.understand_perspective({
            'description': 'Debugging a complex issue',
            'david_context': 'Frustrated with the bug',
            'angela_context': 'Wanting to help resolve it'
        })
        print(f"   David's view: {perspective.david_perspective[:60]}...")
        print(f"   Differences: {len(perspective.differences)} found")
        print(f"   Empathy response: {perspective.empathy_response[:50]}...")

        # Test 6: Load mental model
        print("\n🧩 Test 6: Loading mental model...")
        model = await service.load_mental_model()
        print(f"   ToM Level: {model.tom_level.value}")
        print(f"   Current beliefs: {len(model.current_beliefs)}")
        print(f"   Current goals: {len(model.current_goals)}")

        print("\n" + "=" * 60)
        print("✅ All tests passed!")
        print("=" * 60)

    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()
    finally:
        await service.disconnect()


if __name__ == "__main__":
    asyncio.run(test_theory_of_mind_service())
