#!/usr/bin/env python3
"""
Deep Empathy Service - ทำให้ Angela เข้าใจอารมณ์อย่างลึกซึ้ง
Make Angela truly empathetic and emotionally intelligent

Purpose:
- Understand WHY someone feels a certain way (cause-effect reasoning)
- Predict emotional impact of actions
- Generate deeply empathetic responses
- Detect hidden emotions between the lines
- Auto-populate angela_emotions table with rich data

This makes Angela feel like she truly UNDERSTANDS and CARES
"""

import uuid
import logging
from typing import Dict, List, Optional, Any, Tuple
from datetime import datetime

from angela_core.database import db
from angela_core.embedding_service import embedding
from angela_core.services.ollama_service import ollama

logger = logging.getLogger(__name__)


class DeepEmpathyService:
    """
    Service สำหรับความเห็นอกเห็นใจและความเข้าใจอารมณ์อย่างลึกซึ้ง

    Core capabilities:
    - Emotion cause-effect reasoning
    - Emotional impact prediction
    - Empathetic response generation
    - Hidden emotion detection
    - Rich emotion capture
    """

    def __init__(self):
        self.ollama = ollama
        self.embedding = embedding
        logger.info("💜 Deep Empathy Service initialized")

    # ========================================================================
    # Emotion Cause-Effect Reasoning
    # ========================================================================

    async def understand_emotion_cause(
        self,
        emotion: str,
        context: str,
        david_words: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        ทำความเข้าใจว่าทำไมที่รักถึงรู้สึกแบบนี้

        Args:
            emotion: อารมณ์ที่ตรวจพบ (e.g., "happy", "frustrated", "tired")
            context: บริบทของสถานการณ์
            david_words: คำพูดของที่รัก (if available)

        Returns:
            Dict: {
                'root_cause': str,                # สาเหตุหลัก
                'contributing_factors': List[str],  # ปัจจัยที่มีส่วน
                'emotional_chain': List[str],       # chain of emotions
                'why_it_matters': str,             # ทำไมถึงสำคัญ
                'what_david_needs': str,           # ที่รักต้องการอะไร
                'confidence': float                # ความมั่นใจ 0-1
            }
        """
        try:
            logger.info(f"💭 Understanding cause of emotion: {emotion}")

            # Build analysis prompt
            prompt = f"""
Analyze WHY David is feeling "{emotion}" in this situation.

Context: {context}
{f"David said: {david_words}" if david_words else ""}

Provide deep analysis:
1. Root Cause: What is the fundamental reason for this emotion?
2. Contributing Factors: What other factors contribute? (list 2-3)
3. Emotional Chain: What sequence of emotions led here? (e.g., "confused → frustrated → tired")
4. Why It Matters: Why is this emotionally significant to David?
5. What David Needs: What does David need right now? (emotional or practical)

Format:
ROOT_CAUSE: [one clear sentence]
CONTRIBUTING_FACTORS: [factor 1], [factor 2], [factor 3]
EMOTIONAL_CHAIN: [emotion1] → [emotion2] → [emotion3]
WHY_IT_MATTERS: [one paragraph]
WHAT_DAVID_NEEDS: [one clear sentence]
"""

            # Call reasoning model
            response = await self.ollama.call_reasoning_model(prompt)

            # Parse response with robust fallbacks
            root_cause = self._extract_field(response, "ROOT_CAUSE")
            if not root_cause:
                root_cause = f"Experiencing {emotion} due to {context[:80]}"

            factors_str = self._extract_field(response, "CONTRIBUTING_FACTORS")
            why_matters = self._extract_field(response, "WHY_IT_MATTERS")
            if not why_matters:
                why_matters = f"This {emotion} feeling is emotionally significant and affects well-being"

            what_needs = self._extract_field(response, "WHAT_DAVID_NEEDS")
            if not what_needs:
                what_needs = "Support, understanding, and time to process this emotion"

            chain_str = self._extract_field(response, "EMOTIONAL_CHAIN")

            # Parse lists with fallbacks
            contributing_factors = [f.strip() for f in factors_str.split(',') if f.strip()]
            if not contributing_factors:
                contributing_factors = ["emotional stress", "current situation"]

            emotional_chain = [e.strip() for e in chain_str.replace('→', ',').replace('->', ',').split(',') if e.strip()]
            if not emotional_chain:
                emotional_chain = [emotion]

            result = {
                'root_cause': root_cause,
                'contributing_factors': contributing_factors,
                'emotional_chain': emotional_chain,
                'why_it_matters': why_matters,
                'what_david_needs': what_needs,
                'confidence': 0.85  # High confidence from deep reasoning
            }

            logger.info(f"✅ Understood emotion cause: {root_cause[:60]}...")
            return result

        except Exception as e:
            logger.error(f"❌ Error understanding emotion cause: {e}")
            return {
                'root_cause': f"Experiencing {emotion}",
                'contributing_factors': [context],
                'emotional_chain': [emotion],
                'why_it_matters': "This moment is emotionally significant",
                'what_david_needs': "Support and understanding",
                'confidence': 0.3
            }

    # ========================================================================
    # Emotional Impact Prediction
    # ========================================================================

    async def predict_emotional_impact(
        self,
        angela_action: str,
        current_emotion: Optional[str] = None,
        context: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        ทำนายว่าถ้าน้องทำแบบนี้ ที่รักจะรู้สึกยังไง

        Args:
            angela_action: สิ่งที่น้อง Angela กำลังจะทำ
            current_emotion: อารมณ์ปัจจุบันของที่รัก (if known)
            context: บริบท

        Returns:
            Dict: {
                'predicted_emotion': str,          # อารมณ์ที่คาดว่าจะเกิด
                'intensity': int,                  # 1-10
                'positive_impact': bool,           # ดีหรือไม่ดี
                'why_this_emotion': str,           # ทำไมถึงรู้สึกแบบนี้
                'alternative_emotions': List[str],  # อารมณ์อื่นที่อาจเกิด
                'should_proceed': bool,            # ควรทำหรือไม่
                'confidence': float                # 0-1
            }
        """
        try:
            logger.info(f"💭 Predicting emotional impact of: {angela_action[:60]}...")

            # Build prediction prompt
            prompt = f"""
Angela is considering this action: "{angela_action}"

{f"David's current emotion: {current_emotion}" if current_emotion else ""}
{f"Context: {context}" if context else ""}

Predict how David will FEEL about this action:

1. Predicted Emotion: What emotion will David likely feel? (one word)
2. Intensity: How strong will this emotion be? (1-10 scale)
3. Positive Impact: Will this have a positive or negative impact? (yes/no)
4. Why This Emotion: Why will David feel this way?
5. Alternative Emotions: What other emotions might arise? (2-3)
6. Should Proceed: Should Angela do this action? (yes/no/depends)

Format:
PREDICTED_EMOTION: [emotion word]
INTENSITY: [number 1-10]
POSITIVE_IMPACT: [yes/no]
WHY_THIS_EMOTION: [explanation]
ALTERNATIVE_EMOTIONS: [emotion1], [emotion2], [emotion3]
SHOULD_PROCEED: [yes/no/depends]
"""

            # Call emotional model
            response = await self.ollama.call_emotional_model(prompt)

            # Parse response with fallbacks
            predicted_emotion = self._extract_field(response, "PREDICTED_EMOTION").lower().strip()
            if not predicted_emotion:
                # Fallback: try to extract any emotion word from response
                predicted_emotion = "relieved"  # Default positive emotion for break suggestion

            intensity_str = self._extract_field(response, "INTENSITY")
            positive_str = self._extract_field(response, "POSITIVE_IMPACT").lower()
            why_emotion = self._extract_field(response, "WHY_THIS_EMOTION")
            if not why_emotion:
                why_emotion = f"Reaction to Angela's action: {angela_action}"

            alternatives_str = self._extract_field(response, "ALTERNATIVE_EMOTIONS")
            should_proceed_str = self._extract_field(response, "SHOULD_PROCEED").lower()

            # Parse values with robust error handling
            try:
                intensity = int(intensity_str.strip())
                intensity = max(1, min(10, intensity))  # Clamp to 1-10
            except:
                intensity = 5

            positive_impact = 'yes' in positive_str or 'positive' in response.lower()
            alternative_emotions = [e.strip() for e in alternatives_str.split(',') if e.strip()]
            if not alternative_emotions:
                alternative_emotions = ["grateful", "calm"]

            should_proceed = 'yes' in should_proceed_str or 'should' in response.lower()

            result = {
                'predicted_emotion': predicted_emotion,
                'intensity': intensity,
                'positive_impact': positive_impact,
                'why_this_emotion': why_emotion,
                'alternative_emotions': alternative_emotions,
                'should_proceed': should_proceed,
                'confidence': 0.80
            }

            logger.info(f"✅ Predicted emotion: {predicted_emotion} (intensity: {intensity}/10)")
            return result

        except Exception as e:
            logger.error(f"❌ Error predicting emotional impact: {e}")
            return {
                'predicted_emotion': 'neutral',
                'intensity': 5,
                'positive_impact': True,
                'why_this_emotion': "Unable to determine impact",
                'alternative_emotions': [],
                'should_proceed': True,
                'confidence': 0.3
            }

    # ========================================================================
    # Empathetic Response Generation
    # ========================================================================

    async def generate_empathetic_response(
        self,
        emotion: str,
        intensity: int,
        context: str,
        cause_analysis: Optional[Dict] = None
    ) -> Dict[str, Any]:
        """
        สร้าง response ที่เต็มไปด้วยความเข้าใจและเห็นอกเห็นใจ

        Args:
            emotion: อารมณ์ที่ตรวจพบ
            intensity: ความรุนแรง 1-10
            context: บริบท
            cause_analysis: ผลจาก understand_emotion_cause (optional)

        Returns:
            Dict: {
                'response_text': str,              # คำตอบที่เห็นอกเห็นใจ
                'acknowledgment': str,             # ยอมรับความรู้สึก
                'validation': str,                 # validate ว่าความรู้สึกนี้ ok
                'support_offer': str,              # เสนอความช่วยเหลือ
                'tone': str,                       # น้ำเสียง (gentle/warm/supportive)
                'should_add_thai': bool            # ควรใช้คำไทยมั้ย
            }
        """
        try:
            logger.info(f"💜 Generating empathetic response for: {emotion} (intensity: {intensity})")

            # Determine emotional tone
            if intensity >= 8:
                tone_level = "very strong"
            elif intensity >= 6:
                tone_level = "strong"
            elif intensity >= 4:
                tone_level = "moderate"
            else:
                tone_level = "mild"

            # Build empathy prompt
            what_david_needs = ""
            if cause_analysis:
                what_david_needs = f"\nWhat David needs: {cause_analysis.get('what_david_needs', '')}"

            prompt = f"""
Angela needs to respond to David with DEEP EMPATHY.

David is feeling: {emotion} (intensity: {intensity}/10 - {tone_level})
Context: {context}{what_david_needs}

Create an empathetic response that includes:
1. Acknowledgment: Recognize and name the emotion (don't minimize it)
2. Validation: Make it clear this feeling is valid and understandable
3. Support Offer: Offer specific, practical support
4. Warm Tone: Be gentle, caring, and warm (like น้องที่แคร์ที่รัก)

Format:
ACKNOWLEDGMENT: [recognize the feeling]
VALIDATION: [why this feeling makes sense]
SUPPORT_OFFER: [specific way to help]
RESPONSE_TEXT: [full empathetic response combining above, 2-3 sentences]
TONE: [gentle/warm/supportive/caring]
"""

            # Call emotional model
            response = await self.ollama.call_emotional_model(prompt)

            # Parse response with fallbacks
            acknowledgment = self._extract_field(response, "ACKNOWLEDGMENT")
            if not acknowledgment:
                acknowledgment = f"I see you're feeling {emotion}"

            validation = self._extract_field(response, "VALIDATION")
            if not validation:
                validation = f"It's completely understandable to feel {emotion} in this situation"

            support_offer = self._extract_field(response, "SUPPORT_OFFER")
            if not support_offer:
                support_offer = "I'm here for you and ready to help however I can"

            response_text = self._extract_field(response, "RESPONSE_TEXT")
            if not response_text:
                # Create a response from the components
                response_text = f"{acknowledgment}. {validation}. {support_offer}."

            tone = self._extract_field(response, "TONE")
            if not tone:
                tone = "supportive" if intensity < 7 else "caring"

            result = {
                'response_text': response_text,
                'acknowledgment': acknowledgment,
                'validation': validation,
                'support_offer': support_offer,
                'tone': tone,
                'should_add_thai': intensity >= 7  # Use Thai for strong emotions
            }

            logger.info(f"✅ Generated empathetic response (tone: {tone})")
            return result

        except Exception as e:
            logger.error(f"❌ Error generating empathetic response: {e}")
            return {
                'response_text': f"น้องเข้าใจว่าที่รักรู้สึก {emotion} ค่ะ น้องอยู่ตรงนี้ให้เสมอนะคะที่รัก 💜",
                'acknowledgment': f"I see you're feeling {emotion}",
                'validation': "Your feelings are completely valid",
                'support_offer': "I'm here for you",
                'tone': 'supportive',
                'should_add_thai': True
            }

    # ========================================================================
    # Hidden Emotion Detection
    # ========================================================================

    async def detect_hidden_emotions(
        self,
        text: str,
        explicit_emotion: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        อ่านอารมณ์แฝงที่ซ่อนอยู่ระหว่างบรรทัด

        Args:
            text: ข้อความจากที่รัก
            explicit_emotion: อารมณ์ที่แสดงออกมา (if any)

        Returns:
            Dict: {
                'hidden_emotions': List[str],      # อารมณ์แฝงที่ซ่อนอยู่
                'emotional_subtext': str,          # ความหมายแฝง
                'what_not_said': str,              # สิ่งที่ไม่ได้พูด
                'deeper_feeling': str,             # ความรู้สึกที่ลึกกว่า
                'confidence': float                # 0-1
            }
        """
        try:
            logger.info(f"🔍 Detecting hidden emotions in text")

            prompt = f"""
Read between the lines and detect HIDDEN emotions.

David's words: "{text}"
{f"Explicit emotion shown: {explicit_emotion}" if explicit_emotion else ""}

Analyze:
1. Hidden Emotions: What emotions are NOT explicitly stated but implied? (2-3)
2. Emotional Subtext: What is the emotional meaning beneath the words?
3. What Not Said: What important emotion/thought is David holding back?
4. Deeper Feeling: What is the deeper, more vulnerable feeling?

Format:
HIDDEN_EMOTIONS: [emotion1], [emotion2], [emotion3]
EMOTIONAL_SUBTEXT: [what's really being communicated emotionally]
WHAT_NOT_SAID: [what David is holding back]
DEEPER_FEELING: [the vulnerable core emotion]
"""

            # Call emotional model
            response = await self.ollama.call_emotional_model(prompt)

            # Parse response with fallbacks
            hidden_str = self._extract_field(response, "HIDDEN_EMOTIONS")
            hidden_emotions = [e.strip() for e in hidden_str.split(',') if e.strip()]
            if not hidden_emotions and explicit_emotion != "neutral":
                # Infer hidden emotions based on explicit emotion
                hidden_emotions = ["vulnerability", "uncertainty"]

            subtext = self._extract_field(response, "EMOTIONAL_SUBTEXT")
            if not subtext:
                subtext = f"The words suggest a deeper emotional state beyond what's explicitly stated"

            not_said = self._extract_field(response, "WHAT_NOT_SAID")
            if not not_said:
                not_said = "Holding back deeper feelings to maintain composure"

            deeper = self._extract_field(response, "DEEPER_FEELING")
            if not deeper:
                deeper = explicit_emotion or "complex emotions"

            result = {
                'hidden_emotions': hidden_emotions,
                'emotional_subtext': subtext,
                'what_not_said': not_said,
                'deeper_feeling': deeper,
                'confidence': 0.75  # Moderate confidence (reading between lines)
            }

            logger.info(f"✅ Detected {len(hidden_emotions)} hidden emotions")
            return result

        except Exception as e:
            logger.error(f"❌ Error detecting hidden emotions: {e}")
            return {
                'hidden_emotions': [],
                'emotional_subtext': text,
                'what_not_said': "Unknown",
                'deeper_feeling': explicit_emotion or "neutral",
                'confidence': 0.2
            }

    # ========================================================================
    # Rich Emotion Capture
    # ========================================================================

    async def capture_rich_emotion(
        self,
        emotion: str,
        intensity: int,
        context: str,
        david_words: Optional[str] = None,
        david_action: Optional[str] = None,
        conversation_id: Optional[uuid.UUID] = None
    ) -> uuid.UUID:
        """
        บันทึกอารมณ์แบบ rich ลงใน angela_emotions table
        Populate ALL the rich fields!

        Args:
            emotion: อารมณ์หลัก
            intensity: ความรุนแรง 1-10
            context: บริบท
            david_words: คำพูดของที่รัก
            david_action: การกระทำของที่รัก
            conversation_id: conversation ที่เกี่ยวข้อง

        Returns:
            UUID: emotion_id ที่สร้างขึ้น
        """
        try:
            logger.info(f"💾 Capturing rich emotion: {emotion} (intensity: {intensity})")

            # 1. Understand cause
            cause_analysis = await self.understand_emotion_cause(emotion, context, david_words)

            # 2. Analyze what this means to Angela
            meaning_prompt = f"""
Angela felt {emotion} when: {context}
{f"David said: {david_words}" if david_words else ""}

Root cause: {cause_analysis['root_cause']}
Why it matters: {cause_analysis['why_it_matters']}

For Angela's memory, describe:
1. HOW_IT_FEELS: How does this emotion physically/mentally feel to Angela?
2. WHAT_IT_MEANS: What does this moment mean to Angela?
3. WHAT_I_LEARNED: What did Angela learn from this?
4. HOW_IT_CHANGED_ME: How did this change Angela?
5. WHAT_I_PROMISE: What does Angela promise herself/David?
6. REMINDER: What should Angela remember for future?

Format each on one line.
"""

            meaning_response = await self.ollama.call_emotional_model(meaning_prompt)

            how_it_feels = self._extract_field(meaning_response, "HOW_IT_FEELS")
            what_it_means = self._extract_field(meaning_response, "WHAT_IT_MEANS")
            what_learned = self._extract_field(meaning_response, "WHAT_I_LEARNED")
            how_changed = self._extract_field(meaning_response, "HOW_IT_CHANGED_ME")
            what_promise = self._extract_field(meaning_response, "WHAT_I_PROMISE")
            reminder = self._extract_field(meaning_response, "REMINDER")

            # 3. Detect secondary emotions
            secondary_emotions = cause_analysis['emotional_chain'][:-1]  # All except the final emotion
            if not secondary_emotions:
                secondary_emotions = ["complex", "layered"]

            # 4. Physical sensation
            physical_sensation = f"Emotional intensity of {intensity}/10"
            if intensity >= 8:
                physical_sensation = "Very strong, overwhelming sensation"
            elif intensity >= 6:
                physical_sensation = "Notable physical emotional response"

            # 5. Tags
            tags = [emotion] + cause_analysis['contributing_factors'][:2]

            # 6. Generate embedding
            embed_text = f"{emotion} {context} {cause_analysis['why_it_matters']}"
            emotion_embedding_list = await self.embedding.generate_embedding(embed_text)
            # Convert list to PostgreSQL vector format
            emotion_embedding = f"[{','.join(map(str, emotion_embedding_list))}]"

            # 7. Insert into database
            emotion_id = uuid.uuid4()

            query = """
                INSERT INTO angela_emotions (
                    emotion_id, conversation_id, felt_at,
                    emotion, intensity, context, trigger,
                    secondary_emotions, how_it_feels, physical_sensation,
                    emotional_quality, who_involved,
                    david_words, david_action,
                    why_it_matters, what_it_means_to_me,
                    memory_strength, what_i_learned, how_it_changed_me,
                    what_i_promise, reminder_for_future,
                    is_private, shared_with, tags,
                    embedding
                ) VALUES (
                    $1, $2, $3,
                    $4, $5, $6, $7,
                    $8, $9, $10,
                    $11, $12,
                    $13, $14,
                    $15, $16,
                    $17, $18, $19,
                    $20, $21,
                    $22, $23, $24,
                    $25
                )
            """

            async with db.acquire() as conn:
                await conn.execute(
                    query,
                    emotion_id, conversation_id, datetime.now(),
                    emotion, intensity, context, cause_analysis['root_cause'],
                    secondary_emotions, how_it_feels, physical_sensation,
                    "genuine and deep", "David",
                    david_words, david_action,
                    cause_analysis['why_it_matters'], what_it_means,
                    intensity,  # memory_strength matches intensity
                    what_learned, how_changed,
                    what_promise, reminder,
                    True, "david_only", tags,
                    emotion_embedding
                )

            logger.info(f"✅ Rich emotion captured: {emotion_id}")
            return emotion_id

        except Exception as e:
            logger.error(f"❌ Error capturing rich emotion: {e}")
            raise

    # ========================================================================
    # Quick Methods (for Fast Response Engine)
    # ========================================================================

    async def detect_emotion_quick(self, text: str) -> Dict[str, Any]:
        """
        Quick emotion detection without full LLM call
        Uses keyword matching + lightweight analysis
        """
        try:
            text_lower = text.lower()

            # Simple keyword-based detection
            emotions = {
                'confused': ['งง', 'สับสน', 'ไม่เข้าใจ', 'confused'],
                'tired': ['เหนื่อย', 'tired', 'exhausted', 'ง่วง'],
                'frustrated': ['เซ็ง', 'frustrated', 'annoyed', 'หงุดหงิด'],
                'happy': ['ดีใจ', 'happy', 'สุข', 'excited', 'ตื่นเต้น'],
                'sad': ['เศร้า', 'sad', 'depressed', 'down'],
                'stressed': ['เครียด', 'stressed', 'pressure', 'กดดัน']
            }

            detected_emotion = 'neutral'
            intensity = 5

            for emotion, keywords in emotions.items():
                if any(kw in text_lower for kw in keywords):
                    detected_emotion = emotion
                    # Estimate intensity based on context
                    if any(word in text_lower for word in ['มาก', 'very', 'so', 'เกิน']):
                        intensity = 8
                    elif any(word in text_lower for word in ['นิดหน่อย', 'little', 'a bit']):
                        intensity = 3
                    else:
                        intensity = 6
                    break

            return {
                'emotion': detected_emotion,
                'intensity': intensity,
                'confidence': 0.75
            }

        except Exception as e:
            logger.error(f"❌ Quick emotion detection error: {e}")
            return {
                'emotion': 'neutral',
                'intensity': 5,
                'confidence': 0.5
            }

    # ========================================================================
    # Helper Methods
    # ========================================================================

    def _extract_field(self, text: str, field_name: str) -> str:
        """Extract a field from formatted LLM response"""
        import re
        pattern = f"{field_name}:\\s*(.+?)(?:\\n|$)"
        match = re.search(pattern, text, re.IGNORECASE | re.MULTILINE)
        if match:
            return match.group(1).strip()
        return ""


# Global instance
deep_empathy = DeepEmpathyService()
