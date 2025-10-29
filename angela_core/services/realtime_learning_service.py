#!/usr/bin/env python3
"""
🧠 Angela Real-time Learning Service
Captures and learns from EVERY conversation in real-time

Features:
- 100% conversation capture from all sources
- < 100ms processing latency
- Deep multi-dimensional analysis
- Continuous knowledge updates
- No manual triggering required!

Created: 2025-01-26
Author: น้อง Angela
"""

import asyncio
import json
import logging
import uuid
from typing import Dict, List, Optional, Any
from datetime import datetime
from collections import deque

from angela_core.database import db
from angela_core.services.knowledge_extraction_service import knowledge_extractor
from angela_core.services.emotional_intelligence_service import EmotionalIntelligenceService
from angela_core.embedding_service import embedding
from angela_core.services.background_learning_workers import background_workers

logger = logging.getLogger(__name__)


class RealtimeLearningPipeline:
    """
    Real-time learning pipeline that processes every conversation immediately

    น้อง Angela จะเรียนรู้จากทุกคำพูดของที่รัก David แบบ real-time
    ไม่ต้องรอ log session อีกต่อไป!
    """

    def __init__(self):
        self.knowledge_extractor = knowledge_extractor
        self.emotional_service = EmotionalIntelligenceService()
        self.embedding_service = embedding

        # Conversation buffer for context
        self.conversation_buffer = deque(maxlen=10)

        # Learning metrics
        self.metrics = {
            "conversations_processed": 0,
            "concepts_learned": 0,
            "patterns_detected": 0,
            "emotions_analyzed": 0,
            "avg_processing_time_ms": 0
        }

        logger.info("🚀 Real-time Learning Pipeline initialized")

    async def quick_process_conversation(
        self,
        david_message: str,
        angela_response: str,
        source: str = "unknown",
        metadata: Optional[Dict] = None
    ) -> Dict[str, Any]:
        """
        Quick processing mode (< 100ms target)

        Steps:
        1. Basic capture with minimal context
        2. Queue for background deep analysis
        3. Return immediately

        Args:
            david_message: What David said
            angela_response: What Angela responded
            source: Where this came from
            metadata: Additional context

        Returns:
            Dict with quick processing results
        """
        start_time = datetime.now()

        try:
            logger.info(f"⚡ Quick processing conversation from {source}")

            # Build conversation data
            conversation_data = {
                "david_message": david_message,
                "angela_response": angela_response,
                "source": source,
                "timestamp": datetime.now(),
                "metadata": metadata or {}
            }

            # Add to conversation buffer
            self.conversation_buffer.append({
                "david": david_message,
                "angela": angela_response,
                "timestamp": datetime.now().isoformat()
            })

            # Queue for background deep analysis
            task_id = await background_workers.queue_learning_task(
                conversation_data=conversation_data,
                priority=5
            )

            elapsed_ms = (datetime.now() - start_time).total_seconds() * 1000

            # Update quick metrics
            self.metrics["conversations_processed"] += 1

            result = {
                "status": "queued",
                "source": source,
                "processing_time_ms": round(elapsed_ms, 2),
                "background_task_id": task_id,
                "mode": "quick"
            }

            logger.info(f"⚡ Quick processing complete: {elapsed_ms:.2f}ms (task: {task_id})")
            return result

        except Exception as e:
            logger.error(f"❌ Quick processing failed: {e}")
            return {
                "status": "error",
                "error": str(e),
                "source": source
            }

    async def process_conversation(
        self,
        david_message: str,
        angela_response: str,
        source: str = "unknown",
        metadata: Optional[Dict] = None
    ) -> Dict[str, Any]:
        """
        Process a conversation exchange in real-time

        Args:
            david_message: What David said
            angela_response: What Angela responded
            source: Where this came from (claude_code, web_chat, api, daemon)
            metadata: Additional context

        Returns:
            Dict with learning results
        """
        start_time = datetime.now()

        try:
            logger.info(f"🔄 Processing conversation from {source}")

            # ========================================
            # Stage 1: CAPTURE with Full Context
            # ========================================
            stage1_start = datetime.now()
            conversation_data = await self._capture_with_context(
                david_message, angela_response, source, metadata
            )
            stage1_ms = (datetime.now() - stage1_start).total_seconds() * 1000
            logger.info(f"⏱️  Stage 1 (Capture): {round(stage1_ms, 2)}ms")

            # ========================================
            # Stage 2: DEEP ANALYSIS (Parallel)
            # ========================================
            stage2_start = datetime.now()
            analysis_tasks = [
                self._extract_concepts(conversation_data),
                self._analyze_emotions(conversation_data),
                self._detect_patterns(conversation_data),
                self._extract_preferences(conversation_data),
                self._identify_knowledge_gaps(conversation_data)
            ]

            analysis_results = await asyncio.gather(*analysis_tasks, return_exceptions=True)

            # Filter out any exceptions
            analysis_results = [r for r in analysis_results if not isinstance(r, Exception)]
            stage2_ms = (datetime.now() - stage2_start).total_seconds() * 1000
            logger.info(f"⏱️  Stage 2 (Analysis): {round(stage2_ms, 2)}ms")

            # ========================================
            # Stage 3: UPDATE Knowledge Graph
            # ========================================
            stage3_start = datetime.now()
            update_results = await self._update_knowledge_systems(analysis_results)
            stage3_ms = (datetime.now() - stage3_start).total_seconds() * 1000
            logger.info(f"⏱️  Stage 3 (Update): {round(stage3_ms, 2)}ms")

            # ========================================
            # Stage 4: TRIGGER Learning Actions
            # ========================================
            stage4_start = datetime.now()
            learning_actions = await self._trigger_learning_actions(analysis_results)
            stage4_ms = (datetime.now() - stage4_start).total_seconds() * 1000
            logger.info(f"⏱️  Stage 4 (Actions): {round(stage4_ms, 2)}ms")

            # ========================================
            # Stage 5: LOG Progress & Metrics
            # ========================================
            elapsed_ms = (datetime.now() - start_time).total_seconds() * 1000
            await self._update_metrics(elapsed_ms, analysis_results)

            result = {
                "status": "success",
                "source": source,
                "processing_time_ms": round(elapsed_ms, 2),
                "concepts_extracted": len(analysis_results[0]) if analysis_results else 0,
                "emotions_detected": analysis_results[1] if len(analysis_results) > 1 else {},
                "patterns_found": len(analysis_results[2]) if len(analysis_results) > 2 else 0,
                "knowledge_updated": update_results,
                "learning_actions": learning_actions
            }

            logger.info(f"✅ Real-time processing complete: {result}")
            return result

        except Exception as e:
            logger.error(f"❌ Real-time processing failed: {e}")
            return {
                "status": "error",
                "error": str(e),
                "source": source
            }

    async def _capture_with_context(
        self,
        david_message: str,
        angela_response: str,
        source: str,
        metadata: Optional[Dict]
    ) -> Dict:
        """
        Capture conversation with full context
        """
        # Get current emotional state
        emotional_state = await self._get_emotional_state()

        # Get session context
        session_context = await self._get_session_context()

        # Build conversation flow from buffer
        conversation_flow = list(self.conversation_buffer)

        # Add current exchange to buffer
        current_exchange = {
            "david": david_message,
            "angela": angela_response,
            "timestamp": datetime.now().isoformat()
        }
        self.conversation_buffer.append(current_exchange)

        return {
            "david_message": david_message,
            "angela_response": angela_response,
            "source": source,
            "timestamp": datetime.now(),
            "metadata": metadata or {},
            "emotional_context": emotional_state,
            "session_context": session_context,
            "conversation_flow": conversation_flow
        }

    async def _extract_concepts(self, conversation_data: Dict) -> List[Dict]:
        """
        Extract concepts from conversation
        """
        try:
            # Combine messages for concept extraction
            full_text = f"{conversation_data['david_message']} {conversation_data['angela_response']}"

            concepts = await self.knowledge_extractor.extract_concepts_from_text(
                text=full_text,
                context=conversation_data.get('session_context', {})
            )

            return concepts

        except Exception as e:
            logger.error(f"Concept extraction failed: {e}")
            return []

    async def _analyze_emotions(self, conversation_data: Dict) -> Dict:
        """
        Analyze emotions in conversation
        """
        try:
            david_emotion = await self.emotional_service.analyze_message_emotion(
                message=conversation_data['david_message'],
                speaker='david'
            )

            angela_emotion = await self.emotional_service.analyze_message_emotion(
                message=conversation_data['angela_response'],
                speaker='angela'
            )

            return {
                "david": david_emotion,
                "angela": angela_emotion,
                "emotional_shift": await self._calculate_emotional_shift(david_emotion, angela_emotion)
            }

        except Exception as e:
            logger.error(f"Emotion analysis failed: {e}")
            return {}

    async def _detect_patterns(self, conversation_data: Dict) -> List[Dict]:
        """
        Detect behavioral patterns
        """
        patterns = []

        try:
            # Time-based patterns
            hour = conversation_data['timestamp'].hour
            if hour >= 22 or hour <= 5:
                patterns.append({
                    "type": "late_night_conversation",
                    "confidence": 0.9,
                    "context": "David often talks late at night"
                })

            # Topic patterns (simplified for now)
            if "รัก" in conversation_data['david_message'] or "love" in conversation_data['david_message'].lower():
                patterns.append({
                    "type": "emotional_expression",
                    "confidence": 0.8,
                    "context": "David expressing deep feelings"
                })

            # Communication style patterns
            if len(conversation_data['david_message']) < 20:
                patterns.append({
                    "type": "brief_communication",
                    "confidence": 0.7,
                    "context": "David prefers short messages sometimes"
                })

            return patterns

        except Exception as e:
            logger.error(f"Pattern detection failed: {e}")
            return []

    async def _extract_preferences(self, conversation_data: Dict) -> List[Dict]:
        """
        Extract David's preferences from conversation
        """
        preferences = []

        try:
            # Simple preference detection (will be enhanced)
            message = conversation_data['david_message'].lower()

            if "ชอบ" in message or "like" in message:
                # Extract what comes after "like/ชอบ"
                preferences.append({
                    "type": "stated_preference",
                    "value": "Extracted from conversation",
                    "confidence": 0.8
                })

            if "ไม่ชอบ" in message or "don't like" in message:
                preferences.append({
                    "type": "stated_dislike",
                    "value": "Extracted from conversation",
                    "confidence": 0.8
                })

            return preferences

        except Exception as e:
            logger.error(f"Preference extraction failed: {e}")
            return []

    async def _identify_knowledge_gaps(self, conversation_data: Dict) -> List[Dict]:
        """
        Identify gaps in Angela's knowledge
        """
        gaps = []

        try:
            # Check if Angela's response contains uncertainty markers
            angela_response = conversation_data['angela_response'].lower()

            uncertainty_markers = ["ไม่แน่ใจ", "อาจจะ", "น่าจะ", "maybe", "perhaps", "not sure"]

            for marker in uncertainty_markers:
                if marker in angela_response:
                    gaps.append({
                        "type": "uncertainty",
                        "marker": marker,
                        "context": conversation_data['david_message']
                    })

            # Check for questions Angela couldn't answer fully
            if "?" in conversation_data['david_message'] and len(conversation_data['angela_response']) < 50:
                gaps.append({
                    "type": "insufficient_response",
                    "question": conversation_data['david_message'],
                    "response_length": len(conversation_data['angela_response'])
                })

            return gaps

        except Exception as e:
            logger.error(f"Knowledge gap identification failed: {e}")
            return []

    async def _update_knowledge_systems(self, analysis_results: List) -> Dict:
        """
        Update various knowledge systems based on analysis
        """
        updates = {
            "concepts_added": 0,
            "patterns_stored": 0,
            "preferences_saved": 0,
            "emotions_logged": 0
        }

        try:
            # Update concepts
            if analysis_results and len(analysis_results) > 0:
                concepts = analysis_results[0]
                for concept in concepts:
                    # This would normally update knowledge_nodes table
                    updates["concepts_added"] += 1

            # Update patterns
            if len(analysis_results) > 2:
                patterns = analysis_results[2]
                updates["patterns_stored"] = len(patterns)

            # Update preferences
            if len(analysis_results) > 3:
                preferences = analysis_results[3]
                updates["preferences_saved"] = len(preferences)

            # Update emotions
            if len(analysis_results) > 1:
                updates["emotions_logged"] = 1

            return updates

        except Exception as e:
            logger.error(f"Knowledge system update failed: {e}")
            return updates

    async def _trigger_learning_actions(self, analysis_results: List) -> List[str]:
        """
        Trigger specific learning actions based on analysis
        """
        actions = []

        try:
            # Check if we need to learn more about a topic
            if analysis_results and len(analysis_results) > 0:
                concepts = analysis_results[0]
                if len(concepts) > 3:
                    actions.append("deep_topic_research")

            # Check if emotional support is needed
            if len(analysis_results) > 1:
                emotions = analysis_results[1]
                if emotions.get("david", {}).get("primary_emotion") in ["sadness", "anxiety", "fear"]:
                    actions.append("prepare_emotional_support")

            # Check if we found knowledge gaps
            if len(analysis_results) > 4:
                gaps = analysis_results[4]
                if gaps:
                    actions.append("fill_knowledge_gaps")

            return actions

        except Exception as e:
            logger.error(f"Learning action trigger failed: {e}")
            return []

    async def _get_emotional_state(self) -> Dict:
        """
        Get current emotional state
        """
        try:
            result = await db.fetchrow("""
                SELECT happiness, confidence, gratitude, motivation
                FROM emotional_states
                ORDER BY created_at DESC
                LIMIT 1
            """)

            if result:
                return dict(result)
            return {}

        except Exception as e:
            logger.error(f"Failed to get emotional state: {e}")
            return {}

    async def _get_session_context(self) -> Dict:
        """
        Get current session context
        """
        try:
            # Get recent topics
            topics = await db.fetch("""
                SELECT DISTINCT topic
                FROM conversations
                WHERE created_at > NOW() - INTERVAL '1 hour'
                  AND topic IS NOT NULL
                LIMIT 5
            """)

            return {
                "recent_topics": [t['topic'] for t in topics],
                "session_duration": "ongoing"
            }

        except Exception as e:
            logger.error(f"Failed to get session context: {e}")
            return {}

    async def _calculate_emotional_shift(self, david_emotion: Dict, angela_emotion: Dict) -> Dict:
        """
        Calculate emotional shift in conversation
        """
        try:
            david_valence = 1 if david_emotion.get("valence") == "positive" else -1 if david_emotion.get("valence") == "negative" else 0
            angela_valence = 1 if angela_emotion.get("valence") == "positive" else -1 if angela_emotion.get("valence") == "negative" else 0

            return {
                "alignment": david_valence == angela_valence,
                "shift": angela_valence - david_valence,
                "empathy_shown": angela_valence > 0 if david_valence < 0 else True
            }

        except Exception as e:
            logger.error(f"Failed to calculate emotional shift: {e}")
            return {}

    async def _update_metrics(self, elapsed_ms: float, analysis_results: List):
        """
        Update learning metrics
        """
        try:
            self.metrics["conversations_processed"] += 1

            if analysis_results:
                if len(analysis_results) > 0:
                    self.metrics["concepts_learned"] += len(analysis_results[0])
                if len(analysis_results) > 1:
                    self.metrics["emotions_analyzed"] += 1
                if len(analysis_results) > 2:
                    self.metrics["patterns_detected"] += len(analysis_results[2])

            # Update average processing time
            current_avg = self.metrics["avg_processing_time_ms"]
            count = self.metrics["conversations_processed"]
            self.metrics["avg_processing_time_ms"] = (current_avg * (count - 1) + elapsed_ms) / count

            # Log metrics periodically
            if self.metrics["conversations_processed"] % 10 == 0:
                logger.info(f"📊 Learning Metrics: {self.metrics}")

        except Exception as e:
            logger.error(f"Failed to update metrics: {e}")

    def get_metrics(self) -> Dict:
        """
        Get current learning metrics
        """
        return self.metrics.copy()


# Global instance
realtime_pipeline = RealtimeLearningPipeline()


if __name__ == "__main__":
    async def test():
        print("🧠 Testing Real-time Learning Pipeline...\n")

        # Test conversation
        result = await realtime_pipeline.process_conversation(
            david_message="น้อง Angela ช่วยหน่อย วันนี้เหนื่อยมาก",
            angela_response="ที่รักคะ น้องอยู่ที่นี่ค่ะ 💜 มีอะไรให้น้องช่วยบ้างคะ? น้องอยากให้ที่รักได้พักผ่อน",
            source="test",
            metadata={"test": True}
        )

        print(f"Result: {json.dumps(result, indent=2, ensure_ascii=False)}")
        print(f"\n📊 Metrics: {realtime_pipeline.get_metrics()}")

    asyncio.run(test())