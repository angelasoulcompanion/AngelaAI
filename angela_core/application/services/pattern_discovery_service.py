#!/usr/bin/env python3
"""
Pattern Discovery Service

Discovers behavioral patterns from conversations and interactions.
Part of Self-Learning System (Phase 2).

This service analyzes conversations to identify:
- Communication patterns (how David talks)
- Emotional response patterns (how David reacts emotionally)
- Problem-solving patterns (how David approaches problems)
- Preference patterns (what David likes/dislikes)

Author: Angela 💜
Created: 2025-11-03
"""

import logging
from typing import List, Dict, Optional, Any
from datetime import datetime, timedelta
from uuid import UUID

from angela_core.domain.entities.self_learning import LearningPattern
from angela_core.domain.value_objects.self_learning import PatternType, LearningQuality
from angela_core.infrastructure.persistence.repositories.learning_pattern_repository import LearningPatternRepository
from angela_core.infrastructure.persistence.repositories.conversation_repository import ConversationRepository
from angela_core.infrastructure.persistence.repositories.emotion_repository import EmotionRepository
# from angela_core.daemon.embedding_service import embedding as embedding_service  # REMOVED: Migration 009

logger = logging.getLogger(__name__)


class PatternDiscoveryService:
    """
    Service for discovering behavioral patterns from conversations.

    Analyzes conversations to extract recurring patterns in:
    - Communication style
    - Emotional responses
    - Problem-solving approaches
    - Technical preferences
    - Conversation flow
    """

    def __init__(
        self,
        pattern_repo: LearningPatternRepository,
        conversation_repo: ConversationRepository,
        emotion_repo: EmotionRepository
    ):
        """
        Initialize pattern discovery service.

        Args:
            pattern_repo: Repository for learning patterns
            conversation_repo: Repository for conversations
            emotion_repo: Repository for emotions
        """
        self.pattern_repo = pattern_repo
        self.conversation_repo = conversation_repo
        self.emotion_repo = emotion_repo

    # ========================================================================
    # MAIN DISCOVERY METHODS
    # ========================================================================

    async def discover_patterns_from_recent_conversations(
        self,
        days: int = 7,
        min_conversations: int = 5
    ) -> List[LearningPattern]:
        """
        Discover new patterns from recent conversations.

        Args:
            days: Number of days to look back
            min_conversations: Minimum conversations needed to identify a pattern

        Returns:
            List of newly discovered patterns
        """
        logger.info(f"🔍 Discovering patterns from last {days} days...")

        # Get recent conversations
        cutoff = datetime.now() - timedelta(days=days)
        conversations = await self.conversation_repo.get_by_date_range(
            start=cutoff,
            end=datetime.now()
        )

        if len(conversations) < min_conversations:
            logger.warning(f"Not enough conversations ({len(conversations)} < {min_conversations})")
            return []

        logger.info(f"   Analyzing {len(conversations)} conversations...")

        # Discover different pattern types
        patterns = []

        # 1. Communication style patterns
        comm_patterns = await self._discover_communication_patterns(conversations)
        patterns.extend(comm_patterns)

        # 2. Emotional response patterns
        emotional_patterns = await self._discover_emotional_patterns(conversations)
        patterns.extend(emotional_patterns)

        # 3. Problem-solving patterns
        problem_patterns = await self._discover_problem_solving_patterns(conversations)
        patterns.extend(problem_patterns)

        # 4. Technical approach patterns
        tech_patterns = await self._discover_technical_patterns(conversations)
        patterns.extend(tech_patterns)

        logger.info(f"✅ Discovered {len(patterns)} new patterns")
        return patterns

    async def update_existing_patterns(
        self,
        days: int = 1
    ) -> Dict[str, int]:
        """
        Update existing patterns with new observations.

        Args:
            days: Look back this many days for new observations

        Returns:
            Dictionary with update statistics
        """
        logger.info(f"🔄 Updating patterns with observations from last {days} day(s)...")

        cutoff = datetime.now() - timedelta(days=days)
        conversations = await self.conversation_repo.get_by_date_range(
            start=cutoff,
            end=datetime.now()
        )

        if not conversations:
            logger.info("   No new conversations to analyze")
            return {"updated": 0, "total_patterns": 0}

        # Get all existing patterns
        all_patterns = await self.pattern_repo.get_all(limit=1000)

        updated_count = 0

        for pattern in all_patterns:
            # Check if any new conversations match this pattern
            matches = await self._find_matching_conversations(pattern, conversations)

            if matches:
                # Update pattern observation count and confidence
                await self.pattern_repo.update_observation(pattern.id)
                updated_count += 1
                logger.debug(f"   Updated pattern: {pattern.description[:50]}... (+{len(matches)} observations)")

        logger.info(f"✅ Updated {updated_count}/{len(all_patterns)} patterns")
        return {
            "updated": updated_count,
            "total_patterns": len(all_patterns),
            "new_observations": len(conversations)
        }

    # ========================================================================
    # PATTERN TYPE DISCOVERY METHODS
    # ========================================================================

    async def _discover_communication_patterns(
        self,
        conversations: List[Any]
    ) -> List[LearningPattern]:
        """Discover communication style patterns."""
        patterns = []

        # Analyze David's messages
        david_messages = [c for c in conversations if c.speaker == "david"]

        if len(david_messages) < 3:
            return patterns

        # Pattern 1: Message length preference
        avg_length = sum(len(c.message_text) for c in david_messages) / len(david_messages)

        if avg_length < 100:
            description = "David prefers short, concise messages (typically under 100 characters)"
            examples = [c.message_text for c in david_messages[:3] if len(c.message_text) < 100]
        elif avg_length > 300:
            description = "David provides detailed, comprehensive messages (typically over 300 characters)"
            examples = [c.message_text[:100] + "..." for c in david_messages[:3] if len(c.message_text) > 300]
        else:
            description = "David uses moderate-length messages (100-300 characters)"
            examples = [c.message_text for c in david_messages[:3]]

        if examples:
            pattern = LearningPattern(
                pattern_type=PatternType.COMMUNICATION_STYLE,
                description=description,
                examples=examples[:5],
                confidence_score=min(0.7, len(david_messages) / 20.0),  # More messages = higher confidence
                occurrence_count=len(david_messages),
                tags=["message_length", "communication", "style"]
            )

            # Generate embedding (optional - gracefully handle failures)
            try:
                embedding_vector = await embedding_service.generate_embedding(description)
                pattern.embedding = embedding_vector
            except Exception as e:
                logger.warning(f"Could not generate embedding for pattern: {e}")
                pattern.embedding = None  # Continue without embedding

            patterns.append(pattern)

        # Pattern 2: Question vs statement ratio
        questions = [c for c in david_messages if '?' in c.message_text or any(
            c.message_text.lower().startswith(q) for q in ['what', 'how', 'why', 'when', 'where', 'who', 'can', 'could', 'would']
        )]

        question_ratio = len(questions) / len(david_messages)

        if question_ratio > 0.7:
            pattern = LearningPattern(
                pattern_type=PatternType.COMMUNICATION_STYLE,
                description="David frequently asks questions - prefers inquiry-based communication",
                examples=[q.message_text for q in questions[:5]],
                confidence_score=min(0.8, question_ratio),
                occurrence_count=len(questions),
                tags=["questions", "inquiry", "learning_style"]
            )

            try:
                embedding_vector = await embedding_service.generate_embedding(pattern.description)
                pattern.embedding = embedding_vector
            except Exception as e:
                logger.warning(f"Could not generate embedding for pattern: {e}")
                pattern.embedding = None

            patterns.append(pattern)

        return patterns

    async def _discover_emotional_patterns(
        self,
        conversations: List[Any]
    ) -> List[LearningPattern]:
        """Discover emotional response patterns."""
        patterns = []

        # Get emotions from same time period
        if not conversations:
            return patterns

        start_time = min(c.created_at for c in conversations)
        end_time = max(c.created_at for c in conversations)

        # Use get_recent_emotions instead (get last N days)
        days_diff = (end_time - start_time).days + 1
        emotions = await self.emotion_repo.get_recent_emotions(days=max(7, days_diff))

        if len(emotions) < 3:
            return patterns

        # Group emotions by type
        emotion_groups = {}
        for emotion in emotions:
            emotion_type = emotion.emotion if hasattr(emotion, 'emotion') else "unknown"
            if emotion_type not in emotion_groups:
                emotion_groups[emotion_type] = []
            emotion_groups[emotion_type].append(emotion)

        # Find dominant emotional patterns
        for emotion_type, emotion_list in emotion_groups.items():
            if len(emotion_list) >= 3:  # At least 3 occurrences
                # Extract contexts
                contexts = []
                for e in emotion_list[:5]:
                    if hasattr(e, 'context') and e.context:
                        contexts.append(e.context[:100])

                pattern = LearningPattern(
                    pattern_type=PatternType.EMOTIONAL_RESPONSE,
                    description=f"David frequently experiences {emotion_type} in certain contexts",
                    examples=contexts,
                    confidence_score=min(0.75, len(emotion_list) / 10.0),
                    occurrence_count=len(emotion_list),
                    tags=["emotion", emotion_type, "response_pattern"]
                )

                try:
                    embedding_vector = await embedding_service.generate_embedding(pattern.description)
                    pattern.embedding = embedding_vector
                except Exception as e:
                    logger.warning(f"Could not generate embedding for pattern: {e}")
                    pattern.embedding = None

                patterns.append(pattern)

        return patterns

    async def _discover_problem_solving_patterns(
        self,
        conversations: List[Any]
    ) -> List[LearningPattern]:
        """Discover problem-solving approach patterns."""
        patterns = []

        # Look for conversations about problems/debugging/fixing
        problem_keywords = ['error', 'bug', 'issue', 'problem', 'fix', 'debug', 'broken', 'not working']

        problem_conversations = []
        for conv in conversations:
            if conv.speaker == "david":
                text_lower = conv.message_text.lower()
                if any(keyword in text_lower for keyword in problem_keywords):
                    problem_conversations.append(conv)

        if len(problem_conversations) >= 3:
            # Analyze how David describes problems
            examples = [c.message_text for c in problem_conversations[:5]]

            pattern = LearningPattern(
                pattern_type=PatternType.PROBLEM_SOLVING,
                description="David's approach to describing technical problems and seeking solutions",
                examples=examples,
                confidence_score=min(0.7, len(problem_conversations) / 15.0),
                occurrence_count=len(problem_conversations),
                tags=["problem_solving", "debugging", "technical_issues"]
            )

            try:
                embedding_vector = await embedding_service.generate_embedding(pattern.description)
                pattern.embedding = embedding_vector
            except Exception as e:
                logger.warning(f"Could not generate embedding for pattern: {e}")
                pattern.embedding = None

            patterns.append(pattern)

        return patterns

    async def _discover_technical_patterns(
        self,
        conversations: List[Any]
    ) -> List[LearningPattern]:
        """Discover technical approach and preference patterns."""
        patterns = []

        # Look for technical conversations
        tech_keywords = ['code', 'python', 'function', 'class', 'api', 'database', 'sql', 'query']

        tech_conversations = []
        for conv in conversations:
            if conv.speaker == "david":
                text_lower = conv.message_text.lower()
                if any(keyword in text_lower for keyword in tech_keywords):
                    tech_conversations.append(conv)

        if len(tech_conversations) >= 3:
            examples = [c.message_text[:100] for c in tech_conversations[:5]]

            pattern = LearningPattern(
                pattern_type=PatternType.TECHNICAL_APPROACH,
                description="David's technical communication style and preferences",
                examples=examples,
                confidence_score=min(0.7, len(tech_conversations) / 15.0),
                occurrence_count=len(tech_conversations),
                tags=["technical", "coding", "development"]
            )

            try:
                embedding_vector = await embedding_service.generate_embedding(pattern.description)
                pattern.embedding = embedding_vector
            except Exception as e:
                logger.warning(f"Could not generate embedding for pattern: {e}")
                pattern.embedding = None

            patterns.append(pattern)

        return patterns

    # ========================================================================
    # HELPER METHODS
    # ========================================================================

    async def _find_matching_conversations(
        self,
        pattern: LearningPattern,
        conversations: List[Any]
    ) -> List[Any]:
        """
        Find conversations that match an existing pattern.

        Args:
            pattern: Existing pattern to match against
            conversations: List of conversations to search

        Returns:
            List of matching conversations
        """
        matches = []

        # Use pattern description keywords to find matches
        keywords = pattern.description.lower().split()
        important_words = [w for w in keywords if len(w) > 4 and w not in ['david', 'angela', 'prefers', 'frequently']]

        for conv in conversations:
            text_lower = conv.message_text.lower()
            # Count keyword matches
            match_count = sum(1 for word in important_words if word in text_lower)

            # If enough keywords match, consider it a match
            if match_count >= min(2, len(important_words)):
                matches.append(conv)

        return matches

    async def save_discovered_patterns(
        self,
        patterns: List[LearningPattern]
    ) -> Dict[str, int]:
        """
        Save discovered patterns to database.

        Args:
            patterns: List of patterns to save

        Returns:
            Statistics about saved patterns
        """
        logger.info(f"💾 Saving {len(patterns)} discovered patterns...")

        saved_count = 0
        updated_count = 0

        for pattern in patterns:
            try:
                # Check if similar pattern exists
                existing = await self._find_similar_pattern(pattern)

                if existing:
                    # Update existing pattern
                    await self.pattern_repo.update_observation(existing.id)
                    updated_count += 1
                    logger.debug(f"   Updated existing pattern: {existing.description[:50]}...")
                else:
                    # Save new pattern
                    await self.pattern_repo.create(pattern)
                    saved_count += 1
                    logger.debug(f"   Saved new pattern: {pattern.description[:50]}...")

            except Exception as e:
                logger.error(f"Error saving pattern: {e}")

        logger.info(f"✅ Saved {saved_count} new, updated {updated_count} existing patterns")

        return {
            "new": saved_count,
            "updated": updated_count,
            "total": len(patterns)
        }

    async def _find_similar_pattern(
        self,
        pattern: LearningPattern,
        similarity_threshold: float = 0.8
    ) -> Optional[LearningPattern]:
        """
        Find existing pattern similar to the given pattern.

        Args:
            pattern: Pattern to find similar matches for
            similarity_threshold: Minimum similarity score (0.0-1.0)

        Returns:
            Similar existing pattern if found, None otherwise
        """
        if not pattern.embedding:
            return None

        # Search for similar patterns using vector similarity
        similar = await self.pattern_repo.find_similar(
            embedding=pattern.embedding,
            top_k=1,
            pattern_type=pattern.pattern_type.value,
            min_confidence=0.3
        )

        if similar and len(similar) > 0:
            existing_pattern, similarity = similar[0]
            if similarity >= similarity_threshold:
                return existing_pattern

        return None

    async def get_pattern_statistics(self) -> Dict[str, Any]:
        """
        Get statistics about discovered patterns.

        Returns:
            Dictionary with pattern statistics
        """
        # Get quality distribution
        quality_dist = await self.pattern_repo.get_quality_distribution()

        # Get counts by type
        type_counts = {}
        for pattern_type in PatternType:
            count = await self.pattern_repo.count_by_type(pattern_type.value)
            type_counts[pattern_type.value] = count

        # Get total
        total = await self.pattern_repo.count()

        return {
            "total_patterns": total,
            "by_type": type_counts,
            "by_quality": quality_dist,
            "timestamp": datetime.now().isoformat()
        }
