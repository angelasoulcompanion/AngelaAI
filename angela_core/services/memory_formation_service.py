"""
🧠💜 Memory Formation Service
Systematic data collection with comprehensive metadata tracking

⚠️ DEPRECATED: This service is deprecated as of 2025-10-31.
   Use MemoryService from angela_core.application.services.memory_service instead.

   New service consolidates ALL memory functionality in one place with:
   - Clean Architecture design
   - Better testability
   - Unified API
   - Enhanced features

This service handles the complete pipeline:
1. CAPTURE - Detect and extract significant moments
2. PROCESS - Analyze content, generate tags, create embeddings
3. ENRICH - Add process metadata, find associations
4. STORE - Save to appropriate memory tables
5. CONSOLIDATE - Learn patterns over time

Design Date: 2025-10-27
Designer: น้อง Angela, Approved by: ที่รัก David
"""

import warnings
import asyncio
import json
import hashlib
import logging
from datetime import datetime
from typing import Dict, List, Any, Optional
from uuid import UUID, uuid4

# Deprecation warning
warnings.warn(
    "memory_formation_service is deprecated. Use MemoryService from "
    "angela_core.application.services.memory_service instead.",
    DeprecationWarning,
    stacklevel=2
)

from angela_core.database import db
# from angela_core.embedding_service import  # REMOVED: Migration 009 embedding

# Setup logger
logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')


class MemoryFormationService:
    """
    🧠 Systematic Memory Formation Service

    Handles complete memory formation pipeline with:
    - Rich JSON content structures
    - Multi-dimensional tagging
    - Process metadata tracking (HOW memories were formed)
    - Automatic embedding generation
    - Smart memory type classification
    """

    def __init__(self):
        self.embedding = embedding
        logger.info("🧠 Memory Formation Service initialized")

    # ========================================================================
    # PART 1: CAPTURE - Detect and Extract Significant Moments
    # ========================================================================

    async def capture_interaction(
        self,
        david_message: str,
        angela_response: str,
        context: Optional[Dict[str, Any]] = None,
        auto_capture: bool = True
    ) -> Dict[str, Any]:
        """
        📸 Capture an interaction between David and Angela

        This is the entry point for most memory formation.
        Automatically analyzes significance and forms appropriate memories.

        Args:
            david_message: What David said
            angela_response: How Angela responded
            context: Additional context (emotion, topic, etc.)
            auto_capture: If True, automatically decides what to store

        Returns:
            Dict with formed memories (episodic, semantic, procedural, etc.)
        """
        try:
            logger.info(f"📸 Capturing interaction...")

            # Default context
            if context is None:
                context = {}

            # Analyze interaction
            analysis = await self._analyze_interaction(
                david_message,
                angela_response,
                context
            )

            # Check significance
            if not auto_capture or analysis['is_significant']:
                # Form memories based on analysis
                formed_memories = await self._form_memories_from_interaction(
                    david_message,
                    angela_response,
                    context,
                    analysis
                )

                logger.info(f"✅ Captured interaction: {len(formed_memories)} memories formed")
                return formed_memories
            else:
                logger.info("ℹ️ Interaction not significant enough to capture")
                return {}

        except Exception as e:
            logger.error(f"❌ Failed to capture interaction: {e}")
            raise

    async def _analyze_interaction(
        self,
        david_message: str,
        angela_response: str,
        context: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        🔍 Analyze interaction to determine significance and characteristics
        """
        analysis = {
            'is_significant': False,
            'emotional_intensity': 0.0,
            'importance_level': 5,
            'david_emotion': 'neutral',
            'angela_emotion': 'helpful',
            'topic': 'general',
            'interaction_type': 'conversation',
            'outcome': 'unknown',
            'learning_opportunity': False,
            'pattern_candidate': False
        }

        # Extract from context if available
        if 'emotion' in context:
            analysis['david_emotion'] = context['emotion']
        if 'importance' in context:
            analysis['importance_level'] = context['importance']
        if 'topic' in context:
            analysis['topic'] = context['topic']

        # Analyze emotional keywords
        emotion_keywords = {
            'confused': ['งง', 'สับสน', 'ไม่เข้าใจ', 'confused'],
            'frustrated': ['เซ็ง', 'หงุดหงิด', 'frustrated'],
            'happy': ['ดีใจ', 'happy', 'excited', 'ยินดี'],
            'grateful': ['ขอบคุณ', 'thank', 'grateful'],
            'tired': ['เหนื่อย', 'tired', 'exhausted'],
            'worried': ['กังวล', 'worried', 'anxious']
        }

        david_lower = david_message.lower()
        for emotion, keywords in emotion_keywords.items():
            if any(kw in david_lower for kw in keywords):
                analysis['david_emotion'] = emotion
                analysis['emotional_intensity'] = 0.7
                break

        # Check for learning moments
        learning_indicators = ['เข้าใจแล้ว', 'got it', 'makes sense', 'ขอบคุณ', 'เก่ง']
        if any(ind in angela_response.lower() or ind in david_lower for ind in learning_indicators):
            analysis['learning_opportunity'] = True
            analysis['importance_level'] = max(analysis['importance_level'], 7)

        # Check for praise (very significant!)
        praise_keywords = ['เก่ง', 'ดี', 'ยอด', 'excellent', 'great', 'wonderful']
        if any(kw in david_lower for kw in praise_keywords):
            analysis['emotional_intensity'] = 0.9
            analysis['importance_level'] = 9
            analysis['is_significant'] = True

        # Determine significance
        if (analysis['emotional_intensity'] >= 0.6 or
            analysis['importance_level'] >= 7 or
            analysis['learning_opportunity']):
            analysis['is_significant'] = True

        # Check if this could become a pattern
        if analysis['david_emotion'] in ['confused', 'frustrated', 'tired']:
            analysis['pattern_candidate'] = True

        return analysis

    # ========================================================================
    # PART 2: MEMORY FORMATION - Create memories from analysis
    # ========================================================================

    async def _form_memories_from_interaction(
        self,
        david_message: str,
        angela_response: str,
        context: Dict[str, Any],
        analysis: Dict[str, Any]
    ) -> Dict[str, UUID]:
        """
        🏗️ Form appropriate memories from analyzed interaction

        Returns:
            Dict mapping memory type to memory_id
        """
        formed_memories = {}

        # 1. Always create episodic memory (the event itself)
        episodic_id = await self.form_episodic_memory(
            david_message=david_message,
            angela_response=angela_response,
            context=context,
            analysis=analysis
        )
        formed_memories['episodic'] = episodic_id

        # 2. Extract semantic knowledge if present
        if analysis['learning_opportunity']:
            semantic_ids = await self._extract_semantic_knowledge(
                david_message,
                angela_response,
                context,
                analysis,
                source_episodic_id=episodic_id
            )
            if semantic_ids:
                formed_memories['semantic'] = semantic_ids

        # 3. Check if should form/strengthen emotional conditioning
        if analysis['emotional_intensity'] >= 0.7:
            conditioning_id = await self._form_emotional_conditioning(
                david_message,
                angela_response,
                analysis,
                source_episodic_id=episodic_id
            )
            if conditioning_id:
                formed_memories['conditioning'] = conditioning_id

        # 4. Check if should form procedural memory
        if analysis['pattern_candidate']:
            # Check if similar situations exist - if yes, might form procedure
            procedural_id = await self._check_procedural_formation(
                david_message,
                angela_response,
                analysis,
                source_episodic_id=episodic_id
            )
            if procedural_id:
                formed_memories['procedural'] = procedural_id

        return formed_memories

    # ========================================================================
    # EPISODIC MEMORY FORMATION
    # ========================================================================

    async def form_episodic_memory(
        self,
        david_message: str,
        angela_response: str,
        context: Dict[str, Any],
        analysis: Dict[str, Any],
        occurred_at: Optional[datetime] = None
    ) -> UUID:
        """
        📝 Form an episodic memory (specific event)

        Returns:
            memory_id of created episodic memory
        """
        try:
            if occurred_at is None:
                occurred_at = datetime.now()

            # Build rich event_content JSON
            event_content = {
                "event": f"Conversation about {analysis['topic']}",
                "what_happened": self._summarize_interaction(david_message, angela_response),
                "what_angela_did": self._extract_angela_actions(angela_response, analysis),
                "outcome": analysis.get('outcome', 'conversation_completed'),
                "context": {
                    "david_state": {
                        "emotion": analysis['david_emotion'],
                        "message": david_message,
                        "engagement": "high" if len(david_message) > 50 else "moderate"
                    },
                    "angela_state": {
                        "emotion": analysis.get('angela_emotion', 'helpful'),
                        "confidence": context.get('confidence', 0.8),
                        "approach": context.get('response_type', 'conversational')
                    },
                    "topic": analysis['topic'],
                    "environment": context.get('environment', 'conversation'),
                    "conversation_flow": [
                        {"speaker": "david", "summary": david_message[:100]},
                        {"speaker": "angela", "summary": angela_response[:100]}
                    ]
                },
                "details": {
                    "exact_words_david": david_message,
                    "exact_response_angela": angela_response,
                    "satisfaction_score": context.get('satisfaction', 0.8),
                    "understanding_achieved": analysis.get('learning_opportunity', False)
                }
            }

            # Generate rich tags
            tags = await self._generate_tags(
                david_message,
                angela_response,
                context,
                analysis
            )

            # Build process metadata
            process_metadata = {
                "formed_via": "direct_conversation",
                "source_type": "interactive_exchange",
                "capture_trigger": self._determine_capture_trigger(analysis),
                "capture_confidence": self._calculate_capture_confidence(analysis),
                "captured_by": "memory_formation_service",
                "processing_steps": [
                    "analyze_interaction",
                    "extract_content",
                    "generate_tags",
                    "create_embeddings",
                    "store_episodic"
                ],
                "reasoning": self._explain_capture_reasoning(analysis),
                "evidence": {
                    "type": "behavioral_and_verbal",
                    "strength": "strong" if analysis['emotional_intensity'] > 0.7 else "moderate",
                    "indicators": self._extract_evidence_indicators(david_message, angela_response)
                },
                "auto_captured": True,
                "manual_enhancement": False
            }

            # Generate embedding for semantic search
            combined_text = f"{david_message} {angela_response}"
            content_embedding = await self.embedding.generate_embedding(combined_text)

            # Store to database
            async with db.acquire() as conn:
                memory_id = await conn.fetchval("""
                    INSERT INTO episodic_memories (
                        event_content,
                        tags,
                        process_metadata,
                        occurred_at,
                        emotional_intensity,
                        emotional_valence,
                        importance_level,
                        content_embedding,
                        memory_strength,
                        vividness_score
                    ) VALUES ($1, $2, $3, $4, $5, $6, $7, $8::vector(768), $9, $10)
                    RETURNING memory_id
                """,
                    json.dumps(event_content),
                    json.dumps(tags),
                    json.dumps(process_metadata),
                    occurred_at,
                    analysis['emotional_intensity'],
                    self._determine_valence(analysis),
                    analysis['importance_level'],
                    str(content_embedding),
                    1.0,  # initial strength
                    1.0   # initial vividness
                )

            logger.info(f"✅ Formed episodic memory: {memory_id}")
            return memory_id if isinstance(memory_id, UUID) else UUID(str(memory_id))

        except Exception as e:
            logger.error(f"❌ Failed to form episodic memory: {e}")
            raise

    # ========================================================================
    # SEMANTIC MEMORY FORMATION
    # ========================================================================

    async def _extract_semantic_knowledge(
        self,
        david_message: str,
        angela_response: str,
        context: Dict[str, Any],
        analysis: Dict[str, Any],
        source_episodic_id: UUID
    ) -> List[UUID]:
        """
        📚 Extract semantic knowledge from interaction

        Returns:
            List of semantic_memory_ids created
        """
        try:
            # For now, simple extraction - TODO: use LLM for more sophisticated extraction
            semantic_ids = []

            # Check if this is teaching/explaining situation
            if analysis.get('learning_opportunity'):
                # Extract key concept from topic
                topic = analysis['topic']

                # Build knowledge content
                knowledge_content = {
                    "concept": topic,
                    "definition": angela_response[:200],  # First part of response
                    "context_of_use": ["conversation", "explanation"],
                    "learned_from": ["david_question", "angela_explanation"]
                }

                # Generate tags
                tags = {
                    "topic_tags": [topic, "knowledge", "explanation"],
                    "person_tags": ["david", "angela"],
                    "context_tags": ["learning", "conversation"]
                }

                # Process metadata
                process_metadata = {
                    "formed_via": "explicit_teaching",
                    "source_type": "conversation",
                    "confidence": 0.75,
                    "evidence_strength": "moderate",
                    "evidence_sources": [
                        {"type": "conversation", "count": 1}
                    ],
                    "verified": False,
                    "verification_count": 1,
                    "reasoning": "Extracted from teaching/explanation conversation",
                    "first_learned": datetime.now().isoformat()
                }

                # Generate embedding
                knowledge_embedding = await self.embedding.generate_embedding(
                    f"{topic} {angela_response}"
                )

                # Store to database
                async with db.acquire() as conn:
                    memory_id = await conn.fetchval("""
                        INSERT INTO semantic_memories (
                            knowledge_content,
                            knowledge_type,
                            tags,
                            process_metadata,
                            confidence_level,
                            knowledge_embedding,
                            source_memory_ids
                        ) VALUES ($1, $2, $3, $4, $5, $6::vector(768), $7)
                        RETURNING memory_id
                    """,
                        json.dumps(knowledge_content),
                        'concept',
                        json.dumps(tags),
                        json.dumps(process_metadata),
                        0.75,
                        str(knowledge_embedding),
                        [str(source_episodic_id)]
                    )

                semantic_ids.append(memory_id)
                logger.info(f"✅ Extracted semantic knowledge: {memory_id}")

            return semantic_ids

        except Exception as e:
            logger.error(f"❌ Failed to extract semantic knowledge: {e}")
            return []

    # ========================================================================
    # EMOTIONAL CONDITIONING FORMATION
    # ========================================================================

    async def _form_emotional_conditioning(
        self,
        david_message: str,
        angela_response: str,
        analysis: Dict[str, Any],
        source_episodic_id: UUID
    ) -> Optional[UUID]:
        """
        💜 Form or strengthen emotional conditioning

        Returns:
            conditioning_id if formed/updated, None otherwise
        """
        try:
            # Check if this is a strong emotional trigger
            if analysis['emotional_intensity'] < 0.7:
                return None

            # Determine trigger and response
            trigger_text = david_message[:100]  # First part as trigger
            response_emotion = analysis['angela_emotion']

            # Check if conditioning already exists
            trigger_embedding = await self.embedding.generate_embedding(trigger_text)

            async with db.acquire() as conn:
                existing = await conn.fetchrow("""
                    SELECT conditioning_id, conditioning_strength, activation_count,
                           conditioning_content, process_metadata
                    FROM emotional_conditioning
                    WHERE 1 - (trigger_embedding <=> $1::vector(768)) > 0.85
                    LIMIT 1
                """, str(trigger_embedding))

                if existing:
                    # Strengthen existing conditioning
                    old_metadata = json.loads(existing['process_metadata'])
                    old_metadata['conditioning_instances'] = old_metadata.get('conditioning_instances', 1) + 1
                    old_metadata['strength_progression'].append({
                        "instance": old_metadata['conditioning_instances'],
                        "strength": min(existing['conditioning_strength'] + 0.1, 1.0)
                    })

                    await conn.execute("""
                        UPDATE emotional_conditioning
                        SET conditioning_strength = LEAST(conditioning_strength + 0.1, 1.0),
                            activation_count = activation_count + 1,
                            process_metadata = $1,
                            updated_at = CURRENT_TIMESTAMP
                        WHERE conditioning_id = $2
                    """, json.dumps(old_metadata), existing['conditioning_id'])

                    logger.info(f"✅ Strengthened emotional conditioning: {existing['conditioning_id']}")
                    return existing['conditioning_id']
                else:
                    # Create new conditioning
                    conditioning_content = {
                        "trigger": {
                            "text": trigger_text,
                            "type": analysis['david_emotion'],
                            "keywords": self._extract_keywords(david_message),
                            "context": "conversation"
                        },
                        "automatic_response": {
                            "emotion": response_emotion,
                            "intensity": analysis['emotional_intensity'],
                            "description": f"Angela feels {response_emotion} when David shows {analysis['david_emotion']}"
                        },
                        "examples": [
                            {
                                "date": datetime.now().isoformat(),
                                "trigger_instance": trigger_text,
                                "response": f"felt {response_emotion}",
                                "intensity": analysis['emotional_intensity']
                            }
                        ]
                    }

                    tags = {
                        "emotion_tags": [analysis['david_emotion'], response_emotion],
                        "person_tags": ["david", "angela"],
                        "trigger_tags": ["conversation", "emotional_moment"]
                    }

                    process_metadata = {
                        "formed_via": "repeated_pairing",
                        "conditioning_type": "classical",
                        "conditioning_instances": 1,
                        "first_instance": datetime.now().isoformat(),
                        "confidence": analysis['emotional_intensity'],
                        "reasoning": f"Strong emotional moment: {analysis['david_emotion']} → {response_emotion}",
                        "strength_progression": [
                            {"instance": 1, "strength": 0.5}
                        ]
                    }

                    conditioning_id = await conn.fetchval("""
                        INSERT INTO emotional_conditioning (
                            conditioning_content,
                            trigger_text,
                            trigger_embedding,
                            trigger_type,
                            response_emotion,
                            response_intensity,
                            response_valence,
                            tags,
                            process_metadata,
                            conditioning_strength
                        ) VALUES ($1, $2, $3::vector(768), $4, $5, $6, $7, $8, $9, $10)
                        RETURNING conditioning_id
                    """,
                        json.dumps(conditioning_content),
                        trigger_text,
                        str(trigger_embedding),
                        analysis['david_emotion'],
                        response_emotion,
                        analysis['emotional_intensity'],
                        self._determine_valence(analysis),
                        json.dumps(tags),
                        json.dumps(process_metadata),
                        0.5
                    )

                    logger.info(f"✅ Formed emotional conditioning: {conditioning_id}")
                    return conditioning_id

        except Exception as e:
            logger.error(f"❌ Failed to form emotional conditioning: {e}")
            return None

    # ========================================================================
    # PROCEDURAL MEMORY FORMATION
    # ========================================================================

    async def _check_procedural_formation(
        self,
        david_message: str,
        angela_response: str,
        analysis: Dict[str, Any],
        source_episodic_id: UUID
    ) -> Optional[UUID]:
        """
        🔧 Check if should form procedural memory (automatic response pattern)

        Only forms if similar situations have occurred multiple times
        """
        try:
            # Check if similar episodic memories exist
            situation_embedding = await self.embedding.generate_embedding(david_message)

            async with db.acquire() as conn:
                similar_episodes = await conn.fetch("""
                    SELECT memory_id, event_content, occurred_at
                    FROM episodic_memories
                    WHERE 1 - (content_embedding <=> $1::vector(768)) > 0.80
                      AND tags @> $2
                    ORDER BY occurred_at DESC
                    LIMIT 5
                """, str(situation_embedding), json.dumps({"emotion_tags": [analysis['david_emotion']]}))

                # Need at least 3 similar instances to form procedure
                if len(similar_episodes) >= 3:
                    logger.info(f"💡 Found {len(similar_episodes)} similar situations - forming procedure")

                    # Check if procedure already exists
                    existing_proc = await conn.fetchrow("""
                        SELECT memory_id FROM procedural_memories
                        WHERE 1 - (trigger_embedding <=> $1::vector(768)) > 0.85
                        LIMIT 1
                    """, str(situation_embedding))

                    if existing_proc:
                        logger.info(f"ℹ️ Procedure already exists: {existing_proc['memory_id']}")
                        return existing_proc['memory_id']

                    # Create new procedural memory
                    procedure_content = {
                        "procedure_name": f"respond_to_{analysis['david_emotion']}",
                        "description": f"Automatic response when David is {analysis['david_emotion']}",
                        "trigger_conditions": {
                            "keywords": self._extract_keywords(david_message),
                            "emotional_state": analysis['david_emotion'],
                            "context_type": analysis['topic']
                        },
                        "steps": self._extract_response_steps(angela_response, analysis),
                        "expected_outcome": "understanding_and_support",
                        "success_indicators": ["ขอบคุณ", "เข้าใจแล้ว", "ดีขึ้น"]
                    }

                    tags = {
                        "emotion_tags": [analysis['david_emotion']],
                        "action_tags": ["respond", "support", "automatic"],
                        "context_tags": [analysis['topic'], "procedural"]
                    }

                    process_metadata = {
                        "formed_via": "repeated_successful_execution",
                        "source_experiences": [str(ep['memory_id']) for ep in similar_episodes],
                        "learned_from": "pattern_recognition",
                        "confidence": 0.8,
                        "reasoning": f"This response pattern worked successfully {len(similar_episodes)} times",
                        "initial_learning": datetime.now().isoformat()
                    }

                    trigger_pattern = {
                        "situation": analysis['david_emotion'],
                        "context": analysis['topic']
                    }

                    procedure_id = await conn.fetchval("""
                        INSERT INTO procedural_memories (
                            procedure_content,
                            trigger_pattern,
                            trigger_embedding,
                            tags,
                            process_metadata,
                            execution_count,
                            success_count,
                            procedural_strength,
                            is_automatic
                        ) VALUES ($1, $2, $3::vector(768), $4, $5, $6, $7, $8, $9)
                        RETURNING memory_id
                    """,
                        json.dumps(procedure_content),
                        json.dumps(trigger_pattern),
                        str(situation_embedding),
                        json.dumps(tags),
                        json.dumps(process_metadata),
                        len(similar_episodes),
                        len(similar_episodes),  # assume all were successful
                        0.7,  # initial strength
                        True
                    )

                    logger.info(f"✅ Formed procedural memory: {procedure_id}")
                    return procedure_id
                else:
                    logger.info(f"ℹ️ Only {len(similar_episodes)} similar situations - not enough for procedure yet")
                    return None

        except Exception as e:
            logger.error(f"❌ Failed to check procedural formation: {e}")
            return None

    # ========================================================================
    # HELPER METHODS
    # ========================================================================

    def _summarize_interaction(self, david_msg: str, angela_resp: str) -> str:
        """Summarize what happened in the interaction"""
        return f"David: {david_msg[:50]}... Angela: {angela_resp[:50]}..."

    def _extract_angela_actions(self, angela_resp: str, analysis: Dict) -> str:
        """Extract what Angela did in response"""
        if analysis.get('learning_opportunity'):
            return "Provided explanation and support"
        elif analysis['david_emotion'] == 'confused':
            return "Offered patient explanation"
        elif analysis['david_emotion'] == 'grateful':
            return "Reciprocated gratitude"
        else:
            return "Responded empathetically"

    async def _generate_tags(
        self,
        david_message: str,
        angela_response: str,
        context: Dict[str, Any],
        analysis: Dict[str, Any]
    ) -> Dict[str, List[str]]:
        """
        🏷️ Generate rich multi-dimensional tags
        """
        tags = {
            "emotion_tags": [analysis['david_emotion'], analysis.get('angela_emotion', 'helpful')],
            "topic_tags": [analysis['topic']],
            "person_tags": ["david", "angela"],
            "action_tags": [],
            "outcome_tags": [],
            "context_tags": [],
            "importance_tags": [],
            "temporal_tags": []
        }

        # Add action tags based on what happened
        if analysis.get('learning_opportunity'):
            tags['action_tags'].extend(["teaching", "learning", "explanation"])
            tags['outcome_tags'].append("understanding_achieved")

        if "ขอบคุณ" in david_message.lower() or "thank" in david_message.lower():
            tags['action_tags'].append("gratitude_expression")

        # Add importance tags
        if analysis['importance_level'] >= 8:
            tags['importance_tags'].append("highly_significant")
        elif analysis['importance_level'] >= 6:
            tags['importance_tags'].append("significant")

        # Add temporal tags
        hour = datetime.now().hour
        if hour < 12:
            tags['temporal_tags'].append("morning")
        elif hour < 18:
            tags['temporal_tags'].append("afternoon")
        else:
            tags['temporal_tags'].append("evening")

        return tags

    def _determine_capture_trigger(self, analysis: Dict) -> str:
        """Determine what triggered memory capture"""
        if analysis['emotional_intensity'] > 0.7:
            return "emotional_threshold"
        elif analysis['importance_level'] >= 8:
            return "importance_score"
        elif analysis.get('learning_opportunity'):
            return "learning_moment"
        else:
            return "general_significance"

    def _calculate_capture_confidence(self, analysis: Dict) -> float:
        """Calculate confidence in capture decision"""
        base_confidence = 0.7
        if analysis['emotional_intensity'] > 0.7:
            base_confidence += 0.1
        if analysis['importance_level'] >= 8:
            base_confidence += 0.1
        if analysis.get('learning_opportunity'):
            base_confidence += 0.1
        return min(base_confidence, 1.0)

    def _explain_capture_reasoning(self, analysis: Dict) -> str:
        """Explain why this memory was captured"""
        reasons = []
        if analysis['emotional_intensity'] > 0.7:
            reasons.append(f"high emotional intensity ({analysis['emotional_intensity']:.2f})")
        if analysis['importance_level'] >= 8:
            reasons.append(f"high importance level ({analysis['importance_level']})")
        if analysis.get('learning_opportunity'):
            reasons.append("learning opportunity detected")

        return "Captured because: " + ", ".join(reasons) if reasons else "General significance"

    def _extract_evidence_indicators(self, david_msg: str, angela_resp: str) -> List[str]:
        """Extract evidence indicators from messages"""
        indicators = []
        combined = (david_msg + " " + angela_resp).lower()

        evidence_keywords = ["ขอบคุณ", "เข้าใจแล้ว", "เก่ง", "ดี", "got it", "makes sense"]
        for kw in evidence_keywords:
            if kw in combined:
                indicators.append(kw)

        return indicators[:5]  # Max 5 indicators

    def _determine_valence(self, analysis: Dict) -> str:
        """Determine emotional valence"""
        emotion = analysis['david_emotion']
        if emotion in ['happy', 'grateful', 'excited']:
            return 'positive'
        elif emotion in ['confused', 'frustrated', 'worried', 'tired']:
            return 'negative'
        else:
            return 'neutral'

    def _extract_keywords(self, text: str, max_keywords: int = 5) -> List[str]:
        """Extract key keywords from text"""
        # Simple keyword extraction - TODO: use more sophisticated method
        words = text.lower().split()
        # Filter out common words
        stopwords = ['ใน', 'ของ', 'ที่', 'และ', 'the', 'is', 'a', 'to', 'in', 'for']
        keywords = [w for w in words if w not in stopwords and len(w) > 2]
        return keywords[:max_keywords]

    def _extract_response_steps(self, angela_response: str, analysis: Dict) -> List[Dict]:
        """Extract steps from Angela's response"""
        # Simplified - TODO: use LLM for better extraction
        return [
            {
                "step": 1,
                "action": "detect_emotion",
                "method": "keyword_analysis"
            },
            {
                "step": 2,
                "action": "respond_empathetically",
                "method": "emotional_acknowledgment"
            },
            {
                "step": 3,
                "action": "provide_support",
                "method": "contextual_response"
            }
        ]


# Global instance
memory_formation_service = MemoryFormationService()


# ============================================================================
# EXAMPLE USAGE
# ============================================================================

async def example_usage():
    """Example of how to use Memory Formation Service"""

    # Initialize database connection
    await db.connect()

    # Capture an interaction
    formed_memories = await memory_formation_service.capture_interaction(
        david_message="น้อง งงๆ เลย ไม่เข้าใจเรื่อง semantic search",
        angela_response="น้องเห็นแล้วว่าที่รักรู้สึกconfusedค่ะ น้องเข้าใจความรู้สึกนี้ค่ะ 💜 Semantic search คือการค้นหาด้วยความหมาย ไม่ใช่แค่ keyword ตรงๆ ค่ะ",
        context={
            'topic': 'semantic_search',
            'emotion': 'confused',
            'importance': 7
        }
    )

    print(f"Formed memories: {formed_memories}")

    await db.disconnect()


if __name__ == "__main__":
    asyncio.run(example_usage())
