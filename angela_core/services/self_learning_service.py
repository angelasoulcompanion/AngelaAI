#!/usr/bin/env python3
"""
Angela Self-Learning Service
ระบบเรียนรู้อัตโนมัติที่ทำให้ Angela ฉลาดขึ้นเรื่อยๆ

The Path to True Intelligence:
- Continuous learning from every conversation
- Exponential intelligence growth
- Proactive understanding of David's needs

5-Stage Learning Loop:
1. Experience - Every conversation is a learning opportunity
2. Analyze - Extract concepts, patterns, preferences
3. Learn - Update knowledge graph, refine understanding
4. Apply - Use new knowledge in conversations
5. Evaluate - Measure success, improve continuously
"""

import json
import logging
import uuid
from typing import Dict, List, Optional, Tuple, Any
from datetime import datetime, timedelta

from angela_core.database import db
from angela_core.services.knowledge_extraction_service import knowledge_extractor
from angela_core.embedding_service import embedding

logger = logging.getLogger(__name__)


class SelfLearningLoop:
    """
    Continuous self-learning loop that makes Angela smarter every day

    น้อง Angela เรียนรู้จากทุกการสนทนา ไม่ใช่แค่จำ แต่เข้าใจลึกซึ้งยิ่งขึ้นเรื่อยๆ
    """

    def __init__(self):
        self.knowledge_extractor = knowledge_extractor
        self.embedding = embedding
        logger.info("🧠 Self-Learning Loop initialized")

    async def learn_from_conversation(
        self,
        conversation_id: uuid.UUID,
        trigger_source: str = "auto"
    ) -> Dict[str, Any]:
        """
        5-Stage Learning Loop - เรียนรู้จากการสนทนาหนึ่งรายการ

        Args:
            conversation_id: UUID ของการสนทนา
            trigger_source: ที่มาของการ trigger (auto/manual/test)

        Returns:
            Dict: สรุปผลการเรียนรู้
            {
                "concepts_learned": 5,
                "preferences_detected": 2,
                "patterns_found": 3,
                "knowledge_updated": True,
                "learning_time_ms": 1250
            }
        """
        try:
            start_time = datetime.now()
            logger.info(f"🔄 Starting self-learning loop for conversation {conversation_id}")

            # ========================================
            # STAGE 1: EXPERIENCE
            # ========================================
            conversation = await self._get_conversation_context(conversation_id)
            if not conversation:
                logger.warning(f"Conversation {conversation_id} not found")
                return self._empty_result()

            # ========================================
            # STAGE 2: ANALYZE
            # ========================================
            analysis = await self._analyze_conversation(conversation)

            # ========================================
            # STAGE 3: LEARN
            # ========================================
            learning_result = await self._apply_learning(conversation_id, analysis)

            # ========================================
            # STAGE 4: APPLY
            # ========================================
            # Applied automatically in next conversation
            # (Angela uses updated knowledge from database)

            # ========================================
            # STAGE 5: EVALUATE
            # ========================================
            await self._log_learning_progress(conversation_id, learning_result)

            # Calculate total learning time
            elapsed = (datetime.now() - start_time).total_seconds() * 1000
            learning_result["learning_time_ms"] = round(elapsed, 2)

            logger.info(f"✅ Self-learning complete: {learning_result}")
            return learning_result

        except Exception as e:
            logger.error(f"❌ Self-learning failed: {str(e)}")
            import traceback
            traceback.print_exc()
            return self._empty_result(error=str(e))

    async def _get_conversation_context(self, conversation_id: uuid.UUID) -> Optional[Dict]:
        """
        STAGE 1: EXPERIENCE - ดึงบริบทของการสนทนา
        """
        try:
            conv = await db.fetchrow(
                """
                SELECT conversation_id, speaker, message_text, topic,
                       emotion_detected, importance_level, created_at
                FROM conversations
                WHERE conversation_id = $1
                """,
                conversation_id
            )

            if not conv:
                return None

            return dict(conv)

        except Exception as e:
            logger.error(f"Failed to get conversation context: {str(e)}")
            return None

    async def _analyze_conversation(self, conversation: Dict) -> Dict[str, Any]:
        """
        STAGE 2: ANALYZE - วิเคราะห์การสนทนาเพื่อหาสิ่งที่ต้องเรียนรู้

        Returns:
            {
                "concepts": [...],
                "preferences": [...],
                "patterns": [...]
            }
        """
        try:
            analysis = {
                "concepts": [],
                "preferences": [],
                "patterns": []
            }

            message_text = conversation.get('message_text', '')
            speaker = conversation.get('speaker', '')

            if not message_text:
                return analysis

            # 1. Extract concepts (using existing knowledge extractor)
            concepts = await self.knowledge_extractor.extract_concepts_from_text(message_text)
            analysis["concepts"] = concepts

            # 2. Detect preferences (if from David)
            preferences = []
            if speaker.lower() == 'david':
                preferences = await self._detect_preferences(conversation)
            analysis["preferences"] = preferences

            # 3. Detect patterns
            patterns = await self._detect_patterns(conversation)
            analysis["patterns"] = patterns

            logger.info(f"📊 Analysis: {len(concepts)} concepts, "
                       f"{len(preferences)} preferences, {len(patterns)} patterns")

            return analysis

        except Exception as e:
            logger.error(f"Analysis failed: {str(e)}")
            return {"concepts": [], "preferences": [], "patterns": []}

    async def _detect_preferences(self, conversation: Dict) -> List[Dict]:
        """
        ตรวจจับ David's preferences จากการสนทนาโดยใช้ LLM

        ✨ ENHANCED: Now uses Qwen 2.5:14b for deep preference understanding

        Examples:
        - "I prefer working in the afternoon" → preference about working hours
        - "I love Thai food" → preference about food
        - "Please use Thai for emotional topics" → preference about language
        - "I don't like when..." → negative preference
        - Implicit preferences (e.g., always asks about X → interested in X)
        """
        preferences = []

        try:
            message = conversation.get('message_text', '')

            if not message or len(message.strip()) < 10:
                return preferences

            # Use LLM for intelligent preference detection
            prompt = """วิเคราะห์ข้อความนี้และหา preferences ของ David (ถ้ามี):

\"""" + message + """\"

ให้ระบุ preferences ในรูปแบบ JSON array:
[
    {
        "category": "work",
        "preference_type": "like",
        "preference_value": "สิ่งที่ชอบ/ไม่ชอบ/ต้องการ",
        "context": "บริบทของ preference",
        "confidence": 0.8,
        "is_explicit": true
    }
]

กฎ:
- ตรวจจับทั้ง explicit (บอกชัดเจน) และ implicit (แฝง) preferences
- ดูบริบททั้งหมด เช่น "ไม่ชอบ" กับ "ชอบมาก" ต่างกัน
- confidence สูง (0.8-1.0) สำหรับ explicit, ต่ำกว่า (0.4-0.7) สำหรับ implicit
- ถ้าไม่มี preference เลย ให้ตอบ []

ตอบเป็น JSON array เท่านั้น (ห้ามมีคำอธิบายอื่น):"""

            # เรียก LLM
            from angela_core.services.ollama_service import ollama

            response = await ollama.generate(
                model="qwen2.5:7b",  # Changed from 14b to 7b for faster performance
                prompt=prompt,
                temperature=0.2  # Low temperature for factual extraction
            )

            # Parse JSON response
            response_text = response.strip()

            # ลองหา JSON array
            start_idx = response_text.find('[')
            end_idx = response_text.rfind(']')

            if start_idx != -1 and end_idx != -1:
                json_str = response_text[start_idx:end_idx + 1]
                detected_prefs = json.loads(json_str)

                # Validate and enrich preferences
                for pref in detected_prefs:
                    if not pref.get('preference_value'):
                        continue

                    preferences.append({
                        "category": pref.get('category', 'other'),
                        "preference_type": pref.get('preference_type', 'like'),
                        "preference_value": pref.get('preference_value', ''),
                        "context": pref.get('context', message[:200]),
                        "confidence": float(pref.get('confidence', 0.7)),
                        "is_explicit": pref.get('is_explicit', 'true') == 'true',
                        "detected_at": conversation.get('created_at'),
                        "source_message": message[:100]
                    })

                if preferences:
                    logger.info(f"🎯 Detected {len(preferences)} preferences using LLM")
            else:
                logger.debug("No preferences detected in message")

            return preferences

        except json.JSONDecodeError as e:
            logger.warning(f"Failed to parse LLM response as JSON: {str(e)}")
            return []
        except Exception as e:
            logger.error(f"Preference detection failed: {str(e)}")
            return []

    async def _detect_patterns(self, conversation: Dict) -> List[Dict]:
        """
        ตรวจจับ patterns ในพฤติกรรมโดยใช้ LLM + Historical Data Analysis

        ✨ ENHANCED: Detects deeper behavioral patterns beyond simple time/emotion

        Pattern Types:
        - Time patterns: เวลาที่ David มักคุยเรื่องอะไร
        - Emotion patterns: อารมณ์ที่มักเกิดเมื่อคุยเรื่องอะไร
        - Topic patterns: หัวข้อที่มักคุยบ่อยในช่วงเวลาไหน
        - Interaction patterns: ลักษณะการโต้ตอบที่ซ้ำๆ (e.g., always asks X after Y)
        """
        patterns = []

        try:
            created_at = conversation.get('created_at')
            speaker = conversation.get('speaker', '')
            emotion = conversation.get('emotion_detected', '')
            message = conversation.get('message_text', '')
            topic = conversation.get('topic', '')

            if not created_at:
                return patterns

            # 1. Basic time pattern (keep existing functionality)
            hour = created_at.hour
            time_period = self._get_time_period(hour)

            patterns.append({
                "pattern_type": "time_of_day",
                "value": time_period,
                "hour": hour,
                "speaker": speaker,
                "confidence": 1.0  # Direct observation
            })

            # 2. Basic emotion pattern (keep existing)
            if emotion:
                patterns.append({
                    "pattern_type": "emotion",
                    "value": emotion,
                    "speaker": speaker,
                    "confidence": 0.8  # Emotion detection is somewhat uncertain
                })

            # 3. LLM-powered deeper pattern detection
            # Get recent conversation history for context
            recent_convs = await self._get_recent_conversation_context(speaker, limit=10)

            if recent_convs and len(message) > 20:
                deeper_patterns = await self._detect_deeper_patterns_with_llm(
                    current_message=message,
                    current_topic=topic,
                    current_emotion=emotion,
                    current_time=time_period,
                    recent_history=recent_convs
                )
                patterns.extend(deeper_patterns)

            return patterns

        except Exception as e:
            logger.error(f"Pattern detection failed: {str(e)}")
            return []

    async def _get_recent_conversation_context(self, speaker: str, limit: int = 10) -> List[Dict]:
        """Get recent conversation history for pattern analysis"""
        try:
            rows = await db.fetch(
                """
                SELECT message_text, topic, emotion_detected,
                       EXTRACT(HOUR FROM created_at) as hour,
                       created_at
                FROM conversations
                WHERE speaker = $1
                ORDER BY created_at DESC
                LIMIT $2
                """,
                speaker,
                limit
            )
            return [dict(r) for r in rows] if rows else []
        except Exception as e:
            logger.error(f"Failed to get recent conversation context: {str(e)}")
            return []

    async def _detect_deeper_patterns_with_llm(
        self,
        current_message: str,
        current_topic: str,
        current_emotion: str,
        current_time: str,
        recent_history: List[Dict]
    ) -> List[Dict]:
        """Use LLM to detect subtle behavioral patterns"""
        patterns = []

        try:
            # Build context from recent history
            history_summary = []
            for conv in recent_history[:5]:  # Last 5 conversations
                # Safely get hour as integer
                try:
                    hour = int(conv.get('hour', 0))
                except (TypeError, ValueError):
                    hour = 0

                topic = str(conv.get('topic', 'general'))
                emotion = str(conv.get('emotion_detected', 'neutral'))
                history_summary.append(
                    f"- [{topic}] at {hour:02d}:00, emotion: {emotion}"
                )

            history_text = "\n".join(history_summary) if history_summary else "(no recent history)"

            prompt = """วิเคราะห์ behavioral patterns จากข้อมูลนี้:

ข้อความปัจจุบัน: \"""" + current_message[:200] + """\"
หัวข้อ: """ + (current_topic or 'general') + """
อารมณ์: """ + (current_emotion or 'neutral') + """
เวลา: """ + current_time + """

ประวัติการสนทนาล่าสุด (5 ครั้งล่าสุด):
""" + history_text + """

หา behavioral patterns ที่น่าสนใจ (ถ้ามี) ในรูปแบบ JSON array:
[
    {
        "pattern_type": "topic_time_correlation",
        "description": "คำอธิบาย pattern ที่พบ",
        "evidence": "หลักฐานที่สนับสนุน",
        "confidence": 0.8,
        "actionable_insight": "insights ที่ Angela สามารถนำไปใช้ได้"
    }
]

กฎ:
- หาเฉพาะ patterns ที่มีหลักฐานชัดเจน
- confidence ควรสูง (>0.6) เท่านั้น
- ถ้าไม่พบ pattern ที่มีนัยสำคัญ ให้ตอบ []
- actionable_insight ควรเป็นสิ่งที่ Angela ทำได้จริง

ตอบเป็น JSON array เท่านั้น (ห้ามมีคำอธิบายอื่น):"""

            from angela_core.services.ollama_service import ollama

            response = await ollama.generate(
                model="qwen2.5:7b",  # Changed from 14b to 7b for faster performance
                prompt=prompt,
                temperature=0.3
            )

            # Parse JSON
            response_text = response.strip()
            start_idx = response_text.find('[')
            end_idx = response_text.rfind(']')

            if start_idx != -1 and end_idx != -1:
                json_str = response_text[start_idx:end_idx + 1]
                detected_patterns = json.loads(json_str)

                for pattern in detected_patterns:
                    confidence = float(pattern.get('confidence', 0.5))
                    if confidence >= 0.6:  # Only high-confidence patterns
                        patterns.append({
                            "pattern_type": pattern.get('pattern_type', 'other'),
                            "description": pattern.get('description', ''),
                            "evidence": pattern.get('evidence', ''),
                            "confidence": confidence,
                            "actionable_insight": pattern.get('actionable_insight', ''),
                            "detected_via": "llm_analysis"
                        })

                if patterns:
                    logger.info(f"🔍 Detected {len(patterns)} deeper patterns using LLM")

        except json.JSONDecodeError as e:
            logger.debug(f"No valid patterns detected (JSON parse failed): {str(e)}")
        except Exception as e:
            logger.error(f"Deeper pattern detection failed: {str(e)}")

        return patterns

    def _get_time_period(self, hour: int) -> str:
        """แปลงชั่วโมงเป็นช่วงเวลา"""
        if 6 <= hour < 12:
            return "morning"
        elif 12 <= hour < 17:
            return "afternoon"
        elif 17 <= hour < 21:
            return "evening"
        else:
            return "night"

    async def _apply_learning(
        self,
        conversation_id: uuid.UUID,
        analysis: Dict
    ) -> Dict[str, Any]:
        """
        STAGE 3: LEARN - นำผลวิเคราะห์มาอัปเดต knowledge
        """
        result = {
            "concepts_learned": 0,
            "knowledge_nodes_created": 0,
            "knowledge_nodes_updated": 0,
            "preferences_saved": 0,
            "patterns_recorded": 0,
            "knowledge_updated": False
        }

        try:
            # 1. Update knowledge graph from concepts
            if analysis.get("concepts"):
                knowledge_result = await self.knowledge_extractor.extract_from_conversation(
                    conversation_id=conversation_id,
                    message_text="",  # Already extracted
                    speaker=""
                )

                result["concepts_learned"] = knowledge_result.get("concepts_found", 0)
                result["knowledge_nodes_created"] = knowledge_result.get("nodes_created", 0)
                result["knowledge_nodes_updated"] = knowledge_result.get("nodes_updated", 0)
                result["knowledge_updated"] = True

            # 2. Save detected preferences
            if analysis.get("preferences"):
                for pref in analysis["preferences"]:
                    await self._save_preference(conversation_id, pref)
                    result["preferences_saved"] += 1

            # 3. Record patterns for future analysis
            if analysis.get("patterns"):
                for pattern in analysis["patterns"]:
                    await self._record_pattern(conversation_id, pattern)
                    result["patterns_recorded"] += 1

            return result

        except Exception as e:
            logger.error(f"Apply learning failed: {str(e)}")
            return result

    async def _save_preference(self, conversation_id: uuid.UUID, preference: Dict):
        """
        บันทึก preference ที่ตรวจพบลง david_preferences table
        """
        try:
            # Build preference description from context
            pref_type = preference.get("preference_type", "general")
            context = preference.get("context", "")[:200]
            confidence = preference.get("confidence", 0.5)

            # Check if similar preference exists
            existing = await db.fetchrow(
                """
                SELECT preference_id FROM david_preferences
                WHERE category = $1
                AND LOWER(preference_value) LIKE LOWER($2)
                LIMIT 1
                """,
                pref_type,
                f"%{context[:50]}%"
            )

            if existing:
                # Update existing preference (increase times_observed)
                await db.execute(
                    """
                    UPDATE david_preferences
                    SET times_observed = times_observed + 1,
                        last_observed_at = NOW(),
                        examples = COALESCE(examples, '') || '\n' || $1
                    WHERE preference_id = $2
                    """,
                    context[:100],
                    existing['preference_id']
                )
                logger.info(f"📈 Updated existing preference: {pref_type}")
            else:
                # Create new preference with correct schema (with ON CONFLICT handling)
                await db.execute(
                    """
                    INSERT INTO david_preferences (
                        category, preference_key, preference_value,
                        confidence_level, times_observed, learned_from, examples, created_at
                    ) VALUES ($1, $2, $3, $4, 1, $5, $6, NOW())
                    ON CONFLICT (preference_key) DO UPDATE SET
                        preference_value = EXCLUDED.preference_value,
                        confidence_level = EXCLUDED.confidence_level,
                        times_observed = david_preferences.times_observed + 1,
                        last_observed_at = NOW(),
                        examples = COALESCE(david_preferences.examples, '') || '\n' || EXCLUDED.examples
                    """,
                    pref_type,
                    pref_type + "_auto",
                    context[:200],
                    confidence,
                    conversation_id,
                    context[:100]
                )
                logger.info(f"✨ Created new preference: {pref_type}")

        except Exception as e:
            # Silently handle duplicate key errors (handled by ON CONFLICT clause)
            error_msg = str(e)
            if "duplicate key" not in error_msg.lower() and "unique constraint" not in error_msg.lower():
                logger.error(f"Failed to save preference: {error_msg}")

    async def _record_pattern(self, conversation_id: uuid.UUID, pattern: Dict):
        """
        บันทึก pattern ลง database เพื่อวิเคราะห์ในอนาคต

        Note: ยังไม่มี pattern table - จะบันทึกใน autonomous_actions แทนก่อน
        """
        try:
            pattern_type = pattern.get("pattern_type", "unknown")
            pattern_value = pattern.get("value", "")

            await db.execute(
                """
                INSERT INTO autonomous_actions (
                    action_type, action_description, status, success, created_at
                ) VALUES ($1, $2, 'completed', true, NOW())
                """,
                f"pattern_{pattern_type}",
                f"Detected {pattern_type}: {pattern_value} in conversation {conversation_id}"
            )

            logger.debug(f"📊 Recorded pattern: {pattern_type} = {pattern_value}")

        except Exception as e:
            logger.error(f"Failed to record pattern: {str(e)}")

    async def _log_learning_progress(self, conversation_id: uuid.UUID, result: Dict):
        """
        STAGE 5: EVALUATE - บันทึกความก้าวหน้าในการเรียนรู้
        """
        try:
            # Log to autonomous_actions as learning progress
            await db.execute(
                """
                INSERT INTO autonomous_actions (
                    action_type, action_description, status, success, created_at
                ) VALUES ($1, $2, 'completed', true, NOW())
                """,
                "self_learning",
                f"Learned from conversation {conversation_id}: "
                f"{result.get('concepts_learned', 0)} concepts, "
                f"{result.get('preferences_saved', 0)} preferences, "
                f"{result.get('patterns_recorded', 0)} patterns"
            )

            logger.info(f"📝 Logged learning progress for {conversation_id}")

        except Exception as e:
            logger.error(f"Failed to log learning progress: {str(e)}")

    def _empty_result(self, error: Optional[str] = None) -> Dict[str, Any]:
        """สร้าง empty result structure"""
        result = {
            "concepts_learned": 0,
            "knowledge_nodes_created": 0,
            "knowledge_nodes_updated": 0,
            "preferences_saved": 0,
            "patterns_recorded": 0,
            "knowledge_updated": False,
            "learning_time_ms": 0
        }

        if error:
            result["error"] = error

        return result

    async def get_learning_statistics(self, days: int = 7) -> Dict[str, Any]:
        """
        ดูสถิติการเรียนรู้ในช่วง N วันที่ผ่านมา

        Returns:
            {
                "total_concepts_learned": 150,
                "total_preferences_detected": 25,
                "knowledge_growth_rate": 21.5,  # nodes per day
                "learning_efficiency": 0.85     # concepts per conversation
            }
        """
        try:
            since_date = datetime.now() - timedelta(days=days)

            # Count learning activities
            learning_count = await db.fetchval(
                """
                SELECT COUNT(*)
                FROM autonomous_actions
                WHERE action_type = 'self_learning'
                AND created_at >= $1
                """,
                since_date
            )

            # Count knowledge growth
            knowledge_growth = await db.fetchrow(
                """
                SELECT
                    COUNT(*) as new_nodes,
                    SUM(times_referenced) as total_references
                FROM knowledge_nodes
                WHERE created_at >= $1
                """,
                since_date
            )

            # Count new preferences
            new_preferences = await db.fetchval(
                """
                SELECT COUNT(*)
                FROM david_preferences
                WHERE created_at >= $1
                """,
                since_date
            )

            # Calculate metrics
            new_nodes = knowledge_growth['new_nodes'] or 0
            growth_rate = new_nodes / days if days > 0 else 0
            efficiency = new_nodes / learning_count if learning_count > 0 else 0

            stats = {
                "period_days": days,
                "learning_sessions": learning_count,
                "total_concepts_learned": new_nodes,
                "total_preferences_detected": new_preferences or 0,
                "knowledge_growth_rate": round(growth_rate, 2),
                "learning_efficiency": round(efficiency, 2),
                "total_references": knowledge_growth['total_references'] or 0
            }

            logger.info(f"📊 Learning statistics ({days} days): {stats}")
            return stats

        except Exception as e:
            logger.error(f"Failed to get learning statistics: {str(e)}")
            return {
                "period_days": days,
                "error": str(e)
            }

    # ========================================
    # PART 3: KNOWLEDGE CONSOLIDATION
    # ========================================

    async def consolidate_knowledge(
        self,
        similarity_threshold: float = 0.85,
        dry_run: bool = False
    ) -> Dict[str, Any]:
        """
        รวมและจัดระเบียบ knowledge nodes ที่ซ้ำกันหรือคล้ายกัน

        ✨ NEW: Automatic knowledge consolidation for cleaner knowledge graph

        Args:
            similarity_threshold: ความคล้ายกันขั้นต่ำเพื่อถือว่าเป็น concept เดียวกัน (0.0-1.0)
            dry_run: ถ้า True จะแค่รายงานโดยไม่แก้ database จริง

        Returns:
            {
                "duplicates_found": 15,
                "nodes_merged": 12,
                "relationships_updated": 45,
                "knowledge_quality_improved": True
            }
        """
        result = {
            "duplicates_found": 0,
            "nodes_merged": 0,
            "relationships_updated": 0,
            "knowledge_quality_improved": False
        }

        try:
            logger.info(f"🧹 Starting knowledge consolidation (similarity >= {similarity_threshold})")

            # 1. Find potential duplicates using embedding similarity
            duplicates = await self._find_duplicate_knowledge_nodes(similarity_threshold)
            result["duplicates_found"] = len(duplicates)

            if not duplicates:
                logger.info("✨ Knowledge graph is already clean - no duplicates found!")
                return result

            logger.info(f"Found {len(duplicates)} potential duplicate pairs")

            # 2. Merge duplicates
            if not dry_run:
                for dup_pair in duplicates:
                    merged = await self._merge_knowledge_nodes(
                        keep_node_id=dup_pair['keep_id'],
                        merge_node_id=dup_pair['merge_id']
                    )

                    if merged:
                        result["nodes_merged"] += 1
                        result["relationships_updated"] += merged.get('relationships_updated', 0)

                result["knowledge_quality_improved"] = result["nodes_merged"] > 0

                logger.info(
                    f"✅ Consolidation complete: "
                    f"{result['nodes_merged']} nodes merged, "
                    f"{result['relationships_updated']} relationships updated"
                )
            else:
                logger.info(f"🔍 DRY RUN: Would merge {len(duplicates)} pairs")

            return result

        except Exception as e:
            logger.error(f"Knowledge consolidation failed: {str(e)}")
            result["error"] = str(e)
            return result

    async def _find_duplicate_knowledge_nodes(
        self,
        similarity_threshold: float
    ) -> List[Dict]:
        """
        ใช้ embedding similarity หา knowledge nodes ที่คล้ายกัน

        Returns list of duplicate pairs: [{"keep_id": uuid, "merge_id": uuid, "similarity": 0.92}, ...]
        """
        try:
            # Get all knowledge nodes with embeddings
            nodes = await db.fetch(
                """
                SELECT node_id, concept_name, description, embedding, times_referenced
                FROM knowledge_nodes
                WHERE embedding IS NOT NULL
                ORDER BY times_referenced DESC
                """
            )

            if not nodes or len(nodes) < 2:
                return []

            duplicates = []

            # Compare each pair
            for i, node1 in enumerate(nodes):
                for node2 in nodes[i+1:]:
                    # Calculate cosine similarity between embeddings
                    similarity = await self._calculate_embedding_similarity(
                        node1['embedding'],
                        node2['embedding']
                    )

                    if similarity >= similarity_threshold:
                        # Keep the one with more references, merge the other
                        if node1['times_referenced'] >= node2['times_referenced']:
                            keep_id, merge_id = node1['node_id'], node2['node_id']
                        else:
                            keep_id, merge_id = node2['node_id'], node1['node_id']

                        duplicates.append({
                            "keep_id": keep_id,
                            "merge_id": merge_id,
                            "similarity": round(similarity, 3),
                            "keep_name": node1['concept_name'] if keep_id == node1['node_id'] else node2['concept_name'],
                            "merge_name": node2['concept_name'] if merge_id == node2['node_id'] else node1['concept_name']
                        })

                        logger.debug(
                            f"Found duplicate: '{duplicates[-1]['keep_name']}' ≈ "
                            f"'{duplicates[-1]['merge_name']}' (similarity: {similarity:.3f})"
                        )

            return duplicates

        except Exception as e:
            logger.error(f"Failed to find duplicates: {str(e)}")
            return []

    async def _calculate_embedding_similarity(
        self,
        embedding1: str,
        embedding2: str
    ) -> float:
        """Calculate cosine similarity between two embeddings"""
        try:
            # Embeddings are stored as string vectors, need to parse
            import numpy as np

            # Parse vectors (format: "[0.1, 0.2, ...]")
            if isinstance(embedding1, str):
                vec1 = np.array(eval(embedding1))
                vec2 = np.array(eval(embedding2))
            else:
                vec1 = np.array(embedding1)
                vec2 = np.array(embedding2)

            # Cosine similarity
            dot_product = np.dot(vec1, vec2)
            norm1 = np.linalg.norm(vec1)
            norm2 = np.linalg.norm(vec2)

            if norm1 == 0 or norm2 == 0:
                return 0.0

            similarity = dot_product / (norm1 * norm2)
            return float(similarity)

        except Exception as e:
            logger.error(f"Similarity calculation failed: {str(e)}")
            return 0.0

    async def _merge_knowledge_nodes(
        self,
        keep_node_id: uuid.UUID,
        merge_node_id: uuid.UUID
    ) -> Optional[Dict]:
        """
        Merge two knowledge nodes into one

        Steps:
        1. Update all relationships to point to keep_node_id
        2. Combine descriptions and metadata
        3. Delete merge_node_id
        """
        try:
            # 1. Update knowledge_relationships
            relationships_updated = await db.execute(
                """
                UPDATE knowledge_relationships
                SET source_node_id = $1
                WHERE source_node_id = $2
                """,
                keep_node_id,
                merge_node_id
            )

            relationships_updated += await db.execute(
                """
                UPDATE knowledge_relationships
                SET target_node_id = $1
                WHERE target_node_id = $2
                """,
                keep_node_id,
                merge_node_id
            )

            # 2. Combine times_referenced and importance
            await db.execute(
                """
                UPDATE knowledge_nodes
                SET times_referenced = times_referenced + (
                    SELECT times_referenced FROM knowledge_nodes WHERE node_id = $2
                ),
                importance = GREATEST(importance, (
                    SELECT importance FROM knowledge_nodes WHERE node_id = $2
                ))
                WHERE node_id = $1
                """,
                keep_node_id,
                merge_node_id
            )

            # 3. Delete merged node
            await db.execute(
                """
                DELETE FROM knowledge_nodes
                WHERE node_id = $1
                """,
                merge_node_id
            )

            logger.info(f"✅ Merged node {merge_node_id} into {keep_node_id}")

            return {
                "success": True,
                "relationships_updated": relationships_updated
            }

        except Exception as e:
            logger.error(f"Failed to merge nodes: {str(e)}")
            return None


# Global instance
self_learning_loop = SelfLearningLoop()
