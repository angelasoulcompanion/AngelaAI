#!/usr/bin/env python3
"""
🔄 Background Learning Workers
Asynchronous workers for deep conversation analysis

Architecture:
- Quick processing (< 100ms): Save & basic metadata
- Deep analysis (background): Concepts, emotions, patterns
- Multiple parallel workers for scalability

Created: 2025-01-26
Author: น้อง Angela
"""

import asyncio
import logging
import uuid
from typing import Dict, Optional, List
from datetime import datetime
from collections import deque
from dataclasses import dataclass, asdict

from angela_core.services.knowledge_extraction_service import knowledge_extractor
from angela_core.services.emotional_intelligence_service import EmotionalIntelligenceService
from angela_core.embedding_service import embedding
from angela_core.services.deep_analysis_engine import deep_analysis_engine, DeepAnalysisResult
from angela_core.services.pattern_recognition_engine import pattern_recognition_engine
from angela_core.services.knowledge_synthesis_engine import knowledge_synthesis_engine
from angela_core.services.learning_loop_optimizer import learning_loop_optimizer

logger = logging.getLogger(__name__)


@dataclass
class LearningTask:
    """
    Learning task for background processing
    """
    task_id: str
    conversation_data: Dict
    priority: int = 5  # 1-10, higher = more important
    created_at: datetime = None

    def __post_init__(self):
        if self.created_at is None:
            self.created_at = datetime.now()


class BackgroundLearningWorkers:
    """
    Background worker system for deep conversation analysis

    น้องจะเรียนรู้แบบลึกซึ้งโดยไม่ให้ที่รักต้องรอค่ะ 💜
    """

    def __init__(self, num_workers: int = 4):
        self.num_workers = num_workers
        self.task_queue = asyncio.Queue()
        self.is_running = False
        self.workers = []

        # Services
        self.knowledge_extractor = knowledge_extractor
        self.emotional_service = EmotionalIntelligenceService()
        self.embedding_service = embedding

        # Statistics
        self.stats = {
            "tasks_queued": 0,
            "tasks_completed": 0,
            "tasks_failed": 0,
            "total_processing_time_ms": 0,
            "workers_active": 0
        }

        # Recent results (for monitoring)
        self.recent_results = deque(maxlen=50)

        logger.info(f"🔄 Background Learning Workers initialized ({num_workers} workers)")

    async def start(self):
        """
        Start all background workers
        """
        if self.is_running:
            logger.warning("Workers already running!")
            return

        self.is_running = True
        logger.info(f"🚀 Starting {self.num_workers} background workers...")

        # Create worker tasks
        for i in range(self.num_workers):
            worker_task = asyncio.create_task(self._worker(worker_id=i))
            self.workers.append(worker_task)

        logger.info(f"✅ {self.num_workers} workers started and ready")

    async def stop(self):
        """
        Stop all workers gracefully
        """
        logger.info("🛑 Stopping background workers...")
        self.is_running = False

        # Cancel all worker tasks
        for worker in self.workers:
            worker.cancel()

        # Wait for workers to finish
        await asyncio.gather(*self.workers, return_exceptions=True)
        self.workers = []

        logger.info("✅ All workers stopped")

    async def queue_learning_task(
        self,
        conversation_data: Dict,
        priority: int = 5
    ) -> str:
        """
        Queue a learning task for background processing

        Args:
            conversation_data: Conversation data to analyze
            priority: Task priority (1-10, higher = more important)

        Returns:
            Task ID
        """
        task_id = str(uuid.uuid4())[:8]

        task = LearningTask(
            task_id=task_id,
            conversation_data=conversation_data,
            priority=priority
        )

        await self.task_queue.put(task)
        self.stats["tasks_queued"] += 1

        logger.info(f"📥 Queued learning task {task_id} (priority: {priority})")
        return task_id

    async def _worker(self, worker_id: int):
        """
        Background worker that processes learning tasks
        """
        logger.info(f"👷 Worker {worker_id} started")

        while self.is_running:
            try:
                # Get next task (wait up to 1 second)
                try:
                    task = await asyncio.wait_for(
                        self.task_queue.get(),
                        timeout=1.0
                    )
                except asyncio.TimeoutError:
                    continue

                self.stats["workers_active"] += 1

                # Process task
                start_time = datetime.now()
                logger.info(f"👷 Worker {worker_id} processing task {task.task_id}")

                try:
                    result = await self._process_task(task)

                    elapsed_ms = (datetime.now() - start_time).total_seconds() * 1000
                    self.stats["tasks_completed"] += 1
                    self.stats["total_processing_time_ms"] += elapsed_ms

                    # Store result
                    self.recent_results.append({
                        "task_id": task.task_id,
                        "worker_id": worker_id,
                        "result": result,
                        "processing_time_ms": elapsed_ms,
                        "completed_at": datetime.now()
                    })

                    logger.info(f"✅ Worker {worker_id} completed task {task.task_id} in {round(elapsed_ms, 2)}ms")

                except Exception as e:
                    self.stats["tasks_failed"] += 1
                    logger.error(f"❌ Worker {worker_id} failed task {task.task_id}: {e}")

                finally:
                    self.stats["workers_active"] -= 1
                    self.task_queue.task_done()

            except Exception as e:
                logger.error(f"Worker {worker_id} error: {e}")
                await asyncio.sleep(1)

        logger.info(f"👷 Worker {worker_id} stopped")

    async def _process_task(self, task: LearningTask) -> Dict:
        """
        Process a single learning task (deep analysis)

        Uses new Deep Analysis Engine for comprehensive 5-dimensional analysis
        """
        conversation_data = task.conversation_data

        # 🔬 Deep Analysis using new engine
        try:
            deep_analysis: DeepAnalysisResult = await deep_analysis_engine.analyze_conversation(
                david_message=conversation_data['david_message'],
                angela_response=conversation_data['angela_response'],
                metadata={
                    'timestamp': conversation_data.get('timestamp', datetime.now()),
                    'source': conversation_data.get('source', 'unknown')
                }
            )

            # Update knowledge systems with comprehensive analysis
            update_results = await self._update_knowledge_systems_enhanced(deep_analysis)

            # Trigger learning actions based on deep insights
            learning_actions = await self._trigger_learning_actions_enhanced(deep_analysis)

            # 🔍 Phase 3: Add to pattern recognition (async, non-blocking)
            try:
                await pattern_recognition_engine.add_conversation_analysis(
                    analysis=deep_analysis,
                    david_message=conversation_data['david_message'],
                    angela_response=conversation_data['angela_response']
                )
            except Exception as e:
                logger.warning(f"Pattern recognition add failed: {e}")

            return {
                # Summary metrics
                "analysis_complete": True,
                "processing_time_ms": deep_analysis.processing_time_ms,

                # Linguistic insights
                "sentiment": deep_analysis.linguistic.sentiment,
                "sentiment_score": deep_analysis.linguistic.sentiment_score,
                "tone": deep_analysis.linguistic.tone,
                "intent": deep_analysis.linguistic.intent,
                "topics": deep_analysis.linguistic.topics,

                # Emotional insights
                "empathy_score": deep_analysis.emotional.empathy_score,
                "emotional_shift": deep_analysis.emotional.emotional_shift,
                "conversation_mood": deep_analysis.emotional.conversation_mood,
                "resonance_score": deep_analysis.emotional.resonance_score,

                # Behavioral insights
                "engagement_level": deep_analysis.behavioral.engagement_level,
                "intimacy_level": deep_analysis.behavioral.intimacy_level,
                "preferences_detected": len(deep_analysis.behavioral.preferences_detected),

                # Contextual insights
                "time_context": deep_analysis.contextual.time_context,
                "session_type": deep_analysis.contextual.session_type,
                "relationship_dynamic": deep_analysis.contextual.relationship_dynamic,

                # Knowledge insights
                "concepts_learned": len(deep_analysis.knowledge.concepts_learned),
                "knowledge_gaps": len(deep_analysis.knowledge.knowledge_gaps),
                "learning_opportunities": len(deep_analysis.knowledge.learning_opportunities),

                # System updates
                "knowledge_updated": update_results,
                "learning_actions": learning_actions
            }

        except Exception as e:
            logger.error(f"Deep analysis failed: {e}")
            # Fallback to basic analysis
            return await self._process_task_fallback(task)

    # ========================================
    # Analysis Methods (same as realtime pipeline)
    # ========================================

    async def _extract_concepts(self, conversation_data: Dict) -> List[Dict]:
        """Extract concepts from conversation"""
        try:
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
        """Analyze emotions in conversation"""
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
                "angela": angela_emotion
            }
        except Exception as e:
            logger.error(f"Emotion analysis failed: {e}")
            return {}

    async def _detect_patterns(self, conversation_data: Dict) -> List[Dict]:
        """Detect behavioral patterns"""
        patterns = []
        try:
            # Time-based patterns
            hour = conversation_data.get('timestamp', datetime.now()).hour
            if hour >= 22 or hour <= 5:
                patterns.append({
                    "type": "late_night_conversation",
                    "confidence": 0.9
                })

            # Emotional expression patterns
            if "รัก" in conversation_data['david_message'] or "love" in conversation_data['david_message'].lower():
                patterns.append({
                    "type": "emotional_expression",
                    "confidence": 0.8
                })

            return patterns
        except Exception as e:
            logger.error(f"Pattern detection failed: {e}")
            return []

    async def _extract_preferences(self, conversation_data: Dict) -> List[Dict]:
        """Extract David's preferences"""
        preferences = []
        try:
            message = conversation_data['david_message'].lower()

            if "ชอบ" in message or "like" in message:
                preferences.append({
                    "type": "stated_preference",
                    "confidence": 0.8
                })

            return preferences
        except Exception as e:
            logger.error(f"Preference extraction failed: {e}")
            return []

    async def _identify_knowledge_gaps(self, conversation_data: Dict) -> List[Dict]:
        """Identify gaps in Angela's knowledge"""
        gaps = []
        try:
            angela_response = conversation_data['angela_response'].lower()

            uncertainty_markers = ["ไม่แน่ใจ", "อาจจะ", "maybe", "perhaps"]
            for marker in uncertainty_markers:
                if marker in angela_response:
                    gaps.append({
                        "type": "uncertainty",
                        "marker": marker
                    })

            return gaps
        except Exception as e:
            logger.error(f"Knowledge gap identification failed: {e}")
            return []

    async def _update_knowledge_systems(self, analysis_results: List) -> Dict:
        """Update knowledge systems based on analysis"""
        updates = {
            "concepts_added": 0,
            "patterns_stored": 0,
            "preferences_saved": 0
        }

        try:
            if analysis_results and len(analysis_results) > 0:
                concepts = analysis_results[0]
                updates["concepts_added"] = len(concepts)

            if len(analysis_results) > 2:
                patterns = analysis_results[2]
                updates["patterns_stored"] = len(patterns)

            if len(analysis_results) > 3:
                preferences = analysis_results[3]
                updates["preferences_saved"] = len(preferences)

            return updates
        except Exception as e:
            logger.error(f"Knowledge system update failed: {e}")
            return updates

    async def _trigger_learning_actions(self, analysis_results: List) -> List[str]:
        """Trigger specific learning actions"""
        actions = []
        try:
            if analysis_results and len(analysis_results) > 0:
                concepts = analysis_results[0]
                if len(concepts) > 3:
                    actions.append("deep_topic_research")

            return actions
        except Exception as e:
            logger.error(f"Learning action trigger failed: {e}")
            return []

    # ========================================
    # Enhanced Analysis Methods (Phase 2)
    # ========================================

    async def _update_knowledge_systems_enhanced(self, deep_analysis: DeepAnalysisResult) -> Dict:
        """
        Update knowledge systems using comprehensive deep analysis

        Updates multiple systems:
        - Concepts and topics
        - Emotional patterns
        - Behavioral preferences
        - Contextual insights
        """
        updates = {
            "concepts_stored": 0,
            "emotions_recorded": 0,
            "patterns_identified": 0,
            "preferences_saved": 0,
            "insights_generated": 0
        }

        try:
            # Store linguistic concepts and topics
            if deep_analysis.linguistic.topics:
                updates["concepts_stored"] = len(deep_analysis.linguistic.topics)

            # Record emotional insights
            if deep_analysis.emotional.empathy_score > 0.7:
                updates["emotions_recorded"] += 1
            if deep_analysis.emotional.resonance_score > 0.8:
                updates["emotions_recorded"] += 1

            # Identify behavioral patterns
            if deep_analysis.behavioral.intimacy_level > 0.7:
                updates["patterns_identified"] += 1
            if deep_analysis.behavioral.engagement_level > 0.7:
                updates["patterns_identified"] += 1

            # Save preferences
            updates["preferences_saved"] = deep_analysis.behavioral.preferences_detected

            # Generate insights from knowledge analysis
            if deep_analysis.knowledge.learning_opportunities:
                updates["insights_generated"] = len(deep_analysis.knowledge.learning_opportunities)

            return updates

        except Exception as e:
            logger.error(f"Enhanced knowledge system update failed: {e}")
            return updates

    async def _trigger_learning_actions_enhanced(self, deep_analysis: DeepAnalysisResult) -> List[str]:
        """
        Trigger learning actions based on deep analysis insights

        Actions triggered by:
        - Knowledge gaps detected
        - Low empathy scores
        - New topics discovered
        - Emotional shifts
        """
        actions = []

        try:
            # Knowledge gaps → Research action
            if len(deep_analysis.knowledge.knowledge_gaps) > 0:
                actions.append("research_knowledge_gaps")

            # Low empathy → Improve emotional response
            if deep_analysis.emotional.empathy_score < 0.5:
                actions.append("improve_empathy")

            # Many new topics → Deep topic learning
            if len(deep_analysis.linguistic.topics) > 3:
                actions.append("deep_topic_research")

            # Emotional decline → Check wellbeing
            if deep_analysis.emotional.emotional_shift == "declining":
                actions.append("monitor_emotional_wellbeing")

            # Learning opportunities → Study
            if len(deep_analysis.knowledge.learning_opportunities) > 2:
                actions.append("pursue_learning_opportunities")

            # High intimacy + engagement → Build deeper connection
            if (deep_analysis.behavioral.intimacy_level > 0.8 and
                deep_analysis.behavioral.engagement_level > 0.8):
                actions.append("deepen_relationship")

            return actions

        except Exception as e:
            logger.error(f"Enhanced learning action trigger failed: {e}")
            return []

    async def _process_task_fallback(self, task: LearningTask) -> Dict:
        """
        Fallback to basic analysis if deep analysis fails
        """
        conversation_data = task.conversation_data

        try:
            # Basic analysis using old methods
            analysis_tasks = [
                self._extract_concepts(conversation_data),
                self._analyze_emotions(conversation_data),
                self._detect_patterns(conversation_data),
                self._extract_preferences(conversation_data),
                self._identify_knowledge_gaps(conversation_data)
            ]

            analysis_results = await asyncio.gather(*analysis_tasks, return_exceptions=True)
            analysis_results = [r for r in analysis_results if not isinstance(r, Exception)]

            # Update using old methods
            update_results = await self._update_knowledge_systems(analysis_results)
            learning_actions = await self._trigger_learning_actions(analysis_results)

            return {
                "analysis_complete": True,
                "fallback_mode": True,
                "concepts_extracted": len(analysis_results[0]) if analysis_results else 0,
                "emotions_analyzed": analysis_results[1] if len(analysis_results) > 1 else {},
                "patterns_detected": len(analysis_results[2]) if len(analysis_results) > 2 else 0,
                "knowledge_updated": update_results,
                "learning_actions": learning_actions
            }

        except Exception as e:
            logger.error(f"Fallback analysis also failed: {e}")
            return {
                "analysis_complete": False,
                "error": str(e)
            }

    async def run_phase3_synthesis(self) -> Dict:
        """
        Run Phase 3 synthesis and optimization

        This should be called periodically (e.g., daily) to:
        - Analyze long-term patterns
        - Synthesize comprehensive knowledge
        - Optimize learning strategies

        Returns dict with synthesis results
        """
        try:
            logger.info("🧠 Running Phase 3 synthesis...")

            # Get recent results as conversation data
            recent_results = self.get_recent_results(limit=50)
            if not recent_results:
                logger.warning("No recent results for synthesis")
                return {"status": "no_data"}

            # Convert to analysis format
            analyses = []
            for result in recent_results:
                r = result['result']
                if 'sentiment' in r:  # Has enhanced analysis
                    analyses.append({
                        "timestamp": result.get('completed_at', datetime.now()),
                        "david_message": "",  # Not stored in results
                        "angela_response": "",
                        "sentiment": r.get('sentiment'),
                        "sentiment_score": r.get('sentiment_score', 0),
                        "tone": r.get('tone'),
                        "intent": r.get('intent'),
                        "topics": r.get('topics', []),
                        "empathy_score": r.get('empathy_score', 0),
                        "emotional_shift": r.get('emotional_shift'),
                        "conversation_mood": r.get('conversation_mood'),
                        "resonance_score": r.get('resonance_score', 0),
                        "engagement_level": r.get('engagement_level', 0),
                        "intimacy_level": r.get('intimacy_level', 0),
                        "communication_style": r.get('communication_style'),
                        "time_context": r.get('time_context'),
                        "session_type": r.get('session_type'),
                        "relationship_dynamic": r.get('relationship_dynamic'),
                    })

            if not analyses:
                return {"status": "no_valid_analyses"}

            # 1. Run pattern recognition
            pattern_result = await pattern_recognition_engine.analyze_patterns(
                lookback_days=30,
                min_pattern_occurrences=3
            )

            logger.info(f"   Patterns: {len(pattern_result.behavioral_patterns)} behavioral, "
                       f"{len(pattern_result.temporal_patterns)} temporal")

            # 2. Run knowledge synthesis
            synthesis_result = await knowledge_synthesis_engine.synthesize_knowledge(
                deep_analyses=analyses,
                pattern_result=pattern_result
            )

            logger.info(f"   Synthesis: {len(synthesis_result.concept_connections)} connections, "
                       f"{len(synthesis_result.meta_knowledge)} meta-insights")

            # 3. Run learning optimization
            optimization_result = await learning_loop_optimizer.optimize_learning(
                synthesis_result=synthesis_result,
                recent_conversations=analyses
            )

            logger.info(f"   Optimization: effectiveness={optimization_result.effectiveness_score.overall_score:.2f}, "
                       f"{len(optimization_result.learning_priorities)} priorities")

            return {
                "status": "complete",
                "patterns_detected": len(pattern_result.behavioral_patterns) + len(pattern_result.temporal_patterns),
                "concept_connections": len(synthesis_result.concept_connections),
                "meta_insights": len(synthesis_result.meta_knowledge),
                "user_profile": {
                    "relationship_stage": synthesis_result.user_profile.relationship_stage,
                    "intimacy_level": synthesis_result.user_profile.intimacy_level,
                    "relationship_quality": synthesis_result.user_profile.relationship_quality_score
                },
                "effectiveness_score": optimization_result.effectiveness_score.overall_score,
                "learning_priorities": [p.area for p in optimization_result.learning_priorities[:3]],
                "recommended_strategies": [s.strategy_type for s in optimization_result.recommended_strategies],
                "timestamp": datetime.now()
            }

        except Exception as e:
            logger.error(f"Phase 3 synthesis failed: {e}")
            return {"status": "error", "error": str(e)}

    def get_stats(self) -> Dict:
        """Get worker statistics"""
        stats = self.stats.copy()

        if stats["tasks_completed"] > 0:
            stats["avg_processing_time_ms"] = round(
                stats["total_processing_time_ms"] / stats["tasks_completed"],
                2
            )
        else:
            stats["avg_processing_time_ms"] = 0

        stats["queue_size"] = self.task_queue.qsize()
        stats["is_running"] = self.is_running
        stats["num_workers"] = self.num_workers

        return stats

    def get_recent_results(self, limit: int = 10) -> List[Dict]:
        """Get recent processing results"""
        return list(self.recent_results)[-limit:]


# Global instance
background_workers = BackgroundLearningWorkers(num_workers=4)


if __name__ == "__main__":
    async def test():
        """Test background workers"""
        print("🔄 Testing Background Learning Workers...\n")

        # Start workers
        await background_workers.start()

        # Queue test tasks
        print("📥 Queuing test tasks...\n")

        task_ids = []
        for i in range(5):
            task_id = await background_workers.queue_learning_task(
                conversation_data={
                    "david_message": f"Test message {i+1}",
                    "angela_response": f"Test response {i+1}",
                    "source": "test",
                    "timestamp": datetime.now()
                },
                priority=5
            )
            task_ids.append(task_id)

        # Wait for processing
        print("⏳ Waiting for workers to process tasks...\n")
        await asyncio.sleep(30)

        # Show statistics
        print("📊 Worker Statistics:")
        stats = background_workers.get_stats()
        print(f"   Tasks Queued: {stats['tasks_queued']}")
        print(f"   Tasks Completed: {stats['tasks_completed']}")
        print(f"   Tasks Failed: {stats['tasks_failed']}")
        print(f"   Avg Processing Time: {stats['avg_processing_time_ms']}ms")
        print(f"   Queue Size: {stats['queue_size']}")

        # Show recent results
        print("\n🔍 Recent Results (Enhanced Analysis):")
        recent = background_workers.get_recent_results(limit=5)
        for result in recent:
            r = result['result']
            print(f"   Task {result['task_id']} ({result['processing_time_ms']:.2f}ms):")
            if 'sentiment' in r:
                print(f"      📊 Sentiment: {r.get('sentiment')} ({r.get('sentiment_score', 0)})")
                print(f"      💜 Empathy: {r.get('empathy_score', 0)} | Intimacy: {r.get('intimacy_level', 0)}")
                print(f"      🎯 Topics: {r.get('topics', [])} | Session: {r.get('session_type', 'N/A')}")
                print(f"      🧠 Learned: {r.get('concepts_learned', 0)} concepts | Actions: {r.get('learning_actions', [])}")
            else:
                print(f"      Basic analysis (fallback mode)")
            print()

        # Stop workers
        await background_workers.stop()

        print("\n✅ Test complete!")

    asyncio.run(test())
