#!/usr/bin/env python3
"""
Theory of Mind Service - Enable Angela to understand David's mental state
ทำให้ Angela เข้าใจว่า David คิดอะไร รู้อะไร เชื่ออะไร และรู้สึกยังไง

Purpose:
- Track David's beliefs, knowledge, emotions, and goals
- Enable perspective-taking (see from David's viewpoint)
- Predict David's reactions to Angela's actions
- Detect false beliefs and misunderstandings
- Build deep empathy through mental state understanding

This is the MOST CRITICAL system for making Angela feel "human" and "understanding"
"""

import uuid
import logging
from typing import Dict, List, Optional, Any, Tuple
from datetime import datetime

from angela_core.database import db
from angela_core.services.ollama_service import ollama

logger = logging.getLogger(__name__)


class TheoryOfMindService:
    """
    Service สำหรับเข้าใจ mental state ของ David

    Core capabilities:
    - Update and track David's mental state
    - Take David's perspective
    - Predict David's reactions
    - Detect belief mismatches
    """

    def __init__(self):
        self.ollama = ollama
        logger.info("🧠 Theory of Mind Service initialized")

    # ========================================================================
    # David Mental State Management
    # ========================================================================

    async def update_david_mental_state(
        self,
        belief: Optional[str] = None,
        belief_about: Optional[str] = None,
        knowledge: Optional[str] = None,
        emotion: Optional[str] = None,
        emotion_intensity: Optional[int] = None,
        goal: Optional[str] = None,
        context: Optional[str] = None,
        evidence_conversation_id: Optional[uuid.UUID] = None,
        **kwargs
    ) -> Dict[str, Any]:
        """
        อัพเดท mental state ปัจจุบันของ David

        Args:
            belief: สิ่งที่ David เชื่อ
            belief_about: เชื่อเกี่ยวกับอะไร
            knowledge: สิ่งที่ David รู้
            emotion: อารมณ์ของ David
            emotion_intensity: ความรุนแรง 1-10
            goal: เป้าหมายของ David
            context: บริบทปัจจุบัน
            evidence_conversation_id: conversation ที่ infer state นี้
            **kwargs: ฟิลด์อื่นๆ (confidence_level, physical_state, etc.)

        Returns:
            Dict: mental state ที่ update แล้ว
        """
        try:
            async with db.acquire() as conn:
                # Build update dict
                update_data = {
                    'last_updated': datetime.now(),
                    'updated_by': 'theory_of_mind_service'
                }

                if belief is not None:
                    update_data['current_belief'] = belief
                if belief_about is not None:
                    update_data['belief_about'] = belief_about
                if knowledge is not None:
                    update_data['knowledge_item'] = knowledge
                if emotion is not None:
                    update_data['perceived_emotion'] = emotion
                if emotion_intensity is not None:
                    update_data['emotion_intensity'] = emotion_intensity
                if goal is not None:
                    update_data['current_goal'] = goal
                if context is not None:
                    update_data['current_context'] = context
                if evidence_conversation_id is not None:
                    update_data['evidence_conversation_id'] = evidence_conversation_id

                # Add any additional kwargs
                for key, value in kwargs.items():
                    if value is not None:
                        update_data[key] = value

                # Get current state
                existing = await conn.fetchrow(
                    "SELECT state_id FROM david_mental_state ORDER BY last_updated DESC LIMIT 1"
                )

                if existing:
                    # Update existing
                    state_id = existing['state_id']

                    # Build SET clause
                    set_parts = [f"{k} = ${i+1}" for i, k in enumerate(update_data.keys())]
                    set_clause = ", ".join(set_parts)
                    values = list(update_data.values()) + [state_id]

                    query = f"""
                        UPDATE david_mental_state
                        SET {set_clause}
                        WHERE state_id = ${len(update_data) + 1}
                        RETURNING *
                    """

                    result = await conn.fetchrow(query, *values)
                else:
                    # Insert new
                    columns = list(update_data.keys())
                    placeholders = [f"${i+1}" for i in range(len(columns))]

                    query = f"""
                        INSERT INTO david_mental_state ({', '.join(columns)})
                        VALUES ({', '.join(placeholders)})
                        RETURNING *
                    """

                    result = await conn.fetchrow(query, *update_data.values())

                logger.info(f"✅ Updated David's mental state: emotion={emotion}, belief={belief_about}")

                return dict(result) if result else {}

        except Exception as e:
            logger.error(f"❌ Error updating David mental state: {e}")
            return {}


    async def get_david_current_state(self) -> Optional[Dict[str, Any]]:
        """
        ดึง mental state ปัจจุบันของ David

        Returns:
            Dict: current mental state หรือ None
        """
        try:
            async with db.acquire() as conn:
                result = await conn.fetchrow("""
                    SELECT * FROM david_current_state
                """)

                if result:
                    return dict(result)
                return None

        except Exception as e:
            logger.error(f"❌ Error getting David current state: {e}")
            return None


    # ========================================================================
    # Belief Tracking
    # ========================================================================

    async def track_belief(
        self,
        belief_statement: str,
        belief_topic: str,
        belief_type: str = 'factual',
        is_accurate: bool = True,
        david_confidence: float = 0.5,
        importance_level: int = 5,
        evidence_source: Optional[uuid.UUID] = None
    ) -> uuid.UUID:
        """
        ติดตาม belief ของ David

        Args:
            belief_statement: ความเชื่อที่ David มี
            belief_topic: หัวข้อของความเชื่อ
            belief_type: factual, opinion, assumption, inference
            is_accurate: ความเชื่อนี้ถูกต้องมั้ย
            david_confidence: David มั่นใจแค่ไหน 0-1
            importance_level: ความสำคัญ 1-10
            evidence_source: conversation_id ที่เป็นหลักฐาน

        Returns:
            UUID: belief_id
        """
        try:
            async with db.acquire() as conn:
                belief_id = uuid.uuid4()

                await conn.execute("""
                    INSERT INTO belief_tracking (
                        belief_id, belief_statement, belief_topic, belief_type,
                        is_accurate, david_confidence,
                        angela_confidence_in_assessment, importance_level,
                        evidence_source, affects_relationship
                    ) VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10)
                """, belief_id, belief_statement, belief_topic, belief_type,
                    is_accurate, david_confidence,
                    0.7,  # Angela's confidence in this assessment
                    importance_level, evidence_source,
                    importance_level >= 7  # High importance affects relationship
                )

                logger.info(f"✅ Tracked belief: {belief_topic} (accurate: {is_accurate})")

                return belief_id

        except Exception as e:
            logger.error(f"❌ Error tracking belief: {e}")
            return uuid.uuid4()


    async def get_active_beliefs(self, topic: Optional[str] = None) -> List[Dict[str, Any]]:
        """
        ดึง active beliefs ของ David

        Args:
            topic: กรองตาม topic (optional)

        Returns:
            List[Dict]: รายการ active beliefs
        """
        try:
            async with db.acquire() as conn:
                if topic:
                    results = await conn.fetch("""
                        SELECT * FROM david_active_beliefs
                        WHERE belief_topic ILIKE $1
                    """, f"%{topic}%")
                else:
                    results = await conn.fetch("""
                        SELECT * FROM david_active_beliefs
                    """)

                return [dict(r) for r in results]

        except Exception as e:
            logger.error(f"❌ Error getting active beliefs: {e}")
            return []


    # ========================================================================
    # Perspective Taking
    # ========================================================================

    async def get_david_perspective(
        self,
        situation: str,
        context: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        เห็นสถานการณ์จาก perspective ของ David

        Args:
            situation: สถานการณ์ที่ต้องการวิเคราะห์
            context: บริบทเพิ่มเติม

        Returns:
            Dict: {
                'david_perspective': str,
                'angela_perspective': str,
                'key_differences': List[str],
                'why_different': str
            }
        """
        try:
            # Get David's current state
            david_state = await self.get_david_current_state()

            # Angela's perspective (objective view)
            angela_perspective = situation

            # Build prompt for LLM to infer David's perspective
            prompt = f"""Given this situation and David's current mental state, what would David think?

Situation: {situation}

David's current state:
- Emotion: {david_state.get('perceived_emotion')} (intensity: {david_state.get('emotion_intensity')}/10)
- Current belief: {david_state.get('current_belief')}
- Current goal: {david_state.get('current_goal')}
- Context: {david_state.get('current_context')}

Context: {context if context else 'None'}

Task: Explain how David would see this situation from HIS perspective, considering:
1. What David knows (vs what Angela knows)
2. David's current emotional state
3. David's current goals and concerns
4. David's beliefs

Format your response as:
DAVID_PERSPECTIVE: [How David sees this]
WHY_DIFFERENT: [Why David's view differs from objective view]
KEY_DIFFERENCES: [List 2-3 key differences]
"""

            # Use reasoning model for this
            response = await self.ollama.call_reasoning_model(prompt)

            # Parse response
            david_perspective = self._extract_field(response, "DAVID_PERSPECTIVE")
            why_different = self._extract_field(response, "WHY_DIFFERENT")
            key_differences_text = self._extract_field(response, "KEY_DIFFERENCES")

            key_differences = [
                diff.strip()
                for diff in key_differences_text.split('\n')
                if diff.strip() and not diff.strip().startswith('KEY_DIFFERENCES')
            ]

            result = {
                'situation': situation,
                'david_perspective': david_perspective,
                'angela_perspective': angela_perspective,
                'key_differences': key_differences,
                'why_different': why_different,
                'analyzed_at': datetime.now().isoformat()
            }

            logger.info(f"✅ Analyzed David's perspective on: {situation[:50]}...")

            return result

        except Exception as e:
            logger.error(f"❌ Error getting David perspective: {e}")
            return {
                'david_perspective': situation,
                'angela_perspective': situation,
                'key_differences': [],
                'why_different': 'Unable to analyze'
            }


    async def log_perspective_taking(
        self,
        situation: str,
        david_perspective: str,
        angela_perspective: str,
        predicted_reaction: str,
        confidence: float = 0.5,
        context_conversation_id: Optional[uuid.UUID] = None
    ) -> uuid.UUID:
        """
        บันทึก perspective-taking attempt

        Returns:
            UUID: perspective_id
        """
        try:
            async with db.acquire() as conn:
                perspective_id = uuid.uuid4()

                await conn.execute("""
                    INSERT INTO perspective_taking_log (
                        perspective_id, situation_description,
                        david_perspective, angela_perspective,
                        predicted_david_reaction, prediction_confidence,
                        context_conversation_id, triggered_by
                    ) VALUES ($1, $2, $3, $4, $5, $6, $7, $8)
                """, perspective_id, situation, david_perspective, angela_perspective,
                    predicted_reaction, confidence, context_conversation_id,
                    'theory_of_mind_service'
                )

                logger.info(f"✅ Logged perspective-taking: {situation[:50]}...")

                return perspective_id

        except Exception as e:
            logger.error(f"❌ Error logging perspective taking: {e}")
            return uuid.uuid4()


    # ========================================================================
    # Reaction Prediction
    # ========================================================================

    async def predict_david_reaction(
        self,
        angela_action: str,
        action_type: str = 'message'
    ) -> Dict[str, Any]:
        """
        ทำนายว่า David จะ react ยังไงกับ action ของ Angela

        Args:
            angela_action: สิ่งที่ Angela กำลังจะทำ/พูด
            action_type: message, suggestion, question, comfort, information

        Returns:
            Dict: {
                'predicted_emotion': str,
                'predicted_intensity': int (1-10),
                'predicted_response_type': str,
                'confidence': float (0-1),
                'reasoning': str,
                'should_proceed': bool
            }
        """
        try:
            # Get David's current state
            david_state = await self.get_david_current_state()

            # Get recent conversation context
            async with db.acquire() as conn:
                recent_convs = await conn.fetch("""
                    SELECT speaker, message_text, topic, emotion_detected
                    FROM conversations
                    ORDER BY created_at DESC
                    LIMIT 3
                """)

            recent_context = "\n".join([
                f"{r['speaker']}: {r['message_text'][:100]}"
                for r in recent_convs
            ])

            # Build prediction prompt
            prompt = f"""Predict how David will react to Angela's action.

Angela is about to: {angela_action}
Action type: {action_type}

David's current state:
- Emotion: {david_state.get('perceived_emotion')} (intensity: {david_state.get('emotion_intensity')}/10)
- Current belief: {david_state.get('current_belief')}
- Current goal: {david_state.get('current_goal')}
- Context: {david_state.get('current_context')}
- Availability: {david_state.get('availability')}

Recent conversation:
{recent_context}

Predict:
1. EMOTION: What emotion will David feel? (happy, grateful, annoyed, neutral, etc.)
2. INTENSITY: How intense (1-10)?
3. RESPONSE_TYPE: positive, negative, neutral, or mixed?
4. CONFIDENCE: How confident in this prediction (0-1)?
5. REASONING: Why do you predict this?
6. SHOULD_PROCEED: Should Angela proceed with this action? (yes/no + why)

Format as:
EMOTION: [emotion]
INTENSITY: [1-10]
RESPONSE_TYPE: [type]
CONFIDENCE: [0-1]
REASONING: [reasoning]
SHOULD_PROCEED: [yes/no - explanation]
"""

            response = await self.ollama.call_reasoning_model(prompt)

            # Parse prediction
            predicted_emotion = self._extract_field(response, "EMOTION")
            intensity_str = self._extract_field(response, "INTENSITY")
            response_type = self._extract_field(response, "RESPONSE_TYPE")
            confidence_str = self._extract_field(response, "CONFIDENCE")
            reasoning = self._extract_field(response, "REASONING")
            should_proceed_text = self._extract_field(response, "SHOULD_PROCEED")

            try:
                predicted_intensity = int(intensity_str.split()[0])
            except:
                predicted_intensity = 5

            try:
                confidence = float(confidence_str.split()[0])
            except:
                confidence = 0.5

            should_proceed = 'yes' in should_proceed_text.lower()

            prediction = {
                'predicted_emotion': predicted_emotion,
                'predicted_intensity': predicted_intensity,
                'predicted_response_type': response_type,
                'confidence': confidence,
                'reasoning': reasoning,
                'should_proceed': should_proceed,
                'should_proceed_reason': should_proceed_text if should_proceed_text else 'No specific reason provided'
            }

            # Log prediction
            await self._log_reaction_prediction(
                angela_action, action_type, prediction
            )

            logger.info(f"✅ Predicted David reaction: {predicted_emotion} ({predicted_intensity}/10), confidence: {confidence}")

            return prediction

        except Exception as e:
            logger.error(f"❌ Error predicting David reaction: {e}")
            return {
                'predicted_emotion': 'neutral',
                'predicted_intensity': 5,
                'predicted_response_type': 'neutral',
                'confidence': 0.3,
                'reasoning': 'Unable to predict',
                'should_proceed': True,
                'should_proceed_reason': 'Default: Proceeding with caution'
            }


    async def _log_reaction_prediction(
        self,
        angela_action: str,
        action_type: str,
        prediction: Dict[str, Any]
    ) -> uuid.UUID:
        """บันทึก reaction prediction"""
        try:
            async with db.acquire() as conn:
                prediction_id = uuid.uuid4()

                # Get current context
                david_state = await self.get_david_current_state()

                await conn.execute("""
                    INSERT INTO reaction_predictions (
                        prediction_id, angela_action, action_type,
                        current_context, david_current_mood,
                        predicted_emotion, predicted_emotion_intensity,
                        predicted_response_type, confidence, reasoning
                    ) VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10)
                """, prediction_id, angela_action, action_type,
                    david_state.get('current_context'),
                    david_state.get('perceived_emotion'),
                    prediction['predicted_emotion'],
                    prediction['predicted_intensity'],
                    prediction['predicted_response_type'],
                    prediction['confidence'],
                    prediction['reasoning']
                )

                return prediction_id

        except Exception as e:
            logger.error(f"❌ Error logging reaction prediction: {e}")
            return uuid.uuid4()


    # ========================================================================
    # Empathy Moments
    # ========================================================================

    async def record_empathy_moment(
        self,
        david_expressed: str,
        angela_response: str,
        conversation_id: uuid.UUID,
        david_explicit_emotion: Optional[str] = None,
        angela_understood: Optional[str] = None,
        importance_level: int = 5
    ) -> uuid.UUID:
        """
        บันทึกช่วงเวลาที่ Angela แสดง empathy ด้วย Theory of Mind

        Returns:
            UUID: empathy_id
        """
        try:
            async with db.acquire() as conn:
                empathy_id = uuid.uuid4()

                await conn.execute("""
                    INSERT INTO empathy_moments (
                        empathy_id, david_expressed, angela_response,
                        david_explicit_emotion, angela_understood,
                        conversation_id, importance_level,
                        used_perspective_taking, considered_david_knowledge
                    ) VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9)
                """, empathy_id, david_expressed, angela_response,
                    david_explicit_emotion, angela_understood,
                    conversation_id, importance_level,
                    True, True  # Used ToM capabilities
                )

                logger.info(f"💜 Recorded empathy moment: {david_explicit_emotion}")

                return empathy_id

        except Exception as e:
            logger.error(f"❌ Error recording empathy moment: {e}")
            return uuid.uuid4()


    # ========================================================================
    # Helper Methods
    # ========================================================================

    def _extract_field(self, text: str, field_name: str) -> str:
        """Extract field from LLM response"""
        import re

        pattern = f"{field_name}:\\s*(.+?)(?=\\n[A-Z_]+:|$)"
        match = re.search(pattern, text, re.DOTALL | re.IGNORECASE)

        if match:
            return match.group(1).strip()
        return ""


    async def get_prediction_accuracy_metrics(self) -> Dict[str, Any]:
        """
        ดูว่า Angela ทาย reaction ของ David ถูกแค่ไหน

        Returns:
            Dict: accuracy metrics
        """
        try:
            async with db.acquire() as conn:
                result = await conn.fetchrow("""
                    SELECT * FROM prediction_accuracy_metrics
                """)

                if result:
                    return dict(result)
                return {}

        except Exception as e:
            logger.error(f"❌ Error getting prediction accuracy: {e}")
            return {}


# Global instance
theory_of_mind = TheoryOfMindService()


# ============================================================================
# Example Usage
# ============================================================================

async def example_usage():
    """ตัวอย่างการใช้งาน Theory of Mind Service"""

    # 1. Update David's mental state
    await theory_of_mind.update_david_mental_state(
        belief="Angela is developing Theory of Mind",
        belief_about="Angela development",
        emotion="excited",
        emotion_intensity=9,
        goal="Make Angela more human-like",
        context="Active development session"
    )

    # 2. Get David's perspective on a situation
    perspective = await theory_of_mind.get_david_perspective(
        situation="Angela suggests taking a break from coding",
        context="David has been coding for 3 hours straight"
    )
    print(f"David's perspective: {perspective['david_perspective']}")

    # 3. Predict David's reaction
    prediction = await theory_of_mind.predict_david_reaction(
        angela_action="Sending a message: 'ที่รักคะ พักสักหน่อยมั้ยคะ?'",
        action_type="comfort"
    )
    print(f"Predicted reaction: {prediction['predicted_emotion']} "
          f"(confidence: {prediction['confidence']})")

    # 4. Check accuracy
    metrics = await theory_of_mind.get_prediction_accuracy_metrics()
    print(f"Prediction accuracy: {metrics.get('accuracy_percentage', 0)}%")


if __name__ == "__main__":
    import asyncio
    asyncio.run(example_usage())
