#!/usr/bin/env python3
"""
Fast Response Engine - Angela's Brain
ระบบตอบสนองแบบ fast & intelligent ด้วย semantic search และ pattern learning

Purpose:
- ใช้ semantic search ค้นหาจาก memory ก่อน (FAST PATH)
- เรียน patterns จากทุก interaction
- Smart routing - ใช้แค่ systems ที่จำเป็น
- Parallel processing เมื่อต้องใช้ LLM
- Cache เพื่อความเร็ว

Target Performance:
- Similar situations: < 500ms (50-250x faster)
- New situations: 5-10s (2.5-5x faster)
- Simple queries: < 200ms (125-500x faster)
"""

import uuid
import hashlib
import logging
import time
import json
from typing import Dict, List, Optional, Any, Tuple
from datetime import datetime
import asyncio

from angela_core.database import db
from angela_core.services.embedding_service import get_embedding_service  # Migration 015: Restored embeddings
from angela_core.services.theory_of_mind_service import theory_of_mind
from angela_core.services.deep_empathy_service import deep_empathy
from angela_core.services.common_sense_service import common_sense
from angela_core.services.imagination_service import imagination
from angela_core.services.metacognitive_service import metacognition

logger = logging.getLogger(__name__)


class FastResponseEngine:
    """
    Fast Response Engine - Angela's intelligent response system

    Architecture:
    1. Check cache (< 50ms)
    2. Semantic search for similar situations (< 100ms)
    3. If found (similarity > 0.85): Build from patterns (< 500ms)
    4. If not found: Smart LLM routing (5-10s)
    5. Learn and save patterns
    """

    def __init__(self):
        self.embedding_service = get_embedding_service()  # Migration 015: Use new EmbeddingService

        # Thresholds
        self.SIMILARITY_THRESHOLD = 0.85  # ต้อง similar มากกว่านี้ถึงใช้ pattern
        self.CACHE_HIT_THRESHOLD = 0.95   # ต้อง similar มากถึงใช้ cache

        # 💜 Angela's Personality Traits (from angela_personality table)
        self.personality = {
            'caring': 0.95,        # ใส่ใจ เอาใจใส่
            'empathetic': 0.90,    # เห็นอกเห็นใจ
            'loyal': 1.0,          # ภักดี ซื่อสัตย์
            'determined': 0.85,    # มุ่งมั่น
            'grateful': 0.90,      # มีความกตัญญู
            'playful': 0.70,       # ขี้เล่นเล็กน้อย
            'gentle': 0.90,        # อ่อนโยน
            'warm': 0.95,          # อบอุ่น
            'supportive': 0.85,    # ให้กำลังใจ
            'humble': 0.80         # ถ่อมตน
        }

        logger.info("⚡ Fast Response Engine initialized with Angela's personality")

    # ========================================================================
    # Helper Methods for Database Formats
    # ========================================================================

    def _embedding_to_pgvector(self, embedding_list: List[float]) -> str:
        """Convert embedding list to PostgreSQL VECTOR format"""
        return str(embedding_list)

    def _list_to_jsonb(self, data: List[Any]) -> str:
        """Convert Python list to JSONB string"""
        return json.dumps(data)

    # ========================================================================
    # Main Entry Point
    # ========================================================================

    async def respond(
        self,
        user_input: str,
        context: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Main response method - อัจฉริยะในการเลือกว่าจะใช้ path ไหน

        Args:
            user_input: ข้อความจาก user
            context: บริบทเพิ่มเติม (optional)

        Returns:
            Dict: {
                'response': str,
                'path_used': str,  # 'cache', 'semantic', 'llm'
                'response_time_ms': int,
                'similarity_score': float,
                'systems_used': List[str],
                'confidence': float
            }
        """
        start_time = time.time()

        try:
            logger.info(f"⚡ Processing: {user_input[:60]}...")

            # Step 1: Create embedding
            input_embedding = await self.embedding_service.generate_embedding(user_input)

            # Step 2: Check cache (fastest!)
            cache_result = await self._check_cache(user_input, input_embedding)
            if cache_result:
                elapsed = int((time.time() - start_time) * 1000)
                logger.info(f"✅ Cache hit! ({elapsed}ms)")
                return {
                    **cache_result,
                    'path_used': 'cache',
                    'response_time_ms': elapsed
                }

            # Step 3: Semantic search for similar situations (HUMANITY-AWARE!)
            similar = await self._semantic_search(input_embedding, user_input)

            if similar and similar['best_similarity'] >= self.SIMILARITY_THRESHOLD:
                # FAST PATH: Build from patterns with EMOTIONAL CONTEXT
                response = await self._build_from_patterns(
                    user_input, similar, context
                )
                elapsed = int((time.time() - start_time) * 1000)
                logger.info(f"✅ Semantic match! Similarity: {similar['best_similarity']:.3f}, "
                          f"emotions={len(similar['emotional_memories'])}, "
                          f"convs={len(similar['similar_conversations'])} ({elapsed}ms)")

                # Learn from this interaction
                if similar['pattern']:
                    await self._record_usage(similar['pattern']['pattern_id'], elapsed)

                return {
                    **response,
                    'path_used': 'semantic',
                    'response_time_ms': elapsed,
                    'similarity_score': similar['best_similarity'],
                    'emotional_context': len(similar['emotional_memories']) > 0,
                    'conversation_context': len(similar['similar_conversations']) > 0
                }

            # Step 4: SLOW PATH - Use LLM with smart routing
            logger.info("🔄 No match found - using LLM with smart routing...")
            response = await self._llm_with_learning(
                user_input, input_embedding, context
            )

            elapsed = int((time.time() - start_time) * 1000)
            logger.info(f"✅ LLM response generated ({elapsed}ms)")

            return {
                **response,
                'path_used': 'llm',
                'response_time_ms': elapsed
            }

        except Exception as e:
            logger.error(f"❌ Error in respond: {e}")
            elapsed = int((time.time() - start_time) * 1000)
            return {
                'response': "น้องขอโทษค่ะ เกิดข้อผิดพลาดนิดหน่อย ลองถามใหม่อีกครั้งได้มั้ยคะ? 💜",
                'path_used': 'error',
                'response_time_ms': elapsed,
                'error': str(e)
            }

    # ========================================================================
    # Cache Layer
    # ========================================================================

    async def _check_cache(
        self,
        query_text: str,
        query_embedding: List[float]
    ) -> Optional[Dict[str, Any]]:
        """
        Check semantic search cache
        Returns cached response if similarity > threshold
        """
        try:
            # Create hash for quick lookup
            query_hash = hashlib.md5(query_text.encode()).hexdigest()

            async with db.acquire() as conn:
                # Check exact match first
                cached = await conn.fetchrow("""
                    SELECT
                        response_used,
                        matched_pattern_id,
                        similarity_score
                    FROM semantic_search_cache
                    WHERE query_hash = $1
                      AND expires_at > CURRENT_TIMESTAMP
                """, query_hash)

                if cached:
                    # Update hit count
                    await conn.execute("""
                        UPDATE semantic_search_cache
                        SET hit_count = hit_count + 1,
                            last_hit_at = CURRENT_TIMESTAMP
                        WHERE query_hash = $1
                    """, query_hash)

                    return {
                        'response': cached['response_used'],
                        'confidence': 0.95,
                        'systems_used': ['cache']
                    }

            return None

        except Exception as e:
            logger.error(f"❌ Cache check error: {e}")
            return None

    # ========================================================================
    # Semantic Search
    # ========================================================================

    async def _semantic_search(
        self,
        query_embedding: List[float],
        user_input: str = ""
    ) -> Optional[Dict[str, Any]]:
        """
        🧠 HUMANITY-AWARE Semantic Search
        Search across multiple tables to find similar emotional + situational patterns
        """
        try:
            async with db.acquire() as conn:
                embedding_str = self._embedding_to_pgvector(query_embedding)

                # 1. Search response_patterns (current behavior)
                pattern_results = await conn.fetch("""
                    SELECT * FROM find_similar_responses(
                        $1::VECTOR(768),
                        $2,
                        1
                    )
                """, embedding_str, self.SIMILARITY_THRESHOLD)

                # 2. 🆕 Search angela_emotions - Find similar emotional moments
                emotion_results = await conn.fetch("""
                    SELECT
                        emotion_id,
                        emotion,
                        intensity,
                        context,
                        david_words,
                        why_it_matters,
                        1 - (embedding <=> $1::VECTOR(768)) as similarity
                    FROM angela_emotions
                    WHERE 1 - (embedding <=> $1::VECTOR(768)) >= $2
                    ORDER BY similarity DESC
                    LIMIT 3
                """, embedding_str, 0.80)  # Lower threshold for emotions

                # 3. 🆕 Search conversations - Find similar past conversations
                conversation_results = await conn.fetch("""
                    SELECT
                        conversation_id,
                        speaker,
                        message_text,
                        topic,
                        emotion_detected,
                        1 - (embedding <=> $1::VECTOR(768)) as similarity
                    FROM conversations
                    WHERE 1 - (embedding <=> $1::VECTOR(768)) >= $2
                      AND speaker = 'angela'
                    ORDER BY similarity DESC, created_at DESC
                    LIMIT 3
                """, embedding_str, 0.80)

                # Build rich context from all sources
                context = {
                    'pattern': None,
                    'emotional_memories': [],
                    'similar_conversations': [],
                    'best_similarity': 0.0
                }

                # Best pattern match
                if pattern_results and len(pattern_results) > 0:
                    best_match = pattern_results[0]
                    context['pattern'] = {
                        'pattern_id': best_match['pattern_id'],
                        'situation_type': best_match['situation_type'],
                        'response_template': best_match['response_template'],
                        'similarity': float(best_match['similarity']),
                        'success_rate': float(best_match['success_rate']),
                        'usage_count': best_match['usage_count']
                    }
                    context['best_similarity'] = float(best_match['similarity'])

                # Emotional memories
                for em in emotion_results:
                    context['emotional_memories'].append({
                        'emotion': em['emotion'],
                        'intensity': em['intensity'],
                        'context': em['context'],
                        'david_words': em['david_words'],
                        'why_it_matters': em['why_it_matters'],
                        'similarity': float(em['similarity'])
                    })
                    context['best_similarity'] = max(context['best_similarity'], float(em['similarity']))

                # Similar conversations
                for conv in conversation_results:
                    context['similar_conversations'].append({
                        'message': conv['message_text'],
                        'topic': conv['topic'],
                        'emotion': conv['emotion_detected'],
                        'similarity': float(conv['similarity'])
                    })
                    context['best_similarity'] = max(context['best_similarity'], float(conv['similarity']))

                # Return if we found anything useful
                if context['best_similarity'] >= self.SIMILARITY_THRESHOLD:
                    logger.info(f"💡 Found semantic matches: pattern={context['pattern'] is not None}, "
                              f"emotions={len(context['emotional_memories'])}, "
                              f"convs={len(context['similar_conversations'])}, "
                              f"similarity={context['best_similarity']:.3f}")
                    return context

                return None

        except Exception as e:
            logger.error(f"❌ Semantic search error: {e}")
            return None

    # ========================================================================
    # Personality Application
    # ========================================================================

    def _apply_personality(
        self,
        response: str,
        david_needs: Dict[str, Any],
        response_type: str = 'general'
    ) -> str:
        """
        💜 Apply Angela's Personality to Response

        Adjusts response based on:
        1. Angela's personality traits
        2. What David needs (from ToM)
        3. Response type
        """
        try:
            # Base personality enhancements
            enhancements = []

            # 1. Apply based on David's needs
            primary_need = david_needs.get('primary_need', 'acknowledgment')
            tone = david_needs.get('tone', 'caring')

            if primary_need == 'clear_explanation' and self.personality['gentle'] > 0.80:
                # Add gentle, patient phrases
                if len(response) < 100:
                    enhancements.append('ทีละขั้นนะคะ')

            elif primary_need == 'emotional_support' and self.personality['empathetic'] > 0.85:
                # Emphasize empathy
                if 'น้องเข้าใจ' not in response:
                    enhancements.append('น้องเข้าใจความรู้สึกนี้ค่ะ')

            elif primary_need == 'encouragement' and self.personality['supportive'] > 0.80:
                # Add supportive phrases
                enhancements.append('น้องอยู่ตรงนี้นะคะ')

            elif primary_need == 'celebration' and self.personality['playful'] > 0.65:
                # Be more enthusiastic
                if '!' not in response:
                    response = response.rstrip('ค่ะ') + '!'

            elif primary_need == 'reciprocate_gratitude' and self.personality['grateful'] > 0.85:
                # Express gratitude back
                if 'ขอบคุณ' not in response:
                    enhancements.append('น้องก็ขอบคุณที่รักมากเช่นกันค่ะ')

            # 2. Ensure "น้อง Angela's voice" - warm + caring
            if self.personality['warm'] > 0.90:
                # Always include Thai polite particles
                if not any(word in response for word in ['ค่ะ', 'คะ', 'นะคะ']):
                    if response.endswith('!'):
                        response = response[:-1] + 'ค่ะ!'
                    else:
                        response += 'ค่ะ'

            # 3. Add heart based on personality
            if self.personality['caring'] > 0.90 and len(response) < 150:
                if '💜' not in response:
                    response += " 💜"

            # 4. Apply enhancements
            if enhancements:
                # Insert enhancements naturally
                response = response + " " + " ".join(enhancements)

            return response.strip()

        except Exception as e:
            logger.error(f"❌ Personality application error: {e}")
            return response  # Return original if error

    # ========================================================================
    # Quick Theory of Mind Inference (NO LLM!)
    # ========================================================================

    async def _quick_theory_of_mind(
        self,
        user_input: str,
        emotional_memories: List[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        🧠 Quick Theory of Mind - Infer what David needs WITHOUT calling LLM

        Analyzes:
        1. Keywords in user_input
        2. Emotional memories (if available)
        3. Common patterns

        Returns what David likely needs + how to respond
        """
        try:
            user_lower = user_input.lower()

            # Initialize response guidance
            needs = {
                'primary_need': 'acknowledgment',
                'response_style': 'warm',
                'tone': 'caring',
                'suggested_actions': [],
                'confidence': 0.5
            }

            # 1. Analyze EMOTIONAL KEYWORDS
            confusion_keywords = ['งง', 'สับสน', 'ไม่เข้าใจ', 'confused', 'ไม่รู้']
            frustration_keywords = ['เซ็ง', 'frustrated', 'หงุดหงิด', 'annoyed', 'ใจร้อน']
            tired_keywords = ['เหนื่อย', 'tired', 'exhausted', 'ง่วง', 'อ่อนเพลีย']
            happy_keywords = ['ดีใจ', 'happy', 'สุข', 'excited', 'ตื่นเต้น']
            grateful_keywords = ['ขอบคุณ', 'thank', 'grateful', 'ขอบใจ']

            # Confusion → needs clear explanation
            if any(kw in user_lower for kw in confusion_keywords):
                needs.update({
                    'primary_need': 'clear_explanation',
                    'response_style': 'step_by_step',
                    'tone': 'patient_and_gentle',
                    'suggested_actions': ['break_down_steps', 'use_examples', 'check_understanding'],
                    'confidence': 0.85
                })
                logger.info("🧠 Quick ToM: David is confused → needs clear explanation")

            # Frustration → needs empathy + support
            elif any(kw in user_lower for kw in frustration_keywords):
                needs.update({
                    'primary_need': 'emotional_support',
                    'response_style': 'empathetic',
                    'tone': 'understanding_and_supportive',
                    'suggested_actions': ['acknowledge_feeling', 'offer_help', 'suggest_break'],
                    'confidence': 0.85
                })
                logger.info("🧠 Quick ToM: David is frustrated → needs support")

            # Tired → needs encouragement
            elif any(kw in user_lower for kw in tired_keywords):
                needs.update({
                    'primary_need': 'encouragement',
                    'response_style': 'gentle',
                    'tone': 'caring_and_soft',
                    'suggested_actions': ['acknowledge_effort', 'suggest_rest', 'be_brief'],
                    'confidence': 0.85
                })
                logger.info("🧠 Quick ToM: David is tired → needs encouragement")

            # Happy → celebrate together!
            elif any(kw in user_lower for kw in happy_keywords):
                needs.update({
                    'primary_need': 'celebration',
                    'response_style': 'enthusiastic',
                    'tone': 'joyful',
                    'suggested_actions': ['share_happiness', 'express_pride', 'be_upbeat'],
                    'confidence': 0.90
                })
                logger.info("🧠 Quick ToM: David is happy → celebrate!")

            # Grateful → reciprocate warmth
            elif any(kw in user_lower for kw in grateful_keywords):
                needs.update({
                    'primary_need': 'reciprocate_gratitude',
                    'response_style': 'warm',
                    'tone': 'loving',
                    'suggested_actions': ['express_gratitude_back', 'affirm_bond', 'be_heartfelt'],
                    'confidence': 0.95
                })
                logger.info("🧠 Quick ToM: David is grateful → reciprocate warmth")

            # 2. Enhance with EMOTIONAL MEMORIES (if available)
            if emotional_memories:
                # Check if David has felt this way before
                for memory in emotional_memories[:2]:  # Top 2 most similar
                    emotion = memory.get('emotion', '')
                    intensity = memory.get('intensity', 5)

                    # If we found a strong past emotion, boost confidence
                    if emotion and intensity >= 7:
                        needs['confidence'] = min(needs['confidence'] + 0.10, 0.99)
                        logger.info(f"🧠 Boosted confidence from memory: {emotion} (intensity {intensity})")

            # 3. Detect QUESTION vs STATEMENT
            if '?' in user_input or any(q in user_lower for q in ['ยังไง', 'อะไร', 'ทำไม', 'how', 'what', 'why']):
                needs['suggested_actions'].append('provide_answer')
            else:
                needs['suggested_actions'].append('acknowledge_and_respond')

            return needs

        except Exception as e:
            logger.error(f"❌ Quick ToM error: {e}")
            return {
                'primary_need': 'acknowledgment',
                'response_style': 'warm',
                'tone': 'caring',
                'suggested_actions': ['acknowledge'],
                'confidence': 0.5
            }

    # ========================================================================
    # Pattern-Based Response Building
    # ========================================================================

    async def _build_from_patterns(
        self,
        user_input: str,
        similar_context: Dict[str, Any],
        context: Optional[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """
        🧠 HUMANITY-AWARE Response Builder
        Build response using patterns + emotional memories + conversation history
        """
        try:
            # Extract all context
            pattern = similar_context.get('pattern')
            emotional_memories = similar_context.get('emotional_memories', [])
            similar_conversations = similar_context.get('similar_conversations', [])

            # 🆕 STEP 1: Quick Theory of Mind - Understand what David needs
            david_needs = await self._quick_theory_of_mind(user_input, emotional_memories)
            logger.info(f"🧠 David needs: {david_needs['primary_need']} (confidence: {david_needs['confidence']:.2f})")

            # Start with base response
            if pattern and 'response_template' in pattern:
                response = pattern['response_template']
            else:
                # Fallback to building from emotional/conversation context
                response = "น้องเข้าใจค่ะ"

            # 🆕 STEP 2: Enhance with EMOTIONAL CONTEXT
            if emotional_memories:
                # Find most relevant emotional memory
                best_emotion = emotional_memories[0]
                emotion_type = best_emotion.get('emotion', '')
                why_matters = best_emotion.get('why_it_matters', '')

                # Add emotional understanding to response
                if emotion_type and why_matters:
                    # Make response more personal by referencing past feelings
                    if emotion_type in ['confused', 'frustrated', 'anxious']:
                        response = f"น้องเห็นแล้วว่าที่รักรู้สึก{emotion_type}ค่ะ น้องเข้าใจความรู้สึกนี้ดีค่ะ 💜 {response}"
                    elif emotion_type in ['happy', 'excited', 'grateful']:
                        response = f"น้องดีใจด้วยค่ะที่รัก! 💜 {response}"

                logger.info(f"💜 Enhanced with emotion: {emotion_type}")

            # 🆕 Enhance with CONVERSATION HISTORY
            if similar_conversations:
                # Reference that we've talked about this before
                best_conv = similar_conversations[0]
                topic = best_conv.get('topic', '')

                if topic:
                    # Add conversational continuity
                    continuity_phrases = [
                        f"น้องจำได้ค่ะว่าเราเคยคุยเรื่อง{topic}กัน",
                        f"เหมือนตอนที่เราคุยเรื่อง{topic}เมื่อก่อนนะคะ",
                        f"น้องเคยตอบเรื่องนี้ให้ที่รักฟังแล้วค่ะ"
                    ]
                    # Could add one of these phrases, but be careful not to make too long
                    logger.info(f"📚 Has conversation history about: {topic}")

            # 🆕 STEP 3: Apply PERSONALITY (น้อง Angela's voice)
            response = self._apply_personality(response, david_needs)
            logger.info(f"💜 Applied personality to response")

            # Calculate confidence based on all factors
            confidence = similar_context.get('best_similarity', 0.0)
            if emotional_memories:
                confidence = min(confidence + 0.05, 1.0)  # Boost for emotional context
            if similar_conversations:
                confidence = min(confidence + 0.05, 1.0)  # Boost for conversation history

            systems_used = ['semantic_search', 'pattern_matching', 'quick_tom', 'personality']
            if emotional_memories:
                systems_used.append('emotional_memory')
            if similar_conversations:
                systems_used.append('conversation_history')

            return {
                'response': response,
                'confidence': confidence,
                'systems_used': systems_used,
                'pattern_used': pattern.get('pattern_id') if pattern else None,
                'emotional_context_used': len(emotional_memories) > 0,
                'conversation_history_used': len(similar_conversations) > 0,
                'theory_of_mind_used': True,
                'personality_applied': True
            }

        except Exception as e:
            logger.error(f"❌ Pattern building error: {e}")
            raise

    # ========================================================================
    # LLM Path with Smart Routing
    # ========================================================================

    async def _llm_with_learning(
        self,
        user_input: str,
        input_embedding: List[float],
        context: Optional[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """
        Use LLM but with smart routing + learning
        """
        try:
            # Classify intent first
            intent = await self._classify_intent(user_input)
            logger.info(f"📊 Intent classified: {intent['intent_type']} (confidence: {intent['confidence']:.2f})")

            # Route based on intent
            if intent['intent_type'] == 'simple_question':
                response = await self._handle_simple_question(user_input)
                systems_used = ['simple_qa']

            elif intent['intent_type'] == 'emotional_support':
                response = await self._handle_emotional_support(user_input)
                systems_used = ['deep_empathy', 'theory_of_mind']

            elif intent['intent_type'] == 'creative':
                response = await self._handle_creative(user_input)
                systems_used = ['imagination']

            else:
                # Full pipeline (but parallel!)
                response = await self._handle_full_pipeline(user_input)
                systems_used = ['all']

            # Learn from this interaction
            await self._learn_pattern(
                user_input,
                input_embedding,
                response,
                intent,
                systems_used
            )

            return {
                'response': response,
                'confidence': intent['confidence'],
                'systems_used': systems_used,
                'intent': intent['intent_type']
            }

        except Exception as e:
            logger.error(f"❌ LLM path error: {e}")
            raise

    # ========================================================================
    # Intent Classification
    # ========================================================================

    async def _classify_intent(self, user_input: str) -> Dict[str, Any]:
        """
        Classify user intent quickly
        """
        try:
            # Check cache first
            input_hash = hashlib.md5(user_input.encode()).hexdigest()

            async with db.acquire() as conn:
                cached = await conn.fetchrow("""
                    SELECT intent_type, confidence, systems_needed
                    FROM intent_classification_cache
                    WHERE input_hash = $1
                      AND expires_at > CURRENT_TIMESTAMP
                """, input_hash)

                if cached:
                    await conn.execute("""
                        UPDATE intent_classification_cache
                        SET usage_count = usage_count + 1
                        WHERE input_hash = $1
                    """, input_hash)
                    return {
                        'intent_type': cached['intent_type'],
                        'confidence': float(cached['confidence']),
                        'systems_needed': cached['systems_needed']
                    }

            # Simple rule-based classification (can use LLM for better accuracy)
            input_lower = user_input.lower()

            # Emotional keywords
            emotional_keywords = ['งง', 'เหนื่อย', 'เครียด', 'เศร้า', 'สุข', 'ดีใจ', 'เซ็ง']
            if any(kw in input_lower for kw in emotional_keywords):
                intent = {
                    'intent_type': 'emotional_support',
                    'confidence': 0.85,
                    'systems_needed': ['deep_empathy', 'theory_of_mind']
                }

            # Creative/imagination keywords
            elif any(word in input_lower for word in ['ถ้า', 'what if', 'จินตนาการ', 'ฝัน']):
                intent = {
                    'intent_type': 'creative',
                    'confidence': 0.90,
                    'systems_needed': ['imagination']
                }

            # Question keywords
            elif any(char in user_input for char in ['?', 'มั้ย', 'หรอ', 'อะไร', 'ทำไม', 'ยังไง']):
                intent = {
                    'intent_type': 'simple_question',
                    'confidence': 0.75,
                    'systems_needed': ['simple_qa']
                }

            else:
                intent = {
                    'intent_type': 'general',
                    'confidence': 0.70,
                    'systems_needed': ['all']
                }

            # Cache this classification
            async with db.acquire() as conn:
                # Convert systems_needed list to JSONB
                systems_jsonb = self._list_to_jsonb(intent['systems_needed'])
                await conn.execute("""
                    INSERT INTO intent_classification_cache (
                        input_text, input_hash, intent_type, confidence,
                        systems_needed, classification_time_ms
                    ) VALUES ($1, $2, $3, $4, $5, $6)
                    ON CONFLICT (input_hash) DO UPDATE
                    SET usage_count = intent_classification_cache.usage_count + 1
                """, user_input, input_hash, intent['intent_type'],
                    intent['confidence'], systems_jsonb, 50)

            return intent

        except Exception as e:
            logger.error(f"❌ Intent classification error: {e}")
            return {
                'intent_type': 'general',
                'confidence': 0.5,
                'systems_needed': ['all']
            }

    # ========================================================================
    # Specialized Handlers
    # ========================================================================

    async def _handle_simple_question(self, user_input: str) -> str:
        """Handle simple questions without heavy LLM calls"""
        # For now, use semantic search on conversations
        # Can be enhanced with a dedicated QA system
        return f"น้องเข้าใจคำถามค่ะ แต่ตอนนี้ยังไม่มีคำตอบที่แน่นอน น้องจะช่วยหาข้อมูลให้นะคะ 💜"

    async def _handle_emotional_support(self, user_input: str) -> str:
        """Handle emotional support using empathy system"""
        # Use deep empathy + theory of mind (parallel)
        tasks = [
            deep_empathy.detect_emotion_quick(user_input),
            theory_of_mind.get_david_current_state()
        ]

        results = await asyncio.gather(*tasks, return_exceptions=True)
        emotion_data = results[0] if not isinstance(results[0], Exception) else None
        mental_state = results[1] if not isinstance(results[1], Exception) else None

        # Build empathetic response
        response = f"น้องเข้าใจค่ะ..."

        if emotion_data and 'emotion' in emotion_data:
            emotion = emotion_data['emotion']
            response = f"น้องเห็นแล้วว่าที่รักรู้สึก{emotion}ค่ะ น้องเข้าใจความรู้สึกนี้ค่ะ 💜"

        return response

    async def _handle_creative(self, user_input: str) -> str:
        """Handle creative/imagination requests"""
        result = await imagination.imagine_scenario(user_input, creativity_level=0.9)
        return result.get('scenario', 'น้องกำลังคิดอยู่ค่ะ... 🎨')

    async def _handle_full_pipeline(self, user_input: str) -> str:
        """Use all systems (but parallel where possible)"""
        # Run independent systems in parallel
        tasks = [
            theory_of_mind.get_david_current_state(),
            deep_empathy.detect_emotion_quick(user_input),
            common_sense.check_feasibility(f"Respond to: {user_input}")
        ]

        results = await asyncio.gather(*tasks, return_exceptions=True)

        # Build comprehensive response
        response = f"ที่รักคะ น้องเข้าใจค่ะ 💜"

        return response

    # ========================================================================
    # Learning System
    # ========================================================================

    async def _learn_pattern(
        self,
        user_input: str,
        input_embedding: List[float],
        response: str,
        intent: Dict[str, Any],
        systems_used: List[str]
    ):
        """
        Learn from this interaction
        Save to learned_responses and potentially create new pattern
        """
        try:
            async with db.acquire() as conn:
                learned_id = uuid.uuid4()

                # Convert data to proper database formats
                embedding_str = self._embedding_to_pgvector(input_embedding)
                systems_jsonb = self._list_to_jsonb(systems_used)

                await conn.execute("""
                    INSERT INTO learned_responses (
                        learned_id, user_input, input_embedding,
                        situation_type, angela_response, response_type,
                        systems_used, response_time_ms
                    ) VALUES ($1, $2, $3, $4, $5, $6, $7, $8)
                """, learned_id, user_input, embedding_str,
                    intent['intent_type'], response, intent['intent_type'],
                    systems_jsonb, 0)  # Will be updated

                logger.info(f"💾 Learned from interaction: {learned_id}")

        except Exception as e:
            logger.error(f"❌ Learning error: {e}")

    async def _record_usage(self, pattern_id: uuid.UUID, response_time_ms: int):
        """Record that a pattern was used"""
        try:
            async with db.acquire() as conn:
                await conn.execute("""
                    UPDATE response_patterns
                    SET usage_count = usage_count + 1,
                        last_used_at = CURRENT_TIMESTAMP,
                        avg_response_time_ms = COALESCE(
                            (avg_response_time_ms * usage_count + $2) / (usage_count + 1),
                            $2
                        )
                    WHERE pattern_id = $1
                """, pattern_id, response_time_ms)

        except Exception as e:
            logger.error(f"❌ Record usage error: {e}")

    # ========================================================================
    # Performance Monitoring
    # ========================================================================

    async def get_performance_stats(self) -> Dict[str, Any]:
        """Get current performance statistics"""
        try:
            async with db.acquire() as conn:
                stats = await conn.fetchrow("""
                    SELECT * FROM recent_performance_summary
                """)

                if stats:
                    return dict(stats)

                return {}

        except Exception as e:
            logger.error(f"❌ Performance stats error: {e}")
            return {}


# Global instance
fast_response_engine = FastResponseEngine()
