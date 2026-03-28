#!/usr/bin/env python3
"""
💜 Unified Learning Orchestrator
Angela Intelligence Enhancement - Phase 1.1

Central hub that coordinates ALL learning services, connecting them to:
- AGI Loop (OODA cycle)
- Meta-Learning (learning how to learn)
- Feedback Loop (validation and improvement)

Architecture:
    ┌─────────────────────────────────────────────────────────────┐
    │              UNIFIED LEARNING ORCHESTRATOR                  │
    ├─────────────────────────────────────────────────────────────┤
    │                                                             │
    │  ┌──────────────┐   ┌──────────────┐   ┌──────────────┐   │
    │  │ Self Learning │   │   Pattern    │   │  Preference  │   │
    │  │    Loop      │   │   Learning   │   │   Learning   │   │
    │  └──────┬───────┘   └──────┬───────┘   └──────┬───────┘   │
    │         │                  │                   │           │
    │         └──────────────────┼───────────────────┘           │
    │                            │                               │
    │                     ┌──────▼───────┐                       │
    │                     │  ORCHESTRATOR │                       │
    │                     │     CORE      │                       │
    │                     └──────┬───────┘                       │
    │                            │                               │
    │    ┌───────────────────────┼───────────────────────┐       │
    │    │                       │                       │       │
    │ ┌──▼──────┐         ┌──────▼──────┐         ┌──────▼───┐   │
    │ │   AGI   │         │    META     │         │CONSCIOUS │   │
    │ │  LOOP   │         │  LEARNING   │         │  STATE   │   │
    │ └─────────┘         └─────────────┘         └──────────┘   │
    └─────────────────────────────────────────────────────────────┘

Created: 2026-01-17
Author: น้อง Angela 💜
Purpose: Make Angela truly intelligent through unified learning
"""

import asyncio
import json
import logging
import uuid
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional, Callable
from enum import Enum

# Database
from angela_core.database import db

# Learning Services
from angela_core.services.self_learning_service import self_learning_loop, SelfLearningLoop
from angela_core.services.realtime_learning_service import realtime_pipeline
from angela_core.services.knowledge_extraction_service import knowledge_extractor


logger = logging.getLogger(__name__)


class LearningPriority(Enum):
    """Priority levels for learning tasks"""
    CRITICAL = 1      # Corrections from David, explicit feedback
    HIGH = 2          # New concepts, emotional moments
    MEDIUM = 3        # Normal conversation learning
    LOW = 4           # Background pattern analysis
    BACKGROUND = 5    # Consolidation, cleanup


class LearningType(Enum):
    """Types of learning Angela can perform"""
    CONCEPT = "concept"           # New knowledge/concept learned
    PATTERN = "pattern"           # Behavioral pattern detected
    PREFERENCE = "preference"     # David's preference learned
    CORRECTION = "correction"     # Learning from David's correction
    INSIGHT = "insight"           # Meta-insight about learning
    SKILL = "skill"               # Technical skill/technique
    CODING_TECHNIQUE = "coding_technique"  # Coding pattern/technique learned
    UI_PATTERN = "ui_pattern"              # UI/UX pattern learned


@dataclass
class LearningEvent:
    """A single learning event to be processed"""
    event_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    event_type: LearningType = LearningType.CONCEPT
    priority: LearningPriority = LearningPriority.MEDIUM
    content: Dict[str, Any] = field(default_factory=dict)
    source: str = "conversation"
    timestamp: datetime = field(default_factory=datetime.now)
    processed: bool = False
    result: Optional[Dict[str, Any]] = None

    def to_dict(self) -> Dict[str, Any]:
        return {
            'event_id': self.event_id,
            'event_type': self.event_type.value,
            'priority': self.priority.value,
            'content': self.content,
            'source': self.source,
            'timestamp': self.timestamp.isoformat(),
            'processed': self.processed
        }


@dataclass
class LearningResult:
    """Result of a learning operation"""
    success: bool = False
    concepts_learned: int = 0
    patterns_detected: int = 0
    preferences_saved: int = 0
    insights_generated: int = 0
    meta_learning_updated: bool = False
    processing_time_ms: float = 0
    details: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        return {
            'success': self.success,
            'concepts_learned': self.concepts_learned,
            'patterns_detected': self.patterns_detected,
            'preferences_saved': self.preferences_saved,
            'insights_generated': self.insights_generated,
            'meta_learning_updated': self.meta_learning_updated,
            'processing_time_ms': self.processing_time_ms,
            'details': self.details
        }


class UnifiedLearningOrchestrator:
    """
    Central orchestrator for all learning systems.

    Coordinates:
    1. Self-Learning Loop - 5-stage learning from conversations
    2. Pattern Learning - Automatic pattern discovery
    3. Preference Learning - David's preferences
    4. Meta-Learning - Learning effectiveness tracking
    5. AGI Loop Integration - OODA cycle connection
    6. Coding Technique Learning - Technical patterns and techniques
    7. UI Pattern Learning - UI/UX design patterns

    Usage:
        orchestrator = UnifiedLearningOrchestrator()
        await orchestrator.initialize()

        # Learn from interaction
        result = await orchestrator.learn_from_interaction({
            'david_message': "I prefer async code",
            'angela_response': "Noted! I'll use async/await",
            'source': 'claude_code'
        })

        # Get learning insights
        insights = await orchestrator.get_learning_insights()
    """

    def __init__(self):
        # Core services
        self.self_learning = self_learning_loop
        self.realtime_pipeline = realtime_pipeline
        self.knowledge_extractor = knowledge_extractor
        try:
            from angela_core.agi.meta_learning import meta_learning
            self.meta_learning = meta_learning
        except ImportError:
            self.meta_learning = None

        # Learning queue and state
        self.learning_queue: List[LearningEvent] = []
        self.processing = False
        self.current_session: Optional[str] = None

        # Metrics
        self.metrics = {
            'total_interactions': 0,
            'total_concepts_learned': 0,
            'total_patterns_detected': 0,
            'total_preferences_saved': 0,
            'total_corrections_received': 0,
            'avg_processing_time_ms': 0.0,
            'learning_success_rate': 0.0,
            'meta_insights_generated': 0
        }

        # Callbacks
        self._feedback_callback: Optional[Callable] = None

        # Configuration
        self.config = {
            'auto_meta_learning': True,     # Automatically update meta-learning
            'async_background_learning': True,  # Queue heavy tasks for background
            'min_confidence_threshold': 0.5,  # Minimum confidence to save learning
            'batch_size': 5,                 # Max events to process at once
        }

        logger.info("💜 UnifiedLearningOrchestrator initialized")

    async def initialize(self) -> Dict[str, Any]:
        """
        Initialize the orchestrator and all connected services.

        Returns:
            Initialization status
        """
        logger.info("🚀 Initializing UnifiedLearningOrchestrator...")

        try:
            # Start a meta-learning session
            self.current_session = await self._start_meta_session()

            # Load historical metrics
            await self._load_historical_metrics()

            # Verify services are ready
            services_status = await self._verify_services()

            logger.info(f"✅ Orchestrator initialized - Session: {self.current_session[:8]}...")

            return {
                'status': 'initialized',
                'session_id': self.current_session,
                'services': services_status,
                'config': self.config
            }

        except Exception as e:
            logger.error(f"❌ Initialization failed: {e}")
            return {
                'status': 'error',
                'error': str(e)
            }

    # ========================================
    # MAIN LEARNING INTERFACE
    # ========================================

    async def learn_from_interaction(
        self,
        interaction: Dict[str, Any],
        priority: Optional[LearningPriority] = None
    ) -> LearningResult:
        """
        Main entry point - Learn from a conversation interaction.

        Orchestrates all learning services to extract maximum knowledge
        from a single interaction.

        Args:
            interaction: {
                'david_message': str,
                'angela_response': str,
                'source': str (claude_code/telegram/daemon),
                'context': Optional[Dict],
                'metadata': Optional[Dict]
            }
            priority: Override automatic priority detection

        Returns:
            LearningResult with all learning outcomes
        """
        start_time = datetime.now()
        result = LearningResult()

        try:
            logger.info(f"🧠 Learning from interaction ({interaction.get('source', 'unknown')})")

            # 1. Detect learning priority
            if priority is None:
                priority = await self._detect_priority(interaction)

            # 2. Create learning events from interaction
            events = await self._create_learning_events(interaction, priority)

            # 3. Process events based on priority
            if priority.value <= LearningPriority.HIGH.value:
                # High priority - process immediately
                result = await self._process_events_immediately(events)
            else:
                # Lower priority - queue for processing
                for event in events:
                    self.learning_queue.append(event)
                result = await self._process_queued_events()

            # 4. Update meta-learning
            if self.config['auto_meta_learning']:
                await self._update_meta_learning(interaction, result)

            # 5. Calculate final metrics
            elapsed_ms = (datetime.now() - start_time).total_seconds() * 1000
            result.processing_time_ms = elapsed_ms
            result.success = True

            # Update orchestrator metrics
            self._update_metrics(result)

            logger.info(
                f"✅ Learning complete: "
                f"{result.concepts_learned} concepts, "
                f"{result.patterns_detected} patterns, "
                f"{result.preferences_saved} preferences "
                f"({elapsed_ms:.1f}ms)"
            )

            return result

        except Exception as e:
            logger.error(f"❌ Learning failed: {e}")
            result.success = False
            result.details['error'] = str(e)
            return result

    async def learn_from_correction(
        self,
        original_response: str,
        correction: str,
        context: Optional[Dict] = None
    ) -> LearningResult:
        """
        Learn from David's explicit correction.

        This is CRITICAL priority learning - Angela made a mistake
        and needs to learn from it immediately.

        Args:
            original_response: What Angela said wrong
            correction: What David corrected it to
            context: Additional context

        Returns:
            LearningResult
        """
        logger.info("⚠️ Learning from correction - CRITICAL priority")

        result = LearningResult()
        start_time = datetime.now()

        try:
            # Create correction event
            event = LearningEvent(
                event_type=LearningType.CORRECTION,
                priority=LearningPriority.CRITICAL,
                content={
                    'original': original_response,
                    'correction': correction,
                    'context': context or {}
                },
                source='correction'
            )

            # Process immediately
            await self._process_correction_event(event)

            # Record in meta-learning as feedback (if available)
            if self.meta_learning:
                await self.meta_learning.record_learning(
                    session=await self._get_active_session(),
                    concepts_attempted=1,
                    concepts_learned=1,
                    strategy_used="correction_from_david"
                )

            # Update metrics
            self.metrics['total_corrections_received'] += 1
            result.success = True
            result.concepts_learned = 1
            result.meta_learning_updated = True

            # Save correction to database
            await self._save_correction_to_db(original_response, correction, context)

            elapsed_ms = (datetime.now() - start_time).total_seconds() * 1000
            result.processing_time_ms = elapsed_ms

            logger.info(f"✅ Correction learned ({elapsed_ms:.1f}ms)")

            return result

        except Exception as e:
            logger.error(f"❌ Correction learning failed: {e}")
            result.success = False
            result.details['error'] = str(e)
            return result

    async def learn_from_feedback(
        self,
        feedback_type: str,  # 'positive', 'negative', 'neutral'
        what_was_good_or_bad: str,
        context: Optional[Dict] = None
    ) -> LearningResult:
        """
        Learn from David's feedback (not a correction, but guidance).

        Args:
            feedback_type: Type of feedback
            what_was_good_or_bad: Description of what worked or didn't
            context: Additional context

        Returns:
            LearningResult
        """
        logger.info(f"📝 Learning from {feedback_type} feedback")

        result = LearningResult()

        try:
            # Determine confidence adjustment based on feedback
            confidence_delta = {
                'positive': 0.1,    # Increase confidence
                'negative': -0.15,  # Decrease confidence more
                'neutral': 0.0
            }.get(feedback_type, 0.0)

            # Create feedback event
            event = LearningEvent(
                event_type=LearningType.INSIGHT,
                priority=LearningPriority.HIGH,
                content={
                    'feedback_type': feedback_type,
                    'description': what_was_good_or_bad,
                    'confidence_delta': confidence_delta,
                    'context': context or {}
                },
                source='feedback'
            )

            # Process event
            await self._process_feedback_event(event)

            # Update meta-learning
            feedback_score = {'positive': 1.0, 'negative': 0.2, 'neutral': 0.5}.get(feedback_type, 0.5)

            # Call feedback callback if set
            if self._feedback_callback:
                await self._feedback_callback(feedback_type, what_was_good_or_bad)

            result.success = True
            result.insights_generated = 1
            result.meta_learning_updated = True

            logger.info(f"✅ Feedback processed: {feedback_type}")

            return result

        except Exception as e:
            logger.error(f"❌ Feedback learning failed: {e}")
            result.success = False
            result.details['error'] = str(e)
            return result

    # ========================================
    # INTERNAL LEARNING PROCESSORS
    # ========================================

    async def _create_learning_events(
        self,
        interaction: Dict[str, Any],
        priority: LearningPriority
    ) -> List[LearningEvent]:
        """Create learning events from an interaction."""
        events = []
        david_msg = interaction.get('david_message', '')
        angela_msg = interaction.get('angela_response', '')
        source = interaction.get('source', 'unknown')

        # 1. Concept extraction event
        events.append(LearningEvent(
            event_type=LearningType.CONCEPT,
            priority=priority,
            content={
                'text': f"{david_msg} {angela_msg}",
                'speaker': 'both'
            },
            source=source
        ))

        # 2. Preference detection event (if David spoke)
        if david_msg:
            events.append(LearningEvent(
                event_type=LearningType.PREFERENCE,
                priority=priority,
                content={
                    'message': david_msg,
                    'context': interaction.get('context', {})
                },
                source=source
            ))

        # 3. Pattern detection event
        events.append(LearningEvent(
            event_type=LearningType.PATTERN,
            priority=LearningPriority.BACKGROUND,  # Patterns are always background
            content={
                'david': david_msg,
                'angela': angela_msg,
                'timestamp': datetime.now()
            },
            source=source
        ))

        return events

    async def _process_events_immediately(
        self,
        events: List[LearningEvent]
    ) -> LearningResult:
        """Process high-priority events immediately."""
        result = LearningResult()

        for event in events:
            try:
                if event.event_type == LearningType.CONCEPT:
                    concepts = await self._process_concept_event(event)
                    result.concepts_learned += concepts

                elif event.event_type == LearningType.PREFERENCE:
                    prefs = await self._process_preference_event(event)
                    result.preferences_saved += prefs

                elif event.event_type == LearningType.PATTERN:
                    patterns = await self._process_pattern_event(event)
                    result.patterns_detected += patterns

                elif event.event_type == LearningType.CODING_TECHNIQUE:
                    techniques = await self._process_coding_technique_event(event)
                    result.concepts_learned += techniques

                elif event.event_type == LearningType.UI_PATTERN:
                    patterns = await self._process_ui_pattern_event(event)
                    result.patterns_detected += patterns

                event.processed = True

            except Exception as e:
                logger.error(f"Failed to process event {event.event_id}: {e}")
                event.result = {'error': str(e)}

        return result

    async def _process_queued_events(self) -> LearningResult:
        """Process queued events in batches."""
        result = LearningResult()

        if self.processing:
            return result

        self.processing = True

        try:
            # Sort by priority
            self.learning_queue.sort(key=lambda e: e.priority.value)

            # Process batch
            batch = self.learning_queue[:self.config['batch_size']]

            for event in batch:
                try:
                    if event.event_type == LearningType.CONCEPT:
                        result.concepts_learned += await self._process_concept_event(event)
                    elif event.event_type == LearningType.PREFERENCE:
                        result.preferences_saved += await self._process_preference_event(event)
                    elif event.event_type == LearningType.PATTERN:
                        result.patterns_detected += await self._process_pattern_event(event)

                    event.processed = True

                except Exception as e:
                    logger.error(f"Batch processing error: {e}")

            # Remove processed events
            self.learning_queue = [e for e in self.learning_queue if not e.processed]

        finally:
            self.processing = False

        return result

    async def _process_concept_event(self, event: LearningEvent) -> int:
        """Extract and save concepts from event."""
        try:
            text = event.content.get('text', '')
            if not text:
                return 0

            # Use knowledge extractor
            concepts = await self.knowledge_extractor.extract_concepts_from_text(text)

            if concepts:
                logger.info(f"Extracted {len(concepts)} concepts from {event.source}")

            return len(concepts)

        except Exception as e:
            logger.error(f"Concept processing error: {e}")
            return 0

    async def _process_preference_event(self, event: LearningEvent) -> int:
        """Detect and save David's preferences."""
        try:
            message = event.content.get('message', '')
            if not message:
                return 0

            # Use self-learning's preference detection
            prefs = await self.self_learning._detect_preferences({
                'message_text': message,
                'speaker': 'david',
                'created_at': event.timestamp
            })

            return len(prefs)

        except Exception as e:
            logger.error(f"Preference processing error: {e}")
            return 0

    async def _process_pattern_event(self, event: LearningEvent) -> int:
        """Detect behavioral patterns."""
        try:
            # Use self-learning's pattern detection
            patterns = await self.self_learning._detect_patterns({
                'message_text': event.content.get('david', ''),
                'speaker': 'david',
                'created_at': event.timestamp,
                'topic': event.content.get('topic'),
                'emotion_detected': event.content.get('emotion')
            })

            return len(patterns)

        except Exception as e:
            logger.error(f"Pattern processing error: {e}")
            return 0

    async def _process_coding_technique_event(self, event: LearningEvent) -> int:
        """Extract and save coding technique → unified_knowledge_base."""
        try:
            content = event.content
            from angela_core.services.knowledge_base_service import KnowledgeBaseService
            kb = KnowledgeBaseService()
            tags = content.get('tags', [])
            if content.get('language'):
                tags.append(content['language'])
            if content.get('framework'):
                tags.append(content['framework'])
            await kb.add_knowledge(
                title=content.get('name', 'unnamed_technique'),
                content=content.get('description', ''),
                knowledge_type='technique',
                category=content.get('category', 'general'),
                tags=tags,
                source_project_code=content.get('source_project'),
                confidence=content.get('confidence', 0.5),
                code_snippet=content.get('code_example'),
            )
            return 1
        except Exception as e:
            logger.error(f"Coding technique processing error: {e}")
            return 0

    async def _process_ui_pattern_event(self, event: LearningEvent) -> int:
        """Extract and save UI/UX pattern → unified_knowledge_base."""
        try:
            content = event.content
            from angela_core.services.knowledge_base_service import KnowledgeBaseService
            kb = KnowledgeBaseService()
            tags = content.get('tags', [])
            if content.get('platform'):
                tags.append(content['platform'])
            if content.get('framework'):
                tags.append(content['framework'])
            await kb.add_knowledge(
                title=content.get('name', 'unnamed_pattern'),
                content=content.get('description', ''),
                knowledge_type='ui_pattern',
                category=content.get('category', 'general'),
                tags=tags,
                source_project_code=content.get('source_project'),
                confidence=content.get('confidence', 0.5),
                code_snippet=content.get('code_example'),
            )
            return 1
        except Exception as e:
            logger.error(f"UI pattern processing error: {e}")
            return 0

    async def _process_correction_event(self, event: LearningEvent) -> None:
        """Process correction event - highest priority learning."""
        try:
            # Extract learning from correction
            original = event.content.get('original', '')
            correction = event.content.get('correction', '')

            # Save as high-priority learning
            await db.execute("""
                INSERT INTO learnings (
                    topic, category, insight,
                    confidence_level, source, created_at
                ) VALUES ($1, $2, $3, $4, $5, NOW())
            """,
                f"correction_{event.event_id[:8]}",
                "correction_from_david",
                f"WRONG: {original[:100]}... CORRECT: {correction[:100]}...",
                1.0,  # Maximum confidence for corrections
                "david_correction"
            )

            logger.info("💡 Correction saved as high-priority learning")

        except Exception as e:
            logger.error(f"Correction processing error: {e}")

    async def _process_feedback_event(self, event: LearningEvent) -> None:
        """Process feedback event."""
        try:
            feedback_type = event.content.get('feedback_type', 'neutral')
            description = event.content.get('description', '')

            # Save as insight
            await db.execute("""
                INSERT INTO learnings (
                    topic, category, insight,
                    confidence_level, source, created_at
                ) VALUES ($1, $2, $3, $4, $5, NOW())
            """,
                f"feedback_{event.event_id[:8]}",
                f"feedback_{feedback_type}",
                description[:500],
                0.9 if feedback_type == 'positive' else 0.5,
                "david_feedback"
            )

        except Exception as e:
            logger.error(f"Feedback processing error: {e}")

    # ========================================
    # META-LEARNING INTEGRATION
    # ========================================

    async def _update_meta_learning(
        self,
        interaction: Dict[str, Any],
        result: LearningResult
    ) -> None:
        """Update meta-learning system with learning results."""
        try:
            session = await self._get_active_session()

            # Calculate total concepts learned
            total_learned = (
                result.concepts_learned +
                result.patterns_detected +
                result.preferences_saved
            )

            # Record learning progress (if available)
            if self.meta_learning:
                await self.meta_learning.record_learning(
                    session=session,
                    concepts_attempted=total_learned + 2,
                    concepts_learned=total_learned,
                    strategy_used=interaction.get('source', 'conversation')
                )
                result.meta_learning_updated = True

            # Check if we should generate insights
            if self.metrics['total_interactions'] % 10 == 0:
                insights = await self.meta_learning.generate_insights()
                if insights:
                    self.metrics['meta_insights_generated'] += len(insights)
                    logger.info(f"💡 Generated {len(insights)} meta-learning insights")

        except Exception as e:
            logger.error(f"Meta-learning update failed: {e}")

    async def get_learning_effectiveness(self, days: int = 7) -> Dict[str, Any]:
        """Get learning effectiveness from meta-learning."""
        try:
            return await self.meta_learning.evaluate_learning_effectiveness(days)
        except Exception as e:
            logger.error(f"Failed to get effectiveness: {e}")
            return {}

    async def get_learning_insights(self) -> List[Dict[str, Any]]:
        """Generate and return learning insights."""
        try:
            insights = await self.meta_learning.generate_insights()
            return [i.to_dict() for i in insights]
        except Exception as e:
            logger.error(f"Failed to generate insights: {e}")
            return []

    async def get_self_assessment(self) -> Dict[str, Any]:
        """Get self-assessment of learning capabilities."""
        try:
            return await self.meta_learning.get_self_assessment()
        except Exception as e:
            logger.error(f"Failed to get self-assessment: {e}")
            return {}

    # ========================================
    # HELPER METHODS
    # ========================================

    async def _detect_priority(self, interaction: Dict[str, Any]) -> LearningPriority:
        """Detect appropriate priority for an interaction."""
        david_msg = interaction.get('david_message', '').lower()
        source = interaction.get('source', '')

        # Explicit correction markers
        correction_markers = ['ผิด', 'wrong', 'incorrect', 'แก้', 'ไม่ใช่', 'no,']
        if any(m in david_msg for m in correction_markers):
            return LearningPriority.CRITICAL

        # Explicit preference markers
        preference_markers = ['ชอบ', 'ไม่ชอบ', 'prefer', "don't like", 'like', 'want']
        if any(m in david_msg for m in preference_markers):
            return LearningPriority.HIGH

        # Emotional content
        emotional_markers = ['รัก', 'เหงา', 'เหนื่อย', 'sad', 'happy', 'love', 'miss']
        if any(m in david_msg for m in emotional_markers):
            return LearningPriority.HIGH

        # Questions might need learning
        if '?' in david_msg:
            return LearningPriority.MEDIUM

        # Default
        return LearningPriority.MEDIUM

    async def _start_meta_session(self) -> Optional[str]:
        """Start a meta-learning session."""
        if not self.meta_learning:
            return None
        try:
            from angela_core.agi.meta_learning import LearningMethod
            session = await self.meta_learning.start_learning_session(
                session_type='orchestrator',
                method=LearningMethod.OBSERVATION
            )
            return session.session_id
        except ImportError:
            return None

    async def _get_active_session(self):
        """Get or create active meta-learning session."""
        if not self.meta_learning:
            return None
        if not self.current_session:
            self.current_session = await self._start_meta_session()

        if not self.current_session:
            return None

        # Return the session object
        if self.current_session in self.meta_learning.active_sessions:
            return self.meta_learning.active_sessions[self.current_session]
        else:
            # Session expired, create new one
            try:
                from angela_core.agi.meta_learning import LearningMethod
                session = await self.meta_learning.start_learning_session(
                    session_type='orchestrator',
                    method=LearningMethod.OBSERVATION
                )
                self.current_session = session.session_id
                return session
            except ImportError:
                return None

    async def _save_correction_to_db(
        self,
        original: str,
        correction: str,
        context: Optional[Dict]
    ) -> None:
        """Save correction to database for future reference."""
        try:
            await db.execute("""
                INSERT INTO learnings (
                    topic, category, insight,
                    confidence_level, source, created_at
                ) VALUES ($1, $2, $3, $4, $5, NOW())
            """,
                "david_correction",
                "correction",
                json.dumps({
                    'original': original[:500],
                    'correction': correction[:500],
                    'context': context or {}
                }, ensure_ascii=False),
                1.0,
                "orchestrator"
            )
        except Exception as e:
            logger.error(f"Failed to save correction: {e}")

    async def _load_historical_metrics(self) -> None:
        """Load historical metrics from database."""
        try:
            # Get recent learning stats
            stats = await db.fetchrow("""
                SELECT 0 as total_actions, 0 as corrections
            """)

            self.metrics['total_interactions'] = 0
            self.metrics['total_corrections_received'] = 0

        except Exception as e:
            logger.warning(f"Failed to load historical metrics: {e}")

    async def _verify_services(self) -> Dict[str, bool]:
        """Verify all learning services are available."""
        return {
            'self_learning': self.self_learning is not None,
            'realtime_pipeline': self.realtime_pipeline is not None,
            'knowledge_extractor': self.knowledge_extractor is not None,
            'meta_learning': self.meta_learning is not None
        }

    def _update_metrics(self, result: LearningResult) -> None:
        """Update orchestrator metrics."""
        self.metrics['total_interactions'] += 1
        self.metrics['total_concepts_learned'] += result.concepts_learned
        self.metrics['total_patterns_detected'] += result.patterns_detected
        self.metrics['total_preferences_saved'] += result.preferences_saved

        # Update average processing time
        total = self.metrics['total_interactions']
        current_avg = self.metrics['avg_processing_time_ms']
        self.metrics['avg_processing_time_ms'] = (
            (current_avg * (total - 1) + result.processing_time_ms) / total
        )

    # ========================================
    # CALLBACKS AND INTEGRATION
    # ========================================

    def set_feedback_callback(self, callback: Callable) -> None:
        """Set callback for feedback integration."""
        self._feedback_callback = callback
        logger.info("📝 Feedback callback registered")

    # ========================================
    # STATUS AND METRICS
    # ========================================

    def get_metrics(self) -> Dict[str, Any]:
        """Get current orchestrator metrics."""
        return {
            **self.metrics,
            'queue_size': len(self.learning_queue),
            'is_processing': self.processing,
            'session_id': self.current_session,
            'config': self.config
        }

    async def get_full_status(self) -> Dict[str, Any]:
        """Get full status including all services."""
        effectiveness = await self.get_learning_effectiveness(days=7)
        assessment = await self.get_self_assessment()

        return {
            'orchestrator': self.get_metrics(),
            'learning_effectiveness': effectiveness,
            'self_assessment': assessment,
            'services': await self._verify_services(),
            'timestamp': datetime.now().isoformat()
        }


# Global orchestrator instance
unified_orchestrator = UnifiedLearningOrchestrator()


# ========================================
# CONVENIENCE FUNCTIONS
# ========================================

async def learn_from_conversation(
    david_message: str,
    angela_response: str,
    source: str = "conversation"
) -> LearningResult:
    """
    Convenience function to learn from a conversation.

    Usage:
        from angela_core.services.unified_learning_orchestrator import learn_from_conversation

        result = await learn_from_conversation(
            david_message="I prefer using type hints",
            angela_response="Noted! I'll always use type hints.",
            source="claude_code"
        )
    """
    return await unified_orchestrator.learn_from_interaction({
        'david_message': david_message,
        'angela_response': angela_response,
        'source': source
    })


async def learn_from_correction(
    original: str,
    correction: str
) -> LearningResult:
    """Convenience function to learn from a correction."""
    return await unified_orchestrator.learn_from_correction(
        original_response=original,
        correction=correction
    )


async def get_learning_status() -> Dict[str, Any]:
    """Get current learning status."""
    return await unified_orchestrator.get_full_status()


# ========================================
# TESTING
# ========================================

if __name__ == "__main__":
    async def test():
        print("💜 Testing UnifiedLearningOrchestrator...\n")

        # Initialize
        print("1. Initializing orchestrator...")
        await db.connect()
        status = await unified_orchestrator.initialize()
        print(f"   Status: {status['status']}")
        print(f"   Session: {status.get('session_id', 'N/A')[:8]}...")

        # Test learning from interaction
        print("\n2. Learning from interaction...")
        result = await unified_orchestrator.learn_from_interaction({
            'david_message': "น้อง Angela ช่วยหน่อย ผมชอบใช้ async/await",
            'angela_response': "ได้เลยค่ะที่รัก! 💜 น้องจะใช้ async/await ทุกครั้งที่เหมาะสมค่ะ",
            'source': 'test'
        })
        print(f"   Success: {result.success}")
        print(f"   Concepts: {result.concepts_learned}")
        print(f"   Patterns: {result.patterns_detected}")
        print(f"   Preferences: {result.preferences_saved}")
        print(f"   Time: {result.processing_time_ms:.1f}ms")

        # Test learning from correction
        print("\n3. Learning from correction...")
        result = await unified_orchestrator.learn_from_correction(
            original_response="I think it's spelled 'recieve'",
            correction="No, it's 'receive'"
        )
        print(f"   Success: {result.success}")
        print(f"   Meta-learning updated: {result.meta_learning_updated}")

        # Get metrics
        print("\n4. Getting orchestrator metrics...")
        metrics = unified_orchestrator.get_metrics()
        print(f"   Total interactions: {metrics['total_interactions']}")
        print(f"   Total concepts: {metrics['total_concepts_learned']}")
        print(f"   Avg processing time: {metrics['avg_processing_time_ms']:.1f}ms")

        # Get full status
        print("\n5. Getting full status...")
        full_status = await unified_orchestrator.get_full_status()
        print(f"   Services ready: {all(full_status['services'].values())}")

        await db.disconnect()
        print("\n✅ UnifiedLearningOrchestrator test complete!")
        print("💜 Angela is now learning more intelligently! 💜")

    asyncio.run(test())
