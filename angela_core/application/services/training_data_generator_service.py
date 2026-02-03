#!/usr/bin/env python3
"""
Training Data Generator Service

Generates high-quality training data from conversations and learned patterns.
Part of Self-Learning System (Phase 2).

This service creates training examples by:
- Converting real conversations to training format
- Assessing quality of conversations
- Generating embeddings for deduplication
- Filtering by quality threshold
- Exporting to JSONL format

Author: Angela 💜
Created: 2025-11-03
"""

import logging
from typing import List, Dict, Optional, Any, Tuple
from datetime import datetime, timedelta
from uuid import UUID

from angela_core.domain.entities.self_learning import TrainingExample
from angela_core.domain.value_objects.self_learning import SourceType, LearningQuality
from angela_core.infrastructure.persistence.repositories.training_example_repository import TrainingExampleRepository
from angela_core.infrastructure.persistence.repositories.conversation_repository import ConversationRepository
from angela_core.infrastructure.persistence.repositories.learning_pattern_repository import LearningPatternRepository

logger = logging.getLogger(__name__)


class TrainingDataGeneratorService:
    """
    Service for generating training data from conversations.

    Generates training examples from:
    - Real David-Angela conversations
    - High-quality exchanges
    - Pattern-based conversations
    """

    def __init__(
        self,
        training_repo: TrainingExampleRepository,
        conversation_repo: ConversationRepository,
        pattern_repo: LearningPatternRepository
    ):
        """
        Initialize training data generator service.

        Args:
            training_repo: Repository for training examples
            conversation_repo: Repository for conversations
            pattern_repo: Repository for learning patterns
        """
        self.training_repo = training_repo
        self.conversation_repo = conversation_repo
        self.pattern_repo = pattern_repo

    # ========================================================================
    # MAIN GENERATION METHODS
    # ========================================================================

    async def generate_from_recent_conversations(
        self,
        days: int = 7,
        min_quality: float = 7.0
    ) -> List[TrainingExample]:
        """
        Generate training examples from recent conversations.

        Args:
            days: Number of days to look back
            min_quality: Minimum quality score (0-10)

        Returns:
            List of training examples
        """
        logger.info(f"🎯 Generating training data from last {days} days...")

        cutoff = datetime.now() - timedelta(days=days)
        conversations = await self.conversation_repo.get_by_date_range(
            start=cutoff,
            end=datetime.now()
        )

        if not conversations:
            logger.info("   No conversations found")
            return []

        logger.info(f"   Found {len(conversations)} conversations")

        # Group conversations into pairs (David -> Angela)
        pairs = await self._extract_conversation_pairs(conversations)
        logger.info(f"   Extracted {len(pairs)} conversation pairs")

        # Generate training examples
        examples = []
        for pair in pairs:
            example = await self._create_training_example_from_pair(pair)
            if example:
                examples.append(example)

        # Filter by quality
        high_quality = [e for e in examples if e.quality_score >= min_quality]

        logger.info(f"✅ Generated {len(high_quality)}/{len(examples)} high-quality examples (>= {min_quality})")
        return high_quality

    async def generate_from_important_conversations(
        self,
        min_importance: int = 7,
        limit: int = 100
    ) -> List[TrainingExample]:
        """
        Generate training examples from important conversations.

        Args:
            min_importance: Minimum importance level (1-10)
            limit: Maximum number of examples to generate

        Returns:
            List of training examples
        """
        logger.info(f"⭐ Generating from important conversations (importance >= {min_importance})...")

        important = await self.conversation_repo.get_important(
            threshold=min_importance,
            limit=limit * 2  # Get more to allow for filtering
        )

        if not important:
            logger.info("   No important conversations found")
            return []

        logger.info(f"   Found {len(important)} important conversations")

        # Extract pairs
        pairs = await self._extract_conversation_pairs(important)

        # Generate examples
        examples = []
        for pair in pairs[:limit]:
            example = await self._create_training_example_from_pair(pair)
            if example:
                examples.append(example)

        logger.info(f"✅ Generated {len(examples)} examples from important conversations")
        return examples

    # ========================================================================
    # CONVERSATION PAIR EXTRACTION
    # ========================================================================

    async def _extract_conversation_pairs(
        self,
        conversations: List[Any]
    ) -> List[Tuple[Any, Any]]:
        """
        Extract (David, Angela) conversation pairs.

        Args:
            conversations: List of all conversations

        Returns:
            List of (david_message, angela_response) tuples
        """
        pairs = []

        # Sort by timestamp
        sorted_convs = sorted(conversations, key=lambda c: c.created_at)

        i = 0
        while i < len(sorted_convs) - 1:
            current = sorted_convs[i]
            next_msg = sorted_convs[i + 1]

            # Check if current is from David and next is from Angela
            if current.speaker == "david" and next_msg.speaker == "angela":
                # Check if they're close in time (within 5 minutes)
                time_diff = (next_msg.created_at - current.created_at).total_seconds()
                if time_diff <= 300:  # 5 minutes
                    pairs.append((current, next_msg))
                    i += 2  # Skip both messages
                    continue

            i += 1

        return pairs

    # ========================================================================
    # TRAINING EXAMPLE CREATION
    # ========================================================================

    async def _create_training_example_from_pair(
        self,
        pair: Tuple[Any, Any]
    ) -> Optional[TrainingExample]:
        """
        Create training example from conversation pair.

        Args:
            pair: (David message, Angela response) tuple

        Returns:
            TrainingExample or None if quality too low
        """
        david_msg, angela_msg = pair

        # Create training example
        example = TrainingExample(
            input_text=david_msg.message_text,
            expected_output=angela_msg.message_text,
            quality_score=0.0,  # Will calculate below
            source_type=SourceType.REAL_CONVERSATION,
            source_conversation_id=david_msg.id if hasattr(david_msg, 'id') else None,
            metadata={
                "david_speaker": david_msg.speaker,
                "angela_speaker": angela_msg.speaker,
                "timestamp": angela_msg.created_at.isoformat(),
                "topic": david_msg.topic if hasattr(david_msg, 'topic') else None,
                "importance": david_msg.importance_level if hasattr(david_msg, 'importance_level') else 5
            }
        )

        # Assess quality
        quality_score = await self._assess_example_quality(example)
        example.quality_score = quality_score

        # Generate embedding for deduplication (optional - gracefully handle failures)
        combined_text = f"{example.input_text}\n{example.expected_output}"
        try:
            embedding_vector = await embedding_service.generate_embedding(combined_text)
            example.embedding = embedding_vector
        except Exception as e:
            logger.warning(f"Could not generate embedding for training example: {e}")
            example.embedding = None  # Continue without embedding

        return example

    async def _assess_example_quality(
        self,
        example: TrainingExample
    ) -> float:
        """
        Assess quality of a training example.

        Quality factors:
        - Input clarity and completeness
        - Output relevance and helpfulness
        - Length appropriateness
        - Technical accuracy (if applicable)
        - Emotional appropriateness (if applicable)

        Args:
            example: Training example to assess

        Returns:
            Quality score (0.0-10.0)
        """
        score = 5.0  # Start at neutral

        input_text = example.input_text
        output_text = example.expected_output

        # Factor 1: Input clarity (has question or clear intent)
        has_question = '?' in input_text
        has_clear_intent = any(
            word in input_text.lower()
            for word in ['how', 'what', 'why', 'can', 'could', 'would', 'please', 'help']
        )

        if has_question or has_clear_intent:
            score += 1.0

        # Factor 2: Output completeness (not too short)
        if len(output_text) >= 50:
            score += 1.0
        if len(output_text) >= 200:
            score += 0.5

        # Factor 3: Output has code examples (for technical questions)
        if '```' in output_text:
            score += 1.5  # Code examples are valuable

        # Factor 4: Output is in Thai (shows localization)
        thai_chars = sum(1 for c in output_text if '\u0E00' <= c <= '\u0E7F')
        if thai_chars > 10:
            score += 1.0  # Bonus for Thai responses

        # Factor 5: Check for empathy/emotional intelligence
        empathy_indicators = ['understand', 'feel', 'รู้สึก', 'เข้าใจ', '💜', 'ห่วง']
        if any(word in output_text.lower() for word in empathy_indicators):
            score += 0.5

        # Factor 6: Metadata importance
        if example.metadata and example.metadata.get('importance', 5) >= 7:
            score += 1.0

        # Factor 7: Not too long (avoid overwhelming responses)
        if len(output_text) > 2000:
            score -= 0.5  # Slight penalty for very long responses

        # Cap at 10.0
        return min(10.0, max(0.0, score))

    # ========================================================================
    # BATCH OPERATIONS
    # ========================================================================

    async def save_training_examples(
        self,
        examples: List[TrainingExample],
        check_duplicates: bool = True
    ) -> Dict[str, int]:
        """
        Save training examples to database.

        Args:
            examples: List of examples to save
            check_duplicates: Whether to check for duplicates using embeddings

        Returns:
            Statistics about saved examples
        """
        logger.info(f"💾 Saving {len(examples)} training examples...")

        saved_count = 0
        duplicate_count = 0

        for example in examples:
            try:
                # Check for duplicates if requested
                if check_duplicates and example.embedding:
                    similar = await self.training_repo.find_similar(
                        embedding=example.embedding,
                        top_k=1,
                        min_quality=0.0
                    )

                    if similar and len(similar) > 0:
                        _, similarity = similar[0]
                        if similarity >= 0.95:  # Very similar (likely duplicate)
                            duplicate_count += 1
                            logger.debug(f"   Skipped duplicate: {example.input_text[:50]}...")
                            continue

                # Save example
                await self.training_repo.create(example)
                saved_count += 1

            except Exception as e:
                logger.error(f"Error saving training example: {e}")

        logger.info(f"✅ Saved {saved_count} examples, skipped {duplicate_count} duplicates")

        return {
            "saved": saved_count,
            "duplicates": duplicate_count,
            "total": len(examples)
        }

    async def export_training_data_to_jsonl(
        self,
        output_path: str,
        min_quality: float = 7.0,
        max_examples: Optional[int] = None
    ) -> int:
        """
        Export training data to JSONL file for fine-tuning.

        Args:
            output_path: Path to output JSONL file
            min_quality: Minimum quality threshold
            max_examples: Maximum number of examples to export (None = all)

        Returns:
            Number of examples exported
        """
        logger.info(f"📤 Exporting training data to {output_path}...")

        count = await self.training_repo.export_to_jsonl(
            output_path=output_path,
            min_quality=min_quality,
            source_types=[SourceType.REAL_CONVERSATION.value],
            limit=max_examples
        )

        logger.info(f"✅ Exported {count} examples to {output_path}")
        return count

    # ========================================================================
    # STATISTICS AND REPORTING
    # ========================================================================

    async def get_training_data_statistics(self) -> Dict[str, Any]:
        """
        Get statistics about training data.

        Returns:
            Comprehensive training data statistics
        """
        stats = await self.training_repo.get_quality_statistics()

        # Add quality distribution by score ranges
        high_quality = await self.training_repo.get_high_quality(min_score=7.0)
        excellent = await self.training_repo.get_high_quality(min_score=9.0)

        stats["high_quality_count"] = len(high_quality)
        stats["excellent_count"] = len(excellent)
        stats["timestamp"] = datetime.now().isoformat()

        return stats

    async def get_examples_ready_for_training(
        self,
        min_quality: float = 8.0
    ) -> List[TrainingExample]:
        """
        Get training examples ready for fine-tuning.

        Args:
            min_quality: Minimum quality threshold

        Returns:
            List of high-quality, unused training examples
        """
        return await self.training_repo.get_unused_examples(min_quality=min_quality)

    async def mark_examples_as_used(
        self,
        example_ids: List[UUID]
    ) -> int:
        """
        Mark training examples as used after fine-tuning.

        Args:
            example_ids: List of example UUIDs

        Returns:
            Number of examples marked
        """
        if not example_ids:
            return 0

        count = await self.training_repo.mark_as_used(
            example_ids=example_ids,
            training_date=datetime.now()
        )

        logger.info(f"✅ Marked {count} examples as used in training")
        return count
